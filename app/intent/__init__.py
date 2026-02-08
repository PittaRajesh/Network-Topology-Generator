"""Intent-Based Networking module.

This module enables users to specify high-level networking goals
(intent) rather than explicitly designing topologies.
"""

from .parser import IntentParser

__all__ = ["IntentParser"]
