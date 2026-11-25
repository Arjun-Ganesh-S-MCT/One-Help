// Tamil / English text. Tamil is the default language.
import { STRINGS } from "./data.js";

let lang = "ta";
try { lang = localStorage.getItem("oru.lang") || "ta"; } catch (e) { /* private mode */ }
const listeners = new Set();

export const getLang = () => lang;
export function setLang(code) {
  if ((code !== "ta" && code !== "en") || code === lang) return;
  lang = code;
  try { localStorage.setItem("oru.lang", code); } catch (e) { /* ignore */ }
  document.documentElement.lang = code;
  listeners.forEach((f) => f());
}
export const onLang = (f) => { listeners.add(f); return () => listeners.delete(f); };

/** t("key", {n: 3}) -> text in the current language ({x} placeholders are filled in). */
export function t(key, vars) {
  const e = STRINGS[key];
  if (!e) return key;
  let s = e[lang];
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(String(v));
  return s;
}
/** pick(issue, "name") -> issue.name_ta or issue.name_en */
export const pick = (obj, base) => obj[`${base}_${lang}`];
