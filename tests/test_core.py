import unittest

from bgt.algorithms import oracle_reduce_max
from bgt.core import (
    advance_day,
    create_bamboos,
    cut,
    grow,
    max_height,
    normalize_rates,
)


class CoreTests(unittest.TestCase):
    def test_grow_and_cut_return_new_bamboos(self) -> None:
        bamboos = create_bamboos([0.6, 0.4])

        grown = grow(bamboos)
        trimmed = cut(grown, 0)

        self.assertEqual([b.height for b in bamboos], [0.0, 0.0])
        self.assertEqual([b.height for b in grown], [0.6, 0.4])
        self.assertEqual([b.height for b in trimmed], [0.0, 0.4])

    def test_advance_day_reports_pre_cut_makespan_and_target(self) -> None:
        next_bamboos, day_makespan, target = advance_day(
            create_bamboos([0.3, 0.7]),
            oracle_reduce_max,
        )

        self.assertEqual(target, 1)
        self.assertAlmostEqual(day_makespan, 0.7)
        self.assertEqual([b.height for b in next_bamboos], [0.3, 0.0])

    def test_normalize_rates_sums_to_one(self) -> None:
        rates = normalize_rates([2, 1, 1])

        self.assertAlmostEqual(sum(rates), 1.0)
        self.assertEqual(rates, [0.5, 0.25, 0.25])

    def test_max_height(self) -> None:
        bamboos = grow(grow(create_bamboos([0.4, 0.2])))

        self.assertAlmostEqual(max_height(bamboos), 0.8)


if __name__ == "__main__":
    unittest.main()

