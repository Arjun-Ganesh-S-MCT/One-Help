// Speaking and listening, using what the phone's browser provides (free, no key).
// Speaking: speechSynthesis (needs a Tamil voice installed on the phone for Tamil).
// Listening: SpeechRecognition (Chrome on Android; needs internet). Without them the chat still works by typing.
const SR = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;
const LOCALE = { ta: "ta-IN", en: "en-IN" };

export const canSpeak = () => typeof speechSynthesis !== "undefined" && typeof SpeechSynthesisUtterance !== "undefined";
export const canListen = () => !!SR;

export function cleanForSpeech(text) {
  return text.replace(/[*#_`•>|]/g, " ").replace(/\s+/g, " ").trim();
}

function voiceFor(lang) {
  const voices = speechSynthesis.getVoices() || [];
  const want = LOCALE[lang].toLowerCase();
  return voices.find((v) => v.lang.toLowerCase() === want) || voices.find((v) => v.lang.toLowerCase().startsWith(lang));
}

/** Returns "ok" or "no_voice" (no installed voice for that language) so the screen can say so. */
export function speak(text, lang, { onstart, onend } = {}) {
  if (!canSpeak()) return "unsupported";
  stopSpeaking();
  const clean = cleanForSpeech(text);
  if (!clean) return "ok";
  const u = new SpeechSynthesisUtterance(clean);
  u.lang = LOCALE[lang];
  const v = voiceFor(lang);
  if (v) u.voice = v;
  u.onstart = () => onstart && onstart();
  u.onend = u.onerror = () => onend && onend();
  speechSynthesis.speak(u);
  return v ? "ok" : "no_voice";
}
export function stopSpeaking() { if (canSpeak()) speechSynthesis.cancel(); }

/** One listening session. cb: {onheard(text), onerror(code), onend()}. Returns {stop()} */
export function listen(lang, cb) {
  if (!SR) { cb.onerror("unsupported"); return { stop() {} }; }
  const rec = new SR();
  rec.lang = LOCALE[lang];
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  let heard = false;
  rec.onresult = (e) => { heard = true; cb.onheard(e.results[0][0].transcript); };
  rec.onerror = (e) => {
    const map = { "not-allowed": "no_mic", "service-not-allowed": "no_mic", "audio-capture": "no_mic", "no-speech": "too_short", "network": "offline" };
    if (e.error !== "aborted") cb.onerror(map[e.error] || "not_understood");
  };
  rec.onend = () => { if (!heard) { /* error already reported or nothing said */ } cb.onend && cb.onend(); };
  try { rec.start(); } catch (e) { cb.onerror("no_mic"); }
  return { stop() { try { rec.stop(); } catch (e) { /* already stopped */ } } };
}
