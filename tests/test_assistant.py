import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from oru import assistant as A


class Fake(BaseHTTPRequestHandler):
    script = []          # list of (status, body) to return in order, written Claude-style
    style = "anthropic"
    seen = []

    def do_POST(self):
        n = int(self.headers["content-length"])
        Fake.seen.append({"headers": dict(self.headers), "body": json.loads(self.rfile.read(n))})
        status, body = Fake.script.pop(0)
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.end_headers()
        if Fake.style != "anthropic" and status == 200:
            body = to_openai(body)
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *a):
        pass


@pytest.fixture(params=["anthropic", "gemini"])
def server(request, monkeypatch, tmp_path):
    """Runs every test twice: against a Claude-style and an OpenAI-style (Gemini/Groq/Ollama) fake."""
    srv = HTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    monkeypatch.setenv("ORU_BASE_URL", base + ("/v1/messages" if request.param == "anthropic" else "/openai"))
    monkeypatch.setenv("ORU_PROVIDER", request.param)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    Fake.style = request.param
    Fake.script, Fake.seen = [], []
    yield Fake
    srv.shutdown()


def to_openai(body):
    """Re-shape a Claude-style reply as an OpenAI-style one."""
    msg = {"role": "assistant", "content": "".join(b.get("text", "") for b in body["content"] if b["type"] == "text") or None}
    calls = [{"id": b["id"], "type": "function", "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
             for b in body["content"] if b["type"] == "tool_use"]
    if calls:
        msg["tool_calls"] = calls
    return {"choices": [{"message": msg}]}


def text(t):
    return {"content": [{"type": "text", "text": t}]}


def test_tool_loop_uses_our_data(server):
    server.script = [
        (200, {"content": [{"type": "tool_use", "id": "t1", "name": "find_office",
                            "input": {"issue_id": "road", "area": "chennai"}}]}),
        (200, text("Call 1913.")),
    ]
    a = A.Assistant()
    reply, actions = a.ask("pothole in Chennai", "en")
    assert reply == "Call 1913."
    last = server.seen[1]["body"]["messages"][-1]
    result = last["content"][0]["content"] if server.style == "anthropic" else last["content"]
    assert "1913" in result and (server.style == "anthropic" or last["role"] == "tool")
    h = {k.lower(): v for k, v in server.seen[0]["headers"].items()}
    assert (h.get("x-api-key") if server.style == "anthropic" else h.get("authorization")) in ("test-key", "Bearer test-key")
    if server.style != "anthropic":
        assert server.seen[0]["body"]["messages"][0]["role"] == "system"
        assert server.seen[0]["body"]["tools"][0]["type"] == "function"


def test_open_form_action(server):
    server.script = [
        (200, {"content": [{"type": "tool_use", "id": "t1", "name": "open_complaint_form",
                            "input": {"issue_id": "garbage"}}]}),
        (200, text("Form opened.")),
    ]
    _, actions = A.Assistant().ask("garbage", "ta")
    assert actions == [{"type": "open_form", "issue_id": "garbage"}]


def test_bad_tool_input_does_not_crash(server):
    server.script = [
        (200, {"content": [{"type": "tool_use", "id": "t1", "name": "find_office", "input": {"issue_id": "nope", "area": "x"}}]}),
        (200, text("Sorry.")),
    ]
    assert A.Assistant().ask("x", "en")[0] == "Sorry."


@pytest.mark.parametrize("status,code", [(401, "bad_key"), (429, "busy"), (500, "server")])
def test_errors_and_retry_forgets_failed_turn(server, status, code):
    server.script = [(status, {}), (200, text("ok"))]
    a = A.Assistant()
    with pytest.raises(A.AssistantError) as e:
        a.ask("hi", "en")
    assert str(e.value) == code and a.history == []
    assert a.ask("hi", "en")[0] == "ok"


def test_no_key_then_saved(monkeypatch, tmp_path):
    for v in ("GEMINI_API_KEY", "ORU_PROVIDER", "ORU_BASE_URL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert A.provider() == "gemini" and not A.is_configured()
    with pytest.raises(A.AssistantError, match="no_key"):
        A.Assistant().ask("hi", "en")
    A.save_settings("gemini", " abc ")
    assert A.api_key() == "abc" and A.is_configured()


def test_ollama_needs_no_key_and_reports_not_running(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("ORU_PROVIDER", "ollama")
    monkeypatch.setenv("ORU_BASE_URL", "http://127.0.0.1:1/v1")
    assert A.is_configured()
    with pytest.raises(A.AssistantError, match="no_local"):
        A.Assistant().ask("hi", "en")


def test_offline(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("ORU_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("ORU_BASE_URL", "http://127.0.0.1:1/v1")
    with pytest.raises(A.AssistantError, match="offline"):
        A.Assistant().ask("hi", "en")


def test_garbled_openai_reply_is_a_server_error(monkeypatch, tmp_path, server):
    server.script = [(200, {"content": [{"type": "text", "text": "x"}]})]
    Fake.style = "anthropic"          # the fake sends Claude-shaped JSON...
    monkeypatch.setenv("ORU_PROVIDER", "gemini")   # ...to an OpenAI-style client
    monkeypatch.setenv("ORU_BASE_URL", A.base_url())
    with pytest.raises(A.AssistantError, match="server"):
        A.Assistant().ask("hi", "en")


def test_history_trim_never_starts_on_tool_result(server):
    a = A.Assistant()
    for i in range(20):
        server.script.append((200, text(f"r{i}")))
        a.ask(f"q{i}", "en")
    assert len(a.history) <= A.KEEP_MESSAGES
    assert a.history[0]["role"] == "user"


def test_prompt_mentions_language():
    assert "Tamil" in A.system_prompt("ta") and "NEVER invent" in A.system_prompt("en")


def test_error_has_code():
    assert A.AssistantError("offline").code == "offline"
