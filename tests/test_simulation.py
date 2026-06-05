import unittest

from app import (
    Bamboo,
    advance_day,
    create_bamboos,
    cut,
    grow,
    max_height,
    normalize_rates,
    oracle_optimal,
    oracle_reduce_fastest,
    oracle_reduce_max,
)


class SimulationTests(unittest.TestCase):
    def test_grow_and_cut_return_new_bamboos(self) -> None:
        bamboos = create_bamboos([0.6, 0.4])

        grown = grow(bamboos)
        trimmed = cut(grown, 0)

        self.assertEqual([b.height for b in bamboos], [0.0, 0.0])
        self.assertEqual([b.height for b in grown], [0.6, 0.4])
        self.assertEqual([b.height for b in trimmed], [0.0, 0.4])

    def test_reduce_max_picks_tallest_bamboo(self) -> None:
        bamboos = cut(grow(create_bamboos([0.25, 0.75])), 0)

        self.assertEqual(oracle_reduce_max(bamboos), 1)

    def test_reduce_fastest_prefers_fastest_eligible_bamboo(self) -> None:
        bamboos = [
            Bamboo(id=0, growth=0.2, height=1.4),
            Bamboo(id=1, growth=0.7, height=1.1),
            Bamboo(id=2, growth=0.1, height=1.8),
        ]

        self.assertEqual(oracle_reduce_fastest(1.0)(bamboos), 1)

    def test_reduce_fastest_falls_back_to_reduce_max(self) -> None:
        bamboos = grow(create_bamboos([0.2, 0.7, 0.1]))

        self.assertEqual(oracle_reduce_fastest(2.0)(bamboos), 1)

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

    def test_max_height_and_optimal_oracle(self) -> None:
        bamboos = grow(grow(create_bamboos([0.4, 0.2])))

        self.assertAlmostEqual(max_height(bamboos), 0.8)
        self.assertEqual(oracle_optimal(bamboos), 0)


if __name__ == "__main__":
    unittest.main()
