"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

from ._version import __version__
from .models import LED, Battery, Circuit, Point, Wire

__all__ = ["__version__", "Battery", "Circuit", "LED", "Point", "Wire"]
