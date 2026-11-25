package com.oruudhavi.app

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import java.util.Locale

/** Reads answers aloud with the phone's own text-to-speech (Tamil or English). */
class Speaker(ctx: Context) {
    private var ready = false
    private var tts: TextToSpeech? = null
    var onDone: (() -> Unit)? = null

    init {
        tts = TextToSpeech(ctx.applicationContext) { status ->
            ready = status == TextToSpeech.SUCCESS
            tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(id: String?) {}
                override fun onDone(id: String?) { onDone?.invoke() }
                @Deprecated("Deprecated in Java") override fun onError(id: String?) { onDone?.invoke() }
            })
        }
    }

    val available: Boolean get() = ready

    /** "ok", "no_voice" (the phone has no voice for that language) or "unsupported". */
    fun speak(text: String, lang: String): String {
        val t = tts ?: return "unsupported"
        if (!ready) return "unsupported"
        val locale = if (lang == "ta") Locale("ta", "IN") else Locale("en", "IN")
        val r = t.setLanguage(locale)
        if (r == TextToSpeech.LANG_MISSING_DATA || r == TextToSpeech.LANG_NOT_SUPPORTED) return "no_voice"
        t.speak(clean(text), TextToSpeech.QUEUE_FLUSH, null, "oru")
        return "ok"
    }

    fun stop() { tts?.stop() }
    fun shutdown() { tts?.stop(); tts?.shutdown() }

    private fun clean(s: String): String =
        s.replace(Regex("[*_#`>~]"), " ").replace(Regex("\\s+"), " ").trim()
}
