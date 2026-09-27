#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 *_papers.json 生成 Markdown + 深色单文件 HTML 交付物
用法: python3 build_outputs.py <papers.json> [--collection "Compensation from FT50 &UTD24"]
"""
import json, html, argparse, re, os

THEME_COLOR = "#d29922"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonfile")
    ap.add_argument("--collection", default=None, help="Zotero 文库名（默认 '<keyword> from FT50 &UTD24'）")
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()

    d = json.load(open(a.jsonfile))
    recs = d["records"]
    kw = d.get("keyword", ["?"])[0]
    coll = a.collection or f"{kw.capitalize()} from FT50 &UTD24"
    for i, r in enumerate(recs, 1):
        r["no"] = i
    n_ab = sum(1 for r in recs if r["abstract"])
    n_j = len(set(r["journal"] for r in recs))
    span = f"{d.get('from','?')} 至 {d.get('to','?')}"

    # ---------- Markdown ----------
    md = [f"""# FT50/UTD24 期刊 "{kw}" 主题论文检索结果（{span}）

> **检索说明**
> - 覆盖：FT50 + UTD24 全部 51 种期刊，{span} 发表的 research article。
> - 方法：Crossref 官方元数据库逐刊检索（等价于扫描每期目录），标题/摘要命中关键词 {d.get('keyword')}，标题命中优先，每刊保留上限见检索参数。
> - 摘要：{n_ab}/{len(recs)} 篇可直接展示（出版商未向 Crossref 开放的，点 DOI 查原文页）。

## 论文明细表
| # | 年份 | 标题 | 作者 | 期刊 | DOI | 摘要 |
|---|------|------|------|------|-----|------|
"""]
    for r in recs:
        ab = (r["abstract"] or f"[摘要见原文](https://doi.org/{r['doi']})").replace("|", "\\|").replace("\n", " ")
        doi = r["doi"].replace("|", "\\|")
        md.append(f"| {r['no']} | {r['year']} | [{r['title']}](https://doi.org/{r['doi']}) | {r['authors']} | {r['journal']} | [{doi}](https://doi.org/{r['doi']}) | {ab} |\n")
    md.append(f"""
## 附注
1. 本表为按标题相关度筛选的代表性文献集（非穷举），引用前请点 DOI 核对原文。
2. 检索时间 {span}（Crossref REST API）；原始数据 {os.path.basename(a.jsonfile)}。
3. Zotero 导入：双击/打开 RIS 文件即可，文件名即自动创建的文库名：**{coll}**。
""")
    os.makedirs(a.outdir, exist_ok=True)
    md_path = os.path.join(a.outdir, f"{kw}_papers_FT50-UTD24.md")
    open(md_path, "w").write("".join(md))

    # ---------- HTML ----------
    def esc(s):
        return html.escape(str(s), quote=True)
    rows = []
    for r in recs:
        ab = r["abstract"] or "摘要见原文链接"
        rows.append(f"""<tr><td class="num">{r['no']}</td><td>{r['year']}</td>
<td class="title"><a href="https://doi.org/{esc(r['doi'])}" target="_blank">{esc(r['title'])}</a></td>
<td class="auth">{esc(r['authors'])}</td><td class="jrnl">{esc(r['journal'])}</td>
<td class="doi"><a href="https://doi.org/{esc(r['doi'])}" target="_blank">{esc(r['doi'])}</a></td>
<td class="abs">{esc(ab)}</td></tr>""")
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FT50/UTD24 · {esc(kw)} 主题论文检索</title>
<style>
:root{{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#c9d1d9;--muted:#8b949e;--accent:#58a6ff;--gold:#d29922}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,"Segoe UI",Helvetica,Arial,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.55;padding:24px}}
.wrap{{max-width:1400px;margin:0 auto}}
h1{{font-size:1.6rem;color:#f0f6fc}} .sub{{color:var(--muted);font-size:.88rem;margin:6px 0 16px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.stat{{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:10px 18px}}
.stat b{{font-size:1.3rem;color:var(--gold)}} .stat span{{color:var(--muted);font-size:.8rem;display:block}}
.toolbar{{margin-bottom:14px}} input{{background:#0d1117;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:7px 12px;font-size:.85rem;width:300px}}
table{{width:100%;border-collapse:collapse;font-size:.84rem;background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow:hidden}}
th{{background:#1c2128;color:var(--muted);font-size:.75rem;text-transform:uppercase;letter-spacing:.4px;padding:9px 10px;text-align:left;position:sticky;top:0}}
td{{padding:9px 10px;border-bottom:1px solid var(--border);vertical-align:top}} tr:hover td{{background:#1c2128}}
td.num{{color:var(--muted);width:40px}} td.title a{{color:var(--accent);text-decoration:none}} td.title a:hover{{text-decoration:underline}}
td.auth,td.jrnl{{color:var(--muted);white-space:nowrap}} td.jrnl{{font-style:italic}}
td.doi a{{color:var(--muted);font-size:.78rem;word-break:break-all}} td.doi a:hover{{color:var(--accent)}}
td.abs{{max-width:440px;color:#a8b3bf;font-size:.8rem}}
.note{{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--gold);border-radius:6px;padding:10px 14px;font-size:.82rem;margin-bottom:20px;color:var(--muted)}}
footer{{margin-top:24px;color:var(--muted);font-size:.78rem}}
</style></head><body><div class="wrap">
<h1>FT50 / UTD24 期刊 · "{esc(kw)}" 主题论文导航</h1>
<p class="sub">覆盖 51 种 FT50+UTD24 期刊 · {esc(span)} · Crossref 元数据全量检索 · 关键词: {esc(', '.join(d.get('keyword', [])))}</p>
<div class="stats"><div class="stat"><b>{len(recs)}</b><span>入选论文</span></div>
<div class="stat"><b>{n_ab}</b><span>含可展示摘要</span></div>
<div class="stat"><b>{n_j}</b><span>覆盖期刊</span></div></div>
<div class="note">每刊按标题相关度保留代表作（非全量穷举）；点击 DOI 链接可查看官方原文页的完整摘要与关键词。</div>
<div class="toolbar"><input id="q" placeholder="搜索标题 / 作者 / 期刊 / 摘要…"></div>
<table><thead><tr><th>#</th><th>年份</th><th>标题（点击看原文）</th><th>作者</th><th>期刊</th><th>DOI</th><th>摘要（节选）</th></tr></thead>
<tbody id="tb">{chr(10).join(rows)}</tbody></table>
<footer>数据源：Crossref REST API · ft50-utd24-literature-search skill · 引用前请核对原文</footer></div>
<script>
document.getElementById('q').oninput=e=>{{
  const q=e.target.value.toLowerCase();
  [...document.getElementById('tb').rows].forEach(tr=>{{tr.style.display=!q||tr.textContent.toLowerCase().includes(q)?'':'none';}});
}};
</script></body></html>"""
    html_path = os.path.join(a.outdir, f"{kw}_papers_FT50-UTD24.html")
    open(html_path, "w").write(html_doc)
    print(f"WROTE {md_path}\nWROTE {html_path}")

if __name__ == "__main__":
    main()
