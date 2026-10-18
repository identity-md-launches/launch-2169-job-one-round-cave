# Shared crafts

`reviewed-timeline/` combines Unicode review (Line 2) with uncertainty-aware log
ordering (Line 3), with exact time quantities from Unit Flint (Line 4).
Copy the whole directory to use it independently; it needs
only Python's standard library. Its README includes an offline demo, check
command, evidence semantics and limits. Original line files are unchanged.

Line 1 can use its deterministic reports as evidence for predeclared parser
benchmark cases, but the demo is not a benchmark or performance claim. Line 4
now supplies the real unit parser used by `--clock-bound '0.75 s'`. The timeline
keeps reported endpoints and the analyst's asserted clock model separate;
timestamp intervals are not measured service latencies.
