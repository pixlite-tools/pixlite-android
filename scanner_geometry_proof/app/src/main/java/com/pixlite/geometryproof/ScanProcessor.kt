package com.pixlite.geometryproof

import org.opencv.core.Mat
import org.opencv.core.MatOfPoint2f
import org.opencv.core.Point
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc
import kotlin.math.hypot
import kotlin.math.max

/**
 * Geometry-only processing. No enhancement/filter stage is included here on
 * purpose -- this proof is scoped to boundary-detection and crop geometry
 * only, per the task requirements.
 */
object ScanProcessor {

    /**
     * Classic four-point perspective transform. Must be called with the
     * ORIGINAL-resolution Mat -- corners are fractions (0..1), so this works
     * correctly regardless of what resolution detection ran at.
     */
    fun fourPointTransform(src: Mat, corners: List<PointF>): Mat {
        val w = src.cols().toDouble()
        val h = src.rows().toDouble()
        val pts = corners.map { Point(it.x * w, it.y * h) } // TL, TR, BR, BL
        val tl = pts[0]; val tr = pts[1]; val br = pts[2]; val bl = pts[3]

        val widthTop = hypot(tr.x - tl.x, tr.y - tl.y)
        val widthBottom = hypot(br.x - bl.x, br.y - bl.y)
        val maxWidth = max(widthTop, widthBottom).toInt().coerceAtLeast(1)

        val heightLeft = hypot(bl.x - tl.x, bl.y - tl.y)
        val heightRight = hypot(br.x - tr.x, br.y - tr.y)
        val maxHeight = max(heightLeft, heightRight).toInt().coerceAtLeast(1)

        val srcMat = MatOfPoint2f(tl, tr, br, bl)
        val dstMat = MatOfPoint2f(
            Point(0.0, 0.0),
            Point((maxWidth - 1).toDouble(), 0.0),
            Point((maxWidth - 1).toDouble(), (maxHeight - 1).toDouble()),
            Point(0.0, (maxHeight - 1).toDouble())
        )

        val transform = Imgproc.getPerspectiveTransform(srcMat, dstMat)
        val warped = Mat()
        Imgproc.warpPerspective(src, warped, transform, Size(maxWidth.toDouble(), maxHeight.toDouble()))

        transform.release(); srcMat.release(); dstMat.release()
        return warped
    }
}
