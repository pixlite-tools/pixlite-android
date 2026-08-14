package com.pixlite.naturalproof

import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.pixlite.naturalproof.databinding.ActivityResultBinding
import java.io.File

class ResultActivity : AppCompatActivity() {

    private lateinit var binding: ActivityResultBinding
    private lateinit var result: ScanResult
    private var showingFinal = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityResultBinding.inflate(layoutInflater)
        setContentView(binding.root)

        result = intent.getSerializableExtra(EXTRA_RESULT) as? ScanResult ?: run { finish(); return }

        binding.btnOriginal.setOnClickListener { showingFinal = false; show() }
        binding.btnFinalNatural.setOnClickListener { showingFinal = true; show() }
        binding.shareButton.setOnClickListener { shareCurrent() }

        binding.statsText.text = buildString {
            append("Original dimensions:  ${result.originalDims.width} x ${result.originalDims.height} px\n")
            append("Final dimensions:     ${result.finalDims.width} x ${result.finalDims.height} px\n\n")
            append("Crop/detection time:  ${result.timings.cropDetectionMs} ms\n")
            append("Enhancement time:     ${result.timings.enhancementMs} ms\n")
            append("Total processing:     ${result.timings.totalMs} ms\n")
        }

        show()
    }

    private fun show() {
        val path = if (showingFinal) result.finalPath else result.originalPath
        val bmp = BitmapFactory.decodeFile(path)
        binding.zoomImage.setImageBitmap(bmp)
        binding.zoomImage.post { binding.zoomImage.resetZoom() }
    }

    private fun shareCurrent() {
        val path = if (showingFinal) result.finalPath else result.originalPath
        val file = File(path)
        val uri: Uri = FileProvider.getUriForFile(this, "com.pixlite.naturalproof.fileprovider", file)
        val sendIntent = Intent(Intent.ACTION_SEND).apply {
            type = "image/jpeg"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(sendIntent, if (showingFinal) "Share Final Natural" else "Share Original"))
    }

    companion object {
        private const val EXTRA_RESULT = "extra_result"

        fun start(context: Context, result: ScanResult) {
            context.startActivity(Intent(context, ResultActivity::class.java).apply {
                putExtra(EXTRA_RESULT, result)
            })
        }
    }
}
