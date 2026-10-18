"""Tests for exact familywise comparisons; run with unittest discover."""

import itertools
import unittest
from decimal import Decimal
from fractions import Fraction

import candidate_ladder as ladder


class CandidateLadderTests(unittest.TestCase):
    def test_demo_known_decisions(self):
        raw = ladder.demo_csv()
        names, rows = ladder.read_csv_bytes(raw)
        report = ladder.analyze(raw, names, rows, Decimal('0.05'))
        self.assertEqual((report['paired_cases'], report['baseline_passes']), (40, 20))
        swift, steady, noisy = report['candidates']
        self.assertEqual((swift['candidate_only_pass'], swift['baseline_only_pass']), (12, 0))
        self.assertEqual(swift['holm_adjusted_p']['decimal_16_digits'], '0.00146484375')
        self.assertEqual(steady['holm_adjusted_p']['decimal_16_digits'], '0.21875')
        self.assertEqual(noisy['holm_adjusted_p']['decimal_16_digits'], '1')
        self.assertEqual([x['familywise_reject_equal_discordance'] for x in report['candidates']],
                         [True, False, False])

    def test_exact_p_matches_enumerated_fair_coin_sequences(self):
        for discordant in range(9):
            for wins in range(discordant + 1):
                losses = discordant - wins
                tail = sum(1 for seq in itertools.product((0, 1), repeat=discordant)
                           if sum(seq) <= min(wins, losses))
                oracle = min(Fraction(1), Fraction(2 * tail, 2 ** discordant))
                self.assertEqual(ladder.exact_mcnemar(wins, losses), oracle)

    def test_holm_boundary_is_compared_exactly(self):
        raw = ladder.demo_csv()
        names, rows = ladder.read_csv_bytes(raw)
        equal = ladder.analyze(raw, names, rows, Decimal('0.00146484375'))
        below = ladder.analyze(raw, names, rows, Decimal('0.00146484374'))
        self.assertTrue(equal['candidates'][0]['familywise_reject_equal_discordance'])
        self.assertFalse(below['candidates'][0]['familywise_reject_equal_discordance'])

    def test_tied_p_values_have_stable_ranks_and_adjusted_p(self):
        raw = b'case,baseline,a,b\nx,0,1,1\ny,0,1,1\n'
        names, rows = ladder.read_csv_bytes(raw)
        items = ladder.analyze(raw, names, rows, Decimal('0.05'))['candidates']
        self.assertEqual([x['holm_rank'] for x in items], [1, 2])
        self.assertEqual([x['holm_adjusted_p']['decimal_16_digits'] for x in items], ['1', '1'])

    def test_parser_rejects_incomplete_and_duplicate_cases(self):
        for raw in (b'case,baseline,a,b\nx,1,0\n',
                    b'case,baseline,a,b\nx,1,0,1\nx,0,1,0\n',
                    b'case,baseline,a,b\nx,1,0,\n',
                    b'case,baseline,a,a\nx,1,0,1\n',
                    b'case,baseline,a,b\n x,1,0,1\n',
                    b'case,baseline,a,b\nx,1,0,2\n'):
            with self.subTest(raw=raw), self.assertRaises(ladder.InputError):
                ladder.read_csv_bytes(raw)

    def test_limits_and_no_discordance(self):
        with self.assertRaises(ladder.InputError):
            ladder.read_csv_bytes(b'x' * (ladder.MAX_BYTES + 1))
        with self.assertRaises(ladder.InputError):
            ladder.read_csv_bytes(b'case,baseline,a\nx,0,1\n')
        raw = b'case,baseline,a,b\nx,1,1,1\n'
        names, rows = ladder.read_csv_bytes(raw)
        items = ladder.analyze(raw, names, rows, Decimal('0.05'))['candidates']
        self.assertTrue(all(x['exact_two_sided_p']['decimal_16_digits'] == '1' for x in items))


if __name__ == '__main__':
    unittest.main()
