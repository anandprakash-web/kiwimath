#!/usr/bin/env python3
"""
Kiwi's Grand Math Adventure — Level 2 (Grades 3-4).
An ORIGINAL kid-friendly math book: Socratic build-up, Bloom's-laddered practice,
hand-drawn SVG figures, worked examples, back-exercises. Organised by the Kiwimath
L2 taxonomy. Chapters live in l2_chNN_*.py modules; run this to render the book.
Reads like a real book (Euclid's-Garden style): title page -> full index you jump
from -> open flowing chapters with prev/next + Contents, A-/A+ font sizing, night.
"""
import os
from l2_helpers import esc, fit_svgs

_dir = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(_dir, "../../content-books/l2-mathbook"))

CHAPTERS = []
def chapter(part, num, title, taxonomy, body):
    CHAPTERS.append({"part": part, "num": num, "title": title, "tax": taxonomy, "body": body})

# register chapters (each module exposes build(chapter)); tolerant so one bad
# module can't sink the whole build — failures are printed.
import importlib
_CH_MODULES = [
    "l2_ch01_bignumbers", "l2_ch02_compare_ops", "l2_ch03_number_families", "l2_ch04_divisibility",
    "l2_ch05_fractions", "l2_ch06_fraction_ops", "l2_ch07_decimals", "l2_ch08_conversions",
    "l2_ch09_patterns", "l2_ch10_algebra", "l2_ch11_perimeter", "l2_ch12_area",
    "l2_ch13_shapes", "l2_ch14_symmetry", "l2_ch15_counting", "l2_ch16_probability",
    "l2_ch17_cryptarithms", "l2_ch18_venn", "l2_ch19_logic", "l2_ch20_data",
    "l2_ch21_kangaroo_tricks", "l2_ch22_kangaroo_set",
]
for _m in _CH_MODULES:
    try:
        importlib.import_module(_m).build(chapter)
    except Exception as _e:
        print(f"[SKIP {_m}] {type(_e).__name__}: {_e}")

OUTLINE = [
    ("Part 1 · Big Numbers", ["Place Value & Reading Big Numbers", "Comparing, Ordering & Smart Operations",
                              "Number Families — Factors, Multiples & Primes", "Divisibility Magic Tricks"]),
    ("Part 2 · Fair Shares", ["Fractions — Parts of a Whole", "Comparing & Adding Fractions",
                              "Decimals — Another Way to Share", "Useful Conversions"]),
    ("Part 3 · Rule Finders & Balance the Scale", ["Patterns, Analogies & Classification", "Letters for Numbers (Algebra)"]),
    ("Part 4 · Measure Masters & Turn & Flip", ["Perimeter", "Area", "2D & 3D Shapes & Nets", "Symmetry"]),
    ("Part 5 · Brain Benders", ["Counting & Combinations", "Probability", "Cryptarithms & Magic Squares",
                                "Venn Diagrams", "Logic: Relations, Codes, Clocks & Folding"]),
    ("Part 6 · Data Detectives", ["Bar Charts, Pictographs & Circle Graphs"]),
    ("Part 7 · 🦘 Kangaroo Corner", ["Kangaroo Thinking Tricks", "Kangaroo Challenge Set (3·4·5 points)"]),
]

# Core / Stretch / Olympiad track per chapter — so the difficulty reads as
# intentional (core G3-4 curriculum vs enrichment vs olympiad/Kangaroo).
TRACK = {1: "Core", 2: "Core", 3: "Stretch", 4: "Stretch", 5: "Core", 6: "Core",
         7: "Core", 8: "Core", 9: "Core", 10: "Stretch", 11: "Core", 12: "Core",
         13: "Core", 14: "Core", 15: "Stretch", 16: "Stretch", 17: "Olympiad",
         18: "Olympiad", 19: "Stretch", 20: "Core", 21: "Olympiad", 22: "Olympiad"}
_TRK_CLS = {"Core": "trk-core", "Stretch": "trk-stretch", "Olympiad": "trk-oly"}
def _badge(n):
    t = TRACK.get(n, "Core"); return f'<span class="trk {_TRK_CLS[t]}">{t}</span>'


def render():
    by_num = {c["num"]: c for c in CHAPTERS}
    part_of = {}
    # full clean INDEX, grouped by part — every chapter a tappable line
    nav, cn = [], 0
    for part, chs in OUTLINE:
        nav.append(f'<div class="tp">{esc(part)}</div>')
        for t in chs:
            cn += 1
            c = by_num.get(cn)
            part_of[cn] = part
            tax = f'<span class="tx">{esc(c["tax"])}</span>' if c else ""
            if c:
                nav.append(f'<a class="ix" href="#ch{cn}"><span class="num">{cn}</span>'
                           f'<span class="ti">{esc(t)}{tax}</span>{_badge(cn)}</a>')
            else:
                nav.append(f'<span class="ix soon"><span class="num">{cn}</span>'
                           f'<span class="ti">{esc(t)}<span class="badge">soon</span></span></span>')
    # open flowing chapter sections with prev/next + Contents
    secs = []
    for c in sorted(CHAPTERS, key=lambda c: c["num"]):
        n = c["num"]
        kick = esc(part_of.get(n, "")) + f" · Chapter {n}"
        prev = by_num.get(n - 1); nxt = by_num.get(n + 1)
        pa = (f'<a href="#ch{n-1}">‹ {esc(prev["title"])}</a>' if prev else '<span></span>')
        na = (f'<a href="#ch{n+1}">{esc(nxt["title"])} ›</a>' if nxt else '<span></span>')
        secs.append(
            f'<section class="chap" id="ch{n}">'
            f'<div class="chead"><span class="cnum">{n}</span>'
            f'<div class="ctt"><span class="kick">{kick}</span><h1>{esc(c["title"])}</h1></div></div>'
            f'<div class="ctax">{esc(c["tax"])} {_badge(n)}</div>'
            f'{c["body"]}'
            f'<nav class="chnav">{pa}<a class="contents" href="#index">↑ Contents</a>{na}</nav>'
            f'</section>')
    doc = TEMPLATE.replace("{{NAV}}", "".join(nav)).replace("{{SECS}}", "".join(secs))
    os.makedirs(OUT, exist_ok=True)
    p = f"{OUT}/l2-mathbook.html"
    open(p, "w").write(fit_svgs(doc))
    tot = sum(len(x[1]) for x in OUTLINE)
    print(f"wrote {p}  ({os.path.getsize(p)/1e6:.2f} MB, {len(CHAPTERS)}/{tot} chapters)")


TEMPLATE = r"""<!doctype html><!-- l2-mathbook fmt:bookstyle --><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Kiwi's Grand Math Adventure · Level 2</title>
<style>
:root{--o:#FF6F00;--od:#E65100;--bg:#FFFCF6;--ink:#2b2622;--mut:#8c8377;--card:#fff;--line:#00000010;--sky:#3B9CE6;--grass:#39A85B;--berry:#E0556E;--gold:#E8A33D;--fscale:1}
body.night{--bg:#16140f;--ink:#ece6da;--mut:#9a9182;--card:#1f1c16;--line:#ffffff14}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:calc(17px * var(--fscale))/1.62 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif}
a{-webkit-tap-highlight-color:transparent}
/* top bar with font sizing + night */
.bar{position:sticky;top:0;z-index:50;display:flex;align-items:center;gap:8px;padding:9px 14px;background:var(--bg);border-bottom:1px solid var(--line)}
.bar .home{flex:1;font-weight:800;color:var(--od);text-decoration:none;font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar button{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:5px 11px;font-weight:800;color:var(--ink);cursor:pointer;font-size:14px;line-height:1}
.bar button:active{transform:scale(.95)}
.wrap{max-width:760px;margin:0 auto;padding:0 16px 90px}
/* title page */
.cover{margin:0 -16px 6px;padding:52px 24px 44px;text-align:center;color:#fff;border-radius:0 0 28px 28px;background:radial-gradient(120% 90% at 50% 0%,#FF8A2B 0%,#FF6F00 45%,#E1571A 100%)}
.cover .mascot{font-size:76px;line-height:1}
.cover h1{font-family:Georgia,'Times New Roman',serif;font-size:40px;margin:8px 0 0;font-weight:800;letter-spacing:.5px}
.cover .sub{max-width:440px;margin:12px auto 0;font-size:15px;opacity:.95;font-style:italic}
.cover .lv{display:inline-block;margin-top:16px;border:1.5px solid #ffffffaa;border-radius:999px;padding:5px 18px;font-weight:800;letter-spacing:3px;font-size:13px}
.cover .by{margin-top:14px;font-size:13px;opacity:.9}
.cover .brand{margin-top:6px;font-size:11px;font-weight:800;letter-spacing:3px;opacity:.8}
/* index */
.index{margin:24px 0 8px}
.index h2{font-family:Georgia,serif;color:var(--od);font-size:23px;text-align:center;margin:0}
.index .lead{text-align:center;color:var(--mut);font-size:13px;margin:2px 0 8px}
.tp{font-weight:800;font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:var(--o);margin:20px 4px 6px}
.ix{display:flex;align-items:center;gap:12px;text-decoration:none;color:var(--ink);padding:11px 13px;border:1px solid var(--line);border-radius:12px;margin:7px 0;background:var(--card)}
.ix:active{background:#FF6F0010}
.ix .num{flex:none;width:30px;height:30px;border-radius:9px;background:#FF6F0014;color:var(--od);display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800}
.ix .ti{flex:1;font-weight:700;line-height:1.25}
.ix .tx{display:block;font-size:12px;font-weight:600;color:var(--mut);margin-top:1px}
.ix.soon{opacity:.55;border-style:dashed} .ix .badge{font-size:11px;font-weight:800;color:var(--mut);margin-left:6px}
/* chapter sections (open, flowing) */
.chap{scroll-margin-top:56px;padding-top:10px;margin-top:30px;border-top:2px solid var(--line)}
.chap:first-of-type{border-top:none;margin-top:14px}
.chead{display:flex;align-items:center;gap:13px}
.chead .cnum{flex:none;width:42px;height:42px;border-radius:13px;background:var(--o);color:#fff;display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:800}
.chead .kick{display:block;font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--mut);font-weight:800;margin-bottom:1px}
.chead h1{font-family:Georgia,'Times New Roman',serif;color:var(--od);font-size:27px;line-height:1.13;margin:0}
.ctax{color:var(--mut);font-size:13px;font-weight:700;margin:8px 0 2px 55px}
.chnav{display:flex;align-items:stretch;gap:8px;margin:30px 0 0;padding-top:14px;border-top:1px solid var(--line);font-size:13px;font-weight:700}
.chnav a{flex:1;color:var(--od);text-decoration:none;border:1px solid var(--line);border-radius:10px;padding:9px 11px;display:flex;align-items:center}
.chnav a[href$="#index"]{flex:none;border-color:var(--o);background:#FF6F000d;justify-content:center}
.chnav a:last-child{justify-content:flex-end;text-align:right}
.chnav span{flex:1}
/* ---- content blocks (kept from L2: warm colors, figures, pedagogy) ---- */
.ch-h{color:var(--od);font-size:1.16em;margin:24px 0 6px}
p{margin:11px 0}
.kiwi{display:flex;gap:11px;align-items:flex-start;background:#FFF4E6;border:1px solid #FFE2BE;border-radius:13px;padding:12px 14px;margin:14px 0}
body.night .kiwi{background:#2a2113;border-color:#4a3a1c}
.kbird{font-size:24px;line-height:1.2;flex:none}
.bigq{background:linear-gradient(120deg,#3B9CE612,#39A85B12);border-left:4px solid var(--sky);border-radius:0 12px 12px 0;padding:12px 15px;margin:16px 0;font-size:1.02em;font-weight:600}
.bigq span{display:block;font-size:.66em;letter-spacing:2px;font-weight:800;color:var(--sky);margin-bottom:3px}
figure{margin:16px 0;text-align:center}
.fig{max-width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:12px;padding:8px}
body.night .fig{background:#15130f}
figcaption{font-size:.82em;color:var(--mut);margin-top:6px}
.pv{border-collapse:collapse;margin:14px auto;font-size:1em}
.pv th{background:#FF6F0012;color:var(--od);font-size:.74em;letter-spacing:.5px;padding:7px 16px;border:1px solid var(--line)}
.pv td{padding:8px 16px;border:1px solid var(--line);text-align:center}
.pv .big td{font-size:1.6em;font-weight:800;font-family:Georgia,serif}
.eg{background:#F4FAFF;border:1px solid #D4EAFB;border-radius:13px;padding:13px 15px;margin:16px 0}
body.night .eg{background:#0e1a24;border-color:#1d3346}
.eg-t{font-weight:800;color:#1769A8;margin-bottom:4px}
body.night .eg-t{color:#7FC2F0}
.steps{margin:8px 0 2px;padding-left:22px} .steps li{margin:5px 0}
.try{background:#F2FBF4;border:1px solid #CDEBD6;border-radius:13px;padding:12px 14px;margin:14px 0}
body.night .try{background:#0f1f15;border-color:#1f3b2a}
.try details,.pr-list details{margin-top:4px;display:inline-block}
.try summary,.pr-list summary{cursor:pointer;font-weight:700;color:var(--grass);font-size:.86em;list-style:none;display:inline}
.try summary::-webkit-details-marker,.pr-list summary::-webkit-details-marker{display:none}
.try summary::before,.pr-list summary::before{content:"▸ "}
.try details[open] summary::before,.pr-list details[open] summary::before{content:"▾ "}
.ans{color:var(--ink);font-weight:600}
.pr{margin:16px 0}
.pr-l{display:inline-block;font-size:.68em;font-weight:800;letter-spacing:1.5px;color:#fff;background:var(--gold);border-radius:999px;padding:3px 12px;margin-bottom:4px;text-transform:uppercase}
.pr-list{margin:4px 0;padding-left:24px} .pr-list>li{margin:9px 0}
.pr-list summary{color:var(--od)}
.chal{background:linear-gradient(120deg,#FFF3D6,#FFE7C2);border:1px solid #F3CE86;border-radius:13px;padding:13px 15px;margin:18px 0}
body.night .chal{background:#2a2010;border-color:#5a431a}
.chal-t{font-weight:800;color:#B5740B;margin-bottom:4px}
.trap{background:#FFF0EE;border:1px solid #F3B6AB;border-left:4px solid var(--berry);border-radius:0 12px 12px 0;padding:12px 15px;margin:16px 0}
body.night .trap{background:#2a1614;border-color:#5a2a24}
.trap-t{font-weight:800;color:#C0392B;margin-bottom:3px} body.night .trap-t{color:#ff9a8a}
.trk{display:inline-block;font-size:11px;font-weight:800;letter-spacing:.08em;border-radius:999px;padding:2px 10px;margin-left:9px;vertical-align:middle;text-transform:uppercase}
.trk-core{background:#E9F5EE;color:#2b7a4b} .trk-stretch{background:#FFF3D6;color:#B5740B} .trk-oly{background:#EDE7FB;color:#6A2C9E}
body.night .trk-core{background:#1c2a22;color:#5fc98c} body.night .trk-stretch{background:#2a2010;color:#e0b14e} body.night .trk-oly{background:#241836;color:#c79bd6}
.ix .trk{font-size:10px;padding:1px 8px;margin-left:auto}
.fab{position:fixed;right:16px;bottom:18px;height:46px;padding:0 18px;border-radius:24px;background:var(--o);color:#fff;display:flex;align-items:center;gap:7px;font-weight:800;box-shadow:0 4px 14px #0004;text-decoration:none;z-index:40}
b,strong{color:var(--od)} body.night b,body.night strong{color:#FFB066}
em{font-style:normal;background:#FFF0A8;border-radius:4px;padding:0 4px} body.night em{background:#4a4220}
</style></head><body>
<div class="bar"><a class="home" href="#index">🥝 Kiwi's Grand Math Adventure</a>
<button onclick="bump(-1)" aria-label="Smaller text">A−</button>
<button onclick="bump(1)" aria-label="Larger text">A+</button>
<button onclick="night()" aria-label="Day or night">☾</button></div>
<div class="wrap">
<header class="cover"><div class="mascot">🥝</div><h1>Kiwi's Grand<br>Math Adventure</h1>
<div class="sub">A journey through numbers, shapes, puzzles and patterns — from your first counting all the way to the Kangaroo.</div>
<div class="lv">LEVEL 2 · GRADES 3–4</div>
<div class="by">with Kiwi, your guide</div>
<div class="brand">VOS LIBRARY</div></header>
<nav class="index" id="index"><h2>Contents</h2><div class="lead">Tap any chapter to jump straight in.</div>{{NAV}}</nav>
{{SECS}}
<p style="text-align:center;color:var(--mut);font-size:12px;margin-top:46px">Vedantu Olympiad School · VOS Library · Made with care for young mathematicians</p>
</div>
<a class="fab" href="#index">↑ Contents</a>
<script>
var _fs=1;function bump(d){_fs=Math.max(.8,Math.min(1.7,+(_fs+0.1*d).toFixed(2)));document.documentElement.style.setProperty('--fscale',_fs);}
function night(){document.body.classList.toggle('night');}
</script>
</body></html>"""

if __name__ == "__main__":
    render()
