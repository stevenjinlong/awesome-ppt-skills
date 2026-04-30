#!/usr/bin/env python3
"""Build an image-first PPTX from an Awesome PPT deck spec.

The writer intentionally uses only the Python standard library. It creates a
minimal OOXML presentation with one full-slide raster image per slide plus
editable native text boxes layered above it.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


EMU_PER_INCH = 914400
ASPECT_SIZES = {
    "16:9": (13.333333, 7.5, "wide"),
    "4:3": (10.0, 7.5, "screen4x3"),
    "1:1": (7.5, 7.5, "custom"),
}
ALIGN = {
    "left": "l",
    "center": "ctr",
    "right": "r",
}
ANCHOR = {
    "top": "t",
    "middle": "ctr",
    "bottom": "b",
}
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


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


def _emu(inches: float) -> int:
    return int(round(inches * EMU_PER_INCH))


def _xml(text: Any) -> str:
    return escape(str(text), {'"': "&quot;", "'": "&apos;"})


def _color(value: str) -> str:
    if not HEX_RE.match(value):
        return "111111"
    return value.lstrip("#").upper()


def _content_type_for_image(path: Path) -> str:
    content_type, _ = mimetypes.guess_type(path.name)
    if content_type in {"image/png", "image/jpeg"}:
        return content_type
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    raise SystemExit(f"Unsupported image type for PPTX embedding: {path}")


def _extension_for_content_type(content_type: str) -> str:
    return ".png" if content_type == "image/png" else ".jpg"


def _rels(items: list[tuple[str, str, str]]) -> str:
    relationships = "\n".join(
        f'<Relationship Id="{_xml(rel_id)}" Type="{_xml(rel_type)}" Target="{_xml(target)}"/>'
        for rel_id, rel_type, target in items
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{relationships}</Relationships>"
    )


def _sp_tree_start() -> str:
    return """
<p:nvGrpSpPr>
  <p:cNvPr id="1" name=""/>
  <p:cNvGrpSpPr/>
  <p:nvPr/>
</p:nvGrpSpPr>
<p:grpSpPr>
  <a:xfrm>
    <a:off x="0" y="0"/>
    <a:ext cx="0" cy="0"/>
    <a:chOff x="0" y="0"/>
    <a:chExt cx="0" cy="0"/>
  </a:xfrm>
</p:grpSpPr>
""".strip()


def _picture_xml(shape_id: int, rel_id: str, cx: int, cy: int) -> str:
    return f"""
<p:pic>
  <p:nvPicPr>
    <p:cNvPr id="{shape_id}" name="Background Image"/>
    <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
    <p:nvPr/>
  </p:nvPicPr>
  <p:blipFill>
    <a:blip r:embed="{rel_id}"/>
    <a:stretch><a:fillRect/></a:stretch>
  </p:blipFill>
  <p:spPr>
    <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
</p:pic>
""".strip()


def _merge_style(theme: dict[str, Any], block_style: Any) -> dict[str, Any]:
    style = {
        "font_face": theme.get("font_face", "Aptos"),
        "font_size": 22,
        "color": theme.get("text_color", "#111111"),
        "bold": False,
        "italic": False,
        "align": "left",
        "vertical_anchor": "top",
    }
    if isinstance(block_style, dict):
        style.update(block_style)
    return style


def _run_xml(text: str, style: dict[str, Any]) -> str:
    size = int(round(float(style.get("font_size", 22)) * 100))
    bold = ' b="1"' if bool(style.get("bold")) else ""
    italic = ' i="1"' if bool(style.get("italic")) else ""
    typeface = _xml(style.get("font_face", "Aptos"))
    color = _color(str(style.get("color", "#111111")))
    return f"""
<a:r>
  <a:rPr lang="en-US" sz="{size}"{bold}{italic}>
    <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
    <a:latin typeface="{typeface}"/>
    <a:ea typeface="{typeface}"/>
    <a:cs typeface="{typeface}"/>
  </a:rPr>
  <a:t>{_xml(text)}</a:t>
</a:r>
""".strip()


def _paragraph_xml(text: str, style: dict[str, Any], bullet: bool = False, level: int = 0) -> str:
    align = ALIGN.get(str(style.get("align", "left")), "l")
    indent = ""
    bullet_xml = ""
    if bullet:
        margin = 342900 + max(level, 0) * 342900
        indent = f' marL="{margin}" indent="-171450"'
        bullet_xml = '<a:buChar char="•"/>'
    return f"""
<a:p>
  <a:pPr algn="{align}"{indent}>{bullet_xml}</a:pPr>
  {_run_xml(text, style)}
</a:p>
""".strip()


def _text_shape_xml(shape_id: int, block: dict[str, Any], deck_cx: int, deck_cy: int, theme: dict[str, Any]) -> str:
    box = block["box"]
    x = int(deck_cx * float(box["x"]))
    y = int(deck_cy * float(box["y"]))
    w = int(deck_cx * float(box["w"]))
    h = int(deck_cy * float(box["h"]))
    style = _merge_style(theme, block.get("style"))
    anchor = ANCHOR.get(str(style.get("vertical_anchor", "top")), "t")
    name = _xml(block.get("id", f"Text {shape_id}"))

    if isinstance(block.get("paragraphs"), list) and block["paragraphs"]:
        paragraph_xml = "\n".join(
            _paragraph_xml(
                str(paragraph.get("text", "")),
                style,
                bullet=bool(paragraph.get("bullet", False)),
                level=int(paragraph.get("level", 0)),
            )
            for paragraph in block["paragraphs"]
        )
    else:
        paragraph_xml = "\n".join(
            _paragraph_xml(line, style)
            for line in str(block.get("text", "")).splitlines()
            if line.strip()
        )
        if not paragraph_xml:
            paragraph_xml = _paragraph_xml("", style)

    return f"""
<p:sp>
  <p:nvSpPr>
    <p:cNvPr id="{shape_id}" name="{name}"/>
    <p:cNvSpPr txBox="1"/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr wrap="square" anchor="{anchor}" rtlCol="0">
      <a:spAutoFit/>
    </a:bodyPr>
    <a:lstStyle/>
    {paragraph_xml}
  </p:txBody>
</p:sp>
""".strip()


def _slide_xml(slide_spec: dict[str, Any], image_rel_id: str, deck_cx: int, deck_cy: int, theme: dict[str, Any]) -> str:
    shapes = [_sp_tree_start(), _picture_xml(2, image_rel_id, deck_cx, deck_cy)]
    shape_id = 3
    for block in slide_spec.get("editable_text", []):
        shapes.append(_text_shape_xml(shape_id, block, deck_cx, deck_cy, theme))
        shape_id += 1
    shape_xml = "\n".join(shapes)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      {shape_xml}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""


def _presentation_xml(slide_count: int, deck_cx: int, deck_cy: int, slide_type: str) -> str:
    slide_ids = "\n".join(
        f'<p:sldId id="{255 + idx}" r:id="rId{idx + 1}"/>'
        for idx in range(1, slide_count + 1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{deck_cx}" cy="{deck_cy}" type="{slide_type}"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr><a:defRPr lang="en-US"/></a:defPPr>
  </p:defaultTextStyle>
</p:presentation>
"""


def _content_types(slides: list[dict[str, Any]], media_types: list[str]) -> str:
    defaults = {
        "rels": "application/vnd.openxmlformats-package.relationships+xml",
        "xml": "application/xml",
    }
    if "image/png" in media_types:
        defaults["png"] = "image/png"
    if "image/jpeg" in media_types:
        defaults["jpg"] = "image/jpeg"
        defaults["jpeg"] = "image/jpeg"
    default_xml = "\n".join(
        f'<Default Extension="{ext}" ContentType="{content_type}"/>'
        for ext, content_type in defaults.items()
    )
    slide_overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for idx, _ in enumerate(slides, start=1)
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  {default_xml}
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {slide_overrides}
</Types>
"""


def _slide_master_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>{_sp_tree_start()}</p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle/><p:bodyStyle/><p:otherStyle/>
  </p:txStyles>
</p:sldMaster>
"""


def _slide_layout_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree>{_sp_tree_start()}</p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"""


def _theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Awesome PPT">
  <a:themeElements>
    <a:clrScheme name="Awesome PPT">
      <a:dk1><a:srgbClr val="111111"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F2937"/></a:dk2>
      <a:lt2><a:srgbClr val="F8FAFC"/></a:lt2>
      <a:accent1><a:srgbClr val="2563EB"/></a:accent1>
      <a:accent2><a:srgbClr val="F97316"/></a:accent2>
      <a:accent3><a:srgbClr val="10B981"/></a:accent3>
      <a:accent4><a:srgbClr val="E11D48"/></a:accent4>
      <a:accent5><a:srgbClr val="7C3AED"/></a:accent5>
      <a:accent6><a:srgbClr val="0F766E"/></a:accent6>
      <a:hlink><a:srgbClr val="2563EB"/></a:hlink>
      <a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Awesome PPT">
      <a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Aptos"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Awesome PPT">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>
"""


def _core_xml(title: str) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{_xml(title)}</dc:title>
  <dc:creator>awesome-ppt</dc:creator>
  <cp:lastModifiedBy>awesome-ppt</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>
"""


def _app_xml(slide_count: int) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>awesome-ppt</Application>
  <PresentationFormat>On-screen Show</PresentationFormat>
  <Slides>{slide_count}</Slides>
</Properties>
"""


def build_deck(spec_path: Path, out_path: Path) -> None:
    data = _load_json(spec_path)
    deck = data["deck"]
    slides = data["slides"]
    aspect_ratio = deck.get("aspect_ratio", "16:9")
    width_in, height_in, slide_type = ASPECT_SIZES.get(aspect_ratio, ASPECT_SIZES["16:9"])
    deck_cx = _emu(width_in)
    deck_cy = _emu(height_in)
    theme = deck.get("theme") if isinstance(deck.get("theme"), dict) else {}

    image_entries: list[tuple[int, Path, str, str]] = []
    media_types: list[str] = []
    for idx, slide in enumerate(slides, start=1):
        image_path = _resolve_asset(spec_path, _slide_image_value(slide))
        if not image_path.exists():
            raise SystemExit(f"Missing slide image: {image_path}")
        content_type = _content_type_for_image(image_path)
        media_types.append(content_type)
        image_entries.append((idx, image_path, content_type, _extension_for_content_type(content_type)))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as pptx:
        pptx.writestr("[Content_Types].xml", _content_types(slides, media_types))
        pptx.writestr(
            "_rels/.rels",
            _rels(
                [
                    ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml"),
                    ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
                    ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties", "docProps/app.xml"),
                ]
            ),
        )
        presentation_rels = [
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml")
        ]
        for idx, _slide in enumerate(slides, start=1):
            presentation_rels.append(
                (f"rId{idx + 1}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", f"slides/slide{idx}.xml")
            )
        pptx.writestr("ppt/_rels/presentation.xml.rels", _rels(presentation_rels))
        pptx.writestr("ppt/presentation.xml", _presentation_xml(len(slides), deck_cx, deck_cy, slide_type))
        pptx.writestr("ppt/slideMasters/slideMaster1.xml", _slide_master_xml())
        pptx.writestr(
            "ppt/slideMasters/_rels/slideMaster1.xml.rels",
            _rels(
                [
                    ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
                    ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "../theme/theme1.xml"),
                ]
            ),
        )
        pptx.writestr("ppt/slideLayouts/slideLayout1.xml", _slide_layout_xml())
        pptx.writestr(
            "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            _rels(
                [
                    ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml")
                ]
            ),
        )
        pptx.writestr("ppt/theme/theme1.xml", _theme_xml())
        pptx.writestr("docProps/core.xml", _core_xml(str(deck.get("title", "Awesome PPT Deck"))))
        pptx.writestr("docProps/app.xml", _app_xml(len(slides)))

        for idx, image_path, _content_type, extension in image_entries:
            media_name = f"image{idx}{extension}"
            pptx.write(image_path, f"ppt/media/{media_name}")
            pptx.writestr(
                f"ppt/slides/_rels/slide{idx}.xml.rels",
                _rels(
                    [
                        ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
                        ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", f"../media/{media_name}"),
                    ]
                ),
            )
            pptx.writestr(f"ppt/slides/slide{idx}.xml", _slide_xml(slides[idx - 1], "rId2", deck_cx, deck_cy, theme))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Path to deck.json")
    parser.add_argument("--out", type=Path, required=True, help="Output .pptx path")
    args = parser.parse_args()

    build_deck(args.spec, args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
