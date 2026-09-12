package com.pixlite.scannerproof

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.scannerproof.databinding.ActivityProcessingBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.opencv.android.Utils
import org.opencv.core.Mat
import org.opencv.core.MatOfInt
import org.opencv.core.Size
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
 * Runs the full pipeline entirely on Dispatchers.Default -- off the Flutter-
 * equivalent UI thread here, off Android's main thread -- so heavy OpenCV
 * calls cannot freeze the app. This is the structural fix for the ANR found
 * in the Phase 1 audit of the existing PixLite build.
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

        binding.progressText.text = "Starting…"

        CoroutineScope(Dispatchers.Main).launch {
            val (outputs, stages, totalMs) = withContext(Dispatchers.Default) {
                runPipeline(originalPath, corners) { label ->
                    runOnUiThread { binding.progressText.text = label }
                }
            }
            ResultActivity.start(this@ProcessingActivity, outputs, stages, totalMs)
            finish()
        }
    }

    private fun runPipeline(
        originalPath: String,
        corners: List<PointF>,
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

        var bmp = loadBoundedBitmap(originalFile)
        bmp = ExifUtils.normalizeOrientation(originalFile, bmp)

        var workingMat = Mat()
        Utils.bitmapToMat(bmp, workingMat)
        Imgproc.cvtColor(workingMat, workingMat, Imgproc.COLOR_RGBA2BGR)

        val longEdgeNow = maxOf(workingMat.cols(), workingMat.rows()).toDouble()
        if (longEdgeNow > MAX_PROCESSING_DIM) {
            val s = MAX_PROCESSING_DIM / longEdgeNow
            val resized = Mat()
            Imgproc.resize(workingMat, resized, Size(workingMat.cols() * s, workingMat.rows() * s))
            workingMat.release()
            workingMat = resized
        }
        val originalMat = workingMat
        timer.mark("load_exif_bound")

        onStage("Perspective correction (working resolution)")
        val warped = ScanProcessor.fourPointTransform(originalMat, corners)
        timer.mark("perspective_warp")

        onStage("Illumination correction")
        val illuminated = ScanProcessor.correctIllumination(warped)
        timer.mark("illumination")

        onStage("Rendering Natural")
        val natural = ScanProcessor.toNatural(illuminated)
        val naturalPath = saveMat(natural, sessionDir, "natural.jpg")
        timer.mark("natural")
        outputs.add(ProcessOutput("Natural", naturalPath, Dimensions(natural.cols(), natural.rows())))

        onStage("Rendering Document")
        val document = ScanProcessor.toDocument(illuminated)
        val documentPath = saveMat(document, sessionDir, "document.jpg")
        timer.mark("document")
        outputs.add(ProcessOutput("Document", documentPath, Dimensions(document.cols(), document.rows())))

        onStage("Rendering B&W (Sauvola)")
        val bw = ScanProcessor.toBW(illuminated)
        val bwPath = saveMat(bw, sessionDir, "bw.png")
        timer.mark("bw_sauvola")
        outputs.add(ProcessOutput("B&W", bwPath, Dimensions(bw.cols(), bw.rows())))

        originalMat.release(); warped.release(); illuminated.release()
        natural.release(); document.release(); bw.release()

        val results = timer.results()
        val total = timer.totalMs()
        Log.i("ScannerProof", "Stage timings: $results totalMs=$total")

        return Triple(outputs, results, total)
    }

    /**
     * Decodes without ever materializing the full sensor-resolution bitmap
     * in memory: subsamples down to close to MAX_PROCESSING_DIM first via
     * inSampleSize, leaving only a final precise resize on the Mat. The file
     * on disk is never touched -- this only bounds the in-memory working copy.
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
        if (filename.endsWith(".jpg")) {
            val params = MatOfInt(Imgcodecs.IMWRITE_JPEG_QUALITY, 95)
            Imgcodecs.imwrite(file.absolutePath, mat, params)
        } else {
            Imgcodecs.imwrite(file.absolutePath, mat)
        }
        return file.absolutePath
    }

    companion object {
        private const val EXTRA_PATH = "extra_path"
        private const val EXTRA_CORNERS = "extra_corners"
        private const val MAX_PROCESSING_DIM = 4800.0

        fun start(context: Context, originalPath: String, corners: List<PointF>) {
            val flat = FloatArray(8)
            for (i in 0 until 4) {
                flat[i * 2] = corners[i].x
                flat[i * 2 + 1] = corners[i].y
            }
            context.startActivity(Intent(context, ProcessingActivity::class.java).apply {
                putExtra(EXTRA_PATH, originalPath)
                putExtra(EXTRA_CORNERS, flat)
            })
        }
    }
}
