#!/usr/bin/env python3
"""Big SVG figure toolkit for the L2 math book. All exact-vector, kid-friendly.
Imported into l2_helpers so chapters get every figure from one place."""
import math
INK, SKY, GRASS, BERRY, ORANGE, GOLD, PURPLE = "#2b2622", "#3B9CE6", "#39A85B", "#E0556E", "#FF6F00", "#E8A33D", "#8B5CF6"

def _svg(inner, w, h):
    return f'<svg class="fig" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">{inner}</svg>'

def _t(x, y, s, size=14, col=INK, anchor="middle", w=600):
    return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-size="{size}" font-weight="{w}" fill="{col}">{s}</text>'

# ── numbers / arithmetic ───────────────────────────────
def compare(a, b):
    sign = "&gt;" if a > b else ("&lt;" if a < b else "=")
    col = GRASS if a != b else GOLD
    s = [_t(110, 56, str(a), 34, SKY, w=800), _t(230, 60, sign, 40, col, w=800),
         _t(350, 56, str(b), 34, BERRY, w=800)]
    return _svg("".join(s), 460, 86)

def array_dots(rows, cols, col=ORANGE):
    s, r = [], 11
    for i in range(rows):
        for j in range(cols):
            s.append(f'<circle cx="{24+j*30}" cy="{20+i*30}" r="{r}" fill="{col}55" stroke="{col}" stroke-width="1.6"/>')
    return _svg("".join(s), cols*30+30, rows*30+18)

def factor_tree(n, a, b, a2=None, b2=None, c2=None, d2=None):
    """Simple 2-level factor tree: n -> a,b ; optionally a->a2,b2 and b->c2,d2."""
    s = [_t(150, 28, str(n), 22, INK, w=800)]
    s += [f'<line x1="138" y1="36" x2="86" y2="64" stroke="{INK}" stroke-width="1.6"/>',
          f'<line x1="162" y1="36" x2="214" y2="64" stroke="{INK}" stroke-width="1.6"/>']
    ca = ORANGE if a2 else GRASS; cb = ORANGE if c2 else GRASS
    s += [_t(80, 80, str(a), 19, ca, w=800), _t(220, 80, str(b), 19, cb, w=800)]
    h = 104
    if a2:
        s += [f'<line x1="72" y1="88" x2="46" y2="112" stroke="{INK}" stroke-width="1.4"/>',
              f'<line x1="88" y1="88" x2="114" y2="112" stroke="{INK}" stroke-width="1.4"/>',
              _t(42, 128, str(a2), 18, GRASS, w=800), _t(114, 128, str(b2), 18, GRASS, w=800)]
        h = 150
    if c2:
        s += [f'<line x1="212" y1="88" x2="186" y2="112" stroke="{INK}" stroke-width="1.4"/>',
              f'<line x1="228" y1="88" x2="254" y2="112" stroke="{INK}" stroke-width="1.4"/>',
              _t(182, 128, str(c2), 18, GRASS, w=800), _t(254, 128, str(d2), 18, GRASS, w=800)]
        h = 150
    return _svg("".join(s), 300, h)

# ── fractions / decimals ───────────────────────────────
def fraction_bar(parts, shaded, w=360, col=ORANGE):
    cw = (w-20)/parts; s = []
    for i in range(parts):
        f = f"{col}66" if i < shaded else "#ffffff"
        s.append(f'<rect x="{10+i*cw:.1f}" y="14" width="{cw:.1f}" height="46" fill="{f}" stroke="{col}" stroke-width="1.8"/>')
    return _svg("".join(s), w, 76)

def fraction_circle(parts, shaded, col=ORANGE):
    cx, cy, r = 70, 70, 56; s = []
    for i in range(parts):
        a0 = -90 + i*360/parts; a1 = -90 + (i+1)*360/parts
        x0, y0 = cx+r*math.cos(math.radians(a0)), cy+r*math.sin(math.radians(a0))
        x1, y1 = cx+r*math.cos(math.radians(a1)), cy+r*math.sin(math.radians(a1))
        f = f"{col}66" if i < shaded else "#ffffff"
        s.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f} Z" fill="{f}" stroke="{col}" stroke-width="1.8"/>')
    return _svg("".join(s), 144, 144)

def decimal_grid(shaded, w=140):
    """10x10 grid with `shaded` little squares filled (for decimals / percent)."""
    s = [f'<rect x="8" y="8" width="120" height="120" fill="none" stroke="{SKY}" stroke-width="2"/>']
    for k in range(1, 10):
        s.append(f'<line x1="{8+k*12}" y1="8" x2="{8+k*12}" y2="128" stroke="{SKY}" stroke-width=".7" opacity=".55"/>')
        s.append(f'<line x1="8" y1="{8+k*12}" x2="128" y2="{8+k*12}" stroke="{SKY}" stroke-width=".7" opacity=".55"/>')
    for i in range(min(shaded, 100)):
        r, c = divmod(i, 10)
        s.append(f'<rect x="{8+c*12}" y="{8+r*12}" width="12" height="12" fill="{SKY}66"/>')
    return _svg("".join(s), 136, 136)

def frac_on_line(den, num, w=440):
    pts = [(i/den, f"{i}/{den}" if 0 < i < den else ("0" if i == 0 else "1"), INK) for i in range(den+1)]
    x0, x1, y = 30, w-30, 50
    s = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{INK}" stroke-width="2.5"/>']
    for v, lab, _ in pts:
        x = x0+v*(x1-x0)
        s.append(f'<line x1="{x:.0f}" y1="{y-7}" x2="{x:.0f}" y2="{y+7}" stroke="{INK}" stroke-width="2"/>')
        s.append(_t(x, y+24, lab, 13))
    xm = x0+num/den*(x1-x0)
    s.append(f'<circle cx="{xm:.0f}" cy="{y}" r="8" fill="{ORANGE}"/>')
    return _svg("".join(s), w, 80)

# ── geometry ───────────────────────────────────────────
def rect_fig(w_lab, h_lab, px=220, py=120, fill=SKY):
    s = [f'<rect x="60" y="24" width="{px}" height="{py}" fill="{fill}22" stroke="{fill}" stroke-width="2.4"/>',
         _t(60+px/2, 18, str(w_lab), 15, fill, w=800),
         _t(46, 24+py/2, str(h_lab), 15, fill, "end", w=800)]
    return _svg("".join(s), px+110, py+44)

def area_grid(cols, rows, unit="1 cm", fill=GRASS):
    c = 30; w = max(cols*c+20, 230); s = []
    for r in range(rows):
        for cc in range(cols):
            s.append(f'<rect x="{10+cc*c}" y="{10+r*c}" width="{c}" height="{c}" fill="{fill}" fill-opacity="0.13" stroke="{fill}" stroke-width="1.2"/>')
    s.append(f'<rect x="10" y="10" width="{cols*c}" height="{rows*c}" fill="none" stroke="{fill}" stroke-width="2.4"/>')
    s.append(_t(w/2, 10+rows*c+20, f"1 square = {unit} × {unit}", 12, INK))
    return _svg("".join(s), w, rows*c+36)

def polygon(points, labels=None, fill=PURPLE):
    """points=[(x,y)] in a ~0..1 box; labels on edges (optional list of str)."""
    W, H = 300, 200
    pts = [(40+x*(W-80), 30+y*(H-70)) for x, y in points]
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    s = [f'<polygon points="{poly}" fill="{fill}1f" stroke="{fill}" stroke-width="2.4"/>']
    if labels:
        n = len(pts)
        for i, lab in enumerate(labels):
            if not lab: continue
            x = (pts[i][0]+pts[(i+1) % n][0])/2; y = (pts[i][1]+pts[(i+1) % n][1])/2
            s.append(_t(x, y-6, str(lab), 14, fill, w=800))
    return _svg("".join(s), W, H)

def solid(kind="cube"):
    s = [];
    if kind in ("cube", "cuboid"):
        wdt = 130 if kind == "cube" else 170; dp = 36
        s = [f'<rect x="30" y="50" width="{wdt}" height="100" fill="{SKY}22" stroke="{SKY}" stroke-width="2"/>',
             f'<polygon points="30,50 {30+dp},20 {30+wdt+dp},20 {30+wdt},50" fill="{SKY}33" stroke="{SKY}" stroke-width="2"/>',
             f'<polygon points="{30+wdt},50 {30+wdt+dp},20 {30+wdt+dp},120 {30+wdt},150" fill="{SKY}18" stroke="{SKY}" stroke-width="2"/>']
        return _svg("".join(s), 30+wdt+dp+20, 170)
    if kind == "cone":
        s = [f'<ellipse cx="90" cy="140" rx="60" ry="16" fill="{GRASS}22" stroke="{GRASS}" stroke-width="2"/>',
             f'<path d="M30,140 L90,18 L150,140" fill="{GRASS}18" stroke="{GRASS}" stroke-width="2"/>']
        return _svg("".join(s), 180, 168)
    if kind == "cylinder":
        s = [f'<ellipse cx="90" cy="40" rx="50" ry="15" fill="{BERRY}33" stroke="{BERRY}" stroke-width="2"/>',
             f'<path d="M40,40 L40,140 A50,15 0 0 0 140,140 L140,40" fill="{BERRY}18" stroke="{BERRY}" stroke-width="2"/>',
             f'<ellipse cx="90" cy="140" rx="50" ry="15" fill="none" stroke="{BERRY}" stroke-width="2"/>']
        return _svg("".join(s), 180, 168)
    if kind == "sphere":
        s = [f'<circle cx="80" cy="80" r="62" fill="{ORANGE}22" stroke="{ORANGE}" stroke-width="2"/>',
             f'<ellipse cx="80" cy="80" rx="62" ry="20" fill="none" stroke="{ORANGE}" stroke-width="1.4" opacity=".6"/>']
        return _svg("".join(s), 168, 168)
    return _svg("", 160, 160)

def cube_net():
    c = 40; s = []
    cells = [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (1, 3)]
    for (cx, cy) in cells:
        s.append(f'<rect x="{20+cx*c}" y="{12+cy*c}" width="{c}" height="{c}" fill="{SKY}22" stroke="{SKY}" stroke-width="1.8"/>')
    return _svg("".join(s), 20+3*c+20, 12+4*c+12)

def symmetry_fig(kind="heart", lines=1):
    s = []
    if kind == "heart":
        s = [f'<path d="M100,150 C40,100 40,40 100,60 C160,40 160,100 100,150 Z" fill="{BERRY}22" stroke="{BERRY}" stroke-width="2.4"/>']
    elif kind == "tri":
        s = [f'<polygon points="100,30 50,150 150,150" fill="{GRASS}22" stroke="{GRASS}" stroke-width="2.4"/>']
    elif kind == "square":
        s = [f'<rect x="50" y="48" width="100" height="100" fill="{SKY}22" stroke="{SKY}" stroke-width="2.4"/>']
    s.append(f'<line x1="100" y1="20" x2="100" y2="160" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>')
    if lines >= 2:
        s.append(f'<line x1="40" y1="98" x2="160" y2="98" stroke="{ORANGE}" stroke-width="2" stroke-dasharray="6 5"/>')
    return _svg("".join(s), 200, 175)

# ── sets / data / logic ────────────────────────────────
def venn2(left, both, right, la="A", lb="B"):
    s = [f'<circle cx="103" cy="100" r="62" fill="{SKY}1f" stroke="{SKY}" stroke-width="2.2"/>',
         f'<circle cx="197" cy="100" r="62" fill="{BERRY}1f" stroke="{BERRY}" stroke-width="2.2"/>',
         _t(68, 106, str(left), 20, INK, w=800), _t(150, 106, str(both), 20, INK, w=800),
         _t(232, 106, str(right), 20, INK, w=800),
         _t(72, 30, la, 14, SKY, w=800), _t(228, 30, lb, 14, BERRY, w=800)]
    return _svg("".join(s), 300, 184)

def bar_chart(data, unit="", maxh=130):
    """data=[(label,value)]"""
    mx = max(v for _, v in data) or 1; bw = 46; gap = 22; x = 40
    s = [f'<line x1="32" y1="{maxh+18}" x2="{40+len(data)*(bw+gap)}" y2="{maxh+18}" stroke="{INK}" stroke-width="2"/>']
    cols = [SKY, GRASS, BERRY, ORANGE, PURPLE, GOLD]
    for i, (lab, v) in enumerate(data):
        h = v/mx*maxh; c = cols[i % len(cols)]
        s.append(f'<rect x="{x}" y="{maxh+18-h:.0f}" width="{bw}" height="{h:.0f}" fill="{c}99" stroke="{c}" stroke-width="1.6" rx="3"/>')
        s.append(_t(x+bw/2, maxh+18-h-6, str(v), 13, c, w=800))
        s.append(_t(x+bw/2, maxh+36, str(lab), 12))
        x += bw+gap
    return _svg("".join(s), 40+len(data)*(bw+gap)+10, maxh+46)

def pictograph(data, icon="⭐", per=1):
    s = []; y = 24
    for lab, v in data:
        s.append(_t(12, y+6, str(lab), 13, INK, "start", w=700))
        row = (icon+" ")*int(v)
        s.append(f'<text x="92" y="{y+8}" font-size="18" text-anchor="start">{row}</text>')
        y += 30
    s.append(_t(12, y+10, f"each {icon} = {per}", 11, "#8c8377", "start"))
    return _svg("".join(s), 380, y+22)

def pie(data):
    """data=[(label,value,color?)] -> circle graph."""
    cx, cy, r = 95, 95, 78; tot = sum(v for _, v in data) or 1; a = -90; s = []
    cols = [SKY, GRASS, BERRY, ORANGE, PURPLE, GOLD]
    for i, (lab, v) in enumerate(data):
        a1 = a + v/tot*360
        x0, y0 = cx+r*math.cos(math.radians(a)), cy+r*math.sin(math.radians(a))
        x1, y1 = cx+r*math.cos(math.radians(a1)), cy+r*math.sin(math.radians(a1))
        large = 1 if (a1-a) > 180 else 0
        s.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{cols[i%len(cols)]}aa" stroke="#fff" stroke-width="2"/>')
        am = math.radians((a+a1)/2)
        s.append(_t(cx+r*.6*math.cos(am), cy+r*.6*math.sin(am)+4, str(v), 13, "#fff", w=800))
        a = a1
    # legend
    ly = 24
    for i, (lab, v) in enumerate(data):
        s.append(f'<rect x="200" y="{ly}" width="14" height="14" fill="{cols[i%len(cols)]}aa"/>')
        s.append(_t(220, ly+12, str(lab), 13, INK, "start"))
        ly += 24
    return _svg("".join(s), 360, max(190, ly+10))

def magic_square(grid):
    """grid = 3x3 list; use '' or None for blanks."""
    c = 56; s = [f'<rect x="10" y="10" width="{3*c}" height="{3*c}" fill="none" stroke="{ORANGE}" stroke-width="2.4"/>']
    for k in (1, 2):
        s.append(f'<line x1="{10+k*c}" y1="10" x2="{10+k*c}" y2="{10+3*c}" stroke="{ORANGE}" stroke-width="1.6"/>')
        s.append(f'<line x1="10" y1="{10+k*c}" x2="{10+3*c}" y2="{10+k*c}" stroke="{ORANGE}" stroke-width="1.6"/>')
    for r in range(3):
        for col in range(3):
            v = grid[r][col]
            if v not in ("", None):
                s.append(_t(10+col*c+c/2, 10+r*c+c/2+8, str(v), 22, INK, w=800))
            else:
                s.append(_t(10+col*c+c/2, 10+r*c+c/2+8, "?", 22, BERRY, w=800))
    return _svg("".join(s), 3*c+20, 3*c+20)

def clock(h, m):
    cx, cy, r = 90, 90, 76; s = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2.6"/>']
    for k in range(12):
        a = math.radians(k*30-90)
        s.append(_t(cx+(r-14)*math.cos(a), cy+(r-14)*math.sin(a)+5, str(k or 12), 13, INK, w=700))
    ah = math.radians((h % 12)*30 + m*0.5 - 90); am = math.radians(m*6 - 90)
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+r*0.5*math.cos(ah):.0f}" y2="{cy+r*0.5*math.sin(ah):.0f}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    s.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+r*0.78*math.cos(am):.0f}" y2="{cy+r*0.78*math.sin(am):.0f}" stroke="{ORANGE}" stroke-width="3" stroke-linecap="round"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>')
    return _svg("".join(s), 180, 180)

def spinner(sectors):
    """sectors=[(label,color?)] equal slices."""
    cx, cy, r = 95, 95, 78; n = len(sectors); s = []
    cols = [SKY, GRASS, BERRY, ORANGE, PURPLE, GOLD]
    for i, lab in enumerate(sectors):
        a0 = -90+i*360/n; a1 = -90+(i+1)*360/n
        x0, y0 = cx+r*math.cos(math.radians(a0)), cy+r*math.sin(math.radians(a0))
        x1, y1 = cx+r*math.cos(math.radians(a1)), cy+r*math.sin(math.radians(a1))
        s.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f} Z" fill="{cols[i%len(cols)]}99" stroke="#fff" stroke-width="2"/>')
        am = math.radians((a0+a1)/2)
        s.append(_t(cx+r*.62*math.cos(am), cy+r*.62*math.sin(am)+4, str(lab), 13, "#fff", w=800))
    s.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{INK}"/>')
    s.append(f'<polygon points="{cx},{cy-r-4} {cx-7},{cy-r+10} {cx+7},{cy-r+10}" fill="{INK}"/>')
    return _svg("".join(s), 190, 190)

def balance(left, right, lab_l="", lab_r=""):
    tilt = 0 if left == right else (-6 if left > right else 6)
    s = [f'<polygon points="150,152 128,172 172,172" fill="{INK}"/>',
         f'<line x1="150" y1="58" x2="150" y2="154" stroke="{INK}" stroke-width="3"/>',
         f'<g transform="rotate({tilt} 150 58)">',
         f'<line x1="55" y1="58" x2="245" y2="58" stroke="{INK}" stroke-width="3"/>',
         f'<line x1="65" y1="58" x2="65" y2="80" stroke="{INK}" stroke-width="1.5"/>',
         f'<line x1="235" y1="58" x2="235" y2="80" stroke="{INK}" stroke-width="1.5"/>',
         f'<rect x="33" y="80" width="64" height="36" rx="7" fill="{SKY}33" stroke="{SKY}" stroke-width="2"/>',
         f'<rect x="203" y="80" width="64" height="36" rx="7" fill="{BERRY}33" stroke="{BERRY}" stroke-width="2"/>',
         _t(65, 103, str(lab_l or left), 16, INK, w=800), _t(235, 103, str(lab_r or right), 16, INK, w=800),
         '</g>']
    return _svg("".join(s), 300, 184)

def pattern_seq(items, q=True):
    """items=list of (text,color); draws boxes; q adds a '?' box at end."""
    s = []; x = 12; bw = 60
    seq = list(items) + ([("?", BERRY)] if q else [])
    for txt, col in seq:
        s.append(f'<rect x="{x}" y="14" width="{bw}" height="{bw}" rx="10" fill="{col}1f" stroke="{col}" stroke-width="2"/>')
        s.append(_t(x+bw/2, 14+bw/2+8, txt, 22, col, w=800))
        x += bw+14
    return _svg("".join(s), x, 92)
