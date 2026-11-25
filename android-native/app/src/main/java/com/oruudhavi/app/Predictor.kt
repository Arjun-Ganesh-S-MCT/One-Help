package com.oruudhavi.app

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.net.Uri
import org.json.JSONObject
import java.nio.FloatBuffer
import kotlin.math.exp
import kotlin.math.min
import kotlin.math.roundToInt

/** Looks at a leaf photo with the on-phone ONNX model (assets/models/crop_model.onnx). Null when the model files are not there. */
class Predictor private constructor(
    private val env: OrtEnvironment, private val session: OrtSession, private val labels: List<String>,
    private val mean: FloatArray, private val std: FloatArray, private val size: Int, private val resize: Int?,
) {
    companion object {
        fun load(ctx: Context): Predictor? = try {
            val cfg = JSONObject(ctx.assets.open("models/crop_labels.json").bufferedReader().readText())
            val bytes = ctx.assets.open("models/crop_model.onnx").readBytes()
            val env = OrtEnvironment.getEnvironment()
            val session = env.createSession(bytes)
            fun floats(key: String, def: FloatArray) = cfg.optJSONArray(key)?.let { a -> FloatArray(a.length()) { a.getDouble(it).toFloat() } } ?: def
            Predictor(env, session, cfg.getJSONArray("labels").strs(),
                floats("mean", floatArrayOf(0.485f, 0.456f, 0.406f)), floats("std", floatArrayOf(0.229f, 0.224f, 0.225f)),
                cfg.optInt("size", 224), if (cfg.has("resize")) cfg.getInt("resize") else null)
        } catch (e: Exception) { null }

        fun decode(ctx: Context, uri: Uri): Bitmap {
            val src = ImageDecoder.createSource(ctx.contentResolver, uri)
            return ImageDecoder.decodeBitmap(src) { dec, info, _ ->
                dec.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                val longest = maxOf(info.size.width, info.size.height)
                if (longest > 1600) { val k = 1600f / longest; dec.setTargetSize((info.size.width * k).roundToInt(), (info.size.height * k).roundToInt()) }
            }
        }
    }

    private fun prepare(bmp: Bitmap): FloatBuffer {
        val s = size
        val scaled: Bitmap = if (resize != null && resize != s) {
            val k = resize.toFloat() / min(bmp.width, bmp.height)
            val w = maxOf(s, (bmp.width * k).roundToInt()); val h = maxOf(s, (bmp.height * k).roundToInt())
            val big = Bitmap.createScaledBitmap(bmp, w, h, true)
            Bitmap.createBitmap(big, (w - s) / 2, (h - s) / 2, s, s)
        } else Bitmap.createScaledBitmap(bmp, s, s, true)
        val px = IntArray(s * s)
        scaled.getPixels(px, 0, s, 0, 0, s, s)
        val out = FloatArray(3 * s * s)
        for (i in 0 until s * s) {
            val p = px[i]
            val r = ((p shr 16) and 0xFF) / 255f; val g = ((p shr 8) and 0xFF) / 255f; val b = (p and 0xFF) / 255f
            out[i] = (r - mean[0]) / std[0]; out[s * s + i] = (g - mean[1]) / std[1]; out[2 * s * s + i] = (b - mean[2]) / std[2]
        }
        return FloatBuffer.wrap(out)
    }

    /** Best guesses as (raw label, probability), highest first. */
    fun predict(bmp: Bitmap, top: Int = 3): List<Pair<String, Float>> {
        val tensor = OnnxTensor.createTensor(env, prepare(bmp), longArrayOf(1, 3, size.toLong(), size.toLong()))
        tensor.use {
            session.run(mapOf(session.inputNames.first() to tensor)).use { res ->
                @Suppress("UNCHECKED_CAST")
                val logits = (res[0].value as Array<FloatArray>)[0]
                val mx = logits.max()
                val e = FloatArray(logits.size) { exp(logits[it] - mx) }
                val sum = e.sum()
                return e.indices.map { labels[it] to e[it] / sum }.sortedByDescending { it.second }.take(top)
            }
        }
    }
}
