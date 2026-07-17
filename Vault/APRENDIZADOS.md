---
tags:
  - moc
  - home
aliases:
  - Home
  - Índice
  - Mapa Geral
cssclasses:
  - wide-page
---

# 🧠 APRENDIZADOS — Vault do projeto `density`

> [!abstract] O que é isto
> Este é o **hub** de um Obsidian Vault de estudo. Cada conceito que eu domino construindo o `density` vira uma nota profunda e interligada aqui. O objetivo é triplo: (1) **aprender de verdade** os gaps de RAG do meu currículo, (2) ter **material de revisão para entrevista** de AI Engineer, e (3) render **conteúdo de "construindo em público"** no LinkedIn.
>
> Para entender o *porquê* do projeto e a visão de produto, leia [[PROJETO]].

---

## 🗺️ Como usar este vault

- **Abra a pasta `d:\Projetos\Pessoal\IA` como um Vault no Obsidian** (`Open folder as vault`). O `.obsidian/` já está configurado.
- Navegue pela **Graph View** (Ctrl/Cmd+G) para ver como os conceitos se conectam — a densidade de links é intencional.
- Toda nota tem uma seção **Conexões** no fim, ligando para os pré-requisitos e temas relacionados.
- Notas marcadas com 🌱 são **sementes**: têm a base conceitual pronta, mas serão aprofundadas *quando eu construir aquela etapa* (é assim que o aprendizado gruda — dor, solução, medição).

---

## 📊 Tracker de progresso (preenchido conforme avanço)

Legenda: 🔲 não começado · 🏗️ em construção · ✅ dominado (construí e sei explicar o trade-off)

| Etapa | Marco | 🎓 Conceito novo | Nota | Status |
|------:|-------|------------------|------|:------:|
| 0 | Fundação (uv, Docker, pgvector, config) | pgvector, HNSW×IVFFlat | [[Por que Postgres e pgvector]] | 🏗️ |
| 1 | Ingestão + Chunking | Chunking strategies | [[Chunking]] | 🔲 |
| 2 | Embeddings + Storage | Embeddings, espaço vetorial | [[Embeddings]] | 🔲 |
| 3 | Dense retrieval | ANN search | [[Busca Vetorial (ANN)]] | 🔲 |
| 4 | Sparse + Hybrid | BM25, RRF | [[Busca Híbrida e Reciprocal Rank Fusion]] | 🔲 |
| 5 | Reranking | Cross-encoder × bi-encoder | [[Reranking]] | 🔲 |
| 6 | Geração | Grounding, anti-alucinação | [[Grounding e Geração]] | 🔲 |
| 7 | Avaliação (o diferencial) | RAGAS, LLM-as-judge | [[Avaliação com RAGAS]] | 🔲 |
| 8 | Benchmark + relatório | Experimentação sistemática | _a criar_ | 🔲 |
| 9 | MCP server (evolução) | Model Context Protocol | _a criar_ | 🔲 |

> [!tip] Ritual ao fechar cada etapa
> Quando terminar uma etapa, eu (Gilson) volto na nota do conceito e escrevo **com minhas palavras**: o que era o problema, por que a solução funciona, e um trade-off que eu não sabia antes. Se eu não conseguir escrever isso, não dominei — só copiei.

---

## 📓 Diário de bordo

### Etapa 0 — Fundação (🏗️ em andamento)

**O que construímos:** projeto `density` com `src/` layout, `pyproject.toml` (uv), `docker-compose.yml` (pgvector), `config.py` (Pydantic Settings), `models.py` (os 6 modelos de domínio: `Document`, `Chunk`, `EmbeddedChunk`, `Retrieved`, `Answer`, `EvalResult`), `cli.py` (Typer: `db-check` funcional + stubs `ingest`/`search`/`ask`/`eval`), testes (6 passando) e `ruff` limpo.

**2 lições que só apareceram construindo** (isto é ouro pra entrevista — "conte um bug que você resolveu"):

> [!warning] Lição 1 — UTF-8 em CLI no Windows
> `density --help` quebrou com `UnicodeEncodeError` no caractere `→` (seta): o Rich, num console Windows legado (code page **cp1252**), não conseguia encodar a seta e derrubava o programa. **Fix:** reconfigurar `stdout`/`stderr` para **UTF-8** no entrypoint (`_force_utf8_output` em `cli.py`). Lição: CLI que roda em Windows não pode assumir que o terminal é UTF-8.

> [!warning] Lição 2 — Conflito de porta do Postgres
> O `db-check` retornou "autenticação falhou para o usuário density" em vez de "conexão recusada" → **já havia um Postgres ocupando a 5432** na máquina. **Fix:** mapear o container para a porta **5433** no host (`"5433:5432"` no compose). Lição: `host:container` no Docker existe justamente pra desviar de conflitos; nunca assuma que a porta padrão está livre.

**Conceito da etapa:** ver [[Por que Postgres e pgvector]], [[pgvector - tipo vector e operadores de distância]] e [[Índices ANN - HNSW vs IVFFlat]].

**Para virar ✅:** subir o `docker compose up -d` e ver o `db-check` confirmar o pgvector ativo — e eu conseguir explicar, com minhas palavras, por que a extensão `vector` precisa ser criada por banco e o que HNSW faz por baixo.

---

## 🧭 Mapa de Conteúdo (MOC)

### 01 — Arquitetura · *o esqueleto e por que ele tem essa forma*
- [[Arquitetura Hexagonal (Ports e Adapters)]] — o padrão macro que rege tudo
- [[Estrutura de Pastas do density]] — cada pasta justificada, decisão por decisão
- [[Camadas, Domínio e Fronteiras]] — o que é domínio, adapter e aplicação
- [[Fluxo de Dados no Pipeline RAG]] — como um PDF vira uma resposta com citação

### 02 — Design Patterns · *o vocabulário de design que uso no código*
- [[O que são Design Patterns]] — o que são, de onde vêm (GoF), quando NÃO usar
- [[Strategy Pattern]] — trocar chunking/embedder/reranker sem tocar no resto
- [[Adapter Pattern]] — encaixar OpenAI e Anthropic atrás da mesma interface
- [[Factory Method]] — construir o provedor certo a partir da config
- [[Repository Pattern]] — esconder o pgvector atrás de um `VectorStore`
- [[Injeção de Dependência]] — quem monta as peças e por quê
- [[Pipeline (Chain of Responsibility)]] — o RAG como uma esteira de estágios
- [[Modelos de Domínio com Pydantic (DTO e Value Object)]] — os contratos entre estágios

### 03 — Banco de Dados · *design do schema e o motor de busca vetorial*
- [[Por que Postgres e pgvector]] — a decisão de infra e seus trade-offs
- [[Design do Schema (documents, chunks, embeddings)]] — modelagem ER completa
- [[pgvector - tipo vector e operadores de distância]] — cosine, L2, inner product
- [[Índices ANN - HNSW vs IVFFlat]] — o coração da velocidade da busca
- [[Full-text Search e Busca Híbrida no Postgres]] — o lado esparso (BM25/FTS)

### 04 — Linguagens e Ferramentas · *por que cada escolha de stack*
- [[Por que Python]] — por que Python (e não Go) para a camada de IA
- [[Pydantic v2]] — validação, serialização e o "parse, don't validate"
- [[Typer e Rich (o CLI)]] — a interface de linha de comando
- [[uv (gerenciador de pacotes)]] — por que uv e não pip/poetry
- [[Docker e docker-compose]] — reprodutibilidade do Postgres local
- [[pytest e ruff]] — testes e qualidade de código

### 05 — Conceitos RAG · 🌱 *sementes, aprofundadas etapa a etapa*
- [[Chunking]] · [[Embeddings]] · [[Busca Vetorial (ANN)]]
- [[Busca Híbrida e Reciprocal Rank Fusion]] · [[Reranking]]
- [[Grounding e Geração]] · [[Avaliação com RAGAS]]

---

## 🎯 Checklist de palavras-chave (para currículo e entrevista)

Cada item só vira ✅ quando eu **construí** e **sei explicar o trade-off** — não vale ter lido.

- [ ] RAG (arquitetura ponta-a-ponta) → [[Fluxo de Dados no Pipeline RAG]]
- [ ] Vector database (pgvector) → [[Por que Postgres e pgvector]]
- [ ] Embeddings → [[Embeddings]]
- [ ] Chunking strategies → [[Chunking]]
- [ ] Índices ANN (HNSW/IVFFlat) → [[Índices ANN - HNSW vs IVFFlat]]
- [ ] Hybrid search + Reciprocal Rank Fusion → [[Busca Híbrida e Reciprocal Rank Fusion]]
- [ ] Reranking (cross-encoder) → [[Reranking]]
- [ ] RAG evaluation (RAGAS) → [[Avaliação com RAGAS]]
- [ ] Arquitetura hexagonal / Ports & Adapters → [[Arquitetura Hexagonal (Ports e Adapters)]]

---

## 🔗 Conexões
- [[PROJETO]] — a visão de produto e o brief original
