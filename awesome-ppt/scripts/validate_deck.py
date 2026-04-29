#!/usr/bin/env python3
"""Validate an Awesome PPT deck spec."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ASPECT_RATIOS = {
    "16:9": 16 / 9,
    "4:3": 4 / 3,
    "1:1": 1.0,
}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith(b"\xff\xd8"):
        idx = 2
        while idx + 9 < len(data):
            if data[idx] != 0xFF:
                idx += 1
                continue
            marker = data[idx + 1]
            idx += 2
            if marker in {0xD8, 0xD9}:
                continue
            if idx + 2 > len(data):
                break
            segment_length = int.from_bytes(data[idx : idx + 2], "big")
            if segment_length < 2 or idx + segment_length > len(data):
                break
            if 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC}:
                height = int.from_bytes(data[idx + 3 : idx + 5], "big")
                width = int.from_bytes(data[idx + 5 : idx + 7], "big")
                return width, height
            idx += segment_length
    raise ValueError("unsupported image type; use PNG or JPEG")


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Deck spec must be a JSON object.")
    return data


def _resolve_asset(spec_path: Path, asset_path: str) -> Path:
    path = Path(asset_path).expanduser()
    if not path.is_absolute():
        path = spec_path.parent / path
    return path


def _slide_image_value(slide: dict[str, Any]) -> str | None:
    value = slide.get("slide_image")
    if isinstance(value, str) and value.strip():
        return value
    value = slide.get("background_image")
    if isinstance(value, str) and value.strip():
        return value
    return None


def _validate_box(errors: list[str], slide_no: int, block_id: str, box: Any) -> None:
    if not isinstance(box, dict):
        _fail(errors, f"slide {slide_no} text {block_id}: box must be an object")
        return
    for key in ("x", "y", "w", "h"):
        value = box.get(key)
        if not isinstance(value, (int, float)):
            _fail(errors, f"slide {slide_no} text {block_id}: box.{key} must be a number")
            continue
        if value < 0 or value > 1:
            _fail(errors, f"slide {slide_no} text {block_id}: box.{key} must be between 0 and 1")
    x = box.get("x")
    y = box.get("y")
    w = box.get("w")
    h = box.get("h")
    if all(isinstance(v, (int, float)) for v in (x, y, w, h)):
        if w <= 0 or h <= 0:
            _fail(errors, f"slide {slide_no} text {block_id}: box width/height must be positive")
        if x + w > 1.0001:
            _fail(errors, f"slide {slide_no} text {block_id}: box extends past right edge")
        if y + h > 1.0001:
            _fail(errors, f"slide {slide_no} text {block_id}: box extends past bottom edge")


def _validate_style(errors: list[str], slide_no: int, block_id: str, style: Any) -> None:
    if style is None:
        return
    if not isinstance(style, dict):
        _fail(errors, f"slide {slide_no} text {block_id}: style must be an object")
        return
    font_size = style.get("font_size")
    if font_size is not None:
        if not isinstance(font_size, (int, float)) or font_size < 6 or font_size > 96:
            _fail(errors, f"slide {slide_no} text {block_id}: style.font_size must be 6..96")
    color = style.get("color")
    if color is not None and (not isinstance(color, str) or not HEX_RE.match(color)):
        _fail(errors, f"slide {slide_no} text {block_id}: style.color must be #RRGGBB")
    align = style.get("align")
    if align is not None and align not in {"left", "center", "right"}:
        _fail(errors, f"slide {slide_no} text {block_id}: style.align must be left, center, or right")
    anchor = style.get("vertical_anchor")
    if anchor is not None and anchor not in {"top", "middle", "bottom"}:
        _fail(errors, f"slide {slide_no} text {block_id}: style.vertical_anchor must be top, middle, or bottom")


def _validate_text_blocks(errors: list[str], slide_no: int, blocks: Any) -> None:
    if blocks is None:
        return
    if not isinstance(blocks, list):
        _fail(errors, f"slide {slide_no}: editable_text must be an array")
        return
    seen_ids: set[str] = set()
    for idx, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            _fail(errors, f"slide {slide_no} text block {idx}: must be an object")
            continue
        block_id = str(block.get("id") or f"#{idx}")
        if block_id in seen_ids:
            _fail(errors, f"slide {slide_no} text {block_id}: duplicate id")
        seen_ids.add(block_id)
        has_text = isinstance(block.get("text"), str) and bool(block.get("text").strip())
        paragraphs = block.get("paragraphs")
        has_paragraphs = isinstance(paragraphs, list) and len(paragraphs) > 0
        if not has_text and not has_paragraphs:
            _fail(errors, f"slide {slide_no} text {block_id}: provide text or paragraphs")
        if has_paragraphs:
            for p_idx, paragraph in enumerate(paragraphs, start=1):
                if not isinstance(paragraph, dict) or not str(paragraph.get("text", "")).strip():
                    _fail(errors, f"slide {slide_no} text {block_id} paragraph {p_idx}: text is required")
        _validate_box(errors, slide_no, block_id, block.get("box"))
        _validate_style(errors, slide_no, block_id, block.get("style"))


def _validate_rendered_text(errors: list[str], slide_no: int, slide: dict[str, Any]) -> None:
    rendered_text = slide.get("rendered_text")
    if not isinstance(rendered_text, list) or not rendered_text:
        _fail(errors, f"slide {slide_no}: rendered_text must be a non-empty array")
        return

    image_prompt = slide.get("image_prompt")
    if not isinstance(image_prompt, str) or not image_prompt.strip():
        _fail(errors, f"slide {slide_no}: image_prompt is required when rendered_text is present")
        image_prompt = ""

    seen_text: set[str] = set()
    for idx, item in enumerate(rendered_text, start=1):
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text_value = item.get("text")
            text = text_value.strip() if isinstance(text_value, str) else ""
        else:
            _fail(errors, f"slide {slide_no} rendered_text {idx}: must be a string or object")
            continue

        if not text:
            _fail(errors, f"slide {slide_no} rendered_text {idx}: text is required")
            continue
        if text in seen_text:
            _fail(errors, f"slide {slide_no} rendered_text {idx}: duplicate text {text!r}")
        seen_text.add(text)
        if text not in image_prompt:
            _fail(errors, f"slide {slide_no}: image_prompt must include rendered_text verbatim: {text!r}")


def validate_spec(spec_path: Path, tolerance: float = 0.015) -> list[str]:
    data = _load_json(spec_path)
    errors: list[str] = []

    deck = data.get("deck")
    if not isinstance(deck, dict):
        return ["deck must be an object"]

    title = deck.get("title")
    if not isinstance(title, str) or not title.strip():
        _fail(errors, "deck.title is required")

    slide_count = deck.get("slide_count")
    if not isinstance(slide_count, int) or slide_count <= 0:
        _fail(errors, "deck.slide_count must be a positive integer")

    aspect_ratio = deck.get("aspect_ratio")
    if aspect_ratio not in ASPECT_RATIOS:
        _fail(errors, "deck.aspect_ratio must be one of: 16:9, 4:3, 1:1")

    slides = data.get("slides")
    if not isinstance(slides, list):
        return errors + ["slides must be an array"]
    if isinstance(slide_count, int) and len(slides) != slide_count:
        _fail(errors, f"slides length {len(slides)} does not match deck.slide_count {slide_count}")

    expected_ratio = ASPECT_RATIOS.get(aspect_ratio, 16 / 9)
    for expected_no, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            _fail(errors, f"slide {expected_no}: must be an object")
            continue
        slide_no = slide.get("slide_number")
        if slide_no != expected_no:
            _fail(errors, f"slide {expected_no}: slide_number must be {expected_no}")
            slide_no = expected_no
        for field in ("title", "purpose"):
            value = slide.get(field)
            if not isinstance(value, str) or not value.strip():
                _fail(errors, f"slide {slide_no}: {field} is required")
        _validate_rendered_text(errors, int(slide_no), slide)
        slide_image = _slide_image_value(slide)
        if slide_image is None:
            _fail(errors, f"slide {slide_no}: slide_image is required")
        else:
            image_path = _resolve_asset(spec_path, slide_image)
            if not image_path.exists():
                _fail(errors, f"slide {slide_no}: slide_image not found: {image_path}")
            else:
                try:
                    width, height = _image_size(image_path)
                except ValueError as exc:
                    _fail(errors, f"slide {slide_no}: {exc}: {image_path}")
                    continue
                actual_ratio = width / height
                if abs(actual_ratio - expected_ratio) > tolerance:
                    _fail(
                        errors,
                        f"slide {slide_no}: image ratio {actual_ratio:.4f} does not match {aspect_ratio}",
                    )
        _validate_text_blocks(errors, int(slide_no), slide.get("editable_text", []))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to deck.json")
    parser.add_argument("--tolerance", type=float, default=0.015, help="Allowed image ratio delta")
    args = parser.parse_args()

    errors = validate_spec(args.spec, tolerance=args.tolerance)
    if errors:
        print("Deck spec validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"OK: {args.spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
