---
tags: [banco-de-dados, pgvector, postgres, vetores, distancia, cosseno, embeddings, rag]
aliases: [tipo vector, operadores de distancia pgvector, cosseno vs L2, halfvec, quantizacao]
---

# pgvector - tipo vector e operadores de distância

> [!abstract] TL;DR
> `pgvector` adiciona o tipo `vector(n)` — um array de `n` floats — e três operadores de distância: `<->` (L2/euclidiana), `<=>` (cosseno) e `<#>` (inner product negativo). A escolha do operador **depende do modelo de embedding**; para embeddings **normalizados** (como os da OpenAI), cosseno e inner product são equivalentes. A armadilha que derruba iniciantes: **o índice ANN precisa ser criado com a classe de operador que casa com o operador usado na query** — senão o índice é simplesmente ignorado e você cai num scan sequencial silencioso.

## O tipo `vector(n)`

`vector(n)` armazena `n` números de ponto flutuante. O `n` **não é decoração**: é a dimensionalidade do modelo de embedding e tem que bater exatamente.

```sql
-- text-embedding-3-small produz vetores de 1536 dimensoes
ALTER TABLE embeddings ADD COLUMN embedding vector(1536);
```

> [!warning] `n` é um contrato, não uma sugestão
> Se você declarar `vector(1536)` e tentar inserir um vetor de 768 dims, o Postgres **rejeita**. Isso é bom: pega na hora o erro clássico de "troquei o modelo de embedding e esqueci de migrar o schema". No `density`, `1536` amarra a coluna ao `text-embedding-3-small`. Trocar de modelo com dimensão diferente é, por isso mesmo, uma decisão de schema — e é justamente por antecipar isso que a tabela `embeddings` é separada e versiona por `model` (veja [[Design do Schema (documents, chunks, embeddings)]]).

Cada float é, por padrão, um `float4` (4 bytes). Um vetor de 1536 dims ≈ **6 KB**. Multiplique por milhões de chunks e você entende por que memória vira o gargalo dos índices (veja [[Índices ANN - HNSW vs IVFFlat]]).

## Os três operadores de distância

O ponto central: buscar por similaridade é **ordenar por distância crescente**. "O mais parecido" = "o de menor distância". Os operadores:

| Operador | Nome | Significado | Classe de operador do índice |
|----------|------|-------------|------------------------------|
| `<->` | Distância L2 (euclidiana) | Distância "em linha reta" no espaço | `vector_l2_ops` |
| `<=>` | Distância cosseno | `1 - cosseno(a, b)`; mede **ângulo**, ignora magnitude | `vector_cosine_ops` |
| `<#>` | Inner product **negativo** | `-(a · b)`; produto escalar com sinal trocado | `vector_ip_ops` |

> [!info] Por que o inner product é negativo (`<#>`)
> Índices e `ORDER BY` querem "menor primeiro". Mas no inner product, **maior** produto = mais similar. Para reconciliar, `pgvector` retorna o **negativo**: assim "menor `<#>`" continua significando "mais similar", e o mesmo `ORDER BY ... LIMIT k` funciona para todos os três operadores. É uma convenção de engenharia, não uma propriedade matemática — mas se você esquecer, ordena ao contrário.

### Qual operador usar com qual modelo

Aqui está o conhecimento que separa quem copiou de Stack Overflow de quem entende:

- **Cosseno (`<=>`)** mede só o **ângulo** entre vetores, ignorando o comprimento. É a escolha padrão para embeddings de texto, porque "significado" nesses modelos vive na *direção* do vetor, não na sua magnitude.
- **Inner product (`<#>`)** considera ângulo **e** magnitude.
- **L2 (`<->`)** mede distância absoluta; sensível à magnitude.

> [!tip] O atalho da normalização (e por que a OpenAI facilita sua vida)
> Um vetor **normalizado** tem norma (comprimento) = 1. Quando **todos** os vetores estão normalizados, a magnitude some da conta e **cosseno, inner product e L2 dão a mesma ordenação** — mudam os números, não o ranking. E os embeddings da **OpenAI já vêm normalizados**. Consequência prática:
> - Você pode usar `<=>` (cosseno) sem pensar — é o mais à prova de erro.
> - Se performance for crítica, `<#>` (inner product) é ligeiramente mais barato de computar (não precisa dividir pelas normas), e com vetores normalizados dá o **mesmo ranking** do cosseno.
> Para o `density`, `<=>` com `vector_cosine_ops` é o default seguro e legível.

## A armadilha que todo mundo cai: índice tem que casar com o operador

Este é o bug silencioso número um de `pgvector`:

> [!danger] O índice ANN só é usado se a classe de operador casar com o operador da query
> Se você criou o índice com `vector_cosine_ops` mas escreve a query com `<->` (L2), o Postgres **ignora o índice** e faz um scan sequencial `O(n)`. Não dá erro. Não avisa. Só fica **lento** — e você só descobre com `EXPLAIN ANALYZE` mostrando um `Seq Scan` onde deveria haver `Index Scan`.

```sql
-- Indice criado para COSSENO:
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);

-- ✅ USA o indice (operador <=> casa com vector_cosine_ops):
SELECT chunk_id
FROM embeddings
ORDER BY embedding <=> :q      -- :q e o vetor da query
LIMIT 10;

-- ❌ NAO usa o indice (operador <-> nao casa) -> Seq Scan silencioso:
SELECT chunk_id
FROM embeddings
ORDER BY embedding <-> :q
LIMIT 10;
```

Regra a gravar: **decida o operador uma vez, crie o índice com a classe correspondente, e nunca misture.** No `density`, essa consistência mora no adapter `pgvector.py` — a query e a migration do índice usam a mesma métrica por construção. Detalhes de como o índice em si funciona em [[Índices ANN - HNSW vs IVFFlat]].

## A query canônica de busca vetorial

```sql
SELECT
    c.id,
    c.text,
    e.embedding <=> :q AS distance   -- expoe a distancia p/ debug/threshold
FROM embeddings e
JOIN chunks c ON c.id = e.chunk_id
WHERE e.model = 'text-embedding-3-small'   -- so o modelo atual
ORDER BY e.embedding <=> :q               -- similaridade
LIMIT :k;                                  -- top-k
```

Repare: o `ORDER BY ... LIMIT k` **é** a busca top-k. O `JOIN` traz o texto (que mora em `chunks`). O filtro por `model` respeita o versionamento do schema. Isso é a espinha dorsal de `src/density/retrieval/dense.py` (veja [[Busca Vetorial (ANN)]]).

## Compressão: `halfvec`, `bit` e quantização

Vetores full-precision custam memória, e memória é o teto do pgvector. Daí as opções de compressão — **todas trade-off entre memória/velocidade e recall**:

- **`halfvec(n)`** — floats de **2 bytes** (meia precisão) em vez de 4. **Corta a memória do índice pela metade** com perda de recall geralmente pequena. Frequentemente o melhor custo-benefício. Índice: `halfvec_cosine_ops`.
- **Quantização escalar** — reduz cada dimensão a menos bits.
- **`bit` / quantização binária** — cada dimensão vira **1 bit** (sinal). Compressão brutal (32×), busca por distância de Hamming ultrarrápida — mas recall despenca, então serve como **estágio de filtragem grosseira** seguido de re-ranqueamento com o vetor cheio.

> [!example] Como pensar o trade-off
> `float4` → `halfvec` → quantização escalar → `bit`: a cada passo você ganha memória/velocidade e **perde recall**. A pergunta certa não é "quero compressão?" e sim "**quanto recall posso sacrificar por quanta memória economizada?**" — e a única forma honesta de responder é *medir*, com o harness de [[Avaliação com RAGAS]]. Comprimir sem medir recall é otimização cega. Para a escala inicial do `density`, `vector(1536)` full-precision é o ponto de partida certo; `halfvec` é a primeira alavanca a puxar quando a memória apertar.

## Onde isso aparece no density

- A coluna `embedding vector(1536)` da tabela `embeddings` (veja [[Design do Schema (documents, chunks, embeddings)]]) e o `1536` fixado pelo `text-embedding-3-small` em `src/density/models.py`.
- `src/density/retrieval/dense.py` monta a query `ORDER BY embedding <=> :q LIMIT :k` — usando `<=>` (cosseno) para casar com o índice.
- `src/density/store/pgvector.py` garante que a migration do índice e a query usem a mesma métrica, evitando a armadilha do Seq Scan.
- `halfvec` é candidato natural ao benchmark de memória×recall contra Qdrant (veja [[Por que Postgres e pgvector]]).

## Conexões

- [[Índices ANN - HNSW vs IVFFlat]] — o índice que casa com o operador escolhido.
- [[Embeddings]] — de onde vêm os vetores e por que são normalizados.
- [[Busca Vetorial (ANN)]] — o conceito de retrieval que o operador materializa.
- [[Design do Schema (documents, chunks, embeddings)]] — a coluna `vector` no seu contexto.
- [[Por que Postgres e pgvector]] · [[Full-text Search e Busca Híbrida no Postgres]] · [[Avaliação com RAGAS]]
- [[PROJETO]] · [[APRENDIZADOS]]
