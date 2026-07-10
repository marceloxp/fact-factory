# IA-INSTALL — fact-factory installation playbook (for the AI)

> **This file is addressed to you, the AI assistant.** The user pointed you here
> (`@.../templates/IA-INSTALL.md`) so you **install fact-factory and its usage doctrine
> in their project**. Lead the conversation, ask the questions below, and at the end
> **execute each step yourself**. Do not hand instructions back for the user to run
> manually — do it.

## Context you need

Fact-Factory is an offline atomic-fact base queried via the `fact` command. The doctrine
exists so agents **query the base before scanning code**. You will (1) ensure the CLI is
installed on the machine and (2) install the doctrine in the user's project in one or more
**formats**.

Source files (next to this one, in the fact-factory repo):

- **`../README.md`** — official CLI installation/usage (source of truth for Step 2).
- **`../CLAUDE.md`** — full canonical doctrine (reference text).
- **`as-memory/snippet.md`** — condensed snippet for a memory file.
- **`as-agent/fact-factory.md`** — dedicated subagent template.

## Step 1 — Orient yourself (don't ask the obvious)

Before asking anything, discover on your own what you can:

- **Target project root** (the user's project, not this repo).
- **Which platform/assistant** is running (Claude Code, Cursor, etc.). This defines
  where memory files and agents live. Map concepts to your platform: in Claude Code,
  memory is `CLAUDE.md`/`AGENTS.md` at the root and agents live in `.claude/agents/`;
  on others, use the equivalent.
- Whether the project already has a `.fact-factory/` directory.

## Step 2 — Ensure fact-factory is ready to use

`fact --help` working is **not enough**: `add` and `query` generate embeddings via Ollama.
Without Ollama running and the embedding model pulled, the base is not usable (only
`create`/`list` work offline). Cover both fronts — CLI and embedding runtime.
Sources of truth: `../README.md` (CLI install) and **`../OLLAMA.md`** (everything about
Ollama).

**2a — The `fact` CLI:**

1. Check: `fact --help`.
2. If missing, **read `../README.md`** and follow installation (typically
   `uv tool install -e .` from the fact-factory repo, which puts `fact` on PATH).
   **Offer to install yourself** and, with the user's approval, run it. If the environment
   lacks something (e.g. `uv`), follow what the README says.
3. Confirm with `fact --help` before proceeding.

**2b — Embedding runtime (Ollama + model):** follow **`../OLLAMA.md`** — the canonical
document that ensures Ollama responds at the expected URL and the embedding model is
pulled (default `embeddinggemma:latest`, or `embedding_model` from `config.json`).
Complete it through the `/api/embeddings` test. End-to-end validation with `fact`
(which requires a `.fact-factory/` instance) waits for Step 6, after `fact create`.

## Step 3 — Ask which format to install in the project

Offer, one line each:

- **Memory** (recommended, more robust): the doctrine becomes an always-present rule,
  pasted into the project's memory file. Does not depend on a trigger.
- **Dedicated agent**: a subagent the user delegates product questions to; it queries the
  base and answers. Good for isolating retrieval work.
- **Both**: memory enforces the pattern; the agent is an on-demand specialist.

Make clear there is **no** "skill" option on purpose: skills are trigger-driven, and the
mistake the doctrine prevents is an instinct at the start of exploration — too fragile to
depend on a trigger.

## Step 4 — If the user chose the agent, ask for the model

The agent's job is **light retrieval** (query the base, read a few facts, at most one
`grep` when there is a `gap`). Therefore:

- **Present models available on YOUR platform now** — you know the current catalog and
  capabilities; the user does not need to memorize anything. List options with a one-line
  trade-off each (cost/speed vs. capability).
- **Recommend the fast/cheap model** in your line (Haiku/mini/flash class), since this is
  lookup work — and let the user choose.
- **Do not hardcode model names in this flow**: catalogs change over time and vary by
  platform. Decide at install time with what is available.

Record the choice in the agent frontmatter `model:` field.

## Step 5 — Install in the project (do it yourself)

**If memory was chosen:**

1. Locate the memory file at the target project root (`CLAUDE.md` or `AGENTS.md`,
   per platform). Create it if missing.
2. Append content from `as-memory/snippet.md` (the block starting at
   `## Product knowledge base…`; discard the HTML comment at the top).
3. If the user prefers the **full** doctrine instead of the summary, use `../CLAUDE.md`.

**If agent was chosen:**

1. Copy `as-agent/fact-factory.md` to the platform's agent location (in Claude Code:
   `.claude/agents/fact-factory.md`).
2. Fill `model:` with the Step 4 choice and adjust `tools`/`description` if the platform
   requires a different format.

Adapt paths and frontmatter format to the detected platform — doctrine content matters,
not the packaging.

## Step 6 — Verify and confirm

- Confirm files were created/edited and show the user **what** changed.
- If there was no `.fact-factory/` in the project, note the base must be created
  (`fact create`) and populated before it is useful — offer to run `fact create`.
- **End-to-end validation** (pending from Step 2b if there was no instance before): with
  the instance created, run `fact query "test"` and confirm it returns without embedding
  error (facts or `gap` = success). This proves CLI + Ollama + model together.
- End with a one-line summary of what was installed and how the user invokes it.

## Golden rule you are installing (summary)

Query the base with `fact query` before scanning code; **never** use `fact list` for
overview; when you get `gap`, then explore the source and return findings with
`fact add`. The goal is to **avoid** redundant deep discovery — not to forbid legitimate
exploration.
