"""SMPTE timecode generation and parsing.

Exports:
    Timecode: value type for a SMPTE timecode at a given frame rate.
    FrameRate: supported frame rates.
    parse_timecode: parse a timecode string into a Timecode.
"""

from .core import FrameRate, Timecode, parse_timecode

__all__ = ["FrameRate", "Timecode", "parse_timecode"]
