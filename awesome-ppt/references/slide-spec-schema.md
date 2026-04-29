# Slide Spec Schema

Use this JSON shape as the source of truth for `scripts/validate_deck.py` and `scripts/build_deck.py`.

## Deck

```json
{
  "deck": {
    "title": "Deck title",
    "slide_count": 8,
    "language": "en",
    "aspect_ratio": "16:9",
    "theme": {
      "font_face": "Aptos",
      "text_color": "#111111"
    }
  },
  "slides": []
}
```

Required deck fields:

- `title`: non-empty string.
- `slide_count`: integer greater than zero.
- `aspect_ratio`: `16:9`, `4:3`, or `1:1`.

Optional deck fields:

- `language`: BCP-47-ish language tag or short label.
- `theme.font_face`: default font for optional editable helper text.
- `theme.text_color`: default hex color for optional editable helper text.

## Slide

```json
{
  "slide_number": 1,
  "title": "Short slide title",
  "purpose": "The one job this slide performs",
  "slide_image": "images/slide-01.png",
  "image_prompt": "Prompt used with imagegen",
  "rendered_text": [
    { "role": "title", "text": "Exact visible title" },
    { "role": "body", "text": "Exact visible body line" }
  ],
  "editable_text": [],
  "speaker_notes": "Optional notes for the presenter"
}
```

Required slide fields:

- `slide_number`: 1-based sequential integer.
- `title`: non-empty string.
- `purpose`: non-empty string.
- `slide_image`: path to the generated full-slide image.
- `image_prompt`: final prompt used for image generation. It must include every `rendered_text[].text` value verbatim.
- `rendered_text`: complete list of visible text strings that must be rendered inside the generated image.

Optional slide fields:

- `background_image`: deprecated alias for `slide_image`, kept for compatibility.
- `editable_text`: optional native PPT helper text blocks. Do not use this field to supply default visible slide content after image generation.
- `speaker_notes`: presenter notes retained in the source spec. The standard-library v1 builder preserves this field in `deck.json` but does not embed PowerPoint notes pages.

## Rendered Text Item

```json
{
  "role": "title",
  "text": "Exact visible text",
  "placement": "top-left, large, high contrast"
}
```

Required fields:

- `text`: exact visible string that must appear in the generated slide image.

Optional fields:

- `role`: `title`, `subtitle`, `body`, `label`, `caption`, `source`, `callout`, or another short role.
- `placement`: concise layout instruction for the image prompt.

Rules:

- Include every visible title, subtitle, bullet, label, number, caption, source note, and callout.
- Keep strings short and exact.
- Do not include placeholder text.
- Every `text` value must appear verbatim inside `image_prompt`.

## Editable Text Block

Editable text blocks are optional helper layers. In the default v1 workflow, the visible text should already be baked into the generated slide image.

```json
{
  "id": "slide-title",
  "text": "Editable title text",
  "box": { "x": 0.08, "y": 0.08, "w": 0.72, "h": 0.16 },
  "style": {
    "font_face": "Aptos Display",
    "font_size": 38,
    "color": "#111111",
    "bold": true,
    "align": "left",
    "vertical_anchor": "top"
  }
}
```

`box` values are normalized slide coordinates:

- `x` and `y`: top-left position from `0.0` to `1.0`.
- `w` and `h`: width and height as a fraction of the slide.
- `x + w` and `y + h` must be less than or equal to `1.0`.

Text block rules:

- Use `text` for a single paragraph or line-broken text.
- Use `paragraphs` instead of `text` when individual paragraph settings are needed.
- Use concise text. Move long details to `speaker_notes`.
- Do not use visible editable text to patch missing content after image generation unless the user explicitly asks for that tradeoff.

Paragraph form:

```json
{
  "id": "bullets",
  "box": { "x": 0.1, "y": 0.3, "w": 0.52, "h": 0.38 },
  "style": { "font_size": 20, "color": "#222222" },
  "paragraphs": [
    { "text": "First point", "bullet": true, "level": 0 },
    { "text": "Second point", "bullet": true, "level": 0 }
  ]
}
```

Allowed style fields:

- `font_face`: string.
- `font_size`: number from 6 to 96.
- `color`: `#RRGGBB`.
- `bold`: boolean.
- `italic`: boolean.
- `align`: `left`, `center`, or `right`.
- `vertical_anchor`: `top`, `middle`, or `bottom`.

## Minimal Example

```json
{
  "deck": {
    "title": "AI Writing Product Pitch",
    "slide_count": 1,
    "language": "en",
    "aspect_ratio": "16:9",
    "theme": {
      "font_face": "Aptos",
      "text_color": "#111111"
    }
  },
  "slides": [
    {
      "slide_number": 1,
      "title": "Writing, without the blank page",
      "purpose": "Introduce the product promise",
      "slide_image": "images/slide-01.png",
      "image_prompt": "Create a complete 16:9 PowerPoint slide. Exact text to render: Title: \"Writing, without the blank page\". Layout: place \"Writing, without the blank page\" large in the upper left, high contrast. Use no extra text beyond the exact text listed above.",
      "rendered_text": [
        {
          "role": "title",
          "text": "Writing, without the blank page",
          "placement": "upper left, large, high contrast"
        }
      ],
      "editable_text": [],
      "speaker_notes": "Open with the core anxiety this product removes."
    }
  ]
}
```
