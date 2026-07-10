# OLLAMA — Ensure the embedding runtime (for the AI)

- Default Ollama URL: `http://localhost:11434`
- Default fact-factory embedding model: `qwen3-embedding:0.6b`.

## Testing embeddings

```bash
curl -fsS http://localhost:11434/api/embeddings \
    -H "Content-Type: application/json" \
    -d '{"model": "qwen3-embedding:0.6b", "prompt": "test"}'
```

## Installing Ollama

Install if the `ollama` command is missing (choose by OS):

| OS            | Command                                          |
| ------------- | ------------------------------------------------ |
| Linux / macOS | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Windows       | `irm https://ollama.com/install.ps1 \| iex`      |

## Starting the Ollama server

```bash
ollama serve
```

## Pull the model — if missing

```bash
ollama pull qwen3-embedding:0.6b
```

## Different host/port/model

The user may have Ollama configured outside defaults. If you cannot resolve it quickly
on your own, ask the user.
