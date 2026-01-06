# AI 新闻分析系统 - 快速开始

## 📋 前置要求

1. Python 3.10+
2. llmlite API 访问权限
3. 至少一个新闻 Markdown 文件在 `page/src/content/post/news/` 目录

## 🚀 快速启动

### 1. 配置环境变量

```bash
# 方式一：直接设置
export LLMLITE_API_KEY="your-api-key"
export LLMLITE_API_ENDPOINT="https://api.example.com/v1/chat/completions"  # 可选

# 方式二：使用 .env 文件
cp .env.example .env
# 编辑 .env 填入实际密钥
source .env
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行分析

#### 分析今日新闻

```bash
python scripts/run_analysis.py
```

#### 分析指定日期

```bash
python scripts/run_analysis.py --date 2026-01-06
```

#### 分析指定文件

```bash
python scripts/run_analysis.py --file page/src/content/post/news/2026/01/2026-01-06-美国-国产-英伟达-AI.md
```

#### 批量分析（最近5天）

```bash
python scripts/run_analysis.py --batch --limit 5
```

## 📂 输出位置

分析报告将保存在：

```
page/src/content/post/analysis/
├── 2026/
│   └── 01/
│       └── 2026-01-06-market-analysis.md
```

## 🧪 测试验证

### 手动测试步骤

1. **检查模块导入**

```bash
python -c "from scripts.ai_analysis import NewsAnalysisEngine; print('✅ Import successful')"
```

2. **验证配置加载**

```bash
python -c "
from trend.core import load_config
config = load_config('config/config.yaml')
print('AI Analysis Enabled:', config.get('ai_analysis', {}).get('enabled'))
"
```

3. **测试文件解析**

```bash
python -c "
from scripts.ai_analysis.analyzer import NewsAnalysisEngine
engine = NewsAnalysisEngine()
result = engine.parse_news_markdown('page/src/content/post/news/2026/01/2026-01-06-美国-国产-英伟达-AI.md')
print(f'✅ Parsed {len(result[\"news_items\"])} news items')
print(f'Keywords: {result[\"hot_keywords\"][:5]}')
"
```

4. **运行完整分析**

```bash
python scripts/run_analysis.py --file page/src/content/post/news/2026/01/2026-01-06-美国-国产-英伟达-AI.md
```

5. **检查输出文件**

```bash
ls -la page/src/content/post/analysis/2026/01/
cat page/src/content/post/analysis/2026/01/2026-01-06-market-analysis.md
```

## ⚙️ GitHub Actions 配置

### 1. 设置 Secrets

在 GitHub 仓库设置中添加：

- `LLMLITE_API_KEY`: LLM API 密钥

### 2. 设置 Variables（可选）

- `LLMLITE_API_ENDPOINT`: API 端点（如果不同于默认）

### 3. 手动触发

1. 进入 Actions 页面
2. 选择 "ai-news-analysis" workflow
3. 点击 "Run workflow"
4. 选择参数（日期/批量模式等）

### 4. 自动执行

- 默认每天 21:00 (UTC+8) 自动执行分析
- 修改时间：编辑 `.github/workflows/ai-analysis.yml` 中的 cron 表达式

## 🐛 常见问题

### API 调用失败

**症状**: 显示 "API 调用失败"

**解决方案**:

1. 检查环境变量是否正确设置：`echo $LLMLITE_API_KEY`
2. 确认 API endpoint 可访问
3. 查看详细错误日志

### 新闻文件未找到

**症状**: "FileNotFoundError: 未找到日期的新闻文件"

**解决方案**:

1. 确认新闻文件存在：`ls page/src/content/post/news/2026/01/`
2. 检查日期格式是否正确 (YYYY-MM-DD)
3. 使用 `--file` 参数直接指定文件路径

### 分析结果不理想

**解决方案**:

1. 调整 `config/config.yaml` 中的 `temperature` 参数
2. 修改 `scripts/ai_analysis/prompts.py` 中的 Prompt 模板
3. 增加或减少 `focus_sectors` 聚焦板块

## 📊 输出示例

生成的分析报告格式：

```markdown
+++
date = "2026-01-06"
title = "AI市场分析: 2026-01-06"
tags = ["analysis", "ai", "market", "bullish"]
categories = ["analysis"]
sectors = ["科技", "金融"]
sentiment = "bullish"
+++

## 📊 核心要点

1. 英伟达 Rubin 平台发布: 利好 AI 芯片供应链
2. 美国政策动向: 地缘风险溢价上升
...

## 🎯 板块影响评估

| 板块 | 方向 | 影响程度 | 置信度 | 理由 |
|------|------|----------|--------|------|
| 科技 | 利好 | 8/10 | 高 | ... |
...

## 💡 投资建议

**短期（1-3天）**：...
**中期（1-2周）**：...
**风险提示**：...
```

## 🔄 持续优化

1. **Prompt 优化**: 根据实际效果调整 `prompts.py`
2. **评分规则**: 优化 `market_scorer.py` 的解析逻辑
3. **板块分类**: 扩展或调整 `focus_sectors` 列表
4. **输出格式**: 自定义 `report_generator.py` 的模板

## 📝 开发说明

### 模块结构

```
scripts/ai_analysis/
├── __init__.py          # 模块入口
├── analyzer.py          # 核心分析引擎
├── prompts.py           # Prompt 模板管理
├── market_scorer.py     # 市场影响评分
└── report_generator.py  # 报告生成器
```

### 扩展新功能

1. **添加新的分析维度**: 修改 `prompts.py` 中的 Prompt
2. **新增评分指标**: 扩展 `market_scorer.py` 的数据类
3. **自定义报告格式**: 修改 `report_generator.py` 的模板

## 📞 支持

遇到问题请查看：

1. 详细日志输出
2. 配置文件 `config/config.yaml`
3. 示例环境变量 `.env.example`
