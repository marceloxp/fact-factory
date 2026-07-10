# IA-INSTALL — Playbook de instalação do fact-factory (para a IA)

> **Este arquivo é dirigido a você, assistente de IA.** O usuário apontou você para cá
> (`@.../templates/IA-INSTALL.md`) para que você **instale o fact-factory e a sua
> doutrina de uso no projeto dele**. Conduza a conversa, faça as perguntas abaixo e, ao
> final, **execute você mesmo** cada etapa. Não devolva instruções para o usuário fazer
> à mão — faça.

## Contexto que você precisa ter

O fact-factory é uma base offline de fatos atômicos consultável pelo comando `fact`. A
doutrina existe para que agentes **consultem a base antes de varrer o código**. Você vai
(1) garantir que a CLI está instalada na máquina e (2) instalar a doutrina no projeto do
usuário em um ou mais **formatos**.

Arquivos de origem (ao lado deste, no repo do fact-factory):

- **`../README.md`** — instalação/uso oficial da CLI (fonte da verdade para o Passo 2).
- **`../CLAUDE.md`** — a doutrina canônica completa (texto de referência).
- **`as-memory/snippet.md`** — trecho condensado para arquivo de memória.
- **`as-agent/fact-factory.md`** — template de subagente dedicado.

## Passo 1 — Situe-se (sem perguntar o óbvio)

Antes de perguntar qualquer coisa, descubra sozinho o que der:

- **Qual é a raiz do projeto-alvo** (o projeto do usuário, não este repo).
- **Qual plataforma/assistente** está rodando (Claude Code, Cursor, etc.). Isso define
  onde ficam o arquivo de memória e os agentes. Mapeie os conceitos para a sua
  plataforma: em Claude Code, memória é `CLAUDE.md`/`AGENTS.md` na raiz e agentes ficam
  em `.claude/agents/`; em outras, use o equivalente.
- Se o projeto já tem um diretório `.fact-factory/`.

## Passo 2 — Garanta que o fact-factory está pronto para uso

O `fact --help` funcionar **não basta**: `add` e `query` geram embeddings via Ollama.
Sem Ollama no ar e o modelo de embedding baixado, a base não é utilizável (apenas
`create`/`list` funcionam offline). Cubra as duas frentes — CLI e runtime de embeddings.
Fontes da verdade: `../README.md` (instalação da CLI) e **`../OLLAMA.md`** (tudo sobre
o Ollama).

**2a — A CLI `fact`:**

1. Verifique: `fact --help`.
2. Se faltar, **leia o `../README.md`** e siga a instalação (tipicamente
   `uv tool install -e .` a partir do repo do fact-factory, que coloca `fact` no PATH).
   **Ofereça instalar você mesmo** e, com o aval do usuário, execute. Se o ambiente
   faltar algo (ex.: `uv`), siga o que o README orienta.
3. Confirme com `fact --help` antes de prosseguir.

**2b — O runtime de embeddings (Ollama + modelo):** siga o **`../OLLAMA.md`** — documento
canônico que garante o Ollama respondendo na URL esperada e o modelo de embedding
baixado (padrão `qwen3-embedding:0.6b`, ou o `embedding_model` do `config.json`).
Conclua-o até o teste de `/api/embeddings`. A validação ponta a ponta com o `fact`
(que exige uma instância `.fact-factory/`) fica para o Passo 6, após o `fact create`.

## Passo 3 — Pergunte qual formato instalar no projeto

Ofereça, com uma linha cada:

- **Memória** (recomendado, mais robusto): a doutrina vira regra sempre presente,
  colada no arquivo de memória do projeto. Não depende de gatilho.
- **Agente dedicado**: um subagente para o qual o usuário delega perguntas sobre o
  produto; consulta a base e responde. Bom para isolar o trabalho de recuperação.
- **Ambos**: memória garante o padrão; o agente é um especialista sob demanda.

Deixe claro que **não** há opção "skill" de propósito: skills são acionadas por gatilho,
e o erro que a doutrina previne é um instinto no início da exploração — frágil demais
para depender de gatilho.

## Passo 4 — Se o usuário escolher o agente, pergunte o modelo

A tarefa do agente é **recuperação leve** (consultar a base, ler poucos fatos, no
máximo um `grep` quando houver `gap`). Portanto:

- **Apresente os modelos disponíveis na SUA plataforma agora** — você conhece o catálogo
  atual e as capacidades; o usuário não precisa decorar nada. Liste as opções com uma
  linha de trade-off cada (custo/velocidade vs. capacidade).
- **Recomende o modelo rápido/econômico** da sua linha (classe "Haiku"/mini/flash), por
  ser tarefa de lookup — e deixe o usuário escolher.
- **Não fixe nomes de modelo neste fluxo**: o catálogo muda com o tempo e varia por
  plataforma. Decida no momento da instalação, com o que estiver disponível.

Grave a escolha no campo `model:` do frontmatter do agente.

## Passo 5 — Instale no projeto (faça você mesmo)

**Se escolheu memória:**

1. Localize o arquivo de memória na raiz do projeto-alvo (`CLAUDE.md` ou `AGENTS.md`,
   conforme a plataforma). Se não existir, crie.
2. Anexe o conteúdo de `as-memory/snippet.md` (o bloco a partir de
   `## Base de conhecimento…`; descarte o comentário HTML do topo).
3. Se o usuário preferir a doutrina **completa** em vez do resumo, use `../CLAUDE.md`.

**Se escolheu agente:**

1. Copie `as-agent/fact-factory.md` para o local de agentes da plataforma (em Claude
   Code: `.claude/agents/fact-factory.md`).
2. Preencha o `model:` com a escolha do Passo 4 e ajuste `tools`/`description` se a
   plataforma exigir formato diferente.

Adapte caminhos e formato de frontmatter à plataforma detectada — o conteúdo da doutrina
é o que importa, não a embalagem.

## Passo 6 — Verifique e confirme

- Confirme que os arquivos foram criados/editados e mostre ao usuário **o que** mudou.
- Se não havia `.fact-factory/` no projeto, avise que a base precisa ser criada
  (`fact create`) e populada antes de ser útil — ofereça rodar `fact create`.
- **Validação ponta a ponta** (a que ficou pendente do Passo 2b, se não havia instância
  antes): com a instância criada, rode `fact query "teste"` e confirme que retorna sem
  erro de embedding (fatos ou `gap` = sucesso). Isso prova CLI + Ollama + modelo juntos.
- Encerre com um resumo de uma linha do que foi instalado e como o usuário aciona.

## Regra de ouro que você está instalando (resumo)

Perguntar à base com `fact query` antes de varrer o código; **nunca** usar `fact list`
para visão geral; ao receber `gap`, aí sim explorar a fonte e devolver o achado com
`fact add`. O objetivo é **evitar** a busca profunda redundante — não proibir a
exploração legítima.
