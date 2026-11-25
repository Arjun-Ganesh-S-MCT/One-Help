package com.oruudhavi.app

import java.util.Locale
import org.json.JSONObject

// Same behaviour as oru/complaint.py and oru/labels.py (checked against parity.json in the unit tests).

data class Complaint(
    val issueId: String = "", val area: String = "chennai", val town: String = "", val address: String = "",
    val landmark: String = "", val name: String = "", val phone: String = "", val extra: String = "", val hasPhoto: Boolean = false,
)

data class Helpline(val labelEn: String, val labelTa: String, val number: String, val checked: Boolean) {
    fun label(lang: String) = if (lang == "ta") labelTa else labelEn
}

data class Route(val en: String, val ta: String, val shortEn: String, val shortTa: String, val helplines: List<Helpline>) {
    fun block(lang: String) = if (lang == "ta") ta else en
    fun short(lang: String) = if (lang == "ta") shortTa else shortEn
}

data class Reading(val kind: String, val crop: String, val diseaseId: String, val pretty: String)

object Logic {
    fun suggestIssue(text: String): String? {
        val tx = text.lowercase(Locale.ROOT)
        var best: String? = null
        var bestScore = 0
        for (it in Data.issues) {
            val score = it.getJSONArray("keywords").strs().count { k -> tx.contains(k.lowercase(Locale.ROOT)) }
            if (score > bestScore) { best = it.getString("id"); bestScore = score }
        }
        return best
    }

    private fun helplineOf(o: JSONObject) =
        Helpline(o.getString("label_en"), o.getString("label_ta"), o.getString("number"), o.optBoolean("checked", false))

    fun route(issueId: String, area: String): Route {
        val d = Data.depts
        val kind = d.getJSONObject("issue_route").getString(issueId)
        val auth = d.getJSONObject("authorities")
        val block: JSONObject = if (kind == "power") auth.getJSONObject("power")
        else {
            val a = auth.getJSONObject(area)
            a.optJSONObject(kind) ?: a.getJSONObject("local_body")      // some areas have null for this kind
        }
        var helplines = block.getJSONArray("helplines").objs().map(::helplineOf)
        if (helplines.isEmpty()) helplines = listOf(helplineOf(d.getJSONObject("fallback_helpline")))
        return Route(block.getString("en"), block.getString("ta"), block.getString("short_en"), block.getString("short_ta"), helplines)
    }

    fun emergencyNumbers(): List<Triple<String, String, String>> =
        Data.depts.getJSONArray("emergency").objs().map { Triple(it.getString("en"), it.getString("ta"), it.getString("number")) }

    private fun pad(n: Int) = n.toString().padStart(2, '0')
    fun stamp(day: Int, month: Int, year: Int) = "${pad(day)}/${pad(month)}/$year"

    /** month is 1-12. */
    fun buildLetter(c: Complaint, lang: String, day: Int, month: Int, year: Int): String {
        val block = route(c.issueId, c.area)
        val town = c.town.trim().ifEmpty { if (lang == "ta") "சென்னை" else "Chennai" }
        val toBlock = block.block(lang).replace("{town}", town)
        val issue = Data.issue(c.issueId)!!
        val loc = c.landmark.trim().ifEmpty { c.address.trim() }
        val sentence = issue.pick("sentence", lang).replace("{loc}", loc)
        val addressLine = c.address.trim() + if (c.town.trim().isNotEmpty()) ", " + c.town.trim() else ""
        val date = stamp(day, month, year)
        val extra = c.extra.trim()
        val phone = c.phone.trim()
        val lines = ArrayList<String>()
        if (lang == "ta") {
            val subject = "${issue.getString("name_ta")} தொடர்பான புகார்"
            lines += listOf("பெறுநர்:", toBlock, "", "அனுப்புநர்:", c.name.trim(), addressLine)
            if (phone.isNotEmpty()) lines += "தொலைபேசி: $phone"
            lines += listOf(
                "", "நாள்: $date", "", "பொருள்: $subject", "", "மதிப்புமிகு ஐயா / அம்மா,", "",
                "நான் $addressLine பகுதியில் வசிக்கிறேன். $sentence. இதனால் பொதுமக்களுக்குப் பெரும் சிரமம் ஏற்படுகிறது." + (if (extra.isNotEmpty()) " $extra" else ""),
                "",
                "எனவே, இந்தப் பிரச்சினையை விரைவில் நேரில் ஆய்வு செய்து சரிசெய்ய உரிய நடவடிக்கை எடுக்குமாறு பணிவுடன் கேட்டுக்கொள்கிறேன்." + (if (c.hasPhoto) " பிரச்சினையின் புகைப்படம் இணைக்கப்பட்டுள்ளது." else ""),
                "", "நன்றி.", "", "இப்படிக்கு,", c.name.trim(),
            )
        } else {
            val subject = "Complaint regarding ${issue.getString("name_en").lowercase(Locale.ROOT)}"
            lines += listOf("To,", toBlock, "", "From,", c.name.trim(), addressLine)
            if (phone.isNotEmpty()) lines += "Phone: $phone"
            lines += listOf(
                "", "Date: $date", "", "Subject: $subject", "", "Respected Sir / Madam,", "",
                "I am a resident of $addressLine. I would like to bring to your kind notice that $sentence. This is causing great difficulty to the public." + (if (extra.isNotEmpty()) " $extra" else ""),
                "",
                "I kindly request you to inspect the matter and take the necessary action at the earliest." + (if (c.hasPhoto) " A photograph of the problem is attached." else ""),
                "", "Thank you.", "", "Yours faithfully,", c.name.trim(),
            )
        }
        return lines.joinToString("\n")
    }

    /** Returns an error string key or null (same order as the Python app). */
    fun validate(c: Complaint): String? {
        if (c.issueId.isEmpty()) return "err_issue"
        if (c.area != "chennai" && c.town.trim().isEmpty()) return "err_town"
        if (c.address.trim().isEmpty()) return "err_address"
        if (c.name.trim().isEmpty()) return "err_name"
        return null
    }

    // ---- crop labels ----
    private fun norm(raw: String) = raw.lowercase(Locale.ROOT).replace(Regex("[^a-z0-9]+"), " ").trim()

    fun pretty(raw: String): String =
        raw.split(Regex("_{2,}")).filter { it.isNotEmpty() }
            .map { p -> p.replace(Regex("_+"), " ").replace("(", "").replace(")", "").trim() }
            .joinToString(" - ") { p -> if (p.isEmpty()) p else p.substring(0, 1).uppercase(Locale.ROOT) + p.substring(1) }

    fun interpret(raw: String): Reading {
        val words = norm(raw).split(" ").filter { it.isNotEmpty() }.toSet()
        val crop = if ("tomato" in words) "tomato" else if ("potato" in words) "potato" else ""
        val name = pretty(raw)
        if ("healthy" in words) return Reading("healthy", crop, "", name)
        for (r in Data.labelRules) {
            if (r.getString("crop") == crop && r.getJSONArray("must").strs().all { m -> words.any { w -> w.startsWith(m) } })
                return Reading("disease", crop, r.getString("id"), name)
        }
        return Reading("other", crop, "", name)
    }

    const val CONFIDENCE = 0.6f

    /** What to do with the model's best guess: unsure below 60%, else the reading. */
    fun decide(raw: String, p: Float): Reading =
        if (p < CONFIDENCE) Reading("unsure", "", "", raw) else interpret(raw)
}
