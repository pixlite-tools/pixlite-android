package com.pixlite.naturalproof

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

/**
 * Geometry + ONE conservative "Final Natural" enhancement pipeline. No
 * Document/B&W modes, no aggressive global thresholding, no artificial
 * sharpening beyond a mild unsharp pass on luminance only.
 */
object ScanProcessor {

    /**
     * Classic four-point perspective transform. Must be called with the
     * ORIGINAL-resolution Mat -- corners are fractions (0..1).
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
     * Expands the confirmed quad outward by a small fraction around its own
     * centroid, so a pixel-tight detection never clips text/stamps sitting
     * right at the paper edge. Clamped to the image bounds.
     */
    fun padQuadOutward(corners: List<PointF>, marginFraction: Float): List<PointF> {
        val cx = corners.map { it.x }.average().toFloat()
        val cy = corners.map { it.y }.average().toFloat()
        return corners.map { p ->
            val dx = p.x - cx
            val dy = p.y - cy
            PointF(
                (p.x + dx * marginFraction).coerceIn(0f, 1f),
                (p.y + dy * marginFraction).coerceIn(0f, 1f)
            )
        }
    }

    /**
     * The one exposed "Final Natural" result. Pipeline, in order:
     *
     * 1. Gray-world white balance on BGR -- corrects color cast from indoor
     *    lighting before anything else touches the image.
     * 2. LAB conversion; all further tonal work happens on the L (lightness)
     *    channel only -- A/B (color) channels are left untouched, which is
     *    what keeps blue/red stamp ink and colored signatures from shifting
     *    or fading.
     * 3. Division-based illumination normalization on L: estimate a
     *    large-kernel blurred "background" and divide it out, correcting
     *    uneven shadow/lighting without a global threshold.
     * 4. CLAHE on the normalized L for local text/paper contrast, with a
     *    conservative clip limit to avoid amplifying noise.
     * 5. A mild unsharp pass on L only (low amount, avoids color halos and
     *    avoids thickening/breaking thin Arabic strokes).
     * 6. Merge back with the original A/B, convert to BGR.
     * 7. A very mild bilateral denoise as the last step, small enough to
     *    leave fine character strokes and diacritics intact.
     */
    fun toFinalNatural(bgr: Mat): Mat {
        val wb = grayWorldWhiteBalance(bgr)

        val lab = Mat()
        Imgproc.cvtColor(wb, lab, Imgproc.COLOR_BGR2Lab)
        wb.release()

        val labChannels = mutableListOf<Mat>()
        Core.split(lab, labChannels)
        lab.release()
        val l = labChannels[0]
        val a = labChannels[1]
        val b = labChannels[2]

        val lNorm = normalizeIllumination(l)
        l.release()

        val clahe = Imgproc.createCLAHE(1.5, Size(8.0, 8.0))
        val lClahe = Mat()
        clahe.apply(lNorm, lClahe)
        lNorm.release()

        val lSharp = unsharpMask(lClahe, amount = 0.3, radius = 1.5)
        lClahe.release()

        val mergedLab = Mat()
        Core.merge(listOf(lSharp, a, b), mergedLab)
        lSharp.release(); a.release(); b.release()

        val bgrOut = Mat()
        Imgproc.cvtColor(mergedLab, bgrOut, Imgproc.COLOR_Lab2BGR)
        mergedLab.release()

        val denoised = Mat()
        Imgproc.bilateralFilter(bgrOut, denoised, 5, 25.0, 25.0)
        bgrOut.release()

        return denoised
    }

    /** Simple gray-world white balance with a clamp against extreme correction. */
    private fun grayWorldWhiteBalance(bgr: Mat): Mat {
        val channels = mutableListOf<Mat>()
        Core.split(bgr, channels)
        val means = channels.map { Core.mean(it).`val`[0] }
        val gray = (means[0] + means[1] + means[2]) / 3.0

        val scaled = mutableListOf<Mat>()
        for (i in 0 until 3) {
            val scale = (gray / means[i].coerceAtLeast(1.0)).coerceIn(0.7, 1.4)
            val out = Mat()
            channels[i].convertTo(out, CvType.CV_8U, scale, 0.0)
            scaled.add(out)
            channels[i].release()
        }
        val merged = Mat()
        Core.merge(scaled, merged)
        scaled.forEach { it.release() }
        return merged
    }

    /**
     * Division-normalization background flattening on a single (L) channel:
     * estimate the slow-varying illumination via a large Gaussian blur, then
     * divide it out. The kernel is proportional to image size and
     * deliberately large so it captures only the shadow gradient, not
     * individual glyph strokes -- a kernel that's too tight ends up
     * "learning" the text as part of the background and washing it out,
     * which is what made the old Document/B&W modes destroy text.
     */
    private fun normalizeIllumination(l: Mat): Mat {
        val kernel = (max(l.cols(), l.rows()) / 6)
            .let { if (it % 2 == 0) it + 1 else it }
            .coerceAtLeast(61)
        val background = Mat()
        Imgproc.GaussianBlur(l, background, Size(kernel.toDouble(), kernel.toDouble()), 0.0)
        val bgMean = Core.mean(background).`val`[0]

        val l32 = Mat(); l.convertTo(l32, CvType.CV_32F)
        val bg32 = Mat(); background.convertTo(bg32, CvType.CV_32F)
        background.release()
        Core.add(bg32, Scalar(1.0), bg32) // avoid divide-by-zero

        val ratio = Mat()
        Core.divide(l32, bg32, ratio, bgMean)
        l32.release(); bg32.release()

        val out = Mat()
        ratio.convertTo(out, CvType.CV_8U)
        ratio.release()
        return out
    }

    private fun unsharpMask(src: Mat, amount: Double, radius: Double): Mat {
        val blurred = Mat()
        Imgproc.GaussianBlur(src, blurred, Size(0.0, 0.0), radius)
        val out = Mat()
        Core.addWeighted(src, 1.0 + amount, blurred, -amount, 0.0, out)
        blurred.release()
        return out
    }
}
