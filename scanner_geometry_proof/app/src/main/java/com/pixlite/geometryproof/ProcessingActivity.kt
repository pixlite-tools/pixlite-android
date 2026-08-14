package com.pixlite.geometryproof

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.geometryproof.databinding.ActivityProcessingBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.opencv.android.Utils
import org.opencv.core.Mat
import org.opencv.core.MatOfInt
import org.opencv.imgcodecs.Imgcodecs
import org.opencv.imgproc.Imgproc
import java.io.File
import java.io.Serializable

data class Dimensions(val width: Int, val height: Int) : Serializable

data class ProcessOutput(
    val label: String,
    val path: String,
    val dimensions: Dimensions
) : Serializable

/**
 * Perspective correction only -- deliberately no enhancement/filter stage
 * (illumination correction, sharpening, binarization, etc.), per the task
 * scope: this proof evaluates boundary-detection geometry only. Runs
 * entirely on Dispatchers.Default, off the main/UI thread.
 */
class ProcessingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityProcessingBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProcessingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val originalPath = intent.getStringExtra(EXTRA_PATH) ?: run { finish(); return }
        val cornersFlat = intent.getFloatArrayExtra(EXTRA_CORNERS) ?: run { finish(); return }
        val corners = (0 until 4).map { PointF(cornersFlat[it * 2], cornersFlat[it * 2 + 1]) }
        val detectionMs = intent.getLongExtra(EXTRA_DETECTION_MS, 0)
        val detectWorkW = intent.getIntExtra(EXTRA_DETECT_W, 0)
        val detectWorkH = intent.getIntExtra(EXTRA_DETECT_H, 0)
        val autoDetectedPath = intent.getStringExtra(EXTRA_AUTO_PATH)
        val manualCorrectedPath = intent.getStringExtra(EXTRA_MANUAL_PATH)

        binding.progressText.text = "Starting…"

        CoroutineScope(Dispatchers.Main).launch {
            val (outputs, stages, totalMs) = withContext(Dispatchers.Default) {
                runPipeline(
                    originalPath, corners, detectionMs, detectWorkW, detectWorkH,
                    autoDetectedPath, manualCorrectedPath
                ) { label -> runOnUiThread { binding.progressText.text = label } }
            }
            ResultActivity.start(this@ProcessingActivity, outputs, stages, totalMs)
            finish()
        }
    }

    private fun runPipeline(
        originalPath: String,
        corners: List<PointF>,
        detectionMs: Long,
        detectWorkW: Int,
        detectWorkH: Int,
        autoDetectedPath: String?,
        manualCorrectedPath: String?,
        onStage: (String) -> Unit
    ): Triple<List<ProcessOutput>, List<StageTimer.Stage>, Long> {
        val timer = StageTimer()
        val originalFile = File(originalPath)
        val sessionDir = originalFile.parentFile!!
        val outputs = mutableListOf<ProcessOutput>()

        onStage("Reading original + normalizing orientation")
        val trueBounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(originalPath, trueBounds)
        outputs.add(
            ProcessOutput("Original", originalPath, Dimensions(trueBounds.outWidth, trueBounds.outHeight))
        )

        if (autoDetectedPath != null) {
            outputs.add(ProcessOutput("Auto-detected", autoDetectedPath, boundsOf(autoDetectedPath)))
        }
        if (manualCorrectedPath != null) {
            outputs.add(ProcessOutput("Manual-corrected", manualCorrectedPath, boundsOf(manualCorrectedPath)))
        }

        var bmp = loadBoundedBitmap(originalFile)
        bmp = ExifUtils.normalizeOrientation(originalFile, bmp)

        val workingMat = Mat()
        Utils.bitmapToMat(bmp, workingMat)
        Imgproc.cvtColor(workingMat, workingMat, Imgproc.COLOR_RGBA2BGR)
        // loadBoundedBitmap already caps the long edge at MAX_PROCESSING_DIM,
        // which is far above any current phone's still-capture resolution --
        // in practice this Mat *is* the original captured image, unresized.
        timer.mark("load_exif_bound")

        onStage("Perspective correction (original resolution)")
        val warped = ScanProcessor.fourPointTransform(workingMat, corners)
        timer.mark("perspective_warp")

        onStage("Saving perspective_result.jpg")
        val resultPath = saveMat(warped, sessionDir, "perspective_result.jpg")
        outputs.add(
            ProcessOutput("Perspective-result", resultPath, Dimensions(warped.cols(), warped.rows()))
        )

        workingMat.release(); warped.release()

        val results = mutableListOf(
            StageTimer.Stage("onnx_detection", detectionMs)
        )
        results.addAll(timer.results())
        val total = detectionMs + timer.totalMs()

        Log.i(
            "GeometryProof",
            "detect_input=${detectWorkW}x${detectWorkH}->256x256 stages=$results totalMs=$total"
        )

        return Triple(outputs, results, total)
    }

    private fun boundsOf(path: String): Dimensions {
        val opts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(path, opts)
        return Dimensions(opts.outWidth, opts.outHeight)
    }

    /**
     * Decodes without ever materializing more than MAX_PROCESSING_DIM in
     * memory via inSampleSize, leaving only a final precise resize step if
     * needed. The file on disk is never touched -- this only bounds the
     * in-memory working copy used for perspective correction.
     */
    private fun loadBoundedBitmap(file: File): Bitmap {
        val boundsOpts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(file.absolutePath, boundsOpts)
        val longEdge = maxOf(boundsOpts.outWidth, boundsOpts.outHeight)
        var sample = 1
        while (longEdge / (sample * 2) >= MAX_PROCESSING_DIM) sample *= 2
        val opts = BitmapFactory.Options().apply { inSampleSize = sample }
        return BitmapFactory.decodeFile(file.absolutePath, opts)!!
    }

    private fun saveMat(mat: Mat, dir: File, filename: String): String {
        val file = File(dir, filename)
        val params = MatOfInt(Imgcodecs.IMWRITE_JPEG_QUALITY, 95)
        Imgcodecs.imwrite(file.absolutePath, mat, params)
        return file.absolutePath
    }

    companion object {
        private const val EXTRA_PATH = "extra_path"
        private const val EXTRA_CORNERS = "extra_corners"
        private const val EXTRA_DETECTION_MS = "extra_detection_ms"
        private const val EXTRA_DETECT_W = "extra_detect_w"
        private const val EXTRA_DETECT_H = "extra_detect_h"
        private const val EXTRA_AUTO_PATH = "extra_auto_path"
        private const val EXTRA_MANUAL_PATH = "extra_manual_path"
        private const val MAX_PROCESSING_DIM = 4800.0

        fun start(
            context: Context,
            originalPath: String,
            corners: List<PointF>,
            detectionMs: Long,
            detectWorkW: Int,
            detectWorkH: Int,
            autoDetectedPath: String?,
            manualCorrectedPath: String?
        ) {
            val flat = FloatArray(8)
            for (i in 0 until 4) {
                flat[i * 2] = corners[i].x
                flat[i * 2 + 1] = corners[i].y
            }
            context.startActivity(Intent(context, ProcessingActivity::class.java).apply {
                putExtra(EXTRA_PATH, originalPath)
                putExtra(EXTRA_CORNERS, flat)
                putExtra(EXTRA_DETECTION_MS, detectionMs)
                putExtra(EXTRA_DETECT_W, detectWorkW)
                putExtra(EXTRA_DETECT_H, detectWorkH)
                putExtra(EXTRA_AUTO_PATH, autoDetectedPath)
                putExtra(EXTRA_MANUAL_PATH, manualCorrectedPath)
            })
        }
    }
}
