package com.oruudhavi.app

import android.content.Context
import android.graphics.Bitmap
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

sealed interface Screen {
    data object Splash : Screen
    data object Home : Screen
    data object Report : Screen
    data class Letter(val id: Int) : Screen
    data object Crop : Screen
    data object CropResult : Screen
    data object Helper : Screen
    data object History : Screen
    data object Emergency : Screen
}

data class ChatLine(val mine: Boolean, val text: String)
data class CropOutcome(val reading: Reading?, val p: Float, val diseaseId: String)

/** Everything the screens share. */
class AppState(val ctx: Context) {
    val store = Store(ctx)
    val ai = AiSettings(ctx)
    val assistant = Assistant(ai)
    val speaker = Speaker(ctx)
    private val prefs = ctx.getSharedPreferences("oru.app", Context.MODE_PRIVATE)

    var screen: Screen by mutableStateOf(Screen.Splash)
    var lang by mutableStateOf(prefs.getString("lang", "ta") ?: "ta")
        private set
    fun changeLang(code: String) { lang = code; prefs.edit().putString("lang", code).apply() }

    fun t(key: String, vararg vars: Pair<String, Any>) = Data.t(key, lang, *vars)

    var draft by mutableStateOf(Complaint())
    var storeRev by mutableStateOf(0)          // bump to make lists reload
    fun changed() { storeRev++ }

    // crop
    var cropId by mutableStateOf("")
    var cropBitmap: Bitmap? by mutableStateOf(null)
    var cropOutcome: CropOutcome? by mutableStateOf(null)
    private var predictorTried = false
    private var predictor: Predictor? = null
    fun predictor(): Predictor? { if (!predictorTried) { predictorTried = true; predictor = Predictor.load(ctx) }; return predictor }

    // helper chat
    val chat = mutableStateListOf<ChatLine>()
    var busy by mutableStateOf(false)
    var voiceOn by mutableStateOf(true)
    var pendingIssue: String? by mutableStateOf(null)

    fun go(s: Screen) { speaker.stop(); screen = s }
}
