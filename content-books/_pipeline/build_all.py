#!/usr/bin/env python3
"""Build all four IOQM pillar books as self-contained interactive HTML for the
Kiwimath reader. Questions are FAITHFUL page renders (never re-typed); the shell
adds contents (smooth in-page scroll), tap-to-reveal video & worked solutions.

Run from outputs/ioqm_build/. Reads PDFs from the mounted IOQM folder; writes one
HTML per pillar + copies into the repo's content-books/."""
import fitz, io, re, base64, html, os, math, shutil
from PIL import Image

_dir = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Downloads/IOQM 2026")
OUT = os.path.abspath(os.path.join(_dir, "../../outputs/ioqm_build"))
REPO = os.path.abspath(os.path.join(_dir, ".."))
SCALE, Q = 1.7, 82

# ------------------------------------------------------------------ motifs
def motif_geometry():
    angs=[105,5,235]; V=[(math.cos(math.radians(a)),math.sin(math.radians(a))) for a in angs]
    A,B,C=V
    d=lambda P,Qq: math.hypot(P[0]-Qq[0],P[1]-Qq[1])
    a,b,c=d(B,C),d(C,A),d(A,B); s=(a+b+c)/2
    area=abs((B[0]-A[0])*(C[1]-A[1])-(C[0]-A[0])*(B[1]-A[1]))/2
    r=area/s; I=((a*A[0]+b*B[0]+c*C[0])/(a+b+c),(a*A[1]+b*B[1]+c*C[1])/(a+b+c))
    SCp=46; CX,CY=75,56; tx=lambda P:(CX+P[0]*SCp,CY-P[1]*SCp)
    (ax,ay),(bx,by),(cx,cy)=tx(A),tx(B),tx(C); ox,oy=tx((0,0)); ix,iy=tx(I)
    f=lambda x:f"{x:.2f}"
    return (f'<circle cx="{f(ox)}" cy="{f(oy)}" r="{f(46)}" stroke="#FF6F00" stroke-width="2.2"/>'
            f'<path d="M{f(ax)} {f(ay)} L{f(bx)} {f(by)} L{f(cx)} {f(cy)} Z" stroke="#14213D" stroke-width="2.2" stroke-linejoin="round"/>'
            f'<circle cx="{f(ix)}" cy="{f(iy)}" r="{f(r*SCp)}" stroke="#C8901A" stroke-width="1.8"/>'
            f'<circle cx="{f(ox)}" cy="{f(oy)}" r="2.5" fill="#FF6F00"/>'
            f'<circle cx="{f(ix)}" cy="{f(iy)}" r="2.5" fill="#C8901A"/>')

def motif_algebra():
    # axes + exact parabola y = x^2 (mapped), highlighting the vertex
    CX,CY=75,70; sx=40; sy=30
    pts=[]
    x=-1.15
    while x<=1.15+1e-9:
        pts.append((CX+x*sx, CY-(x*x)*sy)); x+=0.1
    path="M"+" L".join(f"{px:.1f} {py:.1f}" for px,py in pts)
    return (f'<line x1="{CX-52}" y1="{CY}" x2="{CX+52}" y2="{CY}" stroke="#C8901A" stroke-width="1.6"/>'
            f'<line x1="{CX}" y1="14" x2="{CX}" y2="100" stroke="#C8901A" stroke-width="1.6"/>'
            f'<path d="{path}" stroke="#FF6F00" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
            f'<circle cx="{CX}" cy="{CY}" r="2.6" fill="#14213D"/>')

def motif_combinatorics():
    CX,CY,R=75,56,38; n=6
    P=[(CX+R*math.cos(i*2*math.pi/n-math.pi/2), CY+R*math.sin(i*2*math.pi/n-math.pi/2)) for i in range(n)]
    seg=[]
    for i in range(n):
        for j in range(i+1,n):
            seg.append(f'<line x1="{P[i][0]:.1f}" y1="{P[i][1]:.1f}" x2="{P[j][0]:.1f}" y2="{P[j][1]:.1f}" stroke="#C8901A" stroke-width="1.1" opacity="0.8"/>')
    dots="".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#FF6F00"/>' for x,y in P)
    return "".join(seg)+dots

def motif_nt():
    # triangular dot lattice (figurate numbers) + ring the apex
    CX,CY=75,22; step=15; out=[]
    for row in range(5):
        for i in range(row+1):
            x=CX+(i-row/2)*step; y=CY+row*step*0.92
            col="#FF6F00" if row==0 else ("#14213D" if (i==0 or i==row) else "#C8901A")
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{col}"/>')
    return "".join(out)

# ------------------------------------------------------------------ pillars
PILLARS = {
 "geometry-ioqm": dict(
   subject="Geometry", title="Geometry", motif=motif_geometry,
   topics=[("Geometry/CONGRUENT TRIANGLES.pdf","Congruent Triangles"),
           ("Geometry/SIMILAR TRIANGLES.pdf","Similar Triangles"),
           ("Geometry/PROBLEMS ON ANGLE CHASING.pdf","Angle Chasing"),
           ("Geometry/CENTROID AND ORTHOCENTER.pdf","Centroid & Orthocentre"),
           ("Geometry/INCENTER AND CIRCUMCENTER.pdf","Incentre & Circumcentre"),
           ("Geometry/CEVAS AND MENELAUS.pdf","Ceva's & Menelaus"),
           ("Geometry/TRIANGLE INEQUALITIES, MPT,BPT.pdf","Triangle Inequalities, MPT & BPT"),
           ("Geometry/PYTHAGORAS, APPOLONIUS, STEWART.pdf","Pythagoras, Apollonius & Stewart"),
           ("Geometry/QUADRILATERALS, CYCLIC QUADRILATERALS.pdf","Quadrilaterals & Cyclic Quadrilaterals"),
           ("Geometry/CIRCLES AND PROPERTIES.pdf","Circles & Their Properties"),
           ("Geometry/PTOLEMY AND TANGENTS.pdf","Ptolemy & Tangents"),
           ("Geometry/PROBLEMS ON AREAS.pdf","Problems on Areas"),
           ("Geometry/PROBLEM SOLVING.pdf","Mixed Problem Solving")]),
 "algebra-ioqm": dict(
   subject="Algebra", title="Algebra", motif=motif_algebra,
   topics=[("Identities.pdf","Algebraic Identities"),
           ("Algebra/Polynomials.pdf","Polynomials"),
           ("Algebra/RELATION BETWEEN ROOTS AND CORFFICIENTS, NATURE OF ROOTS.pdf","Roots & Coefficients"),
           ("Algebra/RATIONAL AND INTEGRAL ROOTS.pdf","Rational & Integral Roots"),
           ("Algebra/FUNCTIONS-INTRO.pdf","Functions — Introduction"),
           ("Algebra/FUNCTIONAL EQUATIONS.pdf","Functional Equations"),
           ("Algebra/MODULUS.pdf","Modulus"),
           ("Algebra/GIF, Fractional part.pdf","Greatest Integer & Fractional Part"),
           ("Algebra/AP,GP,HP.pdf","AP, GP & HP"),
           ("Algebra/SIGMA NOTATION.pdf","Sigma Notation"),
           ("Algebra/TELESCOPING.pdf","Telescoping"),
           ("Algebra/MEANS INEQUALITY, MTH POWERS,RMS.pdf","Means Inequality (AM–GM, RMS)"),
           ("Inequalities.pdf","Inequalities"),
           ("Algebra/GRAPH ANALYSIS AND COMMON ROOTS.pdf","Graph Analysis & Common Roots")]),
 "combinatorics-ioqm": dict(
   subject="Combinatorics", title="Combinatorics", motif=motif_combinatorics,
   topics=[("Combi/nCr.pdf","nCr — Combinations"),
           ("Combi/STANDARD CONCEPTS AND PROBLEMS.pdf","Standard Concepts & Problems"),
           ("Combi/ARRANGEMENT BASED PROBLEMS.pdf","Arrangement-Based Problems"),
           ("Combi/DISTRIBUTION OF DISTINCT OBJECTS, GROUPING.pdf","Distribution & Grouping"),
           ("Combi/OBJECTS IN CIRCLES.pdf","Objects in Circles"),
           ("Combi/DIVISORS.pdf","Divisors"),
           ("Combi/BEGGAR COIN.pdf","Beggar–Coin (Stars & Bars)"),
           ("Combi/RECURRENCE.pdf","Recurrence")]),
 "numbertheory-ioqm": dict(
   subject="Number Theory", title="Number Theory", motif=motif_nt,
   topics=[("NT/BASE SYSTEM.pdf","Base Systems"),
           ("NT/LCM,GCD BASED PROBLEMS.pdf","LCM & GCD"),
           ("NT/PERFECT SQUARES, PRIMES.pdf","Perfect Squares & Primes"),
           ("NT/CONGRUENCE.pdf","Congruences"),
           ("NT/FERMAT AND EULER THEOREM.pdf","Fermat & Euler Theorems"),
           ("NT/WILSON AND CRT.pdf","Wilson's Theorem & CRT"),
           ("NT/DIOPHANTINE EQUATION.pdf","Diophantine Equations"),
           ("NT/PROBLEM SOLVING 1.pdf","Mixed Problem Solving")]),
}

# ------------------------------------------------------------------ helpers
def webp_b64(page):
    pix=page.get_pixmap(matrix=fitz.Matrix(SCALE,SCALE))
    im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
    b=io.BytesIO(); im.save(b,"WEBP",quality=Q,method=6)
    return base64.b64encode(b.getvalue()).decode()

def split_page(d):
    for i in range(d.page_count):
        if re.search(r'Answers?\s*Key|Video\s*Solutions', d[i].get_text(), re.I):
            return i
    return 1

def videos(d):
    seen=[]
    for i in range(d.page_count):
        for l in sorted(d[i].get_links(), key=lambda l:l.get('from',fitz.Rect(0,0,0,0)).y0):
            u=l.get('uri','')
            if u and 'youtu' in u and u not in seen: seen.append(u)
    return seen

CSS = """
:root{--bg:#FCFBF7;--fg:#23262e;--brand:#FF6F00;--brand2:#E65100;--card:#ffffff;--rule:#e7e3d8;--muted:#6B7280;--chip:#FFF3E0}
body.night{--bg:#15171C;--fg:#E6E9EF;--card:#1F232B;--rule:#2c2f36;--muted:#9aa0aa;--chip:#3a2a14}
*{box-sizing:border-box}html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.6;-webkit-text-size-adjust:100%}
.wrap{max-width:740px;margin:0 auto;padding:0 16px 64px}
a{color:var(--brand2)}
.cover{padding:54px 22px 30px;text-align:center}
.cover .kick{letter-spacing:.32em;font-size:.72rem;font-weight:800;color:var(--brand);text-transform:uppercase}
.cover h1{font-size:2.7rem;line-height:1.05;margin:.32em 0 .1em;font-weight:900;letter-spacing:-.5px}
.cover .sub{color:var(--muted);font-size:1rem;margin:.2em 0 1.1em}
.cover svg{display:block;margin:14px auto 18px}
.cover .meta{display:inline-flex;gap:8px;flex-wrap:wrap;justify-content:center}
.cover .pill{background:var(--chip);color:var(--brand2);border-radius:999px;padding:5px 12px;font-size:.78rem;font-weight:700}
.hint{margin:18px auto 0;max-width:520px;background:var(--card);border:1px solid var(--rule);border-radius:14px;padding:14px 16px;color:var(--muted);font-size:.9rem;text-align:left}
.hint b{color:var(--fg)}
hr.div{border:0;border-top:1px solid var(--rule);margin:30px 0}
h2.sec{font-size:.82rem;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:800;margin:8px 0 12px}
.toc{list-style:none;margin:0;padding:0}
.toc a{display:flex;align-items:center;gap:14px;text-decoration:none;color:var(--fg);padding:13px 14px;border:1px solid var(--rule);border-radius:13px;margin:9px 0;background:var(--card)}
.toc .num{flex:0 0 30px;height:30px;border-radius:8px;background:var(--chip);color:var(--brand2);font-weight:800;display:flex;align-items:center;justify-content:center;font-size:.92rem}
.toc .tt{font-weight:650;font-size:1.02rem}
.toc .ar{margin-left:auto;color:var(--muted)}
section.topic{padding-top:14px;scroll-margin-top:8px}
.thead{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;border-top:2px solid var(--brand);padding-top:16px;margin-top:26px}
.thead .tnum{font-size:.74rem;letter-spacing:.18em;font-weight:800;color:var(--brand);text-transform:uppercase}
.thead h3{font-size:1.5rem;margin:.1em 0;font-weight:850;flex:1 1 100%}
.thead .top{margin-left:auto;font-size:.82rem;text-decoration:none;color:var(--muted)}
.label{font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:800;margin:18px 0 8px}
img.pg{width:100%;display:block;aspect-ratio:.707;object-fit:contain;background:#fff;border:1px solid var(--rule);border-radius:10px;margin:10px 0}
img.pg.loaded{aspect-ratio:auto}
details.rev{margin:12px 0;border:1px solid var(--rule);border-radius:13px;overflow:hidden;background:var(--card)}
details.rev>summary{list-style:none;cursor:pointer;padding:14px 16px;font-weight:750;color:var(--brand2);display:flex;align-items:center;gap:10px;user-select:none}
details.rev>summary::-webkit-details-marker{display:none}
.chev{transition:transform .2s;display:inline-block;color:var(--brand)}
details[open]>summary .chev{transform:rotate(90deg)}
.rev .n{color:var(--muted);font-weight:600;margin-left:auto;font-size:.9rem}
.rev .body{padding:4px 14px 14px}
.vids{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:430px){.vids{grid-template-columns:1fr}}
a.vid{display:flex;align-items:center;gap:9px;text-decoration:none;color:var(--fg);padding:11px 13px;border:1px solid var(--rule);border-radius:11px;background:var(--bg);font-size:.92rem;font-weight:600}
a.vid .play{color:#fff;background:#E8543F;border-radius:6px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:.7rem}
a.vid .yt{margin-left:auto;font-size:.7rem;color:var(--muted);font-weight:700}
.endcap{text-align:center;color:var(--muted);font-size:.85rem;padding:40px 0 10px}
"""

SCRIPT = """
(function(){
  var io=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ var im=e.target;
      if(im.dataset.src){ im.src=im.dataset.src; im.removeAttribute('data-src'); }
      im.addEventListener('load',function(){im.classList.add('loaded');}); io.unobserve(im); } });
  },{rootMargin:'800px 0px'});
  function observeAll(root){ (root||document).querySelectorAll('img.pg[data-src]').forEach(function(im){io.observe(im);}); }
  observeAll();
  document.querySelectorAll('details.rev').forEach(function(d){ d.addEventListener('toggle',function(){ if(d.open) observeAll(d); }); });
  // in-page Contents links -> smooth scroll (don't let the WebView reload the file)
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if(a){ var el=document.getElementById(a.getAttribute('href').slice(1));
      if(el){ e.preventDefault(); el.scrollIntoView({behavior:'smooth', block:'start'}); } }
  }, false);
})();
"""

def build(book_id, cfg):
    title=cfg["title"]; subject=cfg["subject"]; T=cfg["topics"]
    parts=[f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>IOQM 2026 · {title}</title><style>{CSS}</style></head><body><div class="wrap">
<div class="cover" id="top"><div class="kick">IOQM 2026</div>
<h1>{html.escape(title)}</h1>
<div class="sub">Assignments, video walkthroughs &amp; worked solutions</div>
<svg width="150" height="116" viewBox="0 0 150 116" fill="none" xmlns="http://www.w3.org/2000/svg">{cfg["motif"]()}</svg>
<div class="meta"><span class="pill">{len(T)} topics</span><span class="pill">Level I &amp; II</span><span class="pill">Video solutions</span></div>
<div class="hint"><b>How to use this book.</b> Tap a topic to jump in. Try the problems first — then open <b>Video solutions</b> or <b>Answers &amp; worked solutions</b> when you're ready.</div>
</div><hr class="div"><h2 class="sec" id="contents">Contents</h2><ul class="toc">''']
    for i,(_,tt) in enumerate(T,1):
        parts.append(f'<li><a href="#t{i}"><span class="num">{i:02d}</span><span class="tt">{html.escape(tt)}</span><span class="ar">&rsaquo;</span></a></li>')
    parts.append("</ul>")
    npages=0
    for i,(rel,tt) in enumerate(T,1):
        d=fitz.open(f"{SRC}/{rel}"); sp=split_page(d); npages+=d.page_count
        probs=[webp_b64(d[j]) for j in range(0,sp)]
        sols=[webp_b64(d[j]) for j in range(sp,d.page_count)]
        vids=videos(d)
        parts.append(f'<section class="topic" id="t{i}"><div class="thead">'
                     f'<span class="tnum">{subject} &middot; {i:02d} of {len(T)}</span>'
                     f'<a class="top" href="#contents">&uarr; Contents</a><h3>{html.escape(tt)}</h3></div>')
        parts.append('<div class="label">Problems</div>')
        for j,b in enumerate(probs):
            a='src' if j==0 else 'data-src'
            parts.append(f'<img class="pg" {a}="data:image/webp;base64,{b}" alt="">')
        if vids:
            parts.append(f'<details class="rev"><summary><span class="chev">&#9656;</span>Video solutions<span class="n">{len(vids)} clips</span></summary><div class="body"><div class="vids">')
            for k,u in enumerate(vids,1):
                parts.append(f'<a class="vid" href="{html.escape(u,quote=True)}" target="_blank" rel="noopener"><span class="play">&#9654;</span><span>Question {k}</span><span class="yt">YouTube</span></a>')
            parts.append('</div></div></details>')
        if sols:
            parts.append(f'<details class="rev"><summary><span class="chev">&#9656;</span>Answers &amp; worked solutions<span class="n">{len(sols)} pages</span></summary><div class="body">')
            for b in sols:
                parts.append(f'<img class="pg" data-src="data:image/webp;base64,{b}" alt="">')
            parts.append('</div></details>')
        parts.append('</section>')
    parts.append(f'<div class="endcap">End of {html.escape(title)} &middot; IOQM 2026</div></div><script>{SCRIPT}</script></body></html>')
    out="".join(parts)
    path=f"{OUT}/{book_id}.html"; open(path,"w",encoding="utf-8").write(out)
    os.makedirs(f"{REPO}/{book_id}",exist_ok=True)
    fname={"geometry-ioqm":"EuclidGeometry_IOQM.html"}.get(book_id, f"{book_id}.html")
    shutil.copy(path, f"{REPO}/{book_id}/{fname}")
    sz=os.path.getsize(path)
    nimg=out.count('class="pg"'); nvid=out.count('class="vid"')
    print(f"{book_id:20} topics {len(T):2} pages {npages:3} imgs {nimg:3} vids {nvid:3}  {sz/1e6:5.2f} MB -> {fname}")
    return sz

if __name__=="__main__":
    for bid,cfg in PILLARS.items():
        build(bid,cfg)
