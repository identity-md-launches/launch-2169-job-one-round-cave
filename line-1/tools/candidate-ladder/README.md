# Candidate Ladder

Compare **2 to 16 candidate systems against one baseline** on the same binary
benchmark cases. Each candidate gets an exact paired McNemar test; Holm's
step-down adjustment controls the familywise false-positive rate for the
prespecified family. Python 3.9+ and the standard library are the only runtime
requirements. The tool reads one workspace CSV and writes JSON to stdout.

From the repository root, see it work with a clearly synthetic benchmark:

```sh
python3 -B line-1/tools/candidate-ladder/candidate_ladder.py --demo
```

When tried locally, this ran 40 paired cases against three candidates. The
baseline passed 20. `swift` passed 32 with 12 candidate-only wins and no losses:
exact two-sided p = 1/2048; Holm-adjusted p = 3/2048 = 0.00146484375, so it
passes the prespecified familywise alpha 0.05. `steady` passed 26 but its
adjusted p was 7/32 = 0.21875; `noisy` passed 20 and had adjusted p = 1.
These are invented observations for demonstration, not evidence about real systems.

## Your own cases

Use one row for each independent case. Evaluate the baseline and **every**
candidate once, under the same pass rule. Candidate columns are one planned
comparison family, in the order given in the header. For example:

```csv
case,baseline,parser-a,parser-b
empty,1,1,1
unicode,0,1,0
truncated,1,0,1
```

Run your own workspace file with:

```sh
python3 -B line-1/tools/candidate-ladder/candidate_ladder.py --input path/to/results.csv --alpha 0.05
```

The file must be UTF-8 (a BOM is accepted), at most 2 MiB, with 1 to 10,000
unique case IDs and 2 to 16 distinct candidate names. IDs cannot be empty or
have edge whitespace or control characters. Outcomes must be literal `0` or
`1`; missing and extra fields fail. The input path must resolve inside the
current working directory. Invalid input exits 2 without a JSON report. A
valid report exits 0 regardless of which candidate, if any, has evidence.

For each candidate, the report keeps paired wins and losses, an effect in
percentage points, the exact two-sided p-value, the exact Holm-adjusted
p-value, and the familywise decision. Fractions are exact integer strings;
16-digit decimal strings are for reading only. Ties in p-value keep CSV column
order. The SHA-256 identifies the exact input bytes, including line endings;
it does not verify that measurements are truthful.

Choose the benchmark, pass rule, candidate family and alpha **before** seeing
outcomes. Include all planned candidates in the CSV. Holm protects against
false positives across that family under valid per-candidate p-values, including
dependent candidate comparisons. It does not correct a chosen subset, repeated
looks, correlated case pairs, cherry-picked cases, or experiments outside this
family. A non-significant result does not prove equivalence. Compare effect
size and practical costs before choosing a system.

## Verification

```sh
python3 -B -m unittest discover -s line-1/tools/candidate-ladder -v
```

Six tests passed locally. They check the demo, exact p-values against exhaustive
fair-coin enumeration through eight discordant pairs, exact alpha boundaries,
stable ties, malformed CSV, limits, and no-discordance cases. No network,
wallet, key, account, or transaction is used.
