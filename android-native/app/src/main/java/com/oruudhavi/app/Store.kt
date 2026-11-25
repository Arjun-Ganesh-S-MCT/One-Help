package com.oruudhavi.app

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class SavedComplaint(
    val id: Int, val created: Long, val issueId: String, val area: String, val areaText: String,
    val lang: String, val letter: String, val status: String, val complaint: Complaint?,
)

/** Saves the user's complaints on the phone (private app storage, works offline). */
class Store(ctx: Context) {
    private val sp = ctx.getSharedPreferences("oru.complaints", Context.MODE_PRIVATE)

    private fun read(): MutableList<SavedComplaint> {
        val out = ArrayList<SavedComplaint>()
        try {
            val arr = JSONArray(sp.getString("rows", "[]"))
            for (o in arr.objs()) {
                val c = o.optJSONObject("c")?.let {
                    Complaint(it.optString("issueId"), it.optString("area", "chennai"), it.optString("town"), it.optString("address"),
                        it.optString("landmark"), it.optString("name"), it.optString("phone"), it.optString("extra"), it.optBoolean("hasPhoto"))
                }
                out += SavedComplaint(o.getInt("id"), o.getLong("created"), o.getString("issueId"), o.getString("area"), o.optString("areaText"),
                    o.getString("lang"), o.getString("letter"), o.getString("status"), c)
            }
        } catch (e: Exception) { /* damaged data: start empty */ }
        return out
    }

    private fun write(rows: List<SavedComplaint>) {
        val arr = JSONArray()
        for (r in rows) arr.put(JSONObject().apply {
            put("id", r.id); put("created", r.created); put("issueId", r.issueId); put("area", r.area); put("areaText", r.areaText)
            put("lang", r.lang); put("letter", r.letter); put("status", r.status)
            r.complaint?.let { c -> put("c", JSONObject().apply {
                put("issueId", c.issueId); put("area", c.area); put("town", c.town); put("address", c.address); put("landmark", c.landmark)
                put("name", c.name); put("phone", c.phone); put("extra", c.extra); put("hasPhoto", c.hasPhoto) }) }
        })
        sp.edit().putString("rows", arr.toString()).apply()
    }

    fun add(c: Complaint, lang: String, letter: String, areaText: String): Int {
        val rows = read()
        val id = (rows.maxOfOrNull { it.id } ?: 0) + 1
        rows += SavedComplaint(id, System.currentTimeMillis(), c.issueId, c.area, areaText, lang, letter, "draft", c)
        write(rows)
        return id
    }
    fun update(id: Int, f: (SavedComplaint) -> SavedComplaint) { write(read().map { if (it.id == id) f(it) else it }) }
    fun remove(id: Int) { write(read().filter { it.id != id }) }
    fun all(): List<SavedComplaint> = read().sortedByDescending { it.id }
    fun get(id: Int): SavedComplaint? = read().firstOrNull { it.id == id }
}
