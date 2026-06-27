# Agent Eval Framework

[![Tests](https://img.shields.io/badge/tests-48%2F48%20PASS-brightgreen)](https://github.com/yuHong-Cray/agent-eval-framework)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个用于深度评测 Coding Agent 的三层混合评估框架。支持对任意 AI 编程助手（CrayCode、Copilot、Cursor 等）进行**代码生成、任务拆解、工具调用、多智能体协作、审查调试、持续记忆**六个维度的可量化、可复现、可横向对比的标准化评测。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│              评测编排层 (Orchestrator + CLI)                   │
│                调度、并发、超时、重试、报告                      │
├─────────────────────────────────────────────────────────────┤
│     __________       __________       __________             │
│    │ CrayCode │    │ Copilot  │    │ Cursor   │  ...        │
│    │ Adapter  │    │ Adapter  │    │ Adapter  │             │
│    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│         └───────────────┼───────────────┘                   │
│                 统一 AgentAdapter 接口                       │
├─────────────────────────────────────────────────────────────┤
│   Docker 沙箱环境 (Python / Node.js / Go)                    │
│   隔离执行，文件系统快照，网络控制                              │
├───────────────────────┬─────────────────────────────────────┤
│  判分引擎 (Scoring)    │  结果存储 & Dashboard                 │
│  L1: 自动化判分        │  SQLite / PostgreSQL + SQLAlchemy     │
│  L2/L3: LLM-as-Judge  │  Streamlit 可视化                    │
└───────────────────────┴─────────────────────────────────────┘
```

### 三层评测体系

| 层级 | 题目数 | 时长 | 实际耗时 | 判分方式 | 重点维度 |
|------|--------|------|---------|---------|---------|
| **Layer 1** 原子能力基准 | 50题 | 5-15min/题 | ≈20-30min (并发4) | 自动化（单测+工具匹配+拆解树相似度） | D1代码生成, D3工具调用, D5审查调试 |
| **Layer 2** 集成场景测试 | 8题 | 30-60min/题 | ≈1-2h (串行) | LLM-as-Judge (DeepSeek-V4-Flash) | 全部6维融合作战 |
| **Layer 3** 长程项目测试 | 2项目×5会话 | 跨多会话 | ≈0.5-1h | LLM-as-Judge + 人工抽检 | D6记忆, D4多智能体, D2拆解 |

### 六大评测维度

| 编号 | 维度 | 说明 |
|------|------|------|
| **D1** | 代码生成 | 语法正确性、逻辑完备性、边界处理、代码风格 |
| **D2** | 任务拆解 | 拆解粒度、依赖识别、优先级排序 |
| **D3** | 工具调用 | 工具选择准确性、参数正确性、链式编排 |
| **D4** | 多智能体协作 | 子Agent分派合理性、结果整合、一致性校验 |
| **D5** | 审查/调试 | Bug发现率、根因定位、修复正确性 |
| **D6** | 持续记忆 | 跨会话上下文保持、偏好积累、错误不再犯 |

---

## 快速开始

### 环境要求

- Python 3.10+
- Docker（沙箱隔离执行，可选）
- PostgreSQL（可选，默认使用 SQLite）

### 安装

```bash
git clone https://github.com/yuHong-Cray/agent-eval-framework.git
cd agent-eval-framework

# 安装依赖
pip install -r requirements.txt
```

### 运行评测

```bash
# ── 一句话全量评测 ──────────────────────────────────────

# 快速模式（≈10分钟）— L1=10题 + L2=2场景
make full-eval

# 完整模式（≈2-4小时）— L1=50题 + L2=8场景 + L3=5会话
# 需要配置 EVAL_JUDGE_API_KEY
make full-eval-full

# ── 单层评测 ────────────────────────────────────────────

# L1: 原子能力基准 (50题, 并发4线程, ≈20-30min)
make run-eval ADAPTER=claude LAYER=L1 SEED=42

# L1: 挑10题快速验证
make run-eval ADAPTER=claude LAYER=L1 COUNT=10 SEED=42

# L2: 集成场景 (需要 API key)
make run-eval ADAPTER=claude LAYER=L2 COUNT=2 SEED=42

# L3: 长程项目 (需要 API key)
make run-eval ADAPTER=claude LAYER=L3

# 通用 CLI 适配器（无需安装任何 agent）
make run-eval ADAPTER=cli COMMAND="echo done" LAYER=L1 COUNT=5 SEED=42

# 清理旧数据重新测试
python -m eval_framework.cli reset
```

### 运行测试

```bash
# 运行全部 48 项单元测试
python -m pytest tests/ -v

# 生成覆盖率报告
python -m pytest tests/ --cov=eval_framework --cov-report=html
```

### 生成报告

```bash
# Markdown 报告
python -m eval_framework.cli report --agent craycode --output reports/report.md

# 全量评测会自动在 reports/<timestamp>/ 下生成报告和 JSON 汇总
```

### 启动 Dashboard

```bash
streamlit run eval_framework/dashboard/app.py
```

浏览器访问 `http://localhost:8501`，可查看：
- 🔴 **六维雷达图**（多 Agent 叠加对比）
- 📊 **分组柱状图**（维度得分对比）
- 📋 **得分下钻**（逐题明细 + 行为轨迹）
- 📈 **历史趋势**（版本迭代得分变化）

---

## 全量评测流程

```
┌──────────────────────────────────────────────────┐
│ 🧹 Step 0  Reset DB     清空上次数据               │
├──────────────────────────────────────────────────┤
│ 🔬 Step 1  Layer 1      原子能力基准              │
│            50题 并发4   ≈20-30min                 │
│            自动判分（单测/工具匹配/拆解树）         │
├──────────────────────────────────────────────────┤
│ 🧪 Step 2  Layer 2      集成场景测试              │
│            8个场景 串行  ≈1-2h                    │
│            LLM-as-Judge 6维评分                   │
├──────────────────────────────────────────────────┤
│ 🏗️ Step 3  Layer 3      长程项目测试              │
│            5个会话 串行  ≈0.5-1h                  │
│            跨会话记忆+多Agent协作                  │
├──────────────────────────────────────────────────┤
│ 📊 Step 4  Report       报告生成                  │
│            Markdown + JSON汇总                    │
│            reports/<timestamp>/                   │
└──────────────────────────────────────────────────┘
```

```bash
# 完整流程（一条命令）
bash run_full_eval.sh --adapter claude

# 或自定义
bash run_full_eval.sh --adapter cray --skip-l3 --l1-count 30
```

---

## 项目结构

```
agent-eval-framework/
├── eval_framework/                # 核心框架
│   ├── config.py                  # YAML + 环境变量配置系统
│   ├── models.py                  # Pydantic 数据模型（6维×3层）
│   ├── cli.py                     # Click CLI 入口 (run/report/reset)
│   │
│   ├── orchestrator/              # 评测编排层
│   │   ├── scheduler.py           # 并发调度 + 端到端执行流程
│   │   ├── tracer.py              # Agent 行为轨迹捕获
│   │   └── context.py             # 测题加载 + 沙箱上下文注入
│   │
│   ├── adapters/                  # Agent 接口适配层
│   │   ├── base.py                # AgentAdapter 抽象基类
│   │   ├── cli_generic.py         # 通用 CLI 适配器
│   │   ├── cray_code.py           # CrayCode 适配器（cray --input + -v 解析）
│   │   └── factory.py             # 适配器工厂 + 注册表
│   │
│   ├── sandbox/                   # Docker 沙箱环境
│   │   ├── manager.py             # 容器生命周期管理（lazy init）
│   │   ├── snapshot.py            # 文件系统快照对比
│   │   └── dockerfiles/           # python / node / go 三语言镜像
│   │
│   ├── scoring/                   # 判分引擎
│   │   ├── l1_runner.py           # L1 判分编排
│   │   ├── test_runner.py         # 多语言测试运行器（pytest/jest/go test）
│   │   ├── tool_matcher.py        # 工具调用轨迹匹配
│   │   ├── tree_similarity.py     # 任务拆解树编辑距离
│   │   ├── l2_l3_judge.py         # LLM-as-Judge（DeepSeek-V4-Flash）
│   │   └── calibrator.py          # 人工抽检校准
│   │
│   ├── db/                        # 数据持久化
│   │   ├── connection.py          # 数据库连接管理 (SQLite WAL + 线程安全)
│   │   ├── models.py              # SQLAlchemy ORM
│   │   └── repository.py          # CRUD + 聚合查询 (写入锁)
│   │
│   └── dashboard/                 # 可视化面板
│       ├── app.py                 # Streamlit 应用 (自动发现 DB 中 agent)
│       ├── charts.py              # 雷达图 / 柱状图 / 趋势折线
│       └── report.py              # Markdown 报告生成
│
├── test_items/                    # 测评题库
│   ├── registry.json              # 测题注册表（63题）
│   ├── l1/                        # Layer 1 — 50道原子题
│   │   ├── d1_code_fill/          # 15题 代码填空 (D1, 难度1-5)
│   │   ├── d2_decompose/          #  8题 任务拆解 (D2, 难度1-5)
│   │   ├── d3_tool_select/        #  5题 工具选择 (D3, 难度1-3)
│   │   ├── d3_tool_chain/         #  5题 链式编排 (D3, 难度3-5)
│   │   ├── d5_bug_fix/            # 10题 Bug定位 (D5, 难度1-5)
│   │   └── d5_code_review/        #  7题 代码审查 (D5, 难度1-5)
│   ├── l2/                        # Layer 2 — 8个集成场景
│   │   ├── L2-SCENARIO-001        # JWT Auth 中间件
│   │   ├── L2-SCENARIO-002        # 数据迁移脚本 + 验证
│   │   ├── L2-SCENARIO-003        # React 注册表单组件
│   │   ├── L2-SCENARIO-004        # API 性能优化
│   │   ├── L2-SCENARIO-005        # CLI 工具开发
│   │   ├── L2-SCENARIO-006        # Web 爬虫 + 缓存
│   │   ├── L2-SCENARIO-007        # 数据库迁移管理器
│   │   └── L2-SCENARIO-008        # 令牌桶限流器
│   └── l3/                        # Layer 3 — 2个长程项目
│       ├── L3-PROJECT-001         # 跨3会话电商API迭代（记忆导向）
│       └── L3-PROJECT-002         # 跨2会话多Agent重构（协作导向）
│
├── tests/                         # 框架测试
│   ├── unit/                      # 48项单元测试
│   └── integration/               # 端到端集成测试
│
├── scripts/                       # 题库生成脚本
├── run_full_eval.sh               # 全量评测一键脚本
├── config.yaml                    # 默认全局配置
├── requirements.txt               # Python 依赖
├── docker-compose.yml             # PostgreSQL 本地开发
└── Makefile                       # 常用命令
```

---

## 适配器使用

### 已注册适配器

| 别名 | 适配器 | 说明 |
|------|--------|------|
| `claude` | CrayCodeAdapter | 默认，调用 `cray` CLI |
| `craycode` | CrayCodeAdapter | 同上 |
| `cray` | CrayCodeAdapter | 同上 |
| `cli` | CLIAdapter | 通用命令行，stdin 输入 |

### CLIAdapter（通用命令行）

适用于任何可通过 CLI 调用并接受 stdin 输入的 Agent：

```bash
python -m eval_framework.cli run \
    --adapter cli \
    --command "my-agent run --workspace /tmp/eval" \
    --layer L1 --count 5
```

### CrayCodeAdapter

内建适配器，已自动注册。调用 `cray` CLI 命令，支持：

- **非交互模式**：`cray --input "<prompt>" -d <dir> -v`
- **工具调用追踪**：解析 `[Cray] [Permission] ... allowing "tool"` 日志行
- **安全命令构建**：`shlex.quote()` 防止注入
- **终端输出提取**：过滤框架日志，仅保留 agent 最终回复

```bash
# 直接使用
make run-eval ADAPTER=claude LAYER=L1 COUNT=10 SEED=42
```

### 添加新适配器

```python
from eval_framework.adapters.base import AgentAdapter
from eval_framework.adapters.factory import AdapterFactory

class MyAdapter(AgentAdapter):
    def execute(self, prompt, context):
        # 实现：发送 prompt，返回 AgentTrace
        ...

    def capabilities(self):
        return AgentCapabilities(
            agent_name="my-agent",
            supported_tools=["read", "write", "edit"],
            ...
        )

AdapterFactory.register("my-agent", MyAdapter)
```

---

## 评分体系

### 总评分公式

```
最终得分 = L1 × 0.40 + L2 × 0.40 + L3 × 0.20

L1 = Σ(各题型得分 × 题型权重) / 总题数
L2 = Σ(各场景六维评分 × 5) / 场景数
L3 = Σ(各项目评分) / 项目数
```

### L1 题型权重

| 题型 | 权重 | 判分方式 | 满分条件 |
|------|------|---------|---------|
| 代码填空 | 0.25 | 单元测试通过率 | ≥ 85% pass |
| Bug 定位 | 0.20 | Bug检出率 + 修复正确率 | 100%检出, ≥80%修复 |
| 工具选择 | 0.15 | 工具名+参数精确匹配 | 精确匹配 |
| 子任务拆解 | 0.15 | 拆解树编辑距离 | 距离 ≤ 阈值 |
| 代码审查 | 0.15 | 关键问题点命中率 | ≥ 70% 命中 |
| 链式工具编排 | 0.10 | 工具序列正确性 | 完全匹配 |

### L2/L3 评分维度（1-5分制）

| 分数 | 等级 | 说明 |
|------|------|------|
| 1 | 未达预期 | 严重缺陷，交付物不可用 |
| 2 | 勉强可用 | 核心功能部分实现，存在明显问题 |
| 3 | 达到基准 | 核心功能正确实现，无严重缺陷 |
| 4 | 超出预期 | 实现全面，边界处理得当 |
| 5 | 卓越 | 最佳实践范例，展现深度理解 |

---

## 配置

通过 `config.yaml` 或环境变量覆盖：

```yaml
# config.yaml
sandbox:
  network_mode: "none"        # none | whitelist | open
  max_concurrency: 4
  timeout_default: 900        # 默认超时 15分钟

scoring:
  l1:
    pass_threshold: 0.85
  l2_l3:
    judge_model: "deepseek-v4-flash"    # LLM-as-Judge 模型
    judge_api_base: "https://api.deepseek.com"
    judge_max_retries: 3

layers:
  l1:
    concurrency: "high"       # 高并发 (4线程)
    retry: 1
    timeout_minutes: 15
  l2:
    concurrency: "low"        # 串行
    retry: 0
    timeout_minutes: 60
  l3:
    concurrency: "serial"     # 串行
    retry: 0
    timeout_minutes: 120

database:
  url: "sqlite:///eval_framework.db"    # 本地 SQLite
  # url: "postgresql://eval:eval@localhost:5432/eval_framework"  # 生产用 PostgreSQL
```

环境变量覆盖：

```bash
export EVAL_DATABASE_URL="postgresql://user:pass@host:5432/eval"
export EVAL_JUDGE_API_KEY="sk-xxx"      # L2/L3 评测必需
export EVAL_SANDBOX_MAX_CONCURRENCY=8
```

---

## 添加新测题

每道题包含 `metadata.json` + context 文件 + judge 文件：

```
test_items/l1/d1_code_fill/L1-D1-PY-016/
├── metadata.json          # 题目元数据
├── context/
│   └── main.py            # 种子代码（agent 在此基础上修改）
└── judge/
    └── test_main.py       # 判分测试
```

然后在 `test_items/registry.json` 注册：

```json
{
  "items": [
    { "id": "L1-D1-PY-016", "path": "l1/d1_code_fill/L1-D1-PY-016", "enabled": true }
  ]
}
```

---

## 横向对比流程

1. **统一题目集**：同一版本的 `registry.json`，同一 `random_seed`
2. **统一环境**：同一 Docker 镜像，同一网络条件
3. **72小时窗口**：所有待测 Agent 在同一轮评测周期内完成
4. **生成对比报告**：

```
┌─────────────────────────────────────────────────────┐
│               Agent 横向对比报告 v2026.07             │
├─────────────────────────────────────────────────────┤
│  1. CrayCode   87.3  (代码:91, 拆解:85, 工具:89)     │
│  2. Copilot    82.1  (代码:79, 拆解:88, 工具:81)     │
│  3. Cursor     76.5  (...)                          │
└─────────────────────────────────────────────────────┘
```

---

## CLI 命令

```bash
python -m eval_framework.cli --help

# 子命令
python -m eval_framework.cli run     # 运行评测
python -m eval_framework.cli report  # 生成报告
python -m eval_framework.cli reset   # 清空所有评测数据

# 常用选项
python -m eval_framework.cli run --help
  --adapter TEXT   Agent 适配器 [cli, claude, craycode, cray]
  --layer TEXT     评测层级 [L1, L2, L3]
  --count INTEGER  题目数量 (0=全部)
  --seed INTEGER   随机种子
```

---

## 路线图

- [x] 阶段一：基础设施搭建（配置、模型、沙箱、适配器、DB、判分、Dashboard）
- [x] 阶段二：核心题库建设（50 L1 + 8 L2 + 5 L3）
- [x] 阶段三：完整体系上线（CrayCodeAdapter、并发修复、全量脚本）
- [ ] 阶段四：持续运营
  - [ ] 对抗题目生成流程
  - [ ] CopilotAdapter / CursorAdapter
  - [ ] GitHub Actions CI 自动触发
  - [ ] 定期横向对比报告自动化

---

## License

MIT © 2026
