# Editability Policy

V1 decks are image-model-rendered PPTX files:

- Generated raster images provide the complete visible slide, including text.
- PowerPoint assembly turns those rendered images into a deck.
- Optional native PPT text boxes are helper layers only, not the default content path.

## Image By Default

Put these into generated slide images:

- Titles, subtitles, bullets, quotes, captions, source notes, and footers.
- Numeric labels, callouts, and short chart/table labels.
- Backgrounds, illustrations, scenes, textures, atmosphere, and visual metaphors.
- Complex visual compositions that are expensive to recreate as native shapes.
- Subject imagery and editorial art.

## Optional Editable Helper Layer

Use `editable_text` only when the user explicitly wants a manual-editing layer or when you need an accessibility/reconstruction aid.

Rules:

- Do not use `editable_text` to supply missing visible content after image generation.
- Do not create visible duplicate text over correctly rendered image text unless the user asks for it.
- If used, keep `editable_text` aligned with `rendered_text` so future rebuilding is possible.
- Tell the user clearly whether text is baked into images, editable as native PPT text, or both.

## When To Pause

Pause and explain the tradeoff before proceeding if:

- The user needs legal, medical, financial, or compliance text to be perfectly editable and auditable.
- The slide needs a dense table or many exact numbers.
- The user asks for both "all text rendered by image model" and "all text natively editable" as hard requirements.
- The generated image repeatedly misspells required text after targeted retries.

## Quality Gates

A deck fails v1 quality if:

- A slide lacks `rendered_text`.
- `image_prompt` does not include every `rendered_text` item verbatim.
- Generated slide images omit or misspell required visible text.
- Generated slide images contain unwanted extra text or gibberish.
- `deck.slide_count` differs from the requested `--pages`.
- A generated image has the wrong aspect ratio.
- A slide has no clear purpose.
- The output PPTX cannot be written.
- The final response implies full native text editability when the visible text is baked into images.
