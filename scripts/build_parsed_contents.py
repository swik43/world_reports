"""
Combine Claude's output (name + report_page) with contents_config.json
to produce parsed_contents.json with true_page values.

Expects claude_output.json with format:
{
  "2023_Amnesty_International.pdf": [
    { "name": "Afghanistan", "report_page": 15 },
    { "name": "Albania", "report_page": 21 }
  ]
}

true_page = last_contents_page + report_page
"""

import json
from pathlib import Path

AI_DIR = Path("AI")
CONFIG_PATH = AI_DIR / "contents_config.json"
CLAUDE_OUTPUT_PATH = Path("claude_output.json")
OUTPUT_PATH = AI_DIR / "parsed_contents.json"


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)

    with open(CLAUDE_OUTPUT_PATH) as f:
        claude = json.load(f)

    result = {}
    for pdf_name, countries in sorted(claude.items()):
        if pdf_name not in config:
            print(f"WARNING: {pdf_name} not in contents_config.json, skipping")
            continue

        last_contents_page = max(config[pdf_name]["contents_pages"])

        for country in countries:
            country["true_page"] = last_contents_page + country["report_page"]

        result[pdf_name] = countries
        print(f"{pdf_name}: {len(countries)} countries (offset: +{last_contents_page})")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
