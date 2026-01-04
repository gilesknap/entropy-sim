"""Wire component model."""

from typing import Literal

from entropy_sim.object_type import ObjectType

from .base_connector import BaseConnector


class Wire(BaseConnector):
    """A wire connecting two connection points."""

    object_type: Literal[ObjectType.WIRE] = ObjectType.WIRE
