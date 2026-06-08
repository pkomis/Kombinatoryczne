from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass

from bgt.algorithms import MakespanTwoOracle, oracle_reduce_fastest, oracle_reduce_max
from bgt.config import ALGO_META
from bgt.core import advance_day, create_bamboos


@dataclass(frozen=True)
class ExperimentRun:
    key: str
    day_peaks: list[float]
    makespans: list[float]
    cuts: list[int]
    best_days: int = 0

    @property
    def final_makespan(self) -> float:
        return self.makespans[-1] if self.makespans else 0.0

    @property
    def average_day_peak(self) -> float:
        if not self.day_peaks:
            return 0.0
        return sum(self.day_peaks) / len(self.day_peaks)


@dataclass(frozen=True)
class ComparisonExperiment:
    rates: list[float]
    days: int
    runs: dict[str, ExperimentRun]


def run_comparison_experiment(
    rates: list[float],
    days: int,
    rf_threshold: float = 1 + 1 / math.sqrt(5),
) -> ComparisonExperiment:
    if days <= 0:
        raise ValueError("Experiment length must be positive.")

    oracles = {
        "reduce_max": oracle_reduce_max,
        "reduce_fastest": oracle_reduce_fastest(rf_threshold),
        "makespan_two": MakespanTwoOracle(rates),
    }
    partial_runs: dict[str, ExperimentRun] = {}

    for key, oracle in oracles.items():
        bamboos = create_bamboos(rates)
        day_peaks: list[float] = []
        makespans: list[float] = []
        cuts: list[int] = []
        current_makespan = 0.0

        for _ in range(days):
            bamboos, day_peak, target = advance_day(bamboos, oracle)
            current_makespan = max(current_makespan, day_peak)
            day_peaks.append(day_peak)
            makespans.append(current_makespan)
            cuts.append(target)

        partial_runs[key] = ExperimentRun(
            key=key,
            day_peaks=day_peaks,
            makespans=makespans,
            cuts=cuts,
        )

    best_day_counts = _count_best_days(partial_runs, days)
    runs = {
        key: ExperimentRun(
            key=run.key,
            day_peaks=run.day_peaks,
            makespans=run.makespans,
            cuts=run.cuts,
            best_days=best_day_counts[key],
        )
        for key, run in partial_runs.items()
    }
    return ComparisonExperiment(rates=list(rates), days=days, runs=runs)


def experiment_rows(experiment: ComparisonExperiment) -> list[dict[str, str]]:
    rows = []
    for key, run in experiment.runs.items():
        meta = ALGO_META[key]
        bound = float(meta["bound"])
        rows.append(
            {
                "Algorithm": meta["label"],
                "Final M": f"{run.final_makespan:.3f}",
                "Avg daily peak": f"{run.average_day_peak:.3f}",
                "M / bound": f"{run.final_makespan / bound:.3f}",
                "Best days": str(run.best_days),
            }
        )
    return sorted(rows, key=lambda row: float(row["Final M"]))


def experiment_to_csv(experiment: ComparisonExperiment) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["day", "algorithm", "day_peak", "makespan", "cut_index", "cut_label"])

    for key, run in experiment.runs.items():
        for day, (day_peak, makespan, cut_index) in enumerate(
            zip(run.day_peaks, run.makespans, run.cuts),
            start=1,
        ):
            writer.writerow(
                [
                    day,
                    key,
                    f"{day_peak:.12g}",
                    f"{makespan:.12g}",
                    cut_index,
                    f"b{cut_index + 1}",
                ]
            )
    return buffer.getvalue()


def makespan_two_schedule_rows(rates: list[float]) -> list[dict[str, str]]:
    oracle = MakespanTwoOracle(rates)
    rows = []
    for slot in oracle.slots:
        route = " -> ".join(str(step + 1) for step in slot.route) or "root"
        rows.append(
            {
                "bamboo": f"b{slot.bamboo_index + 1}",
                "h_i": f"{slot.normalized_growth:.4f}",
                "h'_i": f"{slot.rounded_growth:.4f}",
                "period": str(slot.period),
                "route": route,
            }
        )
    return rows


def cut_trace(run: ExperimentRun, limit: int = 40) -> str:
    visible = " ".join(f"b{index + 1}" for index in run.cuts[:limit])
    if len(run.cuts) > limit:
        visible += " ..."
    return visible


def _count_best_days(runs: dict[str, ExperimentRun], days: int) -> dict[str, int]:
    counts = {key: 0 for key in runs}
    for day_index in range(days):
        best = min(run.makespans[day_index] for run in runs.values())
        for key, run in runs.items():
            if abs(run.makespans[day_index] - best) <= 1e-12:
                counts[key] += 1
    return counts
