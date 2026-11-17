"""Tests for py_sw_timecode.core."""

import unittest

from py_sw_timecode import FrameRate, Timecode, parse_timecode


class TestConstruction(unittest.TestCase):
    def test_default_rate_is_25(self):
        tc = Timecode(0)
        self.assertIs(tc.rate, FrameRate.FPS_25)

    def test_rejects_negative_frames(self):
        with self.assertRaises(ValueError):
            Timecode(-1)

    def test_rejects_non_int_frames(self):
        with self.assertRaises(TypeError):
            Timecode(1.5)  # type: ignore[arg-type]

    def test_rejects_bool_frames(self):
        with self.assertRaises(TypeError):
            Timecode(True)  # type: ignore[arg-type]

    def test_rejects_bad_rate(self):
        with self.assertRaises(TypeError):
            Timecode(0, rate=25)  # type: ignore[arg-type]

    def test_frames_per_second_matches_value(self):
        self.assertEqual(FrameRate.FPS_30.frames_per_second, 30)
        self.assertEqual(FrameRate.FPS_30.frames_per_hour, 108000)


class TestFormatting(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(Timecode(0).to_string(), "00:00:00:00")

    def test_simple(self):
        tc = Timecode(1 * 25 * 3600 + 2 * 25 * 60 + 3 * 25 + 4)
        self.assertEqual(tc.to_string(), "01:02:03:04")

    def test_last_frame_of_a_second(self):
        self.assertEqual(Timecode(24).to_string(), "00:00:00:24")

    def test_rolls_into_next_second(self):
        self.assertEqual(Timecode(25).to_string(), "00:00:01:00")

    def test_hour_wraps_at_24(self):
        tc = Timecode(24 * 25 * 3600)
        self.assertEqual(tc.to_string(), "00:00:00:00")

    def test_str_matches_to_string(self):
        tc = Timecode(1234)
        self.assertEqual(str(tc), tc.to_string())

    def test_repr_is_informative(self):
        self.assertEqual(repr(Timecode(5, FrameRate.FPS_30)),
                         "Timecode(5, rate=FPS_30)")


class TestEqualityAndHashing(unittest.TestCase):
    def test_equal_when_same_frames_and_rate(self):
        self.assertEqual(Timecode(10, FrameRate.FPS_24),
                         Timecode(10, FrameRate.FPS_24))

    def test_unequal_across_rates(self):
        self.assertNotEqual(Timecode(10, FrameRate.FPS_24),
                            Timecode(10, FrameRate.FPS_25))

    def test_unequal_to_other_type(self):
        self.assertNotEqual(Timecode(0), "00:00:00:00")

    def test_usable_as_dict_key(self):
        d = {Timecode(1): "a"}
        self.assertEqual(d[Timecode(1)], "a")


class TestOrdering(unittest.TestCase):
    def test_orders_within_same_rate(self):
        self.assertLess(Timecode(1), Timecode(2))
        self.assertLessEqual(Timecode(2), Timecode(2))
        self.assertGreater(Timecode(3), Timecode(2))
        self.assertGreaterEqual(Timecode(2), Timecode(2))

    def test_cross_rate_comparison_raises(self):
        with self.assertRaises(ValueError):
            Timecode(1, FrameRate.FPS_24) < Timecode(1, FrameRate.FPS_25)


class TestOffset(unittest.TestCase):
    def test_positive_offset(self):
        self.assertEqual(Timecode(10).offset(5), Timecode(15))

    def test_negative_offset(self):
        self.assertEqual(Timecode(10).offset(-5), Timecode(5))

    def test_zero_offset_is_equal(self):
        self.assertEqual(Timecode(10).offset(0), Timecode(10))

    def test_offset_below_zero_raises(self):
        with self.assertRaises(ValueError):
            Timecode(3).offset(-4)

    def test_offset_rejects_non_int(self):
        with self.assertRaises(TypeError):
            Timecode(3).offset(1.0)  # type: ignore[arg-type]


class TestSeconds(unittest.TestCase):
    def test_exact_seconds_at_25(self):
        self.assertAlmostEqual(Timecode(50).seconds(), 2.0)

    def test_exact_seconds_at_24(self):
        self.assertAlmostEqual(Timecode(48, FrameRate.FPS_24).seconds(), 2.0)


class TestParse(unittest.TestCase):
    def test_round_trip(self):
        tc = parse_timecode("01:02:03:04", FrameRate.FPS_25)
        self.assertEqual(tc.rate, FrameRate.FPS_25)
        self.assertEqual(tc.to_string(), "01:02:03:04")

    def test_zero(self):
        self.assertEqual(parse_timecode("00:00:00:00"), Timecode(0))

    def test_frame_boundary(self):
        self.assertEqual(parse_timecode("00:00:00:24"), Timecode(24))

    def test_rejects_frame_too_large(self):
        with self.assertRaises(ValueError):
            parse_timecode("00:00:00:25", FrameRate.FPS_25)

    def test_rejects_wrong_field_count(self):
        with self.assertRaises(ValueError):
            parse_timecode("00:00:00")

    def test_rejects_short_fields(self):
        with self.assertRaises(ValueError):
            parse_timecode("1:02:03:04")

    def test_rejects_non_digits(self):
        with self.assertRaises(ValueError):
            parse_timecode("aa:00:00:00")

    def test_rejects_out_of_range_minutes(self):
        with self.assertRaises(ValueError):
            parse_timecode("00:60:00:00")

    def test_rejects_out_of_range_hours(self):
        with self.assertRaises(ValueError):
            parse_timecode("24:00:00:00")

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            parse_timecode(1234)  # type: ignore[arg-type]

    def test_rejects_bad_rate(self):
        with self.assertRaises(TypeError):
            parse_timecode("00:00:00:00", rate=25)  # type: ignore[arg-type]

    def test_parse_then_format_is_stable(self):
        for text in ("00:00:00:00", "12:34:56:07", "23:59:59:23"):
            self.assertEqual(parse_timecode(text).to_string(), text)


if __name__ == "__main__":
    unittest.main()
