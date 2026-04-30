#!/usr/bin/env python3
"""Inspect a PPTX package for slide, media, text, and color sanity checks."""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml$")
TEXT_RE = re.compile(r"<a:t>(.*?)</a:t>", re.DOTALL)
COLOR_RE = re.compile(r'<a:srgbClr\s+val="([0-9A-Fa-f]{6})"')


def _read_slide_xml(pptx_path: Path) -> tuple[list[str], list[str], str]:
    try:
        with ZipFile(pptx_path) as package:
            names = package.namelist()
            slides = sorted(name for name in names if SLIDE_RE.match(name))
            media = sorted(name for name in names if name.startswith("ppt/media/"))
            xml = "\n".join(
                package.read(name).decode("utf-8", errors="ignore") for name in slides
            )
    except BadZipFile as exc:
        raise SystemExit(f"Invalid PPTX package: {pptx_path}") from exc
    return slides, media, xml


def _extract_text(xml: str) -> list[str]:
    return [html.unescape(match).strip() for match in TEXT_RE.findall(xml) if match.strip()]


def inspect_package(pptx_path: Path) -> dict[str, object]:
    slides, media, xml = _read_slide_xml(pptx_path)
    text_nodes = _extract_text(xml)
    colors = sorted({match.upper() for match in COLOR_RE.findall(xml)})
    return {
        "slides": len(slides),
        "media": len(media),
        "text_nodes": len(text_nodes),
        "text_chars": sum(len(text) for text in text_nodes),
        "black_color_uses": xml.upper().count('VAL="000000"'),
        "colors": colors,
        "sample_text": text_nodes[:16],
        "all_text": "\n".join(text_nodes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="PPTX file to inspect")
    parser.add_argument("--expect-slides", type=int, help="Fail unless the slide count matches")
    parser.add_argument("--expect-native-text", action="store_true", help="Fail if no native text nodes exist")
    parser.add_argument("--max-media", type=int, help="Fail if the media file count exceeds this number")
    parser.add_argument(
        "--max-black-color-uses",
        type=int,
        help="Fail if srgb color #000000 appears more than this number of times",
    )
    parser.add_argument(
        "--require-text",
        action="append",
        default=[],
        help="Fail unless this text appears in native PPT text. Can be repeated.",
    )
    args = parser.parse_args()

    pptx_path = args.pptx.expanduser().resolve()
    if not pptx_path.exists():
        raise SystemExit(f"Missing PPTX: {pptx_path}")

    info = inspect_package(pptx_path)
    print(f"file={pptx_path}")
    print(
        "slides={slides} media={media} text_nodes={text_nodes} "
        "text_chars={text_chars} black_color_uses={black_color_uses}".format(**info)
    )
    print("colors=" + ",".join(info["colors"]))  # type: ignore[arg-type]
    print("sample_text=" + " | ".join(info["sample_text"]))  # type: ignore[arg-type]

    errors: list[str] = []
    if args.expect_slides is not None and info["slides"] != args.expect_slides:
        errors.append(f"expected {args.expect_slides} slides, found {info['slides']}")
    if args.expect_native_text and info["text_nodes"] == 0:
        errors.append("expected native editable text nodes, found none")
    if args.max_media is not None and info["media"] > args.max_media:
        errors.append(f"expected at most {args.max_media} media files, found {info['media']}")
    if args.max_black_color_uses is not None and info["black_color_uses"] > args.max_black_color_uses:
        errors.append(
            "expected at most "
            f"{args.max_black_color_uses} black color uses, found {info['black_color_uses']}"
        )
    all_text = str(info["all_text"])
    for text in args.require_text:
        if text not in all_text:
            errors.append(f"required text not found: {text}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
