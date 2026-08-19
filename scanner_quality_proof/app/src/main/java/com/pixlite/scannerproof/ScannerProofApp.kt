package com.pixlite.scannerproof

import android.app.Application
import android.util.Log
import org.opencv.android.OpenCVLoader

class ScannerProofApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val ok = OpenCVLoader.initLocal()
        Log.i("ScannerProof", "OpenCV native init success=$ok")
    }
}
