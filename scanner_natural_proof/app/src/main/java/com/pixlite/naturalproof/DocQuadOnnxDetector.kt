package com.pixlite.naturalproof

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OnnxValue
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.Log
import java.io.File
import java.io.FileOutputStream
import java.nio.FloatBuffer

/**
 * Minimal port of the document-corner detector from MakeACopy
 * (https://github.com/egdels/makeacopy, Apache License 2.0 -- the whole
 * repository, including the exported ONNX model, is licensed Apache 2.0;
 * see that repo's LICENSE/README "Training data & models" section).
 *
 * Only the ARGMAX baseline post-processing is ported here (MakeACopy's own
 * DocQuadPostprocessor javadoc calls this "M6a", the minimal/deterministic
 * spec). The production mask-fallback + multi-guardrail scoring system in
 * MakeACopy's DocQuadPostprocessor/DocQuadDetector is intentionally not
 * reused -- this is a geometry proof, not a production detector.
 *
 * Model: DocQuadNet-256 (MobileNetV3 backbone + FPN), input 256x256x3 RGB
 * float32 [0,1] letterboxed with mid-gray padding, outputs
 * "corner_heatmaps" [1,4,64,64] (TL,TR,BR,BL) and "mask_logits" [1,1,64,64]
 * (unused here). Asset: docquad/docquadnet256_trained_opset17.ort.
 */
object DocQuadOnnxDetector {

    private const val TAG = "DocQuadOnnxDetector"
    const val MODEL_ASSET = "docquad/docquadnet256_trained_opset17.ort"
    const val IN_W = 256
    const val IN_H = 256
    private const val OUT_W = 64
    private const val OUT_H = 64
    private const val LETTERBOX_PAD_COLOR = 0xFF808080.toInt()

    private var env: OrtEnvironment? = null
    private var session: OrtSession? = null

    data class DetectionResult(
        /** TL, TR, BR, BL, each a fraction of the source bitmap's width/height. */
        val cornersFraction: List<PointF>,
        val confident: Boolean
    )

    private class Letterbox(
        val srcW: Int, val srcH: Int,
        val scale: Double, val offsetX: Double, val offsetY: Double
    ) {
        fun inverse(x: Double, y: Double): DoubleArray =
            doubleArrayOf((x - offsetX) / scale, (y - offsetY) / scale)

        companion object {
            fun create(srcW: Int, srcH: Int): Letterbox {
                val s = minOf(IN_W.toDouble() / srcW, IN_H.toDouble() / srcH)
                val newW = srcW * s
                val newH = srcH * s
                val ox = (IN_W - newW) / 2.0
                val oy = (IN_H - newH) / 2.0
                return Letterbox(srcW, srcH, s, ox, oy)
            }
        }
    }

    @Synchronized
    private fun ensureLoaded(context: Context) {
        if (session != null) return
        val e = OrtEnvironment.getEnvironment()
        val modelFile = copyAssetToCache(context, MODEL_ASSET)
        val opts = OrtSession.SessionOptions()
        val s: OrtSession
        try {
            s = e.createSession(modelFile.absolutePath, opts)
        } finally {
            opts.close()
        }
        env = e
        session = s
        Log.i(TAG, "DocQuadNet-256 ONNX model loaded from ${modelFile.absolutePath}")
    }

    private fun copyAssetToCache(context: Context, assetPath: String): File {
        val baseName = File(assetPath).name
        val outFile = File(context.cacheDir, baseName)
        if (!outFile.exists()) {
            context.assets.open(assetPath).use { input ->
                FileOutputStream(outFile).use { output ->
                    val buffer = ByteArray(256 * 1024)
                    while (true) {
                        val n = input.read(buffer)
                        if (n < 0) break
                        output.write(buffer, 0, n)
                    }
                }
            }
        }
        return outFile
    }

    private fun renderLetterbox(src: Bitmap, lb: Letterbox): Bitmap {
        val out = Bitmap.createBitmap(IN_W, IN_H, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(out)
        canvas.drawColor(LETTERBOX_PAD_COLOR)
        val left = lb.offsetX.toFloat()
        val top = lb.offsetY.toFloat()
        val right = (lb.offsetX + src.width * lb.scale).toFloat()
        val bottom = (lb.offsetY + src.height * lb.scale).toFloat()
        val paint = Paint().apply {
            isFilterBitmap = true
            isDither = true
            isAntiAlias = true
        }
        canvas.drawBitmap(src, null, RectF(left, top, right, bottom), paint)
        return out
    }

    /** Preprocess exactly as MakeACopy trains it: RGB, 0..1, NCHW float32. */
    private fun bitmapToNchwFloat01(bmp: Bitmap): FloatArray {
        val w = bmp.width
        val h = bmp.height
        val hw = h * w
        val out = FloatArray(3 * hw)
        val px = IntArray(hw)
        bmp.getPixels(px, 0, w, 0, 0, w, h)
        for (i in 0 until hw) {
            val c = px[i]
            out[i] = ((c shr 16) and 0xFF) / 255.0f
            out[hw + i] = ((c shr 8) and 0xFF) / 255.0f
            out[2 * hw + i] = (c and 0xFF) / 255.0f
        }
        return out
    }

    private fun defaultCorners(): List<PointF> =
        listOf(PointF(0f, 0f), PointF(1f, 0f), PointF(1f, 1f), PointF(0f, 1f))

    /**
     * Returns true iff the four corners form a strictly convex,
     * non-self-intersecting quadrilateral traversed in TL->TR->BR->BL order
     * (clockwise in image coordinates where y grows downward). Ported from
     * MakeACopy's DocQuadDetector.isConvexTLTRBRBL.
     */
    private fun isConvexTlTrBrBl(c: List<PointF>): Boolean {
        if (c.size != 4) return false
        var prevSign = 0.0
        for (i in 0 until 4) {
            val a = c[i]
            val b = c[(i + 1) % 4]
            val d = c[(i + 2) % 4]
            val abx = b.x - a.x
            val aby = b.y - a.y
            val bdx = d.x - b.x
            val bdy = d.y - b.y
            val cross = (abx * bdy - aby * bdx).toDouble()
            if (!cross.isFinite() || cross == 0.0) return false
            val sign = Math.signum(cross)
            if (i == 0) {
                if (sign < 0.0) return false
                prevSign = sign
            } else if (sign != prevSign) {
                return false
            }
        }
        return true
    }

    /**
     * Runs the model on [workBitmap] (caller may pass a downsized copy for
     * speed -- detection always letterboxes internally to a fixed 256x256
     * regardless of input size). Returns TL,TR,BR,BL as fractions of that
     * same bitmap.
     */
    fun detect(context: Context, workBitmap: Bitmap): DetectionResult {
        try {
            ensureLoaded(context)
        } catch (t: Throwable) {
            Log.e(TAG, "Failed to load ONNX model", t)
            return DetectionResult(defaultCorners(), false)
        }
        val s = session ?: return DetectionResult(defaultCorners(), false)
        val e = env ?: return DetectionResult(defaultCorners(), false)

        var letterboxed: Bitmap? = null
        var inputTensor: OnnxTensor? = null
        var results: OrtSession.Result? = null
        try {
            val lb = Letterbox.create(workBitmap.width, workBitmap.height)
            letterboxed = renderLetterbox(workBitmap, lb)
            val inputArray = bitmapToNchwFloat01(letterboxed)

            val shape = longArrayOf(1, 3, IN_H.toLong(), IN_W.toLong())
            inputTensor = OnnxTensor.createTensor(e, FloatBuffer.wrap(inputArray), shape)

            results = s.run(mapOf("input" to inputTensor))

            val cornerHeatmapsValue: OnnxValue = results.get("corner_heatmaps")
                .orElseThrow { IllegalStateException("ONNX output 'corner_heatmaps' missing") }
            @Suppress("UNCHECKED_CAST")
            val cornerHeatmaps = cornerHeatmapsValue.value as Array<Array<Array<FloatArray>>>
            // shape [1][4][64][64]

            val corners256 = Array(4) { DoubleArray(2) }
            for (c in 0 until 4) {
                var best = -Float.MAX_VALUE
                var bx = 0
                var by = 0
                val hm = cornerHeatmaps[0][c]
                for (y in 0 until OUT_H) {
                    val row = hm[y]
                    for (x in 0 until OUT_W) {
                        val v = row[x]
                        if (v > best) {
                            best = v
                            bx = x
                            by = y
                        }
                    }
                }
                corners256[c][0] = (bx + 0.5) * 4.0
                corners256[c][1] = (by + 0.5) * 4.0
            }

            val fractions = corners256.map { p ->
                val orig = lb.inverse(p[0], p[1])
                PointF(
                    (orig[0] / workBitmap.width).toFloat().coerceIn(0f, 1f),
                    (orig[1] / workBitmap.height).toFloat().coerceIn(0f, 1f)
                )
            }

            val confident = isConvexTlTrBrBl(fractions)
            return DetectionResult(if (confident) fractions else defaultCorners(), confident)
        } catch (t: Throwable) {
            Log.e(TAG, "Detection failed", t)
            return DetectionResult(defaultCorners(), false)
        } finally {
            results?.close()
            inputTensor?.close()
            letterboxed?.recycle()
        }
    }
}
