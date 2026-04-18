from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Union

from dotenv import dotenv_values, load_dotenv

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class AppConfig:
    base_url: str
    api_key: str
    model: str
    timeout: float = 60.0


def build_config(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout: Union[str, float] = 60.0,
) -> AppConfig:
    timeout_raw = str(timeout).strip()
    base_url = base_url.strip()
    api_key = api_key.strip()
    model = model.strip()

    if not base_url:
        base_url = DEFAULT_BASE_URL
    if not api_key:
        raise ValueError(
            "Missing API key. Set OPENAI_API_KEY in the environment or fill the API Key field in the app."
        )
    if not model:
        model = DEFAULT_MODEL

    return AppConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=model,
        timeout=float(timeout_raw),
    )


def load_config() -> AppConfig:
    load_dotenv()
    values = read_config_values()
    return build_config(
        base_url=values["LLM_BASE_URL"],
        api_key=values["LLM_API_KEY"],
        model=values["LLM_MODEL"],
        timeout=values["LLM_TIMEOUT"],
    )


def read_config_values(path: Union[str, Path] = ".env") -> Dict[str, str]:
    env_path = Path(path)
    file_values = {
        key: str(value).strip()
        for key, value in dotenv_values(env_path).items()
        if value is not None
    }
    base_url, base_source = _resolve_config_value(
        file_values,
        "LLM_BASE_URL",
        ("OPENAI_BASE_URL",),
        DEFAULT_BASE_URL,
    )
    api_key, api_source = _resolve_config_value(
        file_values,
        "LLM_API_KEY",
        ("OPENAI_API_KEY",),
        "",
    )
    model, model_source = _resolve_config_value(
        file_values,
        "LLM_MODEL",
        ("OPENAI_MODEL",),
        DEFAULT_MODEL,
    )
    timeout, timeout_source = _resolve_config_value(
        file_values,
        "LLM_TIMEOUT",
        tuple(),
        "60",
    )

    return {
        "LLM_BASE_URL": base_url,
        "LLM_API_KEY": api_key,
        "LLM_MODEL": model,
        "LLM_TIMEOUT": timeout,
        "LLM_BASE_URL_SOURCE": base_source,
        "LLM_API_KEY_SOURCE": api_source,
        "LLM_MODEL_SOURCE": model_source,
        "LLM_TIMEOUT_SOURCE": timeout_source,
    }


def save_config_values(
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout: Union[str, float],
    path: Union[str, Path] = ".env",
) -> None:
    env_path = Path(path)
    lines = [
        f"LLM_BASE_URL={base_url.strip()}",
        f"LLM_API_KEY={api_key.strip()}",
        f"LLM_MODEL={model.strip()}",
        f"LLM_TIMEOUT={str(timeout).strip()}",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def clear_saved_config(path: Union[str, Path] = ".env") -> None:
    env_path = Path(path)
    if env_path.exists():
        env_path.unlink()


def describe_config_source(values: Dict[str, str]) -> str:
    api_source = values.get("LLM_API_KEY_SOURCE", "missing")
    base_source = values.get("LLM_BASE_URL_SOURCE", "default")
    model_source = values.get("LLM_MODEL_SOURCE", "default")

    return (
        f"API key: {api_source}; "
        f"base URL: {base_source}; "
        f"model: {model_source}"
    )


def _resolve_config_value(
    file_values: Dict[str, str],
    primary_key: str,
    fallback_env_keys: Tuple[str, ...],
    default: str,
) -> Tuple[str, str]:
    file_value = file_values.get(primary_key, "").strip()
    if file_value:
        return file_value, "override file"

    env_value = os.getenv(primary_key, "").strip()
    if env_value:
        return env_value, "environment"

    for env_key in fallback_env_keys:
        env_value = os.getenv(env_key, "").strip()
        if env_value:
            return env_value, f"environment ({env_key})"

    if default:
        return default, "default"

    return "", "missing"
