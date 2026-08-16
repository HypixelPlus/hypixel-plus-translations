#!/usr/bin/env python3

import argparse
import json
import os
import sys
from pathlib import Path


LANG_DIR = Path("assets/minecraft/lang")


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(data, dict):
        print(f"ERROR: {path} must contain a JSON object.", file=sys.stderr)
        sys.exit(2)

    return data


def compare_files(base_path: Path, translation_path: Path):
    base = load_json(base_path)
    translation = load_json(translation_path)

    base_keys = set(base.keys())
    translation_keys = set(translation.keys())

    missing = sorted(base_keys - translation_keys)
    extra = sorted(translation_keys - base_keys)

    return missing, extra


def language_path(language: str) -> Path:
    language = language.strip()

    if language.endswith(".json"):
        filename = language
    else:
        filename = f"{language}.json"

    return LANG_DIR / filename


def main():
    parser = argparse.ArgumentParser(
        description="Compare language files for missing/extra keys."
    )

    parser.add_argument(
        "--base",
        default="en_us",
        help="Base language, without .json. Default: en_us",
    )

    parser.add_argument(
        "--languages",
        required=True,
        help="Comma-separated list of languages to check.",
    )

    parser.add_argument(
        "--output",
        default="lang-check-report.md",
        help="Markdown output file.",
    )

    args = parser.parse_args()

    base_path = language_path(args.base)
    languages = [
        lang.strip()
        for lang in args.languages.split(",")
        if lang.strip()
    ]

    if not languages:
        print("ERROR: No languages were specified.", file=sys.stderr)
        sys.exit(2)

    if any(language_path(lang) == base_path for lang in languages):
        languages = [
            lang for lang in languages
            if language_path(lang) != base_path
        ]

    if not languages:
        print("No translation files to check.")
        return 0

    results = []
    has_errors = False

    for language in languages:
        translation_path = language_path(language)

        if not translation_path.exists():
            results.append({
                "language": language,
                "missing": [],
                "extra": [],
                "error": f"File does not exist: `{translation_path}`",
            })
            has_errors = True
            continue

        missing, extra = compare_files(base_path, translation_path)

        if missing or extra:
            has_errors = True

        results.append({
            "language": language,
            "missing": missing,
            "extra": extra,
            "error": None,
        })

    markdown = []

    markdown.append("## Language File Check")
    markdown.append("")
    markdown.append(f"**Base language:** `{args.base}.json`")
    markdown.append("")

    if not has_errors:
        markdown.append("### All language files are in sync")
        markdown.append("")
        markdown.append(
            "No missing or extra translation keys were found."
        )
    else:
        markdown.append("### Differences found")
        markdown.append("")

        for result in results:
            language = result["language"]

            markdown.append(f"### `{language}.json`")
            markdown.append("")

            if result["error"]:
                markdown.append(f"{result['error']}")
                markdown.append("")
                continue

            missing = result["missing"]
            extra = result["extra"]

            if missing:
                markdown.append(
                    f"#### Missing keys ({len(missing)})"
                )
                markdown.append("")

                markdown.append("```text")
                markdown.extend(missing)
                markdown.append("```")
                markdown.append("")

            if extra:
                markdown.append(
                    f"#### Extra keys ({len(extra)})"
                )
                markdown.append("")

                markdown.append("```text")
                markdown.extend(extra)
                markdown.append("```")
                markdown.append("")

            if not missing and not extra:
                markdown.append("No differences.")
                markdown.append("")

    report = "\n".join(markdown)

    output_path = Path(args.output)
    output_path.write_text(report + "\n", encoding="utf-8")

    print(report)

    # GitHub Actions output
    github_output = os.environ.get("GITHUB_OUTPUT")

    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"has_errors={'true' if has_errors else 'false'}\n")

    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
