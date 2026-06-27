"""Report generation — Markdown and HTML output."""

from datetime import datetime
from pathlib import Path


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
            l1 = (
                f"{d['avg_l1_score']:.3f}"
                if d.get("avg_l1_score") is not None
                else "N/A"
            )
            judge = (
                f"{d['avg_judge_score']:.1f}"
                if d.get("avg_judge_score") is not None
                else "N/A"
            )
            lines.append(
                f"| {dim} | {l1} | {judge} | {d['run_count']} |"
            )

        lines.append("")
        lines.append("## Summary")

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
