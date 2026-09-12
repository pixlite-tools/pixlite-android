package com.pixlite.scannerproof

import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.MatOfPoint
import org.opencv.core.MatOfPoint2f
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc

/** Simple float point, expressed as a fraction (0..1) of image width/height. */
data class PointF(val x: Float, val y: Float)

data class DetectionResult(
    /** TL, TR, BR, BL, each a fraction of the source image's width/height. */
    val cornersFraction: List<PointF>,
    val confident: Boolean
)

/**
 * Runs on a downscaled copy only (per architecture rule: analysis/detection
 * may use a downsized copy for speed). Corners are returned as fractions of
 * the frame, so callers can apply them directly to the original-resolution
 * Mat without needing to know the detection scale factor.
 */
object BoundaryDetector {

    private const val WORK_MAX_DIM = 1000.0
    private const val MIN_AREA_FRACTION = 0.15
    private const val MAX_AREA_FRACTION = 0.98

    fun detect(fullResMat: Mat): DetectionResult {
        val longEdge = maxOf(fullResMat.rows(), fullResMat.cols()).toDouble()
        val scale = if (longEdge > WORK_MAX_DIM) WORK_MAX_DIM / longEdge else 1.0

        val work = Mat()
        Imgproc.resize(fullResMat, work, Size(fullResMat.cols() * scale, fullResMat.rows() * scale))

        val gray = Mat()
        Imgproc.cvtColor(work, gray, Imgproc.COLOR_BGR2GRAY)
        Imgproc.GaussianBlur(gray, gray, Size(5.0, 5.0), 0.0)

        val edges = Mat()
        Imgproc.Canny(gray, edges, 50.0, 150.0)
        Imgproc.dilate(edges, edges, Mat.ones(Size(3.0, 3.0), CvType.CV_8U))

        val contours = mutableListOf<MatOfPoint>()
        val hierarchy = Mat()
        Imgproc.findContours(edges, contours, hierarchy, Imgproc.RETR_LIST, Imgproc.CHAIN_APPROX_SIMPLE)

        val frameArea = (work.rows() * work.cols()).toDouble()
        var bestApprox: MatOfPoint2f? = null
        var bestArea = 0.0

        for (c in contours) {
            val area = Imgproc.contourArea(c)
            if (area < frameArea * MIN_AREA_FRACTION) continue

            val c2f = MatOfPoint2f(*c.toArray())
            val peri = Imgproc.arcLength(c2f, true)
            val approx = MatOfPoint2f()
            Imgproc.approxPolyDP(c2f, approx, 0.02 * peri, true)

            if (approx.total() == 4L) {
                val approxInt = MatOfPoint(*approx.toArray())
                if (Imgproc.isContourConvex(approxInt) && area > bestArea) {
                    bestArea = area
                    bestApprox = approx
                }
            }
        }

        val confident = bestApprox != null &&
            bestArea > frameArea * MIN_AREA_FRACTION &&
            bestArea < frameArea * MAX_AREA_FRACTION

        val corners: List<PointF> = if (confident) {
            val pts = bestApprox!!.toArray().map {
                PointF((it.x / work.cols()).toFloat(), (it.y / work.rows()).toFloat())
            }
            orderCorners(pts)
        } else {
            // Low confidence: keep the full frame rather than guessing a
            // destructive crop. The user corrects manually from here.
            listOf(PointF(0f, 0f), PointF(1f, 0f), PointF(1f, 1f), PointF(0f, 1f))
        }

        gray.release()
        edges.release()
        hierarchy.release()
        work.release()

        return DetectionResult(corners, confident)
    }

    private fun orderCorners(pts: List<PointF>): List<PointF> {
        val sums = pts.map { it.x + it.y }
        val diffs = pts.map { it.x - it.y }
        val tl = pts[sums.indexOf(sums.min())]
        val br = pts[sums.indexOf(sums.max())]
        val tr = pts[diffs.indexOf(diffs.max())]
        val bl = pts[diffs.indexOf(diffs.min())]
        return listOf(tl, tr, br, bl)
    }
}
