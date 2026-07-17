"""Modelos de domínio do density.

Estes são os CONTRATOS que cruzam as fronteiras entre os estágios do pipeline RAG
(ingestão → chunking → embedding → storage → retrieval → rerank → geração → avaliação).

São imutáveis (`frozen=True`) de propósito: um dado que já atravessou uma fronteira
não deve mais mudar. Isso torna o pipeline auditável e os testes triviais — você passa
uma entrada em memória e compara a saída, sem efeitos colaterais escondidos.

Ver Vault: [[Modelos de Domínio com Pydantic (DTO e Value Object)]] e
[[Fluxo de Dados no Pipeline RAG]].
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Um arquivo ingerido — a fonte de verdade. Granularidade: 1 por arquivo."""

    model_config = ConfigDict(frozen=True)

    id: str
    source: str  # caminho, URL ou nome do arquivo
    mime_type: str  # application/pdf, text/plain, text/markdown...
    checksum: str  # hash do conteúdo — permite deduplicar reingestão
    metadata: dict = Field(default_factory=dict)
    created_at: datetime | None = None


class Chunk(BaseModel):
    """Um pedaço recuperável de um Document. Granularidade: N por documento."""

    model_config = ConfigDict(frozen=True)

    id: str
    document_id: str  # FK lógica -> Document.id
    ordinal: int  # posição do chunk dentro do documento (0, 1, 2, ...)
    text: str
    token_count: int | None = None
    metadata: dict = Field(default_factory=dict)


class EmbeddedChunk(BaseModel):
    """Um Chunk + seu vetor. Separa 'texto' de 'representação vetorial'."""

    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    model: str  # qual modelo gerou o vetor — habilita versionar/reindexar
    dim: int  # dimensão do vetor (deve bater com a coluna vector(n))
    embedding: list[float]


class Retrieved(BaseModel):
    """Um Chunk recuperado por uma busca, com score e a origem da recuperação."""

    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    score: float
    source: str  # 'dense' | 'sparse' | 'hybrid' | 'rerank'


class Answer(BaseModel):
    """Resposta/sumário fundamentado nos contextos recuperados (grounded)."""

    model_config = ConfigDict(frozen=True)

    question: str
    text: str
    contexts: list[Retrieved] = Field(default_factory=list)


class EvalResult(BaseModel):
    """Resultado de UMA métrica de avaliação (RAGAS ou própria)."""

    model_config = ConfigDict(frozen=True)

    metric: str  # 'faithfulness', 'answer_relevancy', 'context_precision'...
    score: float
    detail: dict = Field(default_factory=dict)
