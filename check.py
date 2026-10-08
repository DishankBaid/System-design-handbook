#!/usr/bin/env python3
"""Lint content/ chapters. Usage: python3 check.py [--run-snippets] [slug ...]

Fails (exit 1) on: missing chapters, broken internal links, h2/h3 without id, duplicate ids,
em/en dashes, raw tags inside code blocks, and (with --run-snippets) Python snippets that error.
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from build import CONTENT, PAGES

SLUGS = {slug for _, slug, _, _ in PAGES}


def check(slug: str, run_snippets: bool) -> list[str]:
    path = CONTENT / f"{slug}.html"
    if not path.exists():
        return ["missing"]
    body = path.read_text()
    errs = []
    for ch, name in (("—", "em dash"), ("–", "en dash")):
        if ch in body:
            errs.append(f"{body.count(ch)} {name}(es)")
    for h in re.findall(r"<h[23](?![^>]*\bid=)[^>]*>(.*?)</h[23]>", body):
        errs.append(f"heading without id: {h[:50]}")
    ids = re.findall(r'\bid="([^"]+)"', body)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errs.append(f"duplicate id: {dup}")
    for href in re.findall(r'href="([^"#:]+?)\.html(?:#[^"]*)?"', body):
        if href not in SLUGS and href != "index":
            errs.append(f"broken link: {href}.html")
    for lang, code in re.findall(r'<pre><code class="language-(\w+)">([\s\S]*?)</code></pre>', body):
        if re.search(r"<[a-zA-Z/]", code):
            errs.append(f"unescaped tag in {lang} code block")
        if run_snippets and lang == "python":
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(html.unescape(code))
            r = subprocess.run([sys.executable, "-I", f.name], capture_output=True, text=True, timeout=120)
            if r.returncode:
                errs.append("python snippet failed: " + (r.stderr.strip().splitlines() or ["?"])[-1])
    if body.count("<figure") < 3:
        errs.append(f"only {body.count('<figure')} figure(s)")
    return errs


def main():
    run = "--run-snippets" in sys.argv
    slugs = [a for a in sys.argv[1:] if not a.startswith("--")] or [s for _, s, _, _ in PAGES]
    bad = 0
    for slug in slugs:
        errs = check(slug, run)
        words = len(re.sub(r"<(svg|pre)[\s\S]*?</\1>|<[^>]+>", " ", (CONTENT / f"{slug}.html").read_text()).split()) \
            if (CONTENT / f"{slug}.html").exists() else 0
        status = "ok " if not errs else "ERR"
        bad += bool(errs)
        print(f"{status} {slug:28} {words:>6} words  {'; '.join(errs)}")
    print(f"\n{len(slugs) - bad}/{len(slugs)} chapters pass")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
