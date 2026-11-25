package com.oruudhavi.app

import org.json.JSONArray
import org.json.JSONObject

/** The shared data (texts, problems, offices, remedies) loaded from assets/data.json. No Android classes here, so it is unit-testable. */
object Data {
    private lateinit var root: JSONObject
    fun load(text: String) { root = JSONObject(text) }
    fun root(): JSONObject = root
    fun prompt(lang: String): String = root.getJSONObject("prompt").getString(lang)

    val strings: JSONObject get() = root.getJSONObject("strings")
    val issues: List<JSONObject> get() = root.getJSONArray("issues").objs()
    val depts: JSONObject get() = root.getJSONObject("depts")
    val remedies: JSONObject get() = root.getJSONObject("remedies")
    val labelRules: List<JSONObject> get() = root.getJSONArray("label_rules").objs()
    val crops: List<JSONObject> get() = remedies.getJSONArray("crops").objs()
    val diseases: List<JSONObject> get() = remedies.getJSONArray("diseases").objs()

    fun issue(id: String): JSONObject? = issues.firstOrNull { it.getString("id") == id }
    fun disease(id: String): JSONObject? = diseases.firstOrNull { it.getString("id") == id }
    fun diseasesFor(crop: String): List<JSONObject> = diseases.filter { it.getString("crop") == crop }

    /** t("key", "ta", "n" to 3) -> text with {n} filled in. */
    fun t(key: String, lang: String, vararg vars: Pair<String, Any>): String {
        val e = strings.optJSONObject(key) ?: return key
        var s = e.getString(lang)
        for ((k, v) in vars) s = s.replace("{$k}", v.toString())
        return s
    }
}

fun JSONArray.objs(): List<JSONObject> = (0 until length()).map { getJSONObject(it) }
fun JSONArray.strs(): List<String> = (0 until length()).map { getString(it) }
/** issue.pick("name", "ta") -> name_ta */
fun JSONObject.pick(base: String, lang: String): String = optString("${base}_$lang", "")
