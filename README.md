# World Reports PDF Splitter

Splits human rights organization annual report PDFs into individual per-country files. Currently handles:
- Amnesty International (AI)
- Human Rights Watch (HRW).

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Setup

```bash
# Create virtual environment and install dependencies
uv venv && source .venv/bin/activate
uv sync
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

Open Claude and attach the contents page images for a given report. Use this [prompt](data/ai/contents_json/prompt.md)

Save each response as a JSON file in `data/ai/contents_json/`, named to match the PDF (e.g. `2023_Amnesty_International.json`).

To create a new contents JSON file and open it in your editor, run:
```
scripts/new.sh <kind> <year>
```
where:
- `<kind>` is `ai` or `hrw` 
- `<year>` is the report year

For example:
```
scripts/new.sh ai 2023
```
opens `data/ai/contents_json/2023_Amnesty_International.json` in your editor `$EDITOR` and you can paste the output from Claude in this file.

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

HRW reports come in two layouts:

- **Single-layout** (2005–2015, 2017–2018, 2022): one printed page per PDF page, same as AI reports.
- **Double-layout** (2016, 2019–2021, 2023–2024): two printed pages side by side on each PDF page. These need an extra preprocessing step.

### Step 0: Add PDFs

Place HRW report PDFs in the `HRW/` directory. These are not included in the repo.

### Step 1: Configure

Edit `data/hrw/contents_config.json` to register each PDF with:

- **contents_pages** — 1-indexed PDF pages where the table of contents lives
- **layout** — `"single"` or `"double"`

For single-layout PDFs:
- **offset** — `true_page - report_page` (same as AI)

For double-layout PDFs:
- **double_start** — the PDF page where the double-page layout begins (typically 2, since page 1 is a single-page cover)
- **report_page_1** — the PDF page containing report page 1

### Step 2: Extract contents page images

```bash
python scripts/hrw/extract_contents_images.py           # all PDFs
python scripts/hrw/extract_contents_images.py 2023      # specific year
```

### Step 3: Extract country data with Claude

Same process as AI — attach contents page images and extract `{"name", "report_page"}` entries into `data/hrw/contents_json/`.

### Step 4: Unsplit double-layout PDFs

```bash
python scripts/hrw/unsplit_double_pages.py               # all double-layout PDFs
python scripts/hrw/unsplit_double_pages.py 2024 2023     # specific years
```

This crops each double page into left and right halves, producing single-page-per-sheet PDFs in `output/hrw_unsplit/`. Originals are not modified. This step takes some time.

### Step 5: Build final config

```bash
python scripts/hrw/build_final_config.py
```

For double-layout PDFs, the offset is computed automatically from `report_page_1` and `double_start`. Writes `data/hrw/parsed_contents.json`.

### Step 6: Split PDFs

```bash
python scripts/hrw/split_pdfs.py                # all PDFs
python scripts/hrw/split_pdfs.py 2023 2015      # specific years
```

Single-layout PDFs are read from `HRW/`, double-layout PDFs are read from `output/hrw_unsplit/`. Output goes to `output/hrw/<year>/<Country_Name>.pdf`.

---

## Directory structure

```
world_reports/
├── AI/                            # source PDFs (Amnesty International)
├── HRW/                           # source PDFs (Human Rights Watch)
├── scripts/
│   ├── new.sh                     # helper to open a new contents JSON
│   ├── ai/
│   │   ├── extract_contents_images.py
│   │   ├── build_final_config.py
│   │   ├── split_pdfs.py
│   │   └── convert_to_markdown.py
│   └── hrw/
│       ├── extract_contents_images.py
│       ├── unsplit_double_pages.py # converts double-layout → single-page-per-sheet
│       ├── build_final_config.py
│       ├── split_pdfs.py
│       └── convert_to_markdown.py
├── data/
│   ├── ai/                        # AI intermediate data
│   │   ├── contents_config.json   # contents pages + offsets per PDF
│   │   ├── parsed_contents.json   # generated: country names + true pages
│   │   ├── contents_images/       # generated: PNG images of contents pages
│   │   └── contents_json/         # Claude's extracted country/page data
│   └── hrw/                       # HRW intermediate data
│       ├── contents_config.json   # contents pages + offsets/layout per PDF
│       ├── parsed_contents.json   # generated: country names + true pages
│       ├── contents_images/       # generated: PNG images of contents pages
│       └── contents_json/         # Claude's extracted country/page data
└── output/
    ├── ai/                        # generated: per-country PDFs
    │   └── <year>/
    │       ├── <country>.pdf
    │       └── ...
    ├── hrw/                       # generated: per-country PDFs
    └── hrw_unsplit/               # generated: double-layout PDFs converted to single
```
