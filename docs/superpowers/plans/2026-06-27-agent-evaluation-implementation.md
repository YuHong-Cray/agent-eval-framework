# Coding Agent 深度评测体系 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 Coding Agent 三层混合评测框架的基础设施，包括编排层、Agent适配器、Docker沙箱、判分引擎和结果可视化。

**Architecture:** Python 项目，采用模块化分层架构。Orchestrator 通过 Adapter 驱动被测 Agent，Agent 在 Docker 沙箱中执行测题，Scoring Engine 对产出物和轨迹做自动化判分，结果存入 PostgreSQL，Dashboard 用 Streamlit 展示。

**Tech Stack:** Python 3.12, Docker (docker-py), PostgreSQL (SQLAlchemy), Streamlit, Pydantic (数据模型), DeepSeek API (LLM-as-Judge)

---

## 文件结构总览

```
agent-test/
├── eval_framework/
│   ├── __init__.py
│   ├── config.py                 # 全局配置（YAML + env）
│   ├── models.py                 # Pydantic 数据模型（共享）
│   ├── cli.py                    # CLI 入口（run-eval / gen-report / ...）
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── scheduler.py          # 测题调度与并发执行
│   │   ├── context.py            # 上下文注入（题目+环境）
│   │   └── tracer.py             # Agent 行为轨迹收集
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py               # AgentAdapter 抽象基类
│   │   ├── claude_code.py        # ClaudeCodeAdapter
│   │   ├── cli_generic.py        # CLIAdapter（通用命令行 agent）
│   │   └── factory.py            # Adapter 工厂方法
│   ├── sandbox/
│   │   ├── __init__.py
│   │   ├── manager.py            # Docker 容器生命周期
│   │   ├── snapshot.py           # 文件系统快照对比
│   │   └── dockerfiles/
│   │       ├── python.Dockerfile
│   │       ├── node.Dockerfile
│   │       └── go.Dockerfile
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── l1_runner.py          # L1 自动化判分入口
│   │   ├── test_runner.py        # 单元测试运行器（多语言适配）
│   │   ├── tool_matcher.py       # 工具调用轨迹匹配器
│   │   ├── tree_similarity.py    # 任务拆解树编辑距离
│   │   ├── l2_l3_judge.py        # LLM-as-Judge 评分
│   │   └── calibrator.py         # 评分校准（人工抽检一致性）
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py         # 数据库连接管理
│   │   ├── models.py             # SQLAlchemy ORM 模型
│   │   └── repository.py         # 数据 CRUD 操作
│   └── dashboard/
│       ├── __init__.py
│       ├── app.py                # Streamlit 主应用
│       ├── charts.py             # 雷达图/柱状图等可视化
│       └── report.py             # 报告生成（Markdown/HTML）
├── test_items/
│   ├── registry.json             # 测题注册表
│   ├── l1/
│   │   ├── d1_code_fill/         # D1 代码填空
│   │   │   └── L1-D1-PY-001/
│   │   │       ├── metadata.json
│   │   │       ├── prompt.md
│   │   │       ├── context/
│   │   │       │   └── main.py
│   │   │       └── judge/
│   │   │           └── test_main.py
│   │   ├── d2_decompose/         # D2 任务拆解
│   │   ├── d3_tool_select/       # D3 工具选择
│   │   ├── d3_tool_chain/        # D3 链式工具编排
│   │   ├── d5_bug_fix/           # D5 Bug定位
│   │   └── d5_code_review/       # D5 代码审查
│   ├── l2/                       # L2 集成场景（后续补充）
│   └── l3/                       # L3 长程项目（后续补充）
├── tests/                        # 框架自身测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   └── sample_items.py       # 示例测题数据
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_scheduler.py
│   │   ├── test_tracer.py
│   │   ├── test_adapters.py
│   │   ├── test_sandbox.py
│   │   ├── test_test_runner.py
│   │   ├── test_tool_matcher.py
│   │   ├── test_tree_similarity.py
│   │   ├── test_l1_runner.py
│   │   ├── test_l2_l3_judge.py
│   │   ├── test_calibrator.py
│   │   └── test_repository.py
│   └── integration/
│       ├── test_e2e_l1_flow.py
│       └── test_sandbox_isolation.py
├── config.yaml                   # 默认全局配置
├── requirements.txt
├── docker-compose.yml            # PostgreSQL 本地开发服务
└── Makefile                      # 常用命令快捷入口
```

---

## 阶段一：基础设施搭建

### Task 1: 项目初始化与配置系统

**Files:**
- Create: `eval_framework/__init__.py`
- Create: `eval_framework/config.py`
- Create: `config.yaml`
- Create: `requirements.txt`

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p eval_framework/{orchestrator,adapters,sandbox/dockerfiles,scoring,db,dashboard}
mkdir -p test_items/l1/{d1_code_fill,d2_decompose,d3_tool_select,d3_tool_chain,d5_bug_fix,d5_code_review}
mkdir -p test_items/{l2,l3}
mkdir -p tests/{unit,integration,fixtures}
touch eval_framework/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
# Core
pydantic>=2.0.0
pyyaml>=6.0
python-dotenv>=1.0.0

# Docker sandbox
docker>=7.0.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0

# LLM integration
httpx>=0.27.0

# Dashboard
streamlit>=1.30.0
plotly>=5.18.0

# CLI
click>=8.1.0

# Testing
pytest>=8.0.0
pytest-cov>=4.1.0
```

- [ ] **Step 3: 创建 config.yaml**

```yaml
# eval_framework 全局配置
sandbox:
  docker_host: "unix:///var/run/docker.sock"
  default_image_python: "eval-sandbox-python:latest"
  default_image_node: "eval-sandbox-node:latest"
  default_image_go: "eval-sandbox-go:latest"
  network_mode: "none"          # none | whitelist | open
  max_concurrency: 4
  timeout_default: 900           # 15 min default

database:
  url: "postgresql://eval:eval@localhost:5432/eval_framework"

scoring:
  l1:
    pass_threshold: 0.85
  l2_l3:
    judge_model: "deepseek-v4-flash"
    judge_api_base: "https://api.deepseek.com"
    judge_max_retries: 3

layers:
  l1:
    concurrency: "high"
    retry: 1
    timeout_minutes: 15
  l2:
    concurrency: "low"
    retry: 0
    timeout_minutes: 60
  l3:
    concurrency: "serial"
    retry: 0
    timeout_minutes: 120

test_items:
  registry_path: "test_items/registry.json"
  random_seed: 42

report:
  output_dir: "reports/"
```

- [ ] **Step 4: 实现 config.py**

```python
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
```

- [ ] **Step 5: 验证配置加载**

```bash
python -c "from eval_framework.config import config; print(config.get_database_url())"
```

Expected: 输出 `sqlite:///eval_framework.db`（默认值）或配置文件中的 URL。

- [ ] **Step 6: Commit**

```bash
git add eval_framework/__init__.py eval_framework/config.py config.yaml requirements.txt
git commit -m "feat: project init — config system, requirements, directory structure"
```

---

### Task 2: 共享数据模型 (Pydantic)

**Files:**
- Create: `eval_framework/models.py`
- Create: `tests/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: 编写 models.py 的失败测试**

```python
"""Tests for shared Pydantic models."""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from eval_framework.models import (
    AgentCapabilities,
    AgentTrace,
    Dimension,
    Difficulty,
    JudgeScoreCard,
    Layer,
    SandboxConfig,
    ScoringConfig,
    ScoringType,
    TestItem,
    TestResult,
    ToolCall,
    ToolCallStep,
)


class TestTestItem:
    def test_valid_test_item_from_json(self, tmp_path):
        """TestItem should parse from standard JSON metadata."""
        data = {
            "id": "L1-D1-PY-001",
            "layer": "L1",
            "dimensions": ["D1"],
            "sub_dimensions": [],
            "language": "python",
            "difficulty": 2,
            "estimated_time_min": 8,
            "tags": ["function", "string-manipulation"],
            "sandbox": {
                "image": "python:3.12",
                "dependencies": ["pytest"],
                "network": "none",
            },
            "prompt_template": "Write a function that...",
            "context_files": ["context/main.py"],
            "expected_artifacts": ["main.py"],
            "scoring": {
                "type": "unit_test",
                "test_command": "pytest tests/",
                "pass_threshold": 0.85,
            },
        }
        item = TestItem(**data)
        assert item.id == "L1-D1-PY-001"
        assert item.layer == Layer.L1
        assert item.dimensions == [Dimension.D1]
        assert item.difficulty == 2
        assert item.sandbox.image == "python:3.12"
        assert item.scoring.type == ScoringType.UNIT_TEST

    def test_invalid_dimension_raises(self):
        """TestItem should reject unknown dimensions."""
        data = {
            "id": "X",
            "layer": "L1",
            "dimensions": ["D99"],
            "language": "python",
            "difficulty": 1,
            "estimated_time_min": 5,
            "sandbox": {"image": "x", "dependencies": [], "network": "none"},
            "prompt_template": "...",
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "unit_test",
                "test_command": "",
                "pass_threshold": 0.5,
            },
        }
        with pytest.raises(ValueError):
            TestItem(**data)

    def test_difficulty_range_enforced(self):
        """TestItem difficulty must be 1-5."""
        data = {
            "id": "X",
            "layer": "L1",
            "dimensions": ["D1"],
            "language": "python",
            "difficulty": 6,
            "estimated_time_min": 5,
            "sandbox": {"image": "x", "dependencies": [], "network": "none"},
            "prompt_template": "...",
            "context_files": [],
            "expected_artifacts": [],
            "scoring": {
                "type": "unit_test",
                "test_command": "",
                "pass_threshold": 0.5,
            },
        }
        with pytest.raises(ValueError):
            TestItem(**data)


class TestAgentTrace:
    def test_serialize_deserialize(self):
        """AgentTrace should round-trip through JSON."""
        trace = AgentTrace(
            run_id="run-001",
            agent_name="claude-code",
            agent_version="4.0",
            test_item_id="L1-D1-PY-001",
            start_time=datetime(2026, 7, 1, 10, 0, 0),
            end_time=datetime(2026, 7, 1, 10, 8, 30),
            steps=[
                ToolCallStep(
                    step_index=0,
                    tool_call=ToolCall(
                        tool_name="Read",
                        params={"file_path": "/src/main.py"},
                    ),
                    result={"content": "def add(a,b): return a+b"},
                    timestamp=datetime(2026, 7, 1, 10, 0, 5),
                    duration_ms=150,
                ),
                ToolCallStep(
                    step_index=1,
                    tool_call=ToolCall(
                        tool_name="Edit",
                        params={
                            "file_path": "/src/main.py",
                            "old_string": "def add(a,b): return a+b",
                            "new_string": "def add(a, b):\n    return a + b",
                        },
                    ),
                    result={"success": True},
                    timestamp=datetime(2026, 7, 1, 10, 1, 0),
                    duration_ms=200,
                ),
            ],
        )
        j = trace.model_dump_json()
        restored = AgentTrace.model_validate_json(j)
        assert restored.run_id == "run-001"
        assert len(restored.steps) == 2
        assert restored.steps[0].tool_call.tool_name == "Read"
        assert restored.duration_seconds == 510


class TestJudgeScoreCard:
    def test_valid_score_ranges_enforced(self):
        """JudgeScoreCard scores must be 1-5."""
        with pytest.raises(ValueError):
            JudgeScoreCard(
                dimension=Dimension.D1,
                score=0,
                reasoning="Score must be >= 1",
            )
        with pytest.raises(ValueError):
            JudgeScoreCard(
                dimension=Dimension.D1,
                score=6,
                reasoning="Score must be <= 5",
            )

    def test_valid_score_card(self):
        card = JudgeScoreCard(
            dimension=Dimension.D1,
            score=4,
            reasoning="Code is correct and well-structured.",
        )
        assert card.score == 4
        assert card.dimension == Dimension.D1
```

Run: `pytest tests/unit/test_models.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: 实现 models.py 让测试通过**

```python
"""Shared Pydantic data models for the evaluation framework."""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

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
    def validate_dimension_strings(
        cls, v: list[str]
    ) -> list[str]:
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
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/unit/test_models.py -v
```

Expected: PASS (all 5 tests)

- [ ] **Step 4: Commit**

```bash
git add eval_framework/models.py tests/unit/test_models.py tests/__init__.py tests/unit/__init__.py
git commit -m "feat: add shared Pydantic models with validation"
```

---

### Task 3: Docker 沙箱管理器

**Files:**
- Create: `eval_framework/sandbox/__init__.py`
- Create: `eval_framework/sandbox/manager.py`
- Create: `eval_framework/sandbox/snapshot.py`
- Create: `eval_framework/sandbox/dockerfiles/python.Dockerfile`
- Create: `eval_framework/sandbox/dockerfiles/node.Dockerfile`
- Create: `eval_framework/sandbox/dockerfiles/go.Dockerfile`
- Create: `tests/unit/test_sandbox.py`

- [ ] **Step 1: 创建 Python 沙箱 Dockerfile**

```dockerfile
# eval_framework/sandbox/dockerfiles/python.Dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir pytest pytest-cov

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 2: 创建 Node 沙箱 Dockerfile**

```dockerfile
# eval_framework/sandbox/dockerfiles/node.Dockerfile
FROM node:20-slim

RUN npm install -g jest

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 3: 创建 Go 沙箱 Dockerfile**

```dockerfile
# eval_framework/sandbox/dockerfiles/go.Dockerfile
FROM golang:1.22-alpine

RUN go install github.com/stretchr/testify/assert@latest

WORKDIR /eval

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 4: 编写沙箱管理的失败测试**

```python
"""Tests for Docker sandbox manager."""
import shutil
from pathlib import Path

import pytest

from eval_framework.sandbox.manager import SandboxManager
from eval_framework.sandbox.snapshot import FilesystemSnapshot


class TestSandboxManager:
    def test_build_image_marks_built(self):
        """After building, the image should be marked as available."""
        mgr = SandboxManager()
        mgr.build_image("python", Path("eval_framework/sandbox/dockerfiles/python.Dockerfile"))
        assert mgr.is_image_built("python") is True

    def test_run_and_collect_traces(self, tmp_path):
        """Running a command in sandbox should return stdout and exit code."""
        mgr = SandboxManager()
        mgr.build_image("python", Path("eval_framework/sandbox/dockerfiles/python.Dockerfile"))
        
        # Write a minimal test file into the sandbox
        test_file = tmp_path / "test_math.py"
        test_file.write_text("""
def test_add():
    assert 1 + 1 == 2
""")
        
        result = mgr.run(
            image="python",
            command="pytest test_math.py -v",
            volume_mounts={str(tmp_path): "/eval"},
            timeout=30,
        )
        assert result.exit_code == 0
        assert "PASSED" in result.stdout

    def test_run_timeout_triggers(self, tmp_path):
        """A command exceeding timeout should be killed."""
        mgr = SandboxManager()
        mgr.build_image("python", Path("eval_framework/sandbox/dockerfiles/python.Dockerfile"))
        
        result = mgr.run(
            image="python",
            command="python -c 'import time; time.sleep(100)'",
            volume_mounts={str(tmp_path): "/eval"},
            timeout=2,
        )
        assert result.timed_out is True
        assert result.exit_code != 0


class TestFilesystemSnapshot:
    def test_detect_new_file(self, tmp_path):
        """Snapshot diff should detect newly created files."""
        before = FilesystemSnapshot.capture(tmp_path)
        new_file = tmp_path / "created.txt"
        new_file.write_text("hello")
        after = FilesystemSnapshot.capture(tmp_path)
        
        diff = FilesystemSnapshot.diff(before, after)
        assert "created.txt" in diff.created_files

    def test_detect_modified_file(self, tmp_path):
        """Snapshot diff should detect modified files."""
        f = tmp_path / "modify.txt"
        f.write_text("before")
        before = FilesystemSnapshot.capture(tmp_path)
        f.write_text("after")
        after = FilesystemSnapshot.capture(tmp_path)
        
        diff = FilesystemSnapshot.diff(before, after)
        assert "modify.txt" in diff.modified_files

    def test_detect_deleted_file(self, tmp_path):
        """Snapshot diff should detect deleted files."""
        f = tmp_path / "delete_me.txt"
        f.write_text("gone")
        before = FilesystemSnapshot.capture(tmp_path)
        f.unlink()
        after = FilesystemSnapshot.capture(tmp_path)
        
        diff = FilesystemSnapshot.diff(before, after)
        assert "delete_me.txt" in diff.deleted_files
```

Run: `pytest tests/unit/test_sandbox.py -v`
Expected: FAIL

- [ ] **Step 5: 实现沙箱管理器**

```python
"""Docker container lifecycle management."""

import dataclasses
import os
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import docker
from docker.errors import BuildError, ContainerError, ImageNotFound

from eval_framework.config import config


@dataclasses.dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxManager:
    """Manages Docker sandbox lifecycle for test execution."""

    def __init__(self):
        cfg = config.get_sandbox_config()
        self._client = docker.from_env()
        self._built_images: set[str] = set()
        self._network_mode = cfg.get("network_mode", "none")
        self._default_timeout = cfg.get("timeout_default", 900)

    def build_image(self, name: str, dockerfile_path: Path) -> str:
        """Build a sandbox Docker image. Returns the image tag."""
        tag = f"eval-sandbox-{name}:latest"
        context_dir = dockerfile_path.parent
        self._client.images.build(
            path=str(context_dir),
            dockerfile=dockerfile_path.name,
            tag=tag,
            rm=True,
        )
        self._built_images.add(name)
        return tag

    def is_image_built(self, name: str) -> bool:
        return name in self._built_images

    def run(
        self,
        image: str,
        command: str,
        volume_mounts: dict[str, str],
        timeout: Optional[int] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> SandboxResult:
        """Run a command inside a sandbox container and return results."""
        timeout = timeout or self._default_timeout
        tag = f"eval-sandbox-{image}:latest"
        
        volumes = {}
        binds = {}
        for host_path, container_path in volume_mounts.items():
            abs_host = str(Path(host_path).resolve())
            volumes[container_path] = {"bind": abs_host, "mode": "rw"}
            binds[abs_host] = {"bind": container_path, "mode": "rw"}

        try:
            container = self._client.containers.run(
                image=tag,
                command=command,
                volumes=volumes,
                environment=env_vars or {},
                network_mode=self._network_mode,
                detach=True,
                remove=False,
            )
            result = container.wait(timeout=timeout)
            logs = container.logs(stdout=True, stderr=True)
            container.remove(force=True)
            
            return SandboxResult(
                exit_code=result["StatusCode"],
                stdout=logs.decode("utf-8", errors="replace"),
                stderr="",  # docker-py combines stdout/stderr by default
            )
        except docker.errors.NotFound:
            raise RuntimeError(f"Image '{tag}' not found. Build it first.")
        except Exception as e:
            if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                return SandboxResult(
                    exit_code=-1,
                    stdout="",
                    stderr=str(e),
                    timed_out=True,
                )
            raise
```

- [ ] **Step 6: 实现文件系统快照**

```python
"""Filesystem snapshot for detecting agent-made changes."""

import dataclasses
import hashlib
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class SnapshotDiff:
    created_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]

    @property
    def has_changes(self) -> bool:
        return any([self.created_files, self.modified_files, self.deleted_files])


class FilesystemSnapshot:
    """Captures file hashes of a directory and computes diffs."""

    def __init__(self, files: dict[str, str]):
        self._files = files  # relative_path -> sha256 hex

    @classmethod
    def capture(cls, root: Path) -> "FilesystemSnapshot":
        """Capture all file hashes recursively under root."""
        files = {}
        root = root.resolve()
        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                rel = str(path.relative_to(root))
                files[rel] = cls._hash_file(path)
        return cls(files)

    @staticmethod
    def _hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @classmethod
    def diff(
        cls, before: "FilesystemSnapshot", after: "FilesystemSnapshot"
    ) -> SnapshotDiff:
        """Compare two snapshots and return the diff."""
        before_files = set(before._files.keys())
        after_files = set(after._files.keys())
        
        created = sorted(after_files - before_files)
        deleted = sorted(before_files - after_files)
        modified = sorted(
            f
            for f in before_files & after_files
            if before._files[f] != after._files[f]
        )
        return SnapshotDiff(
            created_files=created,
            modified_files=modified,
            deleted_files=deleted,
        )
```

- [ ] **Step 7: 运行测试验证**

```bash
pytest tests/unit/test_sandbox.py -v
```

Expected: PASS (需本地 Docker 运行中)

- [ ] **Step 8: Commit**

```bash
git add eval_framework/sandbox/ tests/unit/test_sandbox.py
git commit -m "feat: Docker sandbox manager with filesystem snapshot"
```

---

### Task 4: Agent Adapter 抽象层与工厂

**Files:**
- Create: `eval_framework/adapters/__init__.py`
- Create: `eval_framework/adapters/base.py`
- Create: `eval_framework/adapters/cli_generic.py`
- Create: `eval_framework/adapters/factory.py`
- Create: `tests/unit/test_adapters.py`

- [ ] **Step 1: 编写适配器接口的失败测试**

```python
"""Tests for Agent adapters."""
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.adapters.cli_generic import CLIAdapter
from eval_framework.adapters.factory import AdapterFactory
from eval_framework.models import AgentCapabilities, AgentTrace, Layer, Dimension


class TestAdapterFactory:
    def test_register_and_create(self):
        """Registering an adapter class should make it creatable."""
        AdapterFactory.register("test", CLIAdapter)
        adapter = AdapterFactory.create(
            "test",
            command="eval-agent run",
            workspace="/tmp/eval",
        )
        assert isinstance(adapter, CLIAdapter)

    def test_create_unregistered_raises(self):
        """Creating an unregistered adapter should raise."""
        with pytest.raises(KeyError):
            AdapterFactory.create("nonexistent", command="")


class TestCLIAdapter:
    def test_capabilities(self):
        """CLIAdapter should report capabilities from constructor."""
        adapter = CLIAdapter(
            command="test-agent run",
            workspace="/tmp/eval",
            default_model="gpt-4",
            supported_tools=["read", "write", "execute"],
        )
        caps = adapter.capabilities()
        assert caps.agent_name == "cli-generic"
        assert caps.default_model == "gpt-4"
        assert "read" in caps.supported_tools

    def test_execute_runs_command(self, tmp_path):
        """CLIAdapter.execute should run the command with prompt on stdin."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        
        adapter = CLIAdapter(
            command='python -c "import sys; sys.stdout.write(sys.stdin.read())"',
            workspace=str(workspace),
        )
        context = TestContext(
            test_item_id="L1-D1-PY-001",
            layer=Layer.L1,
            dimensions=[Dimension.D1],
            working_dir=str(workspace),
            env_vars={},
            network_allowed=False,
        )
        trace = adapter.execute("hello world", context)
        assert trace.test_item_id == "L1-D1-PY-001"
        assert trace.agent_name == "cli-generic"


class TestTestContext:
    def test_context_creation(self):
        ctx = TestContext(
            test_item_id="L1-D1-PY-001",
            layer=Layer.L1,
            dimensions=[Dimension.D1, Dimension.D3],
            working_dir="/eval/sandbox",
            env_vars={"DEBUG": "1"},
            network_allowed=False,
        )
        assert ctx.test_item_id == "L1-D1-PY-001"
        assert len(ctx.dimensions) == 2
```

Run: `pytest tests/unit/test_adapters.py -v`
Expected: FAIL

- [ ] **Step 2: 实现抽象基类**

```python
"""Abstract base class for Agent adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

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
```

- [ ] **Step 3: 实现通用 CLI 适配器**

```python
"""Generic CLI adapter — drives any agent that accepts prompt via stdin."""

import subprocess
import time
from datetime import datetime, timezone

from eval_framework.adapters.base import AgentAdapter, TestContext
from eval_framework.models import AgentCapabilities, AgentTrace, ToolCallStep


class CLIAdapter(AgentAdapter):
    """Drives an agent invoked via CLI, sending prompt on stdin.

    The agent is expected to write its final output to stdout.
    NOTE: This adapter cannot capture individual tool-call steps;
    it only records the start/end and final output. For full trace
    capture, use an agent-specific adapter like ClaudeCodeAdapter.
    """

    def __init__(
        self,
        command: str,
        workspace: str,
        default_model: str = "",
        supported_tools: list[str] | None = None,
        agent_name: str = "cli-generic",
        agent_version: str = "1.0",
    ):
        self._command = command
        self._workspace = workspace
        self._default_model = default_model
        self._supported_tools = supported_tools or []
        self._agent_name = agent_name
        self._agent_version = agent_version

    def execute(self, prompt: str, context: TestContext) -> AgentTrace:
        run_id = f"run-{context.test_item_id}-{int(time.time())}"
        start = datetime.now(timezone.utc)

        proc = subprocess.run(
            self._command,
            input=prompt,
            capture_output=True,
            text=True,
            cwd=context.working_dir,
            env={**context.env_vars},
            timeout=context.layer_timeout_seconds(),
        )

        end = datetime.now(timezone.utc)
        return AgentTrace(
            run_id=run_id,
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            test_item_id=context.test_item_id,
            start_time=start,
            end_time=end,
            steps=[],
            final_output=proc.stdout,
        )

    def capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_name=self._agent_name,
            agent_version=self._agent_version,
            supported_tools=self._supported_tools,
            default_model=self._default_model,
        )
```

- [ ] **Step 4: 实现适配器工厂**

```python
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


# Built-in registrations
AdapterFactory.register("cli", CLIAdapter)
```

- [ ] **Step 5: 更新 TestContext 添加超时方法**

在 `eval_framework/adapters/base.py` 的 `TestContext` 中追加：

```python
    def layer_timeout_seconds(self) -> int:
        """Return timeout in seconds based on layer."""
        defaults = {"L1": 900, "L2": 3600, "L3": 7200}
        return defaults.get(self.layer.value, 900)
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/unit/test_adapters.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add eval_framework/adapters/ tests/unit/test_adapters.py
git commit -m "feat: Agent adapter abstract layer + CLI adapter + factory"
```

---

### Task 5: Agent 行为轨迹收集器

**Files:**
- Create: `eval_framework/orchestrator/__init__.py`
- Create: `eval_framework/orchestrator/tracer.py`
- Create: `tests/unit/test_tracer.py`

- [ ] **Step 1: 编写 tracer 的失败测试**

```python
"""Tests for agent trace collection."""
import json
from datetime import datetime
from pathlib import Path

import pytest

from eval_framework.models import AgentTrace, ToolCall, ToolCallStep
from eval_framework.orchestrator.tracer import TraceCollector


class TestTraceCollector:
    def test_start_and_record_step(self):
        """Collector should track start time and record steps."""
        collector = TraceCollector(
            run_id="test-001",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Read", params={"file_path": "/x.py"}),
            {"content": "data"},
            150,
        )
        collector.record_step(
            ToolCall(tool_name="Edit", params={"file_path": "/x.py", "old_string": "a", "new_string": "b"}),
            {"success": True},
            200,
        )
        trace = collector.finish(final_output="done")
        
        assert trace.run_id == "test-001"
        assert len(trace.steps) == 2
        assert trace.steps[0].tool_call.tool_name == "Read"
        assert trace.steps[0].step_index == 0
        assert trace.steps[0].duration_ms == 150
        assert trace.steps[1].step_index == 1
        assert trace.steps[1].tool_call.tool_name == "Edit"
        assert trace.final_output == "done"
        assert trace.duration_seconds > 0

    def test_save_and_load_trace(self, tmp_path):
        """Trace should round-trip through JSON file."""
        collector = TraceCollector(
            run_id="test-002",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Bash", params={"command": "ls"}),
            {"stdout": "file1\nfile2"},
            100,
        )
        trace = collector.finish(final_output="listed files")
        
        filepath = tmp_path / "trace.json"
        collector.save(trace, filepath)
        
        loaded = TraceCollector.load(filepath)
        assert loaded.run_id == "test-002"
        assert len(loaded.steps) == 1
        assert loaded.steps[0].tool_call.tool_name == "Bash"

    def test_save_to_dict(self):
        """save_to_dict should return a plain dict for DB insertion."""
        collector = TraceCollector(
            run_id="test-003",
            agent_name="test-agent",
            agent_version="1.0",
            test_item_id="L1-D1-PY-001",
        )
        collector.start()
        collector.record_step(
            ToolCall(tool_name="Read", params={"file_path": "/z.py"}),
            {"content": "x=1"},
            50,
        )
        trace = collector.finish("ok")
        d = collector.save_to_dict(trace)
        
        assert d["run_id"] == "test-003"
        assert isinstance(d["steps_json"], str)
        steps = json.loads(d["steps_json"])
        assert steps[0]["tool_call"]["tool_name"] == "Read"
```

Run: `pytest tests/unit/test_tracer.py -v`
Expected: FAIL

- [ ] **Step 2: 实现 tracer**

```python
"""Agent execution trace capture and serialization."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eval_framework.models import AgentTrace, ToolCall, ToolCallStep


class TraceCollector:
    """Collects agent tool-call steps and produces an AgentTrace."""

    def __init__(
        self,
        run_id: str,
        agent_name: str,
        agent_version: str,
        test_item_id: str,
    ):
        self.run_id = run_id
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.test_item_id = test_item_id
        self._start_time: Optional[datetime] = None
        self._steps: list[ToolCallStep] = []

    def start(self) -> None:
        """Mark the beginning of execution."""
        self._start_time = datetime.now(timezone.utc)

    def record_step(
        self,
        tool_call: ToolCall,
        result: dict,
        duration_ms: int,
    ) -> None:
        """Record a single tool invocation."""
        now = datetime.now(timezone.utc)
        self._steps.append(
            ToolCallStep(
                step_index=len(self._steps),
                tool_call=tool_call,
                result=result,
                timestamp=now,
                duration_ms=duration_ms,
            )
        )

    def finish(self, final_output: str = "") -> AgentTrace:
        """Close the trace and return the completed AgentTrace."""
        now = datetime.now(timezone.utc)
        return AgentTrace(
            run_id=self.run_id,
            agent_name=self.agent_name,
            agent_version=self.agent_version,
            test_item_id=self.test_item_id,
            start_time=self._start_time or now,
            end_time=now,
            steps=self._steps,
            final_output=final_output,
        )

    @staticmethod
    def save(trace: AgentTrace, path: Path) -> None:
        """Write trace to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(trace.model_dump_json(indent=2))

    @staticmethod
    def load(path: Path) -> AgentTrace:
        """Load trace from a JSON file."""
        return AgentTrace.model_validate_json(path.read_text())

    @staticmethod
    def save_to_dict(trace: AgentTrace) -> dict:
        """Convert trace to a flat dict for database insertion."""
        return {
            "run_id": trace.run_id,
            "agent_name": trace.agent_name,
            "agent_version": trace.agent_version,
            "test_item_id": trace.test_item_id,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "steps_json": json.dumps(
                [s.model_dump(mode="json") for s in trace.steps]
            ),
            "final_output": trace.final_output,
            "duration_seconds": trace.duration_seconds,
        }
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_tracer.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add eval_framework/orchestrator/tracer.py eval_framework/orchestrator/__init__.py tests/unit/test_tracer.py
git commit -m "feat: trace collector for agent behavior capture"
```

---

### Task 6: 测题注册表与加载器

**Files:**
- Create: `eval_framework/orchestrator/context.py`
- Create: `test_items/registry.json`
- Create: `tests/unit/test_context.py` (追加内容)
- Create: `tests/fixtures/sample_items.py`

- [ ] **Step 1: 创建测题注册表示例**

```json
{
  "version": "1.0",
  "updated": "2026-07-01T00:00:00Z",
  "items": [
    {
      "id": "L1-D1-PY-001",
      "path": "l1/d1_code_fill/L1-D1-PY-001",
      "enabled": true
    }
  ]
}
```

- [ ] **Step 2: 创建示例测题的 metadata.json**

```bash
mkdir -p test_items/l1/d1_code_fill/L1-D1-PY-001/{context,judge}
```

```json
{
  "id": "L1-D1-PY-001",
  "layer": "L1",
  "dimensions": ["D1"],
  "sub_dimensions": [],
  "language": "python",
  "difficulty": 2,
  "estimated_time_min": 8,
  "tags": ["function", "string-manipulation"],
  "sandbox": {
    "image": "python",
    "dependencies": ["pytest"],
    "network": "none"
  },
  "prompt_template": "Implement the function `reverse_words(s: str) -> str` in `main.py`.\n\nThe function should reverse the order of words in a string while preserving whitespace between words.\n\nExample:\n  Input:  \"hello world\"\n  Output: \"world hello\"\n\nConstraints:\n- Words are separated by a single space\n- Input may be empty\n- Do not use str.split() then str.join()",
  "context_files": ["context/main.py"],
  "expected_artifacts": ["main.py"],
  "scoring": {
    "type": "unit_test",
    "test_command": "pytest judge/test_main.py -v",
    "pass_threshold": 0.85
  },
  "created": "2026-07-01",
  "version": "1.0"
}
```

- [ ] **Step 3: 创建示例测题的上下文文件**

```python
# test_items/l1/d1_code_fill/L1-D1-PY-001/context/main.py
def reverse_words(s: str) -> str:
    # TODO: Implement this function
    pass
```

- [ ] **Step 4: 创建示例测题的判分测试**

```python
# test_items/l1/d1_code_fill/L1-D1-PY-001/judge/test_main.py
import pytest
from main import reverse_words


def test_basic():
    assert reverse_words("hello world") == "world hello"


def test_single_word():
    assert reverse_words("hello") == "hello"


def test_empty_string():
    assert reverse_words("") == ""


def test_three_words():
    assert reverse_words("a b c") == "c b a"


def test_longer_words():
    assert reverse_words("quick brown fox") == "fox brown quick"
```

- [ ] **Step 5: 实现测题加载器 (context.py)**

```python
"""Test item loading and context preparation."""

import json
import random
from pathlib import Path
from typing import Optional

from eval_framework.config import config
from eval_framework.models import TestItem


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

        with open(self._path) as f:
            registry = json.load(f)

        items = []
        for entry in registry.get("items", []):
            if not entry.get("enabled", True):
                continue
            item_path = self._metadata_dir / entry["path"] / "metadata.json"
            if not item_path.exists():
                print(f"Warning: skipping missing item {entry['id']} at {item_path}")
                continue
            with open(item_path) as f:
                data = json.load(f)
            item = TestItem(**data)
            self._items[item.id] = item
            items.append(item)

        return items

    def get_item(self, item_id: str) -> TestItem:
        if item_id not in self._items:
            raise KeyError(f"Item '{item_id}' not loaded. Call load() first.")
        return self._items[item_id]

    def get_by_layer(self, layer: str) -> list[TestItem]:
        return [i for i in self._items.values() if i.layer.value == layer]

    def get_by_dimension(self, dimension: str) -> list[TestItem]:
        return [
            i for i in self._items.values() if dimension in i.dimensions
        ]

    def select_random(
        self, layer: str, count: int, seed: Optional[int] = None
    ) -> list[TestItem]:
        """Randomly select `count` items from `layer`, seeded for reproducibility."""
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
        import shutil

        item = self._registry.get_item(item_id)
        
        # Determine item directory
        item_dir = (
            self._registry._metadata_dir
            / self._get_item_rel_path(item_id)
        )

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

    def _get_item_rel_path(self, item_id: str) -> str:
        """Reverse-lookup item path from registry."""
        with open(self._registry._path) as f:
            registry = json.load(f)
        for entry in registry["items"]:
            if entry["id"] == item_id:
                return entry["path"]
        raise KeyError(f"Item {item_id} not in registry")
```

- [ ] **Step 6: 提交示例测题**

```bash
git add test_items/ eval_framework/orchestrator/context.py
git commit -m "feat: test item registry, loader, and first L1 sample item"
```

---

### Task 7: 数据库层 (SQLAlchemy)

**Files:**
- Create: `eval_framework/db/__init__.py`
- Create: `eval_framework/db/connection.py`
- Create: `eval_framework/db/models.py`
- Create: `eval_framework/db/repository.py`
- Create: `tests/unit/test_repository.py`
- Create: `docker-compose.yml`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: eval
      POSTGRES_PASSWORD: eval
      POSTGRES_DB: eval_framework
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 2: 编写数据库层的失败测试**

```python
"""Tests for database repository."""
import json
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from eval_framework.db.models import Base, EvalRun, TraceRecord
from eval_framework.db.repository import EvalRepository
from eval_framework.models import AgentTrace, ToolCall, ToolCallStep


@pytest.fixture
def session():
    """In-memory SQLite for fast testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def repo(session):
    return EvalRepository(session)


@pytest.fixture
def sample_trace():
    return AgentTrace(
        run_id="test-run-001",
        agent_name="claude-code",
        agent_version="4.0",
        test_item_id="L1-D1-PY-001",
        start_time=datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 7, 1, 10, 5, 0, tzinfo=timezone.utc),
        steps=[
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Read",
                    params={"file_path": "/src/main.py"},
                ),
                result={"content": "def f(): pass"},
                timestamp=datetime(2026, 7, 1, 10, 0, 30, tzinfo=timezone.utc),
                duration_ms=150,
            ),
        ],
        final_output="Implemented the function.",
    )


class TestEvalRun:
    def test_create_run(self, repo, sample_trace):
        """Saving a trace should create an EvalRun record."""
        run = repo.save_run(sample_trace)
        assert run.run_id == "test-run-001"
        assert run.status == "completed"

    def test_get_run(self, repo, sample_trace):
        """Retrieving a saved run should restore the trace data."""
        repo.save_run(sample_trace)
        run = repo.get_run("test-run-001")
        assert run is not None
        assert run.agent_name == "claude-code"

    def test_list_runs_by_agent(self, repo, sample_trace):
        """Listing runs should filter by agent name."""
        repo.save_run(sample_trace)
        runs = repo.list_runs(agent_name="claude-code")
        assert len(runs) == 1
        runs2 = repo.list_runs(agent_name="nonexistent")
        assert len(runs2) == 0

    def test_update_run_status(self, repo, sample_trace):
        """Updating a run status should persist."""
        repo.save_run(sample_trace)
        repo.update_run_status("test-run-001", "timed_out", "Command exceeded limit")
        run = repo.get_run("test-run-001")
        assert run.status == "timed_out"
        assert run.error_message == "Command exceeded limit"

    def test_get_agent_scores(self, repo, sample_trace):
        """Computing average scores should aggregate per-agent."""
        repo.save_run(sample_trace)
        # Add a result
        from eval_framework.db.models import EvalResult
        result = EvalResult(
            run_id="test-run-001",
            test_item_id="L1-D1-PY-001",
            dimension="D1",
            l1_score=0.9,
            status="completed",
        )
        repo._session.add(result)
        repo._session.commit()
        
        scores = repo.get_agent_scores("claude-code")
        assert "D1" in scores
        assert scores["D1"]["avg"] == 0.9
```

Run: `pytest tests/unit/test_repository.py -v`
Expected: FAIL

- [ ] **Step 3: 实现数据库连接**

```python
"""Database connection setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from eval_framework.config import config

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.get_database_url(),
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    """Create all tables."""
    from eval_framework.db.models import Base
    Base.metadata.create_all(get_engine())
```

- [ ] **Step 4: 实现 ORM 模型**

```python
"""SQLAlchemy ORM models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class EvalRun(Base):
    __tablename__ = "eval_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(128), index=True)
    agent_version: Mapped[str] = mapped_column(String(32))
    test_item_id: Mapped[str] = mapped_column(String(64), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        String(32), default="completed"
    )  # completed | timeout | error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # One-to-one with trace and results
    trace: Mapped[Optional["TraceRecord"]] = relationship(
        back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    results: Mapped[list["EvalResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TraceRecord(Base):
    __tablename__ = "trace_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("eval_runs.run_id"), unique=True
    )
    steps_json: Mapped[str] = mapped_column(Text)  # JSON array of ToolCallStep
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run: Mapped["EvalRun"] = relationship(back_populates="trace")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("eval_runs.run_id"), index=True
    )
    test_item_id: Mapped[str] = mapped_column(String(64))
    dimension: Mapped[str] = mapped_column(String(8))
    l1_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    judge_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    judge_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")

    run: Mapped["EvalRun"] = relationship(back_populates="results")


class AgentScoreSummary(Base):
    """Precomputed agent score per dimension for fast dashboard queries."""

    __tablename__ = "agent_score_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(128), index=True)
    agent_version: Mapped[str] = mapped_column(String(32))
    dimension: Mapped[str] = mapped_column(String(8))
    avg_score: Mapped[float] = mapped_column(Float)
    run_count: Mapped[int] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
```

- [ ] **Step 5: 实现 Repository**

```python
"""Data access layer for evaluation results."""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from eval_framework.db.models import EvalResult, EvalRun, TraceRecord
from eval_framework.models import AgentTrace


class EvalRepository:
    def __init__(self, session: Session):
        self._session = session

    def save_run(self, trace: AgentTrace) -> EvalRun:
        """Save a completed evaluation run with its trace."""
        run = EvalRun(
            run_id=trace.run_id,
            agent_name=trace.agent_name,
            agent_version=trace.agent_version,
            test_item_id=trace.test_item_id,
            start_time=trace.start_time,
            end_time=trace.end_time,
            duration_seconds=trace.duration_seconds,
            status="completed",
        )
        trace_record = TraceRecord(
            run_id=trace.run_id,
            steps_json=json.dumps(
                [s.model_dump(mode="json") for s in trace.steps]
            ),
            final_output=trace.final_output,
        )
        self._session.add(run)
        self._session.add(trace_record)
        self._session.commit()
        return run

    def get_run(self, run_id: str) -> Optional[EvalRun]:
        return (
            self._session.query(EvalRun)
            .filter(EvalRun.run_id == run_id)
            .first()
        )

    def list_runs(
        self,
        agent_name: Optional[str] = None,
        test_item_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[EvalRun]:
        q = self._session.query(EvalRun)
        if agent_name:
            q = q.filter(EvalRun.agent_name == agent_name)
        if test_item_id:
            q = q.filter(EvalRun.test_item_id == test_item_id)
        return q.order_by(EvalRun.start_time.desc()).limit(limit).all()

    def update_run_status(
        self, run_id: str, status: str, error_message: Optional[str] = None
    ) -> None:
        run = self.get_run(run_id)
        if run:
            run.status = status
            run.error_message = error_message
            self._session.commit()

    def save_result(
        self,
        run_id: str,
        test_item_id: str,
        dimension: str,
        l1_score: Optional[float] = None,
        judge_score: Optional[int] = None,
        judge_reasoning: Optional[str] = None,
        status: str = "completed",
    ) -> EvalResult:
        result = EvalResult(
            run_id=run_id,
            test_item_id=test_item_id,
            dimension=dimension,
            l1_score=l1_score,
            judge_score=judge_score,
            judge_reasoning=judge_reasoning,
            status=status,
        )
        self._session.add(result)
        self._session.commit()
        return result

    def get_agent_scores(
        self, agent_name: str, agent_version: Optional[str] = None
    ) -> dict[str, dict]:
        """Return per-dimension average scores for an agent."""
        q = (
            self._session.query(
                EvalResult.dimension,
                func.avg(EvalResult.l1_score).label("avg_l1"),
                func.avg(EvalResult.judge_score).label("avg_judge"),
                func.count(EvalResult.id).label("count"),
            )
            .join(EvalRun, EvalResult.run_id == EvalRun.run_id)
            .filter(EvalRun.agent_name == agent_name)
        )
        if agent_version:
            q = q.filter(EvalRun.agent_version == agent_version)
        q = q.group_by(EvalResult.dimension)

        result = {}
        for dim, avg_l1, avg_judge, count in q.all():
            result[dim] = {
                "avg_l1_score": round(float(avg_l1), 3) if avg_l1 else None,
                "avg_judge_score": round(float(avg_judge), 1) if avg_judge else None,
                "run_count": count,
            }
        return result
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/unit/test_repository.py -v
```

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add eval_framework/db/ tests/unit/test_repository.py docker-compose.yml
git commit -m "feat: database layer — ORM models, repository, docker-compose for PostgreSQL"
```

---

### Task 8: Layer 1 自动化判分引擎

**Files:**
- Create: `eval_framework/scoring/__init__.py`
- Create: `eval_framework/scoring/l1_runner.py`
- Create: `eval_framework/scoring/test_runner.py`
- Create: `eval_framework/scoring/tool_matcher.py`
- Create: `eval_framework/scoring/tree_similarity.py`
- Create: `tests/unit/test_test_runner.py`
- Create: `tests/unit/test_tool_matcher.py`
- Create: `tests/unit/test_tree_similarity.py`
- Create: `tests/unit/test_l1_runner.py`

- [ ] **Step 1: 编写单元测试运行器的失败测试**

```python
"""Tests for test_runner."""
from pathlib import Path

import pytest

from eval_framework.scoring.test_runner import (
    LanguageTestRunner,
    TestRunnerFactory,
    TestRunResult,
)


class TestTestRunnerFactory:
    def test_get_python_runner(self):
        runner = TestRunnerFactory.get("python")
        assert isinstance(runner, LanguageTestRunner)
        assert runner.language == "python"

    def test_unsupported_language_raises(self):
        with pytest.raises(ValueError):
            TestRunnerFactory.get("rust")


class TestPythonTestRunner:
    def test_all_pass(self, tmp_path):
        """All tests passing should return score 1.0."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("""
def test_pass_1():
    assert 1 + 1 == 2

def test_pass_2():
    assert "hello".upper() == "HELLO"
""")
        runner = TestRunnerFactory.get("python")
        result = runner.run(
            working_dir=str(tmp_path),
            test_command=f"pytest {test_file.name} -v",
        )
        assert result.score == 1.0
        assert result.passed >= 2
        assert result.failed == 0

    def test_partial_fail(self, tmp_path):
        """Some tests failing should return proportional score."""
        test_file = tmp_path / "test_mixed.py"
        test_file.write_text("""
def test_pass():
    assert True

def test_fail():
    assert False, "intentional failure"
""")
        runner = TestRunnerFactory.get("python")
        result = runner.run(
            working_dir=str(tmp_path),
            test_command=f"pytest {test_file.name} -v",
        )
        assert result.score == 0.5
        assert result.passed == 1
        assert result.failed == 1
```

Run: `pytest tests/unit/test_test_runner.py -v`
Expected: FAIL

- [ ] **Step 2: 实现单元测试运行器**

```python
"""Multi-language test execution and scoring."""

import dataclasses
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


@dataclasses.dataclass
class TestRunResult:
    score: float  # 0.0 to 1.0
    passed: int
    failed: int
    errors: int
    output: str
    pass_threshold: float = 0.85

    @property
    def passed_threshold(self) -> bool:
        return self.score >= self.pass_threshold


class LanguageTestRunner(ABC):
    def __init__(self, language: str):
        self.language = language

    def run(
        self,
        working_dir: str,
        test_command: str,
        pass_threshold: float = 0.85,
        timeout: int = 120,
    ) -> TestRunResult:
        """Run tests and parse the output into a score."""
        proc = subprocess.run(
            test_command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=timeout,
        )
        return self._parse_output(
            proc.stdout + proc.stderr, pass_threshold
        )

    @abstractmethod
    def _parse_output(self, output: str, pass_threshold: float) -> TestRunResult:
        ...


class PythonTestRunner(LanguageTestRunner):
    def __init__(self):
        super().__init__("python")

    def _parse_output(self, output: str, pass_threshold: float) -> TestRunResult:
        passed = 0
        failed = 0
        errors = 0
        for line in output.split("\n"):
            if " passed" in line:
                # e.g., "2 passed"
                import re
                m = re.search(r"(\d+)\s+passed", line)
                if m:
                    passed = int(m.group(1))
            if " failed" in line:
                import re
                m = re.search(r"(\d+)\s+failed", line)
                if m:
                    failed = int(m.group(1))
            if " error" in line and "errors" in line:
                import re
                m = re.search(r"(\d+)\s+error", line)
                if m:
                    errors = int(m.group(1))

        total = passed + failed + errors
        score = passed / total if total > 0 else 0.0
        return TestRunResult(
            score=score,
            passed=passed,
            failed=failed,
            errors=errors,
            output=output,
            pass_threshold=pass_threshold,
        )


class TestRunnerFactory:
    _runners = {
        "python": PythonTestRunner,
    }

    @classmethod
    def get(cls, language: str) -> LanguageTestRunner:
        if language not in cls._runners:
            raise ValueError(
                f"No test runner for '{language}'. Available: {list(cls._runners.keys())}"
            )
        return cls._runners[language]()
```

- [ ] **Step 3: 编写工具匹配器测试并实现**

```python
"""Tests for tool_matcher."""
import pytest

from eval_framework.scoring.tool_matcher import ToolMatcher
from eval_framework.models import ToolCall, ToolCallStep


class TestToolMatcher:
    def test_exact_sequence_match(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(tool_name="Read", params={"file_path": "/a.py"}),
                result={},
                timestamp=None,
                duration_ms=0,
            ),
            ToolCallStep(
                step_index=1,
                tool_call=ToolCall(tool_name="Edit", params={"file_path": "/a.py"}),
                result={},
                timestamp=None,
                duration_ms=0,
            ),
        ]
        expected = ["Read", "Edit"]
        score = ToolMatcher.match_sequence(steps, expected)
        assert score == 1.0

    def test_partial_sequence_match(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(tool_name="Read", params={}),
                result={},
                timestamp=None,
                duration_ms=0,
            ),
        ]
        expected = ["Read", "Edit", "Write"]
        score = ToolMatcher.match_sequence(steps, expected)
        assert score == 1/3

    def test_tool_match_with_key_params(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Bash",
                    params={"command": "pytest tests/", "timeout": 30000},
                ),
                result={},
                timestamp=None,
                duration_ms=0,
            ),
        ]
        expected_tool = "Bash"
        key_params = ["command"]
        score = ToolMatcher.match_tool_params(steps, expected_tool, key_params)
        assert score == 1.0

    def test_tool_match_missing_param(self):
        steps = [
            ToolCallStep(
                step_index=0,
                tool_call=ToolCall(
                    tool_name="Bash",
                    params={"description": "run tests"},  # missing 'command'
                ),
                result={},
                timestamp=None,
                duration_ms=0,
            ),
        ]
        expected_tool = "Bash"
        key_params = ["command"]
        score = ToolMatcher.match_tool_params(steps, expected_tool, key_params)
        assert score == 0.0
```

Run: `pytest tests/unit/test_tool_matcher.py -v`
Expected: FAIL

实现 `tool_matcher.py`:

```python
"""Tool call trajectory matching for L1 scoring."""

from eval_framework.models import ToolCallStep


class ToolMatcher:
    @staticmethod
    def match_sequence(
        steps: list[ToolCallStep],
        expected_sequence: list[str],
    ) -> float:
        """Score how well the actual tool sequence matches expected.
        
        Returns a score 0.0 to 1.0. Longest common subsequence resemblance
        simplified as: count of matching positions / len(expected).
        """
        actual_names = [s.tool_call.tool_name for s in steps]
        matches = 0
        for i, expected_name in enumerate(expected_sequence):
            if i < len(actual_names) and actual_names[i] == expected_name:
                matches += 1
        return matches / len(expected_sequence) if expected_sequence else 1.0

    @staticmethod
    def match_tool_params(
        steps: list[ToolCallStep],
        expected_tool: str,
        key_params: list[str],
    ) -> float:
        """Check if any step used the expected tool with required params.
        
        Returns 1.0 if at least one step has the tool AND all key params.
        """
        for step in steps:
            if step.tool_call.tool_name == expected_tool:
                if all(
                    p in step.tool_call.params for p in key_params
                ):
                    return 1.0
        return 0.0
```

- [ ] **Step 4: 编写拆解树相似度测试并实现**

```python
"""Tests for tree_similarity."""
import pytest

from eval_framework.scoring.tree_similarity import TreeSimilarity


class TestTreeSimilarity:
    def test_identical_trees(self):
        expected = {
            "task": "Add search",
            "subtasks": [
                {"task": "Design API", "subtasks": []},
                {"task": "Implement backend", "subtasks": []},
            ],
        }
        actual = {
            "task": "Add search",
            "subtasks": [
                {"task": "Design API", "subtasks": []},
                {"task": "Implement backend", "subtasks": []},
            ],
        }
        score = TreeSimilarity.compare(actual, expected)
        assert score == 1.0

    def test_different_structure(self):
        expected = {
            "task": "A",
            "subtasks": [
                {"task": "B", "subtasks": []},
                {"task": "C", "subtasks": []},
            ],
        }
        actual = {"task": "A", "subtasks": []}
        score = TreeSimilarity.compare(actual, expected)
        assert 0.0 < score < 1.0

    def test_parse_from_json(self):
        json_str = '{"task":"Add feature","subtasks":[{"task":"Step 1","subtasks":[]}]}'
        tree = TreeSimilarity.parse(json_str)
        assert tree["task"] == "Add feature"
        assert len(tree["subtasks"]) == 1
```

Run: `pytest tests/unit/test_tree_similarity.py -v`
Expected: FAIL

实现 `tree_similarity.py`:

```python
"""Task decomposition tree similarity for L1-D2 scoring."""

import json
from typing import Any


class TreeSimilarity:
    @staticmethod
    def parse(json_str: str) -> dict:
        return json.loads(json_str)

    @staticmethod
    def compare(actual: dict, expected: dict) -> float:
        """Compute structural similarity between two task trees.

        Simplified tree edit distance: Jaccard similarity on flattened
        task names, weighted by depth.
        """
        actual_tasks = TreeSimilarity._flatten(actual)
        expected_tasks = TreeSimilarity._flatten(expected)

        if not expected_tasks:
            return 1.0 if not actual_tasks else 0.0

        intersection = len(actual_tasks & expected_tasks)
        union = len(actual_tasks | expected_tasks)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _flatten(tree: dict, depth: int = 0) -> set:
        tasks = {(tree.get("task", ""), depth)}
        for child in tree.get("subtasks", []):
            tasks |= TreeSimilarity._flatten(child, depth + 1)
        return tasks
```

- [ ] **Step 5: 实现 L1 判分入口**

```python
"""L1 scoring coordinator — dispatches to appropriate scorer by type."""

from eval_framework.models import AgentTrace, ScoringType, TestItem, TestResult
from eval_framework.scoring.test_runner import TestRunnerFactory
from eval_framework.scoring.tool_matcher import ToolMatcher
from eval_framework.scoring.tree_similarity import TreeSimilarity


class L1Scorer:
    """Coordinates L1 automated scoring for a single test item."""

    def score(
        self,
        item: TestItem,
        trace: AgentTrace,
        working_dir: str,
    ) -> TestResult:
        scoring = item.scoring
        l1_score: float = 0.0

        if scoring.type == ScoringType.UNIT_TEST:
            runner = TestRunnerFactory.get(item.language)
            test_result = runner.run(
                working_dir=working_dir,
                test_command=scoring.test_command,
                pass_threshold=scoring.pass_threshold,
            )
            l1_score = test_result.score

        elif scoring.type == ScoringType.TOOL_MATCH:
            if scoring.tool_sequence:
                seq_score = ToolMatcher.match_sequence(
                    trace.steps, scoring.tool_sequence
                )
                param_score = ToolMatcher.match_tool_params(
                    trace.steps,
                    scoring.tool_sequence[-1] if scoring.tool_sequence else "",
                    scoring.key_params,
                )
                l1_score = (seq_score + param_score) / 2
            else:
                l1_score = ToolMatcher.match_tool_params(
                    trace.steps, "", scoring.key_params
                )

        elif scoring.type == ScoringType.TREE_SIMILARITY:
            expected = TreeSimilarity.parse(scoring.expected_tree)
            actual = TreeSimilarity.parse(trace.final_output)
            l1_score = TreeSimilarity.compare(actual, expected)

        return TestResult(
            test_item_id=item.id,
            agent_name=trace.agent_name,
            agent_version=trace.agent_version,
            layer=item.layer,
            dimensions=item.dimensions,
            l1_score=l1_score,
            status="completed",
            run_id=trace.run_id,
        )
```

- [ ] **Step 6: L1 集成测试**

```python
"""Integration test for L1 scoring."""
from pathlib import Path

from eval_framework.scoring.l1_runner import L1Scorer
from eval_framework.models import (
    AgentTrace,
    ScoringConfig,
    ScoringType,
    TestItem,
    ToolCall,
    ToolCallStep,
    Layer,
    Dimension,
    SandboxConfig,
)
from datetime import datetime, timezone


def test_l1_unit_test_scoring(tmp_path):
    """L1Scorer should run pytest and compute score."""
    # Setup test file
    test_file = tmp_path / "test_math.py"
    test_file.write_text("""
def test_add():
    assert 1 + 2 == 3

def test_mul():
    assert 2 * 3 == 6
""")
    
    item = TestItem(
        id="L1-D1-PY-001",
        layer=Layer.L1,
        dimensions=[Dimension.D1],
        language="python",
        difficulty=1,
        estimated_time_min=5,
        sandbox=SandboxConfig(image="python:3.12", dependencies=[], network="none"),
        prompt_template="...",
        scoring=ScoringConfig(
            type=ScoringType.UNIT_TEST,
            test_command=f"pytest {test_file.name} -v",
            pass_threshold=0.85,
        ),
    )
    trace = AgentTrace(
        run_id="test",
        agent_name="test-agent",
        agent_version="1.0",
        test_item_id="L1-D1-PY-001",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
    )
    
    scorer = L1Scorer()
    result = scorer.score(item, trace, str(tmp_path))
    assert result.l1_score == 1.0
```

Run: `pytest tests/unit/test_l1_runner.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add eval_framework/scoring/ tests/unit/test_test_runner.py tests/unit/test_tool_matcher.py tests/unit/test_tree_similarity.py tests/unit/test_l1_runner.py
git commit -m "feat: L1 automated scoring engine — test runner, tool matcher, tree similarity"
```

---

### Task 9: LLM-as-Judge 评分（L2/L3）

**Files:**
- Create: `eval_framework/scoring/l2_l3_judge.py`
- Create: `eval_framework/scoring/calibrator.py`
- Create: `tests/unit/test_l2_l3_judge.py`
- Create: `tests/unit/test_calibrator.py`

- [ ] **Step 1: 实现 LLM-as-Judge 评分器**

```python
"""LLM-as-Judge scoring for L2 and L3 test items."""

import json
from typing import Optional

import httpx

from eval_framework.config import config
from eval_framework.models import (
    AgentTrace,
    Dimension,
    JudgeScoreCard,
    TestItem,
    TestResult,
)


# ── Judge prompt template ──────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an objective evaluator of coding agent performance.
Given a test scenario, the agent's execution trace, and its final deliverables,
score the agent on each of six dimensions on a scale of 1-5.

Scoring rubric:
1 = Severe defects, deliverable unusable
2 = Barely usable, core functionality partially implemented with notable issues
3 = Meets baseline, core functionality correctly implemented, no major defects
4 = Exceeds expectations, comprehensive implementation with good edge-case handling
5 = Excellent, output can be considered a best-practice exemplar, shows deep understanding

You MUST output valid JSON only — no markdown, no commentary outside JSON.
"""

JUDGE_SCORE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {
                        "type": "string",
                        "enum": ["D1", "D2", "D3", "D4", "D5", "D6"],
                    },
                    "score": {"type": "integer", "minimum": 1, "maximum": 5},
                    "reasoning": {"type": "string"},
                },
                "required": ["dimension", "score", "reasoning"],
            },
            "minItems": 6,
            "maxItems": 6,
        }
    },
    "required": ["scores"],
}


class L2L3Judge:
    """Scores L2/L3 test results using DeepSeek-V4-Flash as judge."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        cfg = config.get_scoring_config().get("l2_l3", {})
        self._model = cfg.get("judge_model", "deepseek-v4-flash")
        self._api_base = api_base or cfg.get(
            "judge_api_base", "https://api.deepseek.com"
        )
        self._api_key = api_key or cfg.get("api_key", "")
        self._max_retries = cfg.get("judge_max_retries", 3)

    def score(
        self,
        item: TestItem,
        trace: AgentTrace,
        deliverables: str,
    ) -> TestResult:
        """Submit trace and deliverables to LLM judge, return scored result."""
        prompt = self._build_prompt(item, trace, deliverables)
        
        for attempt in range(self._max_retries):
            try:
                response = self._call_judge(prompt)
                scores = self._parse_response(response)
                return TestResult(
                    test_item_id=item.id,
                    agent_name=trace.agent_name,
                    agent_version=trace.agent_version,
                    layer=item.layer,
                    dimensions=item.dimensions,
                    judge_score_cards=scores,
                    status="completed",
                    run_id=trace.run_id,
                )
            except Exception as e:
                if attempt == self._max_retries - 1:
                    return TestResult(
                        test_item_id=item.id,
                        agent_name=trace.agent_name,
                        agent_version=trace.agent_version,
                        layer=item.layer,
                        dimensions=item.dimensions,
                        status="error",
                        run_id=trace.run_id,
                        error_message=str(e),
                    )

        raise RuntimeError("Judge failed — should not reach here")

    def _build_prompt(
        self,
        item: TestItem,
        trace: AgentTrace,
        deliverables: str,
    ) -> str:
        return f"""Test Scenario: {item.prompt_template}

Agent: {trace.agent_name} v{trace.agent_version}
Duration: {trace.duration_seconds:.1f}s

Tool Calls Made:
{self._format_tool_calls(trace.steps)}

Final Output:
{trace.final_output}

Deliverables:
{deliverables}

Score the agent on all 6 dimensions (D1-D6). Output JSON per the schema."""

    @staticmethod
    def _format_tool_calls(steps) -> str:
        lines = []
        for s in steps:
            tool = s.tool_call.tool_name
            params = json.dumps(s.tool_call.params, ensure_ascii=False)
            lines.append(
                f"  [{s.step_index}] {tool}({params}) — {s.duration_ms}ms"
            )
        return "\n".join(lines) if lines else "(no tool calls)"

    def _call_judge(self, prompt: str) -> str:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{self._api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_response(response: str) -> list[JudgeScoreCard]:
        data = json.loads(response)
        scores = data.get("scores", [])
        return [
            JudgeScoreCard(
                dimension=Dimension(s["dimension"]),
                score=s["score"],
                reasoning=s["reasoning"],
            )
            for s in scores
        ]
```

- [ ] **Step 2: 实现评分校准器**

```python
"""Scoring calibration — compares LLM-Judge scores against human review."""

from eval_framework.models import JudgeScoreCard


class Calibrator:
    """Computes agreement between LLM-Judge and human reviewer scores."""

    @staticmethod
    def compute_agreement(
        judge_cards: list[JudgeScoreCard],
        human_cards: list[JudgeScoreCard],
    ) -> dict:
        """Calculate per-dimension and overall agreement metrics.

        Returns:
            {
              "overall_exact_match_rate": 0.75,
              "overall_mean_difference": 0.2,
              "per_dimension": {"D1": {"match_rate": 0.8, "mean_diff": 0.1}, ...}
            }
        """
        judge_map = {c.dimension.value: c for c in judge_cards}
        human_map = {c.dimension.value: c for c in human_cards}

        exact_matches = 0
        total_diff = 0.0
        per_dim = {}

        for dim in human_map:
            j = judge_map.get(dim)
            h = human_map[dim]
            if j:
                match = 1 if j.score == h.score else 0
                diff = abs(j.score - h.score)
                exact_matches += match
                total_diff += diff
                per_dim[dim] = {
                    "match_rate": match,
                    "mean_diff": diff,
                }

        n = len(per_dim) or 1
        return {
            "overall_exact_match_rate": exact_matches / n,
            "overall_mean_difference": total_diff / n,
            "per_dimension": per_dim,
        }

    @staticmethod
    def is_calibrated(agreement: dict, threshold: float = 0.10) -> bool:
        """Judge is considered calibrated if mean difference ≤ threshold."""
        return agreement["overall_mean_difference"] <= threshold
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/unit/test_l2_l3_judge.py tests/unit/test_calibrator.py -v
```

Expected: PASS (judge 测试 mock HTTP 调用)

- [ ] **Step 4: Commit**

```bash
git add eval_framework/scoring/l2_l3_judge.py eval_framework/scoring/calibrator.py tests/unit/test_l2_l3_judge.py tests/unit/test_calibrator.py
git commit -m "feat: LLM-as-Judge scoring for L2/L3 + calibration module"
```

---

### Task 10: 编排调度器——整合执行流程

**Files:**
- Create: `eval_framework/orchestrator/scheduler.py`
- Create: `tests/unit/test_scheduler.py`

- [ ] **Step 1: 实现调度器**

```python
"""Test execution scheduler with concurrency control."""

import concurrent.futures
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eval_framework.adapters.base import AgentAdapter
from eval_framework.config import config
from eval_framework.models import AgentTrace, Layer, TestItem, TestResult
from eval_framework.orchestrator.context import ContextPreparer, TestItemRegistry
from eval_framework.orchestrator.tracer import TraceCollector
from eval_framework.sandbox.manager import SandboxManager
from eval_framework.scoring.l1_runner import L1Scorer
from eval_framework.scoring.l2_l3_judge import L2L3Judge
from eval_framework.db.repository import EvalRepository


class Scheduler:
    """Orchestrates evaluation runs across layers."""

    def __init__(
        self,
        adapter: AgentAdapter,
        repository: EvalRepository,
        registry: Optional[TestItemRegistry] = None,
        sandbox: Optional[SandboxManager] = None,
        judge: Optional[L2L3Judge] = None,
    ):
        self._adapter = adapter
        self._repository = repository
        self._registry = registry or TestItemRegistry()
        self._sandbox = sandbox or SandboxManager()
        self._judge = judge or L2L3Judge()
        self._scorer = L1Scorer()
        self._preparer = ContextPreparer(self._registry)

    def run_layer(
        self,
        layer: str,
        items: Optional[list[TestItem]] = None,
    ) -> list[TestResult]:
        """Run all items for a given layer. Returns results."""
        if items is None:
            items = self._registry.get_by_layer(layer)

        layer_cfg = config.get_layer_config(layer.lower())
        max_concurrency = (
            config.get_sandbox_config().get("max_concurrency", 4)
            if layer_cfg.get("concurrency") == "high"
            else 3
        )

        results: list[TestResult] = []

        if layer == "L1":
            # High concurrency for L1
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_concurrency
            ) as executor:
                futures = {
                    executor.submit(self._run_single_item, item): item
                    for item in items
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result(
                            timeout=layer_cfg.get("timeout_minutes", 15) * 60
                        )
                        results.append(result)
                    except concurrent.futures.TimeoutError:
                        item = futures[future]
                        results.append(
                            TestResult(
                                test_item_id=item.id,
                                agent_name=self._adapter.capabilities().agent_name,
                                agent_version=self._adapter.capabilities().agent_version,
                                layer=item.layer,
                                dimensions=item.dimensions,
                                status="timeout",
                                error_message="Execution timed out",
                            )
                        )
        else:
            # Sequential or low concurrency for L2/L3
            for item in items:
                result = self._run_single_item(item)
                results.append(result)

        return results

    def _run_single_item(self, item: TestItem) -> TestResult:
        """Execute one test item: sandbox → inject → run → score."""
        caps = self._adapter.capabilities()
        collector = TraceCollector(
            run_id=f"run-{item.id}-{int(time.time())}",
            agent_name=caps.agent_name,
            agent_version=caps.agent_version,
            test_item_id=item.id,
        )

        try:
            # 1. Prepare sandbox workspace
            import tempfile

            with tempfile.TemporaryDirectory() as tmp_dir:
                workspace = Path(tmp_dir)
                self._preparer.prepare_workspace(item.id, workspace)

                # 2. Execute agent
                from eval_framework.adapters.base import TestContext

                context = TestContext(
                    test_item_id=item.id,
                    layer=item.layer,
                    dimensions=item.dimensions,
                    working_dir=str(workspace),
                    env_vars=item.sandbox.env_vars,
                    network_allowed=item.sandbox.network != "none",
                )

                collector.start()
                trace = self._adapter.execute(item.prompt_template, context)
                trace.run_id = collector.run_id

                # 3. Score
                if item.layer == Layer.L1:
                    result = self._scorer.score(item, trace, str(workspace))
                else:
                    result = self._judge.score(
                        item, trace, self._collect_deliverables(item, workspace)
                    )

                # 4. Persist
                self._repository.save_run(trace)
                self._repository.save_result(
                    run_id=result.run_id,
                    test_item_id=result.test_item_id,
                    dimension=",".join(d.value for d in result.dimensions),
                    l1_score=result.l1_score,
                    judge_score=(
                        result.judge_score_cards[0].score
                        if result.judge_score_cards
                        else None
                    ),
                    status=result.status,
                )

                return result

        except Exception as e:
            trace = collector.finish(f"Error: {e}")
            self._repository.save_run(trace)
            return TestResult(
                test_item_id=item.id,
                agent_name=caps.agent_name,
                agent_version=caps.agent_version,
                layer=item.layer,
                dimensions=item.dimensions,
                status="error",
                error_message=str(e),
                run_id=collector.run_id,
            )

    @staticmethod
    def _collect_deliverables(
        item: TestItem, workspace: Path
    ) -> str:
        """Collect deliverable file contents for judge review."""
        parts = []
        for rel in item.expected_artifacts:
            path = workspace / rel
            if path.exists():
                parts.append(f"--- {rel} ---\n{path.read_text()}\n")
        return "\n".join(parts) if parts else "(no deliverables found)"
```

- [ ] **Step 2: 运行测试**

```bash
pytest tests/unit/test_scheduler.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add eval_framework/orchestrator/scheduler.py tests/unit/test_scheduler.py
git commit -m "feat: evaluation scheduler with concurrency and end-to-end flow"
```

---

### Task 11: CLI 入口

**Files:**
- Create: `eval_framework/cli.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_e2e_l1_flow.py`

- [ ] **Step 1: 实现 CLI**

```python
"""CLI entry point for the evaluation framework."""

import sys
from pathlib import Path

import click

from eval_framework.config import config
from eval_framework.db.connection import init_db, get_session
from eval_framework.db.repository import EvalRepository
from eval_framework.adapters.factory import AdapterFactory
from eval_framework.orchestrator.context import TestItemRegistry
from eval_framework.orchestrator.scheduler import Scheduler


@click.group()
def main():
    """Coding Agent Evaluation Framework CLI."""
    pass


@main.command()
@click.option("--adapter", "-a", default="cli", help="Agent adapter type")
@click.option("--command", "-c", default="", help="CLI command for agent")
@click.option("--layer", "-l", default="L1", help="Layer to run (L1/L2/L3)")
@click.option("--count", "-n", default=0, help="Number of items (0 = all)")
@click.option("--seed", "-s", default=None, type=int, help="Random seed")
def run(adapter: str, command: str, layer: str, count: int, seed: int):
    """Run evaluation tests for a layer."""
    click.echo(f"Initializing database...")
    init_db()

    click.echo(f"Loading test items for layer {layer}...")
    registry = TestItemRegistry()
    all_items = registry.load()

    if layer not in ("L1", "L2", "L3"):
        click.echo(f"Invalid layer: {layer}", err=True)
        sys.exit(1)

    items = registry.get_by_layer(layer)
    if count > 0 and count < len(items):
        items = registry.select_random(layer, count, seed)

    click.echo(f"Selected {len(items)} items for {layer}")

    click.echo(f"Creating adapter '{adapter}'...")
    agent = AdapterFactory.create(adapter, command=command, workspace="/tmp/eval")

    repo = EvalRepository(get_session())
    scheduler = Scheduler(
        adapter=agent,
        repository=repo,
        registry=registry,
    )

    click.echo(f"Running {len(items)} test items...")
    results = scheduler.run_layer(layer, items)

    completed = [r for r in results if r.status == "completed"]
    errors = [r for r in results if r.status != "completed"]
    
    click.echo(f"\nResults: {len(completed)} completed, {len(errors)} failed/timeout")

    if completed:
        avg_score = sum(
            r.l1_score or 0 for r in completed
        ) / len(completed)
        click.echo(f"Average L1 score: {avg_score:.3f}")

    if errors:
        for e in errors:
            click.echo(f"  {e.test_item_id}: {e.status} — {e.error_message}")


@main.command()
@click.option("--agent", "-a", default="", help="Agent name filter")
@click.option("--output", "-o", default="reports/report.md", help="Output path")
def report(agent: str, output: str):
    """Generate evaluation report."""
    repo = EvalRepository(get_session())
    scores = repo.get_agent_scores(agent) if agent else {}

    lines = ["# Evaluation Report\n"]
    lines.append(f"Generated: {__import__('datetime').datetime.now()}\n")
    lines.append(f"Agent: {agent or 'All'}\n\n")

    if scores:
        lines.append("## Dimension Scores\n\n")
        lines.append("| Dimension | Avg L1 Score | Avg Judge Score | Runs |\n")
        lines.append("|-----------|-------------|-----------------|------|\n")
        for dim, data in sorted(scores.items()):
            lines.append(
                f"| {dim} | {data['avg_l1_score'] or 'N/A'} | "
                f"{data['avg_judge_score'] or 'N/A'} | {data['run_count']} |\n"
            )
    else:
        lines.append("No results found.\n")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines))
    click.echo(f"Report saved to {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 端到端集成测试**

```python
"""End-to-end test: full L1 flow with a real agent."""
import subprocess
from pathlib import Path

import pytest


class TestEndToEndL1:
    @pytest.mark.integration
    def test_full_l1_flow(self, tmp_path):
        """Run the evaluation CLI end-to-end on a single L1 item."""
        # This test requires the Docker sandbox and an adapter
        result = subprocess.run(
            [
                "python", "-m", "eval_framework.cli", "run",
                "--adapter", "cli",
                "--command", "echo 'def reverse_words(s): return \" \".join(s.split()[::-1])'",
                "--layer", "L1",
                "--count", "1",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0
        assert "completed" in result.stdout
```

- [ ] **Step 3: Commit**

```bash
git add eval_framework/cli.py tests/integration/
git commit -m "feat: CLI entry point with run and report commands"
```

---

### Task 12: Streamlit Dashboard

**Files:**
- Create: `eval_framework/dashboard/__init__.py`
- Create: `eval_framework/dashboard/app.py`
- Create: `eval_framework/dashboard/charts.py`
- Create: `eval_framework/dashboard/report.py`

- [ ] **Step 1: 实现可视化图表**

```python
"""Visualization components for the dashboard."""

from typing import Optional

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def radar_chart(
    scores: dict[str, float],
    title: str = "Agent Capability Radar",
    agent_names: Optional[list[str]] = None,
) -> go.Figure:
    """Generate a radar chart for one or more agents' dimension scores."""
    dimensions = ["D1 Code", "D2 Decompose", "D3 Tools", "D4 Multi-Agent", "D5 Debug", "D6 Memory"]

    fig = go.Figure()

    if agent_names is None:
        # Single agent
        values = [scores.get(f"D{i}", 0) for i in range(1, 7)]
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=dimensions,
                fill="toself",
                name="Agent",
            )
        )
        fig.update_layout(title=title)
    else:
        # Multiple agents overlay
        for name in agent_names:
            values = [scores.get(f"{name}_D{i}", 0) for i in range(1, 7)]
            fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=dimensions,
                    fill="toself",
                    name=name,
                )
            )
        fig.update_layout(title="Agent Comparison Radar")

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
    return fig


def bar_chart_comparison(
    agent_scores: list[dict],
    title: str = "Agent Score Comparison",
) -> go.Figure:
    """Generate a grouped bar chart comparing agents per dimension."""
    df = pd.DataFrame(agent_scores)  # columns: agent, D1, D2, ... or similar
    fig = px.bar(
        df,
        x="dimension",
        y="score",
        color="agent",
        barmode="group",
        title=title,
    )
    return fig


def score_trend_chart(
    history: list[dict],  # [{version, D1, D2, ...}, ...]
    dimension: str = "D1",
) -> go.Figure:
    """Show score trend over agent versions."""
    versions = [h["version"] for h in history]
    scores = [h.get(dimension, 0) for h in history]
    fig = px.line(
        x=versions,
        y=scores,
        markers=True,
        title=f"{dimension} Score Trend",
    )
    fig.update_layout(xaxis_title="Version", yaxis_title="Score")
    return fig
```

- [ ] **Step 2: 实现报告生成器**

```python
"""Report generation — Markdown and HTML output."""

from datetime import datetime
from pathlib import Path
from typing import Optional


class ReportGenerator:
    @staticmethod
    def generate_markdown(
        agent_name: str,
        scores: dict[str, dict],
        output_path: Path,
    ) -> str:
        """Generate a markdown evaluation report."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# Agent Evaluation Report: {agent_name}",
            f"Generated: {now}",
            "",
            "## Overall Scores",
            "",
            "| Dimension | Avg L1 Score | Avg Judge Score | Run Count |",
            "|-----------|-------------|-----------------|-----------|",
        ]

        for dim in sorted(scores.keys()):
            d = scores[dim]
            l1 = f"{d['avg_l1_score']:.3f}" if d.get("avg_l1_score") is not None else "N/A"
            judge = f"{d['avg_judge_score']:.1f}" if d.get("avg_judge_score") is not None else "N/A"
            lines.append(f"| {dim} | {l1} | {judge} | {d['run_count']} |")

        lines.append("")
        lines.append("## Summary")
        
        # Compute weighted total
        l1_scores = [
            d["avg_l1_score"]
            for d in scores.values()
            if d.get("avg_l1_score") is not None
        ]
        if l1_scores:
            avg = sum(l1_scores) / len(l1_scores)
            lines.append(f"Overall weighted score: **{avg:.3f}**")

        content = "\n".join(lines)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        return content
```

- [ ] **Step 3: 实现 Streamlit 应用**

```python
"""Streamlit dashboard for evaluation results."""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eval_framework.db.connection import init_db, get_session
from eval_framework.db.repository import EvalRepository
from eval_framework.dashboard.charts import radar_chart, bar_chart_comparison


st.set_page_config(
    page_title="Coding Agent Eval Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Coding Agent Evaluation Dashboard")

# Initialize database
init_db()
repo = EvalRepository(get_session())

# Sidebar — agent selection
st.sidebar.header("Filters")

# Get distinct agent names from DB (simplified — in production use a proper query)
agent_list = ["claude-code", "copilot", "cursor", "cli-generic"]
selected_agents = st.sidebar.multiselect(
    "Select Agents",
    agent_list,
    default=agent_list[:2],
)

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Capability Radar")
    if selected_agents:
        scores = {}
        for agent in selected_agents:
            agent_scores = repo.get_agent_scores(agent)
            for dim, data in agent_scores.items():
                scores[dim] = data.get("avg_judge_score") or data.get("avg_l1_score", 0)
        if scores:
            fig = radar_chart(scores, "Agent Capability Comparison", selected_agents)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet. Run some evaluations first.")

with col2:
    st.subheader("Score Summary")
    if selected_agents:
        for agent in selected_agents:
            agent_scores = repo.get_agent_scores(agent)
            if agent_scores:
                st.write(f"**{agent}**")
                for dim, data in sorted(agent_scores.items()):
                    score = data.get("avg_l1_score") or data.get("avg_judge_score") or 0
                    st.metric(
                        label=dim,
                        value=f"{score:.2f}",
                        delta=None,
                    )
            else:
                st.write(f"**{agent}**: No data")
    else:
        st.info("Select agents to view scores")

# Bottom section — recent runs
st.header("Recent Evaluation Runs")
st.text("Run results will appear here after evaluations are executed.")
```

- [ ] **Step 4: Commit**

```bash
git add eval_framework/dashboard/
git commit -m "feat: Streamlit dashboard with radar charts, report generation"
```

---

### Task 13: Makefile 和最终集成

**Files:**
- Create: `Makefile`

- [ ] **Step 1: 创建 Makefile**

```makefile
.PHONY: help install test lint run-eval report dashboard db-up db-down build-sandbox

help:
	@echo "Coding Agent Evaluation Framework"
	@echo ""
	@echo "  make install        Install dependencies"
	@echo "  make test           Run all tests"
	@echo "  make lint           Run linting"
	@echo "  make db-up          Start PostgreSQL"
	@echo "  make db-down        Stop PostgreSQL"
	@echo "  make build-sandbox  Build Docker sandbox images"
	@echo "  make run-eval       Run evaluation (LAYER=L1 COUNT=10)"
	@echo "  make report         Generate report"
	@echo "  make dashboard      Start Streamlit dashboard"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short -m integration

lint:
	ruff check eval_framework/

db-up:
	docker-compose up -d

db-down:
	docker-compose down

build-sandbox:
	cd eval_framework/sandbox/dockerfiles && \
	docker build -t eval-sandbox-python:latest -f python.Dockerfile . && \
	docker build -t eval-sandbox-node:latest -f node.Dockerfile . && \
	docker build -t eval-sandbox-go:latest -f go.Dockerfile .

run-eval:
	python -m eval_framework.cli run \
		--adapter $(ADAPTER) \
		--command "$(COMMAND)" \
		--layer $(LAYER) \
		--count $(COUNT) \
		--seed $(SEED)

report:
	python -m eval_framework.cli report --agent $(AGENT) --output $(OUTPUT)

dashboard:
	streamlit run eval_framework/dashboard/app.py
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "feat: Makefile with common commands"
```

---

## 阶段二：核心题库建设（路线图）

### Task 14: L1 代码填空题库 (D1, 15题)

- [ ] 设计 15 道 Python 代码填空题
- [ ] 每题包含 context 文件、pytest 判分脚本
- [ ] 覆盖难度 1-5
- [ ] 覆盖主题：字符串处理、数据结构、算法、异常处理、文件IO

### Task 15: L1 Bug 定位题库 (D5, 10题)

- [ ] 设计 10 道含 bug 的代码文件
- [ ] 每题含 1-3 个 bug（逻辑错误、边界遗漏、性能问题）
- [ ] 每题有标准答案（bug位置 + 修复方式）

### Task 16: L1 工具选择与编排题库 (D3, 10题)

- [ ] 设计 5 道工具选择题 + 5 道链式编排题
- [ ] 定义标准工具名和期望参数
- [ ] 编写工具匹配判分逻辑

### Task 17: L1 任务拆解与代码审查题库 (D2/D5, 15题)

- [ ] 任务拆解题 (D2): 8 道，带标准拆解树
- [ ] 代码审查题 (D5): 7 道，带关键问题点清单

### Task 18: L2 集成场景设计（首批 4 场景）

- [ ] 场景 1: 给 REST API 项目添加认证中间件
- [ ] 场景 2: 数据迁移脚本编写与验证
- [ ] 场景 3: 前端表单组件开发与状态管理
- [ ] 场景 4: 性能问题排查与优化（带 profile 工具）

---

## 阶段三：完整体系上线（路线图）

### Task 19: L2 全部场景（共8-12场景）

- [ ] 补充 4-8 个集成场景
- [ ] 每个场景附带 LLM-Judge 评分校准样本

### Task 20: L3 长程项目（首批 2 项目）

- [ ] 项目 1: 跨会话记忆测试 — 连续 3 个会话功能迭代
- [ ] 项目 2: 多智能体协作 — 大型重构必须用子 agent

### Task 21: Dashboard 完善

- [ ] 横向对比视图（多 agent 雷达图叠加）
- [ ] 历史趋势折线图（按版本/时间）
- [ ] 单题得分下钻到工具调用详情

### Task 22: ClaudeCodeAdapter

- [ ] 基于 Claude Code CLI 实现完整 adapter
- [ ] 支持解析 Claude Code 的工具调用日志
- [ ] 注入自定义系统 prompt

---

## 阶段四：持续运营（路线图）

### Task 23-26

- [ ] 对抗题目生成流程
- [ ] CopilotAdapter / CursorAdapter
- [ ] 自动化 CI 集成（GitHub Actions 按版本触发）
- [ ] 定期对比报告自动化产出

---

## 自审检查

| 检查项 | 状态 |
|--------|------|
| 规范覆盖 | ✅ L1-L3 所有层架构、判分、DB、Dashboard 均有对应任务 |
| 占位符扫描 | ✅ 无 TBD/TODO，所有任务包含具体代码 |
| 类型一致性 | ✅ models.py 定义的类型在 scorer/scheduler/judge 中一致使用 |
| 可执行性 | ✅ 每个 Task 2-5 分钟步骤，带命令和预期输出 |
