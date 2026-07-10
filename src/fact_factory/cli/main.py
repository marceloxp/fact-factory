from __future__ import annotations

from functools import wraps
from pathlib import Path

import typer

from fact_factory.app import build_context, create_instance, locate_instance
from fact_factory.cli import output
from fact_factory.cli.context import set_text_mode
from fact_factory.domain.exceptions import FactFactoryError

TEXT_OUTPUT = typer.Option(
    False,
    "--text",
    help="Human-readable output instead of JSON.",
)
FORCE_OPTION = typer.Option(
    False,
    "--force",
    help="Permanently delete the record.",
)

app = typer.Typer(
    name="fact",
    help="Atomic fact storage and retrieval for AI assistants.",
    no_args_is_help=True,
)
gap_app = typer.Typer(help="Manage knowledge gaps.")
app.add_typer(gap_app, name="gap")


def _use_text_mode(text_output: bool) -> None:
    set_text_mode(text_output)


def _handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        text_output = kwargs.pop("text_output", False)
        _use_text_mode(text_output)
        try:
            return func(*args, **kwargs)
        except FactFactoryError as exc:
            output.print_error(str(exc))
            raise typer.Exit(code=1) from exc

    return wrapper


@app.command("create")
@_handle_errors
def create(
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Create a new fact-factory instance in the current directory."""
    instance_dir = create_instance(Path.cwd())
    output.print_instance_created(str(instance_dir))


@app.command("add")
@_handle_errors
def add(
    fact_texts: list[str] = typer.Argument(
        ...,
        help="One or more fact texts to store.",
    ),
    confidence: float = typer.Option(1.0, "--confidence", "-c", min=0.0, max=1.0),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Add one or more facts to the knowledge base."""
    ctx = build_context(locate_instance())
    tag_list = _parse_tags(tags)
    facts = ctx.fact_service.add_facts(
        texts=fact_texts,
        confidence=confidence,
        tags=tag_list,
    )
    output.emit_facts_added(facts)


@app.command("query")
@_handle_errors
def query(
    question: str = typer.Argument(..., help="Question to search for."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Query the knowledge base using semantic search."""
    ctx = build_context(locate_instance())
    result = ctx.query_service.query(question)
    output.emit_query_result(result)


@app.command("search")
@_handle_errors
def search(
    term: str = typer.Argument(..., help="Text to search for."),
    page: int = typer.Argument(1, min=1, help="Page number."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Search facts by plain text."""
    ctx = build_context(locate_instance())
    facts, total = ctx.fact_repo.search(term, page, ctx.config.page_size)
    output.emit_fact_page(
        facts=facts,
        page=page,
        page_size=ctx.config.page_size,
        total=total,
        title=f"Search results for '{term}'",
    )


@app.command("list")
@_handle_errors
def list_facts(
    page: int = typer.Argument(1, min=1, help="Page number."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """List stored facts."""
    ctx = build_context(locate_instance())
    facts, total = ctx.fact_repo.list_page(page, ctx.config.page_size)
    output.emit_fact_page(
        facts=facts,
        page=page,
        page_size=ctx.config.page_size,
        total=total,
        title="Facts",
    )


@app.command("remove")
@_handle_errors
def remove(
    fact_id: str = typer.Argument(..., help="Fact UUID."),
    force: bool = FORCE_OPTION,
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Remove a fact by UUID (soft-delete by default)."""
    ctx = build_context(locate_instance())
    ctx.fact_service.remove_fact(fact_id, force=force)
    output.emit_fact_removed(fact_id, permanent=force)


@app.command("reindex")
@_handle_errors
def reindex(
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Re-embed all facts using the configured embedding model."""
    ctx = build_context(locate_instance())
    result = ctx.fact_service.reindex_facts(ctx.config.embedding_model)
    output.emit_reindex_result(result)


@app.command("clear")
@_handle_errors
def clear(
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Remove all facts, gaps, and query logs from the instance."""
    typer.confirm(
        "This permanently deletes all facts, gaps, and query logs. Continue?",
        abort=True,
    )
    ctx = build_context(locate_instance())
    result = ctx.clear_service.clear_all()
    output.emit_clear_result(result)


@app.command("stats")
@_handle_errors
def stats(
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Show usage statistics."""
    ctx = build_context(locate_instance())
    output.emit_stats(ctx.stats_service.get_stats())


@gap_app.command("list")
@_handle_errors
def gap_list(
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """List open gaps."""
    ctx = build_context(locate_instance())
    output.emit_gap_list(ctx.gap_service.list_open())


@gap_app.command("show")
@_handle_errors
def gap_show(
    gap_id: str = typer.Argument(..., help="Gap UUID."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Show gap details."""
    ctx = build_context(locate_instance())
    output.emit_gap(ctx.gap_service.show(gap_id))


@gap_app.command("resolve")
@_handle_errors
def gap_resolve(
    gap_id: str = typer.Argument(..., help="Gap UUID."),
    fact_text: str = typer.Argument(..., help="Fact text that resolves the gap."),
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Resolve a gap by creating a new fact."""
    ctx = build_context(locate_instance())
    gap, fact = ctx.gap_service.resolve(gap_id, fact_text)
    output.emit_gap_resolved(gap, fact)


@gap_app.command("remove")
@_handle_errors
def gap_remove(
    gap_id: str = typer.Argument(..., help="Gap UUID."),
    force: bool = FORCE_OPTION,
    text_output: bool = TEXT_OUTPUT,
) -> None:
    """Remove an open gap (soft-delete by default)."""
    ctx = build_context(locate_instance())
    ctx.gap_service.remove(gap_id, force=force)
    output.emit_gap_removed(gap_id, permanent=force)


def _parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


__all__ = ["app"]
