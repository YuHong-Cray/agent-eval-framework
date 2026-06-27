"""CLI entry point for the evaluation framework."""

import sys
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
    agent = AdapterFactory.create(
        adapter, command=command, workspace="/tmp/eval"
    )

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

    click.echo(
        f"\nResults: {len(completed)} completed, "
        f"{len(errors)} failed/timeout"
    )

    if completed:
        avg_score = sum(
            r.l1_score or 0 for r in completed
        ) / len(completed)
        click.echo(f"Average L1 score: {avg_score:.3f}")

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
    repo = EvalRepository(get_session())
    scores = repo.get_agent_scores(agent) if agent else {}

    lines = ["# Evaluation Report\n"]
    lines.append(f"Generated: {datetime.now()}\n\n")
    lines.append(f"Agent: {agent or 'All'}\n\n")

    if scores:
        lines.append("## Dimension Scores\n\n")
        lines.append(
            "| Dimension | Avg L1 Score | Avg Judge Score | Runs |\n"
        )
        lines.append(
            "|-----------|-------------|-----------------|------|\n"
        )
        for dim, data in sorted(scores.items()):
            lines.append(
                f"| {dim} | {data['avg_l1_score'] or 'N/A'} | "
                f"{data['avg_judge_score'] or 'N/A'} | "
                f"{data['run_count']} |\n"
            )
    else:
        lines.append("No results found.\n")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines))
    click.echo(f"Report saved to {out_path}")


if __name__ == "__main__":
    main()
