import sys, os, re
sys.path.insert(0, '.')

# import the real build module (this runs its top-level: registers ch01)
import build_l2book as B

# register MY four chapters using the real chapter() collector + real OUTLINE
import l2_ch11_perimeter, l2_ch12_area, l2_ch13_shapes, l2_ch14_symmetry
l2_ch11_perimeter.build(B.chapter)
l2_ch12_area.build(B.chapter)
l2_ch13_shapes.build(B.chapter)
l2_ch14_symmetry.build(B.chapter)

# redirect OUT to a scratch dir so we don't touch the shipped book
_dir = os.path.dirname(os.path.abspath(__file__))
B.OUT = os.path.abspath(os.path.join(_dir, "_preview/_buildtest"))
B.render()

# validate the produced HTML
p = f"{B.OUT}/l2-mathbook.html"
doc = open(p).read()
print("\n--- VALIDATION ---")
print("file size:", os.path.getsize(p), "bytes")
for ch in (11,12,13,14):
    assert f'id="ch{ch}"' in doc, f"ch{ch} section missing from HTML"
    assert f'href="#ch{ch}"' in doc, f"ch{ch} TOC link missing"
print("all 4 chapter sections + TOC links present: OK")
# unbalanced tag sanity
for tag in ("details","figure","table","svg"):
    o, c = doc.count(f"<{tag}"), doc.count(f"</{tag}>")
    print(f"  <{tag}>={o}  </{tag}>={c}  {'OK' if o==c else 'MISMATCH!'}")
# ensure no python repr leaked (like un-rendered tuples)
assert "{{NAV}}" not in doc and "{{SECS}}" not in doc, "template placeholder left unfilled"
print("template fully rendered: OK")
