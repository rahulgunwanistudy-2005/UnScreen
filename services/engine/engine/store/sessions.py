"""In-memory sessions with a TTL. Nothing here is persisted; a restart forgets everything."""

import hmac
import secrets
import time
from dataclasses import dataclass, field

from engine.config import Settings
from engine.llm.client import VisionModel
from engine.pipeline.session import SessionPipeline


class TokenBucket:
    """Starts full; refills `capacity` tokens per `period_s`."""

    def __init__(self, capacity: int, period_s: float = 60.0) -> None:
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.rate = capacity / period_s
        self.updated = time.monotonic()

    def take(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
        self.updated = now
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True


@dataclass
class Breaker:
    """Opens after repeated model failures so we report 'engine busy' instead of guessing."""

    threshold: int
    cooldown_s: float
    failures: int = 0
    open_until: float = 0.0

    def is_open(self) -> bool:
        return time.monotonic() < self.open_until

    def success(self) -> None:
        self.failures = 0

    def open_for(self, seconds: float) -> None:
        self.open_until = time.monotonic() + seconds
        self.failures = 0

    def failure(self) -> bool:
        """Record a failure; True if this opened the breaker."""
        self.failures += 1
        if self.failures >= self.threshold and not self.is_open():
            self.open_until = time.monotonic() + self.cooldown_s
            self.failures = 0
            return True
        return False


@dataclass
class Session:
    id: str
    token: str
    pipeline: SessionPipeline
    frames: TokenBucket
    asks: TokenBucket
    breaker: Breaker
    created: float = field(default_factory=time.monotonic)
    last_seen: float = field(default_factory=time.monotonic)
    connected: bool = False

    def touch(self) -> None:
        self.last_seen = time.monotonic()

    def check_token(self, token: str) -> bool:
        return hmac.compare_digest(self.token.encode(), token.encode())


class SessionLimitError(Exception):
    pass


class SessionStore:
    def __init__(self, settings: Settings, model: VisionModel) -> None:
        self._settings = settings
        self._model = model
        self._sessions: dict[str, Session] = {}
        self._ip_buckets: dict[str, TokenBucket] = {}

    def create(self, client_ip: str) -> Session:
        self.evict_expired()
        bucket = self._ip_buckets.get(client_ip)
        if bucket is None:
            bucket = self._ip_buckets[client_ip] = TokenBucket(self._settings.sessions_per_ip_per_hour, 3600.0)
        if not bucket.take():
            raise SessionLimitError("too many sessions from this address")
        if len(self._sessions) >= self._settings.max_sessions:
            raise SessionLimitError("the engine is at capacity")
        s = self._settings
        session = Session(
            id=secrets.token_urlsafe(12),
            token=secrets.token_urlsafe(24),
            pipeline=SessionPipeline(self._model, s),
            frames=TokenBucket(s.frames_per_minute),
            asks=TokenBucket(s.asks_per_minute),
            breaker=Breaker(s.breaker_failures, s.breaker_cooldown_s),
        )
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if time.monotonic() - session.last_seen > self._settings.session_ttl_s:
            self._sessions.pop(session_id, None)
            return None
        return session

    def evict_expired(self) -> int:
        now = time.monotonic()
        ttl = self._settings.session_ttl_s
        stale = [k for k, v in self._sessions.items() if not v.connected and now - v.last_seen > ttl]
        for k in stale:
            del self._sessions[k]
        return len(stale)

    def __len__(self) -> int:
        return len(self._sessions)
