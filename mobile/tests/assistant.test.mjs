import test from "node:test";
import assert from "node:assert/strict";

// tiny localStorage for node
const mem = new Map();
globalThis.localStorage = { getItem: (k) => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => mem.set(k, String(v)), removeItem: (k) => mem.delete(k) };

const A = await import("../www/js/assistant.js");

const res = (status, body) => ({ status, ok: status >= 200 && status < 300, json: async () => body });
const toOpenAI = (c) => ({
  choices: [{ message: {
    content: c.filter((b) => b.type === "text").map((b) => b.text).join("") || null,
    tool_calls: c.filter((b) => b.type === "tool_use").map((b) => ({ id: b.id, type: "function", function: { name: b.name, arguments: JSON.stringify(b.input) } })),
  } }],
});
function fake(provider, script) {
  const seen = [];
  const f = async (url, init) => {
    seen.push({ url, init, body: JSON.parse(init.body) });
    const [status, content] = script.shift();
    if (status !== 200) return res(status, {});
    return res(200, provider === "anthropic" ? { content } : toOpenAI(content));
  };
  return { f, seen };
}
const text = (t) => [{ type: "text", text: t }];

for (const prov of ["anthropic", "gemini", "groq"]) {
  const setup = () => { mem.clear(); A.saveSettings(prov, "k1"); };

  test(`${prov}: tool loop uses our data`, async () => {
    setup();
    const { f, seen } = fake(prov, [
      [200, [{ type: "tool_use", id: "t1", name: "find_office", input: { issue_id: "road", area: "chennai" } }]],
      [200, text("Call 1913.")],
    ]);
    const a = new A.Assistant(f);
    const r = await a.ask("pothole in Chennai", "en");
    assert.equal(r.reply, "Call 1913.");
    const last = seen[1].body.messages.at(-1);
    const result = prov === "anthropic" ? last.content[0].content : last.content;
    assert.match(result, /1913/);
    const h = Object.fromEntries(Object.entries(seen[0].init.headers).map(([k, v]) => [k.toLowerCase(), v]));
    assert.ok(prov === "anthropic" ? h["x-api-key"] === "k1" : h.authorization === "Bearer k1");
  });

  test(`${prov}: open form action and bad tool input`, async () => {
    setup();
    const { f } = fake(prov, [
      [200, [{ type: "tool_use", id: "t1", name: "open_complaint_form", input: { issue_id: "garbage" } },
             { type: "tool_use", id: "t2", name: "find_office", input: { issue_id: "nope", area: "x" } }]],
      [200, text("ok")],
    ]);
    const r = await new A.Assistant(f).ask("garbage", "ta");
    assert.deepEqual(r.actions, [{ type: "open_form", issue_id: "garbage" }]);
  });

  for (const [status, code] of [[401, "bad_key"], [429, "busy"], [500, "server"]]) {
    test(`${prov}: HTTP ${status} -> ${code}, failed turn forgotten`, async () => {
      setup();
      const { f } = fake(prov, [[status], [200, text("fine")]]);
      const a = new A.Assistant(f);
      await assert.rejects(a.ask("hi", "en"), (e) => e.code === code);
      assert.equal(a.history.length, 0);
      assert.equal((await a.ask("hi", "en")).reply, "fine");
    });
  }

  test(`${prov}: offline`, async () => {
    setup();
    const a = new A.Assistant(async () => { throw new TypeError("network"); });
    await assert.rejects(a.ask("hi", "en"), (e) => e.code === "offline");
  });
}

test("no key -> no_key; ollama needs none and reports not running", async () => {
  mem.clear();
  await assert.rejects(new A.Assistant(async () => res(200, {})).ask("hi", "en"), (e) => e.code === "no_key");
  A.saveSettings("ollama");
  assert.ok(A.isConfigured());
  await assert.rejects(new A.Assistant(async () => { throw new TypeError("x"); }).ask("hi", "en"), (e) => e.code === "no_local");
});

test("history trim never starts on a tool result", async () => {
  mem.clear(); A.saveSettings("gemini", "k");
  const script = [];
  for (let i = 0; i < 20; i++) script.push([200, text("r" + i)]);
  const a = new A.Assistant(fake("gemini", script).f);
  for (let i = 0; i < 20; i++) await a.ask("q" + i, "en");
  assert.ok(a.history.length <= 24 && a.history[0].role === "user");
});

test("garbled reply is a server error", async () => {
  mem.clear(); A.saveSettings("gemini", "k");
  await assert.rejects(new A.Assistant(async () => res(200, { nope: 1 })).ask("hi", "en"), (e) => e.code === "server");
});

test("system prompt", () => {
  assert.match(A.systemPrompt("ta"), /Tamil/);
  assert.match(A.systemPrompt("en"), /NEVER invent/);
});
