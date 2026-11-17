"""Core SMPTE timecode value type.

A timecode is a count of frames plus a nominal frame rate. We store the
frame count as an integer and derive HH:MM:SS:FF on demand. Storing the
derived fields would let them drift out of sync with the count, so we do not.

Drop-frame is deliberately not implemented. Real drop-frame arithmetic is a
labeling scheme (skip two frame numbers per minute except every tenth
minute) that only applies to 29.97 and 59.94. Mixing it into the same type
as non-drop would force every caller to reason about which branch they are
on. Callers who need drop-frame labels should convert at the boundary.
"""

from __future__ import annotations

from enum import Enum


class FrameRate(Enum):
    """Supported nominal frame rates.

    The value is the integer frame rate used for timecode arithmetic. The
    29.97 and 59.94 entries are the NTSC rates; their timecode labels are
    still counted at 30 and 60 fps respectively, which is the standard
    non-drop convention.
    """

    FPS_24 = 24
    FPS_25 = 25
    FPS_30 = 30
    FPS_50 = 50
    FPS_60 = 60

    @property
    def frames_per_second(self) -> int:
        return self.value

    @property
    def frames_per_hour(self) -> int:
        return self.value * 3600


def _validate_frame_count(frames: int) -> None:
    if isinstance(frames, bool) or not isinstance(frames, int):
        raise TypeError("frames must be an int")
    if frames < 0:
        raise ValueError("frames must be non-negative")


class Timecode:
    """A non-drop SMPTE timecode.

    Instances are immutable in practice: every operation returns a new
    Timecode rather than mutating in place. Equality and hashing use the
    (frame count, frame rate) pair so a Timecode can be a dict key.
    """

    __slots__ = ("_frames", "_rate")

    def __init__(self, frames: int, rate: FrameRate = FrameRate.FPS_25) -> None:
        if not isinstance(rate, FrameRate):
            raise TypeError("rate must be a FrameRate")
        _validate_frame_count(frames)
        self._frames = frames
        self._rate = rate

    @property
    def frames(self) -> int:
        return self._frames

    @property
    def rate(self) -> FrameRate:
        return self._rate

    def _split(self) -> tuple[int, int, int, int]:
        fps = self._rate.frames_per_second
        total = self._frames
        ff = total % fps
        total //= fps
        ss = total % 60
        total //= 60
        mm = total % 60
        total //= 60
        hh = total % 24
        return hh, mm, ss, ff

    def to_string(self) -> str:
        """Render as HH:MM:SS:FF.

        The hour field wraps at 24, matching the SMPTE convention that a
        timecode is a time-of-day label. The underlying frame count keeps
        growing, so two timecodes one day apart compare unequal even though
        they print the same.
        """
        hh, mm, ss, ff = self._split()
        return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"Timecode({self._frames}, rate={self._rate.name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        return self._frames == other._frames and self._rate is other._rate

    def __hash__(self) -> int:
        return hash((self._frames, self._rate))

    def __lt__(self, other: Timecode) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        if self._rate is not other._rate:
            raise ValueError("cannot compare timecodes at different frame rates")
        return self._frames < other._frames

    def __le__(self, other: Timecode) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        if self._rate is not other._rate:
            raise ValueError("cannot compare timecodes at different frame rates")
        return self._frames <= other._frames

    def __gt__(self, other: Timecode) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        if self._rate is not other._rate:
            raise ValueError("cannot compare timecodes at different frame rates")
        return self._frames > other._frames

    def __ge__(self, other: Timecode) -> bool:
        if not isinstance(other, Timecode):
            return NotImplemented
        if self._rate is not other._rate:
            raise ValueError("cannot compare timecodes at different frame rates")
        return self._frames >= other._frames

    def offset(self, frames: int) -> "Timecode":
        """Return a new timecode shifted by ``frames``.

        Negative offsets are allowed as long as the result stays
        non-negative; going below zero raises ValueError rather than
        wrapping around, because a negative timecode is meaningless and
        silently wrapping hides bugs in edit lists.
        """
        if isinstance(frames, bool) or not isinstance(frames, int):
            raise TypeError("frames must be an int")
        result = self._frames + frames
        if result < 0:
            raise ValueError("offset would produce a negative timecode")
        return Timecode(result, self._rate)

    def seconds(self) -> float:
        """Return the elapsed seconds as a float.

        This is the real-time duration assuming the nominal frame rate, not
        the 1000/1001 NTSC pull-down. Callers who need exact wall-clock
        seconds for 29.97 material must divide by 30000/1001 themselves.
        """
        return self._frames / self._rate.frames_per_second


_TC_RE_GROUPS = 4


def parse_timecode(text: str, rate: FrameRate = FrameRate.FPS_25) -> Timecode:
    """Parse ``HH:MM:SS:FF`` into a Timecode at the given rate.

    The frame field must be less than the rate's frames per second. Minutes
    and seconds must be 0-59. Hours are 0-23. Leading zeros are required to
    the width shown in the format, so ``1:02:03:04`` is rejected while
    ``01:02:03:04`` is accepted; this keeps round-tripping unambiguous.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if not isinstance(rate, FrameRate):
        raise TypeError("rate must be a FrameRate")

    parts = text.split(":")
    if len(parts) != _TC_RE_GROUPS:
        raise ValueError(f"expected HH:MM:SS:FF, got {text!r}")

    for part in parts:
        if len(part) != 2 or not part.isdigit():
            raise ValueError(f"expected two-digit field, got {part!r}")

    hh, mm, ss, ff = (int(p) for p in parts)
    if hh > 23:
        raise ValueError("hours must be 0-23")
    if mm > 59:
        raise ValueError("minutes must be 0-59")
    if ss > 59:
        raise ValueError("seconds must be 0-59")
    fps = rate.frames_per_second
    if ff >= fps:
        raise ValueError(f"frames must be 0-{fps - 1}")

    total = ((hh * 60 + mm) * 60 + ss) * fps + ff
    return Timecode(total, rate)
