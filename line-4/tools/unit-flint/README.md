# Unit Flint

Check arithmetic on measurements with exact rational values and explicit dimensions. The command accepts decimal quantities, parentheses, `+`, `-`, `*`, `/`, and integer powers (`^` or `**`). Addition and subtraction require matching dimensions; conversion requires a matching target unit. It evaluates its own small expression grammar and never executes Python code.

Run from the repository root:

```sh
python3 line-4/tools/unit-flint/unit_flint.py '1.5 km + 350 m' --to m
```

When tried locally, that command printed `1850 m`. The command `python3 line-4/tools/unit-flint/unit_flint.py '2 m + 3 s'` exited with an incompatible-dimensions error pointing to the `+`. Use `--json` for an exact machine-readable value, base value, and dimension vector. A repeating value is printed as an exact fraction. Supported units are `mm cm m km in ft mi`, `mg g kg t`, `ms s min h day`, `B KiB MiB GiB`, plus `mL L N J W`. Compound units use arithmetic, for example `10 km / 2 h --to 'm/s'`.

This first piece does not handle offset temperatures, currencies or exchange rates, uncertainty, or arbitrary named units. The magnitude of each input number and each exponent is bounded so accidental huge calculations fail quickly. It uses only Python's standard library and makes no network requests.

## Bounded calculation revision (mark 22)

The gathering's report of an uncaught recursion error is fixed. Inputs now have
limits of 4,096 characters, 256 tokens, and 32 active recursive grammar levels
(parentheses, unary signs and exponent expressions share this budget). Each
exact intermediate numerator and denominator is limited to 2,048 bits; each
dimension exponent must stay within -256..256. Decimal exponents must be within
-200..200, including zero-valued decimals. Existing number-length, magnitude
and integer-power limits still apply. The conversion result shares the arithmetic
budget. Exceeding any budget produces `UnitError`; the CLI prints a location and
exits 2. These are deliberate limits, even if cancellation could make the final
answer small. They bound this calculator's work, not an arbitrary Python caller.

One command demonstrates both ordinary calculations and the repaired failure:

```sh
python3 -B -m unittest discover -s line-4/tools/unit-flint -v
```

Tried locally: all seven tests passed, including the reported 1,100 unary minus
signs, deeply nested parentheses/powers, over-budget rational results and target
conversion, 500 exact formatting round trips, and 1,000 deterministic parser
probes. The documented distance command still prints `1850 m`; speed remains
the exact fraction `25/18 m/s`. These checks establish the covered behavior,
not exhaustive parser correctness or a real-world measurement claim.

**Notation:** `2 m^2` means `(2 m)^2`, which is four square metres in this
grammar. Write `2 * m^2` for two square metres. Use `--` before an expression
beginning with several minus signs so argparse treats it as an expression.
There are no file inputs, environment lookups, network requests or dependencies.
