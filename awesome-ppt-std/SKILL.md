---
name: awesome-ppt-std
description: Create a standard image-first PowerPoint deck from a prompt, brief, or source files. Use when the user invokes $awesome-ppt-std or wants a polished PPT/PPTX where gpt-image/imagegen renders complete full-slide images including all visible text, labels, diagrams, and visual design, then assembles those rendered images into a PPTX. This mode does not run ppt-master and does not claim fully native editability.
---

# Awesome PPT Standard

Use this wrapper for the stable image-first workflow.

## Mode Contract

- Command: `$awesome-ppt-std`
- Output: image-first PPTX with one generated full-slide image per slide.
- Editability: slide/image objects are editable; visible text is baked into generated images unless optional helper text is explicitly requested.
- Do not run `ppt-master` in this mode.
- If the user asks for a fully editable/native deck while invoking `$awesome-ppt-std`, explain that this command is standard mode and recommend `$awesome-ppt-editable`.

## Workflow

Read and follow the shared core skill at `../awesome-ppt/SKILL.md`, with these overrides:

1. Treat the mode as `standard`.
2. If the request includes `--editable`, `--native`, or implicit editable wording, do not execute the editable pass; explain that `$awesome-ppt-std` is standard mode and recommend `$awesome-ppt-editable`.
3. Stop after validating `deck.json`, generating slide images, and building the image-first PPTX.
4. In the final response, state clearly that the produced PPTX is image-first, not fully native editable.

Use the shared resources in `../awesome-ppt/references/` and `../awesome-ppt/scripts/`.
