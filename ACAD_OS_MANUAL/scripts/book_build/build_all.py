#!/usr/bin/env python3
import time, os, subprocess, sys
START=time.time(); BUDGET=float(sys.argv[1]) if len(sys.argv)>1 else 33
_dir = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(_dir, "../../content-books"))
M=[
 ("L5","NumberTheory","Number Theory","IOQM","ioqm-numbertheory"),
 ("L5","Algebra","Algebra","IOQM","ioqm-algebra"),
 ("L5","Arithmetic","Arithmetic","IOQM","ioqm-arithmetic"),
 ("L5","Combinatorics","Combinatorics","IOQM","ioqm-combinatorics"),
 ("L5","Geometry","Geometry","IOQM","ioqm-geometry"),
 ("L6","NumberTheory","Number Theory","RMO","rmo-numbertheory"),
 ("L6","Algebra","Algebra","RMO","rmo-algebra"),
 ("L6","BasicMathematics","Basic Mathematics","RMO","rmo-basicmaths"),
 ("L6","Combinatorics","Combinatorics","RMO","rmo-combinatorics"),
 ("L6","Geometry","Geometry","RMO","rmo-geometry"),
 ("L6","Trigonometry","Trigonometry","RMO","rmo-trigonometry"),
 ("L7","NumberTheory","Number Theory","INMO","inmo-numbertheory"),
 ("L7","Algebra","Algebra","INMO","inmo-algebra"),
 ("L7","BasicMathematics","Basic Mathematics","INMO","inmo-basicmaths"),
 ("L7","Combinatorics","Combinatorics","INMO","inmo-combinatorics"),
 ("L7","Geometry","Geometry","INMO","inmo-geometry"),
]
def done(r):
    p=f"{OUT}/{r[4]}/{r[4]}.html"
    if not (os.path.exists(p) and os.path.getsize(p)>0): return False
    try:
        return "fmt:2tab-cov" in open(p).read(80)
    except Exception:
        return False
built=[]
for r in M:
    if done(r): continue
    if time.time()-START > BUDGET: break
    t=time.time()
    subprocess.run([sys.executable,"build_book.py",*r], check=True)
    built.append((r[4], round(time.time()-t,1)))
left=[r[4] for r in M if not done(r)]
print("built this run:", built)
print(f"DONE {len([r for r in M if done(r)])}/{len(M)}  remaining: {left}")
