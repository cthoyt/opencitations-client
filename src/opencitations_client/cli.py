"""Command line interface for :mod:`opencitations_client`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """Prepare local caches."""
    from .cache import _get_doi_cache, _get_omid_cache, _get_pubmed_cache

    _get_omid_cache()
    _get_pubmed_cache()
    _get_doi_cache()


if __name__ == "__main__":
    main()
