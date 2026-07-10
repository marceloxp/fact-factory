# Fact-Factory

Atomic fact storage and retrieval for AI assistants. Fact-Factory lets agents query consolidated project knowledge before running deep discovery against code, databases, or documentation.

The system runs fully offline using local embedding models through [Ollama](https://ollama.com/).

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally

Pull the default embedding model:

```bash
ollama pull qwen3-embedding:0.6b
```

> Ollama must be running whenever you `add` or `query` — both generate embeddings.
> `fact create` and `fact list` work offline; `add`/`query` will fail if Ollama is down
> or the embedding model is not pulled.
>
> See **[OLLAMA.md](OLLAMA.md)** for a complete setup/verification guide (install per OS,
> start the server, pull the model, and a `curl` test against `/api/embeddings`).

## Installation

```bash
git clone <repository-url>
cd fact-factory
uv sync
```

> Already inside a local checkout (e.g. an assistant following `templates/IA-INSTALL.md`)?
> Skip the clone and run the commands below from the repository root.

Install the `fact` command globally (recommended):

```bash
uv tool install -e .
```

This places `fact` on your PATH (typically `~/.local/bin/fact`). Ensure that directory is in your PATH.

For development without a global install, use `uv run fact` instead of `fact`.

Verify:

```bash
fact --help
```

By default, `add`, `query`, `search`, `list`, `remove`, `stats`, and `gap` commands print **JSON** to stdout. Use `--text` for human-readable tables:

```bash
fact list 1 --text
fact stats --text
```

## Quick start

Create an instance in your project:

```bash
cd /path/to/your-project
fact create
```

This creates:

```text
.fact-factory/
├── facts.db
└── config.json
```

Add facts (English or Portuguese):

```bash
fact add "A manual cannot be edited after creation."
fact add "User permissions are resolved through company_roles and company_permissions."
```

Query the knowledge base:

```bash
fact query "How does manual editing work?"
```

If no relevant facts are found, a gap is recorded automatically.

## Instance discovery

Fact-Factory locates the knowledge base automatically, similar to how Git finds `.git`:

1. Walk up from the current directory looking for `.fact-factory/`.
2. Stop at `$HOME` and fall back to `~/.fact-factory/`.

You normally do not need to specify which instance to use.

## Configuration

Each instance has a `config.json` file:

```json
{
    "embedding_model": "qwen3-embedding:0.6b",
    "ollama_base_url": "http://localhost:11434",
    "top_k": 10,
    "min_relevance_score": 0.65,
    "page_size": 20
}
```

- `min_relevance_score` controls when a query is considered answered vs. when a gap is created.
- Fact and query text may be in English or Portuguese.

## CLI reference

| Command | Description |
|---------|-------------|
| `fact create` | Create a new instance in the current directory |
| `fact add "..."` | Add a fact (`--confidence`, `--tags`) |
| `fact query "..."` | Semantic search with hybrid re-ranking |
| `fact search "term" [page]` | Plain-text search |
| `fact list [page]` | List facts |
| `fact remove <uuid>` | Remove a fact by UUID |
| `fact stats` | Usage statistics |
| `fact gap list` | List open gaps |
| `fact gap show <uuid>` | Show gap details |
| `fact gap resolve <uuid> "fact text"` | Resolve a gap by adding a fact |
| `fact gap remove <uuid>` | Remove an open gap |

## Agent workflow

1. Before deep discovery, run `fact query "<question>"`.
2. If relevant facts are returned, use them in reasoning.
3. If a gap is created, continue investigation as usual.
4. After finding the answer, resolve the gap and add new facts:

```bash
fact gap resolve <gap-uuid> "The discovered fact."
fact add "Another atomic fact about the system."
```

This keeps the knowledge base growing as the project is explored.

## Agent setup

Fact-Factory includes docs and templates so AI assistants adopt the right workflow
(query before deep discovery, never use `list` for orientation, feed gaps back with
`fact add`).

| Resource | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | Canonical agent doctrine (full reference) |
| [templates/IA-INSTALL.md](templates/IA-INSTALL.md) | Step-by-step playbook for an assistant to install the CLI and doctrine in a target project |
| [templates/as-memory/snippet.md](templates/as-memory/snippet.md) | Short block to paste into the target project's `CLAUDE.md` or `AGENTS.md` |
| [templates/as-agent/fact-factory.md](templates/as-agent/fact-factory.md) | Dedicated subagent template for fact retrieval |

To bootstrap a project: point your assistant at `templates/IA-INSTALL.md` (e.g.
`@templates/IA-INSTALL.md`) and let it run the install steps. After `fact create`
and initial facts are in place, agents should use `fact query` as their first move
on any unfamiliar topic.

## Architecture

- **Domain:** business logic (facts, queries, gaps, stats)
- **Infrastructure:** SQLite, Ollama, instance discovery
- **CLI:** Typer adapter over domain services

Future interfaces (HTTP server, MCP, IDE extensions) can reuse the same domain layer.

## License

MIT — see [LICENSE](LICENSE).
