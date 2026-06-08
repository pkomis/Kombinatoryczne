import unittest

from bgt.experiments import (
    experiment_rows,
    experiment_to_csv,
    makespan_two_schedule_rows,
    run_comparison_experiment,
)


class ExperimentTests(unittest.TestCase):
    def test_comparison_experiment_runs_all_algorithms(self) -> None:
        experiment = run_comparison_experiment([0.5, 0.3, 0.2], 50)

        self.assertEqual(set(experiment.runs), {"reduce_max", "reduce_fastest", "makespan_two"})
        for run in experiment.runs.values():
            self.assertEqual(len(run.day_peaks), 50)
            self.assertEqual(len(run.makespans), 50)
            self.assertEqual(len(run.cuts), 50)
            self.assertTrue(all(earlier <= later for earlier, later in zip(run.makespans, run.makespans[1:])))

    def test_experiment_rows_and_csv_are_exportable(self) -> None:
        experiment = run_comparison_experiment([0.5, 0.3, 0.2], 12)

        rows = experiment_rows(experiment)
        csv_text = experiment_to_csv(experiment)

        self.assertEqual(len(rows), 3)
        self.assertIn("day,algorithm,day_peak,makespan,cut_index,cut_label", csv_text)
        self.assertIn("reduce_max", csv_text)
        self.assertIn("makespan_two", csv_text)

    def test_makespan_two_schedule_rows_explain_dyadic_slots(self) -> None:
        rows = makespan_two_schedule_rows([0.5, 0.25, 0.125, 0.125])

        self.assertEqual(
            rows,
            [
                {"bamboo": "b1", "h_i": "0.5000", "h'_i": "0.5000", "period": "2", "route": "1"},
                {"bamboo": "b2", "h_i": "0.2500", "h'_i": "0.2500", "period": "4", "route": "2"},
                {"bamboo": "b3", "h_i": "0.1250", "h'_i": "0.1250", "period": "8", "route": "3"},
                {"bamboo": "b4", "h_i": "0.1250", "h'_i": "0.1250", "period": "8", "route": "4"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
