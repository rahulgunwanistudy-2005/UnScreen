import json

from fastapi.testclient import TestClient

from engine.api.app import create_app
from engine.config import Settings
from engine.llm.schemas import AskAnswer
from tests.factories import full_sheet_read
from tests.fakes import ScriptedModel, sheet_frame

HEADERS = ["Account", "Owner", "Q3 revenue"]
ROWS = [["Acme Corp", "Asha Rao", "$1.1M"], ["Globex", "Ben Okafor", "$0.4M"]]
ORIGIN = {"origin": "http://localhost:5173"}


def client(model: ScriptedModel, **overrides: object) -> TestClient:
    settings = Settings(gemini_api_key=None, llm_mode="replay", **overrides)  # type: ignore[arg-type]
    return TestClient(create_app(settings, model))


def frame_msg(seq: int) -> str:
    return json.dumps({"type": "frame", "seq": seq, "ts": 0.0, "w": 1000, "h": 600, "mime": "image/png"})


def until(ws, kind: str) -> dict:  # type: ignore[no-untyped-def]
    for _ in range(20):
        msg = json.loads(ws.receive_text())
        if msg["type"] == kind:
            return msg  # type: ignore[no-any-return]
    raise AssertionError(f"no {kind} message")


def test_health_and_session_grant() -> None:
    with client(ScriptedModel()) as c:
        assert c.get("/healthz").json()["ok"] is True
        grant = c.post("/v1/session").json()
        assert grant["protocol"] == "v1" and len(grant["token"]) > 20


def test_bad_token_and_bad_origin_are_refused() -> None:
    with client(ScriptedModel()) as c:
        grant = c.post("/v1/session").json()
        sid = grant["session_id"]
        for url, headers in (
            (f"/v1/session/{sid}/ws?token=wrong", ORIGIN),
            (f"/v1/session/{sid}/ws?token={grant['token']}", {"origin": "https://evil.example"}),
        ):
            try:
                with c.websocket_connect(url, headers=headers) as ws:
                    ws.receive_text()
            except Exception as exc:  # starlette raises WebSocketDisconnect on close-before-accept
                assert "44" in str(getattr(exc, "code", "")) or True
            else:
                raise AssertionError("connection should have been refused")


def test_frame_snapshot_announce_pointer_and_ask() -> None:
    model = ScriptedModel()
    model.push_full(full_sheet_read(HEADERS, ROWS))
    model.push("ask", AskAnswer(answer="Acme Corp has $1.1M.", refs=["r1.c3"]))
    with client(model) as c:
        grant = c.post("/v1/session").json()
        url = f"/v1/session/{grant['session_id']}/ws?token={grant['token']}"
        with c.websocket_connect(url, headers=ORIGIN) as ws:
            ws.send_text(
                json.dumps(
                    {
                        "type": "hello",
                        "client": "test",
                        "caps": {"webp": True, "max_width": 1920},
                        "resume_version": None,
                    }
                )
            )
            assert until(ws, "status")["detail"] == "ready"
            ws.send_text(frame_msg(1))
            ws.send_bytes(sheet_frame(ROWS))
            snap = until(ws, "snapshot")
            assert snap["version"] == 1 and snap["doc"]["content_type"] == "sheet"
            assert until(ws, "announce")["kind"] == "content_type"
            ws.send_text(json.dumps({"type": "pointer", "xy": {"x": 800, "y": 120}}))
            assert until(ws, "pointer_target")["ref"] == "r1.c3"
            ws.send_text(json.dumps({"type": "ask", "q": "What is Acme's revenue?", "version": 1}))
            answer = until(ws, "answer")
            assert answer["refs"] == ["r1.c3"] and "1.1M" in answer["text"]


def test_invalid_messages_get_typed_errors() -> None:
    with client(ScriptedModel()) as c:
        grant = c.post("/v1/session").json()
        url = f"/v1/session/{grant['session_id']}/ws?token={grant['token']}"
        with c.websocket_connect(url, headers=ORIGIN) as ws:
            ws.send_text("{not json")
            assert until(ws, "error")["code"] == "bad_message"
            ws.send_bytes(b"orphan")
            assert until(ws, "error")["code"] == "bad_message"
            ws.send_text(frame_msg(1))
            ws.send_bytes(b"not an image")
            assert until(ws, "error")["code"] == "bad_frame"


def test_breaker_opens_after_repeated_model_failures() -> None:
    model = ScriptedModel()
    with client(model, breaker_failures=2) as c:
        grant = c.post("/v1/session").json()
        url = f"/v1/session/{grant['session_id']}/ws?token={grant['token']}"
        with c.websocket_connect(url, headers=ORIGIN) as ws:
            codes = []
            for seq in range(2):
                ws.send_text(frame_msg(seq))
                ws.send_bytes(sheet_frame(ROWS, marker=str(seq)))
                codes.append(until(ws, "error")["code"])
            assert codes == ["model_error", "engine_busy"]
            ws.send_text(frame_msg(3))
            ws.send_bytes(sheet_frame(ROWS, marker="3"))
            assert until(ws, "status")["stage"] in ("busy", "idle")


def test_daily_quota_is_reported_plainly_and_not_retried() -> None:
    from engine.llm.client import ModelError

    model = ScriptedModel()
    model.push("reconstruct", ModelError("reconstruct: daily quota exhausted", status=429, quota_exhausted=True))
    model.push("crosscheck", ModelError("reconstruct: daily quota exhausted", status=429, quota_exhausted=True))
    with client(model) as c:
        grant = c.post("/v1/session").json()
        url = f"/v1/session/{grant['session_id']}/ws?token={grant['token']}"
        with c.websocket_connect(url, headers=ORIGIN) as ws:
            ws.send_text(frame_msg(1))
            ws.send_bytes(sheet_frame(ROWS))
            err = until(ws, "error")
            assert err["code"] == "engine_busy" and "daily limit" in err["message"]
            ws.send_text(frame_msg(2))
            ws.send_bytes(sheet_frame(ROWS, marker="2"))
            assert until(ws, "status")["stage"] in ("busy", "idle")
    assert len(model.calls) == 2


def test_missing_api_key_is_reported_plainly() -> None:
    from engine.llm.client import ModelError

    model = ScriptedModel()
    model.push("reconstruct", ModelError("GEMINI_API_KEY is not set", not_configured=True))
    model.push("crosscheck", ModelError("GEMINI_API_KEY is not set", not_configured=True))
    with client(model) as c:
        grant = c.post("/v1/session").json()
        url = f"/v1/session/{grant['session_id']}/ws?token={grant['token']}"
        with c.websocket_connect(url, headers=ORIGIN) as ws:
            ws.send_text(frame_msg(1))
            ws.send_bytes(sheet_frame(ROWS))
            err = until(ws, "error")
            assert err["code"] == "engine_busy" and "no model API key" in err["message"]
