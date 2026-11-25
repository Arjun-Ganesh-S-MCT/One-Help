package com.oruudhavi.app

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.wrapContentSize
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

fun toast(ctx: Context, msg: String) = Toast.makeText(ctx, msg, Toast.LENGTH_SHORT).show()

fun dial(ctx: Context, number: String) {
    try { ctx.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + number.replace(" ", ""))).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
    catch (e: Exception) { toast(ctx, number) }
}

fun shareText(ctx: Context, text: String) {
    val send = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, text)
    ctx.startActivity(Intent.createChooser(send, null).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
}

/** The page: warm ivory, content scrolls, keyboard pushes it up. */
@Composable
fun Page(content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().background(P.ScreenBrush).imePadding()) { content() }
}

@Composable
fun Header(title: String, onBack: (() -> Unit)?, back: String, right: @Composable () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
        if (onBack != null) RoundKey(onBack, "back", back)
        Box(Modifier.weight(1f).heightIn(min = 48.dp).well(16.dp).padding(horizontal = 10.dp), contentAlignment = Alignment.Center) {
            Text(title, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink, maxLines = 1)
        }
        right()
    }
}

@Composable
fun LangSwitch(app: AppState) {
    Row(Modifier.well(16.dp).padding(4.dp)) {
        for ((code, label) in listOf("en" to "EN", "ta" to "தமிழ்")) {
            val on = app.lang == code
            Box(
                Modifier.defaultMinSize(minWidth = 44.dp, minHeight = 44.dp).let { if (on) it.raised(12.dp, 3.dp) else it.clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp)) }
                    .clickable { app.setLang(code) }.padding(horizontal = 10.dp),
                contentAlignment = Alignment.Center,
            ) { Text(label, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold, color = if (on) P.Ink else P.Muted) }
        }
    }
}

@Composable
fun Body(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Column(modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(start = 22.dp, end = 22.dp, top = 18.dp, bottom = 28.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) { content() }
}

@Composable
fun Step(n: Int, text: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(28.dp).clip(androidx.compose.foundation.shape.CircleShape).background(P.Ink), contentAlignment = Alignment.Center) {
            Text("$n", color = P.Cream, fontSize = 14.sp, fontWeight = FontWeight.ExtraBold)
        }
        Text(text, fontSize = 17.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
    }
}

@Composable
fun Field(value: String, onChange: (String) -> Unit, hint: String, modifier: Modifier = Modifier, keyboard: KeyboardType = KeyboardType.Text, lines: Int = 1) {
    Box(modifier.fillMaxWidth().well(16.dp).defaultMinSize(minHeight = if (lines > 1) 90.dp else 50.dp).padding(horizontal = 16.dp, vertical = 12.dp), contentAlignment = if (lines > 1) Alignment.TopStart else Alignment.CenterStart) {
        if (value.isEmpty()) Text(hint, color = P.Muted, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
        BasicTextField(value, onChange, Modifier.fillMaxWidth(), textStyle = TextStyle(color = P.Ink, fontSize = 16.sp, fontWeight = FontWeight.SemiBold),
            cursorBrush = SolidColor(P.Ink), singleLine = lines == 1, keyboardOptions = KeyboardOptions(keyboardType = keyboard))
    }
}

@Composable
fun Note(text: String, icon: String = "info") {
    Row(Modifier.fillMaxWidth().well(16.dp).padding(horizontal = 16.dp, vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, 20.dp, P.Muted)
        Text(text, fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = P.Ink, lineHeight = 20.sp)
    }
}

/** A selectable option key with a lamp: lit = chosen. */
@Composable
fun Choice(label: String, chosen: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier, icon: String? = null) {
    Key(onClick, modifier, on = chosen) {
        if (icon != null) Icon(icon, 22.dp, P.Ink)
        Text(label, Modifier.weight(1f), color = P.Ink, fontSize = 15.sp, fontWeight = FontWeight.ExtraBold, lineHeight = 19.sp)
        Lamp(chosen, 10.dp)
    }
}
