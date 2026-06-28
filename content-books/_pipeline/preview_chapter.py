#!/usr/bin/env python3
"""Build a STANDALONE, tappable preview of ONE chapter for founder review.
Reuses assemble_ns.py's faithful renderer + CSS, and adds RICH game interactions:
  tapimg   : tap the correct picture (cards auto-detected via OpenCV)
  tapcount : tap a ten-frame dot for each object you count, then Check (answer N)
  dragnum  : drag numeral chips onto the box matching each count (set later)
  one/mcq/fill/...: fall back to assemble_ns.py blocks
Plus a per-chapter ⭐ star score that fills as the kid gets each one right.
"""
import os, importlib.util, html
import fitz, numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("A", os.path.join(HERE, "assemble_ns.py"))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
OUT = os.path.abspath(os.path.join(HERE, "../../outputs"))

# ---------------- card auto-detection (white option cards) --------------------
def detect_cards(ci, slide1, sc=2.0):
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    white = ((img[:,:,0]>232)&(img[:,:,1]>232)&(img[:,:,2]>232)).astype(np.uint8)*255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(white,8); A_=h*w; boxes=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]
        if area<0.03*A_ or bw<0.12*w or bh<0.12*h: continue
        if y<0.18*h and bh<0.2*h: continue
        boxes.append((x,y,bw,bh))
    boxes.sort(key=lambda b:(round(b[1]/(0.18*h)), b[0]))
    return [(x/w,y/h,bw/w,bh/h) for (x,y,bw,bh) in boxes]

def tapimg_block(ci, p, cfg):
    boxes = detect_cards(ci, p+1); bg = A.b64_cache(ci, p)
    hots = "".join(
        f'<button class="hot" style="left:{x*100:.2f}%;top:{y*100:.2f}%;width:{w*100:.2f}%;height:{h*100:.2f}%" '
        f'data-ok="{1 if i==cfg["ans"] else 0}" onclick="taphot(this)"></button>'
        for i,(x,y,w,h) in enumerate(boxes))
    return (f'<div class="iq tapimg"><div class="stage"><img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'{hots}</div><div class="fb">&nbsp;</div></div>')

def tapcount_block(ci, p, cfg):
    N = cfg["ans"]; bg = A.b64_cache(ci, p)
    dots = "".join(f'<button class="dot" onclick="ctdot(this)"></button>' for _ in range(10))
    return (f'<div class="iq tapcount" data-ans="{N}">'
            f'<img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'<div class="counter"><div class="cthint">👆 Tap one dot for each one you count</div>'
            f'<div class="tenframe">{dots}</div>'
            f'<div class="ctrow"><span class="ctnum">0</span>'
            f'<button class="ctreset" onclick="ctreset(this)" title="start over">↺</button>'
            f'<button class="check" onclick="ctcheck(this)">Check</button></div>'
            f'<div class="fb">&nbsp;</div></div></div>')

def detect_buttons(ci, slide1, sc=2.0):
    """Bottom-strip option buttons (Yes/No, or two colour buttons), left→right."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    white = ((img[:,:,0]>235)&(img[:,:,1]>235)&(img[:,:,2]>235)).astype(np.uint8)*255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((7,7),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(white,8); A_=h*w; out=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]
        if (y+bh/2)/h < 0.76: continue           # only the bottom button strip
        if area<0.004*A_ or bw<0.08*w or bh<0.04*h or bw>0.5*w: continue
        out.append((x/w,y/h,bw/w,bh/h))
    out.sort(key=lambda b:b[0])
    return out

def tapopt_block(ci, p, cfg):
    """Full faithful slide + tappable hotspots on the option buttons.
    Box source: explicit cfg['boxes'], else cfg['detect'] in {light,green,buttons}."""
    det = cfg.get("detect", "buttons")
    if cfg.get("boxes"):      boxes = cfg["boxes"]
    elif det == "light":      boxes = detect_light_regions(ci, p+1)
    elif det == "green":      boxes = detect_green_options(ci, p+1)
    else:                     boxes = detect_buttons(ci, p+1)
    bg = A.b64_cache(ci, p)
    def pad(b):
        x,y,w,h=b; dx,dy=w*0.14,h*0.22
        return (max(0,x-dx),max(0,y-dy),min(1,w+2*dx),min(1,h+2*dy))
    hots = "".join(
        f'<button class="hot" style="left:{x*100:.2f}%;top:{y*100:.2f}%;width:{w*100:.2f}%;height:{h*100:.2f}%" '
        f'data-ok="{1 if i==cfg["ans"] else 0}" onclick="taphot(this)"></button>'
        for i,(x,y,w,h) in enumerate(pad(b) for b in boxes))
    return (f'<div class="iq tapimg"><div class="stage"><img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'{hots}</div><div class="fb">&nbsp;</div></div>')

def detect_light_regions(ci, slide1, sc=2.0, ymin=0.18, ymax=0.95, min_w=0.10, min_h=0.07,
                         max_w=0.48, max_h=0.6):
    """Light option cards/buttons — WHITE or CREAM (high blue separates them from the
    yellow page). Use for cream cards + small white MCQ buttons the big-card detector misses."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    light = ((img[:,:,0]>230)&(img[:,:,1]>224)&(img[:,:,2]>185)).astype(np.uint8)*255
    light = cv2.morphologyEx(light, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(light,8); A_=h*w; out=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]; cy=(y+bh/2)/h
        if cy<ymin or cy>ymax: continue
        if bw<min_w*w or bh<min_h*h or bw>max_w*w or bh>max_h*h: continue
        if area<0.6*bw*bh: continue                      # roughly solid rectangle
        out.append((x/w,y/h,bw/w,bh/h))
    out.sort(key=lambda b: b[1]); rows=[]
    for b in out:
        if rows and abs(b[1]-rows[-1][-1][1]) < 0.08: rows[-1].append(b)
        else: rows.append([b])
    res=[]
    for row in rows: res.extend(sorted(row, key=lambda b: b[0]))
    return res

def detect_green_options(ci, slide1, sc=2.0):
    """Green option buttons/number-cards (word-problem options, circle-the-number), row-major."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    green = cv2.inRange(hsv, np.array([38,70,80]), np.array([88,255,255]))
    green = cv2.morphologyEx(green, cv2.MORPH_CLOSE, np.ones((11,11),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(green,8); A_=h*w; out=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]
        if area<0.004*A_ or bw<0.07*w or bh<0.035*h: continue
        if bw>0.45*w or bh>0.25*h: continue
        out.append((x/w,y/h,bw/w,bh/h))
    out.sort(key=lambda b:(round(b[1]/0.10), b[0]))
    return out

def tapgreen_block(ci, p, cfg):
    """Full faithful slide + tappable hotspots on the green option buttons/cards."""
    boxes = detect_green_options(ci, p+1); bg = A.b64_cache(ci, p)
    def pad(b):
        x,y,w,h=b; dx,dy=w*0.10,h*0.20
        return (max(0,x-dx),max(0,y-dy),min(1,w+2*dx),min(1,h+2*dy))
    hots = "".join(
        f'<button class="hot" style="left:{x*100:.2f}%;top:{y*100:.2f}%;width:{w*100:.2f}%;height:{h*100:.2f}%" '
        f'data-ok="{1 if i==cfg["ans"] else 0}" onclick="taphot(this)"></button>'
        for i,(x,y,w,h) in enumerate(pad(b) for b in boxes))
    return (f'<div class="iq tapimg"><div class="stage"><img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'{hots}</div><div class="fb">&nbsp;</div></div>')

def detect_answer_box(ci, slide1, sc=2.0):
    """The small EMPTY printed answer box (high white-fill, square-ish). Falls back
    to the template position if detection is unsure."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    white = ((img[:,:,0]>234)&(img[:,:,1]>234)&(img[:,:,2]>234)).astype(np.uint8)*255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((7,7),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(white,8); A_=h*w; cands=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]
        if area<0.006*A_ or bw<0.05*w or bh<0.05*h: continue
        if area>0.06*A_: continue                       # not the big picture card
        sub=img[y:y+bh, x:x+bw]
        wr=((sub[:,:,0]>234)&(sub[:,:,1]>234)&(sub[:,:,2]>234)).mean()
        ar=bw/bh
        if wr>0.9 and 0.7<ar<1.6:
            cands.append((area,(x/w,y/h,bw/w,bh/h)))
    if cands:
        cands.sort(); return cands[0][1]
    return (0.72,0.55,0.16,0.17)                        # template fallback

def count_block(ci, p, cfg):
    """Full faithful slide + a number input overlaid ON the printed answer box."""
    x,y,bw,bh = detect_answer_box(ci, p+1)
    bg = A.b64_cache(ci, p); N = cfg["ans"]
    inp = (f'<input class="boxin" style="left:{x*100:.2f}%;top:{y*100:.2f}%;width:{bw*100:.2f}%;height:{bh*100:.2f}%" '
           f'inputmode="numeric" pattern="[0-9]*" maxlength="2" data-ans="{N}" oninput="boxcheck(this)" aria-label="type the count">')
    return (f'<div class="iq count"><div class="stage"><img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'{inp}</div><div class="fb">👆 Count them, then tap the box and type the number</div></div>')

def detect_answer_boxes(ci, slide1, sc=2.0, ymin=0.2, ymax=0.85, min_white=0.0):
    """All small empty white answer boxes (multi-box fill), row-major. min_white>0
    keeps only near-empty boxes (used to pick blank cells out of a number strip)."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    white = ((img[:,:,0]>238)&(img[:,:,1]>238)&(img[:,:,2]>238)).astype(np.uint8)*255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((5,5),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(white,8); A_=h*w; out=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]; cy=(y+bh/2)/h
        if cy<ymin or cy>ymax: continue
        if area<0.002*A_ or area>0.03*A_ or bw<0.04*w or bh<0.04*h or bw>0.22*w: continue
        if min_white>0:
            sub=img[y:y+bh, x:x+bw]
            if ((sub[:,:,0]>238)&(sub[:,:,1]>238)&(sub[:,:,2]>238)).mean() < min_white: continue
        out.append((x/w,y/h,bw/w,bh/h))
    # robust row-major: group boxes into rows (y within tol), sort each row by x
    out.sort(key=lambda b: b[1]); rows=[]
    for b in out:
        if rows and abs(b[1]-rows[-1][-1][1]) < 0.07: rows[-1].append(b)
        else: rows.append([b])
    res=[]
    for row in rows: res.extend(sorted(row, key=lambda b: b[0]))
    return res

def multibox_block(ci, p, cfg):
    """Full faithful slide + a number input on each empty answer box (multi-fill)."""
    boxes = cfg.get("boxes") or detect_answer_boxes(ci, p+1, min_white=cfg.get("min_white", 0.0),
                                                    ymin=cfg.get("ymin",0.2), ymax=cfg.get("ymax",0.85))
    ans = cfg["ans"]; bg = A.b64_cache(ci, p)
    ins = "".join(
        f'<input class="boxin mb" style="left:{x*100:.2f}%;top:{y*100:.2f}%;width:{w*100:.2f}%;height:{h*100:.2f}%" '
        f'inputmode="numeric" pattern="[0-9]*" maxlength="2" data-ans="{a}" oninput="boxcheckmulti(this)">'
        for (x,y,w,h),a in zip(boxes, ans))
    return (f'<div class="iq count"><div class="stage"><img class="vis" src="data:image/webp;base64,{bg}" alt="">'
            f'{ins}</div><div class="fb">✏️ Type the missing numbers</div></div>')

def detect_cells(ci, slide1, k=3, sc=2.0):
    """The k largest white 'group' cells, row-major (for drag-match)."""
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc, sc))
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, 3).copy()
    h, w, _ = img.shape
    white = ((img[:,:,0]>232)&(img[:,:,1]>232)&(img[:,:,2]>232)).astype(np.uint8)*255
    white = cv2.morphologyEx(white, cv2.MORPH_CLOSE, np.ones((9,9),np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(white,8); A_=h*w; boxes=[]
    for i in range(1,n):
        x,y,bw,bh,area=stats[i]
        if area<0.02*A_ or bw<0.1*w or bh<0.085*h: continue
        if y<0.18*h and bh<0.16*h: continue
        if (y+bh/2) > 0.70*h: continue          # exclude the bottom number-chip strip
        boxes.append((x,y,bw,bh,area))
    boxes.sort(key=lambda b:-b[4]); boxes=boxes[:k]
    boxes.sort(key=lambda b:(round(b[1]/(0.18*h)), b[0]))
    return [(x/w,y/h,bw/w,bh/h) for (x,y,bw,bh,area) in boxes]

def _crop_b64(ci, slide1, frac, sc=2.4):
    import io, base64
    from PIL import Image
    x,y,w,h = frac
    d = fitz.open(f"{A.SRC}/{A.FILES[ci]}")
    rect = fitz.Rect(768*x, 576*y, 768*(x+w), 576*(y+h))
    pix = d[slide1-1].get_pixmap(matrix=fitz.Matrix(sc,sc), clip=rect)
    im = Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
    b=io.BytesIO(); im.save(b,"WEBP",quality=86,method=4); return base64.b64encode(b.getvalue()).decode()

def dragmatch_block(ci, p, cfg):
    import random
    counts = cfg["counts"]
    cells = cfg.get("cells_explicit") or detect_cells(ci, p+1, k=len(counts))
    cards = "".join(
        f'<div class="dm-cell"><img src="data:image/webp;base64,{_crop_b64(ci,p+1,frac)}" alt="">'
        f'<div class="dm-box" data-need="{cnt}"></div></div>'
        for frac, cnt in zip(cells, counts))
    rnd = random.Random(p*7+ci); order=list(range(len(counts))); rnd.shuffle(order)
    chips = "".join(f'<button class="dm-chip" data-v="{counts[i]}" onpointerdown="chipDown(event)">{counts[i]}</button>' for i in order)
    return (f'<div class="iq dragmatch"><div class="dm-q">👇 Drag each number onto the group that has that many</div>'
            f'<div class="dm-cells">{cards}</div><div class="dm-tray">{chips}</div><div class="fb">&nbsp;</div></div>')

def compare_block(ci, p, cfg):
    """Slide cropped to the two numbers/groups + box (printed sign tray dropped) +
    tap the correct < = > sign below."""
    ans = cfg["ans"]
    crop = cfg.get("crop", (0, 0, 768, 458))   # drop the bottom printed-sign strip
    img = A.b64_crop(ci, p+1, crop)
    btns = "".join(
        f'<button class="signbtn" data-ok="{1 if s==ans else 0}" onclick="picksign(this)">{html.escape(s)}</button>'
        for s in ["<", "=", ">"])
    return (f'<div class="iq compare"><img class="vis" src="data:image/webp;base64,{img}" alt="">'
            f'<div class="signrow">{btns}</div><div class="fb">&nbsp;</div></div>')

# ----------------------------- rich CSS + JS ----------------------------------
CSS_X = """
/* score bar */
.scorebar{position:sticky;top:0;z-index:20;background:linear-gradient(90deg,#FF6F00,#E5197D);color:#fff;
  text-align:center;font-weight:900;padding:8px 12px;font-size:1rem;letter-spacing:.02em;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.scorebar .star{filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
.scorebar.bump{animation:bump .35s}
@keyframes bump{0%{transform:scale(1)}45%{transform:scale(1.06)}100%{transform:scale(1)}}
/* tap-the-image hotspots */
.tapimg .stage{position:relative;display:block;line-height:0}
.tapimg .stage>img{display:block;width:100%}
.hot{position:absolute;background:transparent;border:none;padding:0;margin:0;cursor:pointer;border-radius:16px;
  -webkit-tap-highlight-color:transparent;outline:none;transition:transform .12s ease}
.hot::before{content:"";position:absolute;inset:4%;border-radius:14px;pointer-events:none;
  box-shadow:0 0 0 0 rgba(255,111,0,0);animation:invite 2.4s ease-in-out infinite}
@keyframes invite{0%,100%{box-shadow:0 0 0 0 rgba(255,111,0,0)}50%{box-shadow:0 0 0 5px rgba(255,111,0,.30)}}
.hot.right{transform:scale(1.04);z-index:3}
.hot.right::before{animation:none;box-shadow:0 0 0 6px var(--good),0 0 28px 8px rgba(46,158,91,.45)}
.hot.wrong{animation:shake .4s}.hot.wrong::before{animation:none;box-shadow:0 0 0 6px var(--bad)}
.hot .tick{position:absolute;right:-10px;top:-10px;width:42px;height:42px;border-radius:50%;background:var(--good);
  color:#fff;font-size:1.5rem;font-weight:900;display:flex;align-items:center;justify-content:center;
  box-shadow:0 3px 8px rgba(0,0,0,.25);transform:scale(0);animation:popin .35s .05s forwards}
@keyframes popin{to{transform:scale(1)}}
.spark{position:absolute;pointer-events:none;font-size:1.4rem;animation:fly .9s ease-out forwards;z-index:40}
@keyframes fly{0%{opacity:1;transform:translate(0,0) scale(.6)}100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(1.3)}}
/* tap-to-count */
.tapcount .counter{padding:8px 12px 4px}
.cthint{text-align:center;color:var(--muted);font-weight:700;font-size:.92rem;margin:2px 0 10px}
.tenframe{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;max-width:360px;margin:0 auto;
  background:#FFF6E9;border:2px solid #FFD9A8;border-radius:14px;padding:11px}
body.night .tenframe{background:#241a0e}
.dot{aspect-ratio:1;border-radius:50%;border:3px dashed #F4A23B;background:#fff;cursor:pointer;padding:0;
  -webkit-tap-highlight-color:transparent;transition:transform .12s}
body.night .dot{background:#1f232b}
.dot.on{background:radial-gradient(circle at 35% 30%,#FFB74D,#FF6F00);border:3px solid #E65100;animation:pop .3s}
.dot:active{transform:scale(.92)}
@keyframes pop{0%{transform:scale(.6)}60%{transform:scale(1.12)}100%{transform:scale(1)}}
.ctrow{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:12px}
.ctnum{min-width:54px;height:54px;border-radius:13px;background:var(--chip);color:var(--brand2);
  font-size:1.7rem;font-weight:900;display:flex;align-items:center;justify-content:center}
.ctreset{width:46px;height:46px;border-radius:50%;border:none;background:#EFE7DA;color:#8a6d3b;font-size:1.3rem;cursor:pointer}
/* drag-match (pick & drop) */
.dragmatch{padding:10px 12px 6px}
.dm-q{text-align:center;font-weight:800;font-size:1.02rem;margin:4px 0 12px}
.dm-cells{display:flex;gap:10px;justify-content:center;align-items:flex-start}
.dm-cell{flex:1 1 0;min-width:0;display:flex;flex-direction:column;align-items:center;gap:9px}
.dm-cell img{width:100%;border:1px solid var(--rule);border-radius:12px;background:#fff;display:block}
.dm-box{width:60px;height:60px;border:3px dashed #F4A23B;border-radius:14px;background:#FFFDF6;
  display:flex;align-items:center;justify-content:center;font-size:1.8rem;font-weight:900;color:var(--ink);transition:transform .12s}
.dm-box.over{border-color:var(--brand);background:#FFF0DD;transform:scale(1.08)}
.dm-box.filled{border:3px solid var(--good);background:#EAF7EF;color:var(--good)}
.dm-tray{display:flex;gap:14px;justify-content:center;margin:16px 0 4px;min-height:64px;flex-wrap:wrap}
.dm-chip{width:62px;height:62px;border-radius:50%;border:none;background:var(--brand);color:#fff;
  font-size:1.7rem;font-weight:900;cursor:grab;touch-action:none;box-shadow:0 5px 0 #C85A00;user-select:none;
  -webkit-user-select:none;-webkit-tap-highlight-color:transparent}
.dm-chip.drag{z-index:60;cursor:grabbing;box-shadow:0 12px 20px rgba(0,0,0,.32)}
.dm-chip.used{background:var(--good);box-shadow:0 5px 0 #1f7d44;opacity:.55;pointer-events:none}
/* >/</= compare */
.iq.compare{overflow:visible}
.compare img.vis{display:block;width:100%;border-radius:18px 18px 0 0}
.signrow{display:flex;gap:16px;justify-content:center;padding:16px 12px 8px}
.signbtn{width:78px;height:66px;border:none;border-radius:16px;background:var(--brand);color:#fff;
  font-size:2.1rem;font-weight:900;cursor:pointer;box-shadow:0 5px 0 #C85A00;line-height:1}
.signbtn:active{transform:translateY(2px);box-shadow:0 3px 0 #C85A00}
.signbtn.right{background:var(--good);box-shadow:0 5px 0 #1f7d44;transform:scale(1.08)}
.signbtn.wrong{animation:shake .4s}
/* in-place count input (sits on the printed answer box) */
.count .stage{position:relative;display:block;line-height:0}
.count .stage>img{display:block;width:100%}
.boxin{position:absolute;border:none;background:transparent;text-align:center;font-weight:900;color:#E65100;
  outline:none;border-radius:12px;padding:0;line-height:1;font-size:clamp(1.5rem,8.5vw,3rem);
  -webkit-tap-highlight-color:transparent;caret-color:#FF6F00;animation:boxpulse 2.2s ease-in-out infinite}
@keyframes boxpulse{0%,100%{box-shadow:0 0 0 0 rgba(255,111,0,0)}50%{box-shadow:0 0 0 4px rgba(255,111,0,.28)}}
.boxin:focus{animation:none;box-shadow:0 0 0 4px rgba(255,111,0,.55)}
.boxin.good{color:var(--good);animation:none;box-shadow:0 0 0 4px var(--good)}
.boxin.bad{color:var(--bad);animation:shake .4s;box-shadow:0 0 0 4px var(--bad)}
"""
JS_X = """
var GOT=0;
function bump(){var b=document.querySelector('.scorebar');if(b){b.classList.add('bump');setTimeout(function(){b.classList.remove('bump');},360);}}
function award(el){if(!el||el.dataset.scored)return;el.dataset.scored='1';GOT++;
  var s=document.getElementById('score');if(s)s.textContent=GOT;bump();
  var mx=document.getElementById('scoremax');
  if(mx&&GOT>=parseInt(mx.textContent,10)){var b=document.querySelector('.scorebar');if(b){b.innerHTML='🏆 You finished the chapter! ⭐ '+GOT+'/'+GOT;}}}
function celebrate(host){var em=['⭐','🎉','✨','🌟'];
  for(var i=0;i<10;i++){var s=document.createElement('span');s.className='spark';s.textContent=em[i%em.length];
    s.style.left=(20+Math.random()*60)+'%';s.style.top=(20+Math.random()*50)+'%';
    s.style.setProperty('--dx',(Math.random()*160-80)+'px');s.style.setProperty('--dy',(-40-Math.random()*120)+'px');
    host.appendChild(s);setTimeout((function(n){return function(){n.remove();};})(s),900);}}
function taphot(btn){var stage=btn.closest('.stage');if(stage.dataset.done)return;
  var iq=btn.closest('.iq'),fb=iq.querySelector('.fb');
  if(btn.dataset.ok==='1'){stage.dataset.done='1';btn.classList.add('right');
    var t=document.createElement('span');t.className='tick';t.textContent='✓';btn.appendChild(t);
    celebrate(stage);fb.className='fb good';fb.textContent='🎉 Yes! Great tapping!';award(iq);}
  else{btn.classList.add('wrong');setTimeout(function(){btn.classList.remove('wrong');},450);
    fb.className='fb bad';fb.textContent='👀 Not that one — try again!';}}
function ctcount(iq){return iq.querySelectorAll('.dot.on').length;}
function ctdot(btn){var iq=btn.closest('.iq');if(iq.dataset.scored)return;btn.classList.toggle('on');
  iq.querySelector('.ctnum').textContent=ctcount(iq);var fb=iq.querySelector('.fb');fb.className='fb';fb.textContent='\\u00a0';}
function ctreset(b){var iq=b.closest('.iq');if(iq.dataset.scored)return;
  iq.querySelectorAll('.dot.on').forEach(function(d){d.classList.remove('on');});iq.querySelector('.ctnum').textContent='0';}
function ctcheck(b){var iq=b.closest('.iq');if(iq.dataset.scored)return;var n=ctcount(iq),ans=parseInt(iq.dataset.ans,10);
  var fb=iq.querySelector('.fb');
  if(n===0){fb.className='fb';fb.textContent='👆 Tap the dots to count first!';return;}
  if(n===ans){fb.className='fb good';fb.textContent='🎉 '+ans+'! You counted them all!';celebrate(iq);award(iq);}
  else{fb.className='fb bad';fb.textContent=(n<ans?'Keep going — count again! 🔎':'Too many — count again! 🔎');}}
function boxcheck(inp){var iq=inp.closest('.iq');if(iq.dataset.scored)return;
  var ans=''+inp.dataset.ans;var v=inp.value.replace(/[^0-9]/g,'');inp.value=v;
  var fb=iq.querySelector('.fb');
  if(v===''){inp.classList.remove('bad','good');fb.className='fb';fb.textContent='👆 Count them, then type the number';return;}
  if(v===ans){inp.classList.remove('bad');inp.classList.add('good');inp.readOnly=true;inp.blur();
    celebrate(iq.querySelector('.stage'));fb.className='fb good';fb.textContent='🎉 '+ans+'! Well counted!';award(iq);}
  else if(v.length>=ans.length){inp.classList.remove('good');inp.classList.add('bad');
    fb.className='fb bad';fb.textContent='Not quite — count again! 🔎';}
  else{inp.classList.remove('bad','good');fb.className='fb';fb.textContent='👆 Keep going…';}}
function boxcheckmulti(inp){var iq=inp.closest('.iq');if(iq.dataset.scored)return;
  var v=inp.value.replace(/[^0-9]/g,'');inp.value=v;var ans=''+inp.dataset.ans;
  if(v===ans){inp.classList.remove('bad');inp.classList.add('good');inp.readOnly=true;}
  else if(v.length>=ans.length){inp.classList.remove('good');inp.classList.add('bad');}
  else{inp.classList.remove('good','bad');}
  var all=iq.querySelectorAll('input.boxin'),good=iq.querySelectorAll('input.boxin.good'),fb=iq.querySelector('.fb');
  if(good.length===all.length){fb.className='fb good';fb.textContent='🎉 All correct!';celebrate(iq.querySelector('.stage'));award(iq);}
  else{fb.className='fb';fb.textContent=good.length+' / '+all.length+' correct';}}
function picksign(btn){var iq=btn.closest('.iq');if(iq.dataset.scored)return;var fb=iq.querySelector('.fb');
  if(btn.dataset.ok==='1'){btn.classList.add('right');celebrate(iq);fb.className='fb good';fb.textContent='🎉 Correct!';award(iq);}
  else{btn.classList.add('wrong');setTimeout(function(){btn.classList.remove('wrong');},450);fb.className='fb bad';fb.textContent='❌ Try another sign!';}}
var DRAG=null;
function chipDown(e){var c=e.currentTarget||e.target;if(c.dataset.placed)return;e.preventDefault();
  DRAG={c:c,sx:e.clientX,sy:e.clientY};c.classList.add('drag');}
function _boxUnder(c,x,y){c.style.pointerEvents='none';var el=document.elementFromPoint(x,y);c.style.pointerEvents='';
  return el&&el.closest?el.closest('.dm-box'):null;}
document.addEventListener('pointermove',function(e){if(!DRAG)return;var c=DRAG.c;
  c.style.transform='translate('+(e.clientX-DRAG.sx)+'px,'+(e.clientY-DRAG.sy)+'px) scale(1.12)';
  var iq=c.closest('.iq');iq.querySelectorAll('.dm-box.over').forEach(function(b){b.classList.remove('over');});
  var box=_boxUnder(c,e.clientX,e.clientY);if(box&&!box.dataset.filled)box.classList.add('over');});
document.addEventListener('pointerup',function(e){if(!DRAG)return;var c=DRAG.c;DRAG=null;c.classList.remove('drag');
  var iq=c.closest('.iq');iq.querySelectorAll('.dm-box.over').forEach(function(b){b.classList.remove('over');});
  var box=_boxUnder(c,e.clientX,e.clientY);var fb=iq.querySelector('.fb');
  if(box&&!box.dataset.filled&&parseInt(box.dataset.need,10)===parseInt(c.dataset.v,10)){
    box.dataset.filled='1';box.textContent=c.dataset.v;box.classList.add('filled');
    c.dataset.placed='1';c.classList.add('used');c.style.transform='';
    fb.className='fb good';fb.textContent='✓ Nice match!';
    if(iq.querySelectorAll('.dm-box.filled').length===iq.querySelectorAll('.dm-box').length){
      fb.textContent='🎉 All matched!';celebrate(iq);award(iq);}
  }else{c.style.transition='transform .2s';c.style.transform='';setTimeout(function(){c.style.transition='';},220);
    if(box&&!box.dataset.filled){fb.className='fb bad';fb.textContent='❌ Not that group — try again!';}}});
"""

# ------------------------------ chapter configs -------------------------------
CFG0 = {
 # tap the correct picture (auto-detected; ans = card index, row-major)
 7:{"t":"tapimg","ans":2}, 11:{"t":"tapimg","ans":1}, 12:{"t":"tapimg","ans":0}, 13:{"t":"tapimg","ans":1},
 14:{"t":"tapimg","ans":1}, 19:{"t":"tapimg","ans":0}, 20:{"t":"tapimg","ans":1}, 21:{"t":"tapimg","ans":0},
 22:{"t":"tapimg","ans":0}, 27:{"t":"tapimg","ans":0}, 34:{"t":"tapimg","ans":1},
 60:{"t":"tapimg","ans":1}, 66:{"t":"tapimg","ans":0},   # 9 crayons = LEFT (founder-confirmed)
 # count & write — type the number IN the printed answer box (answer = section number)
 10:{"t":"count","ans":1}, 18:{"t":"count","ans":2}, 26:{"t":"count","ans":3},
 33:{"t":"count","ans":4}, 40:{"t":"count","ans":5}, 41:{"t":"count","ans":5},
 46:{"t":"count","ans":6}, 47:{"t":"count","ans":6}, 52:{"t":"count","ans":7},
 53:{"t":"count","ans":7}, 58:{"t":"count","ans":8}, 59:{"t":"count","ans":8},
 64:{"t":"count","ans":9}, 65:{"t":"count","ans":9}, 70:{"t":"count","ans":10}, 71:{"t":"count","ans":10},
 # match-the-number (PICK & DROP / drag-match): drag each number onto its group
 28:{"t":"dragmatch","counts":[1,2,3]},          # apple rows 1,2,3
 36:{"t":"dragmatch","counts":[4,3,2]},          # books L→R (founder-confirmed)
 42:{"t":"dragmatch","counts":[2,5,3]},          # oranges rows top→bottom
 48:{"t":"dragmatch","counts":[6,4,3]},          # carrots L→R (founder-confirmed)
 54:{"t":"dragmatch","counts":[5,7,4]},          # tomatoes/blueberries/strawberries (confirmed)
 72:{"t":"dragmatch","counts":[7,10,8]},         # tubes/coins/candies L→R (founder-confirmed)
 # basket slides: drag the numbers onto the fruit group with that many (cells = the groups)
 35:{"t":"dragmatch","counts":[2,4,1,3],          # cherry/apples/banana/oranges (confirmed)
     "cells_explicit":[(0.07,0.67,0.18,0.27),(0.27,0.67,0.21,0.27),(0.52,0.67,0.19,0.27),(0.72,0.67,0.21,0.27)]},
 29:{"t":"dragmatch","counts":[3,1,2],            # cherry groups L→R (founder-confirmed)
     "cells_explicit":[(0.07,0.68,0.26,0.22),(0.40,0.68,0.20,0.22),(0.66,0.68,0.26,0.22)]},
}

CFG1 = {  # c01 Number Comparison (1–10)
 # Are there enough? — tap Yes / No  (Yes=idx0 left, No=idx1 right)
 7:{"t":"tapopt","ans":1},   # No  (3 leaves < 5 snails)
 8:{"t":"tapopt","ans":0},   # Yes (3 tulips = 3 butterflies)
 9:{"t":"tapopt","ans":1},   # No  (1 carrot < 3 snowmen)
 10:{"t":"tapopt","ans":1},  # No  (2 brushes < 4 cups)
 11:{"t":"tapopt","ans":0},  # Yes (2 forks >= 1 plate)
 # Which group has more/fewer — tap the correct group card (left=0, right=1)
 14:{"t":"tapimg","ans":1},  # more: 3 brushes > 1 bucket
 15:{"t":"tapimg","ans":0},  # fewer: 1 cushion < 2 rolls
 16:{"t":"tapimg","ans":0},  # more: 3 ladybugs > 1 leaf
 17:{"t":"tapimg","ans":0},  # more: 3 balls > 2 chairs
 18:{"t":"tapimg","ans":0},  # fewer: 1 drum < 3 rockets
 19:{"t":"tapimg","ans":1},  # more: 5 > 3 dots
 20:{"t":"tapimg","ans":0},  # more: 4 > 2 dots
 21:{"t":"tapimg","ans":1},  # more: 3 > 1 dots
 22:{"t":"tapimg","ans":0},  # fewer: 2 < 5 dots
 23:{"t":"tapimg","ans":0},  # fewer: 2 < 4 dots
 # Fewer dots — tap the colour button (left=0, right=1)
 26:{"t":"tapopt","ans":0},  # fewer green (9 < 10 pink) — CONFIRM (close)
 27:{"t":"tapopt","ans":0},  # fewer grey (3 < 4 green)
 28:{"t":"tapopt","ans":0},  # fewer blue (founder-confirmed; blue is left button)
 29:{"t":"tapopt","ans":1},  # fewer grey (8 grey < 10 blue); grey is right button
 # Fewer/more/same than — tap Yes / No
 30:{"t":"tapopt","ans":1},  # No  (1 mug = 1 marshmallow, not fewer)
 31:{"t":"tapopt","ans":1},  # No  (1 tie = 1 shirt)
 32:{"t":"tapopt","ans":1},  # No  (2 leaves > 1 snail)
 33:{"t":"tapopt","ans":0},  # Yes (3 lids > 1 cup)
 34:{"t":"tapopt","ans":1},  # No  (1 tie != 2 shirts)
 # Compare Two Numbers — tap the larger / largest / smallest number card
 37:{"t":"tapimg","ans":1},38:{"t":"tapimg","ans":1},39:{"t":"tapimg","ans":0},40:{"t":"tapimg","ans":1},
 41:{"t":"tapimg","ans":2},42:{"t":"tapimg","ans":1},43:{"t":"tapimg","ans":0},44:{"t":"tapimg","ans":1},
}

CFG2 = {  # c02 Number Comparison & Sequencing (1–20) — compare section first
 # >/</= : tap the correct comparison sign
 15:{"t":"compare","ans":">"},  # 8 > 5
 16:{"t":"compare","ans":">"},  # 7 > 2
 29:{"t":"compare","ans":"<"},  # 4 < 6
 30:{"t":"compare","ans":"<"},  # 6 < 17
 31:{"t":"compare","ans":">"},  # 18 > 8
 34:{"t":"compare","ans":"<"},  # 4 < 6
 35:{"t":"compare","ans":"<"},  # 6 < 17
 36:{"t":"compare","ans":">"},  # 18 > 8
 37:{"t":"compare","ans":">"},  # 19 > 16
 # count-the-blocks then sign (which side has more) — CONFIRM block counts
 26:{"t":"compare","ans":"<"},  # 6 < 8
 27:{"t":"compare","ans":">"},  # 6 > 5
 32:{"t":"compare","ans":"<"},  # 6 < 8
 33:{"t":"compare","ans":">"},  # 8 > 4
 # Word problems — tap the correct option (green buttons; left=0,right=1)
 47:{"t":"tapgreen","ans":0},  # Jenny (19 < 20 min)
 48:{"t":"tapgreen","ans":0},  # Lila (14 > 13)
 49:{"t":"tapgreen","ans":0},  # Plate A (12 < 20)
 50:{"t":"tapgreen","ans":1},  # Team B (7 > 5)
 # Circle the smallest/biggest/<14 — tap the green number card (row-major: TL,TR,mid,BL,BR)
 79:{"t":"tapgreen","ans":4},  # smallest 10 (BR)
 80:{"t":"tapgreen","ans":1},  # biggest 14 (TR)
 42:{"t":"tapgreen","ans":4},  # 12 < 14 (BR)
 # Which-more / MCQ — tap the card (explicit boxes)
 24:{"t":"tapopt","ans":1,"boxes":[(0.06,0.34,0.40,0.43),(0.52,0.34,0.40,0.43)]},   # right crate more apples (verified)
 25:{"t":"tapopt","ans":0,"detect":"light"},   # left cap fewer dots (cards auto-detected)
 40:{"t":"tapopt","ans":2,"detect":"light"},   # C.16 (>15)  (buttons auto-detected)
 41:{"t":"tapopt","ans":1,"detect":"light"},   # B.15 (>13)  (buttons auto-detected)
 # Write before/after/between — multi-box type-in (boxes detected row-major)
 60:{"t":"multibox","ans":[19,16,5,3]},    # before 20,17,6,4
 61:{"t":"multibox","ans":[20,11,8,7]},    # after 19,10,7,6
 62:{"t":"multibox","ans":[12,17,6,10]},   # between 11-13,16-18,5-7,9-11
 # last comparison signs (count blocks/pencils)
 12:{"t":"compare","ans":">"},  # 4 > 2 blocks
 13:{"t":"compare","ans":">"},  # 3 > 2 (guided example)
 14:{"t":"compare","ans":"<"},  # 3 < 5 pencils
 # drag the correct number -> tap the chip greater than 17
 43:{"t":"tapgreen","ans":2},   # 19 (>17); chips 13,17,19,8
 # ordering: write the 3 numbers in order (multi-box, top row)
 75:{"t":"multibox","ans":[7,8,9],"ymax":0.6},     # smallest→biggest 9,7,8
 76:{"t":"multibox","ans":[18,15,11],"ymax":0.6},  # biggest→smallest 11,15,18
 77:{"t":"multibox","ans":[5,12,14],"ymax":0.6},   # smallest→biggest 12,5,14
 78:{"t":"multibox","ans":[20,14,6],"ymax":0.6},   # biggest→smallest 14,6,20
 # left faithful (note): 56-58 strip-fill (cells connected, can't isolate), 28 balloon-count,
 # 45 expression-compare, 39 circle-bigger-in-each-pair, 44 dup, 70-73 ordering teaching slides
}

CONFIGS = {0: CFG0, 1: CFG1, 2: CFG2}
BUILD_CI = 2                       # which chapter this run previews
CI, CFG = BUILD_CI, CONFIGS[BUILD_CI]

def build():
    chap = next(c for c in A.MAN if c["idx"] == CI)
    title = chap["title"]; pages = chap["pages"]; n_int = len(CFG)
    parts = [f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>PREVIEW · {html.escape(title)}</title><style>{A.CSS}{CSS_X}</style></head><body>
<div class="scorebar"><span class="star">⭐</span> <span id="score">0</span>/<span id="scoremax">{n_int}</span></div>
<div class="wrap">
<div class="chap" id="c{CI}"><span class="cn">Chapter {CI+1} · {n_int} interactive</span><h3>{html.escape(title)}</h3></div>''']
    first = True
    for p in range(pages):
        s1 = p+1; cfg = CFG.get(s1)
        if cfg:
            t = cfg["t"]
            if t == "tapimg":    parts.append(tapimg_block(CI, p, cfg))
            elif t == "tapopt":  parts.append(tapopt_block(CI, p, cfg))
            elif t == "tapgreen":parts.append(tapgreen_block(CI, p, cfg))
            elif t == "count":   parts.append(count_block(CI, p, cfg))
            elif t == "tapcount":parts.append(tapcount_block(CI, p, cfg))
            elif t == "dragmatch":parts.append(dragmatch_block(CI, p, cfg))
            elif t == "compare": parts.append(compare_block(CI, p, cfg))
            elif t == "multibox":parts.append(multibox_block(CI, p, cfg))
            elif t == "one":     parts.append(A.one_block(CI, p, cfg))
            elif t == "mcq":     parts.append(A.mcq_block(CI, s1, cfg))
            elif t == "fill_sub":parts.append(A.fillsub_block(CI, p, cfg))
            elif t == "multi":   parts.append(A.multi_block(CI, s1, cfg))
            else:                parts.append(A.fill_block(CI, s1, cfg))
        else:
            parts.append(A.faithful(CI, p, eager=first))
        first = False
    parts.append(f'<div class="endcap">End of preview · {title}</div></div><script>{A.SCRIPT}{JS_X}</script></body></html>')
    out = "".join(parts)
    path = os.path.join(OUT, f"c{CI:02d}_preview.html")
    open(path, "w", encoding="utf-8").write(out)
    print(f"wrote {path}  {os.path.getsize(path)/1e6:.1f} MB | {n_int} interactive / {pages} slides")

if __name__ == "__main__":
    build()
