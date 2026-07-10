#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <gemma|qwen>" >&2
  echo "  gemma  - run benchmark with embeddinggemma:latest" >&2
  echo "  qwen   - run benchmark with qwen3-embedding:0.6b" >&2
  exit 1
}

MODEL_KEY="${1:-}"
[[ -n "$MODEL_KEY" ]] || usage
[[ "$MODEL_KEY" == "gemma" || "$MODEL_KEY" == "qwen" ]] || usage

ROOT="$(cd "$(dirname "$0")" && pwd)"
BENCHMARK_JSON="$ROOT/benchmark.json"
RESULTS_DIR="$ROOT/benchmark-results"
TEST_DIR="/tmp/fact-test/${MODEL_KEY}"

if ! command -v fact >/dev/null 2>&1; then
  echo "error: 'fact' command not found on PATH" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 is required" >&2
  exit 1
fi

mkdir -p "$RESULTS_DIR"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"

export ROOT BENCHMARK_JSON RESULTS_DIR TEST_DIR MODEL_KEY

python3 <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(os.environ["ROOT"])
BENCHMARK_JSON = Path(os.environ["BENCHMARK_JSON"])
RESULTS_DIR = Path(os.environ["RESULTS_DIR"])
TEST_DIR = Path(os.environ["TEST_DIR"])
MODEL_KEY = os.environ["MODEL_KEY"]

benchmark = json.loads(BENCHMARK_JSON.read_text(encoding="utf-8"))
embedding_model = benchmark["models"][MODEL_KEY]
facts = benchmark["facts"]
queries = benchmark["queries"]

fact_text_by_id = {item["id"]: item["text"] for item in facts}


def run_fact(args: list[str], cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["fact", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_json(stdout: str) -> dict:
    return json.loads(stdout)


def update_config_model(instance_dir: Path, model: str) -> None:
    config_path = instance_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["embedding_model"] = model
    config_path.write_text(json.dumps(config, indent=4) + "\n", encoding="utf-8")


def expected_texts(expected_ids: list[str]) -> list[str]:
    return [fact_text_by_id[item_id] for item_id in expected_ids]


def evaluate_hits(returned_texts: list[str], expected_ids: list[str]) -> dict:
    expected = expected_texts(expected_ids)
    hit_at_1 = bool(returned_texts[:1]) and returned_texts[0] in expected
    hit_at_3 = any(text in expected for text in returned_texts[:3])
    return {
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
    }


started_at = datetime.now(timezone.utc)
overall_start = perf_counter()

print(f"model: {MODEL_KEY} ({embedding_model})")
print(f"test dir: {TEST_DIR}")

create_code, _, create_err = run_fact(["create"], TEST_DIR)
if create_code != 0:
    print(create_err, file=sys.stderr)
    sys.exit(create_code)

update_config_model(TEST_DIR / ".fact-factory", embedding_model)

warm_code, _, warm_err = run_fact(["add", "warm-up fact for embedding model"], TEST_DIR)
if warm_code != 0:
    print(warm_err, file=sys.stderr)
    sys.exit(warm_code)

add_items: list[dict] = []
add_total_seconds = 0.0

for fact in facts:
    start = perf_counter()
    code, stdout, stderr = run_fact(["add", fact["text"]], TEST_DIR)
    elapsed = perf_counter() - start
    add_total_seconds += elapsed

    if code != 0:
        print(stderr, file=sys.stderr)
        sys.exit(code)

    payload = parse_json(stdout)
    add_items.append(
        {
            "benchmark_id": fact["id"],
            "seconds": round(elapsed, 4),
            "fact_id": payload["id"],
            "text": payload["text"],
        }
    )
    print(f"added {fact['id']} ({elapsed:.2f}s)")

query_items: list[dict] = []
query_total_seconds = 0.0
hits_at_1 = 0
hits_at_3 = 0
gaps = 0

for query in queries:
    start = perf_counter()
    code, stdout, stderr = run_fact(["query", query["question"]], TEST_DIR)
    elapsed = perf_counter() - start
    query_total_seconds += elapsed

    if code != 0:
        print(stderr, file=sys.stderr)
        sys.exit(code)

    payload = parse_json(stdout)
    returned_facts = payload.get("facts", [])
    returned_texts = [item["text"] for item in returned_facts]
    returned_scores = [item["score"] for item in returned_facts]
    result_type = "gap" if payload.get("gap") else "fact"
    if result_type == "gap":
        gaps += 1

    hits = evaluate_hits(returned_texts, query["expected_fact_ids"])
    hits_at_1 += int(hits["hit_at_1"])
    hits_at_3 += int(hits["hit_at_3"])

    query_items.append(
        {
            "benchmark_id": query["id"],
            "question": query["question"],
            "expected_fact_ids": query["expected_fact_ids"],
            "expected_texts": expected_texts(query["expected_fact_ids"]),
            "seconds": round(elapsed, 4),
            "result_type": result_type,
            "hit_at_1": hits["hit_at_1"],
            "hit_at_3": hits["hit_at_3"],
            "top_fact_texts": returned_texts[:3],
            "top_scores": returned_scores[:3],
            "raw": payload,
        }
    )
    mark = "HIT" if hits["hit_at_1"] else ("hit@3" if hits["hit_at_3"] else ("GAP" if result_type == "gap" else "MISS"))
    print(f"query {query['id']}: {mark} ({elapsed:.2f}s)")

finished_at = datetime.now(timezone.utc)
overall_seconds = perf_counter() - overall_start
timestamp = started_at.strftime("%Y%m%d-%H%M%S")

result = {
    "model_key": MODEL_KEY,
    "embedding_model": embedding_model,
    "started_at": started_at.isoformat(),
    "finished_at": finished_at.isoformat(),
    "total_seconds": round(overall_seconds, 4),
    "test_dir": str(TEST_DIR),
    "facts": {
        "count": len(add_items),
        "total_seconds": round(add_total_seconds, 4),
        "items": add_items,
    },
    "queries": {
        "count": len(query_items),
        "total_seconds": round(query_total_seconds, 4),
        "items": query_items,
    },
    "summary": {
        "hits_at_1": hits_at_1,
        "hits_at_3": hits_at_3,
        "gaps": gaps,
        "misses": len(query_items) - hits_at_3,
        "add_total_seconds": round(add_total_seconds, 4),
        "query_total_seconds": round(query_total_seconds, 4),
    },
}

output_path = RESULTS_DIR / f"{MODEL_KEY}-{timestamp}.json"
latest_path = RESULTS_DIR / f"{MODEL_KEY}-latest.json"
encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
output_path.write_text(encoded, encoding="utf-8")
latest_path.write_text(encoded, encoding="utf-8")

print()
print(f"results: {output_path}")
print(f"latest:  {latest_path}")
print(
    "summary: "
    f"hit@1={hits_at_1}/{len(query_items)}, "
    f"hit@3={hits_at_3}/{len(query_items)}, "
    f"gaps={gaps}, "
    f"add={add_total_seconds:.2f}s, "
    f"query={query_total_seconds:.2f}s, "
    f"total={overall_seconds:.2f}s"
)
PY
