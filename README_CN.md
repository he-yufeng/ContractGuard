<div align="center">

<img src="docs/banner.png" alt="ContractGuard — 再也不用盲签合同了" width="100%">

上传任意合同 → 秒级识别霸王条款、不公平条款，用大白话解释给你听。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/he-yufeng/ContractGuard/actions/workflows/ci.yml/badge.svg)](https://github.com/he-yufeng/ContractGuard/actions)

**[English](README.md) · [中文](README_CN.md)** &nbsp;·&nbsp; [效果演示](#效果演示) · [快速上手](#快速上手) · [工作原理](#工作原理)

</div>

---

## 为什么做 ContractGuard？

每年有数百万人签下自己并不真正理解的合同 — 租房合同里藏着天价违约金，劳动合同里的竞业禁止范围大到离谱，保密协议悄悄剥夺你的权利。请律师审合同要 300-500 元/小时。大多数人的选择是：闭眼签字，祈祷没坑。

**ContractGuard** 改变了这一切。它是一个开源 AI Agent，能读完合同里的每一条每一款，用大白话标出问题，告诉你该怎么谈判 — 整个过程不到 30 秒。

**和直接丢给 ChatGPT 有什么不同？**
- **结构化分析**，不是一大段文字 — 你会得到分类好的红旗警告、注意事项、保护条款和公平性评分
- **每个问题都有可操作的建议** — 不只是说"这不好"，而是告诉你"改成这样"
- **一致的输出格式**（Pydantic 模型）— 方便集成到其他工具
- **CLI 优先** — 一条命令，漂亮的终端输出，不需要打开浏览器
- **支持任何 LLM** — OpenRouter、OpenAI、Ollama（完全本地/隐私）

## 效果演示

```bash
contractguard scan 租房合同.pdf
```

```
✔ 已解析 租房合同.pdf（4,521 字符）

⬤ 红旗警告（发现 5 项）
==================================================

  1. 押金不退
     条款：第三条
     "押金不予退还，合同终止时由出租方保留"
     大部分地区法规要求押金可退。此条款可能违法。
     建议：删除"不予退还"表述。

  2. 房东可随时进入无需通知
     条款：第五条
     "出租方有权随时进入房屋，无需提前通知"
     法律通常要求提前 24 小时书面通知。
     建议：增加"需提前 24 小时书面通知"

  3. 租客承担房屋结构维修
     条款：第四条
     "承租方负责所有维修，包括管道、电气和结构部分"
     结构维修通常是房东的责任。
     建议：限制租客责任为日常小修。

  4. 单方面解约权
     条款：第十条
     "出租方可随时提前 30 天通知解约，无需理由"
     租客没有对等权利，造成不平衡。
     建议：增加双方对等解约权或要求有正当理由。

  5. 租客承担房东律师费（无论胜败）
     条款：第十二条
     "无论诉讼结果如何，承租方须承担出租方全部律师费"
     单方面费用转嫁会打压租客维权。
     建议：改为败诉方承担双方律师费。

⚠ 注意事项（发现 3 项）
==================================================

  1. 不续约需提前 90 天通知
     建议：协商缩短到 30-60 天。

  2. 续约时租金可涨 15%
     建议：协商更低上限或挂钩 CPI。

  3. 未经房东同意不得转租（房东可无理由拒绝）
     建议：增加"不得无理由拒绝"。

✔ 保护条款（发现 2 项）
==================================================
  ✔ 解约需书面通知（第一条）
  ✔ 合同修改需双方书面同意（第十三条）

❓ 缺失保护（4 项）
  ✗ 无居住适宜性保证
  ✗ 违约无宽限期即可终止
  ✗ 滞纳金无上限
  ✗ 无退房后押金退还规定

公平性评分: D (28/100)
  5 项红旗  3 项注意  2 项保护  4 项缺失
```

## 快速上手

### 1. 安装

```bash
pip install contractguard
```

### 2. 配置 API Key

ContractGuard 兼容任何 OpenAI 协议的 API，选一种即可：

**方式 A：OpenRouter（推荐）** — 一个 key 访问 Claude、GPT-4、DeepSeek、Gemini 等 100+ 模型：

```bash
export OPENROUTER_API_KEY=sk-or-...
```

**方式 B：直接用 OpenAI：**

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1
```

**方式 C：本地模型（Ollama）** — 合同数据完全不出本机：

```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
```

### 3. 扫描合同

```bash
contractguard scan 合同.pdf
```

三步搞定，60 秒以内。

## 用法详解

### CLI 命令

```bash
# 基本扫描 — 支持 PDF、DOCX、TXT
contractguard scan lease.pdf
contractguard scan 劳动合同.docx
contractguard scan 保密协议.txt

# 指定模型
contractguard scan contract.pdf --model openai/gpt-4o
contractguard scan contract.pdf --model anthropic/claude-sonnet-4
contractguard scan contract.pdf --model google/gemini-2.5-pro
contractguard scan contract.pdf --model llama3.1    # 本地 Ollama

# 导出 Markdown 报告
contractguard scan contract.pdf --output report.md

# 输出结构化 JSON（方便脚本集成）
contractguard scan contract.pdf --json

# 直接保存结构化 JSON
contractguard scan contract.pdf --json --output report.json

# 直接传 API key（不用环境变量）
contractguard scan contract.pdf --api-key sk-or-...
```

### Python API

在你的项目中作为库使用：

```python
from contractguard.analyzer import analyze_contract
from contractguard.parser import extract_text

# 第 1 步：提取文本
text = extract_text("租房合同.pdf")

# 第 2 步：AI 分析
result = analyze_contract(text)

# 第 3 步：使用结构化结果
print(f"合同类型: {result.contract_type.value}")
print(f"公平性: {result.fairness_grade} ({result.fairness_score}/100)")
print(f"当事人: {', '.join(result.parties)}")

print(f"\n{len(result.red_flags)} 项红旗警告:")
for flag in result.red_flags:
    print(f"  - {flag.title}（条款: {flag.clause}）")
    print(f"    问题: {flag.explanation}")
    print(f"    建议: {flag.suggestion}")

print(f"\n{len(result.warnings)} 项注意事项:")
for w in result.warnings:
    print(f"  - {w.title}: {w.explanation}")

print(f"\n{len(result.good_clauses)} 项保护条款:")
for p in result.good_clauses:
    print(f"  + {p.title}: {p.explanation}")

print(f"\n{len(result.missing_protections)} 项缺失保护:")
for m in result.missing_protections:
    print(f"  ? {m}")

# 导出 Markdown
from contractguard.report import generate_markdown_report
md = generate_markdown_report(result)
with open("report.md", "w") as f:
    f.write(md)
```

### JSON 输出格式

使用 `--json` 时输出的结构化 JSON 对象，可以 pipe 到其他工具：

```json
{
  "contract_type": "lease",
  "summary": "一份为期12个月的住宅租赁合同，包含多个偏向房东的条款...",
  "parties": ["某物业管理有限公司", "承租方"],
  "key_terms": ["期限: 12个月", "月租: 3200元", "押金: 6400元"],
  "red_flags": [
    {
      "title": "押金不退",
      "severity": "red",
      "clause": "第三条",
      "quote": "押金不予退还...",
      "explanation": "大部分地区法规要求押金可退...",
      "suggestion": "删除不予退还表述。"
    }
  ],
  "warnings": [...],
  "good_clauses": [...],
  "missing_protections": [...],
  "fairness_score": 28,
  "fairness_grade": "D"
}
```

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | `.pdf` | 文字型 PDF。扫描件/图片型 PDF 需要 OCR（即将支持） |
| Word | `.docx` | Microsoft Word 文档 |
| 纯文本 | `.txt` | 纯文本文件 |
| Markdown | `.md` | Markdown 文件 |
| 富文本 | `.rtf` | Rich Text Format 文件 |

## 支持的合同类型

ContractGuard 自动识别合同类型并针对性分析。每种类型有特定的红旗项和行业标准保护条款：

| 合同类型 | ContractGuard 检查的内容 |
|---|---|
| **租赁合同** | 租金涨幅、押金可退性、维修义务、房东出入权、提前解约罚金、居住适宜性保证 |
| **保密协议（NDA）** | "保密信息"范围是否过宽、期限、竞业限制/禁止挖角、已有知识排除、资料归还/销毁 |
| **劳动合同** | 竞业禁止范围和期限、知识产权归属（公司是否拥有你的业余项目？）、解约通知期、遣散费、试用期条款 |
| **自由职业/外包合同** | 付款条款和周期、终止费、知识产权归属、赔偿条款、范围蔓延保护、逾期付款违约金 |
| **SaaS 服务条款** | 数据所有权和可迁移性、自动续费和取消、SLA 保证、责任限制、单方面修改权 |
| **贷款合同** | 利率（固定/浮动）、提前还款违约金、违约触发条件、个人担保范围、抵押要求 |
| **买卖合同** | 保修条款、退换货政策、责任上限、争议解决方式（仲裁 vs 法院）、不可抗力 |

## 工作原理

![ContractGuard 流程](docs/architecture.png)

1. **解析** — 从文档中提取文本。PDF 使用 `pdfplumber` 处理复杂排版，DOCX 使用 `python-docx` 读取所有段落。

2. **识别** — 将提取的文本发送到 LLM，自动识别合同类型（租赁、NDA、劳动合同等），并调整分析策略。

3. **分析** — AI Agent 逐条审查每个条款，将发现分为四类：
   - **红旗警告** — 可能造成经济损失、法律责任或权益丧失的严重问题。签字前必须争取修改。
   - **注意事项** — 值得协商但不至于致命的中等问题。很多合同里都有，但你应该知情。
   - **保护条款** — 保护你利益的好条款。合同做对的地方。
   - **缺失保护** — 标准合同中应有但缺失的条款。缺失可能让你暴露在风险中。

4. **评分** — 生成公平性等级，从 A+（优秀，双方公平）到 F（严重偏向一方，多项红旗）。评分基于发现问题的数量和严重程度，与现有保护条款做平衡。

5. **报告** — 输出 Rich 格式的终端美化报告，或导出 Markdown/JSON 以便分享或进一步处理。

## 配置

### LLM 服务商

ContractGuard 使用 OpenAI 兼容 API 格式，几乎支持所有 LLM 服务商：

| 服务商 | 配置方式 | 适用场景 |
|--------|---------|---------|
| **OpenRouter** | `export OPENROUTER_API_KEY=sk-or-...` | 一个 key 访问 100+ 模型 |
| **OpenAI** | `export OPENAI_API_KEY=sk-...` + `export OPENAI_BASE_URL=https://api.openai.com/v1` | 直接使用 GPT-4o、o1 等 |
| **Anthropic（通过 OpenRouter）** | 使用 `--model anthropic/claude-sonnet-4` | 复杂合同的最佳推理能力 |
| **Ollama（本地）** | `export OPENAI_BASE_URL=http://localhost:11434/v1` | 最大隐私保障，数据不出本机 |
| **Azure OpenAI** | 将 `OPENAI_BASE_URL` 设为你的 Azure 端点 | 企业合规场景 |
| **任何 OpenAI 兼容 API** | 设置 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` | 自建模型、vLLM 等 |

### 推荐模型

| 模型 | 质量 | 速度 | 费用 | 说明 |
|------|------|------|------|------|
| `anthropic/claude-sonnet-4`（默认） | 优秀 | 快 | $$ | 质量和速度的最佳平衡 |
| `openai/gpt-4o` | 优秀 | 快 | $$ | 强力替代方案 |
| `google/gemini-2.5-pro` | 优秀 | 中 | $$ | 适合超长合同（100 万 token 上下文） |
| `deepseek/deepseek-chat` | 良好 | 快 | $ | 经济实惠的选择 |
| `llama3.1`（通过 Ollama） | 良好 | 因机器而异 | 免费 | 完全隐私，本地运行 |

## 试用示例合同

仓库里附带了故意加入大量问题的示例合同，用于测试：

```bash
git clone https://github.com/he-yufeng/ContractGuard.git
cd ContractGuard
pip install -e .

export OPENROUTER_API_KEY=sk-or-...

# 示例租赁合同 — 包含 5+ 红旗，包括押金不退、
# 房东随时入户、单方面解约权等
contractguard scan examples/sample_lease.txt

# 示例保密协议 — 包含永久保密义务和宽泛的禁止挖角条款
contractguard scan examples/sample_nda.txt
```

## ContractGuard 能抓到的常见问题

以下是 ContractGuard 设计用来检测的真实问题示例：

**租赁合同：**
- 押金不退（很多地方违法）
- 房东无需通知即可进入（大多数法律要求提前 24-48 小时）
- 租客承担结构维修（通常是房东的责任）
- 自动续约无退出窗口
- 滞纳金过高

**劳动合同：**
- 竞业禁止范围过宽（地域、时间、行业）
- 知识产权归属覆盖个人/业余项目
- 无遣散费的随意解雇
- 强制仲裁且仲裁员由公司选定

**保密协议：**
- "保密信息"定义宽泛到涵盖一切
- 永久保密义务（无到期日）
- NDA 里藏着禁止挖角条款
- 没有排除独立开发的信息

**SaaS/服务条款：**
- 服务商可随时单方面修改条款
- 终止服务后无数据导出/迁移
- 责任上限低于订阅费用
- 强制仲裁并放弃集体诉讼

## 常见问题

**这算法律建议吗？**
不算。ContractGuard 是帮你用大白话理解合同条款的教育工具，不能替代专业法律意见。涉及重大合同决策请务必咨询持证律师。

**我的合同数据会上传到云端吗？**
合同文本会发送到你配置的 LLM 服务商（OpenRouter、OpenAI 等）进行分析。如果对隐私有要求，可以通过 Ollama 使用本地模型，数据完全不出本机。ContractGuard 本身不会存储、记录或传输你的数据到任何地方。

**准确率怎么样？**
ContractGuard 使用最先进的大模型（Claude Sonnet、GPT-4o），在法律文本分析上表现出色。在测试中，它能稳定识别出与专业法律审查一致的主要红旗。但它可能遗漏细微的地方性法规差异或复杂的多条款交叉影响。把它当作"签字前先过一道"的筛查工具，不是最终意见。

**支持中文合同吗？**
支持！ContractGuard 支持底层大模型所支持的任何语言。中英文合同分析效果均好。西班牙语、法语、德语、日语、韩语合同在 Claude 和 GPT-4o 下也能正常工作。

**可以商用吗？**
可以。ContractGuard 使用 MIT 许可证 — 个人和商业项目均可自由使用，也可以集成到你的 SaaS 产品中。

**最长支持多长的合同？**
支持最多约 30,000 token（约 120,000 字符 / 约 60 页）的合同。更长的文档会自动截断。对于超长合同，建议使用大上下文窗口的模型如 `google/gemini-2.5-pro`（100 万 token）。

**能用在 CI/CD 或自动化流水线里吗？**
可以。使用 `--json` 获取结构化输出，可被其他工具解析。成功返回 exit code 0，错误返回 1。示例：`contractguard scan contract.pdf --json | jq '.red_flags | length'`

## 路线图

**已完成**：批量扫描（一次分析多份合同）、合同对比（diff 两个版本并逐条标出变化）。

**规划中**：

- **扫描件 PDF 的 OCR 支持**：处理只有图像的合同，而不只是文本 PDF——大量真实纸面合同就是这种。
- **地域法规感知分析**：按选定法域（中国各地、美国各州、欧盟）判断条款，因为一个条款风不风险，取决于它在哪里执行。
- **逐条协商意见稿生成**：对每个风险点起草替换措辞，把报告变成 redline 的起点。
- **Web 界面**：给不碰命令行的人做一个 Streamlit/Gradio 前端，保持同样的本地化处理。
- **常见合同模板**：几类常见合同 + 已知风险点，既当起点也当测试语料。

## 贡献

欢迎贡献！你可以：

- **报告 bug** — 在 [Issues](https://github.com/he-yufeng/ContractGuard/issues) 中说明合同类型和期望行为
- **增加测试合同** — 更多带有典型问题的示例合同
- **优化 prompt** — 让 LLM 分析更准确
- **多语言测试** — 用不同语言的合同测试并反馈结果
- **做集成** — MCP server、VS Code 扩展、Slack bot 等

## 许可证

[MIT](LICENSE) — 随意使用。

---

<div align="center">

**如果 ContractGuard 帮你避开了一份坑人合同，请给个 star！**

[报告问题](https://github.com/he-yufeng/ContractGuard/issues) · [功能建议](https://github.com/he-yufeng/ContractGuard/issues)

</div>
