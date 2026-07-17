---
tags: [linguagens, docker, docker-compose, postgres, pgvector, reprodutibilidade, infra, devops]
aliases: [Docker, docker-compose, Docker no density, Conteinerizar Postgres]
---

# Docker e docker-compose

> [!abstract] TL;DR
> No `density`, Docker entra primeiro para **conteinerizar o Postgres + pgvector no dev local**. Em vez de instalar Postgres na máquina e compilar a extensão pgvector à mão, um `docker-compose.yml` sobe um banco idêntico ao de produção com **um comando**. Isso resolve reprodutibilidade, paridade dev/prod e o clássico "funciona na minha máquina". Conteinerizar a **própria app** vem depois — quando o servidor MCP/API precisar ser distribuído.

## Por que conteinerizar o Postgres no dev local

O `density` depende de Postgres com a extensão **pgvector** para busca vetorial (ver [[Por que Postgres e pgvector]]). Instalar isso nativamente é onde os problemas começam:

- Instalar Postgres no SO (versões diferentes entre devs), configurar usuário/porta/serviço.
- **Compilar e habilitar a extensão pgvector** (`CREATE EXTENSION vector`) — passo que varia por SO e frequentemente quebra.
- Garantir que a **versão** do Postgres e do pgvector do meu dev bate com a de produção.

Com Docker, tudo isso vira uma imagem versionada. Os ganhos concretos:

- **Reprodutibilidade**: todos que clonam o repo rodam o **mesmo** Postgres+pgvector, na mesma versão. Zero "na minha máquina a extensão não existe".
- **Paridade dev/prod**: a imagem que uso local é a base da que roda em produção — diferenças de ambiente (uma classe inteira de bugs sutis) somem.
- **Descartável e limpo**: `docker compose down` remove tudo sem sujar o SO com um serviço Postgres rodando para sempre. Precisa de um banco zerado? Derruba o volume e sobe de novo.
- **Onboarding trivial**: o revisor do portfólio não instala nada além do Docker. `docker compose up -d` e o banco está de pé.

> [!tip] A dupla que garante reprodutibilidade total
> [[uv (gerenciador de pacotes)|uv]] trava o **espaço Python** (pacotes/versões). Docker trava o **espaço do sistema** (SO, libs nativas, serviços). Juntos, o ambiente inteiro — código + runtime + banco — é determinístico. Nenhum dos dois sozinho fecha a conta.

## A imagem `pgvector/pgvector`

Não é preciso montar Postgres+extensão manualmente: existe a imagem oficial **`pgvector/pgvector`**, que é o Postgres com pgvector **já compilado e disponível**. Escolhe-se uma tag que fixa a versão do Postgres, por exemplo `pgvector/pgvector:pg16` (Postgres 16). Fixar a tag — em vez de `latest` — é o que trava a paridade: `latest` muda sob seus pés e reintroduz o problema que Docker deveria resolver.

## Anatomia de um `docker-compose.yml`

`docker-compose` descreve, declarativamente, os serviços do projeto. Para o dev do `density`, um serviço só (o banco) já basta:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16      # Postgres 16 + pgvector já embutido
    container_name: density-db
    environment:
      POSTGRES_USER: density
      POSTGRES_PASSWORD: density
      POSTGRES_DB: density
    ports:
      - "5432:5432"                    # host:container
    volumes:
      - pgdata:/var/lib/postgresql/data  # persistência dos dados
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U density"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:                              # volume nomeado, sobrevive ao container
```

Lendo campo a campo:

- **`image`**: qual imagem rodar — aqui, Postgres+pgvector numa versão fixa.
- **`environment`**: variáveis que a imagem do Postgres usa para inicializar usuário, senha e banco no primeiro boot. Combinam com a `DATABASE_URL` que o [[Pydantic v2|Settings]] da app lê (ex.: `postgresql://density:density@localhost:5432/density`).
- **`ports`**: mapeia a porta do container para o host, para a app (rodando fora do container, via `uv run`) alcançar o banco em `localhost:5432`.
- **`volumes`**: monta um **volume nomeado** (`pgdata`) no diretório de dados do Postgres — é o que dá **persistência** (próxima seção).
- **`healthcheck`**: deixa o Compose saber quando o banco está de fato pronto para aceitar conexões — útil para orquestrar a ordem de subida quando a app também for conteinerizada.

Comandos do dia a dia:

```bash
docker compose up -d      # sobe o banco em background
docker compose ps         # status / health
docker compose logs -f db # acompanha logs
docker compose down       # derruba (dados persistem no volume pgdata)
docker compose down -v    # derruba E apaga o volume — banco zerado
```

## Volumes vs dados efêmeros

Este é o conceito que mais confunde e mais importa. Por padrão, o filesystem de um container é **efêmero**: derrubou o container, os dados escritos dentro dele **somem**. Para um banco, isso seria catastrófico — cada `down` apagaria todos os embeddings ingeridos.

O **volume** resolve: `pgdata:/var/lib/postgresql/data` guarda os arquivos de dados do Postgres **fora** do ciclo de vida do container, gerenciado pelo Docker. Assim:

- `docker compose down` + `up` → dados **preservados** (o container é novo, o volume é o mesmo).
- `docker compose down -v` → volume removido → banco **zerado** (útil para recomeçar limpo, re-testar a migração de schema, ou reproduzir uma ingestão do zero).

```mermaid
flowchart LR
    subgraph Efêmero
      C[Container Postgres]
    end
    subgraph Persistente
      V[(Volume pgdata)]
    end
    C -- lê/escreve --> V
    C -. down/up recria .-> C
    V -. sobrevive ao down .-> V
```

> [!warning] Reconhecer o que é efêmero de propósito
> Nem tudo deve persistir. Dados de teste, caches, um banco de sandbox para experimentar chunking — muitas vezes você *quer* que sumam (`down -v`) para partir de estado limpo. A decisão de engenharia é escolher conscientemente o que precisa de volume (dados de valor) e o que é descartável. A avaliação com [[Avaliação com RAGAS|RAGAS]], por exemplo, pede um estado de índice conhecido e reproduzível — às vezes é melhor recriá-lo do zero do que confiar num volume acumulado.

## Quando conteinerizar a PRÓPRIA app

No dev inicial, a app roda **no host** (via `uv run`) e só o banco fica no Docker. Isso é deliberado: durante a fase de iteração rápida do núcleo de RAG, rodar a app nativamente dá o loop mais curto (edita, `uv run`, vê o resultado) sem rebuild de imagem a cada mudança. O banco, que é infra estável, ganha com o container; a app, que muda toda hora, não.

Conteinerizar a app faz sentido **mais tarde**, quando ela vira algo a **distribuir e servir** — o servidor MCP/API (ver [[Typer e Rich (o CLI)]] para a progressão CLI → MCP). Aí um `Dockerfile` da app entra em cena e o Compose passa a orquestrar **dois** serviços (`app` + `db`) com `depends_on` amarrado ao healthcheck do banco:

```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev     # layer cacheável: só reinstala se o lock mudar
COPY src ./src
ENTRYPOINT ["uv", "run", "density"]
```

Note a sinergia com [[uv (gerenciador de pacotes)|uv]]: copiar `pyproject.toml`+`uv.lock` e rodar `uv sync --frozen` **antes** do código cria uma camada de dependências que só é reconstruída quando o lock muda — builds muito mais rápidos.

## Trade-offs honestos

- **Overhead de recurso**: containers consomem RAM/CPU; no Windows/macOS o Docker roda numa VM, custando um pouco mais. Para um Postgres de dev, é irrelevante; é bom reconhecer que não é grátis.
- **Curva de conceitos**: imagem vs container vs volume vs rede é uma camada mental extra que precisa ser dominada para depurar ("por que meus dados sumiram?" quase sempre é volume mal configurado).
- **Não é orquestração de produção**: `docker-compose` é ótimo para dev e deploys simples, mas produção em escala pede Kubernetes/ECS ou um Postgres gerenciado (RDS). Compose local não é a resposta de escala — e tudo bem, não é para isso que ele está aqui.

> [!info] Postgres gerenciado em produção
> Em produção real, muitas vezes o Postgres+pgvector vira um serviço gerenciado (RDS, Supabase, Neon) em vez de um container que eu opero. O container do Compose é a **fidelidade de dev**; produção pode terceirizar a operação do banco. A paridade que importa é de **versão e extensão**, não necessariamente de "rodar em container".

## Onde isso aparece no density

- `docker-compose.yml` na raiz: serviço `db` com `pgvector/pgvector:pgXX`, `environment`, `ports 5432`, e volume `pgdata` para persistência.
- A `DATABASE_URL` no [[Pydantic v2|Settings]] aponta para o banco do Compose no dev local.
- O schema (`documents`, `chunks`, `embeddings`) e a extensão `vector` vivem nesse Postgres — ver [[Design do Schema (documents, chunks, embeddings)]] e [[pgvector - tipo vector e operadores de distância]].
- Fase futura: `Dockerfile` da app + serviço `app` no Compose, usando `uv sync --frozen`, para o servidor MCP/API.

## Conexões

- [[Por que Postgres e pgvector]]
- [[uv (gerenciador de pacotes)]]
- [[Design do Schema (documents, chunks, embeddings)]]
- [[pgvector - tipo vector e operadores de distância]]
- [[Pydantic v2]]
- [[Typer e Rich (o CLI)]]
- [[Avaliação com RAGAS]]
- [[PROJETO]]
