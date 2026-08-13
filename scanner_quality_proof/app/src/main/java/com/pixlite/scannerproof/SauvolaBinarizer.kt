package com.pixlite.scannerproof

import org.opencv.core.Core
import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.Scalar
import org.opencv.core.Size
import org.opencv.imgproc.Imgproc
import kotlin.math.max

/**
 * Sauvola adaptive binarization, implemented with vectorized OpenCV box-filter
 * operations (no manual per-pixel loop), so it stays fast enough to run off
 * the UI thread without becoming its own bottleneck on a multi-megapixel
 * image. Chosen over OpenCV's built-in adaptiveThreshold because Sauvola's
 * local-stddev term holds thin/curved strokes -- e.g. Arabic letterforms --
 * far better than a flat local-mean threshold.
 */
object SauvolaBinarizer {

    private const val K = 0.34
    private const val R = 128.0

    fun binarize(gray: Mat): Mat {
        val windowSize = (max(gray.cols(), gray.rows()) / 60)
            .let { if (it % 2 == 0) it + 1 else it }
            .coerceAtLeast(15)
        val winSizeD = Size(windowSize.toDouble(), windowSize.toDouble())

        val gray32 = Mat()
        gray.convertTo(gray32, CvType.CV_32F)

        val mean = Mat()
        Imgproc.boxFilter(gray32, mean, CvType.CV_32F, winSizeD)

        val sq = Mat()
        Core.multiply(gray32, gray32, sq)
        val meanSq = Mat()
        Imgproc.boxFilter(sq, meanSq, CvType.CV_32F, winSizeD)

        val meanSquared = Mat()
        Core.multiply(mean, mean, meanSquared)
        val variance = Mat()
        Core.subtract(meanSq, meanSquared, variance)
        Core.max(variance, Scalar(0.0), variance)
        val stddev = Mat()
        Core.sqrt(variance, stddev)

        // threshold = mean * (1 + k * (stddev / R - 1))
        val stddevTerm = Mat()
        Core.divide(stddev, Scalar(R), stddevTerm)
        Core.subtract(stddevTerm, Scalar(1.0), stddevTerm)
        Core.multiply(stddevTerm, Scalar(K), stddevTerm)
        Core.add(stddevTerm, Scalar(1.0), stddevTerm)
        val threshold = Mat()
        Core.multiply(mean, stddevTerm, threshold)

        val result = Mat()
        Core.compare(gray32, threshold, result, Core.CMP_GT)

        gray32.release(); mean.release(); sq.release(); meanSq.release()
        meanSquared.release(); variance.release(); stddev.release()
        stddevTerm.release(); threshold.release()

        return result
    }
}
