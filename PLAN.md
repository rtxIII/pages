# AI 新闻分析系统实施计划

## 一、需求概述

基于 `/page/src/content/post/news/` 目录下的热点新闻 Markdown 文件，利用 AI 模型撰写金融市场影响分析文章，预测市场走势。

**核心能力**：

- 新闻解析与关键信息提取
- 市场影响评估与板块分析
- **结构化数据输出（通过 Function Calling）**
- **实时市场数据集成（通过 Function Calling）**

## 二、技术方案（已确认）

| 配置项       | 方案                           |
|--------------|--------------------------------|
| AI 模型      | **Anthropic Claude 3.5 Sonnet** (支持 Function Calling) |
| SDK          | **anthropic** Python 库 |
| 密钥管理     | **环境变量** (`ANTHROPIC_API_KEY`) |
| 聚焦领域     | 科技、金融、消费、医疗          |
| 输出位置     | `page/src/content/post/analysis/` |
| 执行频率     | 每日一次                        |
| **Function Calling** | **启用** - 结构化输出 + 数据获取 |

## 三、系统架构

### 3.1 核心数据流

```text
新闻数据流:
  news/*.md → AI 分析器 → Function Calling → 结构化评分 → analysis/*.md
                              ↓
                         实时数据获取
                    (股价/指数/行业数据)
```

### 3.2 目录结构

```text
scripts/ai_analysis/
├── __init__.py
├── analyzer.py          # 核心分析器（集成 Function Calling）
├── prompts.py           # Prompt 模板
├── market_scorer.py     # 市场影响评分
├── report_generator.py  # 报告生成器
├── functions/           # Function Calling 工具集 ⭐ 新增
│   ├── __init__.py
│   ├── tools.py         # 工具函数定义
│   ├── market_data.py   # 市场数据获取
│   └── technical.py     # 技术分析函数
```

## 四、Function Calling 设计 ⭐ 新增

### 4.1 应用场景

#### 场景1：结构化板块影响评分

**目标**: 强制 AI 输出标准化的 JSON 格式评分数据

**工具定义**:

```python
{
  "type": "function",
  "function": {
    "name": "evaluate_sector_impact",
    "strict": True,  # 启用严格模式
    "description": "评估新闻对特定板块的市场影响",
    "parameters": {
      "type": "object",
      "properties": {
        "sector": {
          "type": "string",
          "enum": ["科技", "金融", "消费", "医疗", "能源", "工业"]
        },
        "direction": {
          "type": "string",
          "enum": ["利好", "利空", "中性"]
        },
        "impact_score": {
          "type": "integer",
          "minimum": 1,
          "maximum": 10
        },
        "confidence": {
          "type": "string",
          "enum": ["高", "中", "低"]
        },
        "reasoning": {
          "type": "string",
          "description": "影响评估理由"
        }
      },
      "required": ["sector", "direction", "impact_score", "confidence", "reasoning"],
      "additionalProperties": False
    }
  }
}
```

#### 场景2：实时市场数据获取

**目标**: 在分析过程中获取实时股价、指数等数据

**工具定义**:

```python
{
  "type": "function",
  "function": {
    "name": "get_stock_price",
    "description": "获取指定股票的实时价格和涨跌幅",
    "parameters": {
      "type": "object",
      "properties": {
        "symbol": {
          "type": "string",
          "description": "股票代码，如 NVDA, AAPL"
        },
        "market": {
          "type": "string",
          "enum": ["US", "CN-A", "HK"],
          "description": "市场代码"
        }
      },
      "required": ["symbol", "market"]
    }
  }
}
```

#### 场景3：技术指标计算

**工具定义**:

```python
{
  "type": "function",
  "function": {
    "name": "calculate_technical_indicator",
    "description": "计算技术指标（RSI、MACD等）",
    "parameters": {
      "type": "object",
      "properties": {
        "indicator": {
          "type": "string",
          "enum": ["RSI", "MACD", "MA", "BOLL"]
        },
        "symbol": {"type": "string"},
        "period": {"type": "integer", "default": 14}
      },
      "required": ["indicator", "symbol"]
    }
  }
}
```

### 4.2 工作流程

```text
1. 用户输入新闻数据
   ↓
2. AI 分析新闻内容
   ↓
3. AI 决定调用函数
   - evaluate_sector_impact() → 生成结构化评分
   - get_stock_price() → 获取相关股票数据
   - calculate_technical_indicator() → 计算技术指标
   ↓
4. 系统执行函数并返回结果
   ↓
5. AI 基于函数结果生成最终分析
   ↓
6. 输出 Markdown 报告 + JSON 数据
```

### 4.3 优势分析

| 功能 | 传统 Prompt | Function Calling |
|------|-------------|------------------|
| 数据结构化 | 解析不稳定 | ✅ 强制 JSON Schema |
| 实时数据 | ❌ 无法获取 | ✅ 调用外部 API |
| 准确性 | 依赖 Prompt | ✅ 验证 + 类型检查 |
| 可扩展性 | 重写 Prompt | ✅ 新增函数定义 |

## 五、实施步骤（更新）

### 5.1 创建模块文件

- [x] `scripts/ai_analysis/__init__.py` - 模块初始化
- [x] `scripts/ai_analysis/prompts.py` - AI Prompt 模板
- [x] `scripts/ai_analysis/analyzer.py` - 核心分析逻辑
- [x] `scripts/ai_analysis/market_scorer.py` - 市场影响评分
- [x] `scripts/ai_analysis/report_generator.py` - 报告生成

**⭐ 新增 Function Calling 模块**:

- [x] `scripts/ai_analysis/functions/__init__.py`
- [x] `scripts/ai_analysis/functions/tools.py` - 工具函数定义（8个函数）
- [x] `scripts/ai_analysis/functions/market_data.py` - 市场数据获取（akshare）
- [x] `scripts/ai_analysis/functions/technical.py` - 技术分析（funcat3）

### 5.2 配置扩展

- [x] 更新 `config/config.yaml` - 新增 `ai_analysis` 配置节
- [x] 更新 `.env.example` - 添加 Anthropic API 环境变量说明
- [x] 更新 `requirements.txt` - 新增 anthropic、akshare、funcat3 等依赖

### 5.3 工作流集成

- [x] 创建/更新 GitHub Actions workflow - 每日定时分析
- [x] 创建本地执行脚本 - `scripts/run_analysis.py`

## 六、输出格式（增强）

### 6.1 Markdown 分析报告

```markdown
+++
date = "2026-01-06"
title = "AI市场分析: 2026-01-06"
description = "基于热点新闻的金融市场影响分析"
tags = ["analysis", "ai", "market"]
categories = ["analysis"]
sectors = ["科技", "金融"]
sentiment = "bullish"
+++

## 📊 核心要点

1. **英伟达 Rubin 平台发布** - 利好 AI 芯片供应链
2. **美国政策动向** - 地缘风险溢价上升

## 🎯 板块影响评估 (Function Calling 结构化输出)

| 板块 | 方向 | 影响程度 | 置信度 | 理由 | 相关股票 |
|------|------|----------|--------|------|----------|
| 科技-AI | 利好 | 8/10 | 高 | 英伟达新平台发布 | NVDA ↑2.3% |
| 金融 | 中性 | 4/10 | 中 | 无直接影响 | - |

## 📈 实时市场数据 (Function Calling 获取)

- **NVDA**: $850.23 (+2.34%)
- **纳指**: 18,234 (+0.5%)

## 💡 投资建议

**短期（1-3天）**：科技板块受消息面提振
**中期（1-2周）**：警惕地缘政治发酵
```

### 6.2 JSON 结构化数据（新增）

```json
{
  "date": "2026-01-06",
  "sector_impacts": [
    {
      "sector": "科技",
      "direction": "利好",
      "impact_score": 8,
      "confidence": "高",
      "reasoning": "英伟达新平台发布提振AI供应链预期"
    }
  ],
  "market_data": {
    "NVDA": {"price": 850.23, "change_pct": 2.34},
    "^NDX": {"price": 18234, "change_pct": 0.5}
  },
  "technical_indicators": {
    "NVDA": {"RSI": 68, "signal": "neutral"}
  }
}
```

## 七、验证计划（增强）

### 7.1 单元测试

```bash
# 测试 Function Calling 工具
python -m pytest scripts/ai_analysis/functions/tests/ -v

# 测试完整分析流程
python -m pytest scripts/ai_analysis/tests/ -v
```

### 7.2 Function Calling 验证

```bash
# 测试结构化输出
python scripts/run_analysis.py --test-function evaluate_sector_impact

# 测试市场数据获取
python scripts/run_analysis.py --test-function get_stock_price --symbol NVDA
```

### 7.3 手动验证

```bash
# 运行完整分析
python scripts/run_analysis.py

# 检查 JSON 输出
cat output/analysis_data/2026/01/2026-01-06-structured.json
```

## 八、待办事项（更新）

- [x] 实现基础模块文件
- [x] **实现 Function Calling 工具集**
  - [x] 板块影响评估函数
  - [x] 市场数据获取接口（akshare）
  - [x] 技术指标计算（funcat3）
  - [x] 工具注册表和执行器
- [x] **更新 analyzer.py 集成 Function Calling**
- [x] 配置 Anthropic API 密钥（环境变量）
- [ ] 编写单元测试（包含 Function Calling 测试）
- [ ] 本地测试验证
- [ ] 集成到 CI/CD（GitHub Actions 已创建）

## 九、技术栈

- **AI 模型**: Anthropic Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Python SDK**: anthropic>=0.40.0
- **数据源**: akshare>=1.14.0 (A股/美股/港股实时数据)
- **技术分析**: funcat3>=0.1.0 (技术指标计算)
- **数据处理**: pandas, numpy, scikit-learn

## 十、技术参考

- **Anthropic Claude API**: <https://docs.anthropic.com/en/api/getting-started>
- **Claude Function Calling**: <https://docs.anthropic.com/en/docs/tool-use>
- **akshare 文档**: <https://akshare.akfamily.xyz/>
- **funcat3 GitHub**: <https://github.com/mapicccy/funcat>
- **JSON Schema**: <https://json-schema.org/>
