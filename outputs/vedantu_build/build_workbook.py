#!/usr/bin/env python3
"""Build ONE faithful-render interactive WORKBOOK from a flat folder of Vedantu
session-assignment PDFs (Grade 3-4 / 5-6 courses). Mixed topics, session-ordered,
worked-solution reveal (no video links in these). General designed cover.
Usage: build_workbook.py <SRC_SUBFOLDER> "<Display>" "<Tier>" <out_id> <base_hex> <gold_hex>
"""
import fitz, os, sys, io, base64, re, html, glob
from PIL import Image

_dir = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Downloads/Vedantu_Content")
OUT = os.path.abspath(os.path.join(_dir, "../../content-books"))
SCALE, Q = 2.0, 72


def _dark(hx, f=0.5):
    h = hx.lstrip("#"); r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"


def motif(gold):
    """General workbook emblem: the classic 3x3 magic square in gold line-art."""
    cells = [["8", "1", "6"], ["3", "5", "7"], ["4", "9", "2"]]
    out = [f'<rect x="40" y="40" width="140" height="140" fill="none" stroke="{gold}" stroke-width="2"/>']
    for k in (1, 2):
        out.append(f'<line x1="{40+k*140/3:.0f}" y1="40" x2="{40+k*140/3:.0f}" y2="180" stroke="{gold}" stroke-width="1.2" opacity=".6"/>')
        out.append(f'<line x1="40" y1="{40+k*140/3:.0f}" x2="180" y2="{40+k*140/3:.0f}" stroke="{gold}" stroke-width="1.2" opacity=".6"/>')
    for r in range(3):
        for c in range(3):
            x, y = 40 + c*140/3 + 23, 40 + r*140/3 + 33
            out.append(f'<text x="{x:.0f}" y="{y:.0f}" fill="{gold}" font-family="Georgia,serif" font-size="26" text-anchor="middle">{cells[r][c]}</text>')
    # small star top-centre
    out.append(f'<circle cx="110" cy="24" r="3.4" fill="{gold}"/>')
    return "".join(out)


def cover_block(tier, disp, n, base, gold):
    return f'''<div class="cover" style="background:linear-gradient(155deg,{base} 0%,{_dark(base,0.62)} 60%,{_dark(base,0.4)} 100%)">
  <div class="frame" style="border-color:{gold}55">
    <div class="tier" style="border-color:{gold};color:{gold}">{html.escape(tier)}</div>
    <svg class="motif" viewBox="0 0 220 220">{motif(gold)}</svg>
    <h1 class="ctitle">{html.escape(disp)}</h1>
    <div class="crule" style="background:{gold}"></div>
    <div class="csub" style="color:{gold}">VEDANTU · OLYMPIAD MATH MASTERY</div>
    <div class="cmeta">{n} sessions · problems &amp; worked solutions</div>
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
        if re.search(r'\b(Answers?\s*Key|ANSWER\s*KEY|Solutions?\b)', t):
            return i
    return len(texts)


def b64(wb): return "data:image/webp;base64," + base64.b64encode(wb).decode()
def esc(s): return html.escape(s)


def clean_name(fn):
    n = re.sub(r'^\d+_', '', fn[:-4]).replace("_", " ")
    return re.sub(r'\s+', ' ', n).strip().title()


def main():
    sub, disp, tier, out_id, base, gold = sys.argv[1:7]
    pdfs = sorted(glob.glob(f"{SRC}/{sub}/*.pdf"),
                  key=lambda p: int(re.match(r'(\d+)', os.path.basename(p)).group(1)) if re.match(r'\d', os.path.basename(p)) else 999)
    topics = []
    for f in pdfs:
        name = clean_name(os.path.basename(f))
        pages = render_pages(f)
        si = split_idx([t for _, t in pages])
        prob = [b64(wb) for wb, _ in pages[:si]] or [b64(pages[0][0])]
        soln = [b64(wb) for wb, _ in pages[si:]]
        topics.append((name, prob, soln))
    # Each session is a COLLAPSIBLE card (native <details>, no JS) — so the home
    # view is a clean, scannable list of every session (this IS the contents).
    cards = []
    for i, (n, prob, soln) in enumerate(topics):
        probimgs = "".join(f'<img loading="lazy" class="pg" src="{u}">' for u in prob)
        solimgs = "".join(f'<img loading="lazy" class="pg" src="{u}">' for u in soln)
        sol_block = (f'<details class="rev"><summary>Answers &amp; worked solutions</summary>'
                     f'<div class="rb">{solimgs}</div></details>') if soln else ""
        op = " open" if i == 0 else ""
        cards.append(
            f'<details class="ses" id="t{i}"{op}>'
            f'<summary><span class="num">{i+1}</span><span class="stitle">{esc(n)}</span>'
            f'<span class="chev">›</span></summary>'
            f'<div class="sbody">{probimgs}{sol_block}'
            f'<a class="backtop" href="#home">↑ Contents</a></div>'
            f'</details>')
    cover = cover_block(tier, disp, len(topics), base, gold)
    doc = f"""<!doctype html><!-- fmt:wb2 --><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(disp)} · {esc(tier)}</title><style>
:root{{--o:#FF6F00;--od:#E65100;--bg:#FFFDF9;--ink:#23201d;--mut:#8a8175;--card:#fff;--line:#00000012;}}
body.night{{--bg:#15130f;--ink:#ece6da;--mut:#9a9182;--card:#1f1c17;--line:#ffffff14;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,Segoe UI,Roboto,sans-serif}}
a{{-webkit-tap-highlight-color:transparent}}
.bar{{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:10px;padding:11px 14px;background:var(--bg);border-bottom:1px solid var(--line)}}
.bar .home{{flex:1;font-weight:800;color:var(--od);text-decoration:none;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bar .home .bk{{color:var(--mut);font-weight:700}}
.bar button{{background:transparent;border:1px solid var(--line);border-radius:18px;padding:5px 12px;font-weight:700;color:var(--ink);cursor:pointer}}
.wrap{{max-width:820px;margin:0 auto;padding:0 12px 90px}}
.cover{{color:#f3ecdf;border-radius:0 0 26px 26px;margin:0 -12px 14px;min-height:86vh;display:flex;align-items:center;justify-content:center;text-align:center}}
.frame{{border:1.5px solid;border-radius:14px;margin:20px;padding:34px 26px 26px;width:100%;max-width:520px;min-height:72vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px}}
.tier{{border:1.5px solid;border-radius:999px;padding:5px 18px;font-size:13px;font-weight:800;letter-spacing:3px}}
.motif{{width:182px;height:182px;margin:6px 0}}
.ctitle{{font-family:Georgia,'Times New Roman',serif;font-size:38px;line-height:1.12;margin:0;font-weight:700;color:#fbf4e6}}
.crule{{width:54px;height:3px;border-radius:2px;margin:4px 0}}
.csub{{font-size:11.5px;font-weight:800;letter-spacing:2.5px}}
.cmeta{{font-size:13px;color:#d9d0c0;opacity:.85}}
.cbrand{{margin-top:auto;font-size:11px;font-weight:800;letter-spacing:3px;color:#cdbfa3;opacity:.8}}
.lead{{font-size:12px;letter-spacing:1.5px;color:var(--mut);font-weight:800;margin:6px 4px}}
.ses{{background:var(--card);border:1px solid var(--line);border-radius:14px;margin:10px 0;overflow:hidden;scroll-margin-top:60px}}
.ses>summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:14px 15px;font-weight:700;font-size:16px;user-select:none}}
.ses>summary::-webkit-details-marker{{display:none}}
.num{{flex:none;width:30px;height:30px;border-radius:9px;background:var(--o);color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:800}}
.stitle{{flex:1}}
.chev{{flex:none;color:var(--mut);font-size:22px;line-height:1;transition:transform .2s;transform:rotate(90deg)}}
.ses[open]>summary .chev{{transform:rotate(270deg)}}
.ses[open]>summary{{color:var(--od);border-bottom:1px solid var(--line)}}
.sbody{{padding:10px 14px 16px}}
.pg{{width:100%;border:1px solid var(--line);border-radius:8px;margin:8px 0;background:#fff;display:block}}
.rev{{margin-top:12px;border-top:1px dashed var(--o);padding-top:10px}}
.rev>summary{{cursor:pointer;font-weight:800;color:var(--od);font-size:15px;list-style:none}}
.rev>summary::-webkit-details-marker{{display:none}}
.rev>summary::before{{content:"▸ ";color:var(--o)}}
.rev[open]>summary::before{{content:"▾ "}}
.backtop{{display:inline-block;margin-top:14px;color:var(--od);font-weight:700;text-decoration:none;font-size:14px;border:1px solid var(--o);border-radius:9px;padding:7px 13px}}
.fab{{position:fixed;right:16px;bottom:18px;height:46px;padding:0 18px;border-radius:24px;background:var(--o);color:#fff;display:flex;align-items:center;gap:7px;font-size:15px;font-weight:800;box-shadow:0 4px 14px #0004;text-decoration:none;z-index:30}}
</style></head><body>
<span id="home"></span>
<div class="bar"><a class="home" href="#home"><span class="bk">📘</span> {esc(disp)}</a>
<button onclick="document.body.classList.toggle('night')">☾</button></div>
<div class="wrap">
{cover}
<div class="lead">ALL SESSIONS · TAP TO OPEN</div>
{''.join(cards)}
<p style="text-align:center;color:var(--mut);font-size:12px;margin-top:40px">Vedantu Olympiad School · VOS Library</p>
</div>
<a class="fab" href="#home" title="Back to contents">↑ Contents</a>
</body></html>"""
    od = f"{OUT}/{out_id}"; os.makedirs(od, exist_ok=True)
    p = f"{od}/{out_id}.html"
    open(p, "w").write(doc)
    print(f"wrote {p}  ({os.path.getsize(p)/1e6:.2f} MB, {len(topics)} sessions)")


if __name__ == "__main__":
    main()
