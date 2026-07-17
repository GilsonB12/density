"""Testes da configuração (Pydantic Settings)."""

from density.config import Settings


def test_defaults_carregam(monkeypatch):
    # Ignora .env e variáveis do ambiente para testar os defaults do código.
    for var in ("DATABASE_URL", "EMBEDDING_MODEL", "EMBEDDING_DIM"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.database_url.startswith("postgresql://")
    assert s.embedding_model == "text-embedding-3-small"
    assert s.embedding_dim == 1536


def test_variavel_de_ambiente_sobrescreve_default(monkeypatch):
    monkeypatch.setenv("EMBEDDING_DIM", "768")
    s = Settings(_env_file=None)
    assert s.embedding_dim == 768  # veio do ambiente, não do default
