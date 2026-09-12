package com.pixlite.naturalproof

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.naturalproof.databinding.ActivityProcessingBinding
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

data class ScanTimings(
    val cropDetectionMs: Long,
    val enhancementMs: Long,
    val totalMs: Long
) : Serializable

data class ScanResult(
    val originalPath: String,
    val originalDims: Dimensions,
    val finalPath: String,
    val finalDims: Dimensions,
    val timings: ScanTimings
) : Serializable

/**
 * Perspective correction (on the full-resolution original) followed by the
 * ONE "Final Natural" enhancement pipeline -- no Document/B&W modes. Runs
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

        binding.progressText.text = "Starting…"

        CoroutineScope(Dispatchers.Main).launch {
            val result = withContext(Dispatchers.Default) {
                runPipeline(originalPath, corners, detectionMs) { label ->
                    runOnUiThread { binding.progressText.text = label }
                }
            }
            ResultActivity.start(this@ProcessingActivity, result)
            finish()
        }
    }

    private fun runPipeline(
        originalPath: String,
        corners: List<PointF>,
        detectionMs: Long,
        onStage: (String) -> Unit
    ): ScanResult {
        val originalFile = File(originalPath)
        val sessionDir = originalFile.parentFile!!

        onStage("Reading original + normalizing orientation")
        val trueBounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(originalPath, trueBounds)
        val originalDims = Dimensions(trueBounds.outWidth, trueBounds.outHeight)

        var bmp = loadBoundedBitmap(originalFile)
        bmp = ExifUtils.normalizeOrientation(originalFile, bmp)

        val workingMat = Mat()
        Utils.bitmapToMat(bmp, workingMat)
        Imgproc.cvtColor(workingMat, workingMat, Imgproc.COLOR_RGBA2BGR)
        // loadBoundedBitmap caps the long edge at MAX_PROCESSING_DIM, far
        // above any current phone's still-capture resolution -- in practice
        // this Mat *is* the original captured image, unresized.

        onStage("Perspective correction (original resolution)")
        val t0 = System.nanoTime()
        val safeCorners = ScanProcessor.padQuadOutward(corners, CROP_SAFETY_MARGIN)
        val warped = ScanProcessor.fourPointTransform(workingMat, safeCorners)
        workingMat.release()
        val warpMs = (System.nanoTime() - t0) / 1_000_000

        onStage("Final Natural enhancement")
        val t1 = System.nanoTime()
        val natural = ScanProcessor.toFinalNatural(warped)
        warped.release()
        val enhanceMs = (System.nanoTime() - t1) / 1_000_000

        onStage("Saving final_natural.jpg")
        val finalPath = saveMat(natural, sessionDir, "final_natural.jpg")
        val finalDims = Dimensions(natural.cols(), natural.rows())
        natural.release()

        val cropDetectionMs = detectionMs + warpMs
        val totalMs = cropDetectionMs + enhanceMs

        Log.i(
            "NaturalProof",
            "original=${originalDims.width}x${originalDims.height} " +
                "final=${finalDims.width}x${finalDims.height} " +
                "crop_detection_ms=$cropDetectionMs (onnx=$detectionMs warp=$warpMs) " +
                "enhancement_ms=$enhanceMs total_ms=$totalMs"
        )

        return ScanResult(
            originalPath = originalPath,
            originalDims = originalDims,
            finalPath = finalPath,
            finalDims = finalDims,
            timings = ScanTimings(cropDetectionMs, enhanceMs, totalMs)
        )
    }

    /**
     * Decodes without ever materializing more than MAX_PROCESSING_DIM in
     * memory via inSampleSize. The file on disk is never touched -- this
     * only bounds the in-memory working copy used for the full pipeline.
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
        private const val MAX_PROCESSING_DIM = 4800.0
        private const val CROP_SAFETY_MARGIN = 0.02f

        fun start(
            context: Context,
            originalPath: String,
            corners: List<PointF>,
            detectionMs: Long,
            detectWorkW: Int,
            detectWorkH: Int
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
            })
        }
    }
}
