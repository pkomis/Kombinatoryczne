from __future__ import annotations

import html
import math

from bgt.core import Bamboo, max_height


def panda_svg(flipped: bool, cutting: bool) -> str:
    flip = ' transform="translate(48 0) scale(-1 1)"' if flipped else ""
    scissors = ""
    if cutting:
        scissors = """
        <g transform="translate(32,28) rotate(-30)">
          <line x1="0" y1="0" x2="10" y2="0" stroke="#888" stroke-width="1.5" stroke-linecap="round"/>
          <line x1="0" y1="3" x2="10" y2="3" stroke="#888" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="0" cy="1.5" r="2.5" fill="none" stroke="#888" stroke-width="1"/>
        </g>
        """
    return f"""
    <g{flip}>
      <ellipse cx="24" cy="38" rx="13" ry="12" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>
      <circle cx="24" cy="20" r="11" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>
      <circle cx="14" cy="11" r="5" fill="#222"/>
      <circle cx="34" cy="11" r="5" fill="#222"/>
      <ellipse cx="19" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(-10,19,19)"/>
      <ellipse cx="29" cy="19" rx="4" ry="3.5" fill="#222" transform="rotate(10,29,19)"/>
      <circle cx="19" cy="19" r="1.5" fill="#fff"/>
      <circle cx="29" cy="19" r="1.5" fill="#fff"/>
      <ellipse cx="24" cy="23.5" rx="2.5" ry="1.5" fill="#444"/>
      <path d="M21 25.5 Q24 27.5 27 25.5" fill="none" stroke="#444" stroke-width="0.8" stroke-linecap="round"/>
      <ellipse cx="11" cy="38" rx="5" ry="8" fill="#222" stroke="#222" stroke-width="0.8" transform="rotate(-15,11,38)"/>
      <ellipse cx="37" cy="38" rx="5" ry="8" fill="#222" stroke="#222" stroke-width="0.8" transform="rotate(15,37,38)"/>
      <ellipse cx="18" cy="49" rx="5" ry="4" fill="#222"/>
      <ellipse cx="30" cy="49" rx="5" ry="4" fill="#222"/>
      {scissors}
    </g>
    """


def bamboo_garden_svg(
    bamboos: list[Bamboo],
    max_display_height: float,
    last_cut: int | None = None,
    panda_at: int | None = None,
    hint: str | None = None,
) -> str:
    width = 540
    height = 280
    ground_y = 220
    left_pad = 56
    right_pad = 70
    usable_width = width - left_pad - right_pad
    count = len(bamboos)
    slot_width = usable_width / max(count, 1)
    stalk_width = max(14, min(28, slot_width * 0.38))
    scale_height = max(max_display_height, 1.5, max_height(bamboos))
    scale = (ground_y - 30) / scale_height

    def stalk_x(index: int) -> float:
        return left_pad + slot_width * index + slot_width / 2

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height + 30}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{width}" height="{height + 30}" fill="#fafaf7" rx="6"/>',
    ]

    if bamboos:
        tallest = max(bamboos, key=lambda bamboo: bamboo.height)
        bracket_height = tallest.height * scale
        if bracket_height > 10:
            y_mid = ground_y - bracket_height / 2
            parts.extend(
                [
                    f'<line x1="18" y1="{ground_y - bracket_height:.2f}" x2="18" y2="{ground_y}" stroke="#555" stroke-width="0.8"/>',
                    f'<line x1="14" y1="{ground_y - bracket_height:.2f}" x2="22" y2="{ground_y - bracket_height:.2f}" stroke="#555" stroke-width="0.8"/>',
                    f'<line x1="14" y1="{ground_y}" x2="22" y2="{ground_y}" stroke="#555" stroke-width="0.8"/>',
                    f'<text x="10" y="{y_mid + 4:.2f}" text-anchor="middle" font-size="11" font-family="Georgia,serif" font-style="italic" fill="#333">h</text>',
                    f'<text x="13" y="{y_mid + 10:.2f}" font-size="7" font-family="Georgia,serif" fill="#333">max</text>',
                ]
            )

    for value in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        y = ground_y - value * scale
        if 10 <= y <= ground_y:
            parts.extend(
                [
                    f'<line x1="{left_pad - 4}" y1="{y:.2f}" x2="{width - right_pad + 4}" y2="{y:.2f}" stroke="#ccc" stroke-width="0.5" stroke-dasharray="3 4"/>',
                    f'<text x="{left_pad - 6}" y="{y + 3.5:.2f}" text-anchor="end" font-size="8.5" font-family="Georgia,serif" fill="#999">{value:.1f}</text>',
                ]
            )

    for index, bamboo in enumerate(bamboos):
        center_x = stalk_x(index)
        display_height = max(0.0, bamboo.height)
        pixel_height = display_height * scale
        top = ground_y - pixel_height
        was_cut = last_cut == index
        is_target = panda_at == index
        green_1 = "#22c55e" if was_cut else "#2d8a3e"
        green_2 = "#16a34a" if was_cut else "#1f6b2e"
        green_3 = "#bbf7d0" if was_cut else "#a7d9a0"

        if is_target:
            parts.append(
                f'<rect x="{center_x - stalk_width / 2 - 3:.2f}" y="{top - 3:.2f}" width="{stalk_width + 6:.2f}" height="{pixel_height + 6:.2f}" rx="8" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="3 2" opacity="0.75"/>'
            )

        if pixel_height > 0:
            parts.extend(
                [
                    f'<rect x="{center_x - stalk_width / 2:.2f}" y="{top:.2f}" width="{stalk_width:.2f}" height="{pixel_height:.2f}" rx="{stalk_width / 2:.2f}" fill="{green_1}" stroke="{green_2}" stroke-width="0.8"/>',
                    f'<circle cx="{center_x:.2f}" cy="{top:.2f}" r="{stalk_width / 2 + 1:.2f}" fill="{green_1}" stroke="{green_2}" stroke-width="0.8"/>',
                ]
            )
            if pixel_height > 4:
                parts.append(
                    f'<rect x="{center_x - stalk_width / 2 + 3:.2f}" y="{top + 2:.2f}" width="{stalk_width * 0.25:.2f}" height="{max(0.0, pixel_height - 4):.2f}" rx="2" fill="{green_3}" opacity="0.5"/>'
                )
            joint_count = max(1, math.floor(display_height * 3))
            for joint in range(joint_count):
                y = ground_y - ((joint + 1) / (joint_count + 1)) * pixel_height
                parts.append(
                    f'<line x1="{center_x - stalk_width / 2:.2f}" y1="{y:.2f}" x2="{center_x + stalk_width / 2:.2f}" y2="{y:.2f}" stroke="{green_2}" stroke-width="1.2" opacity="0.6"/>'
                )
            parts.append(
                f'<circle cx="{center_x - stalk_width * 0.15:.2f}" cy="{top - stalk_width * 0.1:.2f}" r="{stalk_width * 0.12:.2f}" fill="{green_3}" opacity="0.6"/>'
            )

        label_y = min(top - stalk_width / 2 - 4, ground_y - 4)
        label_color = "#16a34a" if was_cut else "#444"
        label_weight = "700" if was_cut else "400"
        parts.extend(
            [
                f'<text x="{center_x:.2f}" y="{label_y:.2f}" text-anchor="middle" font-size="9" font-family="Georgia,serif" fill="{label_color}" font-weight="{label_weight}">{display_height:.2f}</text>',
                f'<text x="{center_x:.2f}" y="{ground_y + 18}" text-anchor="middle" font-size="11" font-family="Georgia,serif" font-style="italic" fill="#333">b<tspan font-size="8" baseline-shift="-4">{index + 1}</tspan></text>',
            ]
        )

    ground_width = width - left_pad - right_pad + 16
    parts.extend(
        [
            f'<rect x="{left_pad - 8}" y="{ground_y}" width="{ground_width}" height="3" rx="1" fill="#8B6914"/>',
            f'<rect x="{left_pad - 8}" y="{ground_y + 3}" width="{ground_width}" height="8" rx="1" fill="#a07830" opacity="0.4"/>',
        ]
    )

    if last_cut is not None and 0 <= last_cut < count:
        center_x = stalk_x(last_cut)
        cut_y = ground_y - max(0.2, bamboos[last_cut].height) * scale - stalk_width / 2
        for ray in range(6):
            angle = (ray / 6) * math.tau
            radius = stalk_width + 6
            parts.append(
                f'<line x1="{center_x:.2f}" y1="{cut_y:.2f}" x2="{center_x + math.cos(angle) * radius:.2f}" y2="{cut_y + math.sin(angle) * radius:.2f}" stroke="#fbbf24" stroke-width="1" opacity="0.6"/>'
            )

    panda_x = stalk_x(panda_at) if panda_at is not None and 0 <= panda_at < count else width - right_pad + 10
    flipped = panda_at is not None and panda_at < count / 2
    parts.append(
        f'<g transform="translate({panda_x - 24:.2f}, {ground_y - 50})">{panda_svg(flipped=flipped, cutting=panda_at is not None)}</g>'
    )

    if hint:
        parts.append(
            f'<text x="{width / 2}" y="{height + 22}" text-anchor="middle" font-size="9.5" font-family="Georgia,serif" fill="#777" font-style="italic">{html.escape(hint)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def sparkline_svg(
    data: list[float],
    color: str,
    height: int = 52,
    max_value: float = 3.0,
) -> str:
    width = 400
    if len(data) < 2:
        return f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"></svg>'

    upper = max(max_value, max(data))
    points = []
    for index, value in enumerate(data):
        x = (index / (len(data) - 1)) * width
        y = height - (value / upper) * (height - 2) - 1
        points.append(f"{x:.2f},{y:.2f}")
    point_string = " ".join(points)

    parts = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    for bound, bound_color in {"9": "#dc2626", "2.62": "#b45309", "2": "#1d4ed8"}.items():
        y = height - (float(bound) / upper) * (height - 2) - 1
        if 0 <= y <= height:
            parts.append(
                f'<line x1="0" y1="{y:.2f}" x2="{width}" y2="{y:.2f}" stroke="{bound_color}" stroke-width="0.6" stroke-dasharray="3 3" opacity="0.5"/>'
            )
    parts.extend(
        [
            f'<polyline points="{point_string}" fill="none" stroke="{html.escape(color)}" stroke-width="1.8" stroke-linejoin="round"/>',
            f'<polyline points="0,{height} {point_string} {width},{height}" fill="{html.escape(color)}" opacity="0.08" stroke="none"/>',
            "</svg>",
        ]
    )
    return "\n".join(parts)

