package com.pixlite.naturalproof

import android.app.Application
import android.util.Log
import org.opencv.android.OpenCVLoader

class NaturalProofApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val ok = OpenCVLoader.initLocal()
        Log.i("NaturalProof", "OpenCV native init success=$ok")
    }
}
