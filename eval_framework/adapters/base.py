"""Abstract base class for Agent adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from eval_framework.models import AgentCapabilities, AgentTrace, Dimension, Layer


@dataclass
class TestContext:
    """All information needed to set up an agent execution."""

    test_item_id: str
    layer: Layer
    dimensions: list[Dimension]
    working_dir: str
    env_vars: dict[str, str] = field(default_factory=dict)
    network_allowed: bool = False

    def layer_timeout_seconds(self) -> int:
        """Return timeout in seconds based on layer."""
        defaults = {"L1": 900, "L2": 3600, "L3": 7200}
        return defaults.get(self.layer.value, 900)


class AgentAdapter(ABC):
    """Unified interface for driving any coding agent.

    Subclasses implement the protocol for a specific agent:
      - Claude Code (CLI / SDK)
      - Copilot (VS Code extension API)
      - Cursor (similar)
      - Generic CLI-based agents
    """

    @abstractmethod
    def execute(self, prompt: str, context: TestContext) -> AgentTrace:
        """Send prompt to the agent and capture the full execution trace."""
        ...

    @abstractmethod
    def capabilities(self) -> AgentCapabilities:
        """Return the agent's known capabilities."""
        ...
