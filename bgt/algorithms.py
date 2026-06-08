from __future__ import annotations

import math
from dataclasses import dataclass, field

from bgt.core import Bamboo, Oracle


def oracle_reduce_max(bamboos: list[Bamboo]) -> int:
    return max(range(len(bamboos)), key=lambda i: bamboos[i].height)


def oracle_reduce_fastest(threshold: float) -> Oracle:
    def pick(bamboos: list[Bamboo]) -> int:
        eligible = [i for i, bamboo in enumerate(bamboos) if bamboo.height >= threshold]
        if not eligible:
            return oracle_reduce_max(bamboos)
        return max(eligible, key=lambda i: bamboos[i].growth)

    return pick


@dataclass(frozen=True)
class DyadicSlot:
    bamboo_index: int
    normalized_growth: float
    rounded_growth: float
    code: tuple[int, ...]

    @property
    def period(self) -> int:
        return 1 << len(self.code)


@dataclass
class _PrefixNode:
    bamboo_index: int | None = None
    children: dict[int, "_PrefixNode"] = field(default_factory=dict)


class MakespanTwoOracle:
    """Dyadic BGT schedule following Section 3.3 of Bilò et al. (2022).

    The paper rounds normalized rates down to powers of 1/2 and schedules the
    rounded instance with makespan 1. Prefix-free binary codes realize the same
    periodic slots here; translating back to the original rates gives makespan 2.
    """

    def __init__(self, rates: list[float]) -> None:
        if not rates or any(rate <= 0 for rate in rates):
            raise ValueError("Growth rates must be positive.")

        total_growth = sum(float(rate) for rate in rates)
        self.total_growth = total_growth
        normalized = [float(rate) / total_growth for rate in rates]
        lengths = [_dyadic_period_exponent(rate) for rate in normalized]
        codes = _canonical_prefix_codes(lengths)

        self.slots = tuple(
            DyadicSlot(
                bamboo_index=index,
                normalized_growth=rate,
                rounded_growth=math.ldexp(1.0, -length),
                code=code,
            )
            for index, (rate, length, code) in enumerate(zip(normalized, lengths, codes))
        )
        self._root = _build_prefix_tree(self.slots)
        self.day = 0

    @property
    def guaranteed_bound(self) -> float:
        return 2 * self.total_growth

    def scheduled_index(self, day: int) -> int | None:
        if day < 0:
            raise ValueError("Day must be non-negative.")

        node = self._root
        if node.bamboo_index is not None:
            return node.bamboo_index

        bit_index = 0
        while node.children:
            # Reading day bits least-significant first makes a depth-k leaf recur
            # in exactly one residue class modulo 2**k.
            bit = (day >> bit_index) & 1
            node = node.children.get(bit)
            if node is None:
                return None
            if node.bamboo_index is not None:
                return node.bamboo_index
            bit_index += 1
        return None

    def __call__(self, bamboos: list[Bamboo]) -> int:
        target = self.scheduled_index(self.day)
        self.day += 1
        if target is None:
            return oracle_reduce_max(bamboos)
        return target


def _dyadic_period_exponent(rate: float) -> int:
    _, exponent = math.frexp(rate)
    return max(0, 1 - exponent)


def _canonical_prefix_codes(lengths: list[int]) -> list[tuple[int, ...]]:
    indexed_lengths = sorted(enumerate(lengths), key=lambda item: (item[1], item[0]))
    codes: list[tuple[int, ...] | None] = [None] * len(lengths)
    code_value = 0
    previous_length = 0

    for index, length in indexed_lengths:
        code_value <<= length - previous_length
        if code_value >= 1 << length:
            raise ValueError("Dyadic rates do not satisfy the Kraft inequality.")
        codes[index] = tuple(
            (code_value >> bit_index) & 1
            for bit_index in range(length - 1, -1, -1)
        )
        code_value += 1
        previous_length = length

    return [code for code in codes if code is not None]


def _build_prefix_tree(slots: tuple[DyadicSlot, ...]) -> _PrefixNode:
    root = _PrefixNode()
    for slot in slots:
        node = root
        for bit in slot.code:
            if node.bamboo_index is not None:
                raise ValueError("Schedule codes are not prefix-free.")
            node = node.children.setdefault(bit, _PrefixNode())
        if node.children or node.bamboo_index is not None:
            raise ValueError("Schedule codes are not prefix-free.")
        node.bamboo_index = slot.bamboo_index
    return root
