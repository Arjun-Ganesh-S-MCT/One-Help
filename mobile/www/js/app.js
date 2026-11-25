// Oru Udhavi mobile app: all screens. Plain JS, no framework.
import { t, getLang, setLang, onLang, pick } from "./i18n.js";
import { icon } from "./icons.js";
import * as C from "./complaint.js";
import * as Crop from "./crop.js";
import { store } from "./store.js";
import * as AI from "./assistant.js";
import * as V from "./voice.js";

const $app = document.getElementById("app");

// ---------- tiny helpers ----------
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "style") el.style.cssText = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) el.append(k.nodeType ? k : document.createTextNode(k));
  return el;
}
const ico = (n, s, c, w) => h("span", { html: icon(n, s, c, w), style: "display:inline-flex" });
const cap = (s) => h("div", { class: "t-cap" }, s);
const fmtDate = (iso) => { const d = new Date(iso); return d.toLocaleDateString(getLang() === "ta" ? "ta-IN" : "en-IN", { day: "numeric", month: "short", year: "numeric" }); };

let toastTimer;
function toast(msg) {
  document.querySelector(".toast")?.remove();
  const el = h("div", { class: "toast lcd t-mono", role: "status" }, msg);
  $app.append(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 2600);
}

function langSeg() {
  const mk = (code, label) => h("button", { class: getLang() === code ? "on" : "", "aria-pressed": String(getLang() === code), onclick: () => setLang(code) }, label);
  return h("div", { class: "seg well", role: "group", "aria-label": "Language" }, mk("en", "EN"), mk("ta", "தமிழ்"));
}
function header(title, backTo = "home", right) {
  return h("div", { class: "hdr" },
    h("button", { class: "key kround", "aria-label": t("back"), onclick: () => go(backTo) }, ico("back", 24, "#2B2A2E", 2.2)),
    h("div", { class: "plate well engrave" }, title),
    right || null);
}
const screen = (...kids) => h("div", { class: "col", style: "flex:1;min-height:0" }, ...kids);

// ---------- router ----------
let route = { name: "splash", arg: null };
let assistant = new AI.Assistant();
let chatLog = [];            // {who:"ai"|"me", text}
let voiceOn = true;
let draft = C.newComplaint();
let hintShown = "";
let cropState = { crop: "", result: null, diseaseId: "" };
let predictor, predictorTried = false;

export function go(name, arg = null) {
  V.stopSpeaking();
  route = { name, arg };
  render();
  history.replaceState(null, "", "#" + name);
}
function render() {
  const fn = SCREENS[route.name] || SCREENS.home;
  $app.replaceChildren(fn(route.arg));
  document.title = t("app_name");
}
onLang(() => {
  if (route.name === "letter") { relocalizeLetter(); }
  render();
});

// ---------- 1 splash ----------
function splash() {
  setTimeout(() => { if (route.name === "splash") go("home"); }, 2200);
  return h("button", { class: "splash-hit", "aria-label": t("app_name"), onclick: () => go("home") },
    h("img", { src: "img/logo-wide-transparent.png", alt: t("app_name"), style: "width:78%;max-width:340px;height:auto" }),
    h("div", { class: "lcd t-mono", style: "padding:10px 18px;display:flex;gap:10px;align-items:center;font-size:13px;letter-spacing:.12em;text-transform:uppercase" },
      h("span", { class: "lamp pulse" }), t("tagline")));
}

// ---------- 2 home ----------
function tile(iconName, title, sub, to, red) {
  return h("button", { class: "home-tile raise tile", onclick: () => go(to) },
    h("span", { class: red ? "ico knob-red knob" : "ico well", style: red ? "box-shadow:0 6px 12px rgba(168,16,19,.4)" : "" }, ico(iconName, 30, red ? "#fff" : "#2B2A2E", 1.9)),
    h("span", { style: "font-size:17px;font-weight:800;line-height:1.3;overflow-wrap:anywhere;max-width:100%" }, title),
    h("span", { class: "small muted" }, sub));
}
function home() {
  return screen(
    h("div", { class: "hdr" },
      h("img", { src: "img/icon-192.png", alt: "", width: 48, height: 48, style: "border-radius:14px;box-shadow:5px 5px 12px var(--sh),-4px -4px 10px var(--hi)" }),
      h("div", { class: "plate well engrave", style: "font-size:20px" }, t("app_name")),
      langSeg()),
    h("div", { class: "body pad col gap16" },
      h("div", { style: "font-size:22px;font-weight:800;line-height:1.3;padding:4px 4px 0" }, t("m_greeting")),
      h("div", { class: "tilegrid" },
        tile("list", t("home_report"), t("home_report_sub"), "report", true),
        tile("leaf", t("home_crop"), t("home_crop_sub"), "crop"),
        tile("mic", t("home_chat"), t("home_chat_sub"), "helper"),
        tile("save", t("home_history"), t("home_history_sub"), "history")),
      h("button", { class: "key-ink", style: "min-height:56px", onclick: () => go("emergency") }, ico("phone", 22, "#F4ECE2", 2), t("home_emergency")),
      h("div", { class: "note well small" }, ico("info", 20, "#5F574F"), t("m_offline_note"))));
}

// ---------- 3 report ----------
function field(label, key, opts = {}) {
  const input = h(opts.multi ? "textarea" : "input", {
    class: "field well", id: "f_" + key, value: draft[key], rows: opts.multi ? 3 : null, type: opts.type || "text",
    inputmode: opts.inputmode, autocomplete: opts.ac || "off", "aria-label": label, placeholder: label,
    oninput: (e) => { draft[key] = e.target.value; if (key === "extra" || key === "address") maybeSuggest(); },
  });
  if (!opts.multi) input.value = draft[key]; else input.textContent = draft[key];
  return input;
}
function maybeSuggest() { /* suggestion is only based on the "extra" text; see below */ }
function report(arg) {
  if (arg && arg.issue_id) { draft.issue_id = arg.issue_id; }
  const sel = draft.issue_id;
  const hint = h("div", { class: "small muted", id: "hint", style: "min-height:20px;padding:0 4px" });
  const err = h("div", { id: "err", role: "alert", class: "small", style: "font-weight:800;min-height:20px;padding:0 4px" });
  const describe = h("input", {
    class: "field well", placeholder: t("m_describe"), "aria-label": t("m_describe"), value: "",
    oninput: (e) => {
      const id = C.suggestIssue(e.target.value);
      if (id) { hint.textContent = t("hint_suggest", { x: pick(C.issueById(id), "name") }); hint.dataset.id = id; }
      else hint.textContent = "";
    },
    onchange: (e) => { const id = C.suggestIssue(e.target.value); if (id && !draft.issue_id) { draft.issue_id = id; render(); } },
  });
  const areaKey = (id, label) => h("button", { class: "key areakey" + (draft.area === id ? " on" : ""), "aria-pressed": String(draft.area === id),
    onclick: () => { draft.area = id; render(); } }, label, h("span", { class: "lamp" + (draft.area === id ? "" : " lamp-off") }));
  const photo = h("input", { type: "file", accept: "image/*", class: "hide", id: "photo",
    onchange: (e) => { draft.has_photo = !!e.target.files[0]; render(); } });
  return screen(
    header(t("report_title")),
    h("div", { class: "body pad col gap20" },
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "1"), t("step1").replace(/^\d\.\s*/, "")),
        h("div", { class: "tilegrid" }, C.issues().map((i) => h("button", {
          class: "key issue" + (draft.issue_id === i.id ? " on" : ""), "aria-pressed": String(draft.issue_id === i.id),
          onclick: () => { draft.issue_id = i.id; render(); },
        }, ico(i.icon, 22), h("span", {}, pick(i, "name")), draft.issue_id === i.id ? h("span", { class: "lamp" }) : null))),
        describe, hint),
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "2"), t("step2").replace(/^\d\.\s*/, "")),
        h("div", { class: "row gap12" },
          h("label", { for: "photo", class: "key", style: "flex:1" }, ico("camera", 22), draft.has_photo ? t("photo_change") : t("photo_choose")),
          h("span", { class: "lamp" + (draft.has_photo ? "" : " lamp-off") })),
        photo),
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "3"), t("step3").replace(/^\d\.\s*/, "")),
        h("div", { class: "stack" }, areaKey("chennai", t("area_chennai")), areaKey("city", t("area_city")), areaKey("village", t("area_village"))),
        draft.area !== "chennai" ? field(t("town_label"), "town") : null,
        field(t("address_label"), "address"), field(t("landmark_label"), "landmark")),
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "4"), t("step4").replace(/^\d\.\s*/, "")),
        field(t("name_label"), "name", { ac: "name" }), field(t("phone_label"), "phone", { type: "tel", inputmode: "tel", ac: "tel" }),
        field(t("extra_label"), "extra", { multi: true })),
      err,
      h("button", { class: "key-red", onclick: () => {
        const e = C.validate(draft);
        if (e) { err.textContent = t(e); err.scrollIntoView({ block: "center", behavior: "smooth" }); return; }
        const lang = getLang();
        const letter = C.buildLetter(draft, lang);
        const area_text = C.route(draft.issue_id, draft.area)["short_" + lang];
        const id = store.add(draft.issue_id, draft.area, area_text, lang, letter, { ...draft });
        go("letter", { id });
      } }, ico("arrow", 22, "#fff", 2.4), t("make_letter"))));
}

// ---------- 4 letter ----------
function relocalizeLetter() {
  const row = route.arg && store.get(route.arg.id);
  if (row && row.c && row.lang !== getLang()) store.setLetterLang(row.id, getLang(), C.buildLetter(row.c, getLang()));
}
function letter(arg) {
  const row = store.get(arg.id);
  if (!row) return history_();
  const c = row.c;
  const r = C.route(row.issue_id, row.area);
  const town = (c && c.town.trim()) || (getLang() === "ta" ? "சென்னை" : "Chennai");
  const area = (r["short_" + getLang()] || "").split("{town}").join(town);
  const ta = h("textarea", { class: "letter lined", "aria-label": t("result_title"), spellcheck: "false",
    oninput: (e) => store.updateLetter(row.id, row.lang, e.target.value) });
  ta.value = row.letter;
  const seg = h("div", { class: "seg well" }, ["ta", "en"].map((code) => h("button", {
    class: row.lang === code ? "on" : "", onclick: () => {
      if (c) { store.setLetterLang(row.id, code, C.buildLetter(c, code)); render(); }
      else toast("—");
    } }, code === "ta" ? "தமிழ்" : "EN")));
  const sent = row.status === "sent";
  const share = async () => {
    const text = store.get(row.id).letter;
    if (navigator.share) { try { await navigator.share({ title: t("result_title"), text }); return; } catch (e) { if (e.name === "AbortError") return; } }
    copy(text);
  };
  return screen(
    header(t("result_title"), "history"),
    h("div", { class: "body pad col gap16" },
      h("div", { class: "lcd", style: "padding:12px 16px;display:flex;flex-direction:column;gap:6px" },
        h("span", { class: "t-mono", style: "font-size:12px;letter-spacing:.12em;text-transform:uppercase;opacity:.8" }, t("send_to")),
        h("span", { style: "font-size:16px;font-weight:700" }, area)),
      r.helplines.length ? h("div", { class: "stack" }, r.helplines.map((hl) => h("a", { class: "raise-s tap", href: "tel:" + hl.number.replace(/\s/g, ""),
        style: "display:flex;align-items:center;gap:12px;padding:8px 10px 8px 16px;min-height:56px", "aria-label": `${t("m_call")} ${hl.number}` },
        h("span", { class: "grow small", style: "font-weight:800" }, hl["label_" + getLang()]),
        h("span", { class: "lcd t-mono", style: "padding:8px 14px;font-size:17px;border-radius:12px;white-space:nowrap" }, hl.number)))) : h("div", { class: "small muted" }, t("no_helpline")),
      h("div", { class: "row", style: "justify-content:space-between;gap:12px" }, cap(t("letter_lang")), seg),
      h("div", { class: "paper perf", style: "padding:6px 0 0" }, h("span", { class: "margin-line" }), ta),
      c && c.has_photo ? h("div", { class: "note well small" }, ico("camera", 20, "#5F574F"), t("photo_note")) : null,
      h("div", { class: "row gap12", style: "margin-top:10px" },
        h("button", { class: "key grow", onclick: () => copy(store.get(row.id).letter) }, ico("copy", 20), t("copy")),
        h("button", { class: "key grow", onclick: share }, ico("send", 20), t("m_share"))),
      h("button", { class: sent ? "key" : "key-red", disabled: sent, onclick: () => { store.setStatus(row.id, "sent"); toast(t("sent_done")); render(); } },
        sent ? h("span", { class: "lamp" }) : ico("check", 22, "#fff", 2.4), sent ? t("status_sent") : t("mark_sent"))));
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast(t("copied")); }
  catch (e) {
    const ta = h("textarea", { style: "position:fixed;opacity:0" }); ta.value = text; document.body.append(ta); ta.select();
    try { document.execCommand("copy"); toast(t("copied")); } catch (e2) { /* nothing more to try */ }
    ta.remove();
  }
}

// ---------- 5 crop ----------
function crop() {
  const cs = cropState;
  const status = h("div", { class: "small", id: "cstatus", role: "status", style: "min-height:20px;font-weight:700" });
  const file = h("input", { type: "file", accept: "image/*", class: "hide", id: "leaf" });
  const preview = h("div", { class: "well", style: "height:170px;display:flex;align-items:center;justify-content:center;overflow:hidden" },
    cs.preview ? h("img", { src: cs.preview, alt: "", style: "width:100%;height:100%;object-fit:cover;border-radius:18px" })
      : h("div", { class: "col", style: "align-items:center;gap:8px;text-align:center;padding:12px" }, ico("camera", 38, "#5F574F", 1.6), h("span", { class: "small muted" }, t("m_leaf_tip"))));
  file.addEventListener("change", () => { const f = file.files[0]; if (!f) return; cs.file = f; if (cs.preview) URL.revokeObjectURL(cs.preview); cs.preview = URL.createObjectURL(f); render(); });
  const check = async () => {
    if (!cs.crop) { status.textContent = t("m_no_crop"); return; }
    if (!cs.file) { status.textContent = t("m_no_photo"); return; }
    status.textContent = t("m_checking");
    if (!predictorTried) { predictorTried = true; predictor = await Crop.loadPredictor("models/"); }
    if (!predictor) { status.textContent = t("crop_ai_unavailable"); return; }
    try {
      const top = await predictor.predict(cs.file, 3);
      cs.result = Crop.decide(top[0]); cs.top = top;
      go("cropresult");
    } catch (e) { status.textContent = t("m_ai_failed"); }
  };
  const diseases = cs.crop ? Crop.diseasesFor(cs.crop) : [];
  return screen(
    header(t("crop_title")),
    h("div", { class: "body pad col gap20" },
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "1"), t("m_dial")),
        h("div", { class: "tilegrid" }, Crop.crops().map((c) => h("button", { class: "key issue" + (cs.crop === c.id ? " on" : ""), "aria-pressed": String(cs.crop === c.id),
          onclick: () => { cs.crop = c.id; render(); } }, ico("leaf", 22), pick(c, "name"), cs.crop === c.id ? h("span", { class: "lamp" }) : null)))),
      h("div", { class: "col gap12" }, h("div", { class: "step" }, h("b", {}, "2"), t("m_leaf_photo")), preview,
        h("div", { class: "row gap12" },
          h("label", { for: "leaf", class: "key grow" }, ico("camera", 22), cs.file ? t("photo_change") : t("photo_choose")),
          h("button", { class: "key-red grow", style: "min-height:48px", onclick: check }, t("crop_check"))), file, status),
      h("div", { class: "col gap12" }, cap(t("m_pick_symptoms")),
        !cs.crop ? h("div", { class: "small muted" }, t("m_no_crop")) :
          h("div", { class: "stack" }, diseases.map((d) => h("button", { class: "key areakey", style: "text-align:left", onclick: () => { cs.result = null; cs.diseaseId = d.id; go("cropresult"); } },
            pick(d, "name"), ico("arrow", 18, "#5F574F", 2.2)))))));
}

// ---------- 6 crop result ----------
function cropresult() {
  const cs = cropState, r = cs.result;
  let d = null, banner = "", kind = "disease";
  if (r) {
    kind = r.kind;
    const pct = Math.round(r.p * 100);
    if (r.kind === "unsure") banner = t("ai_not_sure");
    else if (r.kind === "healthy") banner = t("ai_healthy");
    else if (r.kind === "other") banner = t("ai_other", { x: r.pretty, p: pct });
    else { d = Crop.disease(r.diseaseId); banner = t("ai_result", { x: d ? pick(d, "name") : r.pretty, p: pct }); }
  } else d = Crop.disease(cs.diseaseId);
  const list = (items) => h("ul", { class: "ol" }, items.map((s, i) => h("li", {}, h("b", {}, String(i + 1)), h("span", {}, s))));
  return screen(
    header(t("m_result"), "crop"),
    h("div", { class: "body pad col gap16" },
      r ? h("div", { class: "lcd", style: "padding:16px 18px;display:flex;flex-direction:column;gap:10px" },
        h("span", { style: "font-size:17px;font-weight:700;line-height:1.35" }, banner),
        h("div", { class: "row gap12" }, h("span", { class: "lamp" + (kind === "disease" || kind === "healthy" ? "" : " lamp-off") }),
          h("div", { style: "flex:1;height:10px;border-radius:5px;background:#000;box-shadow:inset 0 1px 3px rgba(0,0,0,.8)" },
            h("div", { style: `width:${Math.round(r.p * 100)}%;height:100%;border-radius:5px;background:linear-gradient(90deg,#E2CBB5,#F3E6D6)` })),
          h("span", { class: "t-mono", style: "font-size:14px" }, Math.round(r.p * 100) + "%"))) : null,
      d ? h("div", { class: "paper", style: "padding:18px 18px 20px;display:flex;flex-direction:column;gap:14px" },
        h("div", { style: "font-size:20px;font-weight:800;line-height:1.3" }, pick(d, "name")),
        h("div", { class: "col gap8" }, cap(t("symptoms")), h("div", { class: "small", style: "font-weight:500" }, pick(d, "symptoms"))),
        h("div", { class: "col gap8" }, cap(t("what_to_do")), list(pick(d, "action"))),
        h("div", { class: "col gap8" }, cap(t("prevention")), list(pick(d, "prevent")))) : null,
      h("div", { class: "note well small" }, ico("info", 20, "#5F574F"), r ? t("ai_disclaimer") + " " + t("officer_note") : t("officer_note")),
      h("button", { class: "key-red", onclick: () => { cropState.result = null; cropState.file = null; cropState.preview = null; go("crop"); } }, ico("camera", 22, "#fff", 2.2), t("m_another"))));
}

// ---------- 7 helper ----------
let listening = null, busy = false, speaking = false;
function helper() {
  if (!chatLog.length) chatLog.push({ who: "ai", text: t("chat_hello") });
  const log = h("div", { class: "body col gap12", id: "log", style: "padding:20px 18px 12px", "aria-live": "polite" },
    chatLog.map((m) => h("div", { class: "bubble " + (m.who === "ai" ? "ai raise-s" : "me") }, m.text,
      m.who === "ai" && V.canSpeak() ? h("button", { class: "key kround", style: "width:36px;height:36px;min-height:36px;margin-top:8px;display:flex", "aria-label": "Speak", onclick: () => V.speak(m.text, getLang()) }, ico("speaker", 18)) : null)),
    m_state(),
    m_actions());
  const input = h("textarea", { class: "field well", rows: 1, id: "q", placeholder: t("chat_placeholder"), "aria-label": t("chat_placeholder"), style: "min-height:50px;max-height:110px",
    onkeydown: (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); } } });
  const micBtn = h("button", { class: "knob knob-ink", style: "width:90px;height:90px", "aria-label": listening ? t("chat_listening") : "Mic", "aria-pressed": String(!!listening),
    onclick: toggleMic }, h("i", {}, ico("mic", 34, "#F4ECE2", 1.8)));
  micBtn.firstChild.style.cssText += ";display:flex;align-items:center;justify-content:center";
  if (listening) micBtn.classList.replace("knob-ink", "knob-red");
  const hdrRight = h("div", { class: "row gap8" },
    h("button", { class: "key kround", "aria-label": voiceOn ? t("chat_voice_on") : t("chat_voice_off"), "aria-pressed": String(voiceOn),
      onclick: () => { voiceOn = !voiceOn; if (!voiceOn) V.stopSpeaking(); render(); } }, ico(voiceOn ? "speaker" : "speaker_off", 22)),
    h("button", { class: "key kround", "aria-label": t("chat_setup"), onclick: openSetup }, ico("gear", 22)));
  const el = screen(
    h("div", { class: "hdr" },
      h("button", { class: "key kround", "aria-label": t("back"), onclick: () => go("home") }, ico("back", 24, "#2B2A2E", 2.2)),
      h("div", { class: "plate well engrave" }, t("chat_title")), hdrRight),
    log,
    h("div", { class: "dock raise" },
      h("div", { class: "micwrap" }, micBtn),
      h("div", { class: "small", style: "text-align:center;font-weight:700;min-height:20px", role: "status" },
        listening ? t("chat_listening") : busy ? t("chat_thinking") : speaking ? t("chat_speaking") : t("m_helper_hint")),
      h("div", { class: "row gap12", style: "align-items:flex-end" }, input,
        h("button", { class: "key-red kround", style: "min-height:50px;width:50px", "aria-label": t("m_send"), onclick: () => send(input.value) }, ico("send", 22, "#fff", 2.2))),
      h("button", { class: "key", style: "min-height:40px;font-size:14px", onclick: () => { chatLog = []; assistant.reset(); render(); } }, ico("refresh", 18), t("chat_new"))));
  setTimeout(() => { const l = document.getElementById("log"); if (l) l.scrollTop = l.scrollHeight; }, 0);
  return el;
}
let pendingActions = [];
function m_state() { return busy ? h("div", { class: "bubble ai raise-s row gap8" }, h("span", { class: "lamp pulse" }), t("chat_thinking")) : null; }
function m_actions() {
  return pendingActions.length ? h("div", { class: "stack" }, pendingActions.map((a) => h("button", { class: "key-red", style: "min-height:50px;font-size:16px",
    onclick: () => { const id = a.issue_id; pendingActions = []; draft = C.newComplaint(); go("report", { issue_id: id }); } },
    ico("list", 20, "#fff", 2.2), t("chat_open_form") + ": " + pick(C.issueById(a.issue_id) || { name_ta: "", name_en: "" }, "name")))) : null;
}
function openSetup() {
  let sel = AI.provider();
  const keyIn = h("input", { class: "field well", type: "password", autocomplete: "off", "aria-label": t("chat_setup_key"), placeholder: t("chat_setup_key"), value: AI.apiKey(sel) });
  const info = h("div", { class: "small muted" });
  const sync = () => { const p = AI.PROVIDERS[sel]; keyIn.classList.toggle("hide", !p.needsKey);
    info.textContent = p.needsKey ? t("chat_setup_get", { w: p.where }) : t("chat_setup_local"); keyIn.value = AI.apiKey(sel); };
  const opts = h("div", { class: "stack" });
  const draw = () => { opts.replaceChildren(...Object.entries(AI.PROVIDERS).map(([id, p]) => h("button", { class: "key areakey" + (sel === id ? " on" : ""), "aria-pressed": String(sel === id),
    onclick: () => { sel = id; draw(); sync(); } }, t(p.name), h("span", { class: "lamp" + (sel === id ? "" : " lamp-off") })))); };
  draw(); sync();
  const modal = h("div", { class: "modal", role: "dialog", "aria-modal": "true", "aria-label": t("chat_key_title"), onclick: (e) => { if (e.target === modal) modal.remove(); } },
    h("div", { class: "sheet raise" }, h("div", { style: "font-size:20px;font-weight:800" }, t("chat_key_title")), cap(t("chat_setup_which")), opts, keyIn, info,
      h("div", { class: "row gap12" }, h("button", { class: "key grow", onclick: () => modal.remove() }, t("close")),
        h("button", { class: "key-red grow", style: "min-height:48px", onclick: () => { AI.saveSettings(sel, keyIn.value); modal.remove(); toast(t("copied").replace(/.*/, "✓")); } }, t("chat_setup_save")))));
  $app.append(modal);
}
async function send(text) {
  text = (text || "").trim();
  if (!text || busy) return;
  V.stopSpeaking();
  chatLog.push({ who: "me", text }); busy = true; pendingActions = []; render();
  try {
    const { reply, actions } = await assistant.ask(text, getLang());
    chatLog.push({ who: "ai", text: reply }); pendingActions = actions.filter((a) => a.type === "open_form");
    busy = false; render();
    if (voiceOn && V.canSpeak()) { speaking = true; const st = V.speak(reply, getLang(), { onend: () => { speaking = false; if (route.name === "helper") render(); } });
      if (st === "no_voice") { speaking = false; toast(t("chat_err_tts")); } }
  } catch (e) {
    busy = false;
    const code = e.code || "server";
    if (code === "no_key" || code === "bad_key") { chatLog.push({ who: "ai", text: code === "bad_key" ? t("chat_err_bad_key") : t("m_chat_no_key") }); render(); openSetup(); }
    else { chatLog.push({ who: "ai", text: t("chat_err_" + code) }); render(); }
  }
}
function toggleMic() {
  if (listening) { listening.stop(); return; }
  if (!V.canListen()) { toast(t("chat_no_voice_in").split(":")[0]); return; }
  V.stopSpeaking();
  listening = V.listen(getLang(), {
    onheard: (txt) => { listening = null; send(txt); },
    onerror: (code) => { listening = null; chatLog.push({ who: "ai", text: t("chat_err_" + code) }); render(); },
    onend: () => { if (listening) { listening = null; render(); } },
  });
  render();
}

// ---------- 8 history ----------
function history_() {
  const rows = store.all();
  const sentN = rows.filter((r) => r.status === "sent").length;
  return screen(
    header(t("history_title")),
    h("div", { class: "body pad col", style: "gap:26px" },
      h("div", { class: "lcd", style: "margin:0 6px;padding:12px 18px;display:flex;align-items:center;justify-content:space-between" },
        h("span", { class: "t-mono", style: "font-size:13px;letter-spacing:.12em;text-transform:uppercase" }, t("m_complaints", { n: rows.length })),
        h("span", { class: "row gap8" }, h("span", { class: "lamp" }), h("span", { class: "t-mono", style: "font-size:13px;letter-spacing:.12em;text-transform:uppercase" }, t("m_sent", { n: sentN })))),
      rows.length ? rows.map((r) => {
        const is = C.issueById(r.issue_id) || { icon: "dots", name_ta: "", name_en: "" };
        const sent = r.status === "sent";
        return h("div", { class: "paper perf" },
          h("button", { class: "slip", style: "background:none;margin-bottom:0", "aria-label": `${pick(is, "name")} – ${sent ? t("status_sent") : t("status_draft")}`, onclick: () => go("letter", { id: r.id }) },
            h("span", { class: "ico well" }, ico(is.icon, 26, "#2B2A2E", 1.8)),
            h("span", { class: "col grow", style: "gap:2px;min-width:0" },
              h("span", { style: "font-size:17px;font-weight:800;line-height:1.3" }, pick(is, "name")),
              h("span", { class: "small muted", style: "font-size:13px" }, r.area_text || ""),
              h("span", { class: "t-mono muted", style: "font-size:12px" }, fmtDate(r.created))),
            h("span", { class: "col", style: "align-items:center;gap:6px" }, h("span", { class: "lamp" + (sent ? "" : " lamp-off") }),
              h("span", { style: `font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;${sent ? "" : "color:#5F574F"}` }, sent ? t("status_sent") : t("status_draft")))));
                }) : h("div", { class: "well", style: "padding:34px 20px;text-align:center;font-weight:700" }, t("history_empty")),
      rows.length ? h("button", { class: "key", style: "min-height:44px;font-size:14px", onclick: () => manage(rows) }, ico("trash", 18), t("delete")) : null,
      h("button", { class: "key-red", style: "margin-top:auto", onclick: () => { draft = C.newComplaint(); go("report"); } }, ico("plus", 22, "#fff", 2.4), t("m_new_problem"))));
}
function manage(rows) {
  const modal = h("div", { class: "modal", role: "dialog", "aria-modal": "true", onclick: (e) => { if (e.target === modal) modal.remove(); } },
    h("div", { class: "sheet raise" }, h("div", { style: "font-size:18px;font-weight:800" }, t("m_confirm_delete")),
      h("div", { class: "stack" }, rows.map((r) => { const is = C.issueById(r.issue_id) || { name_ta: "", name_en: "" };
        return h("button", { class: "key areakey", onclick: () => { store.remove(r.id); modal.remove(); render(); } }, ico("trash", 18), `${pick(is, "name")} · ${fmtDate(r.created)}`); })),
      h("button", { class: "key", onclick: () => modal.remove() }, t("close"))));
  $app.append(modal);
}

// ---------- 9 emergency ----------
function emergency() {
  const all = C.emergencyNumbers();
  const [main, ...rest] = all;
  const dial = (n) => "tel:" + n.replace(/\s/g, "");
  return screen(
    header(t("emergency_title")),
    h("div", { class: "body pad col gap12" },
      h("div", { class: "col", style: "align-items:center;gap:14px;padding:6px 0 8px" },
        h("div", { class: "well", style: "width:196px;height:196px;border-radius:50%;display:flex;align-items:center;justify-content:center" },
          h("a", { class: "knob knob-red", href: dial(main.number), style: "width:152px;height:152px", "aria-label": `${t("m_call")} ${main.number} – ${main[getLang()]}` },
            h("i", { style: "display:flex;align-items:center;justify-content:center" }, h("span", { class: "t-mono", style: "font-size:44px;font-weight:500;color:#fff;line-height:1;text-shadow:0 -1px 0 rgba(0,0,0,.35)" }, main.number)))),
        h("span", { style: "font-size:16px;font-weight:800;text-align:center" }, t("m_emergency_hint"))),
      rest.map((e) => h("a", { class: "raise-s tap", href: dial(e.number), style: "display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 10px 8px 18px;min-height:56px", "aria-label": `${t("m_call")} ${e[getLang()]} ${e.number}` },
        h("span", { style: "font-size:16px;font-weight:800;line-height:1.3" }, e[getLang()]),
        h("span", { class: "lcd t-mono", style: "padding:8px 16px;font-size:18px;font-weight:500;border-radius:12px;white-space:nowrap" }, e.number)))));
}

const SCREENS = { splash, home, report, letter, crop, cropresult, helper, history: history_, emergency };

// ---------- start ----------
document.documentElement.lang = getLang();
const start = location.hash.slice(1);
route = { name: SCREENS[start] && start !== "letter" && start !== "cropresult" ? start : "splash", arg: null };
render();
if ("serviceWorker" in navigator && location.protocol.startsWith("http")) navigator.serviceWorker.register("sw.js").catch(() => {});
