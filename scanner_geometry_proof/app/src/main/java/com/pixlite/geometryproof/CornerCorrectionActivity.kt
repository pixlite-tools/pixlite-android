package com.pixlite.geometryproof

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.os.Bundle
import android.os.SystemClock
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.geometryproof.databinding.ActivityCornerCorrectionBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

/**
 * Shows a downscaled preview with a draggable four-corner overlay. The ONNX
 * DocQuadNet-256 detector runs here on that same downscaled copy (detection
 * is allowed to run on a downsized copy per the task requirements); the
 * confirmed fractional corners are handed to ProcessingActivity, which
 * applies them to the original-resolution image.
 *
 * Also saves the two visualization exports required by the geometry proof:
 * auto_detected.jpg (raw ONNX output, before any manual touch) and
 * manual_corrected.jpg (whatever the user confirmed, touched or not).
 */
class CornerCorrectionActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCornerCorrectionBinding
    private lateinit var originalPath: String
    private var detectionMs: Long = 0
    private var detectWorkW: Int = 0
    private var detectWorkH: Int = 0
    private var autoDetectedPath: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCornerCorrectionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        originalPath = intent.getStringExtra(EXTRA_PATH) ?: run { finish(); return }

        val opts = BitmapFactory.Options().apply { inSampleSize = 4 }
        val preview = BitmapFactory.decodeFile(originalPath, opts) ?: run { finish(); return }
        detectWorkW = preview.width
        detectWorkH = preview.height
        binding.cornerOverlay.setImageBitmap(preview)
        binding.statusText.text = "Running ONNX document detection…"

        CoroutineScope(Dispatchers.Main).launch {
            val detection = withContext(Dispatchers.Default) {
                val t0 = SystemClock.elapsedRealtime()
                val result = DocQuadOnnxDetector.detect(this@CornerCorrectionActivity, preview)
                detectionMs = SystemClock.elapsedRealtime() - t0
                result
            }
            binding.cornerOverlay.setCorners(detection.cornersFraction)
            binding.statusText.text = if (detection.confident)
                "ONNX detection: ${detectionMs}ms — drag corners to adjust if needed"
            else
                "ONNX detection low-confidence (${detectionMs}ms) — adjust corners manually"

            // Save auto_detected.jpg immediately, before any manual touch.
            withContext(Dispatchers.Default) {
                autoDetectedPath = saveQuadVisualization(
                    originalPath, detection.cornersFraction, "auto_detected.jpg"
                )
            }
        }

        binding.resetButton.setOnClickListener { binding.cornerOverlay.resetToFullImage() }
        binding.confirmButton.setOnClickListener {
            val finalCorners = binding.cornerOverlay.getCorners()
            binding.confirmButton.isEnabled = false
            binding.statusText.text = "Saving manual_corrected.jpg…"
            CoroutineScope(Dispatchers.Main).launch {
                val manualPath = withContext(Dispatchers.Default) {
                    saveQuadVisualization(originalPath, finalCorners, "manual_corrected.jpg")
                }
                ProcessingActivity.start(
                    this@CornerCorrectionActivity,
                    originalPath,
                    finalCorners,
                    detectionMs,
                    detectWorkW,
                    detectWorkH,
                    autoDetectedPath,
                    manualPath
                )
                finish()
            }
        }
    }

    /**
     * Loads a bounded (not full-sensor-resolution, but sharp enough to judge
     * geometry accuracy) copy of the original image and draws the given
     * fractional quad on top of it, saved next to original.jpg.
     */
    private fun saveQuadVisualization(
        originalPath: String,
        corners: List<PointF>,
        filename: String
    ): String {
        val file = File(originalPath)
        val boundsOpts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(originalPath, boundsOpts)
        val longEdge = maxOf(boundsOpts.outWidth, boundsOpts.outHeight)
        var sample = 1
        while (longEdge / (sample * 2) >= RENDER_MAX_DIM) sample *= 2
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        var bmp = BitmapFactory.decodeFile(originalPath, opts)!!
        bmp = ExifUtils.normalizeOrientation(file, bmp)

        val out = bmp.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(out)
        val w = out.width.toFloat()
        val h = out.height.toFloat()
        val pts = corners.map { Pair(it.x * w, it.y * h) }

        val strokeWidth = maxOf(3f, w / 300f)
        val linePaint = Paint().apply {
            color = Color.parseColor("#5FD1C9")
            style = Paint.Style.STROKE
            this.strokeWidth = strokeWidth
            isAntiAlias = true
        }
        val fillPaint = Paint().apply {
            color = Color.parseColor("#335FD1C9")
            style = Paint.Style.FILL
            isAntiAlias = true
        }
        val handlePaint = Paint().apply {
            color = Color.parseColor("#FF3B30")
            style = Paint.Style.FILL
            isAntiAlias = true
        }
        val path = Path()
        path.moveTo(pts[0].first, pts[0].second)
        for (i in 1..3) path.lineTo(pts[i].first, pts[i].second)
        path.close()
        canvas.drawPath(path, fillPaint)
        canvas.drawPath(path, linePaint)
        val handleRadius = maxOf(6f, w / 120f)
        for (p in pts) canvas.drawCircle(p.first, p.second, handleRadius, handlePaint)

        val outFile = File(file.parentFile, filename)
        FileOutputStream(outFile).use { fos ->
            out.compress(Bitmap.CompressFormat.JPEG, 95, fos)
        }
        bmp.recycle()
        out.recycle()
        return outFile.absolutePath
    }

    companion object {
        private const val EXTRA_PATH = "extra_path"
        private const val RENDER_MAX_DIM = 2000.0

        fun start(context: Context, path: String) {
            context.startActivity(Intent(context, CornerCorrectionActivity::class.java).apply {
                putExtra(EXTRA_PATH, path)
            })
        }
    }
}
