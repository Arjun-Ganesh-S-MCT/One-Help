package com.oruudhavi.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember

class MainActivity : ComponentActivity() {
    private var state: AppState? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Data.load(assets.open("data.json").bufferedReader().readText())
        val app = AppState(applicationContext).also { state = it }
        setContent { Root(app) }
    }

    override fun onDestroy() { state?.speaker?.shutdown(); super.onDestroy() }
}

@Composable
fun Root(app: AppState) {
    val s = app.screen
    BackHandler(enabled = s != Screen.Home && s != Screen.Splash) {
        app.go(when (s) { is Screen.Letter -> Screen.History; Screen.CropResult -> Screen.Crop; else -> Screen.Home })
    }
    when (s) {
        Screen.Splash -> SplashScreen(app)
        Screen.Home -> HomeScreen(app)
        Screen.Report -> ReportScreen(app)
        is Screen.Letter -> LetterScreen(app, s.id)
        Screen.Crop -> CropScreen(app)
        Screen.CropResult -> CropResultScreen(app)
        Screen.Helper -> HelperScreen(app)
        Screen.History -> HistoryScreen(app)
        Screen.Emergency -> EmergencyScreen(app)
    }
}
