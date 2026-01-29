"""Command line interface for :mod:`opencitations_client`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """CLI for opencitations_client."""
    from .download import get_omid_to_pubmed

    omid_to_pubmed = get_omid_to_pubmed(force_process=True)
    click.echo(f"got {len(omid_to_pubmed):,} OMID-PubMed mappings")

    # TODO iterate through citations CSV and map out of OMID
    #  for each row


if __name__ == "__main__":
    main()
