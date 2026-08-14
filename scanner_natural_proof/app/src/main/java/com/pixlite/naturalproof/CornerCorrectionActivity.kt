package com.pixlite.naturalproof

import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.os.Bundle
import android.os.SystemClock
import androidx.appcompat.app.AppCompatActivity
import com.pixlite.naturalproof.databinding.ActivityCornerCorrectionBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Shows a downscaled preview with a draggable four-corner overlay. The ONNX
 * DocQuadNet-256 detector (proved in scanner_geometry_proof/) runs here on
 * that same downscaled copy; the confirmed fractional corners are handed to
 * ProcessingActivity, which applies them to the original-resolution image.
 */
class CornerCorrectionActivity : AppCompatActivity() {

    private lateinit var binding: ActivityCornerCorrectionBinding
    private lateinit var originalPath: String
    private var detectionMs: Long = 0
    private var detectWorkW: Int = 0
    private var detectWorkH: Int = 0

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
        }

        binding.resetButton.setOnClickListener { binding.cornerOverlay.resetToFullImage() }
        binding.confirmButton.setOnClickListener {
            ProcessingActivity.start(
                this,
                originalPath,
                binding.cornerOverlay.getCorners(),
                detectionMs,
                detectWorkW,
                detectWorkH
            )
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
