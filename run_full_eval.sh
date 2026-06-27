#!/bin/bash
# ============================================================
#  Agent Eval Framework — 全量三层评测脚本
#
#  用法:
#    ./run_full_eval.sh                    # 默认: L1全量 → L2全量 → L3全量
#    ./run_full_eval.sh --adapter cray     # 指定适配器
#    ./run_full_eval.sh --skip-l1          # 跳过 L1
#    ./run_full_eval.sh --skip-l2          # 跳过 L2
#    ./run_full_eval.sh --l1-count 20      # L1 只跑 20 题
#    ./run_full_eval.sh --quick            # 快速模式: L1=10, L2=2, L3=skip
# ============================================================
set -euo pipefail

# ── 默认参数 ───────────────────────────────────────────────
ADAPTER="${ADAPTER:-claude}"
SEED="${SEED:-42}"
SKIP_L1=false
SKIP_L2=false
SKIP_L3=false
L1_COUNT=0          # 0 = all
L2_COUNT=0
L3_COUNT=0
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="reports/${TIMESTAMP}"
START_TIME=$(date +%s)

# ── 解析参数 ───────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --adapter)   ADAPTER="$2"; shift 2 ;;
        --skip-l1)   SKIP_L1=true; shift ;;
        --skip-l2)   SKIP_L2=true; shift ;;
        --skip-l3)   SKIP_L3=true; shift ;;
        --l1-count)  L1_COUNT="$2"; shift 2 ;;
        --l2-count)  L2_COUNT="$2"; shift 2 ;;
        --quick)     L1_COUNT=10; L2_COUNT=2; SKIP_L3=true; shift ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --adapter <name>   Agent adapter (default: claude)"
            echo "  --seed <n>         Random seed (default: 42)"
            echo "  --skip-l1/l2/l3    Skip that layer"
            echo "  --l1/l2-count <n>  Number of items (0=all)"
            echo "  --quick            Fast mode: L1=10 L2=2 L3=skip"
            exit 0 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

# ── 标题 ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Coding Agent 深度评测 — 全量三层测试                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Adapter : ${ADAPTER}                                          ║"
echo "║  Seed    : ${SEED}                                            ║"
echo "║  Output  : ${REPORT_DIR}                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

mkdir -p "$REPORT_DIR"

CLI="python -m eval_framework.cli"

# ── 清理 ──────────────────────────────────────────────────
echo "🧹 Step 0/4: Clearing previous data..."
$CLI reset --yes 2>/dev/null || rm -f eval_framework.db eval_framework.db-wal eval_framework.db-shm
echo "   Done."
echo ""

# ── Layer 1 ───────────────────────────────────────────────
if $SKIP_L1; then
    echo "⏭️  Step 1/4: Layer 1 — SKIPPED"
else
    L1_LABEL="all ($(python -c "from eval_framework.orchestrator.context import TestItemRegistry; r=TestItemRegistry(); r.load(); print(len(r.get_by_layer('L1')))") items)"
    if [ "$L1_COUNT" -gt 0 ]; then
        L1_LABEL="$L1_COUNT items (sampled)"
    fi
    echo "🔬 Step 1/4: Layer 1 — 原子能力基准 (${L1_LABEL})"
    echo "──────────────────────────────────────────────────────────"
    L1_START=$(date +%s)

    $CLI run --adapter "$ADAPTER" --layer L1 --count "$L1_COUNT" --seed "$SEED" 2>&1 | tee "${REPORT_DIR}/l1_output.log"

    L1_END=$(date +%s)
    L1_DUR=$((L1_END - L1_START))
    echo "   Layer 1 completed in ${L1_DUR}s"
    echo ""
fi

# ── Layer 2 ───────────────────────────────────────────────
if $SKIP_L2; then
    echo "⏭️  Step 2/4: Layer 2 — SKIPPED (needs LLM-as-Judge API key)"
else
    L2_LABEL="all ($(python -c "from eval_framework.orchestrator.context import TestItemRegistry; r=TestItemRegistry(); r.load(); print(len(r.get_by_layer('L2')))") scenarios)"
    if [ "$L2_COUNT" -gt 0 ]; then
        L2_LABEL="$L2_COUNT scenarios (sampled)"
    fi
    echo "🧪 Step 2/4: Layer 2 — 集成场景测试 (${L2_LABEL})"
    echo "──────────────────────────────────────────────────────────"
    L2_START=$(date +%s)

    $CLI run --adapter "$ADAPTER" --layer L2 --count "$L2_COUNT" --seed "$SEED" 2>&1 | tee "${REPORT_DIR}/l2_output.log"

    L2_END=$(date +%s)
    L2_DUR=$((L2_END - L2_START))
    echo "   Layer 2 completed in ${L2_DUR}s"
    echo ""
fi

# ── Layer 3 ───────────────────────────────────────────────
if $SKIP_L3; then
    echo "⏭️  Step 3/4: Layer 3 — SKIPPED (needs LLM-as-Judge API key)"
else
    L3_LABEL="all ($(python -c "from eval_framework.orchestrator.context import TestItemRegistry; r=TestItemRegistry(); r.load(); print(len(r.get_by_layer('L3')))") sessions)"
    if [ "$L3_COUNT" -gt 0 ]; then
        L3_LABEL="$L3_COUNT sessions (sampled)"
    fi
    echo "🏗️  Step 3/4: Layer 3 — 长程项目测试 (${L3_LABEL})"
    echo "──────────────────────────────────────────────────────────"
    L3_START=$(date +%s)

    $CLI run --adapter "$ADAPTER" --layer L3 --count "$L3_COUNT" --seed "$SEED" 2>&1 | tee "${REPORT_DIR}/l3_output.log"

    L3_END=$(date +%s)
    L3_DUR=$((L3_END - L3_START))
    echo "   Layer 3 completed in ${L3_DUR}s"
    echo ""
fi

# ── 汇总报告 ──────────────────────────────────────────────
END_TIME=$(date +%s)
TOTAL_DUR=$((END_TIME - START_TIME))
HOURS=$((TOTAL_DUR / 3600))
MINS=$(((TOTAL_DUR % 3600) / 60))
SECS=$((TOTAL_DUR % 60))

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     ✅ 全量评测完成                                       ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Duration : ${HOURS}h ${MINS}m ${SECS}s                                            ║"
echo "║  Reports  : ${REPORT_DIR}                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 生成报告 ──────────────────────────────────────────────
echo "📊 Step 4/4: Generating reports..."
echo "──────────────────────────────────────────────────────────"

# Per-agent report
$CLI report --agent "$ADAPTER" --output "${REPORT_DIR}/${ADAPTER}_report.md" 2>&1

# Summary JSON (manual extract from DB)
python -c "
import json
from eval_framework.db.connection import init_db, get_session
from eval_framework.db.repository import EvalRepository
from eval_framework.db.models import EvalRun, EvalResult

init_db()
repo = EvalRepository(get_session())
session = repo._session

# Collect stats
total_runs = session.query(EvalRun).count()
agents = [a[0] for a in session.query(EvalRun.agent_name).distinct().all()]

summary = {'timestamp': '${TIMESTAMP}', 'total_runs': total_runs, 'agents': {}}
for agent in agents:
    scores = repo.get_agent_scores(agent)
    # Count by layer
    by_layer = {}
    for run in session.query(EvalRun).filter(EvalRun.agent_name == agent).all():
        layer = run.test_item_id.split('-')[0][:2]  # L1, L2, L3
        by_layer[layer] = by_layer.get(layer, 0) + 1

    summary['agents'][agent] = {
        'scores': scores,
        'runs_by_layer': by_layer,
    }

out_path = '${REPORT_DIR}/summary.json'
json.dump(summary, open(out_path, 'w'), indent=2, ensure_ascii=False)
print(f'Summary saved to {out_path}')
print()
for agent in agents:
    s = summary['agents'][agent]
    print(f'  {agent}:')
    for layer in ['L1', 'L2', 'L3']:
        cnt = s['runs_by_layer'].get(layer, 0)
        print(f'    {layer}: {cnt} runs')
    for dim, d in sorted(s['scores'].items()):
        score = d.get('avg_l1_score') or d.get('avg_judge_score') or 0
        print(f'    {dim}: {score:.3f}')
" 2>&1

echo ""
echo "──────────────────────────────────────────────────────────"
echo ""
echo "📋 View results:"
echo "   cat ${REPORT_DIR}/${ADAPTER}_report.md"
echo "   streamlit run eval_framework/dashboard/app.py"
echo ""
echo "🏁 Done."
