"""The talking helper. Sends the chat to an AI service (free ones work: Gemini, Groq, or Ollama on
your own computer; Claude also works) and lets it look up
OUR data (offices, helplines, crop remedies) through tools, so phone numbers and remedies
always come from the app's own checked lists and are never invented.

No Qt in here so it is easy to test."""
import json
import os
import urllib.error
import urllib.request

from . import complaint as C
from . import crop
from .paths import data_dir

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MAX_TOOL_ROUNDS = 5
KEEP_MESSAGES = 24        # old turns are dropped so long chats stay cheap


class AssistantError(Exception):
    """The text is a short code: no_key, bad_key, offline, busy, server."""

    @property
    def code(self) -> str:
        return str(self)


# ------------------------------------------------------------------ settings
# Every provider except "anthropic" speaks the common OpenAI-style chat API, so one code path covers them.
# Model names and free limits change over time: override with ORU_MODEL (or "model" in the config file).
PROVIDERS = {
    "gemini": {"name": "Google Gemini (free key)", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
               "model": "gemini-2.5-flash", "needs_key": True, "where": "aistudio.google.com"},
    "groq": {"name": "Groq (free key)", "base": "https://api.groq.com/openai/v1",
             "model": "llama-3.3-70b-versatile", "needs_key": True, "where": "console.groq.com"},
    "ollama": {"name": "Ollama (on this computer, no key)", "base": "http://localhost:11434/v1",
               "model": "qwen2.5:7b", "needs_key": False, "where": "ollama.com"},
    "anthropic": {"name": "Claude (paid key)", "base": ANTHROPIC_URL,
                  "model": "claude-haiku-5-5", "needs_key": True, "where": "console.anthropic.com"},
}
DEFAULT_PROVIDER = "gemini"


def _config_path():
    root = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    p = os.path.join(root, "oru-udhavi")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, "config.json")


def load_config() -> dict:
    try:
        with open(_config_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(provider: str, key: str = "") -> None:
    cfg = load_config()
    cfg["provider"] = provider
    cfg.setdefault("keys", {})[provider] = key.strip()
    path = _config_path()
    with open(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w", encoding="utf-8") as f:
        json.dump(cfg, f)


def provider() -> str:
    p = os.environ.get("ORU_PROVIDER") or load_config().get("provider") or DEFAULT_PROVIDER
    return p if p in PROVIDERS else DEFAULT_PROVIDER


def api_key(prov: str = None) -> str:
    prov = prov or provider()
    env = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY"}.get(prov)
    return (os.environ.get(env, "").strip() if env else "") or load_config().get("keys", {}).get(prov, "").strip()


def is_configured() -> bool:
    prov = provider()
    return (not PROVIDERS[prov]["needs_key"]) or bool(api_key(prov))


def model_name() -> str:
    return os.environ.get("ORU_MODEL") or load_config().get("model") or PROVIDERS[provider()]["model"]


def base_url() -> str:
    return os.environ.get("ORU_BASE_URL") or PROVIDERS[provider()]["base"]


# ------------------------------------------------------------------ tools
TOOLS = [
    {
        "name": "find_office",
        "description": ("Find which office should get a complaint and its helpline, from the app's own "
                        "checked list. Always use this before telling the person where to complain."),
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_id": {"type": "string", "enum": [i["id"] for i in C.issues()]},
                "area": {"type": "string", "enum": ["chennai", "city", "village"],
                         "description": "chennai = Chennai city; city = other city or town (municipality/town panchayat); village = village panchayat"},
            },
            "required": ["issue_id", "area"],
        },
    },
    {
        "name": "crop_remedy",
        "description": "Get symptoms, what to do and how to prevent a crop disease from the app's library.",
        "input_schema": {
            "type": "object",
            "properties": {"disease_id": {"type": "string", "enum": [d["id"] for d in crop._load()["diseases"]]}},
            "required": ["disease_id"],
        },
    },
    {
        "name": "open_complaint_form",
        "description": ("Open the app's 'Report a problem' form so the person can add a photo and get a ready "
                        "letter. Use it once the person wants to complain and you know the problem."),
        "input_schema": {
            "type": "object",
            "properties": {"issue_id": {"type": "string", "enum": [i["id"] for i in C.issues()]}},
            "required": ["issue_id"],
        },
    },
]


def run_tool(name: str, args: dict, actions: list) -> dict:
    """Runs one tool. `actions` collects things the screen should do (like opening the form)."""
    try:
        if name == "find_office":
            r = C.route(args["issue_id"], args["area"])
            return {
                "office": r["short_en"], "office_tamil": r["short_ta"],
                "helplines": [{"name": h["label_en"], "number": h["number"],
                               "verified": bool(h.get("checked"))} for h in r["helplines"]],
                "note": "If a helpline is not verified, tell the person to confirm the number before relying on it.",
            }
        if name == "crop_remedy":
            d = crop.disease(args["disease_id"])
            if not d:
                return {"error": "unknown disease"}
            return {"name": d["name_en"], "symptoms": d["symptoms_en"], "what_to_do": d["action_en"],
                    "prevention": d["prevent_en"],
                    "note": "Advice is general. For chemicals the person must ask a local agriculture officer."}
        if name == "open_complaint_form":
            C.issue_by_id(args["issue_id"])
            actions.append({"type": "open_form", "issue_id": args["issue_id"]})
            return {"ok": True, "note": "The form is now open on the person's screen."}
    except (KeyError, StopIteration) as e:
        return {"error": f"bad input: {e}"}
    return {"error": "unknown tool"}


def system_prompt(lang: str) -> str:
    issues = "; ".join(f"{i['id']} = {i['name_en']}" for i in C.issues())
    diseases = "; ".join(f"{d['id']}" for d in crop._load()["diseases"])
    speak = ("Reply in simple, spoken Tamil (தமிழ்) using Tamil script. If the person writes in English, reply in English."
             if lang == "ta" else
             "Reply in simple English. If the person writes in Tamil, reply in Tamil script.")
    return f"""You are Oru Udhavi (ஒரு உதவி, "One Help"), a friendly helper inside a Tamil Nadu app for ordinary people, many of them not used to apps.
You help with two things: (1) complaints about local problems (roads, garbage, drains, streetlights, water, electricity, stray animals) - find the right office and helpline; (2) crop leaf diseases - explain the remedy.
{speak}
Your replies are READ ALOUD, so: 1 to 3 short sentences, plain words, no markdown, no bullet symbols, no emojis, no tables. Say phone numbers digit by digit grouped in a natural way. Ask at most one question at a time.
For a complaint, you need to know the problem and whether the place is Chennai, another city or town, or a village. Ask if missing. Then call find_office and give the office and helpline. Offer to open the form (open_complaint_form) so they can add a photo and get a letter.
For a crop problem, ask the crop and what they see. The app can check a leaf photo itself on the Check my crop screen. If it matches a disease in the library, call crop_remedy and explain. Never name a chemical, pesticide dose or brand; tell them to ask the local agriculture officer.
NEVER invent phone numbers, offices or rules. Use only what the tools return. If a helpline is not marked verified, say to confirm it first. If unsure, say so.
Emergencies (fire, accident, crime, medical): tell them to call 112 right away.
Problem ids: {issues}. Disease ids: {diseases}.
Stay on these topics; for anything else say kindly that you can help with complaints and crop diseases only."""


# ------------------------------------------------------------------ the chat
# History is kept in a neutral form and translated for each kind of service:
#   {"role": "user", "text": str}
#   {"role": "assistant", "text": str, "calls": [{"id", "name", "args"}]}
#   {"role": "tool", "results": [{"id", "name", "content": str}]}
class Assistant:
    def __init__(self):
        self.history = []

    def reset(self):
        self.history = []

    def _http(self, url: str, payload: dict, headers: dict) -> dict:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                     headers={"content-type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AssistantError("bad_key")
            if e.code == 429:
                raise AssistantError("busy")
            raise AssistantError("server")
        except (urllib.error.URLError, TimeoutError, OSError):
            raise AssistantError("no_local" if provider() == "ollama" else "offline")
        except ValueError:
            raise AssistantError("server")

    # -- one round trip: returns (text, [calls])
    def _complete(self, lang: str):
        prov = provider()
        if PROVIDERS[prov]["needs_key"] and not api_key(prov):
            raise AssistantError("no_key")
        msgs = self.history[-KEEP_MESSAGES:]
        if prov == "anthropic":
            return self._anthropic(msgs, lang)
        return self._openai(msgs, lang, prov)

    def _anthropic(self, msgs, lang):
        out = []
        for m in msgs:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["text"]})
            elif m["role"] == "assistant":
                blocks = ([{"type": "text", "text": m["text"]}] if m["text"] else []) + [
                    {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]} for c in m["calls"]]
                out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": "user", "content": [
                    {"type": "tool_result", "tool_use_id": r["id"], "content": r["content"]} for r in m["results"]]})
        data = self._http(base_url(), {
            "model": model_name(), "max_tokens": 500, "system": system_prompt(lang),
            "tools": TOOLS, "messages": out},
            {"x-api-key": api_key("anthropic"), "anthropic-version": "2023-06-01"})
        content = data.get("content", [])
        text = "".join(b.get("text", "") for b in content if b.get("type") == "text").strip()
        calls = [{"id": b["id"], "name": b["name"], "args": b.get("input", {})}
                 for b in content if b.get("type") == "tool_use"]
        return text, calls

    def _openai(self, msgs, lang, prov):
        out = [{"role": "system", "content": system_prompt(lang)}]
        for m in msgs:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["text"]})
            elif m["role"] == "assistant":
                d = {"role": "assistant", "content": m["text"] or None}
                if m["calls"]:
                    d["tool_calls"] = [{"id": c["id"], "type": "function", "function": {
                        "name": c["name"], "arguments": json.dumps(c["args"])}} for c in m["calls"]]
                out.append(d)
            else:
                out += [{"role": "tool", "tool_call_id": r["id"], "content": r["content"]} for r in m["results"]]
        tools = [{"type": "function", "function": {
            "name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in TOOLS]
        headers = {"authorization": "Bearer " + api_key(prov)} if api_key(prov) else {}
        data = self._http(base_url().rstrip("/") + "/chat/completions", {
            "model": model_name(), "max_tokens": 500, "messages": out, "tools": tools}, headers)
        try:
            msg = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            raise AssistantError("server")
        calls = []
        for i, c in enumerate(msg.get("tool_calls") or []):
            try:
                args = json.loads(c["function"].get("arguments") or "{}")
            except ValueError:
                args = {}
            calls.append({"id": c.get("id") or f"call_{i}", "name": c["function"]["name"], "args": args})
        return (msg.get("content") or "").strip(), calls

    def ask(self, text: str, lang: str):
        """Returns (reply_text, actions). Raises AssistantError(code)."""
        start = len(self.history)
        self.history.append({"role": "user", "text": text})
        actions = []
        try:
            for _ in range(MAX_TOOL_ROUNDS):
                reply, calls = self._complete(lang)
                self.history.append({"role": "assistant", "text": reply, "calls": calls})
                if not calls:
                    self._trim()
                    return reply or "…", actions
                self.history.append({"role": "tool", "results": [
                    {"id": c["id"], "name": c["name"],
                     "content": json.dumps(run_tool(c["name"], c["args"], actions), ensure_ascii=False)}
                    for c in calls]})
            self._trim()
            return "…", actions
        except AssistantError:
            del self.history[start:]      # forget the failed turn so the user can just retry
            raise

    def _trim(self):
        """Keep the history short but never start on a tool result (it would be orphaned)."""
        h = self.history
        while len(h) > KEEP_MESSAGES:
            h.pop(0)
        while h and h[0]["role"] != "user":
            h.pop(0)
