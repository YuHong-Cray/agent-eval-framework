"""Adapter factory — registry-based creation."""

from typing import Any

from eval_framework.adapters.base import AgentAdapter
from eval_framework.adapters.cli_generic import CLIAdapter


class AdapterFactory:
    _registry: dict[str, type[AgentAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_cls: type[AgentAdapter]) -> None:
        cls._registry[name] = adapter_cls

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> AgentAdapter:
        if name not in cls._registry:
            raise KeyError(
                f"Unknown adapter '{name}'. Registered: {list(cls._registry.keys())}"
            )
        return cls._registry[name](**kwargs)


from eval_framework.adapters.cray_code import CrayCodeAdapter
from eval_framework.adapters.claude_code import ClaudeCodeAdapter

# Built-in registrations
AdapterFactory.register("cli", CLIAdapter)
AdapterFactory.register("craycode", CrayCodeAdapter)
AdapterFactory.register("cray", CrayCodeAdapter)
AdapterFactory.register("claude", ClaudeCodeAdapter)
