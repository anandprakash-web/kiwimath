#!/usr/bin/env python3
"""Download the Vedantu assignment PDFs via RCLONE (uses your Google sign-in, so
NO anonymous-throttling and it can reach files shared to you specifically).
Resumable: skips anything already downloaded by the gdown run.

ONE-TIME SETUP (do this first):
  1) brew install rclone            (or: curl https://rclone.org/install.sh | sudo bash)
  2) rclone config
       n  (new remote)
       name>  gdrive
       Storage>  drive            (type the number shown next to "Google Drive")
       client_id>     (just press Enter)
       client_secret> (just press Enter)
       scope>  1                  (full access)  — or type: drive.readonly
       root_folder_id> (Enter)    service_account_file> (Enter)
       Edit advanced config>  n
       Use web browser to authenticate?>  y   --> sign in with the Google account
                                                   that can open these files
       Configure this as a Shared Drive?>  n
       Keep this "gdrive" remote?>  y     then  q  to quit

THEN RUN:
  python3 download_via_rclone.py
"""
import os, subprocess, tempfile, shutil, sys

BASE = os.path.expanduser("~/Downloads/Vedantu_Content")
REMOTE = "gdrive:"   # must match the remote name you made in `rclone config`

if shutil.which("rclone") is None:
    sys.exit("rclone not found. Install it:  brew install rclone   (then run `rclone config`)")

ASSIGNMENTS = [
    ("L5","NumberTheory","Unit_digit","1tWh3wLI9ayBAQUAzT6mX4tHkujLxk6iJ"),
    ("L5","NumberTheory","HCF_&_LCM","1IKZCNSe-_PK5rvkIJcSK85n-YMMrvDnb"),
    ("L5","NumberTheory","HCF_&_LCM_2","1_CFbsXst0c7al-ZoyXr9DfoGMWEBHuHa"),
    ("L5","NumberTheory","Divisibility_Rules","1x23Sbhpvu3Tt2cMc-h4cStzntHdWKP4z"),
    ("L5","NumberTheory","Divisibility_Rules_2","1cE_8KGWupqJ61SFXKXke4QzebhUQP-lV"),
    ("L5","NumberTheory","Decimal","1upRkhitj4h_BMgrh-wSCCZAH_yiWy92b"),
    ("L5","NumberTheory","Exponent","1LFFc3k0R7wqjJqArXXE4LXaUKyqcycf4"),
    ("L5","NumberTheory","Surds","1T38FnNiuuj1vMbHGoBNWTHx0u5BEuQ06"),
    ("L5","NumberTheory","Playing_with_numbers-1","1y-lp0_OrmbLhUJ7hGmgr3HsjSC0YOxLJ"),
    ("L5","NumberTheory","Playing_with_numbers-2","1-obCQMJApoQXrHZb0mc14CRDGSRu6V1H"),
    ("L5","NumberTheory","Diophantine_Equation-1","1MYaIEqJA6EBKdxwULU1cxiLSbmINFDWF"),
    ("L5","NumberTheory","Diophantine_Equation-2","1Dd_si2uURCCRykWjCMUzwxyEk5Hm4BuM"),
    ("L5","Algebra","Identities-1","1kHNl5JMu_J-osZJ17GkPzLOVRujLizzq"),
    ("L5","Algebra","Identities-2","1q6Ly0ZLS2MMjlIruuRCI9fThbOXCns7i"),
    ("L5","Algebra","linear_equation_in_two_variable","1nqYUCDShILvJ8Qo7IX44UexNDZVeRrTZ"),
    ("L5","Algebra","linear_equation_in_one_variable","1ASdItyxY1YJO60LKE-xkTQYNGiL11_eD"),
    ("L5","Algebra","System_of_Equations","1xdPPcNTdFDNJMhJKpU8dzyY7VLMNmHOP"),
    ("L5","Algebra","Polynomials-1","1qPLkMsVqrAlUG0TuswBZhzHfIe-iZkn_"),
    ("L5","Algebra","Polynomials-2","11BFruu8z4YI5Zp5A-spPWhiLjbKwdWuu"),
    ("L5","Algebra","Introduction_to_Quadratic_Equation","1wLM8yF8HApc7Y--58hp7Oc_ks1o8gFcO"),
    ("L5","Algebra","Methods_to_solve_Quadratic_Equation","1f5eoMEQrGgfqN6ACZawkwDmePMzFt00c"),
    ("L5","Algebra","Introduction_to_sequence","1iGJ9QRhsAlufSfS3UGsNjMlFNysu4ick"),
    ("L5","Algebra","Arithmetic_Progression","1QzITDu5Kc9X5SJTTYPtJutsCbTRGy0nM"),
    ("L5","Arithmetic","Ratio_&_Proportion","1rUU6gqf1-PhabKQL2RiPHORomVfYhMdv"),
    ("L5","Arithmetic","Profit_&_Loss","1yP85RQ6H1wkBVxWXwJfmX9r223Zrpvn2"),
    ("L5","Arithmetic","Time_&_work","1oYGP_e-gGCVGQye46pR5z0Mq2841zTAa"),
    ("L5","Geometry","Angle_Chasing","1UTLirQAIiKoKmwXL4NLIU-5AfOqaI0ED"),
    ("L5","Geometry","Important_points_of_Triangles","1aDAx9Jr50-Nqp4vAN3plzjWheAtoaRVL"),
    ("L5","Geometry","Congruent_triangles-1","1LVxFOYW2A5egNCNfzBaoNYvKCRxKsLM1"),
    ("L5","Geometry","Triangle_Inequality","1opB2kuIwcALaqugNyhY6OfRuV6lVBoSX"),
    ("L5","Geometry","Constructions","1x5rctNUEN9YYAss8oUB3VlteuPyk_kGV"),
    ("L5","Geometry","Quadrilaterals","1TfGQM1g-YJBic1b0mHXOpR2ecJU_SzVT"),
    ("L5","Geometry","Polygons","1MotQ3478A0aJajbA1rowLp_q1b1Xhelq"),
    ("L5","Geometry","Pythagoras_theorem","1eCJ0n9_Wtp72XcFVwojE-DWAjAumh3Pz"),
    ("L5","Geometry","Area_of_parallelogram_&_triangles-1","1RnIJT2V9LrFKQONr9KBgj5ug4eLAZaS5"),
    ("L5","Geometry","Area_of_parallelogram_&_triangles-2","1P9LVHSgg4-G14DmOT4lUAfVXVVrPliWv"),
    ("L5","Combinatorics","Factorial","1bKvmaz4rKTAo6pul50ds-duxLs6Xnyp4"),
    ("L5","Combinatorics","Fundamental_Principles_of_counting","1msEXiwOYLJ6fbz6ysOySvS6kCzE-bfOz"),
    ("L5","Combinatorics","Number_of_divisors","1q_TACyJE0rCefhz6qKIlIDuw9XcwG45G"),
    ("L6","BasicMathematics","Basic_Identities","1XzlWIofdT1lzgN_27gkGbNNVmg7gL7Ik"),
    ("L6","BasicMathematics","Factorization","1uY4lPUw-71wagxEnzOJ9v6UrzwjH6X3L"),
    ("L6","BasicMathematics","Inequalities_and_Wavy_Curve","19dbSbQvF4C4TjPhXUd3f0DmY4-YVN5TC"),
    ("L6","NumberTheory","GCD_&_LCM","1dqQq5SoPc-8jgbovfVXvJNwvL2-0TE1a"),
    ("L6","NumberTheory","Cyclicity","1CSIjOT7enzJuuo3MCWWyCn988qbMNDbH"),
    ("L6","NumberTheory","Congruence","1bEZfchNSjXK01pVz8SCjq1mxJisVIoXO"),
    ("L6","NumberTheory","Congruence_based_Problems","1fTQyvub4YW3E9bF1IbXDU1vKrulXLdVh"),
    ("L6","NumberTheory","Divisibility_Tests","1-D5ozHb94JCPFPzOIyxUyt9XbrF04hzX"),
    ("L6","NumberTheory","Diophantine_Equation","1jXdOiofNgaHm4MS7Zf-Z4NEUNeWml2At"),
    ("L6","NumberTheory","Diophantine_based_Problems_and_theorems","1Ch8LP9H1_BVOSFYcKOMFOk35sniBs_U6"),
    ("L6","NumberTheory","Theorems_and_Base_System","1r-BXbkbbY3mA0uPWa1mi5paZ5z0gcueS"),
    ("L6","NumberTheory","Problem_Solving","1PnsJ3Aq-hpax0cDiy6L2GLIIcLZKieb7"),
    ("L6","Geometry","Angle_Sense","16-o9aqL4cR4LykSHSwJTyGbB8SyQSN-q"),
    ("L6","Geometry","Congruent_triangles","1SWf67xj2oWeaECu-dP3i8IdeAMXaIo24"),
    ("L6","Geometry","Applications_Congruent_triangles_Triangle_Inequalities","1Ig9LIW9hMsNirYeZS1-hPc6rmMXrkf6r"),
    ("L6","Geometry","MPT_BPT","1Ya4z3nDOOx4UZmuJCUXx1JcDD5uSvea-"),
    ("L6","Geometry","Similar_Triangles","1HgokOGw3WPmygby0EDOEi0sIZE3dDYs4"),
    ("L6","Geometry","Angle_Bisector_Theorem_Pythagoras","12U-MUouPMwe15JTeaeJcxwpQ0vOxU4gR"),
    ("L6","Geometry","Areas","11J8aZ2Y6-5gzTtntNhUNAyIcPxAS_8dD"),
    ("L6","Geometry","Points_of_Triangles","1LoVjxHmY8xYZzEt8JiNqXrqywlqcnFn_"),
    ("L6","Geometry","Circles_and_Related_Theorems","1HLXmAoq-IV9lyHq_BYzQA9bqyaVLWr8N"),
    ("L6","Geometry","Tangents_and_Power","1pXxiXKVQMA5mVHhlUl2vGtgwOpK6ySwp"),
    ("L6","Algebra","Factor_and_Remainder_Theorem","1XsL27I6AtnD3wMkrPxp2kCgIEvX5sTWS"),
    ("L6","Algebra","Quadratic_Equations","170y2Vokh9rRE6CUqapuvAG6fGOLywYLH"),
    ("L6","Algebra","Nature_Of_Roots_and_iota","1izZIbNkik9SMaKRMP2_WcKegNznScgSg"),
    ("L6","Algebra","Analysis_of_Graph_of_Quadratic","1N8v_ryRlsD7sSG6CjiEr2TeY-6c3SWmG"),
    ("L6","Algebra","System_Of_Equations","1O6yz7QQoy2ReyfqIE2DFBNeATeXzsKUI"),
    ("L6","Algebra","Problems_on_Quadratic_Equations","1lf-pP_jIRJ0VrYCA3MCN7wbKr3tj8yQW"),
    ("L6","Algebra","Arithmetic_Progressions","1HS1cVsmiA7X3BN3kK4Gfw1TwuXuE9YPv"),
    ("L6","Algebra","Geometric_Progressions","1mrXIhIwiiPajJ6qcS5kp4ZnD_oEIatTF"),
    ("L6","Algebra","Telescoping","1nEaCnfrGwF-DWBRySpx-PMuVLnY7syrn"),
    ("L6","Algebra","GIF","1O0ylTFWemU5TguYKrQN4IwF3dpmDoPJn"),
    ("L6","Combinatorics","Arrangements","1CbjzJVLLzsnWl3w_Z_O1z3iRiXYsnMQo"),
    ("L6","Combinatorics","Selections","16mDK-pGfCmFjfqm7nLbG8yIH1hNrBCBr"),
    ("L6","Combinatorics","Gap_and_Block_Method","17FSH75Tp3pq35PgNTBdYoFUCAN77rROr"),
    ("L6","Combinatorics","Beggar_Coin","1-1nrSuBaldWMCAwnTxkiuuFnsRDfItxM"),
    ("L6","Combinatorics","Divisors","15itd6Y8b1utfxOPoR7Eno5oQkuuCHOk4"),
    ("L6","Trigonometry","Trigonometry_Ratios","1fL1t_qY_zD6gEZxghMBMr6YOViBVjPTN"),
    ("L6","Trigonometry","Identities_and_Standard_Angles","1jxkk6X8A8mVo0VlCG1ZnrRT-uIhfNrpy"),
    ("L6","Trigonometry","Trigonometry_Big_Picture","1z1p4pVr9VCLCv-osT_uWOe-GzqMwYLhh"),
    ("L6","Trigonometry","Areas_and_Height_and_Distance","1aXMTWea81DzRdezunmhBuvuRvgG2-tp4"),
    ("L7","BasicMathematics","Identities","1lgc8oqgs_I-uqadPDucBhlpptXEmUhHH"),
    ("L7","BasicMathematics","Inequations_and_Wavy_Curve","1crlyXFIYa4bP4R4jRzdOPX4jN_55wthw"),
    ("L7","BasicMathematics","Binomial_Theorem","1mKuR9YncXgaUwKnwB0DC21d9uyp7wyQB"),
    ("L7","NumberTheory","LCM_GCD_based_Problems","1UIivSVgF0q4t26dEHevYu0WoFbFWMgHj"),
    ("L7","NumberTheory","Congruence","1QD4kNgjuNk3JYD-6UTTK6XmiaaHYOucB"),
    ("L7","NumberTheory","Fermat_and_Euler_Theorem","1xoj3TRL8jVMZAuy6TX3aJk8WPU6yG0kd"),
    ("L7","NumberTheory","Wilson_and_CRT","1FvbwIPx2z1_or6Er9VK8mG2tQfVMFhOO"),
    ("L7","NumberTheory","Perfect_Squares_Primes","163BVwLE6QVkzVkQJ_fwpsTiNhBv48pj6"),
    ("L7","NumberTheory","Diophantine_Equation","1W5DNF85HQwd7OM5LRxMtxkEZFELDcKG7"),
    ("L7","NumberTheory","Base_System","1nYJ024jVEZP595dylweW7hhUuiCzmmbj"),
    ("L7","NumberTheory","Mathematical_Induction","1czc4PRIsTxUM_nRM6Qw0VMGgNQW7QvdW"),
    ("L7","NumberTheory","Problem_Solving_1","1nOogn_-nSXeH2jvQN8WMz2VnXjEbzpa5"),
    ("L7","Geometry","Trigonometry_Introduction","1ikrkhcCjsBypALtRPggErpIRLXxgJMSi"),
    ("L7","Geometry","Compound_Multiple_Angles","1UTd4MlA9nfwmi3kP-ZN3S5ZVqnAZcRg3"),
    ("L7","Geometry","Sine_and_Cosine_Rule","16PdH33yzWqCe6soXbXZAR-IO6eqqHFRY"),
    ("L7","Geometry","Problems_on_Angle_Chasing","1lLFrpsBHqtOa860f0LgdSoYD4KNfEOo9"),
    ("L7","Geometry","Congruent_Triangles","1VoS3yxcZZzZcsr87_Z51ydYC4aWWZ3pt"),
    ("L7","Geometry","Triangle_Inequalities_MPT_BPT","1-oWGAb6yxKWzEYTbxNu31lbVz0evzBHO"),
    ("L7","Geometry","Similar_Triangles","1yJty_VCT5iedNz5POwfYxDqje0_I9dby"),
    ("L7","Geometry","Pythagoras_Appolonius_Stewart","1vOyuQaFjgYFR691lx9yzbYGOFyCuZwuq"),
    ("L7","Geometry","Problems_on_Areas","1nNDVXhTfnVAxA8UhRRYHmQw-7MM224HZ"),
    ("L7","Geometry","Cevas_and_Menelaus","1cQcnZUYBT7eYAb51__jfaV9tCS3EdrYt"),
    ("L7","Geometry","Concept_of_Rotation","1w3mfL0n3a5WRVZI6WFh07WF0rA1GjaHB"),
    ("L7","Geometry","Quadrilaterals_Cyclic_Quadrilaterals","1uPlZgaK2J7fjreZcUfOCBJKAnfGWbSIz"),
    ("L7","Geometry","Circles_and_Properties","1kPOi6XwhCvWDu8u-KdOVJhCt331RFhdh"),
    ("L7","Geometry","Ptolemy_and_Tangents","1jveJ-YWLSHFZHgVaICO_4kK6nBtnf-Db"),
    ("L7","Geometry","Centroid_and_Orthocenter","1BbjE3XOhPphdqI7YwK_HCjkAFVa6m0FL"),
    ("L7","Geometry","Incenter_and_Circumcenter","1unYbci0PwCI1FAYq6Rx-Ghx0RfzMxmvj"),
    ("L7","Geometry","Problem_Solving_Geo","10z4Uc0fgQMPc4tsxHye0KqrNXyGPu6Cd"),
    ("L7","Geometry","Analytical_Geometry","1tORYEC16wAJR_5oqPpf4Wy8T3qQEfti5"),
    ("L7","Combinatorics","Arrangement_based_Problems","1xkFDXVwDyUXVmZXDxVwiwC7nC6BGhXMg"),
    ("L7","Combinatorics","nCr","1B_SFyhu4Vzcm-_kZZNR-XxPE_zhHpHCr"),
    ("L7","Combinatorics","Standard_Concepts_and_Problems","1mwMeasDGuLJw1VHmyV64m6oK1xanksZY"),
    ("L7","Combinatorics","Beggar_Coin","1wFIT7SKEd7SimqsdI4ib-S_TBmq_lle9"),
    ("L7","Combinatorics","Generating_Functions","1VECauX1wYZrodgFBNkrMue_RwuBSzRAH"),
    ("L7","Combinatorics","Divisors","1WKcRNaMwgtUqc6LzyXG4qen43fGs3MiW"),
    ("L7","Combinatorics","Distribution_of_Distinct_Objects_Grouping","1yaz3J1kaN1Ddh170TlMU4U18dYLRkJ1X"),
    ("L7","Combinatorics","Objects_in_Circles","18K2Du2_Vv-y-r_CKVz_pkF9q6qRSvK1U"),
    ("L7","Combinatorics","PHP","1V03ywzM6-Dw8ct8vMEZjpb3kz4dFxVzU"),
    ("L7","Combinatorics","Recurrence","1sfLZ2O0GGx2H8ogpkNJuQbqxTHJPtzaV"),
    ("L7","Combinatorics","Coloring_Techniques","1vHVqsYWy_zx43nCtVF6Ks0VBJQJxdbeN"),
    ("L7","Combinatorics","Parity_and_Invariance","1VVUfk6eET4IduoEPGbS0p-HhA_FNBCyn"),
    ("L7","Combinatorics","Problem_Solving_Combi","1UUKLI_ETXFo2lBQh56GSYsXXg9OgeKVq"),
    ("L7","Algebra","Factor_and_Remainder_Theorem","1LghgtPAfVf4bsoHzvSAZYLuFVZa6Nkeu"),
    ("L7","Algebra","Roots_and_Coefficients_Nature_of_Roots","1Jp8x0B3Tz0wgvN3ikRbj381xcS1kk1pa"),
    ("L7","Algebra","Rational_and_Integral_Roots","1G9l4QuDKZ9ar31sGUa9Qbi3vgCRnuguy"),
    ("L7","Algebra","Graph_Analysis_and_Common_Roots","1CBr44K7vc0CC3Vu_urUTR0-vkiIHhc7c"),
    ("L7","Algebra","Miscellaneous_Equations","1B6ptMCaWxwbJrx59c30ggCtzOI4ipaLD"),
    ("L7","Algebra","Complex_Numbers","1acRCQOnoBD3MstBuB48zJt5f3pr1fTE5"),
    ("L7","Algebra","Sigma_Notation","1_t2LWm8ZiH9pUT3VsnQKh1qaivzav83D"),
    ("L7","Algebra","AP_GP_HP","11IozdkI5Q4LNXwvZuYhfGztrbOH_4FTq"),
    ("L7","Algebra","Other_Sequences","1NXi5sQi0EtBH-iigs6l87DEvmibu06oH"),
    ("L7","Algebra","Telescoping","1snZgJOLAZeM9v_wNGVuDfmsT_XtYTIoI"),
    ("L7","Algebra","Means_Inequality_Power_Means_RMS","1DHPDy1oIpVij-uvQJcNYHkqMaxgV-OnZ"),
    ("L7","Algebra","Cauchy_Schwarz_Rearrangement_Titu","1n8_9N6OCxqxaCd3TWcBgstvqVhUiNEpN"),
    ("L7","Algebra","Functions_Intro","1gvrkg7YHQin6QyOYUrqnslSkw6CsCvUg"),
    ("L7","Algebra","Modulus","1F27hCaH3ecRgr6ljtNqcTzEAuDRhAqvk"),
    ("L7","Algebra","GIF_Fractional_part","1scx_oKE85bpHICilnRhmGZBUNkzGj1u7"),
    ("L7","Algebra","Logarithm","15M8wYVT89D42eomZyXIlYDvGIPz10Zu4"),
    ("L7","Algebra","Functional_Equations","1CqJSzY9Au0RYOzDALXqSw2Z63dnEPGc0"),
]

def main():
    ok = skip = 0; failed = []
    total = len(ASSIGNMENTS)
    for n, (lvl, pillar, topic, fid) in enumerate(ASSIGNMENTS, 1):
        out = os.path.join(BASE, lvl, pillar, topic + ".pdf")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            skip += 1; continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        print(f"[{n}/{total}] {lvl}/{pillar}/{topic}")
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(["rclone", "backend", "copyid", REMOTE, fid, td + "/"],
                               capture_output=True, text=True)
            got = [f for f in os.listdir(td) if os.path.getsize(os.path.join(td, f)) > 0]
            if got:
                shutil.move(os.path.join(td, got[0]), out); ok += 1
            else:
                failed.append((lvl, pillar, topic, fid))
                print("   ! " + (r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else "no file returned"))
    print(f"\n=== {ok} downloaded, {skip} already present, {len(failed)} failed ===")
    print("Folder: " + BASE)
    if failed:
        print("\nStill failed (check the remote name / that you can open these in browser):")
        for lvl, p, t, f in failed:
            print(f"  {lvl}/{p}/{t}  ->  https://drive.google.com/file/d/{f}/view")
    else:
        print("\nAll done. Tell Claude the folder path and it builds the books.")

if __name__ == "__main__":
    main()
