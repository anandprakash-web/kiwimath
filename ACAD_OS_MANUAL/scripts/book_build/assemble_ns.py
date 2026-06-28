#!/usr/bin/env python3
"""Assemble ONE 'Number Sense' interactive book from the 13-worksheet slide cache.
Faithful slides + 13 chapters + contents nav; interactive slides (config-driven)
become tap-to-answer / type-and-check. Re-run after extending INTERACTIVE."""
import os, io, base64, json, html, fitz
from PIL import Image

_dir = os.path.dirname(os.path.abspath(__file__))
NSB = os.path.abspath(os.path.join(_dir, "../../outputs/nsbuild"))
CACHE = f"{NSB}/cache"
SRC = os.path.expanduser("~/Downloads/VEL Wavebook PDFs/Number Sense and Operations")
MAN = json.load(open(f"{CACHE}/manifest.json"))
FILES = {c["idx"]: c["file"] for c in MAN}

# ------- interactive answer key (chapter_idx, slide_1based) -> config ----------
# type 'mcq'  : tap the right option.   crop = visual to keep (drop printed options)
# type 'fill' : type a+b=c and check.   crop = visual to keep (drop printed boxes)
INTERACTIVE = {
 # ---- Chapter 7: Addition & Forward Sequencing (c06) ----
 (6, 4): {"t": "mcq",  "crop": (0,0,768,538), "label": "Total number of birds =", "opts": [7,5,4], "ans": 5},
 (6, 5): {"t": "mcq",  "crop": (0,0,768,538), "label": "Total pairs of shoes =",  "opts": [8,5,4], "ans": 4},
 (6, 8): {"t": "fill", "crop": (0,0,768,352), "abc": (3,2,5)},
 (6, 9): {"t": "fill", "crop": (0,0,768,352), "abc": (5,3,8)},
 (6,10): {"t": "fill", "crop": (0,0,768,352), "abc": (3,5,8)},
 (6,11): {"t": "fill", "crop": (0,0,768,352), "abc": (2,1,3)},
 (6,13): {"t": "mcq",  "crop": (0,0,768,430), "opts": ["2+2=4","1+1=4","3+2=5","3+3=5"], "ans": "3+2=5"},
 (6,14): {"t": "fill", "crop": (0,0,768,430), "abc": (3,2,5)},
 (6,16): {"t": "fill", "crop": (0,0,768,430), "abc": (3,4,7)},
 (6,19): {"t": "one",  "ans": 5},
 (6,20): {"t": "one",  "ans": 7},
 (6,21): {"t": "one",  "ans": 8},
 (6,23): {"t": "mcq",  "crop": (0,0,768,452), "opts": [8,3,30,6], "ans": 3},
 (6,24): {"t": "mcq",  "crop": (0,0,768,452), "opts": [100,1,10,6], "ans": 10},
 (6,25): {"t": "mcq",  "crop": (0,0,768,452), "opts": [8,3,4,6], "ans": 6},
 (6,26): {"t": "mcq",  "crop": (0,0,768,452), "opts": [8,3,4,6], "ans": 8},
 (6,28): {"t": "mcq",  "crop": (0,0,768,452), "opts": [8,3,0,6], "ans": 0},
 (6,29): {"t": "mcq",  "crop": (0,0,768,452), "opts": [9,3,0,6], "ans": 9},
 (6,30): {"t": "mcq",  "crop": (0,0,768,452), "opts": [8,3,0,6], "ans": 3},
 (6,32): {"t": "one",  "ans": 7},
 (6,33): {"t": "one",  "ans": 3},
 (6,34): {"t": "one",  "ans": 8},
 (6,35): {"t": "one",  "ans": 6},   # 1 Play + 5 Novels
 (6,36): {"t": "one",  "ans": 6},
 (6,37): {"t": "one",  "ans": 9},
 (6,38): {"t": "one",  "ans": 4},   # 6 cupcakes -> 4 more for 10
 (6,39): {"t": "one",  "ans": 9},   # 1 cheetah -> 9 more
 (6,40): {"t": "one",  "ans": 5},
 (6,41): {"t": "one",  "ans": 5},
 (6,42): {"t": "one",  "ans": 9},   # 1 dot -> 9 more (verify)
 # 15 (which-picture match) + 18 (number-line read) left faithful — ambiguous to auto-read
 # ---- Chapter 8: Subtraction & Backward Sequencing (c07) ----
 (7,15): {"t": "one", "ans": 3}, (7,16): {"t": "one", "ans": 7}, (7,17): {"t": "one", "ans": 5}, (7,18): {"t": "one", "ans": 2},
 (7,26): {"t": "one", "ans": 3}, (7,27): {"t": "one", "ans": 3}, (7,28): {"t": "one", "ans": 6},
 (7,30): {"t": "fill_sub", "abc": (1,1,0)}, (7,31): {"t": "fill_sub", "abc": (7,5,2)},
 (7,32): {"t": "fill_sub", "abc": (8,8,0)}, (7,33): {"t": "fill_sub", "abc": (6,3,3)},
 (7,34): {"t": "mcq", "crop": (0,0,768,186), "opts": ["9-4","5-3","4-1","5-5"], "ans": "5-3"},
 (7,35): {"t": "mcq", "crop": (0,0,768,186), "opts": ["10-1","10-0","9-1","10-2"], "ans": "10-0"},
 (7,36): {"t": "mcq", "crop": (0,0,768,186), "opts": ["7-6","9-6","8-6","9-5"], "ans": "9-6"},
 (7,37): {"t": "mcq", "crop": (0,0,768,186), "opts": ["9-2","4-3","10-5","6-3"], "ans": "10-5"},
 (7,39): {"t": "fill_sub", "abc": (8,5,3)}, (7,40): {"t": "fill_sub", "abc": (10,4,6)}, (7,41): {"t": "fill_sub", "abc": (6,0,6)},
 (7,43): {"t": "one", "ans": 2}, (7,44): {"t": "one", "ans": 5}, (7,45): {"t": "one", "ans": 8}, (7,46): {"t": "one", "ans": 6},
 (7,48): {"t": "mcq", "crop": (0,0,768,452), "opts": [3,1,4,2], "ans": 2},
 (7,49): {"t": "one", "ans": 2}, (7,50): {"t": "one", "ans": 4}, (7,51): {"t": "one", "ans": 2}, (7,52): {"t": "one", "ans": 1},
 (7,53): {"t": "one", "ans": 2}, (7,54): {"t": "one", "ans": 3}, (7,55): {"t": "one", "ans": 6},
 # faithful (hard to auto-read): 5,6,8-13 mango drag · 20,22 which-picture · 21,23 write-sentence count · 25 number-line MCQ
 # ---- Chapter 9: Challenges on Addition & Subtraction up to 10 (c08) ----
 (8,19): {"t": "one", "ans": 5}, (8,20): {"t": "one", "ans": 6}, (8,21): {"t": "one", "ans": 2}, (8,22): {"t": "one", "ans": 4},
 (8,23): {"t": "one", "ans": 4}, (8,24): {"t": "one", "ans": 9}, (8,25): {"t": "one", "ans": 6}, (8,26): {"t": "one", "ans": 10},
 (8,27): {"t": "one", "ans": 5}, (8,28): {"t": "one", "ans": 8}, (8,31): {"t": "one", "ans": 3}, (8,32): {"t": "one", "ans": 1},
 (8,33): {"t": "one", "ans": 5}, (8,42): {"t": "one", "ans": 6},
 # faithful (hard): 5-12 dot/finger/fruit counts · 14-17 sign/number drag · 29-30,34-40 number-line missing · 43-45 number bonds
 # ---- Chapter 10: Addition Facts up to 20 (c09) ----
 (9,40): {"t": "multi", "crop": (0,0,768,190), "opts": ["1,8","3,7","5,5","3,6"], "correct": ["1,8","3,6"]},
 (9,41): {"t": "multi", "crop": (0,0,768,190), "opts": ["7,9","3,7","5,11","6,6"], "correct": ["7,9","5,11"]},
 (9,42): {"t": "multi", "crop": (0,0,768,190), "opts": ["7,7","3,7","5,11","8,6"], "correct": ["7,7","8,6"]},
 (9,51): {"t": "mcq", "crop": (0,0,768,452), "opts": [10,3,2,4], "ans": 2},
 (9,53): {"t": "mcq", "crop": (0,0,768,452), "opts": [8,6,4,7], "ans": 7},
 (9,54): {"t": "mcq", "crop": (0,0,768,452), "opts": [5,4,6,14], "ans": 4},
 (9,55): {"t": "mcq", "crop": (0,0,768,452), "opts": [10,14,12,8], "ans": 10},
 (9,56): {"t": "mcq", "crop": (0,0,768,452), "opts": [5,3,6,4], "ans": 6},
 (9,59): {"t": "one", "ans": 3},
 # faithful: 5-14 pick&drop laddoos · 16-21 make-10 counts · 22-39 drag blocks/bonds · 45-50 teaching · 58,60,61 pair MCQ
}

def b64_cache(ci, p):
    # downscale the cached slide a touch + recompress to keep the single-file
    # book light enough to open smoothly on lower-end phones.
    im = Image.open(f"{CACHE}/c{ci:02d}/p{p:03d}.webp").convert("RGB")
    w, h = im.size
    im = im.resize((round(w * 0.82), round(h * 0.82)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "WEBP", quality=72, method=4)
    return base64.b64encode(b.getvalue()).decode()

def b64_crop(ci, slide1, rect):
    d = fitz.open(f"{SRC}/{FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(2.0,2.0), clip=fitz.Rect(*rect))
    im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    b = io.BytesIO(); im.save(b, "WEBP", quality=86, method=6)
    return base64.b64encode(b.getvalue()).decode()

def faithful(ci, p, eager=False):
    a = "src" if eager else "data-src"
    return f'<img class="pg" {a}="data:image/webp;base64,{b64_cache(ci,p)}" alt="">'

def mcq_block(ci, s, cfg):
    cols = ["#E5197D", "#1565C0", "#F4511E", "#2E7D32"]
    img = f'<img class="vis" src="data:image/webp;base64,{b64_crop(ci,s,cfg["crop"])}" alt="">'
    wide = any(isinstance(v, str) for v in cfg["opts"])
    btns = "".join(
        f'<button class="opt{" wide" if wide else ""}" style="--c:{cols[i%len(cols)]}" '
        f'data-ok="{1 if v==cfg["ans"] else 0}" onclick="pick(this)">{html.escape(str(v))}</button>'
        for i, v in enumerate(cfg["opts"]))
    lbl = cfg.get("label", "")
    qline = f'<div class="qline">{html.escape(lbl)}</div>' if lbl else ""
    return f'<div class="iq">{img}{qline}<div class="opts">{btns}</div><div class="fb">&nbsp;</div></div>'

def one_block(ci, p, cfg):
    # single-answer slide: show the whole faithful slide + one input to check.
    img = f'<img class="vis" src="data:image/webp;base64,{b64_cache(ci,p)}" alt="">'
    return (f'<div class="iq">{img}<div class="oneans"><span class="lbl">Type your answer:</span>'
            f'<input class="num" inputmode="numeric" pattern="[0-9]*" maxlength="2" data-ans="{cfg["ans"]}">'
            f'<button class="check" onclick="check(this)">Check</button></div>'
            f'<div class="fb">&nbsp;</div></div>')

def fillsub_block(ci, p, cfg):
    # subtraction sentence a - b = c (full faithful slide + 3 inputs below).
    a, b, c = cfg["abc"]
    img = f'<img class="vis" src="data:image/webp;base64,{b64_cache(ci,p)}" alt="">'
    box = lambda ans: f'<input class="num" inputmode="numeric" pattern="[0-9]*" maxlength="2" data-ans="{ans}">'
    return (f'<div class="iq">{img}<div class="oneans"><span class="lbl">Type the missing sentence:</span></div>'
            f'<div class="sentence">{box(a)}<span class="op minus">−</span>{box(b)}<span class="op eq">=</span>{box(c)}</div>'
            f'<div class="row"><button class="check" onclick="check(this)">Check</button></div>'
            f'<div class="fb">&nbsp;</div></div>')

def multi_block(ci, s, cfg):
    # tap ALL the correct options (multi-select), immediate per-tap feedback.
    img = f'<img class="vis" src="data:image/webp;base64,{b64_crop(ci,s,cfg["crop"])}" alt="">'
    correct = set(str(v) for v in cfg["correct"])
    cols = ["#E5197D", "#1565C0", "#F4511E", "#2E7D32"]
    btns = "".join(
        f'<button class="opt wide" style="--c:{cols[i%len(cols)]}" data-ok="{1 if str(v) in correct else 0}" '
        f'onclick="multipick(this)">{html.escape(str(v))}</button>' for i, v in enumerate(cfg["opts"]))
    return (f'<div class="iq">{img}<div class="opts" data-need="{len(correct)}" data-got="0">{btns}</div>'
            f'<div class="fb">&nbsp;</div></div>')

def fill_block(ci, s, cfg):
    a, b, c = cfg["abc"]
    img = f'<img class="vis" src="data:image/webp;base64,{b64_crop(ci,s,cfg["crop"])}" alt="">'
    box = lambda ans: f'<input class="num" inputmode="numeric" pattern="[0-9]*" maxlength="2" data-ans="{ans}">'
    return (f'<div class="iq">{img}<div class="sentence">{box(a)}<span class="op plus">+</span>'
            f'{box(b)}<span class="op eq">=</span>{box(c)}</div>'
            f'<div class="row"><button class="check" onclick="check(this)">Check answer</button></div>'
            f'<div class="fb">&nbsp;</div></div>')

CSS = """
:root{--bg:#FFFDF8;--ink:#22324A;--brand:#FF6F00;--brand2:#E65100;--card:#fff;--rule:#ECE6DA;--muted:#6B7280;--chip:#FFF3E0;--good:#2E9E5B;--bad:#E5484D}
body.night{--bg:#15171C;--ink:#E6E9EF;--card:#1F232B;--rule:#2c2f36;--muted:#9aa0aa;--chip:#3a2a14}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,system-ui,sans-serif;line-height:1.5;-webkit-text-size-adjust:100%}
.wrap{max-width:720px;margin:0 auto;padding:0 12px 70px}
a{color:var(--brand2)}
.cover{padding:52px 20px 26px;text-align:center}
.cover .kick{letter-spacing:.28em;font-size:.72rem;font-weight:800;color:var(--brand);text-transform:uppercase}
.cover h1{font-size:2.4rem;line-height:1.05;margin:.3em 0 .12em;font-weight:900;letter-spacing:-.5px}
.cover .sub{color:var(--muted);font-size:1rem;margin:.2em 0 1em}
.cover svg{display:block;margin:12px auto 16px}
.cover .pill{display:inline-block;background:var(--chip);color:var(--brand2);border-radius:999px;padding:5px 13px;font-size:.78rem;font-weight:700}
.hint{margin:16px auto 0;max-width:520px;background:var(--card);border:1px solid var(--rule);border-radius:14px;padding:13px 15px;color:var(--muted);font-size:.9rem;text-align:left}
.hint b{color:var(--ink)}
hr.div{border:0;border-top:1px solid var(--rule);margin:26px 0}
h2.sec{font-size:.8rem;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:800;margin:6px 0 10px}
.toc{list-style:none;margin:0;padding:0}
.toc a{display:flex;align-items:center;gap:13px;text-decoration:none;color:var(--ink);padding:12px 13px;border:1px solid var(--rule);border-radius:12px;margin:8px 0;background:var(--card)}
.toc .num{flex:0 0 28px;height:28px;border-radius:8px;background:var(--chip);color:var(--brand2);font-weight:800;display:flex;align-items:center;justify-content:center;font-size:.86rem}
.toc .tt{font-weight:650;font-size:.99rem}
.toc .ar{margin-left:auto;color:var(--muted)}
.chap{display:flex;align-items:baseline;gap:10px;border-top:2px solid var(--brand);padding-top:14px;margin:30px 0 6px;scroll-margin-top:6px}
.chap .cn{font-size:.72rem;letter-spacing:.16em;font-weight:800;color:var(--brand);text-transform:uppercase}
.chap h3{font-size:1.4rem;margin:.08em 0;font-weight:850;flex:1 1 100%}
.chap .top{margin-left:auto;font-size:.8rem;text-decoration:none;color:var(--muted)}
img.pg{width:100%;display:block;aspect-ratio:1.333;object-fit:contain;background:#fff;border:1px solid var(--rule);border-radius:10px;margin:9px 0}
img.pg.loaded{aspect-ratio:auto}
.iq{background:var(--card);border:2px solid #FFD9A8;border-radius:18px;overflow:hidden;margin:12px 0;box-shadow:0 4px 16px rgba(20,30,50,.06)}
.iq img.vis{display:block;width:100%}
.qline{text-align:center;font-weight:800;font-size:1.12rem;margin:12px 10px 2px}
.opts{display:flex;gap:11px;justify-content:center;padding:10px 12px 6px;flex-wrap:wrap}
.opt{min-width:70px;height:58px;border:none;border-radius:15px;background:var(--c);color:#fff;font-size:1.6rem;font-weight:900;cursor:pointer;box-shadow:0 4px 0 rgba(0,0,0,.16)}
.opt:active{transform:translateY(2px);box-shadow:0 2px 0 rgba(0,0,0,.16)}
.opt.wide{min-width:0;width:auto;padding:0 18px;font-size:1.15rem;height:52px}
.opt.right{outline:4px solid var(--good);outline-offset:2px}
.opt.wrong{animation:shake .4s}
.oneans{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;padding:14px 12px 4px}
.oneans .lbl{font-weight:700;color:var(--muted)}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-7px)}75%{transform:translateX(7px)}}
.sentence{display:flex;align-items:center;justify-content:center;gap:9px;padding:16px 8px 4px}
.num{width:60px;height:60px;border:3px dashed #F4A23B;border-radius:13px;background:#FFFDF6;text-align:center;font-size:1.8rem;font-weight:900;color:var(--ink);outline:none}
.num:focus{border-color:var(--brand);border-style:solid}
.num.good{border:3px solid var(--good);background:#EAF7EF;color:var(--good)}
.num.bad{border:3px solid var(--bad);background:#FCEBEC;color:var(--bad)}
.op{font-size:1.7rem;font-weight:900}.op.plus{color:#E5484D}.op.minus{color:#1565C0}.op.eq{color:var(--ink)}
.row{display:flex;justify-content:center;padding:6px 12px 2px}
.check{background:var(--brand);color:#fff;border:none;border-radius:13px;padding:12px 26px;font-size:1.02rem;font-weight:800;cursor:pointer;box-shadow:0 4px 0 #C85A00}
.check:active{transform:translateY(2px);box-shadow:0 2px 0 #C85A00}
.fb{text-align:center;font-weight:800;font-size:1rem;min-height:1.4em;padding:7px 10px 14px}
.fb.good{color:var(--good)}.fb.bad{color:var(--bad)}
.endcap{text-align:center;color:var(--muted);font-size:.85rem;padding:40px 0 8px}
"""

SCRIPT = """
(function(){
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var im=e.target;
    if(im.dataset.src){im.src=im.dataset.src;im.removeAttribute('data-src');}
    im.addEventListener('load',function(){im.classList.add('loaded');});io.unobserve(im);}});},{rootMargin:'900px 0px'});
  document.querySelectorAll('img.pg[data-src]').forEach(function(im){io.observe(im);});
  document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');
    if(a){var el=document.getElementById(a.getAttribute('href').slice(1));if(el){e.preventDefault();el.scrollIntoView({behavior:'smooth',block:'start'});}}},false);
})();
function pick(btn){var opts=btn.closest('.opts');if(opts.dataset.done)return;var fb=btn.closest('.iq').querySelector('.fb');
  if(btn.dataset.ok==='1'){btn.classList.add('right');opts.dataset.done='1';fb.className='fb good';fb.textContent='🎉 Correct! Well done!';}
  else{btn.classList.add('wrong');setTimeout(function(){btn.classList.remove('wrong');},450);fb.className='fb bad';fb.textContent='❌ Oops — try again!';}}
function check(btn){var iq=btn.closest('.iq');var ins=iq.querySelectorAll('input.num'),ok=true,empty=false;
  ins.forEach(function(i){var v=i.value.trim();if(v==='')empty=true;
    if(v!==''&&parseInt(v,10)===parseInt(i.dataset.ans,10)){i.classList.remove('bad');i.classList.add('good');}
    else{i.classList.remove('good');if(v!=='')i.classList.add('bad');ok=false;}});
  var fb=iq.querySelector('.fb');
  if(empty){fb.className='fb';fb.textContent='✏️ Fill in all the boxes first!';return;}
  if(ok){fb.className='fb good';fb.textContent='🎉 Great job! That is correct!';}
  else{fb.className='fb bad';fb.textContent='❌ Not quite — fix the red boxes and check again!';}}
function multipick(btn){var opts=btn.closest('.opts');if(btn.dataset.tapped)return;
  var fb=btn.closest('.iq').querySelector('.fb');
  if(btn.dataset.ok==='1'){btn.classList.add('right');btn.dataset.tapped='1';
    var got=parseInt(opts.dataset.got)+1;opts.dataset.got=got;
    if(got>=parseInt(opts.dataset.need)){fb.className='fb good';fb.textContent='🎉 You found them all!';}
    else{fb.className='fb good';fb.textContent='✓ Yes! Keep looking…';}}
  else{btn.classList.add('wrong');setTimeout(function(){btn.classList.remove('wrong');},450);
    fb.className='fb bad';fb.textContent='❌ That one does not fit — try another!';}}
"""

def build():
    parts = [f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Number Sense &amp; Operations</title><style>{CSS}</style></head><body><div class="wrap">
<div class="cover" id="top"><div class="kick">Kiwimath · Interactive Workbook</div>
<h1>Number Sense<br>&amp; Operations</h1>
<div class="sub">Count · compare · add · subtract — tap and type your answers</div>
<svg width="190" height="80" viewBox="0 0 190 80" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="28" cy="40" r="20" fill="#FFE0B2"/><text x="28" y="49" font-size="24" font-weight="900" text-anchor="middle" fill="#E65100">1</text>
  <circle cx="74" cy="40" r="20" fill="#FFCC80"/><text x="74" y="49" font-size="24" font-weight="900" text-anchor="middle" fill="#E65100">2</text>
  <circle cx="120" cy="40" r="20" fill="#FFB74D"/><text x="120" y="49" font-size="24" font-weight="900" text-anchor="middle" fill="#fff">3</text>
  <circle cx="166" cy="40" r="20" fill="#FF9800"/><text x="166" y="49" font-size="22" font-weight="900" text-anchor="middle" fill="#fff">+</text>
</svg>
<div class="pill">13 chapters · tap &amp; type answers</div>
<div class="hint"><b>How it works.</b> Read each slide. On the question slides you can <b>tap the right answer</b> or <b>type the numbers and tap Check</b> — it tells you if you're right.</div>
</div><hr class="div"><h2 class="sec" id="contents">Chapters</h2><ul class="toc">''']
    for c in MAN:
        parts.append(f'<li><a href="#c{c["idx"]}"><span class="num">{c["idx"]+1}</span>'
                     f'<span class="tt">{html.escape(c["title"])}</span><span class="ar">&rsaquo;</span></a></li>')
    parts.append("</ul>")
    interactive_count = 0
    for c in MAN:
        ci = c["idx"]
        parts.append(f'<div class="chap" id="c{ci}"><span class="cn">Chapter {ci+1}</span>'
                     f'<a class="top" href="#contents">&uarr; Chapters</a><h3>{html.escape(c["title"])}</h3></div>')
        first = True
        for p in range(c["pages"]):
            key = (ci, p+1)
            if key in INTERACTIVE:
                cfg = INTERACTIVE[key]
                t = cfg["t"]
                if t == "mcq":
                    parts.append(mcq_block(ci, p+1, cfg))
                elif t == "one":
                    parts.append(one_block(ci, p, cfg))
                elif t == "fill_sub":
                    parts.append(fillsub_block(ci, p, cfg))
                elif t == "multi":
                    parts.append(multi_block(ci, p+1, cfg))
                else:
                    parts.append(fill_block(ci, p+1, cfg))
                interactive_count += 1
            else:
                parts.append(faithful(ci, p, eager=first))
            first = False
        print(f"  chapter {ci+1}/13 done", flush=True)
    parts.append(f'<div class="endcap">End of Number Sense &amp; Operations · {len(MAN)} chapters</div></div>'
                 f'<script>{SCRIPT}</script></body></html>')
    out = "".join(parts)
    path = f"{NSB}/number-sense.html"
    open(path, "w", encoding="utf-8").write(out)
    repo_ns = os.path.abspath(os.path.join(_dir, "../number-sense"))
    os.makedirs(repo_ns, exist_ok=True)
    import shutil; shutil.copy(path, os.path.join(repo_ns, "number-sense.html"))
    print(f"written {path}  {os.path.getsize(path)/1e6:.1f} MB | chapters {len(MAN)} | interactive {interactive_count} | total slides {sum(c['pages'] for c in MAN)}")

if __name__ == "__main__":
    build()
