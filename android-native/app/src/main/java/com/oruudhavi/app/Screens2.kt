package com.oruudhavi.app

import android.content.Intent
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date
import java.util.Locale

// ---------------------------------------------------------------- 5 crop
@Composable
fun CropScreen(app: AppState) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var status by remember { mutableStateOf("") }
    val pick = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) scope.launch {
            try { app.cropBitmap = withContext(Dispatchers.IO) { Predictor.decode(ctx, uri) } } catch (e: Exception) { status = app.t("m_ai_failed") }
        }
    }
    Page {
        Header(app.t("crop_title"), { app.go(Screen.Home) }, app.t("back"))
        Body {
            Step(1, app.t("m_dial"))
            for (pair in Data.crops.chunked(2)) Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                for (c in pair) Choice(c.pick("name", app.lang), app.cropId == c.getString("id"), { app.cropId = c.getString("id") }, Modifier.weight(1f), icon = "leaf")
                if (pair.size == 1) Spacer(Modifier.weight(1f))
            }
            Step(2, app.t("m_leaf_photo"))
            Box(Modifier.fillMaxWidth().height(170.dp).well(18.dp), contentAlignment = Alignment.Center) {
                val bmp = app.cropBitmap
                if (bmp != null) Image(bmp.asImageBitmap(), null, Modifier.fillMaxSize().clip(androidx.compose.foundation.shape.RoundedCornerShape(18.dp)), contentScale = ContentScale.Crop)
                else Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(12.dp)) {
                    Icon("camera", 38.dp, P.Muted, stroke = 1.6f)
                    Text(app.t("m_leaf_tip"), fontSize = 14.sp, color = P.Muted, fontWeight = FontWeight.SemiBold)
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Key({ pick.launch("image/*") }, Modifier.weight(1f)) { Icon("camera", 22.dp); KeyText(if (app.cropBitmap != null) app.t("photo_change") else app.t("photo_choose"), 15) }
                Key({
                    val bmp = app.cropBitmap
                    if (app.cropId.isEmpty()) { status = app.t("m_no_crop"); return@Key }
                    if (bmp == null) { status = app.t("m_no_photo"); return@Key }
                    status = app.t("m_checking")
                    scope.launch {
                        val res = withContext(Dispatchers.Default) {
                            val p = app.predictor() ?: return@withContext null
                            try { p.predict(bmp, 3) } catch (e: Throwable) { emptyList() }
                        }
                        when {
                            res == null -> status = app.t("crop_ai_unavailable")
                            res.isEmpty() -> status = app.t("m_ai_failed")
                            else -> { val (raw, p) = res[0]; app.cropOutcome = CropOutcome(Logic.decide(raw, p).let { r -> if (r.kind == "unsure") r.copy(pretty = Logic.pretty(raw)) else r }, p, ""); status = ""; app.go(Screen.CropResult) }
                        }
                    }
                }, Modifier.weight(1f), kind = KeyKind.Red) { KeyText(app.t("crop_check"), 16) }
            }
            if (status.isNotEmpty()) Text(status, fontSize = 14.sp, fontWeight = FontWeight.Bold, color = P.Ink)
            Cap(app.t("m_pick_symptoms"))
            if (app.cropId.isEmpty()) Text(app.t("m_no_crop"), fontSize = 14.sp, color = P.Muted)
            else for (d in Data.diseasesFor(app.cropId)) Key({ app.cropOutcome = CropOutcome(null, 0f, d.getString("id")); app.go(Screen.CropResult) }, Modifier.fillMaxWidth()) {
                Text(d.pick("name", app.lang), Modifier.weight(1f), color = P.Ink, fontSize = 15.sp, fontWeight = FontWeight.ExtraBold)
                Icon("arrow", 18.dp, P.Muted, stroke = 2.2f)
            }
        }
    }
}

// ---------------------------------------------------------------- 6 crop result
@Composable
private fun NumberedList(items: List<String>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items.forEachIndexed { i, s ->
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.Top) {
                Box(Modifier.padding(top = 1.dp).size(22.dp).clip(androidx.compose.foundation.shape.CircleShape).background(P.Ink), contentAlignment = Alignment.Center) {
                    Text("${i + 1}", color = P.Cream, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold)
                }
                Text(s, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = P.Ink, lineHeight = 20.sp)
            }
        }
    }
}

@Composable
fun CropResultScreen(app: AppState) {
    val out = app.cropOutcome
    if (out == null) { LaunchedEffect(Unit) { app.go(Screen.Crop) }; return }
    val r = out.reading
    val pct = Math.round(out.p * 100)
    var d = if (r == null) Data.disease(out.diseaseId) else null
    var banner = ""
    var good = false
    if (r != null) when (r.kind) {
        "unsure" -> banner = app.t("ai_not_sure")
        "healthy" -> { banner = app.t("ai_healthy"); good = true }
        "other" -> banner = app.t("ai_other", "x" to r.pretty, "p" to pct)
        else -> { d = Data.disease(r.diseaseId); banner = app.t("ai_result", "x" to (d?.pick("name", app.lang) ?: r.pretty), "p" to pct); good = true }
    }
    Page {
        Header(app.t("m_result"), { app.go(Screen.Crop) }, app.t("back"))
        Body {
            if (r != null) Lcd(Modifier.fillMaxWidth()) {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(banner, color = P.Cream, fontSize = 17.sp, fontWeight = FontWeight.Bold, lineHeight = 23.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Lamp(good)
                        Box(Modifier.weight(1f).height(10.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(5.dp)).background(Color.Black)) {
                            Box(Modifier.fillMaxWidth(out.p.coerceIn(0f, 1f)).fillMaxSize().background(Brush.horizontalGradient(listOf(P.Sand, P.Cream))))
                        }
                        LcdText("$pct%", 14)
                    }
                }
            }
            val dd = d
            if (dd != null) Column(Modifier.fillMaxWidth().paper().padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Text(dd.pick("name", app.lang), fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) { Cap(app.t("symptoms")); Text(dd.pick("symptoms", app.lang), fontSize = 14.sp, color = P.Ink, lineHeight = 20.sp, fontWeight = FontWeight.Medium) }
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) { Cap(app.t("what_to_do")); NumberedList(dd.getJSONArray("action_${app.lang}").strs()) }
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) { Cap(app.t("prevention")); NumberedList(dd.getJSONArray("prevent_${app.lang}").strs()) }
            }
            Note((if (r != null) app.t("ai_disclaimer") + " " else "") + app.t("officer_note"))
            Key({ app.cropOutcome = null; app.cropBitmap = null; app.go(Screen.Crop) }, Modifier.fillMaxWidth(), kind = KeyKind.Red) {
                Icon("camera", 22.dp, Color.White, stroke = 2.2f); KeyText(app.t("m_another"), 18)
            }
        }
    }
}

// ---------------------------------------------------------------- 7 helper
@Composable
fun HelperScreen(app: AppState) {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    var input by remember { mutableStateOf("") }
    var showSetup by remember { mutableStateOf(false) }
    var speaking by remember { mutableStateOf(false) }
    val scroll = rememberScrollState()
    LaunchedEffect(Unit) { if (app.chat.isEmpty()) app.chat.add(ChatLine(false, app.t("chat_hello"))) }
    LaunchedEffect(app.chat.size, app.busy) { scroll.animateScrollTo(scroll.maxValue) }
    DisposableSpeaker(app) { speaking = false }

    fun speak(text: String) {
        val r = app.speaker.speak(text, app.lang)
        if (r == "ok") speaking = true else if (r == "no_voice") toast(ctx, app.t("chat_err_tts"))
    }
    fun send(raw: String) {
        val text = raw.trim()
        if (text.isEmpty() || app.busy) return
        app.speaker.stop(); speaking = false
        input = ""
        app.chat.add(ChatLine(true, text)); app.busy = true; app.pendingIssue = null
        scope.launch {
            try {
                val a = app.assistant.ask(text, app.lang)
                app.chat.add(ChatLine(false, a.reply)); app.pendingIssue = a.openFormIssue; app.busy = false
                if (app.voiceOn) speak(a.reply)
            } catch (e: AiError) {
                app.busy = false
                when (e.code) {
                    "no_key" -> { app.chat.add(ChatLine(false, app.t("m_chat_no_key"))); showSetup = true }
                    "bad_key" -> { app.chat.add(ChatLine(false, app.t("chat_err_bad_key"))); showSetup = true }
                    else -> app.chat.add(ChatLine(false, app.t("chat_err_" + e.code)))
                }
            } catch (e: Exception) { app.busy = false; app.chat.add(ChatLine(false, app.t("chat_err_server"))) }
        }
    }
    val listen = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { r ->
        val heard = r.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
        if (heard != null) send(heard)
    }
    fun mic() {
        app.speaker.stop(); speaking = false
        val i = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
            .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            .putExtra(RecognizerIntent.EXTRA_LANGUAGE, if (app.lang == "ta") "ta-IN" else "en-IN")
        try { listen.launch(i) } catch (e: Exception) { toast(ctx, app.t("chat_err_no_mic")) }
    }

    Page {
        Header(app.t("chat_title"), { app.go(Screen.Home) }, app.t("back")) {
            RoundKey({ app.voiceOn = !app.voiceOn; if (!app.voiceOn) { app.speaker.stop(); speaking = false } }, if (app.voiceOn) "speaker" else "speaker_off", if (app.voiceOn) app.t("chat_voice_on") else app.t("chat_voice_off"))
            RoundKey({ showSetup = true }, "gear", app.t("chat_setup"))
        }
        Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(scroll).padding(horizontal = 18.dp, vertical = 20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            for (m in app.chat) {
                if (m.mine) Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.CenterEnd) {
                    Box(Modifier.widthIn(max = 300.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(20.dp, 20.dp, 6.dp, 20.dp))
                        .background(Brush.verticalGradient(listOf(Color(0xFFF04A4D), P.Red, Color(0xFFBC1217)))).padding(14.dp)) {
                        Text(m.text, color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold, lineHeight = 23.sp)
                    }
                } else Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.CenterStart) {
                    Column(Modifier.widthIn(max = 300.dp).raised(20.dp, 5.dp).padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(m.text, color = P.Ink, fontSize = 16.sp, fontWeight = FontWeight.SemiBold, lineHeight = 23.sp)
                        if (app.speaker.available) RoundKey({ speak(m.text) }, "speaker", "Speak", 36.dp)
                    }
                }
            }
            if (app.busy) Row(Modifier.raised(20.dp, 5.dp).padding(14.dp), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Lamp(true); Text(app.t("chat_thinking"), color = P.Ink, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            }
            val issue = app.pendingIssue
            if (issue != null) Key({ app.draft = Complaint(issueId = issue); app.pendingIssue = null; app.go(Screen.Report) }, Modifier.fillMaxWidth(), kind = KeyKind.Red) {
                Icon("list", 20.dp, Color.White, stroke = 2.2f); KeyText(app.t("chat_open_form") + ": " + (Data.issue(issue)?.pick("name", app.lang) ?: ""), 16)
            }
        }
        // the dock with the mic knob
        Box(Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth().padding(top = 38.dp).raised(30.dp, 10.dp).padding(start = 18.dp, end = 18.dp, top = 58.dp, bottom = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(if (app.busy) app.t("chat_thinking") else if (speaking) app.t("chat_speaking") else app.t("m_helper_hint"),
                    Modifier.fillMaxWidth(), fontSize = 14.sp, fontWeight = FontWeight.Bold, color = P.Ink, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Bottom) {
                    Box(Modifier.weight(1f)) { Field(input, { input = it }, app.t("chat_placeholder")) }
                    Key({ send(input) }, Modifier.width(66.dp), kind = KeyKind.Red) { Icon("send", 22.dp, Color.White, stroke = 2.2f) }
                }
                Key({ app.chat.clear(); app.assistant.reset(); app.chat.add(ChatLine(false, app.t("chat_hello"))) }, Modifier.fillMaxWidth()) { Icon("refresh", 18.dp); KeyText(app.t("chat_new"), 14) }
            }
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                Knob(90.dp, KeyKind.Ink, onClick = { mic() }, description = "Mic") { Icon("mic", 34.dp, P.Cream, stroke = 1.8f) }
            }
        }
    }
    if (showSetup) SetupDialog(app) { showSetup = false }
}

@Composable
private fun DisposableSpeaker(app: AppState, onFinished: () -> Unit) {
    androidx.compose.runtime.DisposableEffect(Unit) {
        app.speaker.onDone = { onFinished() }
        onDispose { app.speaker.onDone = null; app.speaker.stop() }
    }
}

@Composable
private fun SetupDialog(app: AppState, onClose: () -> Unit) {
    var sel by remember { mutableStateOf(app.ai.providerId) }
    var key by remember { mutableStateOf(app.ai.key(sel)) }
    val p = PROVIDERS.first { it.id == sel }
    Dialog(onDismissRequest = onClose) {
        Column(Modifier.raised(28.dp, 10.dp).padding(20.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(app.t("chat_key_title"), fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
            Cap(app.t("chat_setup_which"))
            for (o in PROVIDERS) Choice(app.t(o.nameKey), sel == o.id, { sel = o.id; key = app.ai.key(o.id) }, Modifier.fillMaxWidth())
            if (p.needsKey) Field(key, { key = it }, app.t("chat_setup_key"))
            Text(if (p.needsKey) app.t("chat_setup_get", "w" to p.where) else app.t("chat_setup_local"), fontSize = 14.sp, color = P.Muted)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Key(onClose, Modifier.weight(1f)) { KeyText(app.t("close")) }
                Key({ app.ai.providerId = sel; app.ai.setKey(sel, key); onClose() }, Modifier.weight(1f), kind = KeyKind.Red) { KeyText(app.t("chat_setup_save")) }
            }
        }
    }
}

// ---------------------------------------------------------------- 8 history
@Composable
fun HistoryScreen(app: AppState) {
    app.storeRev.let { }
    val rows = app.store.all()
    var deleting by remember { mutableStateOf<SavedComplaint?>(null) }
    val sentN = rows.count { it.status == "sent" }
    val fmt = remember(app.lang) { DateFormat.getDateInstance(DateFormat.MEDIUM, Locale(app.lang, "IN")) }
    Page {
        Header(app.t("history_title"), { app.go(Screen.Home) }, app.t("back"))
        Body {
            Lcd(Modifier.fillMaxWidth().padding(horizontal = 6.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    LcdText(app.t("m_complaints", "n" to rows.size).uppercase(), 13)
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) { Lamp(true); LcdText(app.t("m_sent", "n" to sentN).uppercase(), 13) }
                }
            }
            if (rows.isEmpty()) Box(Modifier.fillMaxWidth().well(18.dp).padding(vertical = 34.dp), contentAlignment = Alignment.Center) { Text(app.t("history_empty"), fontWeight = FontWeight.Bold, color = P.Ink) }
            for (r in rows) {
                val issue = Data.issue(r.issueId)
                val sent = r.status == "sent"
                Row(Modifier.fillMaxWidth().paper().clickable { app.go(Screen.Letter(r.id)) }.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(52.dp).well(26.dp), contentAlignment = Alignment.Center) { Icon(issue?.getString("icon") ?: "dots", 26.dp, P.Ink, stroke = 1.8f) }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(issue?.pick("name", app.lang) ?: "", fontSize = 17.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink, lineHeight = 22.sp)
                        Text(r.areaText, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = P.Muted)
                        Text(fmt.format(Date(r.created)), fontSize = 12.sp, fontFamily = FontFamily.Monospace, color = P.Muted)
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Lamp(sent)
                        Text((if (sent) app.t("status_sent") else app.t("status_draft")).uppercase(), fontSize = 11.sp, fontWeight = FontWeight.ExtraBold, color = if (sent) P.Ink else P.Muted)
                    }
                    RoundKey({ deleting = r }, "trash", app.t("delete"), 40.dp)
                }
            }
            Key({ app.draft = Complaint(); app.go(Screen.Report) }, Modifier.fillMaxWidth(), kind = KeyKind.Red) { Icon("plus", 22.dp, Color.White, stroke = 2.4f); KeyText(app.t("m_new_problem"), 18) }
        }
    }
    val del = deleting
    if (del != null) Dialog(onDismissRequest = { deleting = null }) {
        Column(Modifier.raised(28.dp, 10.dp).padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Text(app.t("m_confirm_delete"), fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Key({ deleting = null }, Modifier.weight(1f)) { KeyText(app.t("close")) }
                Key({ app.store.remove(del.id); app.changed(); deleting = null }, Modifier.weight(1f), kind = KeyKind.Red) { KeyText(app.t("delete")) }
            }
        }
    }
}

// ---------------------------------------------------------------- 9 emergency
@Composable
fun EmergencyScreen(app: AppState) {
    val ctx = LocalContext.current
    val all = Logic.emergencyNumbers()
    val (mainEn, mainTa, mainNo) = all.first()
    Page {
        Header(app.t("emergency_title"), { app.go(Screen.Home) }, app.t("back"))
        Body {
            Column(Modifier.fillMaxWidth().padding(vertical = 6.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Box(Modifier.size(196.dp).well(98.dp), contentAlignment = Alignment.Center) {
                    Knob(152.dp, KeyKind.Red, onClick = { dial(ctx, mainNo) }, description = "${app.t("m_call")} $mainNo") {
                        Text(mainNo, color = Color.White, fontSize = 44.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Medium)
                    }
                }
                Text(app.t("m_emergency_hint"), fontSize = 16.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
            }
            for ((en, ta, no) in all.drop(1)) Row(Modifier.fillMaxWidth().raised(18.dp, 5.dp).clickable { dial(ctx, no) }.padding(start = 18.dp, end = 10.dp, top = 8.dp, bottom = 8.dp).heightIn(min = 40.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(if (app.lang == "ta") ta else en, Modifier.weight(1f), fontSize = 16.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink, lineHeight = 21.sp)
                Lcd { LcdText(no, 16) }
            }
        }
    }
}
