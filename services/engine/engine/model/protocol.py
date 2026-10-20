"""WebSocket wire protocol v1. Text frames carry these JSON messages; a `frame` message is
immediately followed by one binary WebSocket message holding the encoded image."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from engine.model.document import Box, Document

PROTOCOL_VERSION = "v1"

Verbosity = Literal["all", "important", "quiet"]
NumericStyle = Literal["old_to_new", "new_only"]
Priority = Literal["content_type", "focus", "other"]
AnnounceKind = Literal[
    "content_type",
    "title",
    "cell",
    "row_added",
    "row_removed",
    "scroll",
    "line",
    "lines_added",
    "lines_removed",
    "block",
    "uncertain",
    "status",
]
Stage = Literal["idle", "classify", "reconstruct", "region", "verify", "diff", "busy", "ask"]
ErrorCode = Literal[
    "bad_message",
    "bad_frame",
    "rate_limited",
    "engine_busy",
    "model_error",
    "session_expired",
    "unauthorized",
]


class _Msg(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class Point(_Msg):
    """Normalised 0..1000 of the full frame."""

    x: int = Field(ge=0, le=1000)
    y: int = Field(ge=0, le=1000)


class ClientCaps(_Msg):
    webp: bool = True
    max_width: int = Field(default=1920, ge=320, le=3840)


class Hello(_Msg):
    type: Literal["hello"] = "hello"
    client: str = Field(max_length=64)
    caps: ClientCaps = ClientCaps()
    resume_version: int | None = None


class Frame(_Msg):
    type: Literal["frame"] = "frame"
    seq: int = Field(ge=0)
    ts: float
    w: int = Field(ge=16, le=7680)
    h: int = Field(ge=16, le=4320)
    mime: Literal["image/webp", "image/jpeg", "image/png"] = "image/webp"
    change_score: float = Field(default=1.0, ge=0.0, le=1.0)
    changed_tiles: list[int] = Field(default_factory=list, max_length=4096)
    pointer: Point | None = None


class PointerMsg(_Msg):
    type: Literal["pointer"] = "pointer"
    xy: Point


class Ask(_Msg):
    type: Literal["ask"] = "ask"
    q: str = Field(min_length=1, max_length=500)
    version: int = Field(ge=0)


class Settings(_Msg):
    type: Literal["settings"] = "settings"
    verbosity: Verbosity = "all"
    numeric_style: NumericStyle = "old_to_new"
    focus_ref: str | None = Field(default=None, max_length=64)


ClientMessage = Annotated[Hello | Frame | PointerMsg | Ask | Settings, Field(discriminator="type")]


class PatchOp(_Msg):
    """RFC 6902 operation. Only add, remove and replace are emitted."""

    op: Literal["add", "remove", "replace"]
    path: str
    value: Any = None


class Snapshot(_Msg):
    type: Literal["snapshot"] = "snapshot"
    version: int
    doc: Document


class Patch(_Msg):
    type: Literal["patch"] = "patch"
    version: int
    base: int
    ops: list[PatchOp]


class Announce(_Msg):
    type: Literal["announce"] = "announce"
    version: int
    priority: Priority
    kind: AnnounceKind
    text: str
    refs: list[str] = Field(default_factory=list)


class PointerTarget(_Msg):
    type: Literal["pointer_target"] = "pointer_target"
    ref: str | None
    text: str


class Answer(_Msg):
    type: Literal["answer"] = "answer"
    q: str
    text: str
    refs: list[str]
    version: int


class Status(_Msg):
    type: Literal["status"] = "status"
    stage: Stage
    latency_ms: int | None = None
    detail: str | None = None
    content_bbox: Box | None = None


class Error(_Msg):
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str


ServerMessage = Annotated[
    Snapshot | Patch | Announce | PointerTarget | Answer | Status | Error,
    Field(discriminator="type"),
]


class SessionGrant(_Msg):
    """Response of POST /v1/session."""

    session_id: str
    token: str
    expires_in_s: int
    protocol: str = PROTOCOL_VERSION
