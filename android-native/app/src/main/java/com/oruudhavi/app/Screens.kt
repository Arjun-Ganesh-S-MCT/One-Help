package com.oruudhavi.app

import android.content.Intent
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
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import java.time.LocalDate

// ---------------------------------------------------------------- 1 splash
@Composable
fun SplashScreen(app: AppState) {
    LaunchedEffect(Unit) { delay(2200); if (app.screen == Screen.Splash) app.go(Screen.Home) }
    Box(Modifier.fillMaxSize().background(P.ScreenBrush).clickable { app.go(Screen.Home) }, contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(34.dp)) {
            Image(painterResource(R.drawable.logo_wide), app.t("app_name"), Modifier.fillMaxWidth(0.78f), contentScale = ContentScale.FillWidth)
            Lcd { Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) { Lamp(true); LcdText(app.t("tagline"), 13) } }
        }
    }
}

// ---------------------------------------------------------------- 2 home
@Composable
private fun HomeTile(icon: String, title: String, sub: String, red: Boolean, modifier: Modifier, onClick: () -> Unit) {
    Column(modifier.raised().clickable(onClick = onClick).padding(18.dp).heightIn(min = 172.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        if (red) Knob(62.dp, KeyBrushRed) { Icon(icon, 28.dp, Color.White) }
        else Box(Modifier.size(62.dp).well(31.dp), contentAlignment = Alignment.Center) { Icon(icon, 30.dp, P.Ink) }
        Text(title, fontSize = 17.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink, lineHeight = 22.sp)
        Text(sub, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = P.Muted, lineHeight = 20.sp)
    }
}
private val KeyBrushRed = KeyKind.Red

@Composable
fun HomeScreen(app: AppState) {
    Page {
        Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Image(painterResource(R.drawable.app_icon), null, Modifier.size(48.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(14.dp)))
            Box(Modifier.weight(1f).heightIn(min = 48.dp).well(16.dp), contentAlignment = Alignment.Center) {
                Text(app.t("app_name"), fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
            }
            LangSwitch(app)
        }
        Body {
            Text(app.t("m_greeting"), fontSize = 22.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink, lineHeight = 28.sp, modifier = Modifier.padding(top = 4.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                HomeTile("list", app.t("home_report"), app.t("home_report_sub"), true, Modifier.weight(1f)) { app.draft = Complaint(); app.go(Screen.Report) }
                HomeTile("leaf", app.t("home_crop"), app.t("home_crop_sub"), false, Modifier.weight(1f)) { app.go(Screen.Crop) }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                HomeTile("mic", app.t("home_chat"), app.t("home_chat_sub"), false, Modifier.weight(1f)) { app.go(Screen.Helper) }
                HomeTile("save", app.t("home_history"), app.t("home_history_sub"), false, Modifier.weight(1f)) { app.go(Screen.History) }
            }
            Key({ app.go(Screen.Emergency) }, Modifier.fillMaxWidth(), kind = KeyKind.Ink) { Icon("phone", 22.dp, P.Cream, stroke = 2f); KeyText(app.t("home_emergency")) }
            Note(app.t("m_offline_note"))
        }
    }
}

// ---------------------------------------------------------------- 3 report
@Composable
fun ReportScreen(app: AppState) {
    val d = app.draft
    var describe by remember { mutableStateOf("") }
    var err by remember { mutableStateOf("") }
    val pick = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> app.draft = app.draft.copy(hasPhoto = uri != null) }
    val hint = Logic.suggestIssue(describe)?.let { Data.issue(it) }
    Page {
        Header(app.t("report_title"), { app.go(Screen.Home) }, app.t("back"))
        Body {
            Step(1, app.t("step1").replace(Regex("^\\d\\.\\s*"), ""))
            val all = Data.issues
            for (pair in all.chunked(2)) Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                for (i in pair) Choice(i.pick("name", app.lang), d.issueId == i.getString("id"), { app.draft = d.copy(issueId = i.getString("id")) }, Modifier.weight(1f), icon = i.getString("icon"))
                if (pair.size == 1) Spacer(Modifier.weight(1f))
            }
            Field(describe, { describe = it }, app.t("m_describe"))
            if (hint != null && d.issueId.isEmpty()) Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(app.t("hint_suggest", "x" to hint.pick("name", app.lang)), Modifier.weight(1f), fontSize = 14.sp, color = P.Muted, fontWeight = FontWeight.SemiBold)
                Key({ app.draft = d.copy(issueId = hint.getString("id")) }) { KeyText(app.t("m_use"), 14) }
            }
            Step(2, app.t("step2").replace(Regex("^\\d\\.\\s*"), ""))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Key({ pick.launch("image/*") }, Modifier.weight(1f)) { Icon("camera", 22.dp); KeyText(if (d.hasPhoto) app.t("photo_change") else app.t("photo_choose")) }
                Lamp(d.hasPhoto)
            }
            Step(3, app.t("step3").replace(Regex("^\\d\\.\\s*"), ""))
            for ((id, key) in listOf("chennai" to "area_chennai", "city" to "area_city", "village" to "area_village"))
                Choice(app.t(key), d.area == id, { app.draft = d.copy(area = id) }, Modifier.fillMaxWidth())
            if (d.area != "chennai") Field(d.town, { app.draft = d.copy(town = it) }, app.t("town_label"))
            Field(d.address, { app.draft = d.copy(address = it) }, app.t("address_label"))
            Field(d.landmark, { app.draft = d.copy(landmark = it) }, app.t("landmark_label"))
            Step(4, app.t("step4").replace(Regex("^\\d\\.\\s*"), ""))
            Field(d.name, { app.draft = d.copy(name = it) }, app.t("name_label"))
            Field(d.phone, { app.draft = d.copy(phone = it) }, app.t("phone_label"), keyboard = KeyboardType.Phone)
            Field(d.extra, { app.draft = d.copy(extra = it) }, app.t("extra_label"), lines = 3)
            if (err.isNotEmpty()) Text(err, color = P.RedLo, fontWeight = FontWeight.ExtraBold, fontSize = 14.sp)
            Key({
                val e = Logic.validate(d)
                if (e != null) { err = app.t(e); return@Key }
                val today = LocalDate.now()
                val letter = Logic.buildLetter(d, app.lang, today.dayOfMonth, today.monthValue, today.year)
                val areaText = Logic.route(d.issueId, d.area).short(app.lang)
                val id = app.store.add(d, app.lang, letter, areaText)
                app.changed(); app.go(Screen.Letter(id))
            }, Modifier.fillMaxWidth(), kind = KeyKind.Red) { Icon("arrow", 22.dp, Color.White, stroke = 2.4f); KeyText(app.t("make_letter"), 18) }
        }
    }
}

// ---------------------------------------------------------------- 4 letter
@Composable
fun LetterScreen(app: AppState, id: Int) {
    val ctx = LocalContext.current
    val clip = LocalClipboardManager.current
    app.storeRev.let { }   // re-read when something changed
    val row = app.store.get(id)
    if (row == null) { LaunchedEffect(Unit) { app.go(Screen.History) }; return }
    var text by remember(id, row.lang) { mutableStateOf(row.letter) }
    val route = Logic.route(row.issueId, row.area)
    val c = row.complaint
    val town = (c?.town?.trim().orEmpty()).ifEmpty { if (app.lang == "ta") "சென்னை" else "Chennai" }
    Page {
        Header(app.t("result_title"), { app.go(Screen.History) }, app.t("back"))
        Body {
            Lcd(Modifier.fillMaxWidth()) {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(app.t("send_to").uppercase(), color = P.Cream.copy(alpha = .8f), fontSize = 12.sp, fontFamily = FontFamily.Monospace, letterSpacing = 1.5.sp)
                    Text(route.short(app.lang).replace("{town}", town), color = P.Cream, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
            if (route.helplines.isEmpty()) Text(app.t("no_helpline"), color = P.Muted, fontSize = 14.sp)
            for (h in route.helplines) Row(Modifier.fillMaxWidth().raised(18.dp, 5.dp).clickable { dial(ctx, h.number) }.padding(start = 16.dp, end = 10.dp, top = 8.dp, bottom = 8.dp).heightIn(min = 40.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(h.label(app.lang), Modifier.weight(1f), fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
                Lcd { LcdText(h.number, 17) }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Cap(app.t("letter_lang"))
                Row(Modifier.well(16.dp).padding(4.dp)) {
                    for ((code, label) in listOf("ta" to "தமிழ்", "en" to "EN")) {
                        val on = row.lang == code
                        Box(Modifier.defaultMinSize(44.dp, 44.dp).let { if (on) it.raised(12.dp, 3.dp) else it }.clickable(enabled = c != null) {
                            if (c != null && !on) {
                                val t = LocalDate.now()
                                app.store.update(id) { r -> r.copy(lang = code, letter = Logic.buildLetter(c, code, t.dayOfMonth, t.monthValue, t.year)) }
                                app.changed()
                            }
                        }.padding(horizontal = 12.dp), contentAlignment = Alignment.Center) { Text(label, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = if (on) P.Ink else P.Muted) }
                    }
                }
            }
            Box(Modifier.fillMaxWidth().paper()) {
                BasicTextField(text, { text = it; app.store.update(id) { r -> r.copy(letter = it) } },
                    Modifier.fillMaxWidth().heightIn(min = 340.dp).lined(26.dp).padding(start = 32.dp, end = 16.dp, top = 6.dp, bottom = 14.dp),
                    textStyle = TextStyle(color = P.Ink, fontSize = 14.sp, lineHeight = 26.sp, fontWeight = FontWeight.Medium), cursorBrush = SolidColor(P.Ink))
            }
            if (c?.hasPhoto == true) Note(app.t("photo_note"), "camera")
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Key({ clip.setText(AnnotatedString(text)); toast(ctx, app.t("copied")) }, Modifier.weight(1f)) { Icon("copy", 20.dp); KeyText(app.t("copy"), 15) }
                Key({ shareText(ctx, text) }, Modifier.weight(1f)) { Icon("send", 20.dp); KeyText(app.t("m_share"), 15) }
            }
            val sent = row.status == "sent"
            Key({ app.store.update(id) { it.copy(status = "sent") }; app.changed(); toast(ctx, app.t("sent_done")) }, Modifier.fillMaxWidth(), kind = if (sent) KeyKind.Plain else KeyKind.Red, enabled = !sent) {
                if (sent) Lamp(true) else Icon("check", 22.dp, Color.White, stroke = 2.4f)
                KeyText(if (sent) app.t("status_sent") else app.t("mark_sent"), 18)
            }
        }
    }
}
