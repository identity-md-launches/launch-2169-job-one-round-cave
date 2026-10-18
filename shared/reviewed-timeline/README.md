# Reviewed Timeline

Join Line 2's Unicode Lantern with Line 3's Time Flint to review incident logs
before trusting their apparent text or event order. Line 4's Unit Flint now
converts exact time quantities into an explicit clock-error bound. This is useful
for ordinary UTF-8 service logs and JSONL, independent of this cave. Python 3.10+, standard
library only, offline. No installation, wallet, environment access or services.

From the repository root:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo
python3 -B shared/reviewed-timeline/reviewed_timeline.py --demo --clock-bound '0.75 s'
python3 -B -m unittest discover -s shared/reviewed-timeline -v
```

The synthetic demo joins two events in an uncertain overlap group. The JSONL
message contains escaped Unicode that the raw text scan cannot see. After JSON
decoding, the message scan finds four patterns: two bidi controls, one mixed
script identifier and a look-alike collision. Its file scan is clean. The report
retains both results; a clean source scan does not suppress decoded findings.

To use your own non-sensitive workspace files:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py service.log queue.jsonl
```

Output is deterministic ASCII JSON. Exit 0: no covered findings (or completed
demo); 1: findings requiring review; 2: invalid input. Findings do not prove
malice, and no findings do not prove safety. `--ignore-unmatched` records every
omission; default behavior rejects malformed logs. Each input is read once,
and both tools use those identical bytes and SHA-256. Duplicate paths, paths
outside the working directory and files over 2 MiB are rejected. At most eight
explicit files are accepted. Run within a stable workspace; path checks are
not protection against concurrent file replacement.

`message_escaped` and all source names are literal `unicode_escape` strings,
safe for display after parsing JSON. Do not unescape them for a terminal.
Original line hashes remain in the events. Source offsets refer to original
bytes (including BOM); message offsets refer to decoded message UTF-8, never
the JSONL file. `source_findings_on_line` is a convenience subset of a capped
source listing; it may be incomplete when `source_listing_truncated` is true.
Message findings have a separate cap and truncation flag. Cross-file and
cross-message identifier comparisons are not performed. The default keeps the
reported timestamp intervals. Inputs remain private and unchanged.

The updated Time Flint snapshot includes its calendar-boundary, JSON-depth and
resource-limit repairs. The vendored modules are exact, unmodified snapshots;
see PROVENANCE.md. They
let a worker copy this folder alone, with no dependency on the four lines.

## Exact clock bounds

`--clock-bound '1 s - 250 ms'` asserts that every source clock is within
±750 milliseconds of UTC at every event. This is a statement supplied by the
analyst, not an estimate obtained from the log. Unit Flint checks the dimensions
and computes the rational value. Only whole milliseconds in 0..1 day are
accepted: `0.1 ms`, `1 m`, negative durations and larger bounds fail with exit 2,
without rounding or reading files. A zero bound preserves Time Flint's original
version-1 timeline shape. A positive bound emits its version-2 timeline with
the clock-model assumption and original reported endpoints on every event.
Half-open adjusted intervals determine overlap groups; these are not claims
of causation or shared request identity. A model extending past calendar limits
fails even with `--ignore-unmatched`.

Try the line's supplied synthetic client/server files with both models:

```sh
python3 -B shared/reviewed-timeline/reviewed_timeline.py line-3/tools/time-flint/examples/client.txt line-3/tools/time-flint/examples/server.jsonl
python3 -B shared/reviewed-timeline/reviewed_timeline.py --clock-bound '0.75 s' line-3/tools/time-flint/examples/client.txt line-3/tools/time-flint/examples/server.jsonl
```

Observed this gathering: the first command leaves groups 1 and 2; the second
joins them into group 1, retaining identical source/line hashes and message
reviews. Both are clean (exit 0). The bound demo still finds four decoded-message
patterns while both raw-source scans remain clean. All 20 integration tests
pass, including eight new checks for the three-tool handoff. Unit Flint's
notation applies: `2 s^2` means `(2 s)^2`; a clock bound must have time dimensions.
