# density

Ferramenta open-source de **RAG production-ready** para sumarização e busca inteligente
sobre documentos longos (PDF, TXT, MD). O diferencial sobre "mais um RAG tutorial" é a
**avaliação rigorosa integrada**: o `density` não só faz RAG — ele **mede** a qualidade
da recuperação e da geração.

> 📚 **Aprendizado e decisões de arquitetura** vivem no Obsidian Vault em [`Vault/`](Vault/).
> Comece por [`Vault/PROJETO.md`](Vault/PROJETO.md) e o hub [`Vault/APRENDIZADOS.md`](Vault/APRENDIZADOS.md).

## Stack

Python 3.11+ · pgvector (Postgres) · Pydantic v2 · Typer + Rich · Docker · pytest + ruff · uv

## Setup (Etapa 0 — Fundação)

Pré-requisitos: [Docker](https://www.docker.com/) e [uv](https://docs.astral.sh/uv/).

```bash
# 1. Instalar o uv (se ainda não tiver)
pip install uv

# 2. Criar o ambiente e instalar dependências (uv baixa o Python 3.12 se preciso)
uv sync

# 3. Subir o Postgres + pgvector (exposto na porta 5433 do host)
docker compose up -d

# 4. Verificar que a fundação está de pé
uv run density db-check
```

> ℹ️ O container expõe o Postgres na **porta 5433** do host (não 5432) para não
> colidir com um Postgres já instalado na máquina. Para conectar por um cliente
> externo: `localhost:5433`, usuário/senha/db = `density`.

`db-check` deve responder que o **pgvector está ativo**. A partir daí, seguimos o roadmap.

## Comandos da CLI

| Comando            | Status        | Etapa |
|--------------------|---------------|-------|
| `density db-check` | ✅ funcional   | 0     |
| `density ingest`   | 🔲 stub        | 1     |
| `density search`   | 🔲 stub        | 3–4   |
| `density ask`      | 🔲 stub        | 6     |
| `density eval`     | 🔲 stub        | 7     |

## Desenvolvimento

```bash
uv run pytest      # testes
uv run ruff check  # lint
uv run ruff format # formatação
```

## Estrutura

```
src/density/     código do pacote (config, models, cli, e os módulos das próximas etapas)
tests/           testes (espelham a estrutura de src/)
db/init/         SQL de inicialização do Postgres (habilita a extensão vector)
Vault/           Obsidian Vault: notas de estudo e decisões de arquitetura
```
