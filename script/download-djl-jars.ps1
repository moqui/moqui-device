# Download DJL + ONNX Runtime JARs required by run#TrajectoryPlanner
# Run from the moqui-device component directory:
#   powershell -ExecutionPolicy Bypass -File script\download-djl-jars.ps1

$LIB_DIR = Join-Path $PSScriptRoot "..\lib"
New-Item -ItemType Directory -Force -Path $LIB_DIR | Out-Null

$MAVEN = "https://repo1.maven.org/maven2"
$JARS = @(
    # DJL core API
    "$MAVEN/ai/djl/api/0.31.0/api-0.31.0.jar",
    # DJL ONNX Runtime engine
    "$MAVEN/ai/djl/onnxruntime/onnxruntime-engine/0.31.0/onnxruntime-engine-0.31.0.jar",
    # Microsoft ONNX Runtime (CPU, bundles native libs)
    "$MAVEN/com/microsoft/onnxruntime/onnxruntime/1.18.0/onnxruntime-1.18.0.jar",
    # DJL transitive dependencies
    "$MAVEN/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar"
)

foreach ($url in $JARS) {
    $file = Join-Path $LIB_DIR ([System.IO.Path]::GetFileName($url))
    if (Test-Path $file) {
        Write-Host "  already present: $file"
    } else {
        Write-Host "  downloading $url ..."
        Invoke-WebRequest -Uri $url -OutFile $file -UseBasicParsing
        Write-Host "  saved: $file"
    }
}

Write-Host ""
Write-Host "Done. Restart moqui to load the JARs."
Write-Host "Then call: run#TrajectoryPlanner with mathModelId=TrjPlannerMlp6DofV1"
