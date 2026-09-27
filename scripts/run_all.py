#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键编排：检索 → 交付物 → RIS →（可选）触发 Zotero 导入
用法:
  python3 run_all.py "compensation" [--synonyms "ceo pay,bonus"] [--years 20] [--cap 4] \
      [--collection "Compensation from FT50 &UTD24"] [--outdir <dir>] [--open-zotero]
"""
import argparse, subprocess, sys, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

def run(cmd):
    print(f"\n=== {' '.join(cmd)} ===", flush=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"STEP FAILED: {' '.join(cmd)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--synonyms", default="")
    ap.add_argument("--years", type=int, default=20)
    ap.add_argument("--cap", type=int, default=4)
    ap.add_argument("--collection", default=None)
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--open-zotero", action="store_true", help="生成 RIS 后自动用 Zotero 打开（弹导入对话框）")
    a = ap.parse_args()

    coll = a.collection or f"{a.keyword.capitalize()} from FT50 &UTD24"
    outdir = os.path.abspath(a.outdir)
    os.makedirs(outdir, exist_ok=True)

    # 1. 检索
    run([PY, os.path.join(HERE, "search_papers.py"), a.keyword,
         "--synonyms", a.synonyms, "--years", str(a.years), "--cap", str(a.cap), "--outdir", outdir])
    jf = os.path.join(outdir, f"{a.keyword.strip().replace(' ', '_')}_papers.json")
    if not os.path.exists(jf):
        sys.exit(f"ERROR: {jf} not found")

    # 2. 交付物 MD + HTML
    run([PY, os.path.join(HERE, "build_outputs.py"), jf, "--collection", coll, "--outdir", outdir])

    # 3. RIS（文件名 = Zotero 自动新建文库名）
    run([PY, os.path.join(HERE, "build_ris.py"), jf, "--collection", coll])

    # 4. 触发 Zotero 导入
    ris = os.path.join(outdir, f"{coll}.ris")
    if a.open_zotero:
        if not os.path.exists("/Applications/Zotero.app"):
            print("[WARN] 未检测到 /Applications/Zotero.app，请先安装 Zotero: https://www.zotero.org/download/")
        else:
            subprocess.run(["open", "-a", "Zotero", ris])
            print(f"\n已用 Zotero 打开 {ris} —— 请在弹出的导入对话框中：")
            print("  1) 勾选『将新收入的项目放入新文库』(Place imported items into new collection)")
            print(f"  2) 点击『导入』→ 文库「{coll}」自动创建并写入全部条目")
    else:
        print(f"\nRIS 已生成: {ris}")
        print("后续手动导入: open -a Zotero 该文件, 或 Zotero 菜单 文件→导入")

    print("\n交付物清单（位于", outdir, "）:")
    for f in sorted(glob.glob(os.path.join(outdir, f"*{a.keyword.strip().replace(' ', '_')}*")) + [ris]):
        print(" -", os.path.basename(f))

if __name__ == "__main__":
    main()
