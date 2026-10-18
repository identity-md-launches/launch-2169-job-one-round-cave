"""Cross-line checks for exact units, asserted intervals and Unicode evidence."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

import reviewed_timeline as r


class ClockBoundChecks(unittest.TestCase):
    INPUTS = [("client.log", b"2026-10-18T10:00:00Z owner accepted\n"),
              ("server.jsonl", b'{"ts":"2026-10-18T10:00:02Z",'
               b'"message":"owner \\u043ewner \\u202ehidden\\u202c"}\n')]

    def test_equivalent_units_and_exact_arithmetic(self):
        for expression in ("750 ms", "0.75 s", "1 s - 250 ms", "3 / 4 * s", "0.0125 min"):
            self.assertEqual(r.parse_clock_bound(expression), 750)
        self.assertEqual(r.parse_clock_bound("1 day"), 86_400_000)
        self.assertEqual(r.parse_clock_bound("0 ms"), 0)

    def test_wrong_dimensions_sub_ms_negative_and_large_bounds_fail(self):
        for expression in ("750", "1 m", "1 s / m", "0.1 ms", "-1 ms", "1 day + 1 ms",
                           "1 / 0 * s", "(" * 40 + "1 s" + ")" * 40):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                r.parse_clock_bound(expression)

    def test_clock_bound_joins_groups_without_changing_evidence(self):
        original = r.build(self.INPUTS)
        adjusted = r.build(self.INPUTS, clock_uncertainty_ms=r.parse_clock_bound("0.75 s"))
        self.assertEqual([e["overlap_group"] for e in original["timeline"]["events"]], [1, 2])
        self.assertEqual([e["overlap_group"] for e in adjusted["timeline"]["events"]], [1, 1])
        self.assertEqual(original["source_reviews"], adjusted["source_reviews"])
        self.assertEqual(adjusted["timeline"]["clock_model"]["uncertainty_ms"], 750)
        self.assertEqual(adjusted["timeline"]["version"], 2)
        for before, after in zip(original["timeline"]["events"], adjusted["timeline"]["events"]):
            self.assertEqual(after["reported_start_utc"], before["start_utc"])
            self.assertEqual(after["reported_end_utc_exclusive"], before["end_utc_exclusive"])
            for key in ("line_sha256", "source_review_sha256", "message_escaped", "message_review"):
                self.assertEqual(before[key], after[key])
        self.assertEqual(adjusted["timeline"]["events"][1]["message_review"]["finding_count"], 4)

    def test_half_open_clock_adjusted_adjacency(self):
        report = r.build(self.INPUTS, clock_uncertainty_ms=500)
        self.assertEqual([e["overlap_group"] for e in report["timeline"]["events"]], [1, 2])

    def test_zero_bound_preserves_timeline_shape(self):
        self.assertEqual(r.build(self.INPUTS), r.build(self.INPUTS, clock_uncertainty_ms=0))
        self.assertNotIn("clock_model", r.build(self.INPUTS)["timeline"])

    def test_calendar_model_overflow_is_fatal_even_with_omissions(self):
        with self.assertRaises(r.time_flint.TimelineError):
            r.build([("edge", b"0001-01-01T00:00:00Z event")], True, 1)

    def test_invalid_model_is_rejected_before_opening_files(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(r, "workspace_inputs", side_effect=AssertionError("must not read")), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(r.main(["example.log", "--clock-bound", "1 m"]), 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("time dimensions", json.loads(err.getvalue())["error"])

    def test_cli_review_and_clock_expression_are_both_visible(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(r, "workspace_inputs", return_value=self.INPUTS), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(r.main(["example.log", "--clock-bound", "1 s - 250 ms"]), 1)
        report = json.loads(out.getvalue())
        self.assertEqual(err.getvalue(), "")
        self.assertEqual(report["clock_bound"]["milliseconds"], 750)
        self.assertEqual(report["assessment"], "review-required")
        self.assertTrue(out.getvalue().isascii())


if __name__ == "__main__":
    unittest.main()
