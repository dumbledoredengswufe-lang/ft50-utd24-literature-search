---
name: ft50-utd24-literature-search
description: 在 FT50 与 UTD24 全部 51 种商学院顶刊中检索任意关键词（如 compensation、ESG、earnings management）过去 N 年的论文，产出含标题/作者/期刊/年份/DOI/摘要的结构化 Markdown 与深色 HTML 明细表，并生成 Zotero 可导入的 RIS 文件、自动新建同名文库。当用户要求"在 FT50/UTD24/顶刊里搜某主题论文"、"扫一遍顶刊某关键词"、"把论文导入 Zotero 新建文库"时使用本 skill。数据源为 Crossref REST API（覆盖每期目录），不依赖网页抓取。
agent_created: true
---

# FT50/UTD24 顶刊文献检索 → 明细表 → Zotero 导入

## Overview

本 skill 将"FT50 + UTD24 全部 51 刊 × 过去 20 年"的关键词文献检索打包为一条流水线：

**检索（Crossref 元数据全量覆盖每期目录）→ 生成 MD + 深色 HTML 明细表 → 生成 RIS → 触发 Zotero 导入并自动建同名文库。**

用户只需提供**一个关键词**即可全流程执行。完整期刊名录与官网见 `references/journals.md`。

## 快速开始（一条命令跑完全流程）

```bash
python3 ~/.workbuddy/skills/ft50-utd24-literature-search/scripts/run_all.py "<关键词>" \
  --synonyms "<同义词1>,<同义词2>" \
  --years 20 --cap 4 \
  --collection "<关键词> from FT50 &UTD24" \
  --outdir <输出目录> \
  --open-zotero
```

参数说明：
- `keyword`（必填）：检索词，如 `compensation`、`ESG`、`asset specificity`
- `--synonyms`：同义词/扩展词（逗号分隔），提高召回；不加则只搜关键词本身
- `--years`：回溯年数，默认 20（即 from-pub-date = 当前年-20）
- `--cap`：每刊保留篇数上限，默认 4（51 刊 × 4 ≈ 最多 200 篇；会计/金融主阵地可单独调高，见"检索策略"）
- `--collection`：Zotero 文库名，**默认 `<Keyword> from FT50 &UTD24`**（RIS 文件名即导入后自动创建的文库名）
- `--outdir`：所有产物的输出目录，默认当前目录
- `--open-zotero`：生成 RIS 后自动 `open -a Zotero` 触发导入对话框

## 执行步骤（详细）

### 第 1 步：明确检索参数

- 关键词缺失时先向用户确认；用户给的是中文时，翻译成规范英文学术词（如 "高管薪酬"→`compensation`，同义词 `ceo pay, executive pay, pay for performance`）。
- 区间默认"过去 20 年"，用户另有指定时用 `--from YYYY-MM-DD --to YYYY-MM-DD` 直接传给 search_papers.py。

### 第 2 步：运行检索（约 1-2 分钟，51 次 API 调用）

```bash
python3 ~/.workbuddy/skills/ft50-utd24-literature-search/scripts/search_papers.py "compensation" \
  --synonyms "ceo pay,bonus,incentive" --years 20 --cap 4 --outdir <输出目录>
```

- 脚本逐刊调用 Crossref API（`/works?query.title=…&query.container-title=…`），每次请求间隔 0.6s（polite pool）。
- **标题命中优先于摘要命中**；严格校验 container-title 归属，防止《Annals of …》《European …》等名字相近刊混入。
- 产物：`<keyword>_papers.json`（字段：title / authors / journal / year / doi / abstract / kw）。

### 第 3 步：生成交付物（MD + 深色 HTML）

```bash
python3 ~/.workbuddy/skills/ft50-utd24-literature-search/scripts/build_outputs.py <keyword>_papers.json \
  --collection "<Keyword> from FT50 &UTD24" --outdir <输出目录>
```

- MD 表列：# | 年份 | 标题（DOI 链接）| 作者 | 期刊 | DOI | 摘要。
- HTML 为深色 GitHub 风格单文件（无外部资源），带全文搜索框。
- 摘要可展示与否取决于出版商是否向 Crossref 开放（OUP/Springer/INFORMS 多数开放，Elsevier/Wiley 部分不开放 → 显示"摘要见原文"链接）。

### 第 4 步：生成 RIS 并导入 Zotero

```bash
python3 ~/.workbuddy/skills/ft50-utd24-literature-search/scripts/build_ris.py <keyword>_papers.json \
  --collection "<Keyword> from FT50 &UTD24"
open -a Zotero "<输出目录>/<Keyword> from FT50 &UTD24.ris"   # 或 run_all.py --open-zotero 自动执行
```

- **核心技巧**：RIS 文件名 = Zotero 导入时自动创建的新文库（Collection）名。
- Zotero 弹出导入对话框后，提示用户：勾选『将新收入的项目放入新文库』→ 点『导入』。
- RIS 每条含 TY/TI/AU/JO/PY/DO/UR/AB/KW，Zotero 联网后会按 DOI 自动补全卷期页码并尝试抓 PDF。

### 第 5 步：验证与交付

- 验证：RIS 中 `TY  - JOUR` 条数 == JSON 中 records 数；HTML 中 `doi.org` 链接数 == 条数 × 2。
- 用 present_files 交付 MD + HTML 两个文件。
- 若个别刊 FAILED（网络超时），单独重跑该刊或如实告知用户覆盖缺口。

## 检索策略（重要经验）

1. **Crossref `/journals` 路由不支持 query 参数**（返回 validation-failure），一律用 `/works` + `query.container-title`。
2. **Wiley 期刊官网 URL 用 eISSN 数字去连字符**（如 JOM = 1873-1317 → `onlinelibrary.wiley.com/journal/18731317`）。
3. **命中为 0 属正常**：AMR、HBR、MIT SMR、JMIS、M&SOM 等或因该主题发文极少、或出版商未向 Crossref 开放元数据。
4. 想提高召回：加 `--synonyms`；想深挖某几本主阵地刊（如 JFE/SMJ/TAR），单独用更大 `--cap` 再跑一次并合并去重（按 DOI）。
5. 本检索为**代表性文献集**（标题相关度排序），非穷举——交付时必须向用户说明，引用前需核对原文。
6. **断点重试**：若部分刊网络超时（日志末尾出现 FAILED journals），用 `--only` 只重跑失败刊（期刊名用 `|` 分隔），产物为 `<keyword>_papers_patch.json`，按 DOI 合并回主 JSON 后重跑 build_outputs/build_ris：

   ```bash
   python3 .../search_papers.py "<keyword>" --years 20 --cap 4 --outdir <dir> \
     --only "期刊A|期刊B"
   # 合并: 主 JSON records += patch JSON 中 DOI 未出现的记录, 清空 failed, 重建交付物
   ```
7. Zotero 本地 API（23119 端口）为**只读**，连接器协议也无法程序化建文库——因此 RIS 文件名建文库是唯一可靠的"自动建文库"路径，不要尝试直写 zotero.sqlite。

## Resources

- `scripts/search_papers.py` — Crossref 逐刊检索（参数化关键词/区间/上限）
- `scripts/build_outputs.py` — 生成 MD + 深色单文件 HTML 明细表
- `scripts/build_ris.py` — 生成 Zotero RIS（文件名即新建文库名）
- `scripts/run_all.py` — 一键编排上述三步 + 可选自动打开 Zotero
- `references/journals.md` — FT50/UTD24 全部 51 刊名录、官网、各平台浏览每期目录的路径
