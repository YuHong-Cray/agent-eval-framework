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
    dimensions = [
        "D1 Code",
        "D2 Decompose",
        "D3 Tools",
        "D4 Multi-Agent",
        "D5 Debug",
        "D6 Memory",
    ]

    fig = go.Figure()

    if agent_names is None:
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
        for name in agent_names:
            values = [
                scores.get(f"{name}_D{i}", 0) for i in range(1, 7)
            ]
            fig.add_trace(
                go.Scatterpolar(
                    r=values,
                    theta=dimensions,
                    fill="toself",
                    name=name,
                )
            )
        fig.update_layout(title="Agent Comparison Radar")

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5]))
    )
    return fig


def bar_chart_comparison(
    agent_scores: list[dict],
    title: str = "Agent Score Comparison",
) -> go.Figure:
    """Generate a grouped bar chart comparing agents per dimension."""
    df = pd.DataFrame(agent_scores)
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
    history: list[dict],
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
