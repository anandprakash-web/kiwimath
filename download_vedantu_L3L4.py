#!/usr/bin/env python3
"""Download the Vedantu L3 + L4 (Grade 3-4 / 5-6) assignment PDFs via rclone.
Uses your Google sign-in (remote named "gdrive", same as download_via_rclone.py).
Resumable: skips files already present. RUN:  python3 download_vedantu_L3L4.py
Files land in  ~/Downloads/Vedantu_Content/L3/  and  /L4/ .
"""
import os, subprocess, tempfile, shutil, sys
BASE=os.path.expanduser("~/Downloads/Vedantu_Content"); REMOTE="gdrive:"
if shutil.which("rclone") is None:
    sys.exit("rclone not found. brew install rclone, then `rclone config` (remote name: gdrive)")
ASSIGNMENTS=[
    ("L3","01_Knowing_about_numbers","1aROsfAjWftnyzk9JL1I1E-iA2qG3wgkd"),
    ("L3","02_Operations_on_numbers","1QhhvAEv6TQVyyVpoxFvJAwiChrTK_rcS"),
    ("L3","03_Factors_and_multiples","1r9M5SKcXBEhyXVgqwQQs_rdy7yWspvcu"),
    ("L3","04_Factors_and_multiples","14pcMNWVJ2oQc4ZrJOX5DKKT4fv3wtF9h"),
    ("L3","05_Probability_and_Cryptarithms","1HIwK2_gusF8NHYhTJLIcx-zlxExBu1Zd"),
    ("L3","06_Fractions","10S-VNC_kklyv99gvA_ilkjohdSk2l5hH"),
    ("L3","07_Test_1_and_Assignment_Discussion","1WEqpHLz_umsdZhb6ugBlWzSftEA4lRg3"),
    ("L3","08_Fractions","1aZswTamHEBFgun6VnK3DHJfWZ5dAAtGY"),
    ("L3","09_Decimals","18rrRPJuo3ji9S30LtIm_NUzZ5Wex569C"),
    ("L3","10_Useful_Conversions","15L1qmf3X3zGnQvN19MaaEQcvFKoShhJV"),
    ("L3","11_Finding_largest_and_smallest_number","1ejM8BEev6GbcsUZuQepwfGv9dOottYNd"),
    ("L3","13_Test_2_and_Assignment_Discussion","1LTTFJJexyXmr-2ejOB5YrhUvmWV8IjMA"),
    ("L3","15_venn_diagrams","1zoqcBpbcdxu5op1auMTJsjIPQDxRVApb"),
    ("L3","16_Algebra_fundamentals","1BZavqFH8EljeJf4JtHjXYPDPEbdp-iII"),
    ("L3","17_Algebra_fundamentals","13-Kelc4GnmG2ns0Ryep7SajtcBfIqvsw"),
    ("L3","18_Perimeter_of_Geometric_figures","1y5KlP47xrkJRPILnpAkjAvrU3qw9yeue"),
    ("L3","19_Test_3_and_Assignment_Discussion","1k4MHZqK97HAqAc4ppLNuY9uYYg7_-CB-"),
    ("L3","20_Area_of_Geometrical_figures","13or0u7a-4Of2DA9-2tynRfmxA5Rz2M6X"),
    ("L3","21_Shapes_of_2D_and_3D","1F-y3gQreOm4Cr37m-kKFy0HKiKrosigT"),
    ("L3","22_symmetry","19px3gZFfgAmKaqYHkyVvMtSejl0qCROj"),
    ("L3","25_Alphabet_tests_Coding_decoding","1WOMFqBl95u8akeZuisyrwTWv6nhwB2lT"),
    ("L3","26_Clocks_and_Calendars","1p-15ilQLNRCRGKxMuniCbsVvgK5wyxXu"),
    ("L3","29_Blood_Relation","1j3-5pAjZ-Nsql-vH2XY7cgW5qi8bjoSV"),
    ("L3","30_Paper_Folding_and_cutting","1E58gT8pO4Ssmo-FeVDSpxOgLRw2WSox5"),
    ("L3","31_Test_4_5_and_Assignment_Discussion","1ebohk-fxn5IfTNYz7KfyA2VvOnB_pbep"),
    ("L3","32_Statement_type_questions","1ALGDgudAVwmn_z2KAfGwT2x4HM9GopdV"),
    ("L3","33_magic_square","1NqX5q7sRdQyHyUgelNvo8eJs75Oit1UR"),
    ("L3","36_Basics_with_problems","1QBHBC0mI7RKYkWQhaY20Om2zTIk5Ou4A"),
    ("L3","37_Patterns_Analogy_and_Classification","1Q_RATbyUUFjMhV-p6Xjx8mgWLo6iMLjT"),
    ("L3","38_Bar_Chart_Circle_graph_Pictograph","1vgTuFc3O0CfHK0NopELPXkh8VuCdsODg"),
    ("L3","39_Magical_tricks_of_Maths","14bc6p4IOWiiiS0m9aN-2ix5madGxjeTr"),
    ("L3","40_Test_6_7_and_Assignment_Discussion","1NAghoPjmGVRj20kGRMyYu2MAGLVtfrGG"),
    ("L4","01_Knowing_your_numbers","1gub7xWXh9iRGOSCNpDdmKlRA-rBC6xtH"),
    ("L4","02_Test_of_divisibility","1azT1YPhO_yPy47Y-4Dvpx4uoPVyTtEPO"),
    ("L4","03_Factors_and_multiples","1azwHZ3nx4rIEPRbAjbRiDWpKghHKA1JA"),
    ("L4","04_Integers_and_Fractions","1K5mMZI3Lp2RhlV7LZmrcaCvb1TLWEt15"),
    ("L4","05_Integers_and_Fractions","1N5gHx_nyVTw0blhyX92XUCD9je8eJdtO"),
    ("L4","06_Probability_and_Cryptarithms","1S1eIR2zQnYmk0jsEM1nt0ROk7e2_nC2K"),
    ("L4","09_Profit_and_loss","16T7Yp5Ecr6LRVVCaFYynGvK25z8mT4ns"),
    ("L4","10_Logic_and_Puzzles","1x4Sw_QCT7XDuJo9RTq6S-3m_smeLQRJ7"),
    ("L4","11_Logic_and_Puzzles","1v5WSMXyzH14_nkKVLh3-koVud5gmEj4i"),
    ("L4","13_Test_2_and_Assignment_Discussion","1CP4wRDHcObmluLQnSyrq-R-s5p_XiLHt"),
    ("L4","14_Magic_Squares_Money","1LD3uMyY_hPloF4_-HsuK92QuQ04-BAsD"),
    ("L4","15_Ratio_and_proportion","1-pIQUFIPWAi5rJsCKl_8bsIOSLlyX1ZR"),
    ("L4","16_Lines_angles_triangles","1OoXIzk5zQCC7JYbNjcPxngOwEQ_2_TXI"),
    ("L4","17_Polygons","1-XHGP9vOYPM4zyXpz63Ei6oJ91F1f-rZ"),
    ("L4","19_Average_Piechart","1FW_4_-ftI_ZRkoxTTr6tM9luAHgtYjs3"),
    ("L4","20_Data_Handling","1EuYvNPRlNXQ9DTbg0VdLH4p_s4xUZqwr"),
    ("L4","21_Introduction_Properties_of_algebra","14h3s-MsnfUbZtl3omaBgGPj9kRORWsDS"),
    ("L4","22_Problems_on_variable_and_constants","14dKyg27L9pi0ng_3LfH8FZ8gXxzxzo_y"),
    ("L4","23_Test_3_4_and_Assignment_Discussion","12VblKde8UQpz_vGtN0-p0WrXCFHq1FWt"),
    ("L4","24_Exponents_and_powers","1V7RfvKu3pwTmIKqbmglcYefnKZJFtdwg"),
    ("L4","25_Ranking_and_position","1K6OjhCxKMA23kmsLkziMOuv_Ek6q6J5b"),
    ("L4","26_Geometrical_figures_pattern","1q9frkkd-gEzOaOxmb9338XkajZkHMryo"),
    ("L4","27_Paper_cutting_and_folding","1ecrfLCkokDW-6Tgq1qahyU-8iOu9GLbw"),
    ("L4","28_Mirror_images_and_relationships","1ZcYS1DgV2BWUIryBZRzxjPj3az4mmQEj"),
    ("L4","30_Clock_and_calendar","1qYKqgtx9hvup5o2eLhYbW8qwd_QZsg54"),
    ("L4","31_Net_cube_and_Dice","1f8bG_4of4ygKU1J9zJGeju654K7zjAM7"),
    ("L4","32_Direction_and_patterns","1J_SXgSCirjCHGB4EWx5jRO2i6nAuh7bj"),
    ("L4","33_Possible_Combinations","17_aUSb7UX5DHRswjsL_wjHF9ldBnyLnW"),
    ("L4","34_Direct_and_Inverse_Variations","1io7gIXjwRca-hPt7TQI-ES-_QpuEkbNt"),
    ("L4","37_Perimeter_of_plane_figures","1VA_YzS-OMEW2X4uIyNS0HYMQlrGAXk7F"),
    ("L4","38_Area_of_plane_figures","1AichCMgYSRAFxG5crai4R_vENv4Jni1A"),
    ("L4","39_Axes_of_symmetry_rotational","13cFTDBTuRvw3_n3tRCfUXZuJOP_w5hn_"),
    ("L4","40_Test_6_7_and_Assignment_Discussion","1W1HTUWoXAA8MZW_pQekJIeRWvRteGxSL"),
]
ok=skip=0; failed=[]
total=len(ASSIGNMENTS)
for n,(lvl,name,fid) in enumerate(ASSIGNMENTS,1):
    out=os.path.join(BASE,lvl,name+".pdf")
    if os.path.exists(out) and os.path.getsize(out)>1000:
        skip+=1; continue
    os.makedirs(os.path.dirname(out),exist_ok=True)
    print(f"[{n}/{total}] {lvl}/{name}")
    with tempfile.TemporaryDirectory() as td:
        r=subprocess.run(["rclone","backend","copyid",REMOTE,fid,td+"/"],
                         capture_output=True,text=True)
        got=[f for f in os.listdir(td) if os.path.getsize(os.path.join(td,f))>0]
        if got:
            shutil.move(os.path.join(td,got[0]),out); ok+=1
        else:
            failed.append((lvl,name,fid))
            print("   ! "+(r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else "no file returned"))
print(f"\n=== {ok} downloaded, {skip} already present, {len(failed)} failed (of {total}) ===")
print("Folder: "+BASE)
if failed:
    print("\nStill failed:")
    for lvl,name,fid in failed:
        print(f"  {lvl}/{name}  ->  https://drive.google.com/file/d/{fid}/view")
