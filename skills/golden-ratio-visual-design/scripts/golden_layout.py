#!/usr/bin/env python3
"""Calculate a golden split without changing files (Python stdlib only)."""

import argparse
import json
import math

PHI = (1 + math.sqrt(5)) / 2


def calculate(width, height, padding=0, gap=0, axis="x"):
    if not all(math.isfinite(v) for v in (width, height, padding, gap)):
        raise ValueError("Dimensions must be finite")
    if width <= 0 or height <= 0 or padding < 0 or gap < 0:
        raise ValueError("Width/height must be positive; padding/gap nonnegative")
    if axis not in ("x", "y"):
        raise ValueError("Axis must be x or y")
    inner_width, inner_height = width - 2 * padding, height - 2 * padding
    if min(inner_width, inner_height) <= 0:
        raise ValueError("Padding leaves no usable canvas")
    available = (inner_width if axis == "x" else inner_height) - gap
    if available <= 0:
        raise ValueError("Gap leaves no room for both regions")
    major = available / PHI
    minor = available - major
    if axis == "x":
        main_rect = dict(x=padding, y=padding, width=major, height=inner_height)
        secondary = dict(
            x=padding + major + gap, y=padding, width=minor, height=inner_height
        )
    else:
        main_rect = dict(x=padding, y=padding, width=inner_width, height=major)
        secondary = dict(
            x=padding, y=padding + major + gap, width=inner_width, height=minor
        )
    return {
        "phi": PHI,
        "canvas": {"width": width, "height": height},
        "padding": padding,
        "gap": gap,
        "axis": axis,
        "main": main_rect,
        "secondary": secondary,
        "main_to_secondary_ratio": major / minor,
        "golden_focus_positions": {
            "x": [padding + inner_width / PHI**2, padding + inner_width / PHI],
            "y": [padding + inner_height / PHI**2, padding + inner_height / PHI],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=float, required=True)
    parser.add_argument("--height", type=float, required=True)
    parser.add_argument("--padding", type=float, default=0)
    parser.add_argument("--gap", type=float, default=0)
    parser.add_argument("--axis", choices=("x", "y"), default="x")
    args = parser.parse_args()
    try:
        result = calculate(args.width, args.height, args.padding, args.gap, args.axis)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
