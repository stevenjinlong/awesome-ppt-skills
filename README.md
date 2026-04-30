<p align="center">
  <img src="https://img.shields.io/badge/Awesome-PPT-111827?style=for-the-badge" alt="Awesome PPT" />
  <img src="https://img.shields.io/badge/gpt--image--2-powered-00A3FF?style=for-the-badge" alt="gpt-image-2 powered" />
  <img src="https://img.shields.io/badge/PPT--Master-editable-2563EB?style=for-the-badge" alt="PPT Master editable optimization" />
  <img src="https://img.shields.io/badge/Codex-Skill-10B981?style=for-the-badge" alt="Codex Skill" />
  <img src="https://img.shields.io/badge/PPTX-export-F97316?style=for-the-badge" alt="PPTX export" />
</p>

<p align="center">
    <a href="https://linux.do" alt="LINUX DO">
        <img
            src="https://img.shields.io/badge/LINUX-DO-FFB003.svg?logo=data:image/svg%2bxml;base64,DQo8c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZyIgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiPjxwYXRoIGQ9Ik00Ni44Mi0uMDU1aDYuMjVxMjMuOTY5IDIuMDYyIDM4IDIxLjQyNmM1LjI1OCA3LjY3NiA4LjIxNSAxNi4xNTYgOC44NzUgMjUuNDV2Ni4yNXEtMi4wNjQtMjMuOTY4LTIxLjQzIDM4LTExLjUxMiA3Ljg4NS0yNS40NDUgOC44NzRoLTYuMjVxLTIzLjk3LTIuMDY0LTM4LjAwNC0yMS40M1EuOTcxIDY3LjA1Ni0uMDU0IDUzLjE4di02LjQ3M0MxLjM2MiAzMC43ODEgOC41MDMgMTguMTQ4IDIxLjM3IDguODE3IDI5LjA0NyAzLjU2MiAzNy41MjcuNjA0IDQ2LjgyMS0uMDU2IiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZWNlY2VjO2ZpbGwtb3BhY2l0eToxIi8+PHBhdGggZD0iTTQ3LjI2NiAyLjk1N3EyMi41My0uNjUgMzcuNzc3IDE1LjczOGE0OS43IDQ5LjcgMCAwIDEgNi44NjcgMTAuMTU3cS00MS45NjQuMjIyLTgzLjkzIDAgOS43NS0xOC42MTYgMzAuMDI0LTI0LjM4N2E2MSA2MSAwIDAgMSA5LjI2Mi0xLjUwOCIgc3R5bGU9InN0cm9rZTpub25lO2ZpbGwtcnVsZTpldmVub2RkO2ZpbGw6IzE5MTkxOTtmaWxsLW9wYWNpdHk6MSIvPjxwYXRoIGQ9Ik03Ljk4IDcwLjkyNmMyNy45NzctLjAzNSA1NS45NTQgMCA4My45My4xMTNRODMuNDI2IDg3LjQ3MyA2Ni4xMyA5NC4wODZxLTE4LjgxIDYuNTQ0LTM2LjgzMi0xLjg5OC0xNC4yMDMtNy4wOS0yMS4zMTctMjEuMjYyIiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZjlhZjAwO2ZpbGwtb3BhY2l0eToxIi8+PC9zdmc+" /></a>
</p>

<h1 align="center">Awesome PPT Skills</h1>

<p align="center">
  Turn a prompt into polished, full-slide PPT decks with <code>gpt-image-2</code>. Use <code>$awesome-ppt-std</code> for the stable image-first flow, or <code>$awesome-ppt-editable</code> for an experimental <code>ppt-master</code> editable reconstruction.
</p>

<p align="center">
  <a href="#english">English</a> | <a href="#中文">中文</a> | <a href="#star-history">Star History</a>
</p>

## English

Awesome PPT is a Codex skill for image-first presentation generation. It uses `gpt-image-2` to render each slide as a complete designed page, including titles, body text, labels, diagrams, and visual style, then assembles those slide images into a `.pptx`.

The repo exposes two explicit commands:

- `$awesome-ppt-std`: stable image-first workflow. It generates full-slide images and packages them into PPTX.
- `$awesome-ppt-editable`: experimental editable workflow. It first runs the standard workflow, then exports a reconstruction brief for [`ppt-master`](https://github.com/hugohe3/ppt-master) so the deck can be rebuilt as native editable text, shapes, charts, and objects.

`$awesome-ppt` remains as a backward-compatible core command, but new users should prefer the explicit `-std` or `-editable` commands.

### Why It Is Different

- Full-slide generation: the model designs the whole page, not just a background.
- Text-aware prompts: every visible title, bullet, label, and callout is written into the image prompt.
- Theme-aware style selection: the skill identifies the deck topic first, then adapts a matching style prompt from the bundled theme library.
- Fast deck assembly: generated slides are packaged into PPTX with a lightweight standard-library builder.
- Editable optimization: generated slide images become visual references for `ppt-master`, while `rendered_text` becomes the exact native editable text source.
- Safer command split: standard and editable workflows are separate commands, so unstable reconstruction behavior does not affect the stable image-first path.
- Rebuildable workflow: `deck.json` keeps the slide plan, rendered text, prompts, and image paths together.

### Install

Clone the repo:

```bash
git clone https://github.com/stevenjinlong/awesome-ppt-skills.git
cd awesome-ppt-skills
```

Install the skill into Codex:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
for skill in awesome-ppt awesome-ppt-std awesome-ppt-editable; do
  ln -sfn "$PWD/$skill" "${CODEX_HOME:-$HOME/.codex}/skills/$skill"
done
```

Restart Codex or open a new Codex session so the skill can be discovered.

`$awesome-ppt-std` works with this repo alone. `$awesome-ppt-editable` also requires the upstream [`ppt-master`](https://github.com/hugohe3/ppt-master) skill to be installed or symlinked in Codex.

### Usage

Invoke the skill in Codex:

```text
$awesome-ppt-std Create a 5-slide technical deck about Transformer, from history to architecture to applications. Use a dark engineering style, 16:9, and render all titles, body text, labels, and diagrams directly inside the generated slide images. --pages 5 --ratio 16:9 --lang en
```

Create an image-first deck and request a native editable optimization:

```text
$awesome-ppt-editable Create a 5-slide technical deck about Transformer. Use a dark engineering style. Generate the polished image-first deck first, then optimize it into a native editable PPTX with ppt-master. --pages 5 --ratio 16:9 --lang en
```

Chinese example:

```text
$awesome-ppt-std 做一个 5 页 PPT，主要介绍 Transformer，从历史到架构到应用，要偏技术风。所有标题、正文、标签都必须由 gpt-image-2 直接生成在每页图片里。 --pages 5 --ratio 16:9 --lang zh
```

### Example: Transformer Architecture

This is a 5-slide `$awesome-ppt-std` image-first deck generated from the Transformer architecture prompt. The visible text and diagrams are rendered directly inside each slide image, then assembled into a PPTX.

```text
$awesome-ppt-std 做一个介绍 Transformer 架构的 PPT，5 页左右，要求技术风，有文本。 --pages 5 --ratio 16:9 --lang zh
```

<p align="center">
  <img src="examples/transformer-architecture-image-first/preview.jpg" alt="Transformer architecture image-first PPT example" />
</p>

### Output

The skill writes a deck workspace like this:

```text
awesome-ppt-output/<deck-slug>/
  deck.json
  images/
    slide-01.png
    slide-02.png
  <deck-slug>.pptx                  # image-first PPTX
  ppt-master-handoff/
    ppt-master-brief.md
    ppt-master-request.md
    images/
      slide-01.png
  ppt-master-rebuild/               # editable mode only, created by ppt-master
  <deck-slug>-editable.pptx          # editable mode output, when available
```

### Build Manually

The scripts use only the Python standard library:

```bash
python scripts/validate_skill_package.py
python awesome-ppt/scripts/validate_deck.py awesome-ppt-output/my-deck/deck.json
python awesome-ppt/scripts/build_deck.py awesome-ppt-output/my-deck/deck.json --out awesome-ppt-output/my-deck/my-deck.pptx
python awesome-ppt/scripts/export_ppt_master_handoff.py awesome-ppt-output/my-deck/deck.json
python awesome-ppt/scripts/inspect_pptx_package.py awesome-ppt-output/my-deck/my-deck.pptx --expect-slides 5 --max-media 5
```

### Current Scope

- Supported image formats: PNG and JPEG.
- Supported ratios: 16:9, 4:3, and 1:1.
- Default visible content layer: generated slide image with rendered text.
- Optional helper layer: native PPT text boxes.
- Native editable optimization: `$awesome-ppt-editable` exports a `ppt-master` reconstruction handoff after the image-first deck is built. This depends on `ppt-master` and is not lossless bitmap-to-vector conversion.
- Future work: OCR-based text QA, notes-page embedding, source-file extraction, templates, and richer chart/table workflows.

## 中文

Awesome PPT 是一个面向 Codex 的 PPT 生成 skill。它的核心思路是让 `gpt-image-2` 直接生成完整幻灯片页面，包括标题、正文、标签、图示和视觉风格，然后再把这些整页图片组装成 `.pptx`。

仓库现在提供两个明确命令：

- `$awesome-ppt-std`：稳定的图片版流程，生成整页图片并组装成 PPTX。
- `$awesome-ppt-editable`：实验性的可编辑流程，先完整跑标准流程，再导出 brief 给 [`ppt-master`](https://github.com/hugohe3/ppt-master)，重建为原生可编辑文本、形状、图表和对象。

`$awesome-ppt` 保留为向后兼容的核心命令；新用户建议优先使用 `-std` 或 `-editable`。

### 优势

- 整页成图：不是只生成背景，而是让模型直接设计完整 PPT 页面。
- 文本进 prompt：每个可见标题、要点、标签和注释都会写进生图 prompt。
- 主题风格识别：先识别 PPT 主题，再参考内置风格 prompt 库做定制化设计。
- 快速组装：用轻量脚本把生成图片打包成 PPTX。
- 可编辑优化：生成图作为 `ppt-master` 的视觉参考，`rendered_text` 作为原生可编辑文本来源。
- 命令隔离：标准流程和可编辑重建流程拆开，避免不稳定的重建行为影响稳定生图链路。
- 可复现：`deck.json` 保留页数、文案、prompt 和图片路径，方便重建和迭代。

### 安装

克隆仓库：

```bash
git clone https://github.com/stevenjinlong/awesome-ppt-skills.git
cd awesome-ppt-skills
```

安装到 Codex：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
for skill in awesome-ppt awesome-ppt-std awesome-ppt-editable; do
  ln -sfn "$PWD/$skill" "${CODEX_HOME:-$HOME/.codex}/skills/$skill"
done
```

重启 Codex，或者打开一个新的 Codex 会话，让 skill 被重新发现。

`$awesome-ppt-std` 只依赖本仓库即可使用。`$awesome-ppt-editable` 还需要把上游 [`ppt-master`](https://github.com/hugohe3/ppt-master) skill 安装或 symlink 到 Codex。

### 使用

在 Codex 里直接调用：

```text
$awesome-ppt-std 做一个 5 页 PPT，主要介绍 Transformer，从历史到架构到应用，要偏技术风。所有标题、正文、标签都必须由 gpt-image-2 直接生成在每页图片里。 --pages 5 --ratio 16:9 --lang zh
```

生成图片版 PPTX 后，再让 `ppt-master` 重建可编辑版本：

```text
$awesome-ppt-editable 做一个 5 页 PPT，主要介绍 Transformer，要偏技术风。先生成高质量图片版 PPTX，再用 ppt-master 优化成原生可编辑 PPTX。 --pages 5 --ratio 16:9 --lang zh
```

也可以指定输出路径：

```text
$awesome-ppt-std 做一个 8 页中文产品发布会 PPT，科技感、电影感、少字大图。 --pages 8 --ratio 16:9 --lang zh --out awesome-ppt-output/product-launch/product-launch.pptx
```

### 示例：Transformer 架构

这是用 `$awesome-ppt-std` 生成的 5 页 Transformer 架构图片版 PPT 示例。所有可见文字和图示都直接渲染在每页幻灯片图片中，然后再组装成 PPTX。

```text
$awesome-ppt-std 做一个介绍 Transformer 架构的 PPT，5 页左右，要求技术风，有文本。 --pages 5 --ratio 16:9 --lang zh
```

<p align="center">
  <img src="examples/transformer-architecture-image-first/preview.jpg" alt="Transformer 架构图片版 PPT 示例" />
</p>

### 输出结构

```text
awesome-ppt-output/<deck-slug>/
  deck.json
  images/
    slide-01.png
    slide-02.png
  <deck-slug>.pptx                  # 图片版 PPTX
  ppt-master-handoff/
    ppt-master-brief.md
    ppt-master-request.md
    images/
      slide-01.png
  ppt-master-rebuild/               # 仅可编辑模式，由 ppt-master 创建
  <deck-slug>-editable.pptx          # 可编辑模式输出，如已生成
```

### 手动构建

脚本只使用 Python 标准库：

```bash
python scripts/validate_skill_package.py
python awesome-ppt/scripts/validate_deck.py awesome-ppt-output/my-deck/deck.json
python awesome-ppt/scripts/build_deck.py awesome-ppt-output/my-deck/deck.json --out awesome-ppt-output/my-deck/my-deck.pptx
python awesome-ppt/scripts/export_ppt_master_handoff.py awesome-ppt-output/my-deck/deck.json
python awesome-ppt/scripts/inspect_pptx_package.py awesome-ppt-output/my-deck/my-deck.pptx --expect-slides 5 --max-media 5
```

### 当前范围

- 支持 PNG 和 JPEG。
- 支持 16:9、4:3、1:1。
- 默认可见内容层是带文字的整页生成图片。
- 可选增加 PPT 原生文本框作为辅助层。
- 可编辑优化：`$awesome-ppt-editable` 在图片版 deck 生成后导出 `ppt-master` 重建 handoff。它依赖 `ppt-master`，不是无损位图转矢量。
- 后续可加入 OCR 文本校验、备注页写入、文件内容抽取、模板和更复杂的图表流程。

## Star History

<a href="https://www.star-history.com/#stevenjinlong/awesome-ppt-skills&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=stevenjinlong/awesome-ppt-skills&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=stevenjinlong/awesome-ppt-skills&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=stevenjinlong/awesome-ppt-skills&type=Date" />
  </picture>
</a>
