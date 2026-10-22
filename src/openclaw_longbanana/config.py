from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENCLAW_RUNTIME = PROJECT_ROOT / "openclaw-runtime" / "openclaw.mjs"
DEFAULT_IMAGE_GEN_MCP_DIR = PROJECT_ROOT / "image-gen-mcp"
DEFAULT_OPENCLAW_SKILLS_DIR = PROJECT_ROOT / "openclaw_skills"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_path(name: str, default: str | Path | None = None) -> Path | None:
    raw = os.environ.get(name)
    if raw is None:
        if default is None:
            return None
        return Path(default).expanduser()
    raw = raw.strip()
    return Path(raw).expanduser() if raw else None


def load_env_file() -> None:
    env_file = env_path("OPENCLAW_LONGBANANA_ENV_FILE", PROJECT_ROOT / ".env")
    if env_file is None or not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def openclaw_bin() -> Path:
    load_env_file()
    return env_path("OPENCLAW_BIN", DEFAULT_OPENCLAW_RUNTIME) or DEFAULT_OPENCLAW_RUNTIME


def image_gen_mcp_dir() -> Path:
    load_env_file()
    return env_path("IMAGE_GEN_MCP_DIR", DEFAULT_IMAGE_GEN_MCP_DIR) or DEFAULT_IMAGE_GEN_MCP_DIR


def openclaw_skills_dir() -> Path:
    load_env_file()
    return env_path("OPENCLAW_SKILLS_DIR", DEFAULT_OPENCLAW_SKILLS_DIR) or DEFAULT_OPENCLAW_SKILLS_DIR


def node_bin() -> str:
    load_env_file()
    return os.environ.get("NODE_BIN", "").strip() or "node"


def no_proxy_default() -> str:
    return "localhost,127.0.0.1"


@dataclass(frozen=True)
class OpenClawModelConfig:
    provider: str
    model: str
    base_url: str
    api_key_env: str
    api: str
    context_window: int
    max_tokens: int
    allow_private_network: bool
    headers: dict[str, str] | None = None

    @property
    def model_ref(self) -> str:
        return f"{self.provider}/{self.model}"

    def provider_config(
        self,
        *,
        api_key: str | None = None,
        force_allow_private_network: bool | None = None,
    ) -> dict:
        provider: dict = {
            "baseUrl": self.base_url,
            "apiKey": api_key if api_key is not None else f"${{{self.api_key_env}}}",
            "api": self.api,
            "models": [
                {
                    "id": self.model,
                    "name": self.model,
                    "reasoning": True,
                    "input": ["text", "image"],
                    "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                    "contextWindow": self.context_window,
                    "maxTokens": self.max_tokens,
                }
            ],
        }
        allow_private_network = (
            self.allow_private_network
            if force_allow_private_network is None
            else force_allow_private_network
        )
        if allow_private_network:
            provider["request"] = {"allowPrivateNetwork": True}
        if self.headers:
            provider["headers"] = self.headers
        return provider


def load_openclaw_model_config(*, max_tokens: int | None = None) -> OpenClawModelConfig:
    load_env_file()
    provider = os.environ.get("OPENCLAW_MODEL_PROVIDER", "anthropic").strip()
    official_claude = provider == "anthropic"
    model = os.environ.get("OPENCLAW_MODEL_ID", "claude-sonnet-4-6" if official_claude else "").strip()
    base_url = os.environ.get("OPENCLAW_MODEL_BASE_URL", "https://api.anthropic.com" if official_claude else "").strip()
    if not model or not base_url:
        raise RuntimeError("OPENCLAW_MODEL_ID and OPENCLAW_MODEL_BASE_URL are required")
    api_key_env = os.environ.get("OPENCLAW_MODEL_API_KEY_ENV", "ANTHROPIC_API_KEY" if official_claude else "OPENCLAW_MODEL_API_KEY").strip()
    if not os.environ.get(api_key_env, "").strip():
        raise RuntimeError(f"{api_key_env} is required for OPENCLAW_MODEL_PROVIDER={provider}")
    headers: dict[str, str] | None = None
    raw_headers = os.environ.get("OPENCLAW_MODEL_HEADERS_JSON", "").strip()
    if raw_headers:
        parsed_headers = json.loads(raw_headers)
        if not isinstance(parsed_headers, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in parsed_headers.items()
        ):
            raise RuntimeError(
                "OPENCLAW_MODEL_HEADERS_JSON must be a JSON object of string values"
            )
        headers = parsed_headers
    return OpenClawModelConfig(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
        api=os.environ.get("OPENCLAW_MODEL_API", "anthropic-messages" if official_claude else "openai-completions").strip(),
        context_window=int(os.environ.get("OPENCLAW_MODEL_CONTEXT_WINDOW", "200000")),
        max_tokens=max_tokens if max_tokens is not None else int(os.environ.get("OPENCLAW_MAX_TOKENS", "16384")),
        allow_private_network=env_bool("OPENCLAW_MODEL_ALLOW_PRIVATE_NETWORK", False),
        headers=headers,
    )


def load_image_backend_config_path(backend: str, config_dir: Path) -> Path:
    load_env_file()
    raw = os.environ.get(f"IMAGE_GEN_CONFIG_{backend.upper()}") or os.environ.get("IMAGE_GEN_CONFIG")
    if not raw:
        raise RuntimeError(
            "IMAGE_GEN_CONFIG is required, or set "
            f"IMAGE_GEN_CONFIG_{backend.upper()} for backend-specific config"
        )
    source = Path(raw).expanduser()
    if not source.exists():
        raise RuntimeError(f"image generation config not found: {source}")
    config_dir.mkdir(parents=True, exist_ok=True)
    return source
