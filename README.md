# FT50/UTD24 Literature Search → Markdown/HTML → Zotero

> 在 **FT50 + UTD24 全部 51 种商学院顶刊**中，按任意关键词一键检索过去 N 年的论文，产出结构化明细表（Markdown + 深色 HTML）与 Zotero RIS 文件——**RIS 文件名即导入时自动创建的 Zotero 文库（Collection）名**。
>
> One-command keyword search across **all 51 FT50/UTD24 business-research journals** via the Crossref REST API, producing Markdown / dark-theme HTML tables and a Zotero RIS file that auto-creates a named collection on import.

- **数据源 Data source**：Crossref REST API 官方元数据（等价于逐期扫描目录），无网页抓取
- **零依赖 Dependencies**：仅使用 Python 标准库，无需 `pip install`
- **实测案例 Example run**：关键词 `ESG` + `CSR`、过去 20 年、51 刊 → **140 篇去重论文，覆盖 34 刊，全部成功导入 Zotero**

## 流水线 Pipeline

```
关键词 + 同义词
      │
      ▼
Crossref /works 逐刊检索（51 刊，每次请求间隔 0.6s）
      │  标题/摘要命中，期刊归属严格校验，标题命中优先
      ▼
<keyword>_papers.json  ──►  Markdown 明细表 + 深色单文件 HTML（自带搜索框）
      └───────────────►  Zotero RIS（文件名 = 自动新建的文库名）
                                   │
                                   ▼
                          open -a Zotero → 一键导入
```

## 功能特性 Features

- 一次调用覆盖 FT50 + UTD24 全部 **51 刊**（会计 6 / 金融 5 / 经济 5 / 管理 15 / 心理学 2 / 营销 6 / 运营 5 / 信统 4 / 实务与创新 3，完整名录见 [`references/journals.md`](references/journals.md)）
- 支持同义词/扩展词（`--synonyms`），中英文关键词均可（中文需自行翻译为规范英文学术词）
- 标题命中优先于摘要命中；container-title 规范化精确匹配，防止名称相近的非目标刊混入
- 每刊保留篇数可调（`--cap`），按相关度 + 年份排序
- 失败期刊支持断点重试（`--only`），产物按 DOI 合并回主结果
- HTML 为无外部资源的单文件，深色 GitHub 风格，带全文实时搜索框
- RIS 每条含 TY/TI/AU/JO/PY/DO/UR/AB/KW；Zotero 联网后按 DOI 自动补全卷期页码并尝试抓取 PDF

## 快速开始 Quick Start

```bash
git clone https://github.com/dumbledoredengswufe-lang/ft50-utd24-literature-search.git
cd ft50-utd24-literature-search

# 一条命令跑完全流程（检索 → MD/HTML → RIS → 唤起 Zotero）
python3 scripts/run_all.py "ESG" \
  --synonyms "corporate social responsibility,CSR,environmental social governance" \
  --years 20 --cap 4 \
  --collection "ESG & CSR from FT50 &UTD24" \
  --outdir ./output \
  --open-zotero
```

Zotero 弹出导入对话框后：勾选 **「将新收入的项目放入新文库 / Place imported items into a new collection」** → 点击「导入」，同名文库自动创建。

### 分步执行

```bash
# 1. 逐刊检索（约 1-2 分钟，51 次 API 调用）
python3 scripts/search_papers.py "compensation" \
  --synonyms "ceo pay,executive pay,pay for performance" --years 20 --cap 4 --outdir ./output

# 2. 生成 Markdown + 深色 HTML 明细表
python3 scripts/build_outputs.py output/compensation_papers.json \
  --collection "Compensation from FT50 &UTD24" --outdir ./output

# 3. 生成 RIS（文件名 = Zotero 新建文库名）
python3 scripts/build_ris.py output/compensation_papers.json \
  --collection "Compensation from FT50 &UTD24"
```

## 参数说明 Arguments

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 检索词（位置参数，必填），如 `ESG`、`earnings management` | — |
| `--synonyms` | 同义词/扩展词，逗号分隔，提高召回 | 无 |
| `--years` | 回溯年数 | `20` |
| `--cap` | 每刊保留篇数上限（51 刊 × N） | `4` |
| `--from` / `--to` | 精确日期区间 `YYYY-MM-DD`（指定后覆盖 `--years`） | 近 20 年至今 |
| `--collection` | Zotero 文库名 / RIS 文件名 | `<Keyword> from FT50 &UTD24` |
| `--outdir` | 所有产物输出目录 | 当前目录 |
| `--only` | 仅重跑指定期刊（`\|` 分隔），用于失败刊断点续跑 | 无 |
| `--open-zotero` | 生成 RIS 后自动唤起 Zotero（仅 run_all.py，macOS） | 关闭 |

## 输出产物 Outputs

| 文件 | 内容 |
|------|------|
| `<keyword>_papers.json` | 原始结构化元数据：title / authors / journal / year / doi / abstract / subject |
| `<keyword>_papers_FT50-UTD24.md` | Markdown 明细表（标题与 DOI 均为可点击链接） |
| `<keyword>_papers_FT50-UTD24.html` | 深色单文件 HTML，带统计卡片与全文搜索框 |
| `<Collection>.ris` | Zotero RIS，文件名即导入后自动创建的文库名 |

## 检索策略与注意事项 Notes

1. **Crossref `/journals` 路由不支持 query 参数**，本工具一律使用 `/works` + `query.container-title`。
2. 结果为**按标题相关度排序的代表性文献集，非穷举**。主阵地刊（如 JBE / TAR / JFE / SMJ）命中量可能远超 `--cap`，需要深挖时对该刊单独用更大上限重跑并按 DOI 合并。
3. 部分期刊命中为 0 属正常现象（主题发文少，或出版商未向 Crossref 开放元数据）。
4. 摘要是否可展示取决于出版商开放政策（OUP/Springer/INFORMS 多数开放；Elsevier/Wiley 部分不开放），未开放时表中提供 DOI 原文链接。
5. **引用前务必通过 DOI 核对原文。**
6. Zotero 本地 API（23119 端口）只读，无法程序化创建文库——「RIS 文件名 = 新文库名」是最可靠的自动建库方式，请勿直写 `zotero.sqlite`。

## 运行环境 Requirements

- Python 3.8+（仅标准库：urllib / json / argparse / html / re）
- 可访问 `https://api.crossref.org` 的网络环境
- Zotero Desktop（可选，仅 RIS 导入环节需要；macOS 下 `--open-zotero` 自动唤起）

## 目录结构 Layout

```
ft50-utd24-literature-search/
├── README.md
├── SKILL.md                      # AI Agent Skill 清单（触发场景与操作规范）
├── references/
│   └── journals.md               # FT50/UTD24 全部 51 刊名录与官网
└── scripts/
    ├── search_papers.py          # Crossref 逐刊检索
    ├── build_outputs.py          # 生成 Markdown + 深色 HTML
    ├── build_ris.py              # 生成 Zotero RIS
    └── run_all.py                # 一键编排
```

## 作为 AI Agent Skill 安装

将本仓库放到 Agent 的 skills 目录（如 `~/.workbuddy/skills/ft50-utd24-literature-search/`），Agent 即可在用户提出「在 FT50/UTD24/顶刊里搜某主题论文」「把论文导入 Zotero 新建文库」等需求时自动加载 `SKILL.md` 执行。

## 免责声明 Disclaimer

本工具仅聚合 Crossref 公开元数据用于学术文献检索，论文版权归原出版商所有；请遵守各出版商使用条款与 Zotero 抓取规范。
