"""CLI entry point for the evaluation framework."""

import sys
sys.setrecursionlimit(10000)  # Pydantic + deep JSON needs more headroom

from datetime import datetime
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
@click.option(
    "--adapter", "-a", default="cli", help="Agent adapter type"
)
@click.option(
    "--command", "-c", default="", help="CLI command for agent"
)
@click.option(
    "--layer", "-l", default="L1", help="Layer to run (L1/L2/L3)"
)
@click.option(
    "--count", "-n", default=0, help="Number of items (0 = all)"
)
@click.option(
    "--seed", "-s", default=None, type=int, help="Random seed"
)
def run(adapter: str, command: str, layer: str, count: int, seed: int):
    """Run evaluation tests for a layer."""
    click.echo("Initializing database...")
    init_db()

    click.echo(f"Loading test items for layer {layer}...")
    registry = TestItemRegistry()
    registry.load()

    if layer not in ("L1", "L2", "L3"):
        click.echo(f"Invalid layer: {layer}", err=True)
        sys.exit(1)

    items = registry.get_by_layer(layer)
    if count > 0 and count < len(items):
        items = registry.select_random(layer, count, seed)

    click.echo(f"Selected {len(items)} items for {layer}")

    click.echo(f"Creating adapter '{adapter}'...")
    kwargs = {"workspace": "/tmp/eval"}
    if command:
        kwargs["command"] = command
    agent = AdapterFactory.create(adapter, **kwargs)

    repo = EvalRepository(get_session())
    scheduler = Scheduler(
        adapter=agent,
        repository=repo,
        registry=registry,
    )

    click.echo(f"Running {len(items)} test items...")
    results = scheduler.run_layer(layer, items)

    completed = [r for r in results if r.status == "completed"]
    skipped = [r for r in results if r.status == "skipped"]
    errors = [
        r for r in results
        if r.status not in ("completed", "skipped")
    ]

    click.echo(
        f"\nResults: {len(completed)} completed, "
        f"{len(skipped)} skipped, "
        f"{len(errors)} failed/timeout"
    )

    if completed:
        # Show both L1 and judge scores — L1 items use automated scoring,
        # L2/L3 items use LLM-as-Judge (1-5 scale)
        l1_scores = [r.l1_score for r in completed if r.l1_score is not None]
        judge_scores = [
            max(c.score for c in r.judge_score_cards) if r.judge_score_cards else None
            for r in completed
        ]
        judge_scores = [s for s in judge_scores if s is not None]

        if l1_scores:
            avg_l1 = sum(l1_scores) / len(l1_scores)
            click.echo(f"Average L1 score: {avg_l1:.3f}  ({len(l1_scores)}/{len(completed)} items)")
        if judge_scores:
            avg_judge = sum(judge_scores) / len(judge_scores)
            click.echo(f"Average judge score: {avg_judge:.1f}/5  ({len(judge_scores)}/{len(completed)} items)")

    if skipped:
        for s in skipped:
            click.echo(
                f"  {s.test_item_id}: skipped — {s.error_message}"
            )

    if errors:
        for e in errors:
            click.echo(
                f"  {e.test_item_id}: {e.status} — {e.error_message}"
            )


@main.command()
@click.option(
    "--agent", "-a", default="", help="Agent name filter"
)
@click.option(
    "--output", "-o", default="reports/report.md", help="Output path"
)
def report(agent: str, output: str):
    """Generate evaluation report."""
    init_db()
    repo = EvalRepository(get_session())
    scores = repo.get_agent_scores(agent) if agent else {}

    lines = ["# Evaluation Report\n"]
    lines.append(f"Generated: {datetime.now()}\n\n")
    lines.append(f"Agent: {agent or 'All'}\n\n")

    if scores:
        lines.append("## Dimension Scores\n\n")
        lines.append(
            "| Dimension | Combined (0-1) | L1 Score | Judge (1-5) | Runs |\n"
        )
        lines.append(
            "|-----------|----------------|----------|-------------|------|\n"
        )
        for dim, data in sorted(scores.items()):
            score = f"{data['combined_score']:.3f}"
            l1 = f"{data['avg_l1_score']:.3f}" if data['avg_l1_score'] is not None else '—'
            judge = f"{data['avg_judge_score']:.1f}" if data['avg_judge_score'] is not None else '—'
            lines.append(
                f"| {dim} | {score} | {l1} | {judge} | "
                f"{data['run_count']} |\n"
            )

        # Overall score: average of all dimension combined_scores, ×10
        all_scores = [data['combined_score'] for d, data in scores.items()]
        if all_scores:
            overall_raw = sum(all_scores) / len(all_scores)
            overall_10 = overall_raw * 10.0
            lines.append(f"\n## Overall Score\n\n")
            lines.append(f"**{overall_10:.1f} / 10** — average across {len(all_scores)} dimensions\n")
            lines.append(f"Raw average: {overall_raw:.3f} (0-1 scale)\n")
    else:
        lines.append("No results found.\n")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines))
    click.echo(f"Report saved to {out_path}")


@main.command()
@click.confirmation_option(prompt="Drop all evaluation data and start fresh?")
def reset():
    """Delete all evaluation records from the database."""
    from eval_framework.db.models import Base
    from eval_framework.db.connection import get_engine

    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    click.echo("All evaluation data cleared. Ready for fresh testing.")


if __name__ == "__main__":
    main()
