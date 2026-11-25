// The talking helper's brain. Same design as oru/assistant.py: an AI service (free ones work:
// Gemini, Groq, or Ollama; Claude too) that looks things up in OUR data through tools, so
// phone numbers and remedies always come from the app's own checked lists.
import { issues, issueById, route } from "./complaint.js";
import { REMEDIES } from "./data.js";
import { disease } from "./crop.js";

export const PROVIDERS = {
  gemini: { name: "m_provider_gemini", base: "https://generativelanguage.googleapis.com/v1beta/openai", model: "gemini-2.5-flash", needsKey: true, where: "aistudio.google.com" },
  groq: { name: "m_provider_groq", base: "https://api.groq.com/openai/v1", model: "llama-3.3-70b-versatile", needsKey: true, where: "console.groq.com" },
  ollama: { name: "m_provider_ollama", base: "http://localhost:11434/v1", model: "qwen2.5:7b", needsKey: false, where: "ollama.com" },
  anthropic: { name: "m_provider_anthropic", base: "https://api.anthropic.com/v1/messages", model: "claude-haiku-5-5", needsKey: true, where: "console.anthropic.com" },
};
export const DEFAULT_PROVIDER = "gemini";
const MAX_TOOL_ROUNDS = 5, KEEP = 24;
const CFG = "oru.ai.v1";

export class AssistantError extends Error {
  constructor(code) { super(code); this.code = code; }
}

// ---- settings (kept on the phone only) ----
export function loadConfig() { try { return JSON.parse(localStorage.getItem(CFG) || "{}"); } catch (e) { return {}; } }
export function saveSettings(provider, key = "") {
  const c = loadConfig();
  c.provider = provider;
  c.keys = { ...(c.keys || {}), [provider]: key.trim() };
  try { localStorage.setItem(CFG, JSON.stringify(c)); } catch (e) { /* ignore */ }
}
export const provider = () => (PROVIDERS[loadConfig().provider] ? loadConfig().provider : DEFAULT_PROVIDER);
export const apiKey = (p = provider()) => ((loadConfig().keys || {})[p] || "").trim();
export const isConfigured = () => !PROVIDERS[provider()].needsKey || !!apiKey();
export const modelName = () => loadConfig().model || PROVIDERS[provider()].model;
export const baseUrl = () => loadConfig().base || PROVIDERS[provider()].base;

// ---- tools ----
export function tools() {
  return [
    {
      name: "find_office",
      description: "Find which office should get a complaint and its helpline, from the app's own checked list. Always use this before telling the person where to complain.",
      input_schema: {
        type: "object",
        properties: {
          issue_id: { type: "string", enum: issues().map((i) => i.id) },
          area: { type: "string", enum: ["chennai", "city", "village"], description: "chennai = Chennai city; city = other city or town (municipality/town panchayat); village = village panchayat" },
        },
        required: ["issue_id", "area"],
      },
    },
    {
      name: "crop_remedy",
      description: "Get symptoms, what to do and how to prevent a crop disease from the app's library.",
      input_schema: { type: "object", properties: { disease_id: { type: "string", enum: REMEDIES.diseases.map((d) => d.id) } }, required: ["disease_id"] },
    },
    {
      name: "open_complaint_form",
      description: "Open the app's 'Report a problem' form so the person can add a photo and get a ready letter. Use it once the person wants to complain and you know the problem.",
      input_schema: { type: "object", properties: { issue_id: { type: "string", enum: issues().map((i) => i.id) } }, required: ["issue_id"] },
    },
  ];
}

export function runTool(name, args, actions) {
  try {
    if (name === "find_office") {
      const r = route(args.issue_id, args.area);
      if (!r || !r.short_en) return { error: "bad input" };
      return {
        office: r.short_en, office_tamil: r.short_ta,
        helplines: r.helplines.map((h) => ({ name: h.label_en, number: h.number, verified: !!h.checked })),
        note: "If a helpline is not verified, tell the person to confirm the number before relying on it.",
      };
    }
    if (name === "crop_remedy") {
      const d = disease(args.disease_id);
      if (!d) return { error: "unknown disease" };
      return { name: d.name_en, symptoms: d.symptoms_en, what_to_do: d.action_en, prevention: d.prevent_en,
        note: "Advice is general. For chemicals the person must ask a local agriculture officer." };
    }
    if (name === "open_complaint_form") {
      if (!issueById(args.issue_id)) return { error: "bad input" };
      actions.push({ type: "open_form", issue_id: args.issue_id });
      return { ok: true, note: "The form is now open on the person's screen." };
    }
  } catch (e) {
    return { error: "bad input" };
  }
  return { error: "unknown tool" };
}

export function systemPrompt(lang) {
  const iss = issues().map((i) => `${i.id} = ${i.name_en}`).join("; ");
  const dis = REMEDIES.diseases.map((d) => d.id).join("; ");
  const speak = lang === "ta"
    ? "Reply in simple, spoken Tamil (தமிழ்) using Tamil script. If the person writes in English, reply in English."
    : "Reply in simple English. If the person writes in Tamil, reply in Tamil script.";
  return `You are Oru Udhavi (ஒரு உதவி, "One Help"), a friendly helper inside a Tamil Nadu app for ordinary people, many of them not used to apps.
You help with two things: (1) complaints about local problems (roads, garbage, drains, streetlights, water, electricity, stray animals) - find the right office and helpline; (2) crop leaf diseases - explain the remedy.
${speak}
Your replies are READ ALOUD, so: 1 to 3 short sentences, plain words, no markdown, no bullet symbols, no emojis, no tables. Say phone numbers digit by digit grouped in a natural way. Ask at most one question at a time.
For a complaint, you need to know the problem and whether the place is Chennai, another city or town, or a village. Ask if missing. Then call find_office and give the office and helpline. Offer to open the form (open_complaint_form) so they can add a photo and get a letter.
For a crop problem, ask the crop and what they see. The app can check a leaf photo itself on the Check my crop screen. If it matches a disease in the library, call crop_remedy and explain. Never name a chemical, pesticide dose or brand; tell them to ask the local agriculture officer.
NEVER invent phone numbers, offices or rules. Use only what the tools return. If a helpline is not marked verified, say to confirm it first. If unsure, say so.
Emergencies (fire, accident, crime, medical): tell them to call 112 right away.
Problem ids: ${iss}. Disease ids: ${dis}.
Stay on these topics; for anything else say kindly that you can help with complaints and crop diseases only.`;
}

// ---- the chat ----
// history entries: {role:"user",text} | {role:"assistant",text,calls:[{id,name,args}]} | {role:"tool",results:[{id,name,content}]}
export class Assistant {
  constructor(fetchImpl = (...a) => fetch(...a)) { this.history = []; this.fetch = fetchImpl; }
  reset() { this.history = []; }

  async _http(url, payload, headers) {
    let r;
    try {
      r = await this.fetch(url, { method: "POST", headers: { "content-type": "application/json", ...headers }, body: JSON.stringify(payload) });
    } catch (e) {
      throw new AssistantError(provider() === "ollama" ? "no_local" : "offline");
    }
    if (r.status === 401 || r.status === 403) throw new AssistantError("bad_key");
    if (r.status === 429) throw new AssistantError("busy");
    if (!r.ok) throw new AssistantError("server");
    try { return await r.json(); } catch (e) { throw new AssistantError("server"); }
  }

  async _complete(lang) {
    const prov = provider();
    if (PROVIDERS[prov].needsKey && !apiKey(prov)) throw new AssistantError("no_key");
    const msgs = this.history.slice(-KEEP);
    return prov === "anthropic" ? this._anthropic(msgs, lang) : this._openai(msgs, lang, prov);
  }

  async _anthropic(msgs, lang) {
    const out = msgs.map((m) => {
      if (m.role === "user") return { role: "user", content: m.text };
      if (m.role === "assistant") {
        const blocks = (m.text ? [{ type: "text", text: m.text }] : []).concat(
          m.calls.map((c) => ({ type: "tool_use", id: c.id, name: c.name, input: c.args })));
        return { role: "assistant", content: blocks };
      }
      return { role: "user", content: m.results.map((r) => ({ type: "tool_result", tool_use_id: r.id, content: r.content })) };
    });
    const data = await this._http(baseUrl(), {
      model: modelName(), max_tokens: 500, system: systemPrompt(lang), tools: tools(), messages: out,
    }, { "x-api-key": apiKey("anthropic"), "anthropic-version": "2023-06-01", "anthropic-dangerous-direct-browser-access": "true" });
    const content = data.content || [];
    const text = content.filter((b) => b.type === "text").map((b) => b.text || "").join("").trim();
    const calls = content.filter((b) => b.type === "tool_use").map((b) => ({ id: b.id, name: b.name, args: b.input || {} }));
    return [text, calls];
  }

  async _openai(msgs, lang, prov) {
    const out = [{ role: "system", content: systemPrompt(lang) }];
    for (const m of msgs) {
      if (m.role === "user") out.push({ role: "user", content: m.text });
      else if (m.role === "assistant") {
        const d = { role: "assistant", content: m.text || null };
        if (m.calls.length) d.tool_calls = m.calls.map((c) => ({ id: c.id, type: "function", function: { name: c.name, arguments: JSON.stringify(c.args) } }));
        out.push(d);
      } else for (const r of m.results) out.push({ role: "tool", tool_call_id: r.id, content: r.content });
    }
    const ts = tools().map((t) => ({ type: "function", function: { name: t.name, description: t.description, parameters: t.input_schema } }));
    const key = apiKey(prov);
    const data = await this._http(baseUrl().replace(/\/$/, "") + "/chat/completions",
      { model: modelName(), max_tokens: 500, messages: out, tools: ts }, key ? { authorization: "Bearer " + key } : {});
    const msg = data && data.choices && data.choices[0] && data.choices[0].message;
    if (!msg) throw new AssistantError("server");
    const calls = (msg.tool_calls || []).map((c, i) => {
      let args = {};
      try { args = JSON.parse((c.function && c.function.arguments) || "{}"); } catch (e) { /* keep {} */ }
      return { id: c.id || `call_${i}`, name: c.function.name, args };
    });
    return [(msg.content || "").trim(), calls];
  }

  /** -> {reply, actions}. Throws AssistantError(code). */
  async ask(text, lang) {
    const start = this.history.length;
    this.history.push({ role: "user", text });
    const actions = [];
    try {
      for (let i = 0; i < MAX_TOOL_ROUNDS; i++) {
        const [reply, calls] = await this._complete(lang);
        this.history.push({ role: "assistant", text: reply, calls });
        if (!calls.length) { this._trim(); return { reply: reply || "…", actions }; }
        this.history.push({ role: "tool", results: calls.map((c) => ({ id: c.id, name: c.name, content: JSON.stringify(runTool(c.name, c.args, actions)) })) });
      }
      this._trim();
      return { reply: "…", actions };
    } catch (e) {
      if (e instanceof AssistantError) this.history.splice(start); // forget the failed turn so a retry works
      throw e;
    }
  }

  _trim() {
    const h = this.history;
    while (h.length > KEEP) h.shift();
    while (h.length && h[0].role !== "user") h.shift();
  }
}
