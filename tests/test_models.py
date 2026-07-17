"""Testes dos modelos de domínio.

Foco: comportamento determinístico (imutabilidade, defaults, validação). Nada
de LLM/DB aqui — essas partes puras são baratíssimas de testar. A qualidade da
GERAÇÃO é medida por avaliação (RAGAS), não por teste unitário. Ver Vault:
[[pytest e ruff]].
"""

import pytest
from pydantic import ValidationError

from density.models import Answer, Chunk, EmbeddedChunk, Retrieved


def _chunk() -> Chunk:
    return Chunk(id="c1", document_id="d1", ordinal=0, text="olá mundo", token_count=2)


def test_chunk_e_imutavel():
    c = _chunk()
    with pytest.raises(ValidationError):
        c.text = "mudei"  # frozen=True proíbe reatribuição após criado


def test_embedded_chunk_carrega_o_chunk():
    c = _chunk()
    e = EmbeddedChunk(chunk=c, model="text-embedding-3-small", dim=3, embedding=[0.1, 0.2, 0.3])
    assert e.chunk.id == "c1"
    assert e.dim == len(e.embedding) == 3


def test_answer_tem_contextos_vazios_por_padrao():
    a = Answer(question="qual o prazo?", text="30 dias")
    assert a.contexts == []


def test_retrieved_exige_score():
    with pytest.raises(ValidationError):
        Retrieved(chunk=_chunk(), source="dense")  # faltou o score obrigatório
