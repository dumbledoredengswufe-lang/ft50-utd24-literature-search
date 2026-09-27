#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FT50/UTD24 全部 51 刊指定关键词论文检索（Crossref 元数据，等价于扫描每一期目录）
用法:
  python3 search_papers.py "compensation" [--synonyms "ceo pay,bonus"] \
      [--years 20] [--cap 4] [--outdir <dir>] [--from 2006-01-01 --to 2026-09-30]
输出: <outdir>/<keyword>_papers.json
"""
import json, re, time, sys, os, html, argparse, urllib.request, urllib.parse
from datetime import date

# ── FT50 + UTD24 期刊清单（UTD24 独有的 INFORMS Journal on Computing 已包含）──
JOURNALS = [
    "The Accounting Review", "Journal of Accounting and Economics", "Journal of Accounting Research",
    "Accounting, Organizations and Society", "Contemporary Accounting Research", "Review of Accounting Studies",
    "The Journal of Finance", "Journal of Financial Economics", "The Review of Financial Studies",
    "Review of Finance", "Journal of Financial and Quantitative Analysis",
    "American Economic Review", "The Quarterly Journal of Economics", "Journal of Political Economy",
    "Econometrica", "The Review of Economic Studies",
    "Academy of Management Journal", "Academy of Management Review", "Administrative Science Quarterly",
    "Strategic Management Journal", "Organization Science", "Journal of International Business Studies",
    "Journal of Management", "Journal of Management Studies", "Organization Studies", "Human Relations",
    "Human Resource Management", "Strategic Entrepreneurship Journal", "Entrepreneurship Theory and Practice",
    "Journal of Business Venturing", "Journal of Business Ethics", "Journal of Applied Psychology",
    "Organizational Behavior and Human Decision Processes",
    "Journal of Marketing", "Journal of Marketing Research", "Marketing Science",
    "Journal of Consumer Research", "Journal of Consumer Psychology",
    "Journal of the Academy of Marketing Science",
    "Management Science", "Operations Research", "Manufacturing & Service Operations Management",
    "Production and Operations Management", "Journal of Operations Management",
    "Information Systems Research", "MIS Quarterly", "Journal of Management Information Systems",
    "INFORMS Journal on Computing", "Harvard Business Review", "MIT Sloan Management Review", "Research Policy",
]

HEADERS = {"User-Agent": "ft50-utd24-literature-search/1.0 (mailto:workbuddy-agent@example.com)"}

def norm(s):
    s = (s or "").lower().replace("&", "and").strip()
    s = re.sub(r"^the ", "", s)
    return re.sub(r"\s+", " ", s)

def fetch(url, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if a == tries - 1:
                print(f"  [WARN] fetch fail: {url[:80]}… {e}", flush=True)
                return None
            time.sleep(3 * (a + 1))

def clean_abstract(ab):
    if not ab:
        return None
    t = html.unescape(re.sub(r"<[^>]+>", " ", ab))
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:600] + "…") if len(t) > 600 else (t or None)

def fmt_authors(authors):
    if not authors:
        return "佚名"
    names = []
    for au in authors[:3]:
        names.append(f"{au.get('family','')} {au.get('given','')}".strip())
    s = ", ".join(n for n in names if n)
    return s + (" 等" if len(authors) > 3 else "") or "佚名"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--synonyms", default="", help="逗号分隔的同义词/扩展词，如 'ceo pay,bonus'")
    ap.add_argument("--years", type=int, default=20)
    ap.add_argument("--cap", type=int, default=4, help="每刊保留篇数上限")
    ap.add_argument("--from", dest="from_date", default=None)
    ap.add_argument("--to", dest="to_date", default=None)
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--only", default="", help="逗号分隔期刊名，只检索这些刊（用于失败刊断点重试）")
    a = ap.parse_args()

    today = date.today()
    from_date = a.from_date or f"{today.year - a.years}-01-01"
    to_date = a.to_date or today.isoformat()
    terms = [a.keyword] + [s.strip() for s in a.synonyms.split(",") if s.strip()]
    pat = re.compile("|".join(re.escape(t) for t in terms), re.I)
    print(f"关键词: {terms} | 区间: {from_date} ~ {to_date} | 每刊上限: {a.cap}", flush=True)

    records, failed = [], []
    only_set = [s.strip() for s in a.only.split("|") if s.strip()] if a.only else []
    journal_list = [j for j in JOURNALS if not only_set or j in only_set]
    for name in journal_list:
        url = ("https://api.crossref.org/works?query.title=" + urllib.parse.quote(a.keyword)
               + "&query.container-title=" + urllib.parse.quote(name)
               + f"&filter=from-pub-date:{from_date},until-pub-date:{to_date},type:journal-article"
               + f"&rows=100&select=DOI,title,container-title,issued,author,abstract,subject")
        d = fetch(url)
        time.sleep(0.6)  # Crossref polite pool
        if not d:
            failed.append(name)
            continue
        kept = []
        for it in d.get("message", {}).get("items", []):
            title = re.sub(r"\s+", " ", (it.get("title") or [""])[0]).strip()
            ctr = (it.get("container-title") or [""])[0]
            # 严格归属：规范化后容器名必须精确匹配（允许 "MIS Quarterly: ..." 形式）
            n_ctr, n_name = norm(ctr), norm(name)
            if not (n_ctr == n_name or n_ctr.startswith(n_name + ":")):
                continue
            year = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            if not year:
                continue
            ab = clean_abstract(it.get("abstract"))
            t_hit = bool(pat.search(title))
            ab_hit = bool(ab and pat.search(ab))
            if not (t_hit or ab_hit):
                continue
            kept.append({"title": title, "authors": fmt_authors(it.get("author")),
                         "journal": ctr, "year": year, "doi": it.get("DOI", ""),
                         "abstract": ab, "title_hit": t_hit, "kw": list(it.get("subject") or [])[:3]})
        seen, uniq = set(), []
        for r in sorted(kept, key=lambda x: (not x["title_hit"], -x["year"])):
            if r["doi"] in seen:
                continue
            seen.add(r["doi"]); r.pop("title_hit", None); uniq.append(r)
        records.extend(uniq[:a.cap])
        print(f"  {name}: kept {min(len(uniq), a.cap)}/{len(kept)}", flush=True)

    records.sort(key=lambda x: (-x["year"], x["journal"]))
    os.makedirs(a.outdir, exist_ok=True)
    suffix = "_patch" if only_set else ""
    out = os.path.join(a.outdir, f"{a.keyword.strip().replace(' ', '_')}_papers{suffix}.json")
    json.dump({"keyword": terms, "from": from_date, "to": to_date,
               "records": records, "failed": failed}, open(out, "w"), ensure_ascii=False, indent=1)
    n_ab = sum(1 for r in records if r["abstract"])
    print(f"\nDONE {len(records)} papers ({n_ab} with abstract) across "
          f"{len(set(r['journal'] for r in records))} journals -> {out}", flush=True)
    if failed:
        print("FAILED journals:", failed, flush=True)

if __name__ == "__main__":
    sys.exit(main())
