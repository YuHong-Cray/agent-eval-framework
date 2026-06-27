"""Configuration loader — reads config.yaml, overlays env vars."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class Config:
    """Singleton config loaded from YAML, with env-var overrides."""

    _instance: Optional["Config"] = None

    def __init__(self, config_path: Optional[Path] = None):
        self._path = config_path or _DEFAULT_CONFIG_PATH
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            with open(self._path, "r") as f:
                self._data = yaml.safe_load(f) or {}
        # Env var overrides
        if db_url := os.getenv("EVAL_DATABASE_URL"):
            self._data.setdefault("database", {})["url"] = db_url
        if judge_key := os.getenv("EVAL_JUDGE_API_KEY"):
            self._data.setdefault("scoring", {}).setdefault("l2_l3", {})[
                "api_key"
            ] = judge_key
        if sandbox_concurrency := os.getenv("EVAL_SANDBOX_MAX_CONCURRENCY"):
            self._data.setdefault("sandbox", {})["max_concurrency"] = int(
                sandbox_concurrency
            )

    @classmethod
    def get(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_sandbox_config(self) -> dict[str, Any]:
        return self._data.get("sandbox", {})

    def get_database_url(self) -> str:
        return self._data.get("database", {}).get(
            "url", "sqlite:///eval_framework.db"
        )

    def get_scoring_config(self) -> dict[str, Any]:
        return self._data.get("scoring", {})

    def get_layer_config(self, layer: str) -> dict[str, Any]:
        return self._data.get("layers", {}).get(layer, {})

    def get_test_items_registry_path(self) -> Path:
        rel = self._data.get("test_items", {}).get(
            "registry_path", "test_items/registry.json"
        )
        return Path(self._path).parent / rel

    def get_random_seed(self) -> int:
        return self._data.get("test_items", {}).get("random_seed", 42)

    def get_report_dir(self) -> Path:
        rel = self._data.get("report", {}).get("output_dir", "reports/")
        return Path(self._path).parent / rel


# Convenience module-level access
config = Config.get()
