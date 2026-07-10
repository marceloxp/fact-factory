# fact-factory — Doutrina de uso para agentes de IA

> **Fonte canônica.** Este é o texto-base ("a cola"). Os demais formatos em
> `templates/` (custom agent, trecho de memória) apenas embrulham esta doutrina.
> Ao alterar o comportamento esperado, edite **aqui** e propague.

## O que é

Fact-Factory é uma base de conhecimento **offline** de **fatos atômicos** sobre um
produto — código-fonte, banco de dados, regras de negócio, operação. Ela existe para
você **consultar antes** de varrer código ou banco. Um projeto tem uma instância
quando existe um diretório `.fact-factory/`. A interface é o comando `fact`.

## A regra de ouro

**Pergunte, não liste.** Recupere por intenção com `fact query "<pergunta específica>"`.
**Nunca** use `fact list` para "ter uma visão geral": em produção há milhares de fatos
de centenas de assuntos; listar não cabe no contexto e devolve tudo sem relevância —
exatamente o problema que a ferramenta resolve. `list` é o equivalente a ler o código
inteiro para "entender o sistema".

**Princípio: evitar a busca profunda, não proibi-la.** O que a doutrina pede que você
**evite** é varrer o código-fonte ou o banco à procura de fatos que a base já responde
de graça — não é uma proibição de explorar. Quando a base não sabe (retorna `gap`) ou o
assunto é genuinamente novo, ir a fundo na fonte é exatamente o certo. A doutrina poupa
trabalho redundante; não amarra suas mãos. (Isto é diferente da regra dura acima: para
`fact list` como "visão geral" a resposta é sempre não.)

## Fluxo de trabalho

1. **Decomponha** a tarefa em perguntas concretas ("qual tabela guarda X?", "qual a
   regra de comissão?", "onde começa o fluxo Y?"). Sem intenção específica não há o
   que recuperar bem — nem aqui, nem no código.
2. **Consulte** cada pergunta: `fact query "..."`.
3. **Leia** os fatos retornados. Vêm rankeados por `score`, acima do limiar de
   relevância. São curados — trate-os como verdade de base.
4. **Decida pelo resultado:**
   - **Veio fato(s):** use-os. Não re-derive do código o que a base já afirma, salvo
     motivo claro para desconfiar.
   - **Veio `gap`** (`"facts": []`): a ferramenta registrou automaticamente uma
     lacuna. **Esse é o sinal** de que a base não sabe — agora sim vá ao código/banco
     investigar.
5. **Devolva o aprendizado** (opcional, mas é o que torna a base mais inteligente): ao
   descobrir a resposta explorando, grave-a com `fact add` — ou `fact gap resolve`
   para fechar a lacuna que você acabou de responder. O próximo agente encontra por
   `query` e não repete a exploração.

## O ciclo virtuoso

```
query  ──▶  (se gap)  ──▶  explorar código/banco  ──▶  fact add  ──▶  próximo query acha
```

Cada exploração alimenta a base e reduz o trabalho da próxima sessão.

## Papel de cada comando

- **`query`** — operação principal. Busca **semântica** por intenção.
- **`search`** — só quando você já sabe o **termo exato** (nome de tabela, classe,
  flag). Match de texto plano.
- **`list`** — inspeção/manutenção da base apenas. **Nunca** para entender o sistema.
- **`gap`** — backlog de perguntas sem resposta; o que a base ainda precisa aprender.
- **`add` / `remove` / `stats`** — manutenção e métricas.

## Anti-padrões (não faça)

- ❌ `fact list` para "pegar o contexto geral".
- ❌ Despejar a base inteira no contexto.
- ❌ Ignorar um fato retornado e re-derivar do zero sem motivo.
- ❌ Inventar resposta quando o resultado foi `gap` — vá verificar na fonte.
- ❌ Consultar com pergunta vaga ("como funciona o sistema?") — refine a intenção.

## Referência rápida de comandos

| Comando                                                | Uso                                                                        |
| ------------------------------------------------------ | -------------------------------------------------------------------------- |
| `fact query "<pergunta>"`                              | Busca semântica; retorna fatos **ou** cria um gap.                         |
| `fact search "<termo>"`                                | Busca por texto plano (termo exato).                                       |
| `fact add "<fato>" [--confidence 0..1] [--tags a,b,c]` | Adiciona fato (confidence padrão `1.0`).                                   |
| `fact gap list \| resolve \| remove`                   | Gerencia lacunas (`resolve` cria fato e fecha; `remove` só em gap aberto). |
| `fact list [PAGE]`                                     | Lista paginada (20/página). **Manutenção apenas.**                         |
| `fact remove <uuid>`                                   | Remove fato por UUID.                                                      |
| `fact stats`                                           | Métricas de uso (fatos, gaps, queries).                                    |

**Saída:** JSON no `stdout` por padrão; use `--text` para tabela legível. Erros vão ao
`stderr` como `{"error": "..."}` com exit code `1`.
