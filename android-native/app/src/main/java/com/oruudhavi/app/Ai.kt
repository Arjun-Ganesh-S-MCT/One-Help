package com.oruudhavi.app

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class AiError(val code: String) : Exception(code)

data class Provider(val id: String, val nameKey: String, val base: String, val model: String, val needsKey: Boolean, val where: String)

val PROVIDERS = listOf(
    Provider("gemini", "m_provider_gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash", true, "aistudio.google.com"),
    Provider("groq", "m_provider_groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", true, "console.groq.com"),
    Provider("ollama", "m_provider_ollama", "http://localhost:11434/v1", "qwen2.5:7b", false, "ollama.com"),
    Provider("anthropic", "m_provider_anthropic", "https://api.anthropic.com/v1/messages", "claude-haiku-5-5", true, "console.anthropic.com"),
)

/** Provider choice and key, kept only on this phone. */
class AiSettings(ctx: Context) {
    private val sp = ctx.getSharedPreferences("oru.ai", Context.MODE_PRIVATE)
    var providerId: String
        get() = sp.getString("provider", "gemini").takeIf { id -> PROVIDERS.any { it.id == id } } ?: "gemini"
        set(v) { sp.edit().putString("provider", v).apply() }
    val provider: Provider get() = PROVIDERS.first { it.id == providerId }
    fun key(id: String = providerId) = (sp.getString("key_$id", "") ?: "").trim()
    fun setKey(id: String, k: String) { sp.edit().putString("key_$id", k.trim()).apply() }
    val configured: Boolean get() = !provider.needsKey || key().isNotEmpty()
}

internal sealed class Msg {
    class User(val text: String) : Msg()
    class Assistant(val text: String, val calls: List<Call>) : Msg()
    class Tool(val results: List<Pair<Call, String>>) : Msg()
}
internal class Call(val id: String, val name: String, val args: JSONObject)

data class Answer(val reply: String, val openFormIssue: String?)

class Assistant(private val settings: AiSettings) {
    private var history = ArrayList<Msg>()
    fun reset() { history = ArrayList() }

    private fun runTool(name: String, a: JSONObject, actions: MutableList<String>): JSONObject = try {
        when (name) {
            "find_office" -> {
                val r = Logic.route(a.getString("issue_id"), a.getString("area"))
                JSONObject().put("office", r.shortEn).put("office_tamil", r.shortTa)
                    .put("helplines", JSONArray(r.helplines.map { JSONObject().put("name", it.labelEn).put("number", it.number).put("verified", it.checked) }))
                    .put("note", "If a helpline is not verified, tell the person to confirm the number before relying on it.")
            }
            "crop_remedy" -> {
                val d = Data.disease(a.getString("disease_id")) ?: throw IllegalArgumentException()
                JSONObject().put("name", d.getString("name_en")).put("symptoms", d.getString("symptoms_en"))
                    .put("what_to_do", d.getJSONArray("action_en")).put("prevention", d.getJSONArray("prevent_en"))
                    .put("note", "Advice is general. For chemicals the person must ask a local agriculture officer.")
            }
            "open_complaint_form" -> {
                val id = a.getString("issue_id")
                if (Data.issue(id) == null) throw IllegalArgumentException()
                actions += id
                JSONObject().put("ok", true).put("note", "The form is now open on the person's screen.")
            }
            else -> JSONObject().put("error", "unknown tool")
        }
    } catch (e: Exception) { JSONObject().put("error", "bad input") }

    private fun http(url: String, payload: JSONObject, headers: Map<String, String>): JSONObject {
        val conn = try {
            (URL(url).openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"; connectTimeout = 15000; readTimeout = 60000; doOutput = true
                setRequestProperty("content-type", "application/json")
                headers.forEach { (k, v) -> setRequestProperty(k, v) }
            }
        } catch (e: Exception) { throw AiError("offline") }
        try {
            try { conn.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) } }
            catch (e: Exception) { throw AiError(if (settings.providerId == "ollama") "no_local" else "offline") }
            val code = try { conn.responseCode } catch (e: Exception) { throw AiError(if (settings.providerId == "ollama") "no_local" else "offline") }
            if (code == 401 || code == 403) throw AiError("bad_key")
            if (code == 429) throw AiError("busy")
            if (code !in 200..299) throw AiError("server")
            return try { JSONObject(conn.inputStream.bufferedReader(Charsets.UTF_8).readText()) } catch (e: Exception) { throw AiError("server") }
        } finally { conn.disconnect() }
    }

    private fun toolsJson(): JSONArray = Data.root().getJSONArray("tools")

    private fun anthropic(msgs: List<Msg>, lang: String): Pair<String, List<Call>> {
        val out = JSONArray()
        for (m in msgs) when (m) {
            is Msg.User -> out.put(JSONObject().put("role", "user").put("content", m.text))
            is Msg.Assistant -> {
                val blocks = JSONArray()
                if (m.text.isNotEmpty()) blocks.put(JSONObject().put("type", "text").put("text", m.text))
                m.calls.forEach { blocks.put(JSONObject().put("type", "tool_use").put("id", it.id).put("name", it.name).put("input", it.args)) }
                out.put(JSONObject().put("role", "assistant").put("content", blocks))
            }
            is Msg.Tool -> out.put(JSONObject().put("role", "user").put("content", JSONArray(m.results.map { (c, r) ->
                JSONObject().put("type", "tool_result").put("tool_use_id", c.id).put("content", r) })))
        }
        val p = settings.provider
        val data = http(p.base, JSONObject().put("model", p.model).put("max_tokens", 500).put("system", Data.prompt(lang))
            .put("tools", toolsJson()).put("messages", out),
            mapOf("x-api-key" to settings.key("anthropic"), "anthropic-version" to "2023-06-01"))
        val content = data.optJSONArray("content") ?: JSONArray()
        val text = content.objs().filter { it.optString("type") == "text" }.joinToString("") { it.optString("text") }.trim()
        val calls = content.objs().filter { it.optString("type") == "tool_use" }.map { Call(it.getString("id"), it.getString("name"), it.optJSONObject("input") ?: JSONObject()) }
        return text to calls
    }

    private fun openAi(msgs: List<Msg>, lang: String): Pair<String, List<Call>> {
        val out = JSONArray().put(JSONObject().put("role", "system").put("content", Data.prompt(lang)))
        for (m in msgs) when (m) {
            is Msg.User -> out.put(JSONObject().put("role", "user").put("content", m.text))
            is Msg.Assistant -> {
                val o = JSONObject().put("role", "assistant").put("content", if (m.text.isEmpty()) JSONObject.NULL else m.text)
                if (m.calls.isNotEmpty()) o.put("tool_calls", JSONArray(m.calls.map {
                    JSONObject().put("id", it.id).put("type", "function")
                        .put("function", JSONObject().put("name", it.name).put("arguments", it.args.toString())) }))
                out.put(o)
            }
            is Msg.Tool -> m.results.forEach { (c, r) -> out.put(JSONObject().put("role", "tool").put("tool_call_id", c.id).put("content", r)) }
        }
        val ts = JSONArray(toolsJson().objs().map { t ->
            JSONObject().put("type", "function").put("function", JSONObject().put("name", t.getString("name"))
                .put("description", t.getString("description")).put("parameters", t.getJSONObject("input_schema"))) })
        val p = settings.provider
        val key = settings.key()
        val data = http(p.base.trimEnd('/') + "/chat/completions",
            JSONObject().put("model", p.model).put("max_tokens", 500).put("messages", out).put("tools", ts),
            if (key.isNotEmpty()) mapOf("authorization" to "Bearer $key") else emptyMap())
        val msg = data.optJSONArray("choices")?.optJSONObject(0)?.optJSONObject("message") ?: throw AiError("server")
        val calls = (msg.optJSONArray("tool_calls") ?: JSONArray()).objs().mapIndexed { i, c ->
            val f = c.getJSONObject("function")
            val args = try { JSONObject(f.optString("arguments", "{}")) } catch (e: Exception) { JSONObject() }
            Call(c.optString("id", "call_$i"), f.getString("name"), args)
        }
        return msg.optString("content", "").let { if (it == "null") "" else it }.trim() to calls
    }

    suspend fun ask(text: String, lang: String): Answer = withContext(Dispatchers.IO) {
        val start = history.size
        history.add(Msg.User(text))
        val actions = ArrayList<String>()
        try {
            for (round in 0 until 5) {
                if (settings.provider.needsKey && settings.key().isEmpty()) throw AiError("no_key")
                val msgs = history.takeLast(24)
                val (reply, calls) = if (settings.providerId == "anthropic") anthropic(msgs, lang) else openAi(msgs, lang)
                history.add(Msg.Assistant(reply, calls))
                if (calls.isEmpty()) return@withContext Answer(reply.ifEmpty { "…" }, actions.lastOrNull())
                history.add(Msg.Tool(calls.map { it to runTool(it.name, it.args, actions).toString() }))
            }
            Answer("…", actions.lastOrNull())
        } catch (e: AiError) {
            while (history.size > start) history.removeAt(history.size - 1)   // forget the failed turn so a retry works
            throw e
        }
    }
}
