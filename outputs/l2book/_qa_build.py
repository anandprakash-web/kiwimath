import sys, re
sys.path.insert(0, '.')

captured = []
def chapter(part, num, title, tax, body):
    captured.append({"part": part, "num": num, "title": title, "tax": tax, "body": body})

mods = ["l2_ch15_counting", "l2_ch16_probability", "l2_ch17_cryptarithms", "l2_ch18_venn"]
for name in mods:
    m = __import__(name)
    m.build(chapter)

print("=" * 70)
for c in sorted(captured, key=lambda c: c["num"]):
    body = c["body"]
    nfig = body.count("<figure>")
    # practice questions = <details> inside pr-list blocks
    prlists = re.findall(r'pr-list.*?</ol>', body, re.S)
    pq = sum(p.count("<details>") for p in prlists)
    ntry = body.count('class="try"')
    nchal = body.count('class="chal"')
    neg = body.count('class="eg"')
    # tryit/challenge contain answers too -> count as questions
    total_q = pq + ntry + nchal
    print(f"Ch{c['num']:>2} {c['title']:<32} | figs={nfig}  examples={neg}  "
          f"practiceQ={pq}  tryit={ntry}  challenge={nchal}  TOTAL_Q≈{total_q}")
    # sanity: ensure body has no None / no 'None' literal that signals a bug
    assert "None" not in body, f"Ch{c['num']} body contains literal None!"
    assert body.strip().startswith("<"), f"Ch{c['num']} body doesn't start with a tag"
    # verify Bloom ladder present
    for lvl in ["Remember", "Understand", "Apply", "Analyze", "Create"]:
        assert lvl in body, f"Ch{c['num']} missing Bloom level {lvl}"
    # taxonomy/part checks against the spec
print("=" * 70)
# exact tuple checks
expect = {
 15: ("Part 5 · Brain Benders","Counting & Combinations","Combinatorics · Brain Benders"),
 16: ("Part 5 · Brain Benders","Probability","Combinatorics · Probability"),
 17: ("Part 5 · Brain Benders","Cryptarithms & Magic Squares","Combinatorics · Brain Benders"),
 18: ("Part 5 · Brain Benders","Venn Diagrams","Combinatorics · Brain Benders"),
}
for c in captured:
    e = expect[c["num"]]
    assert (c["part"],c["title"],c["tax"])==e, f"TUPLE MISMATCH ch{c['num']}: {(c['part'],c['title'],c['tax'])} != {e}"
print("All chapter() tuples match the spec EXACTLY. ✓")
print("All Bloom ladders present, no None artifacts. ✓")
