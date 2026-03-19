# World Reports PDF Splitter

Splits human rights organization annual report PDFs into individual per-country files. Currently supports Amnesty International (AI), with Human Rights Watch (HRW) planned.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Setup

```bash
cd world_reports

# Create virtual environment and install dependencies
uv venv && source .venv/bin/activate
uv pip install pdfplumber pypdf pypdfium2
```

---

## Amnesty International (AI) Workflow

### Step 0: Add PDFs

Place all Amnesty International report PDFs in the `AI/` directory. The filenames should follow the pattern `<year>_Amnesty_International.pdf`, e.g.:

```
AI/
  1999_Amnesty_International.pdf
  2023_Amnesty_International.pdf
  2019_Africa_Amnesty_International.pdf
  ...
```

These PDFs are not included in the repo.

### Step 1: Configure

Edit `data/ai/contents_config.json` to register each PDF with:

- **contents_pages** — the 1-indexed PDF page numbers where the table of contents lives
- **offset** — the difference between a country's true PDF page and its page number as printed in the contents (`true_page - report_page`). Set to `null` if you plan to provide `true_page` values directly in the JSON.

To find the offset, open a PDF, note the page number listed for the first country in the contents (e.g. Afghanistan = 35), then find its actual PDF page (e.g. 48). The offset is `48 - 35 = 13`.

### Step 2: Extract contents page images

```bash
python scripts/ai/extract_contents_images.py           # all PDFs
python scripts/ai/extract_contents_images.py 2023      # specific year
```

This renders the contents pages as PNG images in `data/ai/contents_images/`.

### Step 3: Extract country data with Claude

Open Claude and attach the contents page images for a given report. Use this prompt:

> Extract every country name and its page number from this contents page.
> Return only valid JSON, no markdown fences or commentary:
>
> ```
> {"FILENAME.pdf": [{"name": "Afghanistan", "report_page": 50}, ...]}
> ```
>
> Only include country entries — skip headers like "Foreword", "Regional Overview", etc.

Save each response as a JSON file in `data/ai/contents_json/`, named to match the PDF (e.g. `2023_Amnesty_International.json`).

If a PDF has no machine-readable contents (or you prefer to do it manually), you can provide `true_page` instead of `report_page` in the JSON and set the offset to `null` in the config.

### Step 4: Build final config

```bash
python scripts/ai/build_final_config.py
```

This reads all JSONs from `data/ai/contents_json/`, applies the offsets, and writes `data/ai/parsed_contents.json`.

**Review `data/ai/parsed_contents.json` before proceeding** — spot-check a few entries by opening the original PDF and verifying the `true_page` values land on the correct country.

### Step 5: Split PDFs

```bash
python scripts/ai/split_pdfs.py                # all PDFs
python scripts/ai/split_pdfs.py 2023 2015      # specific years
```

Output goes to `output/ai/<year>/<Country_Name>.pdf`.

---

## Human Rights Watch (HRW) Workflow

_Coming soon._ HRW reports use a different layout and will have dedicated scripts in `scripts/hrw/`.

---

## Directory structure

```
world_reports/
  AI/                          # source PDFs (Amnesty International)
  HRW/                         # source PDFs (Human Rights Watch)
  IDMC/                        # source PDFs (IDMC)
  scripts/
    ai/                        # AI processing scripts
      extract_contents_images.py
      build_final_config.py
      split_pdfs.py
    hrw/                       # HRW processing scripts (planned)
  data/
    ai/                        # AI intermediate data
      contents_config.json     # contents pages + offsets per PDF
      parsed_contents.json     # generated: country names + true pages
      contents_images/         # generated: PNG images of contents pages
      contents_json/           # Claude's extracted country/page data
    hrw/                       # HRW intermediate data (planned)
  output/
    ai/                        # generated: per-country PDFs
      2023/
        Afghanistan.pdf
        Albania.pdf
        ...
    hrw/                       # HRW output (planned)
  new.sh                       # helper to open a new contents JSON
```
