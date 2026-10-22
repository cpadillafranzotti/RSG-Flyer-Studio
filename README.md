# RSG Flyer Studio

A reproducible system for the yearly **"Leadership team" flyers** of the ISCB Student Council Regional Student Groups (RSGs).

Every year each active RSG announces its new leadership with a flyer. Instead of redesigning it by hand every time, the committee keeps **one spreadsheet** (year, RSG, role, name, photo) and the flyers are generated from it instantly, in a consistent ISCB-SC visual identity, for every RSG at once.

There are two ways to use it:

| | **Flyer Studio (web app)** | **Batch script** |
|---|---|---|
| For | RSG leads, anyone on the committee | maintainers, bulk / historical renders |
| Needs | a browser | Python, or a GitHub Actions run |
| Input | Google Sheets link, or an uploaded .xlsx / .csv | CSV files or Google Sheets links |
| Output | live preview, PNG per flyer, ZIP of all | PNGs + a gallery page |

Both use the same designs in `templates/`, so a design change applies everywhere.

---

## 1. Flyer Studio (web app)

`web/index.html` is a single static page, published automatically to GitHub Pages.

1. **Load the data**, choosing one of two options:
   - **Sheet link**: paste a Google Sheets link. The sheet must be shared as *Anyone with the link · Viewer* and contain the tabs `members` and `rsgs`.
   - **Upload table**: drop an Excel file (.xlsx with both tabs) or one or two .csv files. Copy-and-paste of the tabs also works.
2. **Pick** the year, the RSGs to include, the title, the design, the colour palette and the format.
3. **Review** the flyers, which update live as you change options.
4. **Download** each flyer as a PNG (2160 px, ready for social media) or all of them as a ZIP.

The page offers a **template (.xlsx)** with the right columns and example rows. Import it into Google Sheets (*File → Import → Replace spreadsheet*) to start the shared committee sheet.

Photos can be Google Drive links in the sheet (each photo shared as *Anyone with the link*) or image files dropped onto the page; dropped files are matched by file name. Members without a photo get their initials, so drafts can be made before photos arrive.

## 2. The spreadsheet

### `members`: one row per person per year

| year | rsg | order | role | name | photo |
|---|---|---|---|---|---|
| 2026 | nigeria | 1 | President | Ada Okonkwo-Bello | ada.jpg |
| 2026 | nigeria | 2 | Secretary | Tunde Adeyemi | https://drive.google.com/file/d/…/view |
| 2026 | nigeria | 3 | Faculty Advisor | Dr. Ngozi Eze | |

- **New year = new rows.** Nothing is redesigned; the generator defaults to the latest year in the sheet.
- `rsg`: a short lowercase id, matching the `rsgs` tab.
- `order`: position on the flyer (left to right, top to bottom).
- `photo`: a file name, an image URL or a Google Drive link. Leave it empty to show initials. Square photos of at least 600 px with the face centred work best; they're cropped to a circle automatically.
- Spanish headers are also accepted (`año`, `orden`, `rol`, `nombre`, `foto`).

### `rsgs`: one row per RSG, filled in once

| column | example | used for |
|---|---|---|
| rsg | `argentina` | id |
| display_name | `RSG-Argentina` | big title; an `RSG-` prefix is set in the accent colour |
| country | `Argentina` | text in the generated RSG badge |
| website | `rsg-argentina.iscbsc.org` | under the title |
| logo | `argentina.png` | the RSG's own logo (file, URL or Drive link). Empty = a generated round badge in the national flag colours |
| flag_colors | `#74acdf\|#ffffff\|#74acdf` | three colours separated by `\|`, for the generated badge |
| flag_layout | `horizontal` / `vertical` | stripe direction in the badge |
| accent | `#74acdf` | only used with the *RSG colour* palette |
| handle | `@iscbsc` | social handle in the footer |
| email | `rsg@iscbsc.org` | contact in the footer |

If the `rsgs` tab is missing, sensible defaults are used.

## 3. Designs, palettes and formats

**Designs** (`templates/themes/`):

| design | look |
|---|---|
| `hex` | dark navy with a hexagon mesh and outline type, closest to the original 2025 flyers |
| `clean` | light, editorial, coloured photo rings |
| `bold` | solid brand-colour field with large type |

**Colour palettes** (`templates/palettes.json`). By default every RSG uses the same institutional palette, taken from the ISCB-SC logo, so the flyers read as one series:

| palette | colours |
|---|---|
| `sc-teal` *(default)* | Student Council teal, as in the 2025 flyers |
| `sc-ocean` | deep SC logo blue `#006C90` |
| `sc-night` | night blue with the SC logo sky blue `#B4E4FC` |
| `iscb-red` | ISCB helix red `#E41824` |
| `rsg` | each RSG's own `accent` colour, as an opt-in |

National flag colours only appear inside the RSG badge.

**Formats:**

| format | size | use |
|---|---|---|
| `square` | 1080 × 1080 | Instagram / LinkedIn post |
| `portrait` | 1080 × 1350 | Instagram 4:5 post |
| `story` | 1080 × 1920 | Stories |

The layout adapts automatically to teams of 1 to 8 people (see `data/examples/stress_test_members.csv`).

**Footer logos.** Every flyer carries the ISCB-SC and ISCB logos on a dark footer band (`assets/logos/footer_1_iscbsc.png`, `footer_2_iscb.png`). The current files were cropped from a 2025 flyer and are dark-background versions at medium resolution. **Replace them with the official high-resolution files** (same names) and run `python web/build.py`. Files are shown in alphabetical order.

## 4. Publishing the web app (GitHub Pages)

1. Push this repository to GitHub, under a personal account or the ISCB-SC organisation.
2. **Settings → Pages → Source: GitHub Actions.**
3. **Actions → "Publish Flyer Studio (web app)" → Run workflow.** It also runs automatically whenever `web/` or `templates/` change.
4. The app is live at `https://<owner>.github.io/<repo>/`.

## 5. Batch script

```bash
python generate.py                                   # latest year, all RSGs, all designs, square
python generate.py --year 2027 --rsg argentina,nigeria --format all
python generate.py --theme hex --palette sc-ocean
python generate.py --year all                        # re-render the whole history
python generate.py \
  --members "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0" \
  --rsgs    "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=123456789"
```

Output goes to `output/<year>/<rsg>_<year>_<design>_<format>.png`, plus a browsable `output/index.html`.
`--scale 2` (the default) renders at double resolution, and `--keep-html` keeps the intermediate HTML for debugging.

**Without installing anything:** the workflow `.github/workflows/flyers.yml` runs the script on GitHub.
Set the repository variables `MEMBERS_SHEET_URL` and `RSGS_SHEET_URL` (*Settings → Secrets and variables → Actions → Variables*), then **Actions → Generate RSG flyers → Run workflow**. The PNGs are attached to the run as an artifact.

**Local setup:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python generate.py
```

## 6. Adding a new design

1. Copy `templates/themes/hex.css` to `templates/themes/<name>.css` and rename the `.theme-hex` selectors to `.theme-<name>`.
2. Optionally add a background decoration in `templates/themes/<name>_bg.svg`.
3. Run `python web/build.py`. The new design appears in both the web app and the script.

The shared layout lives in `templates/base.css`, so a design only sets colour, type and decoration.

## Repository layout

```
web/app.html          web app source        → python web/build.py → web/index.html
web/fonts/            bundled Lexend + Poppins (no external font requests)
templates/            flyer layout, designs, palettes (shared by app and script)
assets/logos/         footer logos (footer_*.png) and RSG logos
assets/photos/        member photos for the script
data/                 example members.csv / rsgs.csv
generate.py           batch renderer (Playwright + Chromium)
.github/workflows/    pages.yml (publish app) · flyers.yml (batch render)
```

Fonts: Lexend and Poppins, SIL Open Font License.
