"""All configuration is read here and only here."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENGINE_ROOT = Path(__file__).resolve().parent.parent

LlmMode = Literal["live", "record", "replay"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UNSCREEN_",
        env_file=(ENGINE_ROOT.parent.parent / ".env", ENGINE_ROOT / ".env"),
        extra="ignore",
    )

    gemini_api_key: SecretStr | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    llm_mode: LlmMode = "live"
    golden_dir: Path = ENGINE_ROOT / "tests" / "golden" / "responses"

    reconstruct_model: str = "gemini-3.6-flash"
    region_model: str = "gemini-3.6-flash"
    verify_model: str = "gemini-3.5-flash-lite"
    ask_model: str = "gemini-3.6-flash"
    thinking_level: Literal["minimal", "low", "medium", "high"] = "minimal"
    image_resolution: Literal["low", "medium", "high", "ultra_high"] = "high"
    llm_timeout_s: float = 120.0
    llm_max_retries: int = 2

    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    session_ttl_s: int = 30 * 60
    max_sessions: int = 200
    max_frame_bytes: int = 6 * 1024 * 1024
    frames_per_minute: int = 60
    asks_per_minute: int = 10
    sessions_per_ip_per_hour: int = 30

    full_reconstruct_threshold: float = 0.35
    verify_max_items: int = 24
    breaker_failures: int = 3
    breaker_cooldown_s: float = 20.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
