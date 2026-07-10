# OLLAMA — Garantir o runtime de embeddings (para a IA)

- URL padrão do Ollama: `http://localhost:11434`
- Modelo de embedding padrão do fact-factory: `qwen3-embedding:0.6b`.

## Testando o embedding

```bash
curl -fsS http://localhost:11434/api/embeddings \
    -H "Content-Type: application/json" \
    -d '{"model": "qwen3-embedding:0.6b", "prompt": "test"}'
```

## Instalação do Ollama

Instale se o comando `ollama` não existir (escolha pelo SO):

| SO            | Comando                                          |
| ------------- | ------------------------------------------------ |
| Linux / macOS | `curl -fsSL https://ollama.com/install.sh \| sh` |
| Windows       | `irm https://ollama.com/install.ps1 \| iex`      |

## Subindo o servidor Ollama

```bash
ollama serve
```

## Baixar o modelo - caso não exista

```bash
ollama pull qwen3-embedding:0.6b
```

## Host/porta/modelo diferentes

Talvez o usuário tenha um Ollama com configurações fora do padrão, se você
não conseguir resolver sozinho de maneira rápida, pergunte ao usuário.
