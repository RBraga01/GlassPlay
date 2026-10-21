"""Nevermore Halloween experience for Raven Prism."""

from __future__ import annotations

from typing import Any

__all__ = ["NevermoreApp"]


def __getattr__(name: str) -> Any:
    if name == "NevermoreApp":
        from .app import NevermoreApp

        return NevermoreApp
    raise AttributeError(name)
