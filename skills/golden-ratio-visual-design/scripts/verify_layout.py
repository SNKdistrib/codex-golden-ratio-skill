#!/usr/bin/env python3
"""Verify a layout contract against observed boxes tied to a PNG or JPEG. Stdlib only.

This checks supplied measurements, not automatic image understanding or beauty.
Exit codes: 0 PASS, 1 FAIL, 2 UNVERIFIED or invalid input.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

PHI = (1 + math.sqrt(5)) / 2
REQUIRED = {"alignment", "ratio", "spacing", "whitespace"}


def number(value, label, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: finite number required")
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"{label}: invalid number")
    return float(value)


def positive(value, label):
    value = number(value, label, 0)
    if value == 0:
        raise ValueError(f"{label}: must be positive")
    return value


def image_size(path):
    with Path(path).open("rb") as stream:
        data = stream.read()
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        width, height = struct.unpack(">II", data[16:24])
    elif data[:2] == b"\xff\xd8":
        position = 2
        width = height = 0
        while position < len(data):
            if data[position] != 255:
                raise ValueError("Invalid JPEG marker")
            while position < len(data) and data[position] == 255:
                position += 1
            if position >= len(data):
                break
            marker = data[position]
            position += 1
            if marker in {0xD9, 0xDA}:
                break
            if marker in {0x01, 0xD8} or 0xD0 <= marker <= 0xD7:
                continue
            if position + 2 > len(data):
                raise ValueError("Truncated JPEG segment")
            length = int.from_bytes(data[position:position + 2], "big")
            if length < 2 or position + length > len(data):
                raise ValueError("Invalid JPEG segment length")
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if length < 8:
                    raise ValueError("Truncated JPEG frame")
                height, width = struct.unpack(">HH", data[position + 3:position + 7])
                break
            position += length
    else:
        raise ValueError("Evidence must be PNG or JPEG")
    if width == 0 or height == 0:
        raise ValueError("Invalid image dimensions")
    return width, height


def load_json(path):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      parse_constant=reject_constant, object_pairs_hook=unique_keys)


def verify(spec, measured, image):
    if spec.get("version") != 1 or measured.get("version") != 1:
        raise ValueError("Both documents must use version 1")
    checks = []

    def add(name, category, status, detail, **data):
        checks.append(dict(id=name, category=category, status=status, detail=detail, **data))

    canvas = spec["canvas"]
    width = positive(canvas["width"], "spec.width")
    height = positive(canvas["height"], "spec.height")
    mw = positive(measured["canvas"]["width"], "measured.width")
    mh = positive(measured["canvas"]["height"], "measured.height")
    dpr = positive(measured.get("pixel_ratio", 1), "pixel_ratio")
    iw, ih = image_size(image)
    digest = hashlib.sha256(Path(image).read_bytes()).hexdigest()
    proof = measured.get("evidence", {})
    if proof.get("image_sha256", "").lower() != digest:
        add("evidence_hash", "evidence", "UNVERIFIED", "Measurements are not bound to this image")
    else:
        add("evidence_hash", "evidence", "PASS", "Image SHA-256 matches")
    if measured.get("kind") != "observed" or proof.get("method") not in {"manual", "dom"}:
        add("measurement_origin", "evidence", "UNVERIFIED", "Planned, synthetic or unspecified coordinates are not observed evidence")
    else:
        add("measurement_origin", "evidence", "PASS", "Declared observation method: " + proof["method"])
    if abs(iw - mw * dpr) > 1 or abs(ih - mh * dpr) > 1:
        add("image_dimensions", "evidence", "UNVERIFIED", "Image dimensions do not match measurement viewport and pixel ratio")
    else:
        add("image_dimensions", "evidence", "PASS", "Image and measurement viewport agree")
    aspect_error = abs((mw / mh) / (width / height) - 1) * 100
    add("canvas_aspect", "frame", "PASS" if aspect_error <= 0.5 else "FAIL",
        "Aspect error must not exceed 0.5%", error_pct=aspect_error)
    sx, sy = width / mw, height / mh
    boxes = {}
    for name, item in measured.get("boxes", {}).items():
        if not isinstance(name, str) or not name:
            raise ValueError("Invalid box identifier")
        x = number(item["x"], name + ".x")
        y = number(item["y"], name + ".y")
        w = positive(item["width"], name + ".width")
        h = positive(item["height"], name + ".height")
        if x < 0 or y < 0 or x + w > mw + 0.5 or y + h > mh + 0.5:
            add("bounds:" + name, "frame", "FAIL", "Observed box is outside the viewport")
        boxes[name] = dict(x=x * sx, y=y * sy, width=w * sx, height=h * sy)
        if "font_size" in item:
            boxes[name]["font_size"] = positive(item["font_size"], name + ".font_size") * sy
    base = positive(spec["spacing_base"], "spacing_base")
    tolerance = number(spec.get("tolerance_px", 1), "tolerance_px", 0)
    # A large tolerance must not silently turn a bad image into a pass.
    if tolerance > 2:
        raise ValueError("tolerance_px must not exceed 2 reference-canvas units")
    uncertainty = number(proof.get("uncertainty_px", 0), "uncertainty_px", 0)
    if uncertainty > 2:
        add("measurement_precision", "evidence", "UNVERIFIED", "Measurement uncertainty exceeds 2 observed units")

    def box(name):
        if name not in boxes:
            raise LookupError("Missing observed box: " + str(name))
        return boxes[name]

    def value(ref):
        b = box(ref["box"])
        axis = ref["value"]
        if axis not in {"x", "y", "width", "height", "right", "bottom", "center_x", "center_y", "font_size"}:
            raise ValueError("Invalid box value: " + str(axis))
        return {**b, "right": b["x"] + b["width"], "bottom": b["y"] + b["height"],
                "center_x": b["x"] + b["width"] / 2, "center_y": b["y"] + b["height"] / 2}[axis]

    def target(rule):
        exponent = number(rule.get("exponent", 1), "exponent")
        if exponent not in {-2, -1, -0.5, 0, 0.5, 1, 2, 3, 4, 5, 6}:
            raise ValueError("Unsupported phi exponent")
        return PHI ** exponent

    def compare_ratio(rule, a, b):
        if rule.get("exponent", 1) == 0:
            raise ValueError("A golden ratio comparison cannot use exponent zero")
        if a <= 0 or b <= 0:
            return "FAIL", dict(actual=None, detail="Both ratio operands must be positive")
        expected = target(rule)
        error = 100 * abs(a / b - expected) / expected
        limit = number(rule.get("tolerance_pct", 1), "tolerance_pct", 0)
        if limit > 2:
            raise ValueError("Ratio tolerance must not exceed 2 percent")
        return ("PASS" if error <= limit else "FAIL"), dict(actual=a / b, expected=expected,
                error_pct=error, tolerance_pct=limit, detail="Compare measured lengths, excluding gaps")

    rules = spec.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("rules must be a list")
    profile = spec.get("profile", "composition")
    if profile not in {"composition", "glyph-centering"}:
        raise ValueError("Unknown validation profile")
    required = REQUIRED
    if profile == "glyph-centering":
        if not isinstance(spec.get("scope_note"), str) or not spec["scope_note"].strip():
            raise ValueError("glyph-centering requires an explicit scope_note")
        if not rules or any(r.get("type") != "glyph_center" for r in rules):
            raise ValueError("glyph-centering requires one or more glyph_center rules only")
        required = {"alignment"}
    ids = set()
    categories = set()
    for rule in rules:
        ident = rule["id"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError("Rule IDs must be nonempty and unique")
        ids.add(ident)
        kind = rule["type"]
        category = {"align": "alignment", "glyph_center": "alignment", "ratio": "ratio", "gap": "spacing",
                    "position": "placement", "void_ratio": "whitespace",
                    "inner_void_ratio": "whitespace"}.get(kind)
        if category is None:
            raise ValueError("Unknown rule type: " + str(kind))
        categories.add(category)
        try:
            if kind == "glyph_center":
                glyph, container = box(rule["glyph"]), box(rule["container"])
                raw_glyph = measured["boxes"][rule["glyph"]]
                if raw_glyph.get("bounds_kind") != "visible_ink":
                    add(ident, category, "UNVERIFIED", "Visible ink bounds required; a font line box or DOM text Range is insufficient")
                    continue
                dx = glyph["x"] + glyph["width"] / 2 - container["x"] - container["width"] / 2
                dy = glyph["y"] + glyph["height"] / 2 - container["y"] - container["height"] / 2
                contained = all(glyph[a] >= container[a] - tolerance and
                                glyph[a] + glyph[s] <= container[a] + container[s] + tolerance
                                for a, s in (("x", "width"), ("y", "height")))
                add(ident, category, "PASS" if max(abs(dx), abs(dy)) <= tolerance and contained else "FAIL",
                    "Visible glyph bounding-box center on both axes; rectangular containment, not optical balance or circle-corner clearance",
                    delta_x=dx, delta_y=dy, contained=contained, tolerance_px=tolerance)
            elif kind == "align":
                edge = rule["edge"]
                if edge not in {"x", "y", "right", "bottom", "center_x", "center_y", "width", "height"}:
                    raise ValueError("Invalid alignment edge")
                a = value({"box": rule["a"], "value": edge})
                b = value({"box": rule["b"], "value": edge})
                delta = abs(a - b)
                add(ident, category, "PASS" if delta <= tolerance else "FAIL",
                    "Explicit chosen alignment, not a golden-ratio claim", delta=delta, tolerance_px=tolerance)
            elif kind == "ratio":
                if any(ref.get("value") not in {"width", "height", "font_size"} for ref in (rule["a"], rule["b"])):
                    raise ValueError("Ratio operands must be lengths, not coordinates")
                status, result = compare_ratio(rule, value(rule["a"]), value(rule["b"]))
                add(ident, category, status, **result)
            elif kind == "gap":
                axis = rule["axis"]
                if axis not in {"x", "y"}:
                    raise ValueError("Gap axis must be x or y")
                size = "width" if axis == "x" else "height"
                a, b = box(rule["from"]), box(rule["to"])
                actual = b[axis] - a[axis] - a[size]
                expected = base * target(rule)
                delta = abs(actual - expected)
                add(ident, category, "PASS" if actual > 0 and delta <= tolerance else "FAIL",
                    "Empty edge-to-edge gap, not baseline-to-baseline", actual=actual,
                    expected=expected, delta=delta, tolerance_px=tolerance)
            elif kind == "position":
                actual = value(rule["ref"])
                expected = number(rule["expected"], "position.expected")
                delta = abs(actual - expected)
                add(ident, category, "PASS" if delta <= tolerance else "FAIL",
                    "Position in the declared reference canvas", actual=actual,
                    expected=expected, delta=delta, tolerance_px=tolerance)
            else:
                axis = rule["axis"]
                if axis not in {"x", "y"}:
                    raise ValueError("Void axis must be x or y")
                size = "width" if axis == "x" else "height"
                members = [box(name) for name in rule["group"]]
                if not members:
                    raise ValueError("Whitespace group must not be empty")
                start = min(b[axis] for b in members)
                end = max(b[axis] + b[size] for b in members)
                if kind == "inner_void_ratio":
                    container = box(rule["container"])
                    if any(member[a] < container[a] - tolerance or
                           member[a] + member[s] > container[a] + container[s] + tolerance
                           for member in members for a, s in (("x", "width"), ("y", "height"))):
                        add(ident, category, "FAIL", "A group member extends outside its container")
                        continue
                    before = start - container[axis]
                    after = container[axis] + container[size] - end
                else:
                    before_box, after_box = box(rule["before"]), box(rule["after"])
                    before = start - before_box[axis] - before_box[size]
                    after = after_box[axis] - end
                if rule.get("dominant") not in {"before", "after"}:
                    raise ValueError("Specify which empty region is dominant")
                operands = (after, before) if rule["dominant"] == "after" else (before, after)
                status, result = compare_ratio(rule, *operands)
                add(ident, category, status, **result, empty_before=before, empty_after=after)
        except LookupError as error:
            add(ident, category, "UNVERIFIED", str(error))
    for category in sorted(required - categories):
        add("coverage:" + category, category, "UNVERIFIED", "Required layout check category is missing")
    if not boxes:
        add("no_boxes", "evidence", "UNVERIFIED", "No observed boxes supplied")
    statuses = {c["status"] for c in checks}
    status = "FAIL" if "FAIL" in statuses else "UNVERIFIED" if "UNVERIFIED" in statuses else "PASS"
    return {"status": status, "status_label": status + "_DECLARED_RULES_ONLY",
            "global_composition_conformity": "NOT_ESTABLISHED",
            "scope": "geometry_of_supplied_observed_boxes", "validation_profile": profile,
            "scope_note": spec.get("scope_note"),
            "automatic_ocr": False, "aesthetic_judgment": False,
            "evidence_method": proof.get("method"), "image_sha256": digest,
            "image_size": [iw, ih], "reference_canvas": [width, height], "checks": checks,
            "counts": {s: sum(c["status"] == s for c in checks) for s in ("PASS", "FAIL", "UNVERIFIED")},
            "limits": "The image hash binds the evidence, but does not prove manually entered box accuracy. No OCR or automatic object recognition is performed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--measurements", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--out")
    args = parser.parse_args()
    # Never replace any evidence or the contract with a report.
    if args.out and Path(args.out).resolve() in {Path(p).resolve() for p in (args.spec, args.measurements, args.image)}:
        parser.error("Report output must not overwrite an input")
    try:
        report = verify(load_json(args.spec), load_json(args.measurements), args.image)
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        report = {"status": "UNVERIFIED", "input_error": str(error)}
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return {"PASS": 0, "FAIL": 1, "UNVERIFIED": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
