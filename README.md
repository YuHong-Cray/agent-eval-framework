# Agent Eval Framework

[![Tests](https://img.shields.io/badge/tests-56%2F56%20PASS-brightgreen)](https://github.com/yuHong-Cray/agent-eval-framework)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个用于深度评测 Coding Agent 的三层混合评估框架。支持对任意 AI 编程助手（CrayCode、Claude Code、Copilot、Cursor 等）进行**代码生成、任务拆解、工具调用、多智能体协作、审查调试、持续记忆**六个维度的可量化、可复现、可横向对比的标准化评测。

最终输出 **X.X / 10 分** 综合评分，所有 Agent 共用同一套评分标准。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│              评测编排层 (Orchestrator + CLI)                   │
│                调度、超时、结果聚合、报告生成                    │
├─────────────────────────────────────────────────────────────┤
│     __________       __________       __________             │
│    │ Claude   │    │ CrayCode │    │ Copilot  │  ...        │
│    │ Adapter  │    │ Adapter  │    │ Adapter  │             │
│    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│         └───────────────┼───────────────┘                   │
│                 统一 AgentAdapter 接口                       │
├─────────────────────────────────────────────────────────────┤
│  判分引擎 (Scoring)          │  结果存储 & Dashboard          │
│  L1: 自动化判分              │  SQLite + SQLAlchemy          │
│    - unit_test (pytest)      │  reports/<ts>/summary.json    │
│    - tree_sim (Jaccard)      │  Streamlit 可视化            │
│    - tool_match (序列比对)    │  支持历史快照对比              │
│  L2/L3: LLM-as-Judge        │                              │
└─────────────────────────────┴──────────────────────────────┘
```

### 三层评测体系

| 层级 | 题目数 | 实际耗时 | 判分方式 | 重点维度 |
|------|--------|---------|---------|---------|
| **Layer 1** 原子能力基准 | 50题 | ≈20-30min | 自动化（单测+工具匹配+拆解树相似度） | D1代码生成, D3工具调用, D5审查调试 |
| **Layer 2** 集成场景测试 | 8题 | ≈1-2h | LLM-as-Judge (DeepSeek-V4-Flash) 1-5分 | 全部6维融合作战 |
| **Layer 3** 长程项目测试 | 2项目×5会话 | ≈0.5-1h | LLM-as-Judge + 人工抽检 | D6记忆, D4多智能体, D2拆解 |

### 六大评测维度

| 编号 | 维度 | 说明 |
|------|------|------|
| **D1** | 代码生成 | 语法正确性、逻辑完备性、边界处理、代码风格 |
| **D2** | 任务拆解 | 拆解粒度、依赖识别、优先级排序 |
| **D3** | 工具调用 | 工具选择准确性、参数正确性、链式编排 |
| **D4** | 多智能体协作 | 子Agent分派合理性、结果整合、一致性校验 |
| **D5** | 审查/调试 | Bug发现率、根因定位、修复正确性 |
| **D6** | 持续记忆 | 跨会话上下文保持、偏好积累、错误不再犯 |

### 综合评分公式

```
Overall = AVG(D1_combined, D2_combined, ..., D6_combined) × 10

各维度 combined_score = 
    l1_score (自动化判分, 0-1)  如果 l1_score > 0
    否则 judge_score / 5 (LLM判分, 1-5→0-1)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- [Claude Code](https://claude.ai/code) 或 [Cray Code](https://cray.com) CLI（按需安装）
- DeepSeek API key（L2/L3 评测必需）

### 安装

```bash
git clone https://github.com/yuHong-Cray/agent-eval-framework.git
cd agent-eval-framework

# 安装依赖
pip install -r requirements.txt

# 配置 API key（L2/L3 评测必需）
export DEEPSEEK_API_KEY="sk-xxx"
```

### 运行评测

```bash
# ── 一句话全量评测 ──────────────────────────────────────

# 快速模式（≈10分钟）— L1=10题 + L2=2场景
bash run_full_eval.sh --adapter claude --quick

# 完整模式（≈2-4小时）— L1全量50题 + L2全量8场景
bash run_full_eval.sh --adapter claude --reset

# ── CrayCode 评测 ────────────────────────────────────────
bash run_full_eval.sh --adapter cray --quick

# ── 单层评测 ────────────────────────────────────────────

# L1: 原子能力基准
python -m eval_framework.cli run --adapter claude --layer L1 --count 10 --seed 42

# L2: 集成场景测试（需要 API key）
python -m eval_framework.cli run --adapter claude --layer L2 --count 2 --seed 42

# 清理旧数据重新测试
python -m eval_framework.cli reset
```

### 查看结果

```bash
# Markdown 报告
cat reports/*/claude_report.md

# 启动 Dashboard（支持历史快照浏览）
streamlit run eval_framework/dashboard/app.py

# 打开 http://localhost:8501，侧边栏可切换数据源
# - 🟢 Live Database: 当前 SQLite 数据
# - 📁 20260628_...:  历史 runs 快照
```

---

## 适配器

### 已注册适配器

| 别名 | 适配器 | 底层命令 | 工具调用捕获 |
|------|--------|---------|-------------|
| `claude` | ClaudeCodeAdapter | `claude -p --output-format stream-json --verbose` | NDJSON 逐行解析 `message.content[].tool_use` |
| `cray` / `craycode` | CrayCodeAdapter | `cray --input -d -v` | 权限日志 + Thought 关键词推断 + turn 计数 |

### ClaudeCodeAdapter

驱动 `claude -p` 非交互模式，核心特性：

- **prompt 增强**：自动注入工具使用指令 + 工作区文件列表
- **输出格式**：`--output-format stream-json --verbose`，逐行 NDJSON，每行独立解析无递归风险
- **工具捕获**：解析 `type=assistant` → `message.content[].type=tool_use` → `name` 字段
- **结果提取**：逐行 JSON 解析，取 `type=result` 行的 `result` 字段
- **权限模式**：`--permission-mode acceptEdits`，Write/Edit/Bash 自动批准

```bash
python -m eval_framework.cli run --adapter claude --layer L1 --count 10
```

### CrayCodeAdapter

驱动 `cray --input` 非交互模式，核心特性：

- **prompt 增强**：注入工具使用指令 + 工作区文件列表
- **工具捕获**：三层推断策略
  1. `[Cray] [Permission] allowing "Tool"` 日志解析
  2. `Thought:` 文本关键词映射（read→Read, write→Write, bash→Bash 等 11 种）
  3. `[Turn N]` + `Running tools...` 计数兜底
- **安全命令构建**：双引号包裹 + 转义

```bash
python -m eval_framework.cli run --adapter cray --layer L1 --count 10
```

### CLIAdapter（通用命令行）

适用于任何可通过 CLI 调用并接受 stdin 输入的 Agent。

```bash
python -m eval_framework.cli run \
    --adapter cli \
    --command "my-agent run" \
    --layer L1 --count 5
```

### 添加新适配器

详见 [eval_framework/adapters/base.py](eval_framework/adapters/base.py)。

```python
from eval_framework.adapters.base import AgentAdapter
from eval_framework.adapters.factory import AdapterFactory

class MyAdapter(AgentAdapter):
    def execute(self, prompt, context) -> AgentTrace: ...
    def capabilities(self) -> AgentCapabilities: ...

AdapterFactory.register("my-agent", MyAdapter)
```

---

## 评分体系

### L1 评分类型

每道题的 `metadata.json` 中定义 `scoring.type`：

| 类型 | 评分逻辑 | 适用维度 |
|------|---------|---------|
| **unit_test** | `pytest passed / (passed+failed+errors)` | D1, D5 |
| **tree_sim** | JSON 任务树 Jaccard 相似度（最终输出 + 工作区文件兜底） | D2 |
| **tool_match** | 工具序列逐位匹配 + 参数存在性检查 | D3 |
| **llm_judge** | LLM Judge 1-5 分 → /5 映射到 0-1 | D4, D6, L2/L3 |

### L2/L3 LLM-as-Judge（1-5 分制）

| 分数 | 等级 | 说明 |
|------|------|------|
| 1 | ❌ 严重不足 | 未尝试，交付物不可用 |
| 2 | 🟡 部分完成 | 核心功能部分实现，存在明显问题 |
| 3 | 🟢 合格 | 核心功能正确实现，无严重缺陷 |
| 4 | 🔵 超出预期 | 实现全面，边界处理得当 |
| 5 | ⭐ 优秀 | 最佳实践范例 |

Judge 输入包含：题目 prompt → agent 工具调用序列 → agent 输出文本 → 工作区文件内容。

### Dashboard 总分显示

Dashboard 顶部直接显示各 Agent 的 🟢/🟡/🔴 总分卡片：

```
🏆 Overall Score
┌─────────────┐  ┌─────────────┐
│  🟢 claude  │  │  🟡 cray   │
│  8.9 / 10   │  │  6.5 / 10  │
│  6 dims avg │  │  4 dims avg│
└─────────────┘  └─────────────┘
```

---

## 全量评测流程

```
┌──────────────────────────────────────────────────┐
│ 🧹 Step 0  Reset DB     清空上次数据               │
├──────────────────────────────────────────────────┤
│ 🔬 Step 1  Layer 1      原子能力基准              │
│            50题  自动判分                          │
│            D1/D5: unit_test | D2: tree_sim        │
│            D3: tool_match | D4/D6: llm_judge      │
├──────────────────────────────────────────────────┤
│ 🧪 Step 2  Layer 2      集成场景测试              │
│            8场景  LLM-as-Judge 6维评分             │
│            需要 DEEPSEEK_API_KEY                   │
├──────────────────────────────────────────────────┤
│ 🏗️ Step 3  Layer 3      长程项目测试              │
│            5会话 跨会话记忆+多Agent协作             │
├──────────────────────────────────────────────────┤
│ 📊 Step 4  Report       报告生成                  │
│            Markdown + JSON汇总 + 总分 X.X/10      │
│            reports/<timestamp>/                   │
└──────────────────────────────────────────────────┘
```

```bash
# 完整流程（一条命令）
bash run_full_eval.sh --adapter claude --reset

# 自定义选项
bash run_full_eval.sh --adapter cray --skip-l3 --l1-count 30 --quick
```

---

## 配置

通过 `config.yaml` 或环境变量覆盖：

```yaml
# config.yaml
scoring:
  l2_l3:
    judge_model: "deepseek-v4-pro"
    judge_api_base: "https://api.deepseek.com"
    judge_max_retries: 3
```

环境变量覆盖：

```bash
export DEEPSEEK_API_KEY="sk-xxx"      # L2/L3 评测必需
export EVAL_DATABASE_URL="postgresql://..."  # 可选 PostgreSQL
```

---

## 项目结构

```
agent-eval-framework/
├── eval_framework/                # 核心框架
│   ├── config.py                  # YAML + 环境变量配置
│   ├── models.py                  # Pydantic 数据模型
│   ├── cli.py                     # Click CLI (run/report/reset)
│   │
│   ├── orchestrator/              # 评测编排层
│   │   ├── scheduler.py           # 串行执行 + 结果聚合
│   │   ├── tracer.py              # Agent 行为轨迹捕获
│   │   └── context.py             # 测题加载 + 工作区注入
│   │
│   ├── adapters/                  # Agent 接口适配层
│   │   ├── base.py                # AgentAdapter 抽象基类
│   │   ├── claude_code.py         # Claude Code 适配器 (stream-json)
│   │   ├── cray_code.py           # CrayCode 适配器 (v -v 解析)
│   │   ├── cli_generic.py         # 通用 CLI 适配器
│   │   └── factory.py             # 适配器工厂 + 注册表
│   │
│   ├── scoring/                   # 判分引擎
│   │   ├── l1_runner.py           # L1 判分编排（含工作区文件兜底）
│   │   ├── test_runner.py         # 多语言测试运行器
│   │   ├── tool_matcher.py        # 工具调用轨迹匹配
│   │   ├── tree_similarity.py     # 任务拆解树 Jaccard 相似度
│   │   ├── l2_l3_judge.py         # LLM-as-Judge
│   │   └── calibrator.py          # 人工抽检校准
│   │
│   ├── db/                        # 数据持久化
│   │   └── models.py / repository.py / connection.py
│   │
│   └── dashboard/                 # 可视化面板
│       ├── app.py                 # Streamlit（历史 / Live DB 双数据源）
│       ├── charts.py              # 雷达图 / 柱状图
│       └── report.py              # Markdown 报告生成
│
├── test_items/                    # 测评题库（50 L1 + 8 L2 + 5 L3）
├── run_full_eval.sh               # 全量评测一键脚本
├── config.yaml                    # 全局配置
├── requirements.txt               # Python 依赖
└── Makefile                       # 常用命令
```

---

## Dashboard

```bash
streamlit run eval_framework/dashboard/app.py
```

**数据源切换**：侧边栏下拉框选择 `🟢 Live Database`（当前 SQLite）或任意历史 `reports/<timestamp>/` 快照。

**视图模式**：
- 🔴 **雷达图** — 多 Agent 六维叠加对比
- 📊 **柱状图** — 维度得分分组对比
- 📋 **评分表** — 评分矩阵 + Overall 总分
- 📦 **Layer 统计** — 各层运行次数

---

## 常见问题

**Q: D2 分数为什么低？**
> D2 (tree_sim) 比较 agent 输出的 JSON 拆解树和期望树的 Jaccard 相似度。如果 agent 把 JSON 写到了文件而不是 stdout，系统会自动扫描工作区中的 `.json` 文件作为兜底。

**Q: D3 分数为什么低？**
> D3 (tool_match) 比对 agent 实际工具调用序列和期望序列。非交互模式下工具日志可能被截断，系统使用多层捕获策略（NDJSON 解析 / thought 关键词 / turn 计数）最大化覆盖率。

**Q: 所有 Agent 评分公平可比吗？**
> 是的。所有 Agent 走同一套 `Scheduler._run_single_item()` → `L1Scorer.score()` 路径，评分标准完全一致，无 Agent 特定加权。

---

## License

MIT © 2026
