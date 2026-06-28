import sys, re, html
sys.path.insert(0, '.')

captured = []
def chapter(part, num, title, taxonomy, body):
    captured.append({"part": part, "num": num, "title": title, "tax": taxonomy, "body": body})

import l2_ch11_perimeter, l2_ch12_area, l2_ch13_shapes, l2_ch14_symmetry
for mod in (l2_ch11_perimeter, l2_ch12_area, l2_ch13_shapes, l2_ch14_symmetry):
    mod.build(chapter)

print("=== BUILD OK: %d chapters captured ===" % len(captured))
for c in captured:
    body = c["body"]
    n_fig = body.count("<figure>")
    n_svg = body.count("<svg")
    n_tbl = body.count("<table")
    # count questions: practice items (<li> inside .pr-list) + tryit + challenge
    n_pr_items = len(re.findall(r'<li>.*?<details><summary>answer', body))
    n_try = body.count('<div class="try">')
    n_chal = body.count('<div class="chal">')
    n_eg = body.count('<div class="eg">')
    n_levels = body.count('<div class="pr">')
    # tuple check
    print(f"\nCh{c['num']:>2} {c['title']!r}")
    print(f"   part={c['part']!r}")
    print(f"   tax ={c['tax']!r}")
    print(f"   figures(<figure>)={n_fig}  svgs={n_svg}  tables={n_tbl}")
    print(f"   practice-blocks={n_levels}  practice-Qs={n_pr_items}  tryit={n_try}  challenge={n_chal}  worked-examples={n_eg}")
    print(f"   TOTAL questions (practice+tryit+challenge) = {n_pr_items + n_try + n_chal}")
    # balance check: every <details> closed, body non-trivial
    assert body.count("<details>") == body.count("</details>"), f"unbalanced details in ch{c['num']}"
    assert len(body) > 3000, f"ch{c['num']} too short"

# render one real figure from the built bodies via cairosvg
import cairosvg
for c in captured:
    m = re.search(r'(<svg.*?</svg>)', c["body"], re.S)
    if m:
        svgstr = m.group(1)
        out = f"_preview/render_ch{c['num']}.png"
        cairosvg.svg2png(bytestring=svgstr.encode(), write_to=out, output_width=360)
        print(f"rendered first figure of ch{c['num']} -> {out}")
