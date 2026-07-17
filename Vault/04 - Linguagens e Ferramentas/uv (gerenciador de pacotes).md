---
tags: [linguagens, python, uv, gerenciador-de-pacotes, reprodutibilidade, tooling, astral]
aliases: [uv, uv package manager, Gerenciador de pacotes Python, uv vs pip vs poetry]
---

# uv (gerenciador de pacotes)

> [!abstract] TL;DR
> **uv** é um gerenciador de pacotes e ambientes virtuais para Python, escrito em **Rust** pela **Astral** (a mesma casa do [[pytest e ruff|ruff]]). Ele unifica o papel de `pip` + `venv` + `pip-tools` + boa parte de `poetry`/`pipenv`, com resolução de dependências **10–100x mais rápida** e um **lockfile (`uv.lock`)** que garante instalações determinísticas. Num projeto de portfólio, a promessa concreta é: **o revisor clona e roda em segundos**, com o mesmo ambiente que eu tenho — reprodutibilidade real.

## O problema que o uv resolve

O empacotamento em Python foi historicamente fragmentado e doloroso. Um projeto típico misturava:

- `pip` para instalar, `venv` para isolar, `requirements.txt` para listar (sem travar versões transitivas de forma confiável).
- Ou `poetry`/`pipenv` para ter lockfile e resolução — mas com resolução **lenta** e, às vezes, comportamento imprevisível.
- `pyenv` à parte para gerenciar versões do interpretador.

O resultado: onboarding frágil ("funciona na minha máquina"), builds não reprodutíveis e minutos perdidos toda vez que se mexia nas deps. uv colapsa essas ferramentas numa só, rápida, e coloca o `pyproject.toml` como fonte única.

## uv vs pip vs poetry vs pipenv

| Critério | pip (+venv) | pipenv | poetry | **uv** |
|---|---|---|---|---|
| Velocidade de resolução/install | ok, sem lock real | lenta | média | **muito rápida (Rust)** |
| Lockfile determinístico | não (nativo) | `Pipfile.lock` | `poetry.lock` | **`uv.lock`** |
| Gerencia versão do Python | não | não | não | **sim** (baixa o interpretador) |
| Fonte de config | `requirements.txt` | `Pipfile` | `pyproject.toml` | **`pyproject.toml`** (padrão) |
| Abrangência | 1 função | várias | várias | pip+venv+pip-tools+pyenv-ish |

> [!tip] Por que a velocidade importa de verdade
> Não é só conforto. Resolução/instalação rápida muda **comportamento**: você reconstrói o ambiente sem hesitar, testa em CI a cada push sem penalizar o tempo do pipeline, e o revisor não desiste esperando o `install`. Ferramenta lenta cria atrito que empurra as pessoas para atalhos ruins (pular o lock, reusar venv sujo). uv remove esse atrito.

## `pyproject.toml` como fonte única

uv adota o padrão moderno: **`pyproject.toml`** descreve o projeto, e o **`uv.lock`** trava a resolução exata (incluindo transitivas e hashes).

```toml
[project]
name = "density"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2",
    "pydantic-settings",
    "typer",
    "rich",
    "openai",
    "anthropic",
    "psycopg[binary]",
    "pgvector",
    "sentence-transformers",
    "ragas",
]

[dependency-groups]
dev = ["pytest", "ruff", "pytest-cov"]

[project.scripts]
density = "density.cli:app"
```

- **`pyproject.toml`**: o que o humano declara (deps diretas, versões mínimas, scripts).
- **`uv.lock`**: o que a máquina resolve e trava — **commitado no repo**. É ele que garante que a instalação de amanhã, ou na máquina do revisor, é bit-a-bit a mesma da minha hoje.
- **Grupos de dev** separam ferramentas de desenvolvimento ([[pytest e ruff]]) das deps de runtime, então a imagem/instalação de produção não carrega o que só serve para testar.

## Comandos do dia a dia

```bash
uv sync            # cria/atualiza o venv a partir do lock — o "clone e roda"
uv add ragas       # adiciona dep: atualiza pyproject.toml + uv.lock
uv add --dev pytest # adiciona ao grupo de dev
uv remove pipdeptree
uv run density ask "o que diz o contrato sobre rescisão?"  # roda no venv sem ativar
uv run pytest      # roda a suíte no ambiente travado
uv lock            # re-resolve o lockfile
uv python install 3.11  # baixa o próprio interpretador
```

> [!info] `uv run` é o detalhe que muda o fluxo
> `uv run <cmd>` executa o comando **dentro do ambiente do projeto sem você ativar o venv manualmente**. Some a classe inteira de bugs "esqueci de ativar o venv e instalei/rodei no Python global". Combinado com `[project.scripts]`, `uv run density ...` roda o CLI ([[Typer e Rich (o CLI)]]) exatamente com as deps travadas.

## Por que reprodutibilidade importa num portfólio

O `density` é projeto de **portfólio** — sinaliza senioridade (ver [[PROJETO]] e [[APRENDIZADOS]]). A experiência do revisor é parte do produto. O caminho ideal:

```bash
git clone https://github.com/.../density
cd density
uv sync           # segundos: ambiente idêntico ao meu
docker compose up -d   # Postgres + pgvector (ver nota de Docker)
uv run density ingest ./docs
uv run density ask "..."
```

> [!example] O que isso comunica
> "Clonar e rodar em segundos, com ambiente idêntico" diz ao revisor que você **entende reprodutibilidade, lockfiles e DX**. O oposto — um `requirements.txt` sem versões travadas que quebra em resolução de conflito na máquina dele — comunica descuido, independentemente de quão bom seja o código de RAG por baixo. Ferramental é a primeira impressão técnica.

Reprodutibilidade também é o alicerce de **avaliação confiável**: se o ambiente muda entre execuções, você não sabe se a variação nas métricas do [[Avaliação com RAGAS|RAGAS]] veio da sua mudança ou de uma versão diferente de uma dependência. O lock isola a variável.

## Como conversa com Docker

uv e Docker resolvem reprodutibilidade em **camadas diferentes e complementares**:

- **uv** trava o **espaço Python** (pacotes, versões, interpretador).
- **[[Docker e docker-compose]]** trava o **espaço do sistema** (SO, bibliotecas nativas, e serviços como o Postgres+pgvector).

Num Dockerfile da app, o padrão é copiar `pyproject.toml`+`uv.lock` primeiro e rodar `uv sync --frozen` numa layer cacheável, antes de copiar o código — assim rebuilds só reinstalam deps quando o lock muda. Camadas juntas, o ambiente inteiro é determinístico.

## Trade-offs honestos

Escolher uv não é isento de custos:

- **Ferramenta nova**: uv é recente e evolui rápido. A superfície de comandos e alguns comportamentos ainda mudam entre versões — é preciso acompanhar o changelog. poetry/pip são mais "aborrecidos" (estáveis) por serem antigos.
- **Ecossistema em maturação**: menos tutoriais, menos respostas prontas de casos raros, integrações de terceiros ainda alcançando.
- **Aposta num fornecedor**: uv e ruff vêm da mesma empresa (Astral). É uma aposta de que essa stack continuará mantida — provável, dado o momentum, mas é uma dependência estratégica a reconhecer.
- **Curva para quem só conhece pip**: `uv run`, grupos de deps e o lock exigem mudar hábitos.

> [!warning] O que eu NÃO faço
> Não misturo `pip install` avulso dentro do venv gerenciado pelo uv — isso desincroniza o `uv.lock` e mata a reprodutibilidade. Toda dep entra por `uv add`. O lockfile só vale se for a única porta de entrada.

## Onde isso aparece no density

- `pyproject.toml`: fonte única de deps, grupos de dev, `requires-python`, e o script `density`.
- `uv.lock`: commitado, garante instalação determinística para qualquer um que clone.
- README/instruções: `uv sync` + `uv run density ...` como caminho canônico de setup.
- CI e o `Dockerfile` da app (fase MCP/API) usam `uv sync --frozen` para builds reprodutíveis.

## Conexões

- [[Docker e docker-compose]]
- [[pytest e ruff]]
- [[Typer e Rich (o CLI)]]
- [[Avaliação com RAGAS]]
- [[Por que Python]]
- [[PROJETO]]
- [[APRENDIZADOS]]
