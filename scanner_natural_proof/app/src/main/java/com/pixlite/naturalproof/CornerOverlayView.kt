package com.pixlite.naturalproof

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.Rect
import android.graphics.RectF
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.hypot

/** Simple float point, expressed as a fraction (0..1) of image width/height. */
data class PointF(val x: Float, val y: Float)

/**
 * Draws a bitmap letterboxed to fit the view, with four draggable handles
 * over it. Corners are tracked as fractions (0..1) of the BITMAP, not the
 * view, so the same values apply unchanged whether this is showing a
 * downscaled preview or the full-resolution image -- the caller multiplies
 * by the ORIGINAL image's real pixel dimensions later.
 */
class CornerOverlayView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : View(context, attrs) {

    private var bitmap: Bitmap? = null
    private var corners: MutableList<PointF> = mutableListOf(
        PointF(0.1f, 0.1f), PointF(0.9f, 0.1f), PointF(0.9f, 0.9f), PointF(0.1f, 0.9f)
    )
    private var activeHandle = -1

    private var imgLeft = 0f
    private var imgTop = 0f
    private var imgScale = 1f

    private val linePaint = Paint().apply {
        color = Color.parseColor("#5FD1C9")
        strokeWidth = 5f
        style = Paint.Style.STROKE
        isAntiAlias = true
    }
    private val fillPaint = Paint().apply {
        color = Color.parseColor("#335FD1C9")
        style = Paint.Style.FILL
        isAntiAlias = true
    }
    private val handlePaint = Paint().apply {
        color = Color.parseColor("#5FD1C9")
        style = Paint.Style.FILL
        isAntiAlias = true
    }
    private val handleRingPaint = Paint().apply {
        color = Color.WHITE
        style = Paint.Style.STROKE
        strokeWidth = 4f
        isAntiAlias = true
    }

    fun setImageBitmap(bmp: Bitmap) {
        bitmap = bmp
        invalidate()
    }

    fun setCorners(fractions: List<PointF>) {
        if (fractions.size == 4) {
            corners = fractions.toMutableList()
            invalidate()
        }
    }

    fun getCorners(): List<PointF> = corners.toList()

    fun resetToFullImage() {
        corners = mutableListOf(PointF(0f, 0f), PointF(1f, 0f), PointF(1f, 1f), PointF(0f, 1f))
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val bmp = bitmap ?: return

        val viewW = width.toFloat()
        val viewH = height.toFloat()
        val bmpW = bmp.width.toFloat()
        val bmpH = bmp.height.toFloat()
        if (viewW <= 0f || viewH <= 0f) return

        imgScale = minOf(viewW / bmpW, viewH / bmpH)
        val drawW = bmpW * imgScale
        val drawH = bmpH * imgScale
        imgLeft = (viewW - drawW) / 2f
        imgTop = (viewH - drawH) / 2f

        canvas.drawBitmap(
            bmp,
            Rect(0, 0, bmp.width, bmp.height),
            RectF(imgLeft, imgTop, imgLeft + drawW, imgTop + drawH),
            null
        )

        val screenPts = corners.map { toScreen(it) }

        val path = Path()
        path.moveTo(screenPts[0].first, screenPts[0].second)
        for (i in 1..3) path.lineTo(screenPts[i].first, screenPts[i].second)
        path.close()
        canvas.drawPath(path, fillPaint)
        canvas.drawPath(path, linePaint)

        for (p in screenPts) {
            canvas.drawCircle(p.first, p.second, HANDLE_RADIUS, handlePaint)
            canvas.drawCircle(p.first, p.second, HANDLE_RADIUS, handleRingPaint)
        }
    }

    private fun toScreen(pt: PointF): Pair<Float, Float> {
        val bmp = bitmap ?: return Pair(0f, 0f)
        return Pair(
            imgLeft + pt.x * bmp.width * imgScale,
            imgTop + pt.y * bmp.height * imgScale
        )
    }

    private fun toFraction(x: Float, y: Float): PointF {
        val bmp = bitmap ?: return PointF(0f, 0f)
        val fx = ((x - imgLeft) / (bmp.width * imgScale)).coerceIn(0f, 1f)
        val fy = ((y - imgTop) / (bmp.height * imgScale)).coerceIn(0f, 1f)
        return PointF(fx, fy)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                val screenPts = corners.map { toScreen(it) }
                var closest = -1
                var closestDist = Float.MAX_VALUE
                for (i in screenPts.indices) {
                    val d = hypot(event.x - screenPts[i].first, event.y - screenPts[i].second)
                    if (d < closestDist) {
                        closestDist = d
                        closest = i
                    }
                }
                if (closestDist < HANDLE_TOUCH_SLOP) {
                    activeHandle = closest
                    return true
                }
            }
            MotionEvent.ACTION_MOVE -> {
                if (activeHandle in 0..3) {
                    corners[activeHandle] = toFraction(event.x, event.y)
                    invalidate()
                    return true
                }
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                activeHandle = -1
            }
        }
        return super.onTouchEvent(event)
    }

    companion object {
        private const val HANDLE_RADIUS = 24f
        private const val HANDLE_TOUCH_SLOP = 60f
    }
}
