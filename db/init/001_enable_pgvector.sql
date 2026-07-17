-- Habilita a extensão pgvector no banco `density`.
-- Este arquivo roda AUTOMATICAMENTE na primeira subida do container
-- (mecanismo docker-entrypoint-initdb.d do Postgres).
--
-- `CREATE EXTENSION vector` registra no banco o tipo `vector`, os operadores de
-- distância (<->, <=>, <#>) e os métodos de índice ANN (hnsw, ivfflat).
-- Ver Vault: [[pgvector - tipo vector e operadores de distância]] e
-- [[Índices ANN - HNSW vs IVFFlat]].
CREATE EXTENSION IF NOT EXISTS vector;
