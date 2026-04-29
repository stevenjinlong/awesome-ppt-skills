# Image Prompting

Generate one complete slide image per slide. The generated image is the final visible slide, including all titles, body text, labels, captions, and callouts.

## Core Rule

The image prompt must contain every visible text string verbatim. Do not ask the image model to create a generic background and do not rely on PowerPoint text boxes to add the real content later.

## Prompt Template

```text
Use case: productivity-visual
Asset type: complete full-slide PowerPoint page, text included
Slide ratio: <16:9|4:3|1:1>
Deck context: <audience, topic, tone, design system>
Slide number and purpose: <number> / <one job>

Exact text to render:
1. Title: "<exact title>"
2. Subtitle: "<exact subtitle, if any>"
3. Body line: "<exact body line>"
4. Label/caption/source: "<exact label>"

Layout instructions:
- Place "<exact title>" at <location>, large and highly legible.
- Place body lines in <layout>, with clear hierarchy and generous spacing.
- Keep text horizontal, crisp, high contrast, and free of distortion.
- Use no extra text beyond the exact text listed above.

Visual request:
<specific scene, composition, diagram, data visual, atmosphere, materials, lighting>

Typography direction:
<font mood, scale, weight, hierarchy, alignment, line spacing>

Style:
<palette, texture, lighting, motif, brand mood>

Avoid:
watermarks, logos unless provided, misspelled text, gibberish text, extra words, tiny unreadable labels, fake UI text, clutter.
```

## Text Design Rules

- Keep each slide to a small number of text elements.
- Prefer short, high-impact titles over long sentences.
- Use no more than 3-5 body lines on normal slides.
- Keep critical numbers and labels short.
- Avoid dense tables, tiny footnotes, and long legal copy.
- If a slide needs too much text, split it into multiple slides or move detail to `speaker_notes`.
- Use the same language as the deck. For Chinese decks, tell the model to render simplified Chinese text exactly as provided.

## Prompt Quality Pattern

Good prompt behavior:

- Gives exact text in a dedicated `Exact text to render` section.
- Repeats important text once in the layout instructions.
- Says "Use no extra text beyond the exact text listed above."
- Specifies text placement, hierarchy, contrast, and whitespace.
- Keeps text count low enough for the model to succeed.

Bad prompt behavior:

- "Leave space for a title."
- "Add some bullets about productivity."
- "Use elegant labels."
- "Do not render text."
- Asking for a dense dashboard full of tiny values.

## Size Guidance

Use image dimensions that match the deck ratio:

- `16:9`: prefer `1920x1080`, `2560x1440`, or another supported 16:9 size.
- `4:3`: prefer `1600x1200`.
- `1:1`: prefer `1600x1600`.

When using `gpt-image-2`, keep sizes within the model constraints exposed by the active image generation tool or API. If a requested size is rejected, choose the nearest supported same-ratio size and keep the deck spec ratio unchanged.

## Consistency Rules

- Keep a stable deck-wide palette, texture, type direction, and composition language.
- Vary slide composition enough that the deck does not feel like repeated wallpaper.
- Include the slide number and purpose in each image prompt to improve narrative fit.
- If the user supplied brand or source images, describe their role explicitly: reference style, exact asset to include, or source evidence.
- Keep all per-slide text in `rendered_text` so prompt coverage can be checked before generation.

## Per-Slide Prompt Checklist

Before generating, check that the prompt states:

- The slide ratio.
- The deck context.
- The slide purpose.
- Every visible text string verbatim.
- Where each text string should appear.
- The instruction to add no extra text.
- The visual composition.
- The typography direction.
- The avoid list.

After generating, inspect the image:

- Required text appears.
- Text is spelled correctly.
- No unwanted extra text appears.
- Text is readable at slide-view size.
- No important text is too close to edges.
