"""
6-DOF MLP Trajectory Planner — Training & ONNX Export
======================================================

Trains a 3-layer MLP on synthetic quintic-spline trajectories and exports
the trained model to ONNX format for use with the moqui-device
run#TrajectoryPlanner service.

Usage
-----
    pip install torch numpy onnx onnxscript
    python script/train_trajectory_planner.py

Output
------
    data/ml/trajectory_planner.onnx

Model I/O
---------
    Input  : float32[1, 12]  — [q_start(6) || q_goal(6)], joint angles in radians
    Output : float32[1, 60]  — 10 waypoints × 6 joints (flat, row-major)

The DJL service reads the flat output and reconstructs shape [N_WAYPOINTS, 6].
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

# ── Configuration ─────────────────────────────────────────────────────────────

N_JOINTS    = 6
N_WAYPOINTS = 10
N_OUT       = N_WAYPOINTS * N_JOINTS   # 60

JOINT_LIMITS = (-np.pi, np.pi)         # radians, symmetric

N_TRAIN     = 50_000
N_VAL       = 5_000
BATCH       = 512
EPOCHS      = 80
LR          = 1e-3

OUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "ml")
OUT_PATH = os.path.join(OUT_DIR, "trajectory_planner.onnx")

# ── Synthetic data generation (quintic spline) ────────────────────────────────

def quintic_spline_waypoints(q_start: np.ndarray, q_goal: np.ndarray,
                             n_waypoints: int) -> np.ndarray:
    """
    Interpolate between q_start and q_goal using a degree-5 polynomial that
    enforces zero velocity and acceleration at both endpoints.

    Returns array of shape (n_waypoints, n_joints).
    """
    t = np.linspace(0.0, 1.0, n_waypoints)
    # Quintic basis: ensures pos/vel/acc continuity at endpoints
    s = 6*t**5 - 15*t**4 + 10*t**3
    # s(0)=0, s(1)=1, s'(0)=s'(1)=0, s''(0)=s''(1)=0
    waypoints = q_start[None, :] + s[:, None] * (q_goal - q_start)[None, :]
    return waypoints.astype(np.float32)


def generate_dataset(n: int):
    lo, hi = JOINT_LIMITS
    q_start = np.random.uniform(lo, hi, (n, N_JOINTS)).astype(np.float32)
    q_goal  = np.random.uniform(lo, hi, (n, N_JOINTS)).astype(np.float32)
    targets = np.array([
        quintic_spline_waypoints(q_start[i], q_goal[i], N_WAYPOINTS).flatten()
        for i in range(n)
    ], dtype=np.float32)
    inputs = np.concatenate([q_start, q_goal], axis=1)  # (n, 12)
    return inputs, targets


# ── Model ─────────────────────────────────────────────────────────────────────

class TrajectoryMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(12, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, N_OUT),
        )

    def forward(self, x):
        return self.net(x)


# ── Training loop ─────────────────────────────────────────────────────────────

def train():
    print("Generating training data …")
    X_train, y_train = generate_dataset(N_TRAIN)
    X_val,   y_val   = generate_dataset(N_VAL)

    X_train_t = torch.from_numpy(X_train)
    y_train_t = torch.from_numpy(y_train)
    X_val_t   = torch.from_numpy(X_val)
    y_val_t   = torch.from_numpy(y_val)

    dataset = torch.utils.data.TensorDataset(X_train_t, y_train_t)
    loader  = torch.utils.data.DataLoader(dataset, batch_size=BATCH, shuffle=True)

    model   = TrajectoryMLP()
    opt     = optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    print(f"Training {N_TRAIN} samples, {EPOCHS} epochs …")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in loader:
            pred = model(xb)
            loss = loss_fn(pred, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(xb)

        if epoch % 10 == 0 or epoch == 1:
            model.eval()
            with torch.no_grad():
                val_loss = loss_fn(model(X_val_t), y_val_t).item()
            rmse = np.sqrt(total_loss / N_TRAIN)
            print(f"  epoch {epoch:3d}/{EPOCHS}  train-RMSE={rmse:.4f}  val-MSE={val_loss:.4f}")

    return model


# ── ONNX export ───────────────────────────────────────────────────────────────

def _ensure_onnxscript():
    """PyTorch >= 2.5 requires onnxscript even for the legacy exporter path."""
    try:
        import onnxscript  # noqa: F401
    except ModuleNotFoundError:
        import subprocess, sys
        print("Installing onnxscript (required by this PyTorch version) …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "onnxscript"])


def export_onnx(model: nn.Module):
    _ensure_onnxscript()
    os.makedirs(OUT_DIR, exist_ok=True)
    model.eval()
    dummy = torch.zeros(1, 12, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy,
        OUT_PATH,
        input_names=["input"],
        output_names=["waypoints"],
        dynamic_axes={"input": {0: "batch"}, "waypoints": {0: "batch"}},
        opset_version=17,
    )
    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"Exported → {OUT_PATH}  ({size_kb:.1f} KB)")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    np.random.seed(42)
    torch.manual_seed(42)
    model = train()
    export_onnx(model)
    print("Done. Start moqui and call run#TrajectoryPlanner with mathModelId=TrjPlannerMlp6DofV1.")
