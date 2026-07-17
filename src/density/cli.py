"""CLI do density (Typer + Rich).

Na arquitetura hexagonal, o CLI é um *driving adapter*: uma porta de ENTRADA que
apenas orquestra — traduz argumentos do terminal em chamadas ao núcleo. A lógica
de RAG NÃO vive aqui. Ver Vault: [[Typer e Rich (o CLI)]] e
[[Arquitetura Hexagonal (Ports e Adapters)]].

Na Etapa 0 só `db-check` funciona (prova que a fundação está de pé). Os demais
comandos são stubs, implementados etapa a etapa no roadmap.
"""

from __future__ import annotations

import sys

import typer
from rich.console import Console
from rich.panel import Panel

from .config import get_settings


def _force_utf8_output() -> None:
    """Garante stdout/stderr em UTF-8.

    Em consoles Windows legados (code page cp1252) o Rich quebra ao renderizar
    caracteres fora do cp1252 (setas, alguns traços). Reconfigurar para UTF-8
    torna a CLI portável sem depender da configuração do terminal do usuário.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass  # stream não reconfigurável (ex.: redirecionado) — segue o jogo


app = typer.Typer(
    help="density — RAG production-ready com avaliação rigorosa integrada.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command("db-check")
def db_check() -> None:
    """Testa a conexão com o Postgres e confirma que a extensão pgvector está ativa."""
    # Import tardio: a CLI abre (e `--help` funciona) mesmo sem o driver instalado.
    import psycopg

    settings = get_settings()
    try:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("select version();")
                pg_version = cur.fetchone()[0]
                cur.execute("select extversion from pg_extension where extname = 'vector';")
                row = cur.fetchone()
    except Exception as exc:  # noqa: BLE001 - mensagem amigável em vez de traceback cru
        console.print(
            Panel.fit(
                f"[red]Falha ao conectar.[/]\n{exc}\n\n"
                "O Postgres está no ar? Rode [bold]docker compose up -d[/].",
                title="db-check",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from exc

    if row is None:
        console.print(
            Panel.fit(
                "[yellow]Conectou, mas a extensão [bold]vector[/] NÃO está habilitada.[/]\n"
                "Rode no banco: [bold]CREATE EXTENSION vector;[/]",
                title="db-check",
                border_style="yellow",
            )
        )
        raise typer.Exit(code=1)

    console.print(
        Panel.fit(
            f"[green]OK[/] — pgvector [bold]{row[0]}[/] ativo.\n[dim]{pg_version}[/]",
            title="db-check",
            border_style="green",
        )
    )


def _stub(nome: str, etapa: str) -> None:
    console.print(f"[yellow]'{nome}'[/] ainda não implementado — chega na [bold]{etapa}[/].")
    raise typer.Exit(code=1)


@app.command()
def ingest(path: str = typer.Argument(..., help="Arquivo ou pasta a ingerir")) -> None:
    """(Etapa 1) Ingestão + chunking de documentos."""
    _stub("ingest", "Etapa 1 — Ingestão + Chunking")


@app.command()
def search(query: str = typer.Argument(..., help="Consulta em linguagem natural")) -> None:
    """(Etapa 3/4) Busca (densa → híbrida) sobre os chunks."""
    _stub("search", "Etapa 3 — Dense retrieval")


@app.command()
def ask(question: str = typer.Argument(..., help="Pergunta a responder")) -> None:
    """(Etapa 6) Resposta/sumário fundamentado nos documentos (grounded)."""
    _stub("ask", "Etapa 6 — Geração")


@app.command("eval")
def eval_(dataset: str = typer.Argument("", help="Golden dataset para avaliar")) -> None:
    """(Etapa 7) Avaliação com RAGAS + métricas próprias."""
    _stub("eval", "Etapa 7 — Avaliação")


def main() -> None:
    """Ponto de entrada do console_script `density` (ver pyproject.toml)."""
    _force_utf8_output()
    app()


if __name__ == "__main__":
    main()
