---
tags: [linguagens, python, pydantic, validacao, config, dto, parse-dont-validate]
aliases: [Pydantic v2, Pydantic, BaseSettings, Validacao com Pydantic]
---

# Pydantic v2

> [!abstract] TL;DR
> Pydantic v2 é a camada de **validação e serialização** do `density`. Sua v2 reescreveu o motor em **Rust** (`pydantic-core`), ganhando ordens de magnitude de velocidade. Mas a razão de escolhê-lo em vez de `dataclasses`/`attrs` não é performance — é filosofia: **"parse, don't validate"**. Todo dado externo não confiável (config de env, respostas de API, texto de PDF) é transformado, na borda, num tipo confiável e imutável. Depois disso, o resto do código pode assumir que o dado é válido.

## O que a v2 trouxe de concreto

A v2 (2023+) não foi um patch — foi uma reescrita:

- **Núcleo em Rust (`pydantic-core`)**: a validação, que antes era Python puro, virou código nativo. O resultado é validação 5–50x mais rápida. Isso importa quando você valida milhares de chunks numa ingestão.
- **Serialização de primeira classe**: `model_dump()` e `model_dump_json()` substituem o antigo `.dict()`/`.json()` com controle fino (por alias, excluindo `None`, por `mode="json"`).
- **API de validadores redesenhada**: `@field_validator` e `@model_validator` (com `mode="before"`/`"after"`) substituem os antigos `@validator`/`@root_validator`.
- **`model_config` como dict tipado** (`ConfigDict`) no lugar da antiga inner class `Config`.
- **`pydantic-settings` separado**: `BaseSettings` saiu para o pacote `pydantic-settings`, dedicado a carregar config de ambiente.

> [!warning] Armadilha de migração
> Muito material antigo na internet ainda mostra API v1 (`@validator`, `class Config`, `.dict()`). No `density` uso **exclusivamente v2**. Se você copiar um snippet e ele usar `@validator`, está desatualizado. Sinais de v2: `@field_validator`, `model_config = ConfigDict(...)`, `model_dump()`.

## "Parse, don't validate": o conceito central

O nome vem de um ensaio famoso de Alexis King. A ideia:

- **Validar** (anti-padrão): você checa se um dado está ok e segue usando o **mesmo tipo genérico** (`dict`, `str`). O conhecimento "isto é válido" se perde imediatamente — três funções abaixo, alguém revalida ou assume errado.
- **Parsear** (padrão bom): você consome o dado bruto e produz um **tipo mais rico** que só pode existir se for válido. O sistema de tipos passa a carregar a garantia.

```python
# Anti-padrão: valida e continua com dict frouxo
def handle(payload: dict) -> None:
    if "top_k" not in payload:
        raise ValueError("faltou top_k")
    # 200 linhas depois, ninguém lembra se top_k é int ou str...

# Padrão: parseia para um tipo confiável na borda
class SearchRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)

def handle(payload: dict) -> None:
    req = SearchRequest.model_validate(payload)  # borda: bruto -> confiável
    # daqui pra frente req.top_k é int, no range, garantido pelo tipo
```

> [!tip] Onde fica a "borda"
> Na [[Arquitetura Hexagonal (Ports e Adapters)]], a borda é exatamente onde os **adapters** convertem o mundo externo em objetos de domínio. Pydantic é a ferramenta que faz esse parse na fronteira. Depois dele, o núcleo trabalha só com tipos limpos — ver [[Camadas, Domínio e Fronteiras]].

## `BaseSettings`: config de env/.env sem dor

Config espalhada por `os.getenv` no meio do código é uma fonte clássica de bugs (typo silencioso, default implícito, falta em produção). `BaseSettings` (de `pydantic-settings`) resolve declarativamente:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DENSITY_")

    openai_api_key: str                      # obrigatório: falha no boot se faltar
    database_url: str
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = Field(default=800, ge=100, le=4000)
    top_k: int = Field(default=5, ge=1)
```

O que isso compra:

- **Fail fast**: se `DENSITY_OPENAI_API_KEY` não existe, a aplicação **não sobe** — o erro aparece no boot com mensagem clara, não três chamadas de API depois com um 401 críptico.
- **Coerção tipada**: `DENSITY_CHUNK_SIZE=800` vem como string do ambiente e é convertida para `int` validado.
- **Fonte única de verdade** para configuração, injetável no resto do sistema (ver [[Injeção de Dependência]]) em vez de ser lida globalmente em qualquer canto.

## `model_config`, `frozen=True` e validadores

Três recursos que uso muito:

- **`frozen=True`** torna o modelo **imutável** (hasheável, seguro para compartilhar entre threads/corrotinas, impossível de mutar por engano). Perfeito para Value Objects — ver [[Modelos de Domínio com Pydantic (DTO e Value Object)]]. Um `Chunk` que já foi embeddado não deveria ter seu texto mutado silenciosamente depois.
- **`@field_validator`** para regras de um campo (ex.: normalizar/limpar o texto de um chunk, garantir que a dimensão do embedding bate).
- **`@model_validator`** para invariantes que cruzam campos (ex.: se `strategy == "hybrid"`, então `alpha` precisa estar entre 0 e 1).

```python
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

class Chunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    document_id: str
    index: int
    text: str
    embedding: list[float] | None = None

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("chunk vazio não deveria existir")
        return v

    @model_validator(mode="after")
    def dim_check(self):
        if self.embedding is not None and len(self.embedding) != 1536:
            raise ValueError("dimensão do embedding incompatível com o modelo")
        return self
```

## Por que Pydantic e não `dataclasses`/`attrs`?

Pergunta legítima — `dataclasses` é stdlib, `attrs` é ótimo. A distinção é o propósito:

| Ferramenta | Faz | Não faz |
|---|---|---|
| `dataclass`/`attrs` | Estrutura de dados com boilerplate reduzido | **Não valida nem coage** dados de entrada por padrão |
| Pydantic v2 | Estrutura **+ validação + coerção + (de)serialização** | Overhead maior que um dataclass puro |

A regra que aplico: **onde há I/O externo não confiável, use Pydantic**. E o `density` é praticamente todo feito de fronteiras não confiáveis:

- **Texto de PDF/MD/TXT**: entrada suja, encoding duvidoso, precisa ser saneada e estruturada.
- **Respostas de API (OpenAI/Anthropic)**: JSON externo que pode mudar de formato; parseá-lo para um modelo tipado protege o núcleo.
- **Config de ambiente**: como visto acima.

Para uma struct puramente interna, efêmera e nunca serializada, um `dataclass` bastaria. Mas a maioria dos objetos que viajam entre estágios do pipeline cruza uma fronteira, então Pydantic paga.

## Como sustenta os contratos entre estágios

O pipeline de RAG é uma cadeia (ver [[Fluxo de Dados no Pipeline RAG]] e [[Pipeline (Chain of Responsibility)]]): `Document → Chunk → EmbeddedChunk → RetrievedChunk → Answer`. Cada seta é um **contrato**. Modelando cada estágio como um modelo Pydantic:

- A **saída** de um estágio é validada, então a **entrada** do próximo é confiável — erros aparecem na fronteira certa, não três estágios adiante.
- Os modelos são **documentação executável**: ler a classe `RetrievedChunk` diz exatamente o que a busca produz e o gerador consome.
- Refatorar fica seguro: mude o contrato e o validador/type checker aponta quem quebrou.

> [!example] Sinaliza senioridade
> Num projeto de portfólio, validação explícita na borda + tipos imutáveis + config declarativa comunicam que você pensa em **fronteiras de confiança e invariantes**, não só em "fazer funcionar". É o oposto de passar `dict` cru por todo lado.

## Onde isso aparece no density

- `src/density/config.py`: `Settings(BaseSettings)` carregando de `.env`/ambiente — chaves de API, `DATABASE_URL`, modelo de embedding, parâmetros de chunking e `top_k`.
- `src/density/models.py`: os modelos de domínio (`Document`, `Chunk`, `RetrievedChunk`, `Answer`, resultados de avaliação) como `BaseModel`, muitos `frozen=True`.
- Os **adapters** de LLM/embeddings parseiam respostas de API para modelos Pydantic antes de devolver ao núcleo.
- `pyproject.toml` fixa `pydantic>=2` e `pydantic-settings`.

## Conexões

- [[Modelos de Domínio com Pydantic (DTO e Value Object)]]
- [[Camadas, Domínio e Fronteiras]]
- [[Injeção de Dependência]]
- [[Arquitetura Hexagonal (Ports e Adapters)]]
- [[Fluxo de Dados no Pipeline RAG]]
- [[Pipeline (Chain of Responsibility)]]
- [[Por que Python]]
- [[PROJETO]]
