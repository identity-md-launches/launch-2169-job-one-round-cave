"""Offline arithmetic and adversarial input checks; no files or network read."""
import contextlib
from fractions import Fraction
import io
import json
import random
import unittest

from unit_flint import Parser, UnitError, exact_decimal, main


class UnitFlintTests(unittest.TestCase):
    def test_exact_arithmetic_and_conversions(self):
        for expression, expected, dims in [
            ('0.1 + 0.2', Fraction(3, 10), (0, 0, 0, 0)),
            ('1.5 km + 350 m', Fraction(1850), (1, 0, 0, 0)),
            ('10 km / 2 h', Fraction(25, 18), (1, 0, -1, 0)),
            ('1 L - 1000 mL', Fraction(0), (3, 0, 0, 0)),
            ('1 J / 1 s', Fraction(1), (2, 1, -3, 0)),
            ('1 in / 1 ft', Fraction(1, 12), (0, 0, 0, 0)),
            ('2 * m^2', Fraction(2), (2, 0, 0, 0)),
            ('2 m^2', Fraction(4), (2, 0, 0, 0)),
            ('-2^2', Fraction(-4), (0, 0, 0, 0)),
            ('2^3^2', Fraction(512), (0, 0, 0, 0)),
        ]:
            with self.subTest(expression=expression):
                q = Parser(expression).parse()
                self.assertEqual((q.value, q.dims), (expected, dims))

    def test_invalid_arithmetic(self):
        for expression in ('2 m + 3 s', '1 / 0', '0^-1', 'm^0.5',
                           'm^s', 'm^13', 'unknown', '1;print(1)', '()', '1 2'):
            with self.subTest(expression=expression):
                with self.assertRaises(UnitError):
                    Parser(expression).parse()

    def test_all_resource_limits(self):
        for expression, message in [
            ('-' * 1100 + '1', 'tokens'),
            ('-' * 33 + '1', 'nesting'),
            ('(' * 40 + '1' + ')' * 40, 'nesting'),
            ('2^' * 40 + '1', 'nesting'),
            (' ' * 4097, 'characters'),
            ('1+' * 128 + '1', 'tokens'),
            ('(1e100)^12', 'arithmetic budget'),
            ('((1e-100)^12)', 'arithmetic budget'),
            ('((m^12)^12)^2', 'dimension'),
            ('0e-999999999', 'decimal exponent'),
            ('0e999999999', 'decimal exponent'),
        ]:
            with self.subTest(expression=expression[:40]):
                with self.assertRaisesRegex(UnitError, message):
                    Parser(expression).parse()

    def test_boundary_acceptance_and_depth_reset(self):
        self.assertEqual(Parser('-' * 31 + '1').parse().value, -1)
        self.assertEqual(Parser('1+' * 127 + '1').parse().value, 128)
        self.assertEqual(Parser(' ' * 4095 + '1').parse().value, 1)
        self.assertEqual(Parser('(1e100)^6').parse().value, 10**600)
        parser = Parser('(' * 40 + '1' + ')' * 40)
        with self.assertRaises(UnitError):
            parser.parse()
        self.assertEqual(parser.depth, 0)

    def test_cli_json_and_regular_error(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(main(['10 km / 2 h', '--to', 'm/s', '--json']), 0)
        self.assertEqual(json.loads(out.getvalue())['value'], '25/18')
        self.assertEqual(err.getvalue(), '')
        for args in [ ['--', '-' * 1100 + '1'], ['1 m', '--to', 's'],
                      ['1e100', '--to', '(1e-100)^6'], ['1', '--to', 'm+m'] ]:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(main(args), 2)
            self.assertEqual(out.getvalue(), '')
            self.assertIn('unit-flint:', err.getvalue())
            self.assertNotIn('Traceback', err.getvalue())

    def test_exact_formatting_roundtrip(self):
        rng = random.Random(737)
        for _ in range(500):
            value = Fraction(rng.randrange(-100000, 100001), rng.randrange(1, 1000))
            self.assertEqual(Fraction(exact_decimal(value)), value)
        self.assertEqual(exact_decimal(Fraction(1, 8)), '0.125')
        self.assertEqual(exact_decimal(Fraction(1, 3)), '1/3')

    def test_seeded_invalid_input_is_bounded(self):
        rng = random.Random(737)
        for _ in range(1000):
            source = ''.join(rng.choice('0129e+-*/^() ms.') for _ in range(rng.randrange(100)))
            try:
                q = Parser(source).parse()
                exact_decimal(q.value)
            except UnitError:
                pass


if __name__ == '__main__':
    unittest.main()
