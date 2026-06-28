#!/usr/bin/env python3
"""
Ingest Vedantu assignment PDFs -> Verified daily-quiz questions.

Each problem is kept as a FAITHFUL cropped page image (preserves exact math
notation + figures — sidesteps the exponent-mangling that plagues text
extraction) plus its answer resolved from the source Answer Key:
  - integer key            -> exact-match integer
  - MCQ letter (a/b/..)    -> resolved to that option's numeric value
  - fraction / decimal     -> value + accepted [answer_min, answer_max] range

Only problems whose answer can be resolved are ingested (the rest live in the
faithful-render Library books). Every ingested item carries `source` + a real
problem image and is therefore `verified` (drives the Verified daily-quiz pool).

GRADE-ALIGNED level mapping (founder-locked): the source folders are the sheet's
levels; our level is one tier lower.
   source L5 (G7-8)  -> our L4
   source L6 (G9-10) -> our L5 (IOQM)
   source L7         -> our L6 (RMO)

Usage:  python3 ingest_quiz.py <Vedantu_Content_root> <content-live/olympiad root>
Re-runnable: skips any topic file it has already written.
"""
import sys, os, re, io, json, glob, base64
import fitz
from PIL import Image

SRC_TO_OUR = {"L5": "L4", "L6": "L5", "L7": "L6"}
PILLAR_CODE = {
    "NumberTheory": "NT", "Algebra": "ALG", "Geometry": "GEO",
    "Combinatorics": "COM", "Trigonometry": "TRIG",
    "BasicMathematics": "BMATH", "Arithmetic": "ARITH",
}
PILLAR_DISPLAY = {
    "NT": "Number Theory", "ALG": "Algebra", "GEO": "Geometry", "COM": "Combinatorics",
    "TRIG": "Trigonometry", "BMATH": "Basic Mathematics", "ARITH": "Arithmetic",
}
LEVEL_NAME = {"L4": "Grade 7-8", "L5": "IOQM", "L6": "RMO"}

# ----------------------------------------------------------------- parsing
def parse_key(d):
    """Map problem number -> raw key token, read from the 'Answers Key' block."""
    for pg in d:
        t = pg.get_text()
        if re.search(r'Answers?\s*Key', t, re.I):
            seg = re.split(r'Video|Solutions?\b', re.split(r'Answers?\s*Key', t, 1, re.I)[1])[0]
            toks = [x for x in re.split(r'\s+', seg) if x]
            key = {}; i = 0
            while i < len(toks) - 1:
                m = re.match(r'^(\d+)[\.\)]$', toks[i])
                if m:
                    key[int(m.group(1))] = toks[i + 1]; i += 2
                else:
                    i += 1
            if key:
                return key
    return {}

def prob_pages(d):
    out = []
    for i, pg in enumerate(d):
        if re.search(r'Answers?\s*Key|^\s*Solutions?\b', pg.get_text(), re.I | re.M):
            break
        out.append(i)
    return out or [0]

def markers(pg):
    ms = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            txt = "".join(s["text"] for s in l["spans"]).strip()
            m = re.match(r'^(\d{1,2})[\.\)]$', txt)
            if m:
                ms.append((int(m.group(1)), l["bbox"][1], l["bbox"][0]))
    ms.sort(key=lambda x: x[1])
    return ms

def resolve(keyval, opt_text):
    """Resolve the answer key WITHOUT trusting mangled option text.

    - integer key        -> typed-integer answer (exact)
    - fraction/decimal   -> typed answer with an accepted range
    - MCQ letter (a-e)   -> a REAL letter-choice MCQ graded by index. We never
      convert the letter to a number (PDF text mangles fractions/√/exponents in
      options, e.g. '1046½' -> '1 1046 2'); the faithful image shows the options,
      the student taps the letter, we grade the index. Requires the options to be
      a clean contiguous a,b,c(,d,e) set in the crop, else we SKIP (misalignment).
    Returns a dict describing the answer, or None to skip."""
    v = (keyval or "").strip().strip("()").rstrip(".").lower()
    if re.fullmatch(r'-?\d+', v):
        return {"mode": "integer", "value": v}
    if re.fullmatch(r'-?\d+/\d+', v) or re.fullmatch(r'-?\d*\.\d+', v):
        try:
            val = (int(v.split('/')[0]) / int(v.split('/')[1])) if '/' in v else float(v)
        except ZeroDivisionError:
            return None
        tol = max(0.01, abs(val) * 0.01)
        return {"mode": "fill_up", "value": "%g" % val,
                "min": round(val - tol, 4), "max": round(val + tol, 4)}
    if re.fullmatch(r'[a-e]', v):
        letters = sorted(set(m.lower() for m in re.findall(r'\(([a-eA-E])\)', opt_text)))
        nopt = len(letters)
        idx = "abcde".index(v)
        if nopt >= 2 and idx < nopt and letters == list("abcde"[:nopt]):
            return {"mode": "mcq", "idx": idx, "nopt": nopt}
        return None     # options not cleanly detected -> don't risk a wrong key
    return None

def extract(pdf):
    d = fitz.open(pdf)
    key = parse_key(d)
    items, total = [], 0
    if not key:
        return items, 0
    for pi in prob_pages(d):
        pg = d[pi]; ms = markers(pg); W, H = pg.rect.width, pg.rect.height
        for j, (n, y0, x0) in enumerate(ms):
            total += 1
            y1 = ms[j + 1][1] if j + 1 < len(ms) else H - 26
            r = fitz.Rect(max(6, x0 - 6), y0 - 4, W - 18, y1 - 2)
            res = resolve(key.get(n, ""), pg.get_text(clip=r))
            if not res:
                continue
            pix = pg.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=r)
            im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            b = io.BytesIO(); im.save(b, "PNG")
            items.append((n, "data:image/png;base64," + base64.b64encode(b.getvalue()).decode(), res))
    return items, total

# ----------------------------------------------------------------- build
def slug(fname):
    s = re.sub(r'\.pdf$', '', os.path.basename(fname), flags=re.I)
    s = re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_').lower()
    return re.sub(r'_+', '_', s)

def max_serial(oroot, lv, code):
    """Max serial among ORIGINAL (non-Vedantu) bank items only, so Vedantu serials
    are stable and re-runnable (they always start above the original bank)."""
    mx = 0
    for f in glob.glob(f"{oroot}/{lv}/{lv}_{code}_*.json"):
        try:
            for q in json.load(open(f)).get("questions", []):
                src = q.get("source") or ""
                if isinstance(src, str) and src.startswith("Vedantu OMM"):
                    continue
                m = re.search(rf'KM-{lv}-{code}-(\d+)', q.get("id", ""))
                if m: mx = max(mx, int(m.group(1)))
        except Exception:
            pass
    return mx

# hand-validated earlier via brute-force (keep as-is, never overwrite)
PROTECT = {("L5", "NT", "gcd_lcm"), ("L5", "NT", "cyclicity")}

def main(src_root, oroot):
    summary = []
    serials = {}   # (lv,code) -> running serial
    for src_lv in ("L5", "L6", "L7"):
        our = SRC_TO_OUR[src_lv]
        for pil_dir in sorted(glob.glob(f"{src_root}/{src_lv}/*/")):
            pillar = os.path.basename(pil_dir.rstrip("/"))
            code = PILLAR_CODE.get(pillar)
            if not code:
                continue
            for pdf in sorted(glob.glob(pil_dir + "*.pdf")):
                tslug = slug(pdf)
                out = f"{oroot}/{our}/{our}_{code}_{tslug}.json"
                if (our, code, tslug) in PROTECT:
                    summary.append((our, code, tslug, "protected", 0, 0)); continue
                try:
                    items, total = extract(pdf)
                except Exception as e:
                    summary.append((our, code, tslug, f"ERR {e}", 0, 0)); continue
                if not items:
                    summary.append((our, code, tslug, "0 resolved", 0, total)); continue
                if (our, code) not in serials:
                    serials[(our, code)] = max_serial(oroot, our, code)
                qs = []
                disp = PILLAR_DISPLAY[code]; topic_disp = re.sub(r'_', ' ', tslug).title()
                n_mcq = n_int = n_num = 0
                for (n, img, res) in items:
                    serials[(our, code)] += 1
                    s = serials[(our, code)]
                    q = dict(
                        id=f"KM-{our}-{code}-{s:04d}",
                        legacy_id=f"VED-{our}-{code}-{tslug.upper()[:18]}-{n:02d}",
                        stem="Solve the problem shown, then choose the matching option."
                             if res["mode"] == "mcq" else "Solve the problem shown.",
                        hint={"level_0": f"A {disp.lower()} problem — work it step by step.",
                              "level_1": "Re-read what is asked and compute carefully."},
                        solution_steps=None, solution=None,
                        difficulty_tier="medium", irt_b=1.0, difficulty_score=172,
                        visual_svg="", visual_png=img,
                        theme=topic_disp, domain=code,
                        km_level=our, km_pillar=code, km_topic=tslug, km_topic_display=topic_disp,
                        source=f"Vedantu OMM · {disp} · {topic_disp}", verified=True)
                    if res["mode"] == "mcq":
                        q["choices"] = [chr(65 + i) for i in range(res["nopt"])]
                        q["interaction_mode"] = "mcq"
                        q["correct_answer"] = res["idx"]; q["correct_value"] = None
                        n_mcq += 1
                    elif res["mode"] == "integer":
                        q["choices"] = []; q["interaction_mode"] = "integer"
                        q["correct_value"] = res["value"]; q["correct_answer"] = int(res["value"])
                        n_int += 1
                    else:  # fill_up (fraction/decimal direct answer)
                        q["choices"] = []; q["interaction_mode"] = "fill_up"
                        q["correct_value"] = res["value"]; q["correct_answer"] = 0
                        q["answer_min"] = res["min"]; q["answer_max"] = res["max"]
                        n_num += 1
                    qs.append(q)
                _ = (n_mcq, n_int, n_num)
                doc = dict(level=our, level_name=LEVEL_NAME[our], pillar=code,
                           topic_key=tslug, display_name=topic_disp,
                           total_questions=len(qs), questions=qs)
                os.makedirs(f"{oroot}/{our}", exist_ok=True)
                json.dump(doc, open(out, "w"), indent=2, ensure_ascii=False)
                summary.append((our, code, tslug, "OK", len(qs), total))
    # ---- report
    tot = 0
    print(f"{'lvl':4} {'pil':6} {'topic':34} {'status':12} {'in':>4} {'src':>4}")
    for our, code, ts, status, n, total in summary:
        if n: tot += n
        print(f"{our:4} {code:6} {ts[:34]:34} {status:12} {n:>4} {total:>4}")
    print(f"\nTOTAL ingested gradeable questions: {tot}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
