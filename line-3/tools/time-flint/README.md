# Time Flint

Time Flint turns UTF-8 log files into a deterministic incident timeline. It reads
data only; it does not import or execute the services that wrote the logs. Each
event carries its source path, line number, and SHA-256 of the original line;
the output also lists each source file's SHA-256. Input order, timestamp precision, and possible ordering
ambiguity remain visible.

See it work with one command from the repository root:

```sh
python3 -B line-3/tools/time-flint/time_flint.py --demo
```

The demo merges a plain log with JSONL. The minute-precision queue event and the
second-precision request event share an overlap group; the tool does not claim
which happened first. I ran the command and the JSON form locally; both completed
without network access. To analyze your own files:

```sh
python3 -B line-3/tools/time-flint/time_flint.py --json service.log queue.jsonl
```

Plain lines start with an ISO 8601 timestamp followed by whitespace and a
message, for example `2026-10-18T12:00:01.123+02:00 event`. JSONL objects have
exactly one `timestamp`, `time`, or `ts` field; `message`, `msg`, or `event` is
used as the description when present. ISO timestamps require `T` and an explicit
`Z` or numeric UTC offset. JSONL also accepts 10-digit integer epoch seconds or
13-digit integer epoch milliseconds. Blank lines are skipped. All other malformed
or untimestamped lines fail the run with a source and line number. The optional
`--ignore-unmatched` flag records every omission with a line hash and reason in
JSON output; it never discards those lines silently.

Each timestamp is represented as a half-open UTC interval, assuming the logger
truncated rather than rounded to its displayed precision. For example, a
timestamp written only to the minute occupies that entire minute; a timestamp
with three fractional digits occupies one millisecond. Events whose intervals
overlap transitively share an `overlap_group`. This identifies a connected cluster,
not a claim that every pair within it overlaps. The displayed sort order inside
that group is only a stable presentation order. Group numbers have no
meaning across different input sets. The JSON form is suitable for review or
further processing; it contains no runtime timestamp or random field.

Limits: this piece accepts only these explicit timestamp forms, not syslog
dates, local time without an offset, leap seconds, or events split over multiple
lines. It uses reported timestamps as evidence; dishonest logs and clock errors
outside an analyst's asserted bound remain outside its claims. Source line hashes are computed after UTF-8 decoding
and stripping line terminators; source file hashes cover the exact input bytes.
No coin is needed for offline log analysis.

## Round 22: calendar bounds and explicit clock uncertainty

The gathering's two calendar failures now produce `TimelineError` and CLI exit
2 with a cited source and line, rather than a traceback. Both UTC endpoints must
fit years 0001 through 9999, including the exclusive end. An interval ending
beyond the last printable microsecond is rejected, without truncating evidence.
With `--ignore-unmatched`, invalid calendar lines appear in `omitted` like other
invalid events. Deep JSON, duplicate keys, NaN and Infinity are rejected.

To see a useful clock-bound example with one command from the repository root:

```sh
python3 -B line-3/tools/time-flint/time_flint.py --clock-uncertainty-ms 750 --json line-3/tools/time-flint/examples/client.txt line-3/tools/time-flint/examples/server.jsonl
```

These two **synthetic** log records are two seconds apart. Without the option
they occupy separate overlap groups. With a 750 ms error bound, their intervals
overlap and share group 1. The first adjusted interval is
`[2026-10-18T09:59:59.250000Z, 2026-10-18T10:00:01.750000Z)`.
I ran both commands locally and observed those results.

`--clock-uncertainty-ms N` asserts that **every source clock is within ±N ms
of UTC at every event**. It does not estimate skew, synchronize clocks, infer
causation or establish request identity. N is an integer from 0 through
86,400,000 (one day). A common conservative bound supports different unknown
errors across sources and events; it does not assume a shared constant offset.
The tool broadens each reported interval `[s,e)` to `[s-N,e+N)` and recomputes
overlap groups. Precision still describes the original logger representation.

Zero (the default) preserves the original version-1 report shape and behavior
for valid inputs. A positive bound emits version 2, with a `clock_model`
describing the assumption and `reported_start_utc` /
`reported_end_utc_exclusive` on every event. File and line hashes, messages,
source citations, and reported precision remain unchanged. A bound pushing an
endpoint outside the calendar is a fatal model error, even with
`--ignore-unmatched`; valid events are never silently omitted to fit the model.

Explicit files must resolve inside the current working directory, which serves
as the workspace root. Symlinks resolving outside it and non-regular files are
rejected; `-` still accepts stdin once. Inputs are bounded to 64 sources, 8 MiB
per source, 32 MiB total, 100,000 physical lines (including blank lines and the
final empty split after a newline), 64 KiB per decoded line, and 64 nested JSON
containers. Limits are fatal even in omission mode. Reads request at most the
remaining byte budget plus one byte. Duplicate source names are rejected.
Diagnostics and terminal tables escape control characters. The byte and line
limits bound resource use; this is not a security sandbox against concurrent
filesystem changes. It never scans directories or reads service configuration.

Regression checks use only the Python standard library (Python 3.10+):

```sh
python3 -B -m unittest discover -s line-3/tools/time-flint -v
```

Observed: 28 tests passed. Coverage includes both reported calendar failures,
valid near-boundary intervals, ISO offsets and epoch units, half-open adjacency,
transitive groups, original evidence hashes, explicit omissions, deterministic
output, widened intervals, preserved reported evidence, bounds that merge or
just touch, invalid bounds, workspace restrictions, capped reads and cumulative
limits. These are offline examples and conformance checks, not a real incident
analysis or an assertion that an input clock meets the selected bound.
