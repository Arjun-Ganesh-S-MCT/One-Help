// Checks that the JavaScript logic behaves exactly like the Python app (oru/*.py).
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildLetter, route, suggestIssue, validate, newComplaint } from "../www/js/complaint.js";
import { interpret, pretty } from "../www/js/labels.js";
import { decide, softmaxTop } from "../www/js/crop.js";

const P = JSON.parse(readFileSync(new URL("./parity.json", import.meta.url), "utf8"));
const [y, m, d] = P.today.split("-").map(Number);
const TODAY = new Date(y, m - 1, d);

test("letters match Python (all issues x areas x languages x variants)", () => {
  for (const x of P.letters) {
    const c = newComplaint({ ...x.c });
    assert.equal(buildLetter(c, x.lang, TODAY), x.letter, `${x.c.issue_id}/${x.c.area}/${x.lang}`);
  }
  assert.ok(P.letters.length > 100);
});
test("routes match Python", () => {
  for (const x of P.routes) assert.deepEqual(route(x.issue, x.area), x.route, `${x.issue}/${x.area}`);
});
test("issue suggestion matches Python", () => {
  for (const x of P.suggest) assert.equal(suggestIssue(x.text), x.id, x.text);
});
test("all 38 PlantVillage labels are read like Python", () => {
  assert.equal(P.labels.length, 38);
  for (const x of P.labels) assert.deepEqual(interpret(x.raw), { ...x.reading }, x.raw);
});
test("pretty names", () => {
  assert.equal(pretty("Tomato___Late_blight"), "Tomato - Late blight");
});
test("60% rule", () => {
  assert.equal(decide(["Tomato___Late_blight", 0.59]).kind, "unsure");
  const r = decide(["Tomato___Late_blight", 0.6]);
  assert.equal(r.kind, "disease");
  assert.equal(r.diseaseId, "tomato_late_blight");
});
test("softmax", () => {
  const top = softmaxTop([1, 3, 2], ["a", "b", "c"], 2);
  assert.equal(top[0][0], "b");
  assert.ok(Math.abs(top.reduce((s, x) => s + x[1], 0) - (Math.exp(0) + Math.exp(-1)) / (Math.exp(0) + Math.exp(-1) + Math.exp(-2))) < 1e-9);
});
test("form validation order", () => {
  assert.equal(validate(newComplaint()), "err_issue");
  assert.equal(validate(newComplaint({ issue_id: "road", area: "city" })), "err_town");
  assert.equal(validate(newComplaint({ issue_id: "road", area: "chennai" })), "err_address");
  assert.equal(validate(newComplaint({ issue_id: "road", address: "x" })), "err_name");
  assert.equal(validate(newComplaint({ issue_id: "road", address: "x", name: "y" })), null);
});
