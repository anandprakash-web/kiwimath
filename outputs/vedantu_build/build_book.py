#!/usr/bin/env python3
"""Build ONE faithful-render interactive book from a Vedantu pillar folder, with a
designed per-pillar book cover.
Usage: build_book.py <LEVEL> <PILLAR_FOLDER> "<Display Pillar>" <Tier> <out_id>
"""
import fitz, os, sys, io, base64, re, html, glob, math
from PIL import Image

_dir = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Downloads/Vedantu_Content")
OUT = os.path.abspath(os.path.join(_dir, "../../content-books"))
SCALE, Q = 2.0, 72

# ---- per-pillar palette (deep base, gold accent) ----
PAL = {
    "NumberTheory":     ("#1A1036", "#E8B84B"),
    "Algebra":          ("#0E2A3A", "#E8C24B"),
    "Geometry":         ("#0F2E22", "#EBC95C"),
    "Combinatorics":    ("#241033", "#E8B84B"),
    "Trigonometry":     ("#2B0E1E", "#E9B36A"),
    "BasicMathematics": ("#1B1C28", "#D9B66B"),
    "Arithmetic":       ("#2C1A0A", "#E8B84B"),
}

def _dark(hx, f=0.5):
    h = hx.lstrip("#"); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

def motif(folder, gold):
    """Gold line-art centerpiece (inner SVG markup, 220x220 viewBox)."""
    if folder == "NumberTheory":                       # prime-number lattice
        primes = {2,3,5,7,11,13,17,19,23}
        out, k = [], 1
        for r in range(5):
            for c in range(5):
                x, y = 30+c*40, 30+r*40
                fill = gold if k in primes else "none"
                out.append(f'<circle cx="{x}" cy="{y}" r="6.5" fill="{fill}" stroke="{gold}" stroke-width="1.4"/>')
                k += 1
        return "".join(out)
    if folder == "Algebra":                            # parabola + axes
        return (f'<line x1="18" y1="180" x2="202" y2="180" stroke="{gold}" stroke-width="1.4" opacity=".45"/>'
                f'<line x1="110" y1="18" x2="110" y2="202" stroke="{gold}" stroke-width="1.4" opacity=".45"/>'
                f'<path d="M34,42 Q110,250 186,42" fill="none" stroke="{gold}" stroke-width="3.2"/>'
                f'<circle cx="110" cy="168" r="5" fill="{gold}"/>')
    if folder == "Geometry":                           # circumcircle + inscribed triangle + concentric incircle
        cx, cy, R = 110, 110, 80
        pts = [(cx+R*math.cos(math.radians(a)), cy+R*math.sin(math.radians(a))) for a in (-90, 30, 150)]
        poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
        return (f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{gold}" stroke-width="1.8" opacity=".85"/>'
                f'<polygon points="{poly}" fill="none" stroke="{gold}" stroke-width="2.6"/>'
                # incircle of an equilateral triangle is concentric with radius R/2
                f'<circle cx="{cx}" cy="{cy}" r="{R/2:.0f}" fill="none" stroke="{gold}" stroke-width="1.6" opacity=".7"/>')
    if folder == "Combinatorics":                      # complete graph K5
        cx, cy, R = 110, 110, 76
        nd = [(cx+R*math.cos(math.radians(90+72*i)), cy-R*math.sin(math.radians(90+72*i))) for i in range(5)]
        eg = [f'<line x1="{nd[i][0]:.0f}" y1="{nd[i][1]:.0f}" x2="{nd[j][0]:.0f}" y2="{nd[j][1]:.0f}" stroke="{gold}" stroke-width="1.1" opacity=".5"/>'
              for i in range(5) for j in range(i+1, 5)]
        nc = [f'<circle cx="{x:.0f}" cy="{y:.0f}" r="8" fill="{gold}"/>' for x, y in nd]
        return "".join(eg) + "".join(nc)
    if folder == "Trigonometry":                       # unit circle (left) + radius angle, sine wave (right), no overlap
        cx, cy, R = 56, 110, 42
        px, py = cx + R*math.cos(math.radians(52)), cy - R*math.sin(math.radians(52))
        x0 = cx + R + 8
        wp = []
        for t in range(0, 102, 2):
            wp.append(f"{'M' if t == 0 else 'L'}{x0+t:.0f},{cy - R*math.sin(math.radians(t*5)):.0f}")
        return (f'<line x1="14" y1="{cy}" x2="206" y2="{cy}" stroke="{gold}" stroke-width="1" opacity=".3"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{gold}" stroke-width="1.6" opacity=".75"/>'
                f'<line x1="{cx}" y1="{cy}" x2="{px:.0f}" y2="{py:.0f}" stroke="{gold}" stroke-width="1.6"/>'
                f'<circle cx="{px:.0f}" cy="{py:.0f}" r="3.5" fill="{gold}"/>'
                f'<path d="{" ".join(wp)}" fill="none" stroke="{gold}" stroke-width="2.6"/>')
    if folder == "BasicMathematics":                   # (a+b)^2 square partition
        return (f'<rect x="35" y="35" width="150" height="150" fill="none" stroke="{gold}" stroke-width="1.8"/>'
                f'<line x1="125" y1="35" x2="125" y2="185" stroke="{gold}" stroke-width="1.3"/>'
                f'<line x1="35" y1="125" x2="185" y2="125" stroke="{gold}" stroke-width="1.3"/>'
                f'<rect x="35" y="35" width="90" height="90" fill="{gold}" opacity=".13"/>'
                f'<rect x="125" y="125" width="60" height="60" fill="{gold}" opacity=".13"/>')
    if folder == "Arithmetic":                         # ratio bars
        s = ""
        for y, w in [(60, 92), (100, 140), (140, 56)]:
            s += (f'<rect x="30" y="{y}" width="160" height="16" rx="8" fill="none" stroke="{gold}" stroke-width="1.4"/>'
                  f'<rect x="30" y="{y}" width="{w}" height="16" rx="8" fill="{gold}" opacity=".5"/>')
        return s
    return ""

def cover_block(folder, tier, disp, n):
    base, gold = PAL.get(folder, ("#24202C", "#E8B84B"))
    return f'''<div class="cover" style="background:linear-gradient(155deg,{base} 0%,{_dark(base,0.62)} 60%,{_dark(base,0.4)} 100%)">
  <div class="frame" style="border-color:{gold}55">
    <div class="tier" style="border-color:{gold};color:{gold}">{html.escape(tier)}</div>
    <svg class="motif" viewBox="0 0 220 220">{motif(folder, gold)}</svg>
    <h1 class="ctitle">{html.escape(disp)}</h1>
    <div class="crule" style="background:{gold}"></div>
    <div class="csub" style="color:{gold}">VEDANTU · OLYMPIAD MATH MASTERY</div>
    <div class="cmeta">{n} topics · worked solutions &amp; video</div>
    <div class="cbrand">VOS&nbsp;LIBRARY</div>
  </div>
</div>'''

def render_pages(pdf):
    out = []; d = fitz.open(pdf)
    for pg in d:
        pix = pg.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE))
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        b = io.BytesIO(); im.save(b, "WEBP", quality=Q, method=4)
        out.append((b.getvalue(), pg.get_text()))
    d.close(); return out

def split_idx(texts):
    for i, t in enumerate(texts):
        if re.search(r'\b(Answers?\s*Key|ANSWER\s*KEY|Solutions?\b|Video Solution)', t):
            return i
    return len(texts)

def vids(texts):
    s = " ".join(texts)
    return sorted(set(re.findall(r'https?://(?:www\.)?(?:youtu\.be/[\w-]+|youtube\.com/[^\s)]+)', s)))

def b64(wb): return "data:image/webp;base64," + base64.b64encode(wb).decode()
def esc(s): return html.escape(s)

def main():
    level, folder, disp, tier, out_id = sys.argv[1:6]
    pdfs = sorted(glob.glob(f"{SRC}/{level}/{folder}/*.pdf"))
    topics = []
    for f in pdfs:
        name = os.path.basename(f)[:-4].replace("_", " ")
        pages = render_pages(f)
        si = split_idx([t for _, t in pages])
        prob = [b64(wb) for wb, _ in pages[:si]] or [b64(pages[0][0])]
        soln = [b64(wb) for wb, _ in pages[si:]]
        topics.append((name, prob, soln, vids([t for _, t in pages])))
    nav = "".join(f'<a class="nav" href="#t{i}">{esc(n)}</a>' for i, (n, _, _, _) in enumerate(topics))
    secs = []
    for i, (n, prob, soln, vl) in enumerate(topics):
        probimgs = "".join(f'<img loading="lazy" class="pg" src="{u}">' for u in prob)
        solimgs = "".join(f'<img loading="lazy" class="pg" src="{u}">' for u in soln)
        vbtns = "".join(f'<a class="vid" href="{esc(v)}" target="_blank">▶ Video solution {k+1}</a>' for k, v in enumerate(vl))
        vid_block = f'<details class="rev"><summary>▶ Video solutions</summary><div class="rb">{vbtns}</div></details>' if vl else ""
        sol_block = f'<details class="rev"><summary>Answers &amp; worked solutions</summary><div class="rb">{solimgs}</div></details>' if soln else ""
        secs.append(f'<section id="t{i}"><h2>{esc(n)}</h2>{probimgs}{vid_block}{sol_block}</section>')
    cover = cover_block(folder, tier, disp, len(topics))
    doc = f"""<!doctype html><!-- fmt:2tab-cov --><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(disp)} · {esc(tier)}</title><style>
:root{{--o:#FF6F00;--od:#E65100;--bg:#FFFDF9;--ink:#23201d;--mut:#8a8175;--card:#fff;}}
body.night{{--bg:#15130f;--ink:#ece6da;--mut:#9a9182;--card:#1f1c17;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:820px;margin:0 auto;padding:0 12px 80px}}
.cover{{color:#f3ecdf;border-radius:0 0 26px 26px;margin:0 -12px 10px;min-height:92vh;display:flex;align-items:center;justify-content:center;text-align:center}}
.frame{{border:1.5px solid;border-radius:14px;margin:20px;padding:34px 26px 26px;width:100%;max-width:520px;min-height:78vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px}}
.tier{{border:1.5px solid;border-radius:999px;padding:5px 18px;font-size:13px;font-weight:800;letter-spacing:3px}}
.motif{{width:190px;height:190px;margin:6px 0}}
.ctitle{{font-family:Georgia,'Times New Roman',serif;font-size:40px;line-height:1.1;margin:0;font-weight:700;color:#fbf4e6}}
.crule{{width:54px;height:3px;border-radius:2px;margin:4px 0}}
.csub{{font-size:11.5px;font-weight:800;letter-spacing:2.5px}}
.cmeta{{font-size:13px;color:#d9d0c0;opacity:.85}}
.cbrand{{margin-top:auto;font-size:11px;font-weight:800;letter-spacing:3px;color:#cdbfa3;opacity:.8}}
.toc{{background:var(--card);border:1px solid #00000010;border-radius:16px;padding:14px 16px;margin:14px 0}}
.toc b{{font-size:12px;letter-spacing:1.5px;color:var(--mut)}}
.nav{{display:block;padding:9px 4px;border-bottom:1px solid #00000008;color:var(--od);text-decoration:none;font-weight:700;font-size:15px}}
section{{margin:26px 0}} h2{{color:var(--od);font-size:21px;border-left:4px solid var(--o);padding-left:10px}}
.pg{{width:100%;border:1px solid #00000012;border-radius:8px;margin:8px 0;background:#fff;display:block}}
.rev{{margin-top:10px;border-top:1px dashed var(--o);padding-top:8px}}
.rev summary{{cursor:pointer;font-weight:800;color:var(--od);font-size:15px}}
.vid{{display:inline-block;margin:8px 8px 8px 0;background:var(--card);border:1.5px solid var(--o);color:var(--od);text-decoration:none;font-weight:700;font-size:13px;border-radius:9px;padding:7px 12px}}
.tbar{{position:fixed;top:0;left:0;right:0;display:flex;justify-content:flex-end;padding:8px 12px;gap:8px;z-index:9}}
.tbar button{{background:#ffffffcc;border:1px solid #00000020;border-radius:20px;padding:6px 12px;font-weight:700;color:#333}}
</style></head><body><div class="tbar"><button onclick="document.body.classList.toggle('night')">☾</button></div>
<div class="wrap">
{cover}
<div class="toc"><b>CONTENTS</b>{nav}</div>
{''.join(secs)}
<p style="text-align:center;color:var(--mut);font-size:12px;margin-top:40px">Vedantu Olympiad School · VOS Library</p>
</div>
<script>
document.querySelectorAll('a.nav').forEach(a=>a.addEventListener('click',e=>{{e.preventDefault();document.querySelector(a.getAttribute('href')).scrollIntoView({{behavior:'smooth'}});}}));
</script></body></html>"""
    od = f"{OUT}/{out_id}"; os.makedirs(od, exist_ok=True)
    p = f"{od}/{out_id}.html"
    open(p, "w").write(doc)
    print(f"wrote {p}  ({os.path.getsize(p)/1e6:.2f} MB, {len(topics)} topics)")

if __name__ == "__main__":
    main()
