package com.pixlite.scannerproof

import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.scannerproof.databinding.ActivityCornerCorrectionBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.opencv.android.Utils
import org.opencv.core.Mat

/**
 * Shows a downscaled preview with a draggable four-corner overlay. Boundary
 * detection runs here (on the downscaled copy per the architecture rule);
 * the confirmed fractional corners are handed to ProcessingActivity, which
 * applies them to the original-resolution image.
 */
class CornerCorrectionActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCornerCorrectionBinding
    private lateinit var originalPath: String

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityCornerCorrectionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        originalPath = intent.getStringExtra(EXTRA_PATH) ?: run { finish(); return }

        val opts = BitmapFactory.Options().apply { inSampleSize = 4 }
        val preview = BitmapFactory.decodeFile(originalPath, opts) ?: run { finish(); return }
        binding.cornerOverlay.setImageBitmap(preview)
        binding.statusText.text = "Detecting document edges…"

        CoroutineScope(Dispatchers.Main).launch {
            val detection = withContext(Dispatchers.Default) {
                val mat = Mat()
                Utils.bitmapToMat(preview, mat)
                val result = BoundaryDetector.detect(mat)
                mat.release()
                result
            }
            binding.cornerOverlay.setCorners(detection.cornersFraction)
            binding.statusText.text = if (detection.confident)
                "Edges detected — drag corners to adjust if needed"
            else
                "Could not detect edges confidently — adjust corners manually"
        }

        binding.resetButton.setOnClickListener { binding.cornerOverlay.resetToFullImage() }
        binding.confirmButton.setOnClickListener {
            ProcessingActivity.start(this, originalPath, binding.cornerOverlay.getCorners())
            finish()
        }
    }

    companion object {
        private const val EXTRA_PATH = "extra_path"

        fun start(context: Context, path: String) {
            context.startActivity(Intent(context, CornerCorrectionActivity::class.java).apply {
                putExtra(EXTRA_PATH, path)
            })
        }
    }
}
