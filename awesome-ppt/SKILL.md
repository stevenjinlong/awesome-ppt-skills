---
name: awesome-ppt
description: Create image-model-rendered PowerPoint decks from a prompt, brief, or source files. Use when the user invokes $awesome-ppt or asks to make a polished PPT/PPTX by designing full-slide image prompts where gpt-image/imagegen renders the complete slide including all titles, body text, labels, and visual design, then assembling those rendered slide images into a PPTX.
---

# Awesome PPT

## Overview

Build a PPTX by planning the deck, generating one complete slide image per page with `imagegen`, then assembling those rendered slide images into PowerPoint.

V1 is image-model-first: every visible title, subtitle, bullet, label, caption, and callout must be included verbatim in the image prompt and rendered by the image model. Do not create a blank/background image and add the main content later as PowerPoint text.

The assembled PPTX is editable at the slide/image object level. Native editable text overlays are optional helper layers only; they are not the source of visible content in the default workflow.

## Command Shape

Accept free-form prompts after the skill name:

```text
$awesome-ppt <deck prompt> [--pages N] [--ratio 16:9|4:3|1:1] [--lang zh|en|...] [--style "..."] [--out deck.pptx]
```

Parameters:

- `--pages N`: requested slide count. If missing, infer from the narrative; default to 8 when the request is underspecified.
- `--ratio`: slide aspect ratio. Default to `16:9`.
- `--lang`: deck language. Infer from the user prompt when missing.
- `--style`: visual direction, brand mood, or reference style.
- `--out`: output PPTX path. Default to a descriptive slug in the working directory.

If `--pages N` is supplied, the final `slide_count`, number of generated images, and number of PPT slides must all equal `N`.

## Workflow

1. Parse the request and options. Identify audience, goal, language, slide count, ratio, visual tone, output path, and attached/source files.
2. Inspect source files before planning. Extract only the content that supports the deck: thesis, evidence, quotes, data, images, brand assets, and constraints.
3. Create a compact deck brief with `slide_count`, narrative arc, design system, content density, and image text-rendering policy.
4. Create one slide spec per slide using `references/slide-spec-schema.md`.
5. For every slide, define `rendered_text`: the complete visible text that must appear inside the generated image.
6. For every slide, write an `imagegen` prompt from `references/image-prompting.md`. The prompt must include every `rendered_text` item verbatim, plus layout instructions for where each text item appears.
7. Generate slide images with the `imagegen` skill/tool. Save each final slide image into a project-local folder such as `awesome-ppt-output/<deck-slug>/images/`.
8. Inspect generated images for text fidelity. If title/body text is missing, misspelled, or replaced with gibberish, regenerate that slide with a tighter prompt before assembling the deck.
9. Run `scripts/validate_deck.py` against the deck spec before building.
10. Run `scripts/build_deck.py` to create the PPTX.
11. Open or render-check the result when the environment supports it; otherwise at least verify that the PPTX file exists and the package can be written.

## Planning Rules

- Start from the story, not the image prompts. Each slide needs one job and one dominant read.
- Use `--pages` as a hard constraint. If the requested content cannot fit, ask before changing the page count.
- Keep slide text short enough for the image model to render accurately. Split crowded slides instead of shrinking text.
- Put all visible content text into `rendered_text` and the image prompt.
- Use `editable_text` only when explicitly requested as an auxiliary mirror layer for later manual editing. Do not use it to supply missing visible content after image generation.
- For charts and tables, include the exact visible labels/values in `rendered_text` and the image prompt. Avoid dense spreadsheet-like tables in v1 because rendered text fidelity becomes the bottleneck.
- If exact legal, financial, or compliance text must be perfectly editable and auditable, pause and explain that the image-first workflow is the wrong default for that slide.

## File Outputs

Recommended run folder:

```text
awesome-ppt-output/<deck-slug>/
  deck.json
  images/
    slide-01.png
    slide-02.png
  <deck-slug>.pptx
```

The `deck.json` file is the source of truth for assembly. Use relative image paths from the JSON file location when possible.

## Scripts

- `scripts/validate_deck.py`: validate slide count, required fields, `rendered_text`, prompt coverage, image existence, and image aspect ratios.
- `scripts/build_deck.py`: assemble a PPTX from a validated `deck.json`. The standard-library v1 builder writes one full-slide image per slide and can optionally add editable text boxes if `editable_text` is present.
- `scripts/requirements.txt`: reserved for future optional Python dependencies. V1 scripts use only the Python standard library.

No dependency installation is required for v1. If future optional dependencies are added, install them with:

```bash
python -m pip install -r awesome-ppt/scripts/requirements.txt
```

Validate and build:

```bash
python awesome-ppt/scripts/validate_deck.py awesome-ppt-output/my-deck/deck.json
python awesome-ppt/scripts/build_deck.py awesome-ppt-output/my-deck/deck.json --out awesome-ppt-output/my-deck/my-deck.pptx
```

## References

- Read `references/slide-spec-schema.md` before creating `deck.json`.
- Read `references/image-prompting.md` before generating slide images.
- Read `references/editability-policy.md` when deciding whether any optional editable helper layer is appropriate.
