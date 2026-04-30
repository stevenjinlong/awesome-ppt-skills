#!/usr/bin/env python3
"""Validate the Awesome PPT skill package before publishing."""

from __future__ import annotations

import py_compile
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("awesome-ppt", "awesome-ppt-std", "awesome-ppt-editable")
CORE_SCRIPTS = (
    "awesome-ppt/scripts/build_deck.py",
    "awesome-ppt/scripts/validate_deck.py",
    "awesome-ppt/scripts/export_ppt_master_handoff.py",
    "awesome-ppt/scripts/inspect_pptx_package.py",
)
CORE_REFERENCES = (
    "awesome-ppt/references/slide-spec-schema.md",
    "awesome-ppt/references/theme-style-prompt-library.md",
    "awesome-ppt/references/image-prompting.md",
    "awesome-ppt/references/editability-policy.md",
    "awesome-ppt/references/ppt-master-integration.md",
)
README_ASSETS = (
    "examples/transformer-architecture-image-first/preview.jpg",
)
README_FILES = (
    "README.md",
    "README.zh-CN.md",
)
IGNORED_OUTPUT_DIRS = (
    "awesome-ppt-output",
)

FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def main() -> int:
    errors: list[str] = []

    for skill in SKILLS:
        skill_dir = ROOT / skill
        skill_md = skill_dir / "SKILL.md"
        agent_yaml = skill_dir / "agents" / "openai.yaml"
        if not skill_md.exists():
            errors.append(f"missing {skill_md.relative_to(ROOT)}")
            continue
        try:
            metadata = _frontmatter(skill_md)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if metadata.get("name") != skill:
            errors.append(f"{skill_md.relative_to(ROOT)}: name must be {skill!r}")
        if not metadata.get("description"):
            errors.append(f"{skill_md.relative_to(ROOT)}: description is required")
        if not agent_yaml.exists():
            errors.append(f"missing {agent_yaml.relative_to(ROOT)}")

    for rel_path in CORE_REFERENCES:
        if not (ROOT / rel_path).exists():
            errors.append(f"missing {rel_path}")

    for rel_path in README_ASSETS:
        asset = ROOT / rel_path
        if not asset.exists():
            errors.append(f"missing {rel_path}")
            continue
        if asset.stat().st_size > 1_000_000:
            errors.append(f"{rel_path}: README asset should stay under 1 MB")

    for rel_path in README_FILES:
        if not (ROOT / rel_path).exists():
            errors.append(f"missing {rel_path}")

    readme_en = ROOT / "README.md"
    readme_zh = ROOT / "README.zh-CN.md"
    if readme_en.exists() and "README.zh-CN.md" not in readme_en.read_text(encoding="utf-8"):
        errors.append("README.md must link to README.zh-CN.md")
    if readme_zh.exists() and 'href="README.md"' not in readme_zh.read_text(encoding="utf-8"):
        errors.append("README.zh-CN.md must link back to README.md")

    gitignore = ROOT / ".gitignore"
    gitignore_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    for output_dir in IGNORED_OUTPUT_DIRS:
        if f"{output_dir}/" not in gitignore_text.splitlines():
            errors.append(f".gitignore must ignore {output_dir}/")

    if (ROOT / ".git").exists():
        for output_dir in IGNORED_OUTPUT_DIRS:
            result = subprocess.run(
                ["git", "ls-files", "--", output_dir],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(f"git ls-files failed for {output_dir}: {result.stderr.strip()}")
            elif result.stdout.strip():
                tracked = ", ".join(result.stdout.splitlines()[:5])
                errors.append(f"{output_dir}/ must not contain tracked files: {tracked}")

    for rel_path in CORE_SCRIPTS:
        script = ROOT / rel_path
        if not script.exists():
            errors.append(f"missing {rel_path}")
            continue
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"{rel_path}: {exc.msg}")

    for wrapper in ("awesome-ppt-std/SKILL.md", "awesome-ppt-editable/SKILL.md"):
        text = (ROOT / wrapper).read_text(encoding="utf-8")
        if "../awesome-ppt/SKILL.md" not in text:
            errors.append(f"{wrapper}: must reference shared core SKILL.md")
        if "../awesome-ppt/scripts/" not in text or "../awesome-ppt/references/" not in text:
            errors.append(f"{wrapper}: must reference shared scripts and references")

    if errors:
        print("Skill package validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("OK: Awesome PPT skill package is publishable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
