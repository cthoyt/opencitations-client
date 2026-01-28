"""Access and download data from OpenCitations."""

from .api import hello, square

# being explicit about exports is important!
__all__ = [
    "hello",
    "square",
]
