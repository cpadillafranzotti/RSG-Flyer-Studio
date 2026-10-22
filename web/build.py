#!/usr/bin/env python3
"""
Builds web/index.html: a single self-contained page (fonts, flyer themes and
backgrounds inlined) from web/app.html + templates/. Run after editing a theme:

    python web/build.py
"""
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
TPL = ROOT / "templates"
FONTS = WEB / "fonts"

# latin + latin-ext unicode ranges (from Google Fonts / Fontsource)
RANGES = {
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
    "latin-ext": "U+0100-02AF,U+0304,U+0308,U+0329,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF",
}


def font_css() -> str:
    out = []
    for f in sorted(FONTS.glob("*.woff2")):
        # e.g. lexend-latin-ext-300-normal.woff2
        m = re.match(r"(\w+)-(latin-ext|latin)-(\d+)-(normal|italic)\.woff2", f.name)
        if not m:
            continue
        fam, subset, weight, style = m.groups()
        b64 = base64.b64encode(f.read_bytes()).decode()
        out.append(
            f"@font-face{{font-family:'{fam.title()}';font-style:{style};font-weight:{weight};"
            f"font-display:block;src:url(data:font/woff2;base64,{b64}) format('woff2');"
            f"unicode-range:{RANGES[subset]}}}"
        )
    return "\n".join(out)


def flyer_css() -> str:
    base = (TPL / "base.css").read_text()
    # page-level rules from the print template don't apply inside the app
    base = re.sub(r"html, body \{[^}]*\}\n", "", base)
    base = base.replace("body { font-family", ".fl { font-family")
    base = base.replace("* { box-sizing", ".fl, .fl * { box-sizing")
    base = base.replace("\nfigcaption {", "\n.fl figcaption {")
    themes = "\n".join(p.read_text() for p in sorted((TPL / "themes").glob("*.css")))
    css = base + "\n" + themes
    # scope everything under .fl so the flyer CSS can't leak into the app UI
    return css


def backgrounds() -> dict:
    return {p.stem.replace("_bg", ""): p.read_text() for p in sorted((TPL / "themes").glob("*_bg.svg"))}


def main():
    src = (WEB / "app.html").read_text()
    themes = [p.stem for p in sorted((TPL / "themes").glob("*.css"))]
    html = (src
            .replace("/*__FONTS__*/", font_css())
            .replace("/*__FLYER_CSS__*/", flyer_css())
            .replace("/*__BGS__*/{}", json.dumps(backgrounds()))
            .replace("/*__THEMES__*/[]", json.dumps(themes)))
    (WEB / "index.html").write_text(html)
    print(f"web/index.html  {len(html)/1024:.0f} KB  themes: {', '.join(themes)}")


if __name__ == "__main__":
    main()
