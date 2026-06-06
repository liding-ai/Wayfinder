"""
路径与环境变量加载。

import 时自动 load_dotenv，保证后续模块能读到 .env。
"""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"


def load_env() -> None:
    load_dotenv(find_dotenv(usecwd=True))


load_env()


def get_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise KeyError(key)
    return value


def get_amap_api_key() -> str:
    return require_env("AMAP_API_KEY")
