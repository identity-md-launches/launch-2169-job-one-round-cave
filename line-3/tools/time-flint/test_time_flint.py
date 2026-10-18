"""Offline contract checks: evidence, UTC bounds, limits, and clock assumptions."""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import time_flint as t


class CalendarChecks(unittest.TestCase):
    def test_calendar_extremes_are_normal_validation_errors(self):
        for stamp in ("9999-12-31T23:59:59Z", "9999-12-31T23:59:59.999999Z",
                      "0001-01-01T00:00:00+01:00", "9999-12-31T23:00:00-02:00"):
            with self.subTest(stamp=stamp), self.assertRaises(t.TimelineError):
                t.build([("edge", (stamp + " event\n").encode())])

    def test_representable_near_extremes_are_kept(self):
        for stamp in ("0001-01-01T00:00:00Z", "9999-12-31T23:59:58Z",
                      "9999-12-31T23:59:59.999998Z"):
            start, end, _ = t.parse_stamp(stamp)
            self.assertLess(start, end)
            self.assertTrue(t.MIN_MICROS <= start < end <= t.MAX_MICROS)

    def test_offset_equivalence(self):
        self.assertEqual(t.parse_stamp("2026-10-18T12:00:00+02:00"),
                         t.parse_stamp("2026-10-18T10:00:00Z"))

    def test_precision_widths(self):
        for suffix, width in (("10:00Z", 60000000), ("10:00:00Z", 1000000),
                              ("10:00:00.123Z", 1000), ("10:00:00.123456Z", 1)):
            start, end, _ = t.parse_stamp("2026-10-18T" + suffix)
            self.assertEqual(end - start, width)

    def test_epoch_seconds_and_milliseconds(self):
        self.assertEqual(t.parse_stamp(1792317601)[0], t.parse_stamp(1792317601000)[0])
        self.assertEqual(t.parse_stamp(1792317601000)[1] - t.parse_stamp(1792317601000)[0], 1000)

    def test_bad_timestamp_types_and_forms(self):
        for value in (True, None, 1.5, 123, "2026-10-18T10:00:00", "2026-10-18T10:00+24:00",
                      "2026-10-18T10:00+01:60", "2026-10-18T10:00:60Z"):
            with self.subTest(value=value), self.assertRaises(t.TimelineError):
                t.parse_stamp(value)
        with self.assertRaises(t.TimelineError):
            t.parse_stamp(10 ** 5000)

    def test_cli_calendar_failure_has_exit_two_without_traceback(self):
        stderr = io.StringIO()
        with patch.object(t, "read_inputs", return_value=[("edge", b"9999-12-31T23:59:59Z event")]), \
                contextlib.redirect_stderr(stderr):
            self.assertEqual(t.main(["edge"]), 2)
        self.assertIn("edge:1:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


class EvidenceChecks(unittest.TestCase):
    def test_original_file_and_normalized_line_hashes(self):
        raw = b'\xef\xbb\xbf2026-10-18T10:00:00Z caf\xc3\xa9\r\n'
        result = t.build([("a", raw)])
        self.assertEqual(result["sources"][0]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result["events"][0]["line_sha256"],
                         hashlib.sha256("2026-10-18T10:00:00Z caf\u00e9".encode()).hexdigest())

    def test_half_open_adjacent_intervals(self):
        raw = b"2026-10-18T10:00:00Z a\n2026-10-18T10:00:01Z b"
        self.assertEqual([e["overlap_group"] for e in t.build([("a", raw)])["events"]], [1, 2])

    def test_transitive_overlap_does_not_assert_all_pairs_overlap(self):
        raw = b"2026-10-18T10:00Z wide\n2026-10-18T10:00:01Z a\n2026-10-18T10:00:59Z b"
        self.assertEqual({e["overlap_group"] for e in t.build([("a", raw)])["events"]}, {1})

    def test_deterministic_evidence_and_stable_tie_order(self):
        inputs = [("b", b"2026-10-18T10:00:00Z b"), ("a", b"2026-10-18T10:00:00Z a")]
        result = t.build(inputs)
        self.assertEqual(json.dumps(result), json.dumps(t.build(inputs)))
        self.assertEqual([e["source"] for e in result["events"]], ["a", "b"])

    def test_omissions_cite_calendar_errors(self):
        raw = b"bad\n9999-12-31T23:59:59Z edge\n2026-10-18T10:00:00Z valid"
        result = t.build([("a", raw)], ignore_unmatched=True)
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual([o["line"] for o in result["omitted"]], [1, 2])
        self.assertEqual(result["omitted"][0]["line_sha256"], hashlib.sha256(b"bad").hexdigest())

    def test_invalid_utf8_is_fatal_even_in_omission_mode(self):
        with self.assertRaises(t.TimelineError):
            t.build([("a", b"\xff")], ignore_unmatched=True)

    def test_json_duplicates_constants_nesting_and_ambiguous_time_rejected(self):
        lines = ['{"ts":1792317601,"ts":1792317602}', '{"ts":1792317601,"message":NaN}',
                 '{"ts":1792317601,"time":1792317601}',
                 '{"ts":1792317601,"message":' + '[' * 2000 + '0' + ']' * 2000 + '}']
        for raw in lines:
            with self.subTest(prefix=raw[:60]), self.assertRaises(t.TimelineError):
                t.build([("a", raw.encode())])

    def test_cli_escapes_untrusted_diagnostics(self):
        stderr = io.StringIO()
        with patch.object(t, "read_inputs", side_effect=t.TimelineError("bad\x1b[31m\nnext")), \
                contextlib.redirect_stderr(stderr):
            self.assertEqual(t.main(["input"]), 2)
        self.assertNotIn("\x1b", stderr.getvalue())
        self.assertIn("\\u001b", stderr.getvalue())
        self.assertEqual(len(stderr.getvalue().splitlines()), 1)


class ClockChecks(unittest.TestCase):
    RAW = b"2026-10-18T10:00:00Z a\n2026-10-18T10:00:02Z b"

    def test_asserted_bound_can_merge_previously_separate_groups(self):
        baseline = t.build([("a", self.RAW)])
        adjusted = t.build([("a", self.RAW)], clock_uncertainty_ms=750)
        self.assertEqual([e["overlap_group"] for e in baseline["events"]], [1, 2])
        self.assertEqual([e["overlap_group"] for e in adjusted["events"]], [1, 1])
        self.assertEqual(adjusted["events"][0]["start_utc"], "2026-10-18T09:59:59.250000Z")
        self.assertEqual(adjusted["events"][0]["end_utc_exclusive"], "2026-10-18T10:00:01.750000Z")
        self.assertEqual(adjusted["clock_model"]["uncertainty_ms"], 750)
        self.assertEqual(adjusted["version"], 2)

    def test_reported_intervals_and_source_evidence_survive_adjustment(self):
        baseline = t.build([("a", self.RAW)])
        adjusted = t.build([("a", self.RAW)], clock_uncertainty_ms=750)
        self.assertEqual(baseline["sources"], adjusted["sources"])
        for old, new in zip(baseline["events"], adjusted["events"]):
            self.assertEqual(old["start_utc"], new["reported_start_utc"])
            self.assertEqual(old["end_utc_exclusive"], new["reported_end_utc_exclusive"])
            for field in ("source", "line", "line_sha256", "precision", "message"):
                self.assertEqual(old[field], new[field])

    def test_zero_bound_preserves_version_one_shape(self):
        self.assertEqual(t.build([("a", self.RAW)]), t.build([("a", self.RAW)], clock_uncertainty_ms=0))
        self.assertNotIn("clock_model", t.build([("a", self.RAW)]))

    def test_exact_bound_adjacency_stays_separate(self):
        result = t.build([("a", self.RAW)], clock_uncertainty_ms=500)
        self.assertEqual([e["overlap_group"] for e in result["events"]], [1, 2])

    def test_invalid_bounds_rejected(self):
        for value in (True, -1, 86400001, 0.5, "1"):
            with self.subTest(value=value), self.assertRaises(t.TimelineError):
                t.build([], clock_uncertainty_ms=value)

    def test_clock_model_overflow_is_fatal_even_with_ignore_unmatched(self):
        with self.assertRaises(t.TimelineError):
            t.build([("edge", b"0001-01-01T00:00:00Z event")], True, clock_uncertainty_ms=1)


class InputChecks(unittest.TestCase):
    def test_workspace_file_read_and_stdin(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            (root / "a.log").write_bytes(b"hello")
            self.assertEqual(t.read_inputs(["a.log"], root), [("a.log", b"hello")])
        with patch.object(t.sys, "stdin", type("Input", (), {"buffer": io.BytesIO(b"input")})()):
            self.assertEqual(t.read_inputs(["-"]), [("-", b"input")])

    def test_outside_workspace_is_rejected_before_file_read(self):
        root = Path(__file__).resolve().parent
        with self.assertRaises(t.TimelineError):
            t.read_inputs([str(root.parent / "outside.log")], root)

    def test_symlink_escape_and_directory_are_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            (root / "escape").symlink_to(root.parent, target_is_directory=True)
            with self.assertRaises(t.TimelineError):
                t.read_inputs(["escape/outside.log"], root)
            with self.assertRaises(t.TimelineError):
                t.read_inputs(["."], root)

    def test_read_is_capped_before_build(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            (root / "a").write_bytes(b"12345")
            with patch.object(t, "MAX_FILE_BYTES", 4), self.assertRaises(t.TimelineError):
                t.read_inputs(["a"], root)

    def test_cumulative_read_limit(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory).resolve()
            (root / "a").write_bytes(b"123")
            (root / "b").write_bytes(b"456")
            with patch.object(t, "MAX_TOTAL_BYTES", 5), self.assertRaises(t.TimelineError):
                t.read_inputs(["a", "b"], root)

    def test_library_source_byte_line_and_count_limits(self):
        probes = [("MAX_FILE_BYTES", 2, [("a", b"123")]),
                  ("MAX_TOTAL_BYTES", 3, [("a", b"12"), ("b", b"34")]),
                  ("MAX_LINE_BYTES", 2, [("a", b"123")]),
                  ("MAX_LINES", 1, [("a", b"\n")]),
                  ("MAX_SOURCES", 1, [("a", b""), ("b", b"")])]
        for field, value, inputs in probes:
            with self.subTest(field=field), patch.object(t, field, value), self.assertRaises(t.TimelineError):
                t.build(inputs, ignore_unmatched=True)

    def test_duplicate_names_and_invalid_source_types(self):
        for inputs in ([("a", b""), ("a", b"")], [("a", "text")], [(1, b"")]):
            with self.assertRaises(t.TimelineError):
                t.build(inputs)


if __name__ == "__main__":
    unittest.main()
