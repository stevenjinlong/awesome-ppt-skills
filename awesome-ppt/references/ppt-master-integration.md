# PPT Master Integration

Use this reference when the user invokes `$awesome-ppt-editable` or otherwise wants the `awesome-ppt` image-first output optimized into a fully editable native PPTX.

## Positioning

`awesome-ppt` and `ppt-master` solve different parts of the workflow:

- `awesome-ppt`: fast visual exploration and polished full-slide `gpt-image-2` renderings.
- `ppt-master`: native editable PPTX reconstruction with real text boxes, shapes, charts, and objects.

The integration is not raster-to-vector magic. It is a second-stage rebuild. The generated images are the visual target; `rendered_text` is the exact editable text source.

## When To Run

Run the editable optimization when the user invokes `$awesome-ppt-editable` or asks for:

- `--editable`, `--native`, or "fully editable".
- "use ppt-master".
- "turn the gpt-image-2 slides into editable PPT".
- A final artifact where text and core objects must be editable in PowerPoint.

Skip it when the user invokes `$awesome-ppt-std` or only needs a quick visual PPTX, a mood deck, or an image-first deliverable.

## Handoff Command

After slide images are generated, `deck.json` validates, and the image-first PPTX is built:

```bash
python awesome-ppt/scripts/export_ppt_master_handoff.py awesome-ppt-output/my-deck/deck.json
```

Default output:

```text
awesome-ppt-output/my-deck/ppt-master-handoff/
  ppt-master-brief.md
  ppt-master-request.md
  images/
    slide-01.png
    slide-02.png
```

Then invoke `ppt-master` with the generated request:

```text
$ppt-master Create a native editable PPTX from awesome-ppt-output/my-deck/ppt-master-handoff/ppt-master-brief.md. Use the referenced slide images only as visual references. Recreate all visible text from rendered_text as editable native text and do not embed full-slide screenshots as final slide content.
```

If `ppt-master` is not installed in the current Codex skill environment, tell the user to install or symlink the upstream skill from `https://github.com/hugohe3/ppt-master`, then rerun the invocation. Do not silently fall back to screenshot-only output for a request that explicitly requires native editability.

## Normal PPT Master Execution

Use a clean `ppt-master` rebuild project for every deck. Copy the handoff brief and reference images into that project, then generate new SVG pages from the current brief and current images.

Do not reuse an old `svg_output/`, `svg_final/`, `exports/`, or hand-authored SVG test folder. A stale SVG folder can produce a valid-looking but visually wrong PPTX, including black-slide failures that are unrelated to the current image generation step.

When running upstream `ppt-master` scripts directly, use Python 3.10 or newer. The upstream scripts use modern type syntax that fails on older Python versions.

Recommended native export sequence after SVG pages exist:

```bash
python /path/to/ppt-master/skills/ppt-master/scripts/svg_quality_checker.py awesome-ppt-output/my-deck/ppt-master-rebuild
python /path/to/ppt-master/skills/ppt-master/scripts/total_md_split.py awesome-ppt-output/my-deck/ppt-master-rebuild
python /path/to/ppt-master/skills/ppt-master/scripts/finalize_svg.py awesome-ppt-output/my-deck/ppt-master-rebuild
python /path/to/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py awesome-ppt-output/my-deck/ppt-master-rebuild -s final -t none -a none
```

For reliable native conversion, generated SVGs should prefer direct SVG attributes such as `fill`, `stroke`, `font-size`, `font-family`, and `opacity`. Avoid relying on CSS `style` strings or `class` selectors for core visual properties.

## Reconstruction Rules For PPT Master

- Treat each `images/slide-XX.*` file as a reference screenshot, not a final slide layer.
- Recreate title, subtitle, body text, captions, labels, and callouts as editable native text.
- Rebuild simple diagrams, cards, dividers, icons, and chart-like structures as native shapes where practical.
- Use cropped raster assets only for complex illustration or photo subjects that should remain image content.
- Preserve the exact text in `rendered_text`; do not rely on OCR from the generated image.
- Keep the same slide count and aspect ratio as the Awesome PPT spec.

## Quality Gate

Before calling the optimized PPTX done:

- The deck followed the full flow: style prompt selection -> per-slide image prompts -> generated images -> image-first PPTX -> editable reconstruction.
- The image-first PPTX exists and opens or at least writes as a valid package.
- `ppt-master-brief.md` includes every slide and references every generated image.
- The reconstruction used a fresh `ppt-master` rebuild folder, not stale SVG/output folders from a previous attempt.
- `svg_quality_checker.py` passes before export.
- The final `ppt-master` PPTX is not just full-slide screenshots.
- Visible text in the optimized PPTX matches `rendered_text`.
- Any unavoidable raster regions are limited to visual subjects, not the whole slide.
- `scripts/inspect_pptx_package.py` confirms the expected slide count, native text presence, required text strings, and no suspicious black fallback color usage for the chosen design.
