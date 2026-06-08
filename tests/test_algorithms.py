import random
import unittest

from bgt.algorithms import MakespanTwoOracle, oracle_reduce_fastest, oracle_reduce_max
from bgt.core import Bamboo, advance_day, create_bamboos, cut, grow


class AlgorithmTests(unittest.TestCase):
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

    def test_makespan_two_regular_schedule_matches_binary_pattern(self) -> None:
        oracle = MakespanTwoOracle([0.5, 0.25, 0.125, 0.125])

        self.assertEqual(
            [oracle.scheduled_index(day) for day in range(8)],
            [0, 1, 0, 2, 0, 1, 0, 3],
        )

    def test_makespan_two_completes_rates_to_dyadic_values_summing_to_one(self) -> None:
        oracle = MakespanTwoOracle([0.7, 0.2, 0.1])

        self.assertEqual(
            [slot.rounded_growth for slot in oracle.slots],
            [0.5, 0.25, 0.25],
        )
        self.assertAlmostEqual(sum(slot.rounded_growth for slot in oracle.slots), 1.0)
        for slot in oracle.slots:
            self.assertLess(slot.normalized_growth, 2 * slot.rounded_growth)

    def test_makespan_two_builds_virtual_tree_for_non_regular_instances(self) -> None:
        oracle = MakespanTwoOracle([0.4, 0.2, 0.15, 0.15, 0.1])

        self.assertGreater(oracle.tree_height, 1)
        self.assertGreater(oracle.node_count, len(oracle.slots))

    def test_makespan_two_respects_each_guaranteed_period(self) -> None:
        oracle = MakespanTwoOracle([0.4, 0.2, 0.15, 0.15, 0.1])
        horizon = 2 * max(slot.period for slot in oracle.slots)

        for slot in oracle.slots:
            scheduled_days = [
                day
                for day in range(horizon)
                if oracle.scheduled_index(day) == slot.bamboo_index
            ]
            gaps = [
                later - earlier
                for earlier, later in zip(scheduled_days, scheduled_days[1:])
            ]
            self.assertTrue(gaps)
            self.assertLessEqual(max(gaps), slot.period)

    def test_makespan_two_guarantee_in_simulation(self) -> None:
        for rates in (
            [0.95, 0.05],
            [0.5, 0.3, 0.2],
            [0.4, 0.2, 0.15, 0.15, 0.1],
            [0.26, 0.24, 0.2, 0.15, 0.1, 0.05],
        ):
            oracle = MakespanTwoOracle(rates)
            bamboos = create_bamboos(rates)
            observed_makespan = 0.0

            for _ in range(2048):
                bamboos, day_makespan, _ = advance_day(bamboos, oracle)
                observed_makespan = max(observed_makespan, day_makespan)

            self.assertLessEqual(observed_makespan, oracle.guaranteed_bound + 1e-12)

    def test_makespan_two_guarantee_for_seeded_random_instances(self) -> None:
        randomizer = random.Random(20260608)

        for _ in range(40):
            raw_rates = [randomizer.random() + 0.01 for _ in range(randomizer.randint(2, 8))]
            total = sum(raw_rates)
            rates = [rate / total for rate in raw_rates]
            oracle = MakespanTwoOracle(rates)
            bamboos = create_bamboos(rates)
            observed_makespan = 0.0

            for _ in range(1024):
                bamboos, day_makespan, _ = advance_day(bamboos, oracle)
                observed_makespan = max(observed_makespan, day_makespan)

            self.assertLessEqual(observed_makespan, 2.0 + 1e-12)


if __name__ == "__main__":
    unittest.main()
