<!--
  Trecho para colar em CLAUDE.md ou AGENTS.md do projeto-alvo.
  Cole apenas o bloco abaixo (do "## Base de conhecimento" em diante).
  Fonte canônica da doutrina: CLAUDE.md na raiz do repo do fact-factory.
-->

## Base de conhecimento do produto (fact-factory)

Este projeto tem uma base de **fatos atômicos** consultável pelo comando `fact`
(há um diretório `.fact-factory/`). **Antes** de varrer código ou banco para entender
o produto, pergunte à base.

- Use **`fact query "<pergunta específica>"`** — busca semântica por intenção. É a
  operação principal.
- **Nunca** use `fact list` para ter visão geral: não escala a milhares de fatos e
  devolve tudo sem relevância. `list` é só manutenção.
- Se `query` retornar `gap` (`"facts": []`), a base **não sabe**: só então investigue
  a fonte. Ao descobrir, grave com **`fact add "<fato>"`** para o próximo agente achar.
- `fact search "<termo>"` apenas quando souber o **termo exato** (tabela, classe, flag).

**Evite a busca profunda, não a proíba.** O que se quer evitar é varrer código/banco
por fatos que a base já responde de graça — não impedir a exploração. Quando há `gap`
ou o assunto é novo, ir a fundo na fonte é o certo.

**Fluxo:** decomponha a tarefa em perguntas → `query` cada uma → use os fatos (curados,
confiáveis) → vá ao código apenas quando houver `gap` → devolva o aprendizado com
`fact add`.
