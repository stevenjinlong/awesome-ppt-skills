---
name: awesome-ppt-editable
description: Create a PowerPoint deck by first generating a standard image-first PPTX, then running a ppt-master reconstruction pass to produce a native editable PPTX. Use when the user invokes $awesome-ppt-editable or explicitly wants gpt-image/imagegen slide images converted into an editable PPT with native text, shapes, charts, and objects. This is a reconstruction workflow, not automatic lossless raster-to-vector conversion.
---

# Awesome PPT Editable

Use this wrapper for the experimental native editable reconstruction workflow.

## Mode Contract

- Command: `$awesome-ppt-editable`
- Output: two artifacts: the standard image-first PPTX and a `ppt-master` reconstructed native editable PPTX.
- Required flow: select style prompt -> write per-slide content/style/layout image prompts -> generate slide images -> build image-first PPTX -> export `ppt-master` handoff -> rebuild in `ppt-master`.
- Editability: the final native PPTX should use editable text, shapes, charts, and objects where practical.
- Do not claim lossless bitmap conversion. This is a visual/reference reconstruction from generated images plus exact `rendered_text`.

## Workflow

Read and follow the shared core skill at `../awesome-ppt/SKILL.md`, with these overrides:

1. Treat the mode as `editable`.
2. Always complete the standard image-first workflow first.
3. Always read `../awesome-ppt/references/ppt-master-integration.md` before the reconstruction pass.
4. Run `../awesome-ppt/scripts/export_ppt_master_handoff.py` after the image-first deck validates and builds.
5. Invoke `ppt-master` from a fresh rebuild project; do not reuse old `svg_output/`, `svg_final/`, `exports/`, or previous test artifacts.
6. After export, run `../awesome-ppt/scripts/inspect_pptx_package.py` against the native PPTX and verify slide count, native text, media count, required text, and black fallback color usage.
7. In the final response, provide both the image-first PPTX path and the editable PPTX path, plus any unresolved fidelity limitations.

Use the shared resources in `../awesome-ppt/references/` and `../awesome-ppt/scripts/`.
