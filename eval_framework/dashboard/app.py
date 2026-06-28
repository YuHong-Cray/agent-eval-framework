"""Streamlit dashboard for evaluation results.

Supports two data sources:
  1. Live database   — reads directly from eval_framework.db (current session)
  2. Reports archive — reads from reports/<timestamp>/summary.json (historical runs)
"""

import json
import sys
from pathlib import Path
from typing import Optional

import streamlit as st
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eval_framework.config import config
from eval_framework.dashboard.charts import (
    radar_chart,
    bar_chart_comparison,
    score_trend_chart,
)
from eval_framework.dashboard.report import ReportGenerator

st.set_page_config(
    page_title="Coding Agent Eval Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Coding Agent Evaluation Dashboard")


# ── Data Source Helpers ──────────────────────────────────────────────

def _load_reports_dirs() -> list[Path]:
    """Return sorted list of report directories (newest first)."""
    report_root = config.get_report_dir()
    if not report_root.exists():
        return []
    dirs = [
        p for p in sorted(report_root.iterdir(), reverse=True)
        if p.is_dir() and (p / "summary.json").exists()
    ]
    return dirs


def _load_summary(report_dir: Path) -> dict:
    """Load summary.json from a report directory."""
    path = report_dir / "summary.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_agent_list_from_summary(summary: dict) -> list[str]:
    """Extract agent names from a summary dict."""
    return list(summary.get("agents", {}).keys())


def _get_scores_from_summary(summary: dict, agent: str) -> dict:
    """Extract per-dimension scores for one agent from summary dict.

    Returns the same shape as EvalRepository.get_agent_scores():
      {"D1": {"avg_l1_score": ..., "avg_judge_score": ..., "combined_score": ..., "run_count": ...}, ...}
    """
    agents = summary.get("agents", {})
    return agents.get(agent, {}).get("scores", {})


def _get_runs_by_layer_from_summary(summary: dict, agent: str) -> dict:
    """Extract runs_by_layer for one agent from summary dict."""
    agents = summary.get("agents", {})
    return agents.get(agent, {}).get("runs_by_layer", {})


# ── Initialise ──────────────────────────────────────────────────────

report_dirs = _load_reports_dirs()

# Build data-source options
ds_options: dict[str, Optional[Path]] = {"🟢 Live Database": None}
for d in report_dirs:
    label = d.name  # e.g. "20260628_072724"
    ds_options[label] = d

# ── Sidebar ─────────────────────────────────────────────────────────

st.sidebar.header("🔍 Data Source")

selected_label = st.sidebar.selectbox(
    "Choose evaluation run",
    list(ds_options.keys()),
    index=0,
)

selected_dir: Optional[Path] = ds_options[selected_label]

# --- Determine agent list and scores based on source ---
if selected_dir is None:
    # Live DB mode
    from eval_framework.db.connection import init_db, get_session
    from eval_framework.db.models import EvalRun
    from eval_framework.db.repository import EvalRepository

    init_db()
    session = get_session()
    repo = EvalRepository(session)

    total_runs = session.query(EvalRun).count()
    db_agents = [a[0] for a in session.query(EvalRun.agent_name).distinct().all()]

    def get_scores(agent: str) -> dict:
        return repo.get_agent_scores(agent)

    def get_runs_by_layer(agent: str) -> dict:
        run = session.query(EvalRun).filter(EvalRun.agent_name == agent).first()
        return {}  # DB mode delegates layer counts to summary (not tracked per-agent in DB)

    source_badge = "🟢 Live DB"
    source_caption = f"Reading from `eval_framework.db`  •  {total_runs} runs across {len(db_agents)} agent(s)"
    agent_names = db_agents if db_agents else []

else:
    # Reports archive mode
    summary = _load_summary(selected_dir)

    def get_scores(agent: str) -> dict:
        return _get_scores_from_summary(summary, agent)

    def get_runs_by_layer(agent: str) -> dict:
        return _get_runs_by_layer_from_summary(summary, agent)

    total_runs = summary.get("total_runs", 0)
    agent_names = _get_agent_list_from_summary(summary)
    source_badge = f"📁 {selected_dir.name}"
    source_caption = (
        f"Reading from `reports/{selected_dir.name}/summary.json`  •  "
        f"{total_runs} runs across {len(agent_names)} agent(s)"
    )

# Source info
st.sidebar.markdown(f"**Source:** {source_badge}")
st.sidebar.caption(source_caption)

# Agent selector
available_agents = agent_names if agent_names else ["craycode", "claude", "copilot", "cursor", "cli-generic"]
selected_agents = st.sidebar.multiselect(
    "Select Agents",
    available_agents,
    default=available_agents[: min(2, len(available_agents))],
)

view_mode = st.sidebar.radio(
    "View Mode",
    ["Radar Comparison", "Bar Chart", "Score Summary", "Layer Summary"],
)

st.sidebar.divider()
if selected_dir is None:
    st.sidebar.caption(
        "Run `python -m eval_framework.cli run` to populate data.\n\n"
        "Tip: choose a `reports/<ts>/` entry above to view historical runs."
    )
else:
    # Show per-agent layer breakdown in sidebar
    st.sidebar.caption("**Runs by layer:**")
    for agent in available_agents:
        layers = get_runs_by_layer(agent)
        if layers:
            parts = [f"{ly}: {cnt}" for ly, cnt in sorted(layers.items())]
            st.sidebar.caption(f"  *{agent}* — {', '.join(parts)}")


# ── Quick Stats ─────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Runs", total_runs)
with col2:
    st.metric("Agents", len(available_agents))
with col3:
    st.metric("Source", source_badge)


# ── Helper ──────────────────────────────────────────────────────────

def _build_dimension_df(agents: list[str]) -> pd.DataFrame:
    """Build a DataFrame of agent × dimension scores."""
    rows = []
    for agent in agents:
        scores = get_scores(agent)
        if scores:
            for dim, data in scores.items():
                rows.append({
                    "agent": agent,
                    "dimension": dim,
                    "score": data.get("combined_score", 0.0),
                    "runs": data.get("run_count", 0),
                })
    return pd.DataFrame(rows)


def _compute_overall_score(agent: str) -> tuple[float, int]:
    """Return (overall_0to10, num_dimensions) for one agent."""
    scores = get_scores(agent)
    all_scores = [data.get("combined_score", 0.0) for data in scores.values()]
    if not all_scores:
        return (0.0, 0)
    overall_raw = sum(all_scores) / len(all_scores)
    return (overall_raw * 10.0, len(all_scores))


# ── Main Content ────────────────────────────────────────────────────

# Overall Score Banner
if selected_agents:
    st.subheader("🏆 Overall Score")
    cols = st.columns(len(selected_agents))
    for i, agent in enumerate(selected_agents):
        score, n_dims = _compute_overall_score(agent)
        with cols[i]:
            color = "🟢" if score >= 7.0 else "🟡" if score >= 4.0 else "🔴"
            st.metric(
                label=f"{color} {agent}",
                value=f"{score:.1f} / 10",
                help=f"Average of {n_dims} dimension combined scores × 10",
            )

st.divider()

tab1, tab2, tab3 = st.tabs(["📈 Comparison", "📋 Details", "📝 Report"])

# ── Tab 1: Comparison ──────────────────────────────────────────────

with tab1:
    if view_mode == "Radar Comparison":
        st.subheader("🔴 Capability Radar — Multi-Agent Overlay")
        if selected_agents:
            scores = {}
            for agent in selected_agents:
                agent_scores = get_scores(agent)
                for dim, data in agent_scores.items():
                    # Radar expects 0-5 scale — combined_score is 0-1, scale up
                    scores[f"{agent}_{dim}"] = data.get("combined_score", 0.0) * 5.0
            if scores:
                fig = radar_chart(scores, "Agent Capability Comparison", selected_agents)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data yet. Run some evaluations first.")
        else:
            st.info("Select agents to compare.")

    elif view_mode == "Bar Chart":
        st.subheader("📊 Dimension Scores — Grouped Bar Chart")
        df = _build_dimension_df(selected_agents)
        if not df.empty:
            fig = bar_chart_comparison(
                df.to_dict(orient="records"),
                "Agent Dimension Score Comparison",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet.")

    elif view_mode == "Score Summary":
        st.subheader("📋 Score Summary Table")
        df = _build_dimension_df(selected_agents)
        if not df.empty:
            pivot = df.pivot_table(
                index="dimension", columns="agent", values="score", aggfunc="mean",
            )
            st.dataframe(pivot, use_container_width=True)

            # Overall score row
            st.divider()
            st.subheader("🏆 Overall Score")
            cols = st.columns(len(selected_agents))
            for i, agent in enumerate(selected_agents):
                score, n_dims = _compute_overall_score(agent)
                with cols[i]:
                    color = "🟢" if score >= 7.0 else "🟡" if score >= 4.0 else "🔴"
                    st.metric(
                        label=f"{color} {agent}",
                        value=f"{score:.1f} / 10",
                        help=f"Average of {n_dims} dimension combined scores × 10",
                    )

            st.divider()
            st.caption("Scores: 0.0–1.0 scale (L1 automated or L2/L3 judge ÷ 5)")
        else:
            st.info("No data yet.")

    elif view_mode == "Layer Summary":
        st.subheader("📦 Runs by Layer")
        if selected_dir is not None:
            rows = []
            for agent in available_agents:
                layers = get_runs_by_layer(agent)
                for layer, cnt in sorted(layers.items()):
                    rows.append({"agent": agent, "layer": layer, "runs": cnt})
            if rows:
                df = pd.DataFrame(rows)
                fig = bar_chart_comparison(
                    [{"agent": r["agent"], "dimension": r["layer"], "score": r["runs"]}
                     for r in rows],
                    "Runs per Layer per Agent",
                )
                fig.update_layout(yaxis_title="Number of runs")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No layer data available.")
        else:
            # Live DB: query layer counts from DB
            from eval_framework.db.models import EvalRun as ER
            rows = []
            for agent in available_agents:
                for run in session.query(ER).filter(ER.agent_name == agent).all():
                    layer = run.test_item_id.split("-")[0][:2]
                    rows.append({"agent": agent, "layer": layer})
            if rows:
                df = pd.DataFrame(rows)
                counts = df.groupby(["agent", "layer"]).size().reset_index(name="runs")
                fig = bar_chart_comparison(
                    [{"agent": r["agent"], "dimension": r["layer"], "score": r["runs"]}
                     for _, r in counts.iterrows()],
                    "Runs per Layer per Agent (Live DB)",
                )
                fig.update_layout(yaxis_title="Number of runs")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(counts, use_container_width=True, hide_index=True)
            else:
                st.info("No data yet.")

# ── Tab 2: Details ──────────────────────────────────────────────────

with tab2:
    st.subheader("🔍 Score Drill-Down")

    drill_agent = st.selectbox("Agent", selected_agents if selected_agents else available_agents)

    if drill_agent:
        scores = get_scores(drill_agent)
        if scores:
            st.write(f"### {drill_agent} — Per-Dimension Breakdown")

            cols = st.columns(3)
            dim_order = ["D1", "D2", "D3", "D4", "D5", "D6"]
            for i, dim in enumerate(dim_order):
                data = scores.get(dim, {})
                with cols[i % 3]:
                    l1 = data.get("avg_l1_score")
                    judge = data.get("avg_judge_score")
                    runs = data.get("run_count", 0)
                    if l1 is not None:
                        st.metric(label=f"{dim} L1 Score", value=f"{l1:.3f}")
                    if judge is not None:
                        st.metric(label=f"{dim} Judge Score", value=f"{judge:.1f}/5")
                    st.caption(f"{runs} runs")

            # Show layer breakdown in detail view
            layers = get_runs_by_layer(drill_agent)
            if layers:
                st.divider()
                st.write("### Runs by Layer")
                layer_cols = st.columns(len(layers) or 1)
                for i, (ly, cnt) in enumerate(sorted(layers.items())):
                    with layer_cols[i]:
                        st.metric(label=f"Layer {ly}", value=cnt)

            # Overall score for this agent
            st.divider()
            st.write("### Overall Score")
            score_10, n_dims = _compute_overall_score(drill_agent)
            color = "🟢" if score_10 >= 7.0 else "🟡" if score_10 >= 4.0 else "🔴"
            st.metric(
                label=f"{color} {drill_agent}",
                value=f"{score_10:.1f} / 10",
                help=f"Average across {n_dims} dimensions, each 0-1 scaled × 10",
            )

            # Show recent runs (live DB only)
            if selected_dir is None:
                st.divider()
                st.write("### Recent Runs")
                runs = repo.list_runs(agent_name=drill_agent, limit=10)
                if runs:
                    run_data = [
                        {
                            "Run ID": r.run_id[:20] + "...",
                            "Item": r.test_item_id,
                            "Status": r.status,
                            "Duration": f"{r.duration_seconds:.1f}s",
                            "Time": str(r.start_time)[:19],
                        }
                        for r in runs
                    ]
                    st.dataframe(pd.DataFrame(run_data), use_container_width=True)
                else:
                    st.info("No runs yet.")
        else:
            st.info(f"No data for {drill_agent}.")

# ── Tab 3: Report ──────────────────────────────────────────────────

with tab3:
    st.subheader("📝 Generate Report")

    report_agent = st.text_input(
        "Agent name",
        value=selected_agents[0] if selected_agents else "craycode",
    )
    report_path = st.text_input("Output path", value="reports/eval_report.md")

    if st.button("Generate Markdown Report"):
        scores = get_scores(report_agent)
        if scores:
            content = ReportGenerator.generate_markdown(report_agent, scores, Path(report_path))
            st.success(f"Report saved to `{report_path}`")
            st.markdown(content)
        else:
            st.warning(f"No data found for '{report_agent}'.")
