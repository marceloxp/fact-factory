# fact-factory — Usage doctrine for AI agents

> **Canonical source.** This is the base text ("the glue"). Other formats in
> `templates/` (custom agent, memory snippet) only wrap this doctrine.
> When changing expected behavior, edit **here** and propagate.

## What it is

Fact-Factory is an **offline** knowledge base of **atomic facts** about a
product — source code, database, business rules, operations. It exists so you
**query before** scanning code or the database. A project has an instance
when a `.fact-factory/` directory exists. The interface is the `fact` command.

## The golden rule

**Ask, don't list.** Retrieve by intent with `fact query "<specific question>"`.
**Never** use `fact list` to "get an overview": in production there are thousands of facts
across hundreds of topics; listing does not fit in context and returns everything without
relevance — exactly the problem this tool solves. `list` is the equivalent of reading the
entire codebase to "understand the system".

**Principle: avoid deep discovery, don't forbid it.** What the doctrine asks you to
**avoid** is scanning source code or the database for facts the base already answers
for free — it is not a ban on exploration. When the base does not know (returns `gap`) or
the topic is genuinely new, going deep into the source is exactly right. The doctrine saves
redundant work; it does not tie your hands. (This is different from the hard rule above:
for `fact list` as "overview" the answer is always no.)

## Workflow

1. **Break down** the task into concrete questions ("which table stores X?", "what is the
   commission rule?", "where does flow Y start?"). Without specific intent there is nothing
   to retrieve well — neither here nor in the code.
2. **Query** each question: `fact query "..."`.
3. **Read** the returned facts. They come ranked by `score`, above the relevance
   threshold. They are curated — treat them as baseline truth.
4. **Decide from the result:**
   - **Fact(s) returned:** use them. Do not re-derive from code what the base already states,
     unless you have a clear reason to doubt.
   - **`gap` returned** (`"facts": []`): the tool automatically recorded a
     gap. **That is the signal** that the base does not know — now go investigate in
     code/database.
5. **Give back what you learned** (optional, but what makes the base smarter): when you
   discover the answer by exploring, record it with `fact add` — or `fact gap resolve`
   to close the gap you just answered. The next agent finds it via `query` and does not
   repeat the exploration.

## The virtuous cycle

```
query  ──▶  (if gap)  ──▶  explore code/database  ──▶  fact add  ──▶  next query finds it
```

Each exploration feeds the base and reduces work for the next session.

## Role of each command

- **`query`** — primary operation. **Semantic** search by intent.
- **`search`** — only when you already know the **exact term** (table name, class,
  flag). Plain-text match.
- **`list`** — base inspection/maintenance only. **Never** to understand the system.
- **`gap`** — backlog of unanswered questions; what the base still needs to learn.
- **`add` / `remove` / `stats`** — maintenance and metrics.

## Anti-patterns (do not do)

- ❌ `fact list` to "get general context".
- ❌ Dumping the entire base into context.
- ❌ Ignoring a returned fact and re-deriving from scratch without reason.
- ❌ Inventing an answer when the result was `gap` — go verify at the source.
- ❌ Querying with a vague question ("how does the system work?") — refine intent.

## Quick command reference

| Command                                                | Usage                                                                      |
| ------------------------------------------------------ | -------------------------------------------------------------------------- |
| `fact query "<question>"`                              | Semantic search; returns facts **or** creates a gap.                       |
| `fact search "<term>"`                                 | Plain-text search (exact term).                                            |
| `fact add "<fact>" [--confidence 0..1] [--tags a,b,c]` | Add fact (default confidence `1.0`).                                         |
| `fact gap list \| resolve \| remove`                   | Manage gaps (`resolve` creates fact and closes; `remove` only on open gap). |
| `fact list [PAGE]`                                     | Paginated list (20/page). **Maintenance only.**                            |
| `fact remove <uuid>`                                   | Remove fact by UUID.                                                       |
| `fact stats`                                           | Usage metrics (facts, gaps, queries).                                      |

**Output:** JSON on `stdout` by default; use `--text` for readable tables. Errors go to
`stderr` as `{"error": "..."}` with exit code `1`.
