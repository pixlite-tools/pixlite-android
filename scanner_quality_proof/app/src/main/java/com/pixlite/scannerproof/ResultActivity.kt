package com.pixlite.scannerproof

import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.pixlite.scannerproof.databinding.ActivityResultBinding
import java.io.File

class ResultActivity : AppCompatActivity() {

    private lateinit var binding: ActivityResultBinding
    private var outputs: List<ProcessOutput> = emptyList()
    private var current = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityResultBinding.inflate(layoutInflater)
        setContentView(binding.root)

        @Suppress("UNCHECKED_CAST")
        outputs = intent.getSerializableExtra(EXTRA_OUTPUTS) as? ArrayList<ProcessOutput> ?: arrayListOf()
        @Suppress("UNCHECKED_CAST")
        val stages = intent.getSerializableExtra(EXTRA_STAGES) as? ArrayList<StageTimer.Stage> ?: arrayListOf()
        val totalMs = intent.getLongExtra(EXTRA_TOTAL_MS, 0)

        val buttons = listOf(binding.btnOriginal, binding.btnNatural, binding.btnDocument, binding.btnBw)
        buttons.forEachIndexed { i, b -> b.setOnClickListener { show(i) } }

        binding.timingText.text = buildString {
            append("Stage timings:\n")
            stages.forEach { append("  ${it.name}: ${it.ms} ms\n") }
            append("Total: $totalMs ms")
        }

        binding.shareButton.setOnClickListener { shareCurrent() }

        show(0)
    }

    private fun show(index: Int) {
        if (index !in outputs.indices) return
        current = index
        val out = outputs[index]
        val bmp = BitmapFactory.decodeFile(out.path)
        binding.zoomImage.setImageBitmap(bmp)
        binding.zoomImage.post { binding.zoomImage.resetZoom() }
        binding.dimensionsText.text = "${out.label}: ${out.dimensions.width} x ${out.dimensions.height} px"
    }

    private fun shareCurrent() {
        val out = outputs.getOrNull(current) ?: return
        val file = File(out.path)
        val uri: Uri = FileProvider.getUriForFile(this, "com.pixlite.scannerproof.fileprovider", file)
        val sendIntent = Intent(Intent.ACTION_SEND).apply {
            type = if (file.extension == "png") "image/png" else "image/jpeg"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(sendIntent, "Share ${out.label}"))
    }

    companion object {
        private const val EXTRA_OUTPUTS = "extra_outputs"
        private const val EXTRA_STAGES = "extra_stages"
        private const val EXTRA_TOTAL_MS = "extra_total_ms"

        fun start(
            context: Context,
            outputs: List<ProcessOutput>,
            stages: List<StageTimer.Stage>,
            totalMs: Long
        ) {
            context.startActivity(Intent(context, ResultActivity::class.java).apply {
                putExtra(EXTRA_OUTPUTS, ArrayList(outputs))
                putExtra(EXTRA_STAGES, ArrayList(stages))
                putExtra(EXTRA_TOTAL_MS, totalMs)
            })
        }
    }
}
