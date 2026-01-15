# AI Analysis 金融市场分析系统

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Claude API](https://img.shields.io/badge/Claude-3.5%20Sonnet-orange.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

基于热点新闻数据，利用 **Anthropic Claude 3.5** 进行金融市场影响分析。支持 **Function Calling** 实时获取市场数据和技术指标，覆盖 **A股、美股、港股** 三个市场。

## ✨ 核心功能

### 📰 新闻分析引擎

- 解析热点新闻 Markdown 文件
- 提取核心要点和市场信号
- 评估板块影响（科技、金融、消费、医疗等）
- 生成投资建议和风险提示

### 📊 大盘复盘分析

- 主要指数行情（上证、深证、创业板、道琼斯、恒生等）
- 涨跌统计（涨停/跌停、涨跌家数）
- 资金流向（北向/南向资金）
- 板块表现（领涨/领跌板块）

### 🔧 Function Calling 工具集

支持 **13+ 个实时数据工具**，Claude 可在分析过程中自动调用：

| 工具名称 | 功能描述 |
|:--------|:---------|
| `evaluate_sector_impact` | 板块影响评估（结构化输出） |
| `get_stock_price` | 获取股票实时价格 |
| `get_index_price` | 获取大盘指数数据 |
| `search_stock` | 根据关键词搜索股票代码 |
| `get_market_overview` | 获取大盘复盘数据（A股/美股/港股） |
| `calculate_bias` | 计算乖离率（追高风险判断） |
| `check_ma_alignment` | 检查均线排列状态 |
| `calculate_trend_score` | 计算趋势综合评分（0-100分） |
| `get_realtime_quote` | 获取增强行情（量比、换手率等） |
| `get_chip_distribution` | 获取筹码分布（仅A股） |
| `calculate_rsi` | 计算 RSI 技术指标 |
| `calculate_macd` | 计算 MACD 指标 |
| `comprehensive_analysis` | 综合技术分析 |

### 📈 技术分析系统

- **均线分析**：MA5/MA10/MA20/MA60 多头/空头排列检测
- **乖离率（BIAS）**：追高风险预警
- **趋势评分**：0-100分综合评估 + 交易检查清单
- **技术指标**：RSI、MACD、布林带、均线交叉

---

## 🛠️ 项目结构

```
nodevops/
├── ai_analysis/                    # AI 分析核心模块
│   ├── __init__.py                 # 模块入口
│   ├── analyzer.py                 # 新闻分析引擎（支持 Function Calling）
│   ├── prompts.py                  # AI Prompt 模板管理
│   ├── report_generator.py         # 分析报告生成器
│   ├── market_overview.py          # 大盘复盘数据提供器
│   ├── market_scorer.py            # 市场影响评分器
│   └── functions/                  # Function Calling 工具
│       ├── __init__.py
│       ├── tools.py                # 工具注册表（Anthropic 格式）
│       ├── market_data.py          # 市场数据提供器（akshare）
│       └── technical.py            # 技术分析器（funcat3）
├── run_analysis.py                 # AI 新闻分析入口脚本
├── run_market.py                   # 大盘复盘分析入口脚本
├── page/                           # Hugo 静态站点
│   └── src/content/post/
│       ├── news/                   # 新闻 Markdown 文件
│       ├── analysis/               # AI 分析报告输出
│       └── market/                 # 大盘复盘报告输出
└── requirements.txt                # Python 依赖
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

核心依赖：

- `anthropic` - Claude API 客户端
- `akshare` - 金融数据接口
- `funcat3` - 技术分析库
- `pandas` - 数据处理

### 2. 配置 API 密钥

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

获取 API 密钥：[Anthropic Console](https://console.anthropic.com/)

### 3. 运行分析

#### 新闻分析

```bash
# 分析今日新闻
python run_analysis.py

# 分析指定日期
python run_analysis.py --date 2026-01-15

# 分析指定文件
python run_analysis.py --file path/to/news.md

# 批量分析
python run_analysis.py --batch --limit 5
```

#### 大盘复盘

```bash
# 分析 A 股（含 AI 智能分析）
python run_market.py --market CN-A

# 分析美股
python run_market.py --market US

# 分析港股
python run_market.py --market HK

# 分析全部市场
python run_market.py --market all

# 分析指定个股
python run_market.py --stock 000001

# 禁用 AI 分析
python run_market.py --no-ai

# 仅打印不保存
python run_market.py --no-save
```

---

## 📋 交易理念

分析系统内置严格的交易理念规则：

### 🚫 严进策略（不追高）

- **乖离率 < 2%**：最佳买点区间
- **乖离率 2-5%**：可小仓介入
- **乖离率 > 5%**：**严禁追高！** 标记为"观望"

### 📈 趋势交易（顺势而为）

- **多头排列**：MA5 > MA10 > MA20 → 推荐
- **空头排列**：坚决规避

### 🎯 买点偏好（回踩支撑）

- 最佳买点：缩量回踩 MA5
- 次优买点：回踩 MA10
- 观望情况：跌破 MA20

### ⚠️ 风险排查重点

- 减持公告（股东、高管减持）
- 业绩预亏/大幅下滑
- 监管处罚/立案调查
- 行业政策利空

---

## 📊 评分标准

| 评分区间 | 信号 | 条件 |
|:--------:|:----:|:-----|
| 80-100 | 强烈买入 | 多头排列 + 低乖离率(<2%) + 放量突破 + 利好催化 |
| 60-79 | 买入 | 多头排列 + 乖离率<5% + 量能正常 |
| 40-59 | 观望 | 乖离率>5% / 均线缠绕 / 有风险事件 |
| 0-39 | 卖出/减仓 | 空头排列 / 跌破MA20 / 放量下跌 / 重大利空 |

---

## 📄 输出示例

### 分析报告结构

```markdown
---
title: "2026-01-15 市场分析报告"
date: 2026-01-15
categories: ["analysis"]
tags: ["AI分析", "市场分析"]
---

## 📊 核心要点
1. **[事件名称]** - [影响方向]: [简要分析]

## 🎯 板块影响评估
| 板块 | 方向 | 影响程度 | 置信度 | 理由 |
|------|------|----------|--------|------|
| 科技 | 利好 | 8/10 | 高 | ... |

## 📈 实时市场数据
- **上证指数**: xxxx.xx (±x.xx%)

## 💡 投资建议
**短期（1-3天）**：...
**中期（1-2周）**：...
**风险提示**：...
```

---

## 🔗 相关链接

- [Anthropic Claude API](https://docs.anthropic.com/)
- [akshare 文档](https://akshare.akfamily.xyz/)
- [funcat3 项目](https://github.com/cedricporter/funcat)

---

## 📜 License

[Apache License 2.0](LICENSE)

---

> **免责声明**: 本系统由程序自动生成分析报告，AI 分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
