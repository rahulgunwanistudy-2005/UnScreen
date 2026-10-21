import time

from engine.config import Settings
from engine.store.sessions import Breaker, SessionLimitError, SessionStore, TokenBucket
from tests.fakes import ScriptedModel


def store(**overrides: object) -> SessionStore:
    return SessionStore(Settings(gemini_api_key=None, llm_mode="replay", **overrides), ScriptedModel())  # type: ignore[arg-type]


def test_bucket_starts_full_then_limits() -> None:
    bucket = TokenBucket(3, 3600)
    assert [bucket.take() for _ in range(4)] == [True, True, True, False]


def test_per_ip_session_limit_allows_the_configured_burst() -> None:
    s = store(sessions_per_ip_per_hour=5)
    for _ in range(5):
        s.create("1.2.3.4")
    try:
        s.create("1.2.3.4")
    except SessionLimitError:
        pass
    else:
        raise AssertionError("sixth session should be refused")
    s.create("5.6.7.8")


def test_sessions_expire_after_ttl_and_tokens_are_checked() -> None:
    s = store(session_ttl_s=0)
    session = s.create("ip")
    assert session.check_token(session.token) and not session.check_token("nope")
    time.sleep(0.01)
    assert s.get(session.id) is None


def test_breaker_opens_after_threshold_and_resets_on_success() -> None:
    b = Breaker(threshold=2, cooldown_s=60)
    assert b.failure() is False and b.failure() is True and b.is_open()
    b2 = Breaker(threshold=2, cooldown_s=60)
    b2.failure()
    b2.success()
    assert b2.failure() is False
