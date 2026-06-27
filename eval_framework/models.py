"""Shared Pydantic data models for the evaluation framework."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────

class Layer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class Dimension(str, Enum):
    D1 = "D1"  # 代码生成
    D2 = "D2"  # 任务拆解
    D3 = "D3"  # 工具调用
    D4 = "D4"  # 多智能体协作
    D5 = "D5"  # 审查/调试
    D6 = "D6"  # 持续记忆


class ScoringType(str, Enum):
    UNIT_TEST = "unit_test"
    TOOL_MATCH = "tool_match"
    TREE_SIMILARITY = "tree_sim"
    LLM_JUDGE = "llm_judge"


class NetworkMode(str, Enum):
    NONE = "none"
    WHITELIST = "whitelist"
    OPEN = "open"


# ── Sandbox ────────────────────────────────────────────

class SandboxConfig(BaseModel):
    image: str
    dependencies: list[str] = []
    network: NetworkMode = NetworkMode.NONE
    env_vars: dict[str, str] = {}


# ── Scoring ────────────────────────────────────────────

class ScoringConfig(BaseModel):
    type: ScoringType
    test_command: str = ""
    pass_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    tool_sequence: list[str] = []
    key_params: list[str] = []
    expected_tree: str = ""  # JSON-serialized expected decomposition tree
    tree_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


# ── Test Item ──────────────────────────────────────────

class TestItem(BaseModel):
    """A single test item loaded from registry metadata."""

    id: str
    layer: Layer
    dimensions: list[Dimension]
    sub_dimensions: list[Dimension] = []
    language: str
    difficulty: int = Field(ge=1, le=5)
    estimated_time_min: int
    tags: list[str] = []
    sandbox: SandboxConfig
    prompt_template: str
    context_files: list[str] = []
    expected_artifacts: list[str] = []
    scoring: ScoringConfig
    created: Optional[str] = None
    version: str = "1.0"

    @field_validator("dimensions", "sub_dimensions", mode="before")
    @classmethod
    def validate_dimension_strings(cls, v: list[str]) -> list[str]:
        valid = {d.value for d in Dimension}
        for item in v:
            if item not in valid:
                raise ValueError(
                    f"Unknown dimension '{item}'. Valid: {valid}"
                )
        return v


# ── Agent Trace ────────────────────────────────────────

class ToolCall(BaseModel):
    tool_name: str
    params: dict[str, Any]


class ToolCallStep(BaseModel):
    step_index: int
    tool_call: ToolCall
    result: dict[str, Any]
    timestamp: datetime
    duration_ms: int


class AgentTrace(BaseModel):
    """Complete behavior trace of one agent on one test item."""

    run_id: str
    agent_name: str
    agent_version: str
    test_item_id: str
    start_time: datetime
    end_time: datetime
    steps: list[ToolCallStep] = []
    final_output: str = ""

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    @property
    def tool_names_sequence(self) -> list[str]:
        return [s.tool_call.tool_name for s in self.steps]


# ── Scoring Results ────────────────────────────────────

class JudgeScoreCard(BaseModel):
    """LLM-as-Judge 评分卡：单一维度的评分。"""

    dimension: Dimension
    score: int = Field(ge=1, le=5)
    reasoning: str


class TestResult(BaseModel):
    """Final result for a single test item run."""

    test_item_id: str
    agent_name: str
    agent_version: str
    layer: Layer
    dimensions: list[Dimension]
    l1_score: Optional[float] = None  # 0.0 - 1.0
    judge_score_cards: list[JudgeScoreCard] = []
    status: str = "completed"  # completed | timeout | error | skipped
    run_id: str = ""
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


# ── Agent Capabilities ─────────────────────────────────

class AgentCapabilities(BaseModel):
    agent_name: str
    agent_version: str
    supported_tools: list[str]
    uses_subagents: bool = False
    has_memory_across_sessions: bool = False
    default_model: str = ""
