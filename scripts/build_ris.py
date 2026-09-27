#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 *_papers.json 生成 Zotero 可导入的 RIS。
关键技巧：RIS 文件名 = Zotero 导入时自动创建的新文库（Collection）名。
用法: python3 build_ris.py <papers.json> [--collection "Compensation from FT50 &UTD24"]
"""
import json, argparse, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonfile")
    ap.add_argument("--collection", default=None)
    a = ap.parse_args()
    d = json.load(open(a.jsonfile))
    recs = d["records"]
    kw = d.get("keyword", ["?"])[0]
    coll = a.collection or f"{kw.capitalize()} from FT50 &UTD24"

    def esc(s):
        return (s or "").replace("\r", " ").replace("\n", " ").strip()

    path = os.path.join(os.path.dirname(a.jsonfile) or ".", f"{coll}.ris")
    with open(path, "w", encoding="utf-8") as f:
        for r in recs:
            lines = ["TY  - JOUR", f"TI  - {esc(r['title'])}"]
            for au in esc(r["authors"]).replace(" 等", "").split(", "):
                parts = au.rsplit(" ", 1)
                lines.append(f"AU  - {parts[0]},{parts[1]}" if len(parts) == 2 else f"AU  - {au}")
            lines.append(f"JO  - {esc(r['journal'])}")
            lines.append(f"PY  - {r['year']}")
            if r.get("doi"):
                lines.append(f"DO  - {r['doi']}")
                lines.append(f"UR  - https://doi.org/{r['doi']}")
            if r.get("abstract"):
                lines.append(f"AB  - {esc(r['abstract'])[:1200]}")
            for kw_ in r.get("kw", []):
                lines.append(f"KW  - {esc(kw_)}")
            lines.append("ER  - ")
            f.write("\n".join(lines) + "\n\n")
    n = sum(1 for _ in open(path) if _.startswith("TY  - JOUR"))
    print(f"RIS written: {path} (entries={n})")
    if n != len(recs):
        sys.exit(f"ERROR: entry count {n} != records {len(recs)}")

if __name__ == "__main__":
    main()
