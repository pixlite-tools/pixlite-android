package com.pixlite.geometryproof

import android.app.Application
import android.util.Log
import org.opencv.android.OpenCVLoader

class GeometryProofApp : Application() {
    override fun onCreate() {
        super.onCreate()
        val ok = OpenCVLoader.initLocal()
        Log.i("GeometryProof", "OpenCV native init success=$ok")
    }
}
