"""Configuração central do density.

Carrega as settings a partir de variáveis de ambiente / arquivo `.env` usando
Pydantic Settings. Princípio "parse, don't validate": a config externa (não
confiável) é validada UMA vez, aqui na borda, e vira um objeto tipado que o
resto do código consome com segurança.

Ver Vault: [[Pydantic v2]] e [[Camadas, Domínio e Fronteiras]].
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Todas as configurações do density, tipadas e validadas."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variáveis desconhecidas no ambiente
    )

    # Conexão com o Postgres/pgvector (sobe via docker-compose).
    database_url: str = Field(
        default="postgresql://density:density@localhost:5433/density",
        description="DSN do Postgres com a extensão pgvector (porta 5433 no host).",
    )

    # Credenciais de provedores — opcionais até a Etapa 2 (embeddings/geração).
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Modelo de embedding e sua dimensão.
    # A dimensão PRECISA bater com a coluna `vector(n)` no banco.
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536


@lru_cache
def get_settings() -> Settings:
    """Retorna a config carregada (cacheada — lê o ambiente uma única vez)."""
    return Settings()
