from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Bamboo:
    id: int
    growth: float
    height: float = 0.0


Oracle = Callable[[list[Bamboo]], int]


def create_bamboos(rates: list[float]) -> list[Bamboo]:
    return [Bamboo(id=i, growth=float(rate), height=0.0) for i, rate in enumerate(rates)]


def grow(bamboos: list[Bamboo]) -> list[Bamboo]:
    return [
        Bamboo(id=bamboo.id, growth=bamboo.growth, height=bamboo.height + bamboo.growth)
        for bamboo in bamboos
    ]


def cut(bamboos: list[Bamboo], index: int) -> list[Bamboo]:
    return [
        Bamboo(id=bamboo.id, growth=bamboo.growth, height=0.0 if i == index else bamboo.height)
        for i, bamboo in enumerate(bamboos)
    ]


def advance_day(
    bamboos: list[Bamboo],
    oracle: Oracle,
) -> tuple[list[Bamboo], float, int]:
    grown = grow(bamboos)
    target = oracle(grown)
    return cut(grown, target), max_height(grown), target


def max_height(bamboos: list[Bamboo]) -> float:
    return max((bamboo.height for bamboo in bamboos), default=0.0)


def makespan(history: list[float]) -> float:
    return max(history) if history else 0.0


def normalize_rates(rates: list[float]) -> list[float]:
    positive = [max(0.0, float(rate)) for rate in rates]
    total = sum(positive)
    if total <= 0:
        return [1 / len(positive)] * len(positive)
    return [rate / total for rate in positive]

