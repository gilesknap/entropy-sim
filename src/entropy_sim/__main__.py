"""Interface for ``python -m entropy_sim``."""

from argparse import ArgumentParser
from collections.abc import Sequence

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
    parser = ArgumentParser(description="Entropy Simulation - Circuit Builder")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the web server on (default: 8080)",
    )
    parser.parse_args(args)

    # Import and run the canvas application
    from .canvas import run

    run()


if __name__ == "__main__":
    main()
