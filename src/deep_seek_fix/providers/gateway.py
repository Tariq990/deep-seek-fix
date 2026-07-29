from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RetryClassification(StrEnum):
    NONE = "NONE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    EMPTY_RESPONSE = "EMPTY_RESPONSE"


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    base_url: str
    api_key_env: str
    timeout_seconds: int = Field(default=30, ge=1)
    maximum_retries: int = Field(default=2, ge=0, le=5)
    cost_cap_usd: float = Field(default=1.0, ge=0)


@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    configured: bool
    live_tests_enabled: bool


PROVIDERS = {
    "deepseek": ProviderConfig(
        name="deepseek",
        base_url="https://api.deepseek.com",
        api_key_env="DEEPSEEK_API_KEY",
    ),
    "zai": ProviderConfig(name="zai", base_url="https://api.z.ai", api_key_env="ZAI_API_KEY"),
    "qwen": ProviderConfig(
        name="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="QWEN_API_KEY",
    ),
    "kimi": ProviderConfig(
        name="kimi",
        base_url="https://api.moonshot.ai/v1",
        api_key_env="KIMI_API_KEY",
    ),
    "minimax": ProviderConfig(
        name="minimax",
        base_url="https://api.minimax.io/v1",
        api_key_env="MINIMAX_API_KEY",
    ),
}


def health_check(provider: str) -> ProviderHealth:
    config = PROVIDERS[provider]
    return ProviderHealth(
        provider=provider,
        configured=bool(os.environ.get(config.api_key_env)),
        live_tests_enabled=os.environ.get("DSFIX_ENABLE_LIVE_TESTS") == "1",
    )


def backoff_seconds(attempt: int) -> float:
    jitter = secrets.SystemRandom().uniform(0, 0.25)
    return float(min(8.0, (2**attempt) + jitter))


def fake_provider_call(prompt: str) -> str:
    time.sleep(0.001)
    if not prompt.strip():
        raise ValueError(RetryClassification.EMPTY_RESPONSE)
    return '{"verdict":"INCOMPLETE"}'
