#!/usr/bin/env python3
"""
RSG leadership flyer generator.

Reads two tables (local CSV files or Google Sheets tabs):
  members  -> year, rsg, order, role, name, photo
  rsgs     -> rsg, display_name, country, website, logo, flag_colors, flag_layout, accent, handle, email
and renders one PNG per (year, RSG, theme, format).

Examples
  python generate.py                                  # latest year, all RSGs, all themes, square
  python generate.py --year 2026 --rsg argentina      # one RSG
  python generate.py --theme hex --format square,portrait,story
  python generate.py --members "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0" \
                     --rsgs    "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=123456"
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
THEMES = sorted(p.stem for p in (TEMPLATES / "themes").glob("*.css"))
FORMATS = {
    "square":   (1080, 1080),   # Instagram / LinkedIn post
    "portrait": (1080, 1350),   # Instagram 4:5
    "story":    (1080, 1920),   # Stories / Reels cover
}
TITLES = ("dr.", "dra.", "prof.", "profa.", "mr.", "ms.", "mrs.", "lic.", "ing.")


# ---------------------------------------------------------------- data loading
def sheet_to_csv_url(src: str) -> str:
    """Turn a normal Google Sheets link into its CSV export link (keeps the gid/tab)."""
    m = re.search(r"docs\.google\.com/spreadsheets/d/([\w-]+)", src)
    if not m or "format=csv" in src or "output=csv" in src:
        return src
    gid = re.search(r"[#&?]gid=(\d+)", src)
    return (f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
            + (f"&gid={gid.group(1)}" if gid else ""))


def read_table(src: str) -> list[dict]:
    if src.startswith(("http://", "https://")):
        url = sheet_to_csv_url(src)
        with urllib.request.urlopen(url, timeout=30) as r:
            text = r.read().decode("utf-8-sig")
    else:
        text = Path(src).read_text(encoding="utf-8-sig")
    rows = csv.DictReader(io.StringIO(text))
    # normalise headers: "Photo URL" -> "photo_url"
    out = []
    for row in rows:
        clean = {re.sub(r"\W+", "_", (k or "").strip().lower()).strip("_"): (v or "").strip()
                 for k, v in row.items()}
        if any(clean.values()):
            out.append(clean)
    return out


def resolve_image(value: str, subdir: str) -> str | None:
    """Local file (relative to assets/<subdir>/ or repo), http URL, or Google Drive share link."""
    if not value:
        return None
    drive = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([\w-]+)", value)
    if drive:
        return f"https://drive.google.com/thumbnail?id={drive.group(1)}&sz=w1200"
    if value.startswith(("http://", "https://", "data:")):
        return value
    for base in (ASSETS / subdir, ASSETS, ROOT):
        p = (base / value).resolve()
        if p.is_file():
            return p.as_uri()
    print(f"  ! image not found: {value} (looked in assets/{subdir}/)", file=sys.stderr)
    return None


def initials(name: str) -> str:
    words = [w for w in name.split() if w.lower() not in TITLES]
    if not words:
        return "?"
    return (words[0][0] + (words[-1][0] if len(words) > 1 else "")).upper()


def load_rsgs(rows: list[dict]) -> dict[str, dict]:
    rsgs = {}
    for r in rows:
        slug = r.get("rsg", "").lower()
        if not slug:
            continue
        flag = [c.strip() for c in r.get("flag_colors", "").split("|") if c.strip()] or ["#22c3d6"]
        while len(flag) < 3:
            flag.append(flag[-1])
        rsgs[slug] = {
            "slug": slug,
            "display_name": r.get("display_name") or f"RSG-{slug.title()}",
            "country": r.get("country") or slug.title(),
            "website": r.get("website", ""),
            "logo_src": resolve_image(r.get("logo", ""), "logos"),
            "flag": flag[:3],
            "flag_layout": "horizontal" if r.get("flag_layout", "").lower().startswith("h") else "vertical",
            "accent": r.get("accent") or "#22c3d6",
            "handle": r.get("handle", ""),
            "email": r.get("email", ""),
        }
    return rsgs


# ---------------------------------------------------------------- layout
def layout_for(n: int, fmt: str) -> dict:
    """Photo diameter and columns so 1–8 members always fit nicely."""
    if fmt == "story":
        if n == 1:   return {"cols": 1, "photo": 420}
        if n <= 4:   return {"cols": 2, "photo": 300}
        if n <= 6:   return {"cols": 3, "photo": 245}
        return {"cols": 3, "photo": 175}
    # usable width is 936px (1080 - 2*72); gap = 0.3 * photo
    if n <= 2:
        cols, photo = max(n, 1), 300
    elif n == 3:
        cols, photo = 3, 255
    elif n == 4:
        cols, photo = 4, 180
    elif n <= 6:
        cols, photo = 3, 160
    else:
        cols, photo = 4, 145
    if fmt == "portrait" and n > 4:
        photo += 25
    return {"cols": cols, "photo": photo}


# ---------------------------------------------------------------- rendering
def build_pages(members, rsgs, years, only_rsgs, themes, formats, title, footer_logos):
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    tpl = env.get_template("flyer.html")

    groups = defaultdict(list)
    for m in members:
        groups[(m.get("year", ""), m.get("rsg", "").lower())].append(m)

    pages = []
    for (year, slug), rows in sorted(groups.items()):
        if years and year not in years:
            continue
        if only_rsgs and slug not in only_rsgs:
            continue
        if slug not in rsgs:
            print(f"  ! '{slug}' is in members but not in the rsgs table — using defaults", file=sys.stderr)
            rsgs[slug] = load_rsgs([{"rsg": slug}])[slug]
        rows.sort(key=lambda r: (int(r["order"]) if r.get("order", "").isdigit() else 999))
        team = [{
            "role": r.get("role", ""),
            "name": r.get("name", ""),
            "initials": initials(r.get("name", "")),
            "photo_src": resolve_image(r.get("photo", ""), f"photos/{slug}") or resolve_image(r.get("photo", ""), "photos"),
        } for r in rows if r.get("name")]

        for theme in themes:
            for fmt in formats:
                w, h = FORMATS[fmt]
                page_html = tpl.render(
                    year=year, title=title, rsg=rsgs[slug], members=team, theme=theme,
                    fmt={"name": fmt, "w": w, "h": h}, layout=layout_for(len(team), fmt),
                    footer_logos=footer_logos,
                )
                pages.append({"year": year, "rsg": slug, "theme": theme, "format": fmt,
                              "w": w, "h": h, "html": page_html,
                              "name": rsgs[slug]["display_name"], "count": len(team)})
    return pages


def render_png(pages, outdir: Path, scale: float, keep_html: bool):
    from playwright.sync_api import sync_playwright

    html_dir = outdir / "_html"
    html_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for pg in pages:
            stem = f"{pg['rsg']}_{pg['year']}_{pg['theme']}_{pg['format']}"
            hfile = html_dir / f"{stem}.html"
            hfile.write_text(pg["html"], encoding="utf-8")
            png = outdir / pg["year"] / f"{stem}.png"
            png.parent.mkdir(parents=True, exist_ok=True)

            page = browser.new_page(viewport={"width": pg["w"], "height": pg["h"]}, device_scale_factor=scale)
            page.goto(hfile.as_uri(), wait_until="networkidle", timeout=60000)
            page.evaluate("document.fonts.ready")
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": pg["w"], "height": pg["h"]})
            page.close()
            pg["png"] = png.relative_to(outdir).as_posix()
            print(f"  ✓ {pg['png']}")
        browser.close()
    if not keep_html:
        for f in html_dir.glob("*.html"):
            f.unlink()
        html_dir.rmdir()


def write_gallery(pages, outdir: Path):
    cards = "\n".join(
        f'<figure><a href="{p["png"]}" download><img src="{p["png"]}" loading="lazy"></a>'
        f'<figcaption><b>{html.escape(p["name"])}</b> {p["year"]} · {p["theme"]} · {p["format"]}</figcaption></figure>'
        for p in pages)
    (outdir / "index.html").write_text(f"""<!doctype html><meta charset="utf-8">
<title>RSG flyers</title>
<style>body{{font-family:system-ui,sans-serif;background:#0d1117;color:#e6edf3;margin:24px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}}
img{{width:100%;border-radius:8px;display:block}}figcaption{{font-size:13px;margin-top:6px;opacity:.8}}</style>
<h1>RSG leadership flyers</h1><p>Click a flyer to download it.</p><main>{cards}</main>""", encoding="utf-8")
    (outdir / "manifest.json").write_text(json.dumps(
        [{k: v for k, v in p.items() if k != "html"} for p in pages], indent=2), encoding="utf-8")


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--members", default=os.getenv("MEMBERS_SRC", "data/members.csv"),
                    help="CSV path, CSV URL or Google Sheets tab link (env MEMBERS_SRC)")
    ap.add_argument("--rsgs", default=os.getenv("RSGS_SRC", "data/rsgs.csv"),
                    help="CSV path, CSV URL or Google Sheets tab link (env RSGS_SRC)")
    ap.add_argument("--year", help="Year(s) to render, comma separated. Default: latest year in the sheet. 'all' for every year")
    ap.add_argument("--rsg", help="RSG slug(s), comma separated. Default: all")
    ap.add_argument("--theme", default="all", help=f"Theme(s): {', '.join(THEMES)} or all")
    ap.add_argument("--format", default="square", help=f"Format(s): {', '.join(FORMATS)} or all")
    ap.add_argument("--title", default="Leadership team")
    ap.add_argument("--scale", type=float, default=2, help="Pixel density (2 = 2160px wide, crisp on phones)")
    ap.add_argument("--out", default="output")
    ap.add_argument("--keep-html", action="store_true", help="Keep the intermediate HTML for debugging")
    a = ap.parse_args()

    os.chdir(ROOT)
    members = read_table(a.members)
    rsgs = load_rsgs(read_table(a.rsgs))
    all_years = sorted({m.get("year", "") for m in members if m.get("year")})
    if not all_years:
        sys.exit("No rows with a 'year' in the members table.")
    years = set(all_years) if a.year == "all" else set(a.year.split(",")) if a.year else {all_years[-1]}
    themes = THEMES if a.theme == "all" else a.theme.split(",")
    formats = list(FORMATS) if a.format == "all" else a.format.split(",")
    for t in themes:
        if t not in THEMES: sys.exit(f"Unknown theme '{t}'. Available: {', '.join(THEMES)}")
    for f in formats:
        if f not in FORMATS: sys.exit(f"Unknown format '{f}'. Available: {', '.join(FORMATS)}")

    footer_logos = [p.resolve().as_uri() for p in sorted((ASSETS / "logos").glob("footer_*.*"))]
    only = set(a.rsg.lower().split(",")) if a.rsg else None

    pages = build_pages(members, rsgs, years, only, themes, formats, a.title, footer_logos)
    if not pages:
        sys.exit("Nothing to render — check --year / --rsg filters.")
    print(f"Rendering {len(pages)} flyer(s) for {', '.join(sorted(years))} …")
    outdir = (ROOT / a.out).resolve()
    render_png(pages, outdir, a.scale, a.keep_html)
    write_gallery(pages, outdir)
    print(f"Done → {outdir}/index.html")


if __name__ == "__main__":
    main()
