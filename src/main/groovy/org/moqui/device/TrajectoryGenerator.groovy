/*
 * This software is in the public domain under CC0 1.0 Universal plus a
 * Grant of Patent License.
 *
 * To the extent possible under law, the author(s) have dedicated all
 * copyright and related and neighboring rights to this software to the
 * public domain worldwide. This software is distributed without any
 * warranty.
 *
 * You should have received a copy of the CC0 Public Domain Dedication
 * along with this software (see the LICENSE.md file). If not, see
 * <http://creativecommons.org/publicdomain/zero/1.0/>.
 */
package org.moqui.device

import org.moqui.BaseException
import org.moqui.context.ExecutionContext

class TrajectoryGenerator {
    static List<Double> normalizeJointConfig(Object config, String fieldName) {
        if (!(config instanceof List)) {
            throw new BaseException("${fieldName} must be a List with exactly 6 numeric joint angles.")
        }

        List configList = (List) config
        if (configList.size() != 6) {
            throw new BaseException("${fieldName} must contain exactly 6 joint angles, found ${configList.size()}.")
        }

        List<Double> normalized = []
        for (int i = 0; i < configList.size(); i++) {
            Object value = configList.get(i)
            if (value instanceof Number) {
                normalized.add((value as Number).doubleValue())
                continue
            }

            if (value instanceof CharSequence) {
                String textValue = value.toString().trim()
                if (!textValue) throw new BaseException("${fieldName}[${i}] must not be empty.")
                try {
                    normalized.add(Double.parseDouble(textValue))
                    continue
                } catch (NumberFormatException e) {
                    throw new BaseException("${fieldName}[${i}] must be numeric, found value '${textValue}'.", e)
                }
            }

            throw new BaseException("${fieldName}[${i}] must be numeric, found ${value?.getClass()?.getSimpleName() ?: 'null'}.")
        }
        return normalized
    }

    static Map<String, Object> runInference(ExecutionContext ec, String onnxContentLocation,
            List<Double> startConfig, List<Double> goalConfig) {
        if (!onnxContentLocation) throw new BaseException("Missing ONNX content location.")

        float[] rawOutput
        long inferenceLatencyMs = 0L
        File tempOnnx = null
        File tempDataFile = null
        java.nio.file.Path tempDir = null
        def onnxModel = null
        def manager = null
        def predictor = null

        try {
            String origName = onnxContentLocation.substring(onnxContentLocation.lastIndexOf('/') + 1)
            String modelName = origName.replaceAll('\\.onnx$', '')
            tempDir = java.nio.file.Files.createTempDirectory("djl-onnx-")
            tempOnnx = new File(tempDir.toFile(), origName)

            ec.resource.getLocationReference(onnxContentLocation).openStream().withStream { inp ->
                tempOnnx.withOutputStream { out -> out << inp }
            }

            try {
                tempDataFile = new File(tempDir.toFile(), origName + ".data")
                ec.resource.getLocationReference(onnxContentLocation + ".data").openStream().withStream { inp ->
                    tempDataFile.withOutputStream { out -> out << inp }
                }
            } catch (Exception ignored) {
                tempDataFile = null
            }

            manager = ai.djl.ndarray.NDManager.newBaseManager("OnnxRuntime")
            onnxModel = ai.djl.Model.newInstance(modelName, "OnnxRuntime")
            onnxModel.load(tempDir, modelName)
            predictor = onnxModel.newPredictor(new ai.djl.translate.NoopTranslator())

            float[] inputData = new float[12]
            for (int i = 0; i < 6; i++) {
                inputData[i] = startConfig.get(i).floatValue()
                inputData[6 + i] = goalConfig.get(i).floatValue()
            }

            def inputArr = manager.create(inputData, new ai.djl.ndarray.types.Shape(1L, 12L))
            long tInfer = System.currentTimeMillis()
            def outList = predictor.predict(new ai.djl.ndarray.NDList(inputArr))
            inferenceLatencyMs = System.currentTimeMillis() - tInfer
            rawOutput = outList.get(0).toFloatArray()
        } catch (NoClassDefFoundError | ClassNotFoundException e) {
            throw new BaseException("DJL JARs not found on classpath. Place api-0.31.0.jar, onnxruntime-engine-0.31.0.jar and onnxruntime-1.18.0.jar in runtime/component/moqui-device/lib/ and restart.", e)
        } catch (Exception e) {
            throw new BaseException("Trajectory inference failed: ${e.message}", e)
        } finally {
            if (predictor) predictor.close()
            if (onnxModel) onnxModel.close()
            if (manager) manager.close()
            if (tempDir != null) deleteDirectory(tempDir.toFile())
        }

        if (!rawOutput || rawOutput.length == 0) {
            throw new BaseException("Trajectory inference returned an empty output tensor.")
        }
        if ((rawOutput.length % 6) != 0) {
            throw new BaseException("Trajectory inference returned ${rawOutput.length} values, not divisible by 6 joints.")
        }

        List<List<Double>> waypoints = []
        int nWaypoints = rawOutput.length.intdiv(6)
        for (int i = 0; i < nWaypoints; i++) {
            List<Double> waypoint = []
            for (int j = 0; j < 6; j++) {
                waypoint.add((double) rawOutput[i * 6 + j])
            }
            waypoints.add(waypoint)
        }

        return [waypoints: waypoints, waypointCount: nWaypoints, inferenceLatencyMs: inferenceLatencyMs]
    }

    protected static void deleteDirectory(File directory) {
        if (directory == null || !directory.exists()) return

        File[] children = directory.listFiles()
        if (children != null) {
            for (File child in children) {
                if (child.isDirectory()) deleteDirectory(child)
                else child.delete()
            }
        }
        directory.delete()
    }
}
