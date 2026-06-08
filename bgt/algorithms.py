from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations

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
    route: tuple[int, ...]
    period_days: int

    @property
    def period(self) -> int:
        return self.period_days


@dataclass
class _PaperOracleNode:
    rate: Fraction
    bamboo_index: int | None = None
    children: tuple["_PaperOracleNode", ...] = ()
    min_bamboo_index: int = 0

    @property
    def is_leaf(self) -> bool:
        return self.bamboo_index is not None


class MakespanTwoOracle:
    """Dyadic BGT schedule following Section 3.3 of Bilò et al. (2022).

    The paper rounds normalized rates down to powers of 1/2, completes the
    dyadic instance to total growth 1, and builds a tree of virtual bamboos.
    Every internal node schedules its children as a scaled regular instance.
    """

    def __init__(self, rates: list[float]) -> None:
        if not rates or any(rate <= 0 for rate in rates):
            raise ValueError("Growth rates must be positive.")

        total_growth = sum(float(rate) for rate in rates)
        self.total_growth = total_growth
        normalized = [float(rate) / total_growth for rate in rates]
        adjusted_rates = _complete_dyadic_rates(normalized)
        leaves = [
            _PaperOracleNode(
                rate=rate,
                bamboo_index=index,
                min_bamboo_index=index,
            )
            for index, rate in enumerate(adjusted_rates)
        ]
        self._root = _build_virtual_tree(leaves)
        routes = _leaf_routes(self._root)

        self.slots = tuple(
            DyadicSlot(
                bamboo_index=index,
                normalized_growth=rate,
                rounded_growth=float(adjusted_rates[index]),
                route=routes[index],
                period_days=adjusted_rates[index].denominator,
            )
            for index, rate in enumerate(normalized)
        )
        self.tree_height = _tree_height(self._root)
        self.node_count = _node_count(self._root)
        self.day = 0

    @property
    def guaranteed_bound(self) -> float:
        return 2 * self.total_growth

    def scheduled_index(self, day: int) -> int | None:
        if day < 0:
            raise ValueError("Day must be non-negative.")
        return _scheduled_leaf_at(self._root, day)

    def __call__(self, bamboos: list[Bamboo]) -> int:
        target = self.scheduled_index(self.day)
        self.day += 1
        if target is None:
            return oracle_reduce_max(bamboos)
        return target


def _dyadic_period_exponent(rate: float) -> int:
    _, exponent = math.frexp(rate)
    return max(0, 1 - exponent)


def _complete_dyadic_rates(normalized_rates: list[float]) -> list[Fraction]:
    rates = [Fraction(1, 1 << _dyadic_period_exponent(rate)) for rate in normalized_rates]
    order = sorted(range(len(rates)), key=lambda index: (-normalized_rates[index], index))

    for index in order:
        other_sum = sum(rates) - rates[index]
        capacity = Fraction(1, 1) - other_sum
        rates[index] = _largest_dyadic_at_most(capacity)

    if sum(rates) != 1:
        raise ValueError("Could not complete dyadic rates to total growth 1.")
    return rates


def _largest_dyadic_at_most(value: Fraction) -> Fraction:
    if value <= 0:
        raise ValueError("Dyadic completion requires positive capacity.")
    exponent = 0
    rate = Fraction(1, 1)
    while rate > value:
        exponent += 1
        rate = Fraction(1, 1 << exponent)
    return rate


def _build_virtual_tree(leaves: list[_PaperOracleNode]) -> _PaperOracleNode:
    current = list(leaves)
    while len(current) > 1:
        next_phase: list[_PaperOracleNode] = []
        work = list(current)

        while True:
            merge_indices = _find_next_merge(work)
            if merge_indices is None:
                break

            children = [work[index] for index in merge_indices]
            next_phase.append(_merge_regular_children(children))
            for index in sorted(merge_indices, reverse=True):
                work.pop(index)

        next_phase.extend(work)
        if len(next_phase) >= len(current):
            raise ValueError("Virtual bamboo merge phase did not make progress.")
        current = next_phase

    root = current[0]
    if root.rate != 1:
        raise ValueError("The root virtual bamboo must have growth rate 1.")
    return root


def _find_next_merge(nodes: list[_PaperOracleNode]) -> list[int] | None:
    target_order = sorted(range(len(nodes)), key=lambda index: _node_sort_key(nodes[index]))
    all_indices = range(len(nodes))

    for target_index in target_order:
        feasible: list[frozenset[int]] = []
        for size in range(2, len(nodes) + 1):
            for subset in combinations(all_indices, size):
                if target_index not in subset:
                    continue
                if _is_regular_subset([nodes[index] for index in subset]):
                    feasible.append(frozenset(subset))

        if feasible:
            maximal = [
                subset
                for subset in feasible
                if not any(subset < other for other in feasible)
            ]
            chosen = max(
                maximal,
                key=lambda subset: (
                    len(subset),
                    sum(nodes[index].rate for index in subset),
                    tuple(-nodes[index].min_bamboo_index for index in sorted(subset)),
                ),
            )
            return sorted(chosen)

    return None


def _merge_regular_children(children: list[_PaperOracleNode]) -> _PaperOracleNode:
    ordered = _regular_order(children)
    parent_rate = sum(child.rate for child in ordered)
    return _PaperOracleNode(
        rate=parent_rate,
        children=tuple(ordered),
        min_bamboo_index=min(child.min_bamboo_index for child in ordered),
    )


def _is_regular_subset(nodes: list[_PaperOracleNode]) -> bool:
    if len(nodes) < 2:
        return False
    parent_rate = sum(node.rate for node in nodes)
    expected = _regular_child_rates(parent_rate, len(nodes))
    actual = sorted((node.rate for node in nodes), reverse=True)
    return actual == expected


def _regular_order(nodes: list[_PaperOracleNode]) -> list[_PaperOracleNode]:
    ordered = sorted(nodes, key=_node_sort_key)
    expected = _regular_child_rates(sum(node.rate for node in ordered), len(ordered))
    if [node.rate for node in ordered] != expected:
        raise ValueError("Children do not form a regular instance.")
    return ordered


def _regular_child_rates(parent_rate: Fraction, child_count: int) -> list[Fraction]:
    return [
        parent_rate / (1 << exponent)
        for exponent in range(1, child_count)
    ] + [parent_rate / (1 << (child_count - 1))]


def _regular_child_index(local_day: int, child_count: int) -> int:
    for bit_index in range(child_count - 1):
        if ((local_day >> bit_index) & 1) == 0:
            return bit_index
    return child_count - 1


def _regular_occurrences_before(local_day: int, child_index: int, child_count: int) -> int:
    if child_index < child_count - 1:
        period = 1 << (child_index + 1)
        residue = (1 << child_index) - 1
    else:
        period = 1 << (child_count - 1)
        residue = period - 1

    if local_day <= residue:
        return 0
    return ((local_day - 1 - residue) // period) + 1


def _scheduled_leaf_at(node: _PaperOracleNode, local_day: int) -> int:
    if node.bamboo_index is not None:
        return node.bamboo_index

    child_index = _regular_child_index(local_day, len(node.children))
    child = node.children[child_index]
    child_local_day = _regular_occurrences_before(local_day, child_index, len(node.children))
    return _scheduled_leaf_at(child, child_local_day)


def _leaf_routes(node: _PaperOracleNode) -> dict[int, tuple[int, ...]]:
    routes: dict[int, tuple[int, ...]] = {}

    def visit(current: _PaperOracleNode, route: tuple[int, ...]) -> None:
        if current.bamboo_index is not None:
            routes[current.bamboo_index] = route
            return
        for child_index, child in enumerate(current.children):
            visit(child, (*route, child_index))

    visit(node, ())
    return routes


def _tree_height(node: _PaperOracleNode) -> int:
    if node.bamboo_index is not None:
        return 0
    return 1 + max(_tree_height(child) for child in node.children)


def _node_count(node: _PaperOracleNode) -> int:
    return 1 + sum(_node_count(child) for child in node.children)


def _node_sort_key(node: _PaperOracleNode) -> tuple[Fraction, int]:
    return (-node.rate, node.min_bamboo_index)
