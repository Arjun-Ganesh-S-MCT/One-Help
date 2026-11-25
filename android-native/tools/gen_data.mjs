// Writes the shared data (texts, issues, offices, remedies) for the native Android app.
// Source of truth is the Python app; mobile/www/js/data.js is generated from it by tools/gen_mobile_data.py.
import { STRINGS, ISSUES, DEPTS, REMEDIES, LABEL_RULES } from "../../mobile/www/js/data.js";
import { tools, systemPrompt } from "../../mobile/www/js/assistant.js";
import fs from "fs";
const out = new URL("../app/src/main/assets/data.json", import.meta.url);
fs.writeFileSync(out, JSON.stringify({ strings: STRINGS, issues: ISSUES, depts: DEPTS, remedies: REMEDIES, label_rules: LABEL_RULES, tools: tools(), prompt: { ta: systemPrompt("ta"), en: systemPrompt("en") } }));
fs.copyFileSync(new URL("../../mobile/tests/parity.json", import.meta.url), new URL("../app/src/test/resources/parity.json", import.meta.url));
console.log("android data written");
