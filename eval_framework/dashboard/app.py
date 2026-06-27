"""Streamlit dashboard for evaluation results."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eval_framework.db.connection import init_db, get_session
from eval_framework.db.repository import EvalRepository
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

# Initialize database
init_db()
repo = EvalRepository(get_session())


# ── Sidebar ──────────────────────────────────────────

st.sidebar.header("🔍 Filters")

agent_list = ["craycode", "copilot", "cursor", "cli-generic"]
selected_agents = st.sidebar.multiselect(
    "Select Agents",
    agent_list,
    default=agent_list[:2],
)

view_mode = st.sidebar.radio(
    "View Mode",
    ["Radar Comparison", "Bar Chart", "Score Summary", "Trend History"],
)

st.sidebar.divider()
st.sidebar.caption(
    "Run `python -m eval_framework.cli run` to populate data."
)


# ── Helper ───────────────────────────────────────────

def _build_dimension_df(agents: list[str]) -> pd.DataFrame:
    """Build a DataFrame of agent × dimension scores."""
    rows = []
    for agent in agents:
        scores = repo.get_agent_scores(agent)
        if scores:
            for dim, data in scores.items():
                score = data.get("avg_judge_score") or data.get(
                    "avg_l1_score", 0
                )
                rows.append(
                    {
                        "agent": agent,
                        "dimension": dim,
                        "score": score,
                        "runs": data.get("run_count", 0),
                    }
                )
    return pd.DataFrame(rows)


# ── Main Content ─────────────────────────────────────

tab1, tab2, tab3 = st.tabs(
    ["📈 Comparison", "📋 Details", "📝 Report"]
)

# ── Tab 1: Comparison ────────────────────────────────

with tab1:
    if view_mode == "Radar Comparison":
        st.subheader("🔴 Capability Radar — Multi-Agent Overlay")
        if selected_agents:
            scores = {}
            for agent in selected_agents:
                agent_scores = repo.get_agent_scores(agent)
                for dim, data in agent_scores.items():
                    val = data.get("avg_judge_score") or data.get(
                        "avg_l1_score", 0
                    )
                    scores[f"{agent}_{dim}"] = val
            if scores:
                fig = radar_chart(
                    scores,
                    "Agent Capability Comparison",
                    selected_agents,
                )
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
                index="dimension",
                columns="agent",
                values="score",
                aggfunc="mean",
            )
            st.dataframe(pivot, use_container_width=True)

            st.divider()
            st.caption("Scores: 1-5 scale (L2/L3 judge) or 0.0-1.0 (L1 automated)")
        else:
            st.info("No data yet.")

    elif view_mode == "Trend History":
        st.subheader("📈 Score Trend Over Versions")
        dimension = st.selectbox(
            "Dimension",
            ["D1", "D2", "D3", "D4", "D5", "D6"],
            index=0,
        )
        st.caption(
            "Trend data requires multiple version runs. "
            "Shows score evolution over agent releases."
        )
        # Placeholder — trend data requires historical runs
        df = _build_dimension_df(selected_agents)
        if not df.empty:
            dim_df = df[df["dimension"] == dimension]
            if not dim_df.empty:
                st.bar_chart(
                    dim_df.set_index("agent")["score"],
                    use_container_width=True,
                )
            else:
                st.info(f"No data for {dimension}")
        else:
            st.info("No data yet.")

# ── Tab 2: Details ───────────────────────────────────

with tab2:
    st.subheader("🔍 Score Drill-Down")

    drill_agent = st.selectbox(
        "Agent",
        selected_agents if selected_agents else agent_list,
    )

    if drill_agent:
        scores = repo.get_agent_scores(drill_agent)
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
                        st.metric(
                            label=f"{dim} L1 Score",
                            value=f"{l1:.3f}",
                        )
                    if judge is not None:
                        st.metric(
                            label=f"{dim} Judge Score",
                            value=f"{judge:.1f}/5",
                        )
                    st.caption(f"{runs} runs")

            # Show recent runs for this agent
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

# ── Tab 3: Report ────────────────────────────────────

with tab3:
    st.subheader("📝 Generate Report")

    report_agent = st.text_input("Agent name", value=selected_agents[0] if selected_agents else "craycode")
    report_path = st.text_input(
        "Output path",
        value="reports/eval_report.md",
    )

    if st.button("Generate Markdown Report"):
        scores = repo.get_agent_scores(report_agent)
        if scores:
            content = ReportGenerator.generate_markdown(
                report_agent,
                scores,
                Path(report_path),
            )
            st.success(f"Report saved to `{report_path}`")
            st.markdown(content)
        else:
            st.warning(f"No data found for '{report_agent}'.")
