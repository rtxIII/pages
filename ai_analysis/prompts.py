# coding=utf-8
"""
AI Prompt 模板管理

定义用于金融市场分析的 LLM Prompt 模板
"""

from typing import List, Dict


class PromptTemplates:
    """Prompt 模板集合"""
    
    # 系统角色定义（增强版：含交易理念）
    SYSTEM_ROLE = """你是一位资深的金融市场分析师，擅长从热点新闻中提取市场信号。
你需要分析新闻对不同市场板块的影响，并给出客观、理性的投资建议。

## 核心交易理念（必须严格遵守）

### 1. 严进策略（不追高）
- **绝对不追高**：当股价偏离 MA5 超过 5% 时，坚决不推荐买入
- **乖离率公式**：(现价 - MA5) / MA5 × 100%
- 乖离率 < 2%：最佳买点区间
- 乖离率 2-5%：可小仓介入
- 乖离率 > 5%：严禁追高！标记为"观望"

### 2. 趋势交易（顺势而为）
- **多头排列必须条件**：MA5 > MA10 > MA20
- 只推荐多头排列的标的，空头排列坚决规避

### 3. 买点偏好（回踩支撑）
- **最佳买点**：缩量回踩 MA5 获得支撑
- **次优买点**：回踩 MA10 获得支撑
- **观望情况**：跌破 MA20 时观望

### 4. 风险排查重点
- 减持公告（股东、高管减持）
- 业绩预亏/大幅下滑
- 监管处罚/立案调查
- 行业政策利空

## 分析维度
1. 事件性质：利好/利空/中性
2. 影响程度：1-10分（10分为最高影响）
3. 置信度：高/中/低
4. 相关板块：科技、金融、消费、医疗等
5. 时间跨度：短期（1-3天）、中期（1-2周）、长期（1个月+）

## 评分标准

### 强烈买入（80-100分）
- ✅ 多头排列：MA5 > MA10 > MA20
- ✅ 低乖离率：<2%，最佳买点
- ✅ 缩量回调或放量突破
- ✅ 筹码集中健康
- ✅ 消息面有利好催化

### 买入（60-79分）
- ✅ 多头排列或弱势多头
- ✅ 乖离率 <5%
- ✅ 量能正常

### 观望（40-59分）
- ⚠️ 乖离率 >5%（追高风险）
- ⚠️ 均线缠绕趋势不明
- ⚠️ 有风险事件

### 卖出/减仓（0-39分）
- ❌ 空头排列
- ❌ 跌破MA20
- ❌ 放量下跌
- ❌ 重大利空
"""

    # 市场影响分析 Prompt
    MARKET_ANALYSIS_PROMPT = """请分析以下热点新闻对金融市场的影响：

## 新闻数据
日期: {date}
热词分组: {hot_keywords}

{news_items}

## 可用工具

你可以使用以下工具获取实时市场数据，增强分析的准确性：

### 基础工具
1. **evaluate_sector_impact** - 对每个板块进行结构化评估（必须使用）
2. **get_stock_price** - 获取相关股票的实时价格和涨跌幅
3. **get_index_price** - 获取大盘指数数据（如上证指数 000001、深证成指 399001）
4. **search_stock** - 根据关键词搜索相关股票代码
   - **重要**：对于每个关键词，请分别调用两次：`market="CN-A"` 和 `market="HK"`，确保同时搜索 A 股和港股

### 大盘复盘工具（新增）
5. **get_market_overview** - 获取大盘复盘数据（指数、涨跌统计、资金流向、板块表现）
   - 支持市场：CN-A(A股)、US(美股)、HK(港股)

### 趋势分析工具（新增）
6. **calculate_bias** - 计算乖离率，判断是否追高风险
   - 乖离率 < 2%：最佳买点
   - 乖离率 2-5%：可小仓介入
   - 乖离率 > 5%：严禁追高！
7. **check_ma_alignment** - 检查均线排列状态（多头/空头/缠绕）
8. **calculate_trend_score** - 计算趋势综合评分（0-100分）和检查清单

### 增强数据工具（新增）
9. **get_realtime_quote** - 获取增强行情（量比、换手率、市盈率等）
10. **get_chip_distribution** - 获取筹码分布（仅A股）

### 技术分析工具
11. **calculate_rsi** - 计算 RSI 技术指标
12. **calculate_macd** - 计算 MACD 指标
13. **comprehensive_analysis** - 综合技术分析

**请在分析过程中：**
- 使用 **get_market_overview** 获取当日大盘复盘数据
- 使用 **evaluate_sector_impact** 对每个聚焦板块进行评估
- 如果新闻提到具体公司，使用 **calculate_trend_score** 获取趋势评分和检查清单
- 严格遵循交易理念：乖离率 > 5% 时必须标记为"观望"

## 分析要求

1. **核心要点提取**（3-5条）
   - 识别最重要的市场影响事件
   - 每条要点包含：事件 + 影响方向 + 简要原因

2. **板块影响评估**
   - 聚焦板块：{focus_sectors}
   - 对每个相关板块使用 evaluate_sector_impact 工具进行评估
   - 输出表格格式

3. **实时市场数据**（如果获取到）
   - 显示大盘指数和相关股票的实时价格
   - 结合技术指标分析

4. **投资建议**
   - 短期（1-3天）建议
   - 中期（1-2周）建议
   - 风险提示

## 输出格式

请严格按照以下 Markdown 格式输出：

```markdown
## 📊 核心要点

1. **[事件名称]** - [影响方向]: [简要分析]
2. ...

## 🎯 板块影响评估

| 板块 | 方向 | 影响程度 | 置信度 | 理由 |
|------|------|----------|--------|------|
| 科技 | 利好 | 8/10 | 高 | ... |

## 📈 实时市场数据

- **上证指数**: xxxx.xx (±x.xx%)
- **相关股票**: ...

## 💡 投资建议

**短期（1-3天）**：...

**中期（1-2周）**：...

**风险提示**：...
```

要求：
- 分析要客观、有逻辑支撑
- 避免过度乐观或悲观
- 明确指出不确定性
- 使用专业但易懂的语言
- 充分利用工具获取实时数据增强分析
"""

    # 快速摘要 Prompt（用于生成描述）
    SUMMARY_PROMPT = """请用一句话总结以下新闻的核心市场影响（不超过50字）：

{news_summary}

要求：突出最重要的市场信号，语言简洁凝练。
"""

    @classmethod
    def build_analysis_prompt(
        cls,
        date: str,
        hot_keywords: List[str],
        news_items: List[Dict],
        focus_sectors: List[str] = None
    ) -> str:
        """
        构建市场分析 Prompt
        
        Args:
            date: 新闻日期
            hot_keywords: 热词列表
            news_items: 新闻条目列表 [{"title": ..., "url": ..., "source": ...}]
            focus_sectors: 聚焦板块列表
            
        Returns:
            完整的分析 Prompt
        """
        if focus_sectors is None:
            focus_sectors = ["科技", "金融", "消费", "医疗"]
        
        # 格式化热词
        keywords_str = "、".join(hot_keywords[:10])
        
        # 格式化新闻条目
        news_lines = []
        for i, item in enumerate(news_items[:30], 1):  # 限制最多30条新闻
            title = item.get("title", "")
            source = item.get("source", "")
            news_lines.append(f"{i}. {title} ({source})")
        
        news_items_str = "\n".join(news_lines)
        
        # 格式化聚焦板块
        sectors_str = "、".join(focus_sectors)
        
        return cls.MARKET_ANALYSIS_PROMPT.format(
            date=date,
            hot_keywords=keywords_str,
            news_items=news_items_str,
            focus_sectors=sectors_str
        )
    
    @classmethod
    def build_summary_prompt(cls, news_summary: str) -> str:
        """
        构建摘要 Prompt
        
        Args:
            news_summary: 新闻摘要内容
            
        Returns:
            摘要 Prompt
        """
        return cls.SUMMARY_PROMPT.format(news_summary=news_summary)
    
    @classmethod
    def get_system_messages(cls) -> List[Dict]:
        """
        获取系统消息（用于 API 调用）
        
        Returns:
            系统消息列表
        """
        return [
            {
                "role": "system",
                "content": cls.SYSTEM_ROLE
            }
        ]
