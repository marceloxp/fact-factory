from __future__ import annotations

import json
import sys
from datetime import datetime

from rich.console import Console
from rich.table import Table

from fact_factory.cli import serialize
from fact_factory.cli.context import is_text_mode
from fact_factory.domain.models import (
    ClearResult,
    Fact,
    FactSummary,
    Gap,
    QueryResult,
    ReindexResult,
    ScoredFact,
    Stats,
)

console = Console()
error_console = Console(file=sys.stderr)


def print_error(message: str) -> None:
    if is_text_mode():
        error_console.print(f"[red]Error:[/red] {message}")
        return
    _print_json({"error": message}, stream=error_console)


def emit_fact_added(fact: Fact) -> None:
    if is_text_mode():
        _text_fact_added(fact)
        return
    _print_json(serialize.fact_dict(fact))


def emit_query_result(result: QueryResult) -> None:
    if is_text_mode():
        _text_query_result(result)
        return
    _print_json(serialize.query_result_dict(result))


def emit_fact_page(
    facts: list[FactSummary],
    page: int,
    page_size: int,
    total: int,
    title: str,
) -> None:
    if is_text_mode():
        _text_fact_page(facts, page, page_size, total, title)
        return
    _print_json(serialize.fact_page_dict(facts, page, page_size, total))


def emit_fact_removed(fact_id: str) -> None:
    if is_text_mode():
        _text_success(f"Fact removed: {fact_id}")
        return
    _print_json({"id": fact_id, "removed": True})


def emit_reindex_result(result: ReindexResult) -> None:
    if is_text_mode():
        _text_reindex_result(result)
        return
    _print_json(serialize.reindex_result_dict(result))


def emit_clear_result(result: ClearResult) -> None:
    if is_text_mode():
        _text_clear_result(result)
        return
    _print_json(serialize.clear_result_dict(result))


def emit_stats(stats: Stats) -> None:
    if is_text_mode():
        _text_stats(stats)
        return
    _print_json(serialize.stats_dict(stats))


def emit_gap_list(gaps: list[Gap]) -> None:
    if is_text_mode():
        _text_gap_list(gaps)
        return
    _print_json({"gaps": [serialize.gap_dict(gap) for gap in gaps]})


def emit_gap(gap: Gap) -> None:
    if is_text_mode():
        _text_gap(gap)
        return
    _print_json(serialize.gap_dict(gap))


def emit_gap_resolved(gap: Gap, fact: Fact) -> None:
    if is_text_mode():
        _text_gap_resolved(gap, fact)
        return
    _print_json({"gap": serialize.gap_dict(gap), "fact": serialize.fact_dict(fact)})


def emit_gap_removed(gap_id: str) -> None:
    if is_text_mode():
        _text_success(f"Gap removed: {gap_id}")
        return
    _print_json({"id": gap_id, "removed": True})


def print_instance_created(path: str) -> None:
    _text_success(f"Created fact-factory instance at {path}")


def _print_json(payload: dict, stream: Console | None = None) -> None:
    line = json.dumps(payload, ensure_ascii=False)
    if stream is error_console:
        print(line, file=sys.stderr)
    else:
        print(line)


def _text_success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def _text_fact_added(fact: Fact) -> None:
    _text_success(f"Fact added: {fact.id}")
    console.print(fact.text)


def _text_reindex_result(result: ReindexResult) -> None:
    _text_success(
        f"Reindexed {result.reindexed} fact(s) with {result.embedding_model}"
    )


def _text_clear_result(result: ClearResult) -> None:
    _text_success(
        "Cleared instance data: "
        f"{result.facts_removed} fact(s), "
        f"{result.gaps_removed} gap(s), "
        f"{result.query_logs_removed} query log(s)"
    )


def _text_query_result(result: QueryResult) -> None:
    if result.facts:
        console.print("[green]Matching facts:[/green]")
        for item in result.facts:
            _text_scored_fact(item)
        return

    console.print("[yellow]No relevant facts found.[/yellow]")
    if result.gap:
        console.print(f"Gap recorded: {result.gap.id}")


def _text_fact_page(
    facts: list[FactSummary],
    page: int,
    page_size: int,
    total: int,
    title: str,
) -> None:
    if total == 0:
        console.print("No facts found.")
        return

    table = Table(title=title)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Created", style="dim")
    table.add_column("Confidence")
    table.add_column("Text")

    for fact in facts:
        table.add_row(
            fact.id,
            _format_datetime(fact.created_at),
            f"{fact.confidence:.2f}",
            _truncate(fact.text, 100),
        )

    console.print(table)
    console.print(_pagination_label(page, page_size, total))


def _text_gap_list(gaps: list[Gap]) -> None:
    if not gaps:
        console.print("No open gaps.")
        return

    table = Table(title="Open Gaps")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Created", style="dim")
    table.add_column("Question")

    for gap in gaps:
        table.add_row(gap.id, _format_datetime(gap.created_at), gap.question)

    console.print(table)


def _text_gap(gap: Gap) -> None:
    console.print(f"[bold]Gap[/bold] {gap.id}")
    console.print(f"Created: {_format_datetime(gap.created_at)}")
    console.print(f"Question: {gap.question}")
    if gap.resolved_at:
        console.print(f"Resolved: {_format_datetime(gap.resolved_at)}")
    if gap.resolved_fact_id:
        console.print(f"Resolved fact: {gap.resolved_fact_id}")


def _text_gap_resolved(gap: Gap, fact: Fact) -> None:
    _text_success(f"Gap resolved: {gap.id}")
    console.print(f"New fact: {fact.id}")
    console.print(fact.text)


def _text_stats(stats: Stats) -> None:
    table = Table(title="Fact-Factory Statistics")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Facts", str(stats.fact_count))
    table.add_row("Gaps (total)", str(stats.gap_count))
    table.add_row("Open gaps", str(stats.open_gaps))
    table.add_row("Resolved gaps", str(stats.resolved_gaps))
    table.add_row("Queries", str(stats.query_count))
    table.add_row("Answered queries", str(stats.answered_queries))
    table.add_row("Unanswered queries", str(stats.unanswered_queries))
    console.print(table)

    if stats.top_queries:
        console.print()
        _text_ranked_list("Top queried subjects", stats.top_queries)

    if stats.top_gap_subjects:
        console.print()
        _text_ranked_list("Top open gap subjects", stats.top_gap_subjects)


def _text_scored_fact(item: ScoredFact) -> None:
    console.print()
    console.print(f"[cyan]{item.fact.id}[/cyan]  score={item.score:.3f}")
    console.print(item.fact.text)


def _text_ranked_list(title: str, items: list[tuple[str, int]]) -> None:
    table = Table(title=title)
    table.add_column("Subject")
    table.add_column("Count", justify="right")
    for subject, count in items:
        table.add_row(subject, str(count))
    console.print(table)


def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _pagination_label(page: int, page_size: int, total: int) -> str:
    if total == 0:
        return "Page 1 of 1 (0 items)"
    start = (page - 1) * page_size + 1
    end = min(page * page_size, total)
    pages = (total + page_size - 1) // page_size
    return f"Page {page} of {pages} ({start}-{end} of {total})"
