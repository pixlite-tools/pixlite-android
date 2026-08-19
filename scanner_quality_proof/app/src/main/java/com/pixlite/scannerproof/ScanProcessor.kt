package com.pixlite.scannerproof

import org.opencv.core.Core
import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.MatOfPoint2f
import org.opencv.core.Point
import org.opencv.core.Scalar
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc
import kotlin.math.hypot
import kotlin.math.max

object ScanProcessor {

    /**
     * Classic four-point perspective transform. Must be called with the
     * ORIGINAL-resolution Mat -- corners are fractions (0..1), so this works
     * correctly regardless of what resolution boundary detection ran at.
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

    /**
     * Flat-fields illumination on a color (BGR) Mat using a shared background
     * estimate derived from luminance, so shadow/uneven-background correction
     * does not shift color balance -- this is what keeps Natural mode's
     * colors honest instead of tinting the whole page.
     */
    fun correctIllumination(bgr: Mat): Mat {
        val gray = Mat()
        Imgproc.cvtColor(bgr, gray, Imgproc.COLOR_BGR2GRAY)

        val kernel = (max(bgr.cols(), bgr.rows()) / 15)
            .let { if (it % 2 == 0) it + 1 else it }
            .coerceAtLeast(31)
        val background = Mat()
        Imgproc.GaussianBlur(gray, background, Size(kernel.toDouble(), kernel.toDouble()), 0.0)

        val bg32 = Mat()
        background.convertTo(bg32, CvType.CV_32F)
        Core.add(bg32, Scalar(1.0), bg32) // avoid divide-by-zero on pure-black background pixels

        val channels = mutableListOf<Mat>()
        Core.split(bgr, channels)

        val corrected = mutableListOf<Mat>()
        for (ch in channels) {
            val ch32 = Mat()
            ch.convertTo(ch32, CvType.CV_32F)
            val out32 = Mat()
            Core.divide(ch32, bg32, out32, 255.0)
            val out8 = Mat()
            out32.convertTo(out8, CvType.CV_8U)
            corrected.add(out8)
            ch.release(); ch32.release(); out32.release()
        }

        val result = Mat()
        Core.merge(corrected, result)

        gray.release(); background.release(); bg32.release()
        corrected.forEach { it.release() }
        channels.forEach { it.release() }

        return result
    }

    fun sharpen(src: Mat, amount: Double, radius: Double = 1.2): Mat {
        val blurred = Mat()
        Imgproc.GaussianBlur(src, blurred, Size(0.0, 0.0), radius)
        val out = Mat()
        Core.addWeighted(src, 1.0 + amount, blurred, -amount, 0.0, out)
        blurred.release()
        return out
    }

    /** Stays in color, illumination-corrected only, one mild sharpen pass. */
    fun toNatural(illuminationCorrected: Mat): Mat {
        return sharpen(illuminationCorrected, amount = 0.25)
    }

    /** Desaturated AFTER illumination correction, small-tile CLAHE, one sharpen pass. */
    fun toDocument(illuminationCorrected: Mat): Mat {
        val gray = Mat()
        Imgproc.cvtColor(illuminationCorrected, gray, Imgproc.COLOR_BGR2GRAY)
        val clahe = Imgproc.createCLAHE(1.2, Size(8.0, 8.0))
        val equalized = Mat()
        clahe.apply(gray, equalized)
        val out = sharpen(equalized, amount = 0.4, radius = 1.0)
        gray.release(); equalized.release()
        return out
    }

    /** Sauvola adaptive binarization on the illumination-corrected grayscale. */
    fun toBW(illuminationCorrected: Mat): Mat {
        val gray = Mat()
        Imgproc.cvtColor(illuminationCorrected, gray, Imgproc.COLOR_BGR2GRAY)
        val out = SauvolaBinarizer.binarize(gray)
        gray.release()
        return out
    }
}
