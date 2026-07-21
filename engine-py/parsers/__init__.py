#!/usr/bin/env python3
"""
Parser package for engine-py.

ParseResult is defined once in common.py (not here) because the parser
scripts in this package are invoked as standalone subprocesses — each does
`sys.path.insert(0, <this dir>); from common import ParseResult` as a flat
module import, since a subprocess has no notion of the enclosing `parsers`
package. This re-export lets pipeline.py (running in-process) use the same
class via the normal `from parsers import ParseResult` package import.
"""
from __future__ import annotations

from .common import ParseResult

__all__ = ["ParseResult"]
