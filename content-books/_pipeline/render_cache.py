#!/usr/bin/env python3
"""Render every slide of the 13 Number Sense worksheets to a webp cache, so the
assembler can build the book without re-rendering. Idempotent (skips existing)."""
import fitz, io, os, glob, json
from PIL import Image

_dir = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Downloads/VEL Wavebook PDFs/Number Sense and Operations")
CACHE = os.path.abspath(os.path.join(_dir, "../../outputs/nsbuild/cache"))
SCALE, Q = 1.3, 78

# chapter order + clean titles (filename -> title)
CHAPTERS = [
 ("Counting & Number Recognition (1–10).pdf", "Counting & Number Recognition (1–10)"),
 ("Number Comparison (1–10).pdf", "Number Comparison (1–10)"),
 ("Number Comparison & Sequencing (1–20).pdf", "Number Comparison & Sequencing (1–20)"),
 ("Skip Count Fun Upto 20.pdf", "Skip Counting up to 20"),
 ("Group & Count (Bundling of 10).pdf", "Group & Count — Bundling of 10"),
 ("Place Value (O-T).pdf", "Place Value — Ones & Tens"),
 ("Addition & Forward Sequencing Upto 10.pdf", "Addition & Forward Sequencing up to 10"),
 ("Subtraction & Backward Sequencing Upto 10.pdf", "Subtraction & Backward Sequencing up to 10"),
 ("Challenges on Addition & Subtraction Upto 10.pdf", "Challenges: Addition & Subtraction up to 10"),
 ("Addition Facts upto 20.pdf", "Addition Facts up to 20"),
 ("Addition and Subtraction up to 20 - Avinash.pdf", "Addition & Subtraction up to 20"),
 ("Challenges on Addition Upto 20 -  Avinash.pdf", "Challenges: Addition up to 20"),
 ("Challenges on Subtraction Upto 20 -  Avinash.pdf", "Challenges: Subtraction up to 20"),
]

def render(page, scale, clip=None):
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip)
    im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    b = io.BytesIO(); im.save(b, "WEBP", quality=Q, method=6)
    return b.getvalue()

if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    manifest = []
    done = 0
    for ci, (fn, title) in enumerate(CHAPTERS):
        d = fitz.open(f"{SRC}/{fn}")
        cdir = f"{CACHE}/c{ci:02d}"
        os.makedirs(cdir, exist_ok=True)
        pages = []
        for p in range(d.page_count):
            out = f"{cdir}/p{p:03d}.webp"
            if not os.path.exists(out) or os.path.getsize(out) == 0:
                open(out, "wb").write(render(d[p], SCALE))
            pages.append(os.path.getsize(out))
            done += 1
        manifest.append({"idx": ci, "file": fn, "title": title, "pages": d.page_count})
        print(f"c{ci:02d} {title[:44]:46} {d.page_count:3} pages  ({sum(pages)/1e6:.1f} MB)", flush=True)
    json.dump(manifest, open(f"{CACHE}/manifest.json", "w"))
    tot = sum(os.path.getsize(f) for f in glob.glob(f"{CACHE}/c*/p*.webp"))
    print(f"\nDONE — {done} slides cached, {tot/1e6:.1f} MB total", flush=True)
