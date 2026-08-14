package com.pixlite.naturalproof

import java.io.Serializable

/**
 * Marks elapsed wall-clock time between pipeline stages so we can see where
 * time actually goes (per requirement: log processing time for each stage).
 */
class StageTimer {

    data class Stage(val name: String, val ms: Long) : Serializable

    private val stages = mutableListOf<Stage>()
    private var last = System.nanoTime()

    fun mark(name: String) {
        val now = System.nanoTime()
        val ms = (now - last) / 1_000_000
        stages.add(Stage(name, ms))
        last = now
    }

    fun results(): List<Stage> = stages.toList()

    fun totalMs(): Long = stages.sumOf { it.ms }
}
