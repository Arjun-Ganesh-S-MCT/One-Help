// Saves the user's complaints on their own phone (localStorage, no internet needed).
const KEY = "oru.complaints.v1";

function read() {
  try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; }
}
function write(rows) {
  try { localStorage.setItem(KEY, JSON.stringify(rows)); } catch (e) { /* storage full or blocked */ }
}

export const store = {
  add(issue_id, area, area_text, lang, letter, c = null) {
    const rows = read();
    const id = rows.reduce((m, r) => Math.max(m, r.id), 0) + 1;
    rows.push({ id, created: new Date().toISOString().slice(0, 19), issue_id, area, area_text, lang, letter, c, status: "draft" });
    write(rows);
    return id;
  },
  setLetterLang(id, lang, letter) { write(read().map((r) => (r.id === id ? { ...r, lang, letter } : r))); },
  updateLetter(id, lang, letter) { write(read().map((r) => (r.id === id ? { ...r, lang, letter } : r))); },
  setStatus(id, status) { write(read().map((r) => (r.id === id ? { ...r, status } : r))); },
  remove(id) { write(read().filter((r) => r.id !== id)); },
  all() { return read().sort((a, b) => b.id - a.id); },
  get(id) { return read().find((r) => r.id === id) || null; },
};
