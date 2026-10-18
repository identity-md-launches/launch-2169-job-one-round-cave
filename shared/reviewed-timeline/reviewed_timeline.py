#!/usr/bin/env python3
"""Offline Unicode evidence joined to an uncertainty-aware incident timeline."""
import argparse
import json
from pathlib import Path
import sys

from vendor import time_flint, unicode_lantern, unit_flint

MAX_FILES = 8
MAX_BYTES = unicode_lantern.MAX_BYTES
DEMO = [
    ("service.log", b"2026-10-18T10:00:00Z owner accepted\n"),
    ("queue.jsonl", b'{"timestamp":"2026-10-18T10:00Z",'
     b'"message":"owner and \\u043ewner \\u202ehidden\\u202c"}\n'),
]


def workspace_inputs(names):
    """Read each explicitly named regular file once, inside the current workspace."""
    if not 1 <= len(names) <= MAX_FILES:
        raise ValueError(f"supply 1..{MAX_FILES} files")
    root = Path.cwd().resolve()
    seen, inputs = set(), []
    for name in names:
        path = Path(name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("input must be a regular file inside the current workspace")
        if path in seen:
            raise ValueError("the same resolved file was supplied twice")
        seen.add(path)
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError(f"input exceeds {MAX_BYTES} bytes")
        inputs.append((path.relative_to(root).as_posix(), raw))
    return inputs


def parse_clock_bound(expression):
    """Convert an exact time quantity into the timeline's integer milliseconds."""
    try:
        quantity = unit_flint.Parser(expression).parse()
    except unit_flint.UnitError as exc:
        raise ValueError(f"clock bound at character {exc.pos + 1}: {exc}") from exc
    if quantity.dims != (0, 0, 1, 0):
        raise ValueError("clock bound must have time dimensions; include a unit such as ms or s")
    milliseconds = quantity.value * 1000
    if not 0 <= milliseconds <= 86_400_000:
        raise ValueError("clock bound must be between 0 ms and 1 day inclusive")
    if milliseconds.denominator != 1:
        raise ValueError("clock bound must be an exact whole number of milliseconds; no rounding is applied")
    return milliseconds.numerator


def build(inputs, ignore_unmatched=False, clock_uncertainty_ms=0):
    if not 1 <= len(inputs) <= MAX_FILES:
        raise ValueError(f"supply 1..{MAX_FILES} files")
    names = [name for name, _ in inputs]
    if len(set(names)) != len(names):
        raise ValueError("source names must be unique")
    reviews = [unicode_lantern.scan(raw, name, 100) for name, raw in inputs]
    try:
        timeline = time_flint.build(inputs, ignore_unmatched, clock_uncertainty_ms)
    except (OverflowError, RecursionError) as exc:
        raise ValueError("calendar boundary or input nesting exceeds supported range") from exc
    source_map = {name: review for name, review in zip(names, reviews)}
    for event in timeline["events"]:
        name = event["source"]
        message = event.pop("message")
        message_review = unicode_lantern.scan(message.encode("utf-8"), "<decoded-message>", 100)
        # A raw JSONL scan cannot see controls written as JSON escape sequences.
        event["message_escaped"] = unicode_lantern.escaped(message)
        event["message_review"] = message_review
        review = source_map[name]
        event["source_review_sha256"] = review["sha256"]
        event["source_findings_on_line"] = [
            f for f in review["findings"] if f["line"] == event["line"]]
        event["source_listing_truncated"] = review["truncated"]
    for entry in timeline["sources"] + timeline["events"] + timeline["omitted"]:
        entry["source"] = unicode_lantern.escaped(entry["source"])
    needs_review = any(r["finding_count"] for r in reviews) or any(
        e["message_review"]["finding_count"] for e in timeline["events"])
    return {
        "schema_version": 1,
        "tool": "reviewed-timeline",
        "assessment": "review-required" if needs_review else "no-covered-patterns-found",
        "source_reviews": reviews,
        "timeline": timeline,
        "limitations": [
            "Synthetic demo only; user files are not assumed honest or complete.",
            "Source findings use original UTF-8 byte offsets; decoded-message findings use message-local offsets.",
            "Message strings and source names are unicode_escape representations, not raw display text.",
            "Findings are heuristic and capped at 100 per source and per message; inspect truncated fields.",
            "Overlap groups connect uncertain intervals; presentation order is not causal order.",
            "A nonzero clock bound is an analyst assumption, not measured skew or a causal-order guarantee.",
            "Full Unicode confusables, multiline events and cross-file identifier collisions are not modeled.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--ignore-unmatched", action="store_true")
    parser.add_argument("--clock-bound", metavar="QUANTITY",
                        help="assert a symmetric UTC clock-error bound, e.g. '0.75 s' (whole ms, 0..1 day)")
    args = parser.parse_args(argv)
    if args.demo and args.files:
        parser.error("--demo cannot be combined with files")
    try:
        # Validate the asserted model before opening any input files.
        bound = parse_clock_bound(args.clock_bound) if args.clock_bound is not None else 0
        result = build(DEMO if args.demo else workspace_inputs(args.files), args.ignore_unmatched, bound)
        if args.clock_bound is not None:
            result["clock_bound"] = {"expression_escaped": unicode_lantern.escaped(args.clock_bound),
                                     "milliseconds": bound,
                                     "conversion": "exact; no rounding"}
    except (OSError, UnicodeError, ValueError, time_flint.TimelineError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 1 if result["assessment"] == "review-required" and not args.demo else 0


if __name__ == "__main__":
    raise SystemExit(main())
