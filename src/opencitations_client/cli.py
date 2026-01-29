"""Command line interface for :mod:`opencitations_client`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """CLI for opencitations_client."""
    from .download import get_pubmed_citations

    edges = get_pubmed_citations(force_process=True)
    click.echo(f"got {len(edges):,} PubMed-PubMed edges")


if __name__ == "__main__":
    main()
