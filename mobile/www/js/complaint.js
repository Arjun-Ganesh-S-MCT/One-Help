// Complaint logic: guess the problem, find the right office, write the letter.
// Same behaviour as oru/complaint.py (checked by tests/parity.test.mjs).
import { ISSUES, DEPTS } from "./data.js";

export const issues = () => ISSUES;
export const issueById = (id) => ISSUES.find((i) => i.id === id);

/** Very simple keyword match (English + Tamil). Returns an issue id or null. */
export function suggestIssue(text) {
  const tx = (text || "").toLowerCase();
  let best = null, bestScore = 0;
  for (const it of ISSUES) {
    const score = it.keywords.reduce((n, k) => n + (tx.includes(k.toLowerCase()) ? 1 : 0), 0);
    if (score > bestScore) { best = it.id; bestScore = score; }
  }
  return best;
}

/** Which office should get this complaint? area = chennai | city | village */
export function route(issueId, area) {
  const kind = DEPTS.issue_route[issueId];
  let block;
  if (kind === "power") block = DEPTS.authorities.power;
  else block = DEPTS.authorities[area][kind] || DEPTS.authorities[area].local_body;
  let helplines = [...block.helplines];
  if (!helplines.length) helplines = [DEPTS.fallback_helpline];
  return { ...block, helplines };
}

export const emergencyNumbers = () => DEPTS.emergency;

export function newComplaint(o = {}) {
  return { issue_id: "", area: "chennai", town: "", address: "", landmark: "", name: "", phone: "", extra: "", has_photo: false, ...o };
}

const pad = (n) => String(n).padStart(2, "0");
export const stamp = (d) => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;

export function buildLetter(c, lang, today = new Date()) {
  const block = route(c.issue_id, c.area);
  const town = c.town.trim() || (lang === "ta" ? "சென்னை" : "Chennai");
  const toBlock = block[lang].split("{town}").join(town);
  const issue = issueById(c.issue_id);
  const loc = c.landmark.trim() || c.address.trim();
  const sentence = issue[`sentence_${lang}`].split("{loc}").join(loc);
  const addressLine = c.address.trim() + (c.town.trim() ? ", " + c.town.trim() : "");
  const date = stamp(today);
  const extra = c.extra.trim();
  const phone = c.phone.trim();
  let lines;
  if (lang === "ta") {
    const subject = `${issue.name_ta} தொடர்பான புகார்`;
    lines = ["பெறுநர்:", toBlock, "", "அனுப்புநர்:", c.name.trim(), addressLine];
    if (phone) lines.push(`தொலைபேசி: ${phone}`);
    lines.push(
      "", `நாள்: ${date}`, "", `பொருள்: ${subject}`, "", "மதிப்புமிகு ஐயா / அம்மா,", "",
      `நான் ${addressLine} பகுதியில் வசிக்கிறேன். ${sentence}. இதனால் பொதுமக்களுக்குப் பெரும் சிரமம் ஏற்படுகிறது.` + (extra ? ` ${extra}` : ""),
      "",
      "எனவே, இந்தப் பிரச்சினையை விரைவில் நேரில் ஆய்வு செய்து சரிசெய்ய உரிய நடவடிக்கை எடுக்குமாறு பணிவுடன் கேட்டுக்கொள்கிறேன்." + (c.has_photo ? " பிரச்சினையின் புகைப்படம் இணைக்கப்பட்டுள்ளது." : ""),
      "", "நன்றி.", "", "இப்படிக்கு,", c.name.trim());
  } else {
    const subject = `Complaint regarding ${issue.name_en.toLowerCase()}`;
    lines = ["To,", toBlock, "", "From,", c.name.trim(), addressLine];
    if (phone) lines.push(`Phone: ${phone}`);
    lines.push(
      "", `Date: ${date}`, "", `Subject: ${subject}`, "", "Respected Sir / Madam,", "",
      `I am a resident of ${addressLine}. I would like to bring to your kind notice that ${sentence}. This is causing great difficulty to the public.` + (extra ? ` ${extra}` : ""),
      "",
      "I kindly request you to inspect the matter and take the necessary action at the earliest." + (c.has_photo ? " A photograph of the problem is attached." : ""),
      "", "Thank you.", "", "Yours faithfully,", c.name.trim());
  }
  return lines.join("\n");
}

/** Returns an error key (see i18n) or null, in the same order as the Python app. */
export function validate(c) {
  if (!c.issue_id) return "err_issue";
  if (c.area !== "chennai" && !c.town.trim()) return "err_town";
  if (!c.address.trim()) return "err_address";
  if (!c.name.trim()) return "err_name";
  return null;
}
