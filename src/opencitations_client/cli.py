"""Command line interface for :mod:`opencitations_client`."""

import click

__all__ = [
    "main",
]


@click.command()
def main() -> None:
    """CLI for opencitations_client."""


if __name__ == "__main__":
    main()
