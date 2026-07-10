<!--
  Snippet to paste into the target project's CLAUDE.md or AGENTS.md.
  Paste only the block below (from "## Product knowledge base" onward).
  Canonical doctrine source: CLAUDE.md at the fact-factory repo root.
-->

## Product knowledge base (fact-factory)

This project has an **atomic-fact** base queried via the `fact` command
(a `.fact-factory/` directory exists). **Before** scanning code or the database to
understand the product, query the base.

- Use **`fact query "<specific question>"`** — semantic search by intent. This is the
  primary operation.
- **Never** use `fact list` for an overview: it does not scale to thousands of facts and
  returns everything without relevance. `list` is maintenance only.
- If `query` returns `gap` (`"facts": []`), the base **does not know**: only then
  investigate the source. When you find the answer, record with **`fact add "<fact>"`** so
  the next agent can find it.
- `fact search "<term>"` only when you know the **exact term** (table, class, flag).

**Avoid deep discovery, don't forbid it.** What to avoid is scanning code/database for
facts the base already answers for free — not blocking exploration. When there is `gap`
or the topic is new, going deep into the source is right.

**Flow:** break the task into questions → `query` each → use the facts (curated,
trustworthy) → go to code only when there is `gap` → return what you learned with
`fact add`.
