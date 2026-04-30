#!/usr/bin/env python3
"""Export an Awesome PPT deck spec as a PPT Master reconstruction handoff."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


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


def _slide_image_value(slide: dict[str, Any]) -> str:
    value = slide.get("slide_image")
    if isinstance(value, str) and value.strip():
        return value
    value = slide.get("background_image")
    if isinstance(value, str) and value.strip():
        return value
    raise SystemExit(f"Slide {slide.get('slide_number', '?')} is missing slide_image")


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").strip()


def _rendered_text_rows(items: Any) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    if not isinstance(items, list):
        return rows
    for item in items:
        if isinstance(item, str):
            rows.append(("body", item, ""))
        elif isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                rows.append(
                    (
                        str(item.get("role") or "body"),
                        text,
                        str(item.get("placement") or ""),
                    )
                )
    return rows


def _paragraph_lines(block: dict[str, Any]) -> list[str]:
    paragraphs = block.get("paragraphs")
    if isinstance(paragraphs, list) and paragraphs:
        return [str(paragraph.get("text", "")).strip() for paragraph in paragraphs if isinstance(paragraph, dict)]
    text = block.get("text")
    if isinstance(text, str):
        return [line.strip() for line in text.splitlines()]
    return []


def _editable_text_section(slide: dict[str, Any]) -> str:
    blocks = slide.get("editable_text")
    if not isinstance(blocks, list) or not blocks:
        return "No native helper text blocks were provided in the Awesome PPT spec."

    lines = ["| ID | Text | Normalized Box |", "| --- | --- | --- |"]
    for idx, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            continue
        block_id = block.get("id") or f"text-{idx}"
        text = " / ".join(line for line in _paragraph_lines(block) if line)
        box = block.get("box") if isinstance(block.get("box"), dict) else {}
        box_text = ", ".join(f"{key}={box.get(key)}" for key in ("x", "y", "w", "h") if key in box)
        lines.append(f"| {_md_escape(block_id)} | {_md_escape(text)} | {_md_escape(box_text)} |")
    return "\n".join(lines)


def _copy_reference_image(source: Path, images_dir: Path, slide_no: int) -> Path:
    if not source.exists():
        raise SystemExit(f"Missing slide image: {source}")
    suffix = source.suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise SystemExit(f"Unsupported reference image type: {source}")
    destination = images_dir / f"slide-{slide_no:02d}{suffix}"
    images_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_handoff(spec_path: Path, out_dir: Path, copy_images: bool = True) -> tuple[Path, Path]:
    data = _load_json(spec_path)
    deck = data.get("deck")
    slides = data.get("slides")
    if not isinstance(deck, dict):
        raise SystemExit("deck must be an object")
    if not isinstance(slides, list):
        raise SystemExit("slides must be an array")

    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir = out_dir / "images"
    title = str(deck.get("title") or "Awesome PPT Deck")
    aspect_ratio = str(deck.get("aspect_ratio") or "16:9")
    language = str(deck.get("language") or "unspecified")

    image_refs: dict[int, str] = {}
    for expected_no, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            raise SystemExit(f"slide {expected_no}: must be an object")
        slide_no = int(slide.get("slide_number") or expected_no)
        source = _resolve_asset(spec_path, _slide_image_value(slide))
        if copy_images:
            destination = _copy_reference_image(source, images_dir, slide_no)
            image_refs[slide_no] = _relative_or_absolute(destination, out_dir)
        else:
            image_refs[slide_no] = _relative_or_absolute(source, out_dir)

    lines = [
        f"# {title} - PPT Master Editable Reconstruction Brief",
        "",
        "## Objective",
        "",
        "Use PPT Master to rebuild this Awesome PPT image-first deck as a natively editable PPTX.",
        "",
        "**DO NOT embed the generated slide image as the final slide.** Use each generated image only as a visual reference, then recreate the slide with native SVG/PowerPoint text, shapes, charts, icons, and editable objects.",
        "",
        "The exact editable text source is `rendered_text`. The generated slide images define composition, mood, spacing, hierarchy, and visual style.",
        "",
        "## Deck Metadata",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Title | {_md_escape(title)} |",
        f"| Slide count | {_md_escape(deck.get('slide_count', len(slides)))} |",
        f"| Language | {_md_escape(language)} |",
        f"| Aspect ratio | {_md_escape(aspect_ratio)} |",
        "",
        "## Reconstruction Rules",
        "",
        "- Rebuild every slide as editable native PPT elements through PPT Master SVG generation.",
        "- Start from a fresh PPT Master rebuild project for this deck; do not reuse old svg_output, svg_final, or exports folders.",
        "- Preserve all `rendered_text` strings exactly; do not paraphrase, omit, or add visible text unless the user explicitly asks.",
        "- Match the reference image layout and visual direction closely, but prefer clean native shapes over raster screenshots.",
        "- Use reference images for visual QA only; the optimized PPTX should remain editable element-by-element.",
        "- If an image contains complex illustration or photography that cannot be recreated as native shapes, use a cropped image asset only for that visual subject, not as a full-slide screenshot.",
        "- Prefer direct SVG attributes over CSS classes or style strings so PPT Master can convert colors, typography, and shapes reliably.",
        "",
        "## Source Spec",
        "",
        f"- Original Awesome PPT spec: `{_relative_or_absolute(spec_path, out_dir)}`",
        "",
        "## Slides",
        "",
    ]

    for expected_no, slide in enumerate(slides, start=1):
        assert isinstance(slide, dict)
        slide_no = int(slide.get("slide_number") or expected_no)
        rows = _rendered_text_rows(slide.get("rendered_text"))
        lines.extend(
            [
                f"### Slide {slide_no:02d} - {slide.get('title', '')}",
                "",
                f"- Purpose: {_md_escape(slide.get('purpose', ''))}",
                f"- Reference image: `{image_refs[slide_no]}`",
                "",
                "#### Exact Editable Text",
                "",
                "| Role | Text | Placement |",
                "| --- | --- | --- |",
            ]
        )
        if rows:
            for role, text, placement in rows:
                lines.append(f"| {_md_escape(role)} | {_md_escape(text)} | {_md_escape(placement)} |")
        else:
            lines.append("| body |  |  |")
        lines.extend(
            [
                "",
                "#### Existing Native Helper Text",
                "",
                _editable_text_section(slide),
                "",
                "#### Original Image Prompt",
                "",
                "```text",
                str(slide.get("image_prompt") or "").strip(),
                "```",
                "",
            ]
        )
        notes = str(slide.get("speaker_notes") or "").strip()
        if notes:
            lines.extend(["#### Speaker Notes", "", notes, ""])

    lines.extend(
        [
            "## PPT Master Invocation Prompt",
            "",
            "```text",
            f"Use ppt-master to create a native editable {aspect_ratio} PPTX from this reconstruction brief.",
            "Treat the slide images as visual references only. Recreate the deck with editable text, shapes, charts, and objects.",
            "Do not use full-slide screenshots as final visible slide content.",
            "```",
            "",
        ]
    )

    brief_path = out_dir / "ppt-master-brief.md"
    brief_path.write_text("\n".join(lines), encoding="utf-8")

    request_path = out_dir / "ppt-master-request.md"
    request_path.write_text(
        "\n".join(
            [
                "# PPT Master Request",
                "",
                "Use `$ppt-master` with this source brief:",
                "",
                f"```text\n$ppt-master Create a native editable PPTX from {brief_path.as_posix()}. Start from a fresh rebuild project, use the referenced slide images only as visual references, recreate all visible text from rendered_text as editable native text, and do not embed full-slide screenshots as final slide content.\n```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return brief_path, request_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to Awesome PPT deck.json")
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="Output handoff directory. Defaults to <deck-dir>/ppt-master-handoff.",
    )
    parser.add_argument(
        "--no-copy-images",
        action="store_true",
        help="Reference the original slide images instead of copying them into the handoff directory.",
    )
    args = parser.parse_args()

    spec_path = args.spec.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve() if args.out_dir else spec_path.parent / "ppt-master-handoff"
    brief_path, request_path = build_handoff(spec_path, out_dir, copy_images=not args.no_copy_images)
    print(f"Wrote {brief_path}")
    print(f"Wrote {request_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
