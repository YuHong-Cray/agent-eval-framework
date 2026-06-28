"""Test item loading and context preparation."""

import json
import random
import shutil
from pathlib import Path
from typing import Optional

from eval_framework.config import config
from eval_framework.models import TestItem


def _read_json_with_encoding(path: Path) -> dict:
    """Read a JSON file, trying UTF-8 first then falling back to GBK.

    On Chinese Windows some test-item metadata files are saved as GBK.
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("gbk")
    return json.loads(text)


class TestItemRegistry:
    """Loads and manages test items from the filesystem registry."""

    def __init__(self, registry_path: Optional[Path] = None):
        self._path = registry_path or config.get_test_items_registry_path()
        self._items: dict[str, TestItem] = {}
        self._metadata_dir = self._path.parent

    def load(self) -> list[TestItem]:
        """Load all enabled test items from the registry."""
        if not self._path.exists():
            raise FileNotFoundError(f"Registry not found: {self._path}")

        registry = _read_json_with_encoding(self._path)

        items = []
        for entry in registry.get("items", []):
            if not entry.get("enabled", True):
                continue
            item_path = self._metadata_dir / entry["path"] / "metadata.json"
            if not item_path.exists():
                print(
                    f"Warning: skipping missing item {entry['id']} at {item_path}"
                )
                continue
            data = _read_json_with_encoding(item_path)
            item = TestItem(**data)
            self._items[item.id] = item
            items.append(item)

        return items

    def get_item(self, item_id: str) -> TestItem:
        if item_id not in self._items:
            raise KeyError(
                f"Item '{item_id}' not loaded. Call load() first."
            )
        return self._items[item_id]

    def get_by_layer(self, layer: str) -> list[TestItem]:
        return [i for i in self._items.values() if i.layer.value == layer]

    def get_by_dimension(self, dimension: str) -> list[TestItem]:
        return [
            i
            for i in self._items.values()
            if dimension in i.dimensions
        ]

    def select_random(
        self, layer: str, count: int, seed: Optional[int] = None
    ) -> list[TestItem]:
        """Randomly select `count` items from `layer`."""
        rng = random.Random(seed or config.get_random_seed())
        pool = self.get_by_layer(layer)
        if len(pool) < count:
            return pool
        return rng.sample(pool, count)


class ContextPreparer:
    """Prepares test context by copying test item files into sandbox workspace."""

    def __init__(self, registry: TestItemRegistry):
        self._registry = registry

    def prepare_workspace(
        self, item_id: str, workspace_dir: Path
    ) -> TestItem:
        """Copy context and judge files into the sandbox workspace."""
        item = self._registry.get_item(item_id)

        # Determine item directory
        item_dir = self._metadata_dir / self._get_item_rel_path(item_id)

        # Copy context files
        for rel in item.context_files:
            src = item_dir / rel
            dst = workspace_dir / Path(rel).name
            if src.exists():
                shutil.copy2(src, dst)

        # Copy judge files
        judge_src = item_dir / "judge"
        if judge_src.exists() and judge_src.is_dir():
            judge_dst = workspace_dir / "judge"
            shutil.copytree(judge_src, judge_dst, dirs_exist_ok=True)

        return item

    @property
    def _metadata_dir(self) -> Path:
        return self._registry._metadata_dir

    def _get_item_rel_path(self, item_id: str) -> str:
        """Reverse-lookup item path from registry."""
        registry = _read_json_with_encoding(self._registry._path)
        for entry in registry["items"]:
            if entry["id"] == item_id:
                return entry["path"]
        raise KeyError(f"Item {item_id} not in registry")
