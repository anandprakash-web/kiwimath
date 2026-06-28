#!/usr/bin/env python3
"""Shared authoring helpers + SVG figure toolkit for the L2 math book."""
import html
from l2_figs import (compare, array_dots, factor_tree, fraction_bar, fraction_circle,
                     decimal_grid, frac_on_line, rect_fig, area_grid, polygon, solid,
                     cube_net, symmetry_fig, venn2, bar_chart, pictograph, pie,
                     magic_square, clock, spinner, balance, pattern_seq)

def esc(s): return html.escape(str(s))

import re as _re
def _safe(s):
    """Escape a stray '&' but KEEP real HTML entities (&#8722; &times; &hellip; …)
    so authors may use entities in captions/titles without them double-escaping."""
    return _re.sub(r'&(?!#[0-9]+;|#x[0-9a-fA-F]+;|[a-zA-Z][a-zA-Z0-9]*;)', '&amp;', str(s))


def fit_svgs(html):
    """Grow each <svg>'s viewBox so no <text> label is clipped past the edge.
    Only ever ENLARGES the visible window (changes viewBox min-x / width / height),
    so existing content never moves. Estimates text width generously to be safe."""
    def _fix(m):
        svg = m.group(0)
        vb = _re.search(r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)"', svg)
        if not vb:
            return svg
        minx, miny, W, Hh = map(float, vb.groups())
        L, R, B = minx, minx + W, miny + Hh
        for tm in _re.finditer(r'<text\b([^>]*)>(.*?)</text>', svg, _re.S):
            attr, inner = tm.group(1), tm.group(2)
            if 'rotate' in attr or 'transform' in attr:
                continue
            def gv(k, d):
                mm = _re.search(rf'{k}="([^"]*)"', attr); return mm.group(1) if mm else d
            try:
                x = float(gv('x', '0')); y = float(gv('y', '0')); fs = float(gv('font-size', '14'))
            except ValueError:
                continue
            anc = gv('text-anchor', 'start')
            txt = _re.sub(r'<[^>]+>', '', inner); txt = _re.sub(r'&[#a-zA-Z0-9]+;', 'x', txt).strip()
            if not txt:
                continue
            w = len(txt) * fs * 0.6
            x0 = x - w / 2 if anc == 'middle' else (x - w if anc == 'end' else x)
            L = min(L, x0 - 3); R = max(R, x0 + w + 3); B = max(B, y + fs * 0.35)
        nW, nH = R - L, max(Hh, B - miny)
        if L < minx - 1 or nW > W + 1 or nH > Hh + 1:
            svg = _re.sub(r'viewBox="[^"]*"', f'viewBox="{L:.0f} {miny:.0f} {nW:.0f} {nH:.0f}"', svg, count=1)
        return svg
    return _re.sub(r'<svg\b.*?</svg>', _fix, html, flags=_re.S)

GOLD, ORANGE, INK, SKY, GRASS, BERRY, PURPLE = "#E8A33D", "#FF6F00", "#2b2622", "#3B9CE6", "#39A85B", "#E0556E", "#8B5CF6"

def svg(inner, w=460, h=200, vb=None):
    vb = vb or f"0 0 {w} {h}"
    return f'<svg class="fig" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" role="img">{inner}</svg>'

# ── figures ─────────────────────────────────────────────
def number_line(lo, hi, step=1, points=None, w=460):
    points = points or []
    x0, x1, y = 30, w - 30, 56
    n = (hi - lo) // step
    sx = (x1 - x0) / n
    s = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{INK}" stroke-width="2.5"/>',
         f'<polygon points="{x1},{y} {x1-9},{y-5} {x1-9},{y+5}" fill="{INK}"/>']
    for i in range(n + 1):
        v = lo + i * step; x = x0 + i * sx
        s.append(f'<line x1="{x:.0f}" y1="{y-7}" x2="{x:.0f}" y2="{y+7}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<text x="{x:.0f}" y="{y+24}" text-anchor="middle" font-size="14" fill="{INK}">{v}</text>')
    for v, lab, col in points:
        x = x0 + (v - lo) / step * sx
        s.append(f'<circle cx="{x:.0f}" cy="{y}" r="8" fill="{col}"/>')
        s.append(f'<text x="{x:.0f}" y="{y-15}" text-anchor="middle" font-size="14" font-weight="700" fill="{col}">{esc(lab)}</text>')
    return svg("".join(s), w, 86)

def pv_table(num, cols=("Thousands", "Hundreds", "Tens", "Ones")):
    digs = str(num).rjust(len(cols), " ")
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = "".join(f'<td>{d.strip() or ""}</td>' for d in digs)
    return f'<table class="pv"><tr>{head}</tr><tr class="big">{body}</tr></table>'

def base_ten(h=0, t=0, o=0):
    s, x = [], 12
    for _ in range(h):  # hundred-flat = true 10x10 grid of tiny squares
        s.append(f'<rect x="{x}" y="12" width="50" height="50" fill="{SKY}22" stroke="{SKY}" stroke-width="1.6"/>')
        for k in range(1, 10):
            s.append(f'<line x1="{x+k*5:.1f}" y1="12" x2="{x+k*5:.1f}" y2="62" stroke="{SKY}" stroke-width=".5" opacity=".6"/>')
            s.append(f'<line x1="{x}" y1="{12+k*5:.1f}" x2="{x+50}" y2="{12+k*5:.1f}" stroke="{SKY}" stroke-width=".5" opacity=".6"/>')
        x += 62
    for _ in range(t):  # ten-stick = 1x10 column
        s.append(f'<rect x="{x}" y="12" width="11" height="50" fill="{GRASS}30" stroke="{GRASS}" stroke-width="1.4"/>')
        for k in range(1, 10):
            s.append(f'<line x1="{x}" y1="{12+k*5:.1f}" x2="{x+11}" y2="{12+k*5:.1f}" stroke="{GRASS}" stroke-width=".5" opacity=".6"/>')
        x += 19
    x += 6
    for _ in range(o):  # ones = single squares
        s.append(f'<rect x="{x}" y="51" width="11" height="11" fill="{BERRY}44" stroke="{BERRY}" stroke-width="1.3"/>')
        x += 16
    return svg("".join(s), max(x + 12, 180), 76)

def place_arrows(num):
    """Show a number with its digits' place values pulled apart (expanded form)."""
    digs = str(num)
    names = ["Ones", "Tens", "Hundreds", "Thousands", "Ten-thousands"]
    n = len(digs); sp = 84
    W = max((n - 1) * sp + 140, 380); cx = (W - (n - 1) * sp) / 2
    s = []
    for i, d in enumerate(digs):
        place = n - 1 - i
        x = cx + i * sp
        col = [BERRY, GRASS, SKY, ORANGE, PURPLE][place % 5]
        s.append(f'<text x="{x:.0f}" y="40" text-anchor="middle" font-size="34" font-weight="800" font-family="Georgia,serif" fill="{col}">{d}</text>')
        val = int(d) * (10 ** place)
        s.append(f'<text x="{x:.0f}" y="74" text-anchor="middle" font-size="11" fill="{col}">{names[place]}</text>')
        s.append(f'<text x="{x:.0f}" y="92" text-anchor="middle" font-size="13" font-weight="700" fill="{col}">{val}</text>')
    return svg("".join(s), W, 104)

# ── prose blocks ────────────────────────────────────────
def H(t): return f'<h3 class="ch-h">{_safe(t)}</h3>'
def P(t): return f'<p>{t}</p>'
def kiwi(t): return f'<div class="kiwi"><span class="kbird">🥝</span><div>{t}</div></div>'
def big_q(t): return f'<div class="bigq"><span>BIG QUESTION</span>{t}</div>'
def figure(svg_str, cap=""): return f'<figure>{svg_str}{f"<figcaption>{_safe(cap)}</figcaption>" if cap else ""}</figure>'
def example(title, body): return f'<div class="eg"><div class="eg-t">✏️ Worked example — {_safe(title)}</div>{body}</div>'
def steps(items): return "<ol class='steps'>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"
def tryit(prompt, answer):
    return (f'<div class="try"><div class="try-q"><b>Your turn.</b> {prompt}</div>'
            f'<details><summary>Show answer</summary><div class="ans">{answer}</div></details></div>')
def practice(level, items):
    lis = "".join(f'<li>{q} <details><summary>answer</summary> <span class="ans">{a}</span></details></li>' for q, a in items)
    return f'<div class="pr"><div class="pr-l">{esc(level)}</div><ol class="pr-list">{lis}</ol></div>'
def challenge(body): return f'<div class="chal"><div class="chal-t">⭐ Challenge</div>{body}</div>'
def trap(body): return f'<div class="trap"><div class="trap-t">⚠️ Common mistake</div>{body}</div>'
