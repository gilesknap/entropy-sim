"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

from ._version import __version__
from .models import LED, Battery, Circuit, Point, Wire
from .object_type import ObjectType
from .viewmodel import CircuitViewModel
from .wire_manager import WireManager

__all__ = [
    "__version__",
    "Battery",
    "Circuit",
    "CircuitViewModel",
    "LED",
    "ObjectType",
    "Point",
    "Wire",
    "WireManager",
]
