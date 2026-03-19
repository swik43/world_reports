"""
Convert uppercase country names to title case in all JSON files
in AI_contents_json_intermediate/.
"""

import json
from pathlib import Path

DIR = Path("AI_contents_json_intermediate")


def titlecase_name(name: str) -> str:
    if not name.isupper():
        return name
    # Title case, then fix small words and special cases
    result = name.title()
    # Fix common prepositions/articles that should stay lowercase
    for word in ["And", "Of", "The", "D'"]:
        result = result.replace(f" {word} ", f" {word.lower()} ")
    # Fix D' contractions like "Côte D'Ivoire" -> "Côte d'Ivoire"
    result = result.replace("D'", "d'")
    return result


def main():
    for path in sorted(DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        changed = 0
        for pdf_name, countries in data.items():
            for country in countries:
                old = country["name"]
                new = titlecase_name(old)
                if old != new:
                    country["name"] = new
                    changed += 1

        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"{path.name}: {changed} names converted")


if __name__ == "__main__":
    main()
