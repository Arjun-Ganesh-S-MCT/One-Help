package com.oruudhavi.app

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.defaultMinSize
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.asAndroidPath
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** Palette: 60% ivory, 30% ink + sand, 10% red (only the main action and lamps). */
object P {
    val Ivory = Color(0xFFEFE9E0); val IvoryHi = Color(0xFFF8F4EE); val IvoryLo = Color(0xFFE3DBCF)
    val Sand = Color(0xFFE2CBB5); val SandLo = Color(0xFFCDB095)
    val Ink = Color(0xFF2B2A2E); val InkHi = Color(0xFF46454B); val Muted = Color(0xFF5F574F)
    val Red = Color(0xFFD7191C); val RedHi = Color(0xFFEE4144); val RedLo = Color(0xFFA81013)
    val Shade = Color(0x577C644C)      // dark side of every shadow (light comes from the top left)
    val Light = Color(0xF2FFFFFF)
    val Cream = Color(0xFFF3E6D6)
    val ScreenBrush = Brush.linearGradient(listOf(IvoryHi, Ivory, Color(0xFFE5DDD1)), Offset(0f, 0f), Offset(900f, 2400f))
}

private val RaisedBrush = Brush.linearGradient(listOf(Color(0xFFF9F6F0), Color(0xFFE8E1D6)), Offset(0f, 0f), Offset(300f, 300f))
private val KeyBrush = Brush.linearGradient(listOf(Color(0xFFFBF8F3), Color(0xFFE6DED3)), Offset(0f, 0f), Offset(200f, 200f))
private val PressedBrush = Brush.linearGradient(listOf(Color(0xFFE2D9CC), Color(0xFFEFE9E0)), Offset(0f, 0f), Offset(200f, 200f))
private val WellBrush = Brush.linearGradient(listOf(Color(0xFFE4DBCF), Color(0xFFF2EDE5)), Offset(0f, 0f), Offset(300f, 300f))

/** Soft light + dark shadows around a rounded shape (works on Android 9+; older phones show a flat key). */
private fun Modifier.neoShadow(radius: Dp, depth: Dp, dark: Color = P.Shade, light: Color = P.Light): Modifier = drawBehind {
    val r = radius.toPx(); val d = depth.toPx()
    drawIntoCanvas { canvas ->
        val paint = android.graphics.Paint().apply { isAntiAlias = true; color = P.Ivory.toArgb() }
        paint.setShadowLayer(d * 1.3f, -d * .55f, -d * .55f, light.toArgb())
        canvas.nativeCanvas.drawRoundRect(0f, 0f, size.width, size.height, r, r, paint)
        paint.setShadowLayer(d * 1.3f, d * .55f, d * .55f, dark.toArgb())
        canvas.nativeCanvas.drawRoundRect(0f, 0f, size.width, size.height, r, r, paint)
    }
}

/** A panel standing out of the page ("press me"). */
fun Modifier.raised(radius: Dp = 26.dp, depth: Dp = 10.dp): Modifier =
    this.neoShadow(radius, depth)
        .clip(RoundedCornerShape(radius))
        .background(RaisedBrush)
        .border(1.dp, Brush.linearGradient(listOf(Color.White, Color(0x337C644C))), RoundedCornerShape(radius))

/** A sunken area ("holds something"). */
fun Modifier.well(radius: Dp = 18.dp): Modifier =
    this.clip(RoundedCornerShape(radius))
        .background(WellBrush)
        .drawWithContent {
            drawContent()
            val r = radius.toPx(); val w = 7.dp.toPx()
            val path = androidx.compose.ui.graphics.Path().apply {
                addRoundRect(androidx.compose.ui.geometry.RoundRect(0f, 0f, size.width, size.height, CornerRadius(r, r)))
            }
            clipPath(path) {
                drawRoundRect(
                    brush = Brush.linearGradient(listOf(Color(0x597C644C), Color(0x00FFFFFF), Color(0x00FFFFFF), Color(0xE6FFFFFF)), Offset(0f, 0f), Offset(size.width, size.height)),
                    cornerRadius = CornerRadius(r, r), style = Stroke(width = w),
                )
            }
        }

@Composable
fun Lamp(on: Boolean = true, size: Dp = 12.dp, modifier: Modifier = Modifier) {
    Box(modifier.size(size).drawBehind {
        val c = Offset(this.size.width / 2, this.size.height / 2); val r = this.size.minDimension / 2
        if (on) drawIntoCanvas { canvas ->
            val p = android.graphics.Paint().apply { isAntiAlias = true; color = P.Red.toArgb() }
            p.setShadowLayer(r * 1.1f, 0f, 0f, Color(0x8CD7191C).toArgb())
            canvas.nativeCanvas.drawCircle(c.x, c.y, r * .8f, p)
        }
        drawCircle(
            brush = Brush.radialGradient(
                if (on) listOf(Color(0xFFFFB0B1), P.Red, Color(0xFF8E0D10)) else listOf(Color(0xFFF1EBE2), P.SandLo, Color(0xFFB89A80)),
                center = Offset(c.x * .8f, c.y * .75f), radius = r * 1.3f),
            radius = r * .85f, center = c)
    })
}

@Composable
fun Lcd(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Box(modifier
        .border(5.dp, P.IvoryLo, RoundedCornerShape(16.dp))
        .clip(RoundedCornerShape(16.dp))
        .background(Brush.verticalGradient(listOf(Color(0xFF1B1A1E), P.Ink)))
        .padding(horizontal = 16.dp, vertical = 10.dp)) { content() }
}

@Composable
fun LcdText(text: String, size: Int = 14, modifier: Modifier = Modifier) {
    Text(text, modifier, color = P.Cream, fontSize = size.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Medium, letterSpacing = 1.sp)
}

enum class KeyKind { Plain, Red, Ink }

/** A pressable key. Red = the one main action on a screen. */
@Composable
fun Key(
    onClick: () -> Unit, modifier: Modifier = Modifier, kind: KeyKind = KeyKind.Plain, on: Boolean = false, enabled: Boolean = true,
    description: String? = null, content: @Composable RowScope.() -> Unit,
) {
    val src = remember { MutableInteractionSource() }
    val pressed by src.collectIsPressedAsState()
    val down = (pressed || on) && enabled
    val radius = if (kind == KeyKind.Red) 20.dp else 16.dp
    val shape = RoundedCornerShape(radius)
    val h = if (kind == KeyKind.Red) 58.dp else 48.dp
    val base = modifier.defaultMinSize(minHeight = h)
    val look = when {
        !enabled -> base.clip(shape).background(P.IvoryLo)
        kind == KeyKind.Red -> base
            .drawBehind { // the dark edge under the key
                drawRoundRect(P.RedLo, Offset(0f, if (down) 1.dp.toPx() else 4.dp.toPx()), size, CornerRadius(radius.toPx()))
            }
            .padding(bottom = 3.dp)
            .clip(shape).background(Brush.verticalGradient(listOf(Color(0xFFF04A4D), P.Red, Color(0xFFBC1217))))
        kind == KeyKind.Ink -> base.neoShadow(radius, 6.dp, Color(0x592B2A2E), Color.Transparent).clip(shape)
            .background(Brush.verticalGradient(listOf(Color(0xFF55545B), P.Ink, Color(0xFF1E1D21))))
        down -> base.clip(shape).background(PressedBrush).border(1.dp, Color(0x337C644C), shape)
        else -> base.neoShadow(radius, 6.dp).clip(shape).background(KeyBrush).border(1.dp, Brush.linearGradient(listOf(Color.White, Color(0x337C644C))), shape)
    }
    val fg = if (kind == KeyKind.Plain || !enabled) (if (enabled) P.Ink else P.Muted) else if (kind == KeyKind.Red) Color.White else P.Cream
    Row(
        look.clickable(interactionSource = src, indication = null, enabled = enabled, role = Role.Button, onClick = onClick)
            .padding(horizontal = 18.dp, vertical = 10.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp, Alignment.CenterHorizontally), verticalAlignment = Alignment.CenterVertically,
    ) {
        androidx.compose.runtime.CompositionLocalProvider(LocalFg provides fg) { content() }
    }
}

val LocalFg = androidx.compose.runtime.compositionLocalOf { P.Ink }

@Composable
fun KeyText(text: String, size: Int = 16) {
    Text(text, color = LocalFg.current, fontSize = size.sp, fontWeight = FontWeight.ExtraBold)
}

@Composable
fun RoundKey(onClick: () -> Unit, icon: String, description: String, size: Dp = 48.dp, tint: Color = P.Ink) {
    val src = remember { MutableInteractionSource() }
    val pressed by src.collectIsPressedAsState()
    val mod = Modifier.size(size).let { m ->
        if (pressed) m.clip(CircleShape).background(PressedBrush)
        else m.neoShadow(size / 2, 6.dp).clip(CircleShape).background(KeyBrush).border(1.dp, Brush.linearGradient(listOf(Color.White, Color(0x337C644C))), CircleShape)
    }
    Box(mod.clickable(interactionSource = src, indication = null, role = Role.Button, onClickLabel = description, onClick = onClick), contentAlignment = Alignment.Center) {
        Icon(icon, 24.dp, tint, description)
    }
}

/** Round knob: light (default), ink, or red. */
@Composable
fun Knob(size: Dp, kind: KeyKind = KeyKind.Plain, modifier: Modifier = Modifier, onClick: (() -> Unit)? = null, description: String? = null, content: @Composable () -> Unit = {}) {
    val colors = when (kind) {
        KeyKind.Ink -> listOf(Color(0xFF6A6970), P.Ink, Color(0xFF6A6970), Color(0xFF1E1D21), Color(0xFF6A6970), P.Ink, Color(0xFF6A6970))
        KeyKind.Red -> listOf(Color(0xFFF7706F), Color(0xFFC4131A), Color(0xFFF7706F), P.RedLo, Color(0xFFF7706F), Color(0xFFC4131A), Color(0xFFF7706F))
        else -> listOf(Color(0xFFFEFCF8), Color(0xFFDBD3C6), Color(0xFFFEFCF8), Color(0xFFD0C7B9), Color(0xFFFEFCF8), Color(0xFFD9D1C4), Color(0xFFFEFCF8))
    }
    val inner = when (kind) {
        KeyKind.Ink -> listOf(Color(0xFF6B6A72), Color(0xFF37363B), Color(0xFF222126))
        KeyKind.Red -> listOf(Color(0xFFFF8B8C), P.Red, P.RedLo)
        else -> listOf(Color.White, Color(0xFFEEE7DC), Color(0xFFDCD3C5))
    }
    val dark = if (kind == KeyKind.Plain) P.Shade else if (kind == KeyKind.Red) Color(0x66A81013) else Color(0x592B2A2E)
    var m = modifier.size(size).neoShadow(size / 2, 12.dp, dark).clip(CircleShape).background(Brush.sweepGradient(colors))
    if (onClick != null) m = m.clickable(role = Role.Button, onClickLabel = description, onClick = onClick)
    Box(m, contentAlignment = Alignment.Center) {
        Box(Modifier.size(size * 0.74f).clip(CircleShape).background(Brush.radialGradient(inner, Offset(size.value * 1.2f, size.value * 1.0f), size.value * 1.5f)), contentAlignment = Alignment.Center) { content() }
    }
}

@Composable
fun Icon(name: String, size: Dp = 24.dp, tint: Color = P.Ink, description: String? = null, stroke: Float = 1.9f, modifier: Modifier = Modifier) {
    val path = remember(name) { PathParser().parsePathString(IconData.paths[name] ?: "").toPath() }
    androidx.compose.foundation.Canvas(modifier.size(size)) {
        scale(this.size.width / 24f, Offset.Zero) {
            drawPath(path, tint, style = Stroke(width = stroke, cap = StrokeCap.Round, join = StrokeJoin.Round))
        }
    }
}

@Composable
fun Cap(text: String, modifier: Modifier = Modifier) {
    Text(text.uppercase(), modifier, color = P.Muted, fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = 1.6.sp)
}

/** Sheet of paper with a soft shadow. */
fun Modifier.paper(): Modifier =
    this.neoShadow(6.dp, 6.dp, Color(0x527C644C), Color.Transparent).clip(RoundedCornerShape(6.dp)).background(Color(0xFFFFFDF8))

/** Notebook lines (and a red margin) behind text of the given line height. */
fun Modifier.lined(lineHeight: Dp = 26.dp): Modifier = drawBehind {
    val step = lineHeight.toPx()
    var y = step
    while (y < size.height) { drawLine(Color(0x80CDB095), Offset(0f, y), Offset(size.width, y), 1f); y += step }
    drawLine(Color(0x73D7191C), Offset(22.dp.toPx(), 0f), Offset(22.dp.toPx(), size.height), 2f)
}

val Heading = TextStyle(fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, color = P.Ink)
