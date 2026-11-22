# py_sw_timecode

Generate and parse non-drop SMPTE timecodes (`HH:MM:SS:FF`) for video and audio synchronization.

```python
from py_sw_timecode import FrameRate, Timecode, parse_timecode

tc = parse_timecode("01:02:03:04", FrameRate.FPS_25)
print(tc.to_string())          # 01:02:03:04
print(tc.frames)               # 93079
print(tc.offset(50).to_string())  # 01:02:05:04
print(Timecode(0).to_string())    # 00:00:00:00
```

## Why this exists

A timecode is really just a frame count plus a frame rate. Storing the
count and deriving `HH:MM:SS:FF` on demand means the printed form can never
drift from the arithmetic: `offset`, comparison, and hashing all operate on
the same integer. The trade-off is that the hour field wraps at 24 when
printed, so two timecodes a day apart compare unequal but print identically.
That is the SMPTE convention, and keeping it means `Timecode` works as a
dict key without a separate canonical form.

Drop-frame is not implemented. Drop-frame is a labeling scheme for 29.97
and 59.94 material, not a different frame count, and mixing it into the
same type would force every caller to branch on it. Callers who need
drop-frame labels can convert at the boundary.

## The awkward edge

`parse_timecode` requires exactly two digits per field. `"1:02:03:04"` is
rejected; `"01:02:03:04"` is accepted. This keeps round-tripping
unambiguous, which matters more here than lenient input.

Comparing timecodes at different frame rates raises `ValueError` rather
than guessing a conversion. Convert explicitly first.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

