#!/usr/bin/env python3
# coding=utf-8
"""
大盘数据分析脚本（含 AI 智能分析）

分析 A股、美股、港股 三个市场的大盘数据和个股技术指标
使用 Claude AI 生成投资建议

用法:
    python run_market.py                          # 分析 A 股并生成报告（含AI分析）
    python run_market.py --market CN-A            # 仅分析 A 股
    python run_market.py --market US              # 仅分析美股
    python run_market.py --market HK              # 仅分析港股
    python run_market.py --stock 000001           # 分析指定 A 股
    python run_market.py --no-ai                  # 不使用 AI 分析
    python run_market.py --no-save                # 仅打印不保存
"""

import argparse
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent 
sys.path.insert(0, str(PROJECT_ROOT))

from ai_analysis.market_overview import MarketOverviewProvider, MarketOverview
from ai_analysis.functions.technical import TechnicalAnalyzer
from ai_analysis.functions.market_data import MarketDataProvider
from ai_analysis.functions.tools import FunctionToolRegistry
from ai_analysis.prompts import PromptTemplates


def generate_market_overview_md(overview: MarketOverview) -> str:
    """生成大盘复盘 Markdown 内容"""
    market_names = {"CN-A": "A股", "US": "美股", "HK": "港股"}
    market_name = market_names.get(overview.market, overview.market)
    
    content = f"## 📊 {market_name}大盘复盘\n\n"
    
    # 主要指数
    if overview.indices:
        content += "### 主要指数\n\n"
        content += "| 指数 | 收盘 | 涨跌幅 |\n"
        content += "|:----:|-----:|-------:|\n"
        
        for idx in overview.indices:
            direction = "🟢" if idx.change_pct > 0 else "🔴" if idx.change_pct < 0 else "⚪"
            content += f"| {idx.name} | {idx.current:.2f} | {direction} {idx.change_pct:+.2f}% |\n"
        content += "\n"
    
    # 市场概况
    content += "### 市场概况\n\n"
    content += "| 指标 | 数值 |\n"
    content += "|:----:|-----:|\n"
    content += f"| 上涨家数 | {overview.up_count} |\n"
    content += f"| 下跌家数 | {overview.down_count} |\n"
    
    if overview.market == "CN-A":
        content += f"| 涨停 | {overview.limit_up_count} |\n"
        content += f"| 跌停 | {overview.limit_down_count} |\n"
        content += f"| 两市成交额 | {overview.total_amount:.0f}亿 |\n"
        content += f"| 北向资金 | {overview.north_flow:+.2f}亿 |\n"
    elif overview.market == "HK":
        content += f"| 成交额 | {overview.total_amount:.0f}亿港元 |\n"
        content += f"| 南向资金 | {overview.south_flow:+.2f}亿港元 |\n"
    content += "\n"
    
    # 板块表现
    if overview.top_sectors or overview.bottom_sectors:
        content += "### 板块表现\n\n"
        if overview.top_sectors:
            content += "**领涨板块**\n\n"
            for s in overview.top_sectors[:5]:
                content += f"- {s.name}: {s.change_pct:+.2f}%\n"
            content += "\n"
        if overview.bottom_sectors:
            content += "**领跌板块**\n\n"
            for s in overview.bottom_sectors[:5]:
                content += f"- {s.name}: {s.change_pct:+.2f}%\n"
            content += "\n"
    
    return content


def get_ai_market_analysis(overview_data: dict, model: str = "claude-sonnet-4-20250514") -> str:
    """
    使用 Claude AI 分析市场数据，生成投资建议
    
    Args:
        overview_data: 大盘复盘数据字典
        model: Claude 模型名称
        
    Returns:
        AI 生成的分析文本
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "\n> ⚠️ 未设置 ANTHROPIC_API_KEY，跳过 AI 分析\n"
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        # 构建市场数据摘要
        market_summary = json.dumps(overview_data, ensure_ascii=False, indent=2)
        
        # 使用系统角色中的交易理念
        system_prompt = PromptTemplates.SYSTEM_ROLE
        
        user_prompt = f"""请根据以下大盘数据生成简短的市场分析和投资建议：

## 大盘数据
{market_summary}

## 分析要求

1. **市场情绪判断**（1-2句话）
   - 判断当日市场情绪：恐慌/谨慎/中性/乐观/亢奋

2. **核心要点**（3条以内）
   - 提炼今日市场最重要的信息

3. **板块机会**（如有领涨板块）
   - 分析领涨板块的逻辑
   - 注意：如果板块涨幅过大（>5%），提示追高风险

4. **投资建议**
   - 短期操作建议
   - 风险提示

请用简洁的中文回答，使用 Markdown 格式。严格遵循"不追高"的交易理念。
"""
        
        print("[AI 分析] 正在调用 Claude API...")
        
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # 提取文本
        text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
        if text_blocks:
            return "\n## 🤖 AI 智能分析\n\n" + "\n".join(text_blocks) + "\n"
        
        return "\n> ⚠️ AI 分析结果为空\n"
        
    except Exception as e:
        print(f"[AI 分析] 调用失败: {e}")
        return f"\n> ⚠️ AI 分析调用失败: {str(e)}\n"


def generate_report(markets: list, stock: str = None, stock_market: str = "CN-A", enable_ai: bool = True) -> str:
    """生成完整报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Hugo frontmatter
    content = f"""---
title: "{today} 大盘复盘"
date: {today}
categories: ["market"]
tags: ["大盘", "复盘", "技术分析", "AI分析"]
draft: false
---

# 📊 {today} 大盘复盘

*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

"""
    
    # 收集所有市场数据（用于 AI 分析）
    all_overview_data = []
    
    # 添加大盘复盘
    for market in markets:
        try:
            overview = MarketOverviewProvider.get_market_overview(market)
            content += generate_market_overview_md(overview)
            content += "---\n\n"
            
            # 收集数据用于 AI 分析
            all_overview_data.append({
                "market": overview.market,
                "date": overview.date,
                "indices": [{"name": i.name, "current": i.current, "change_pct": i.change_pct} for i in overview.indices],
                "up_count": overview.up_count,
                "down_count": overview.down_count,
                "limit_up_count": overview.limit_up_count,
                "limit_down_count": overview.limit_down_count,
                "total_amount": overview.total_amount,
                "north_flow": overview.north_flow,
                "top_sectors": [{"name": s.name, "change_pct": s.change_pct} for s in overview.top_sectors[:5]],
                "bottom_sectors": [{"name": s.name, "change_pct": s.change_pct} for s in overview.bottom_sectors[:5]]
            })
        except Exception as e:
            content += f"## ❌ {market} 数据获取失败\n\n{str(e)}\n\n---\n\n"
    
    # AI 智能分析
    if enable_ai and all_overview_data:
        ai_analysis = get_ai_market_analysis(all_overview_data)
        content += ai_analysis
        content += "---\n\n"
    
    # 添加个股分析
    if stock:
        content += generate_stock_analysis_md(stock, stock_market)
        content += "---\n\n"
    
    # 免责声明
    content += """
> **免责声明**: 本报告由程序自动生成，AI 分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。
"""
    
    return content


def generate_stock_analysis_md(symbol: str, market: str = "CN-A") -> str:
    """生成个股技术分析 Markdown 内容"""
    content = f"## 📈 个股分析: {symbol}\n\n"
    
    # 获取实时行情
    quote = MarketDataProvider.get_realtime_quote(symbol, market)
    if "error" not in quote:
        content += "### 实时行情\n\n"
        content += "| 指标 | 数值 |\n"
        content += "|:----:|-----:|\n"
        content += f"| 名称 | {quote.get('name', 'N/A')} |\n"
        content += f"| 价格 | {quote.get('price', 0):.2f} |\n"
        content += f"| 涨跌幅 | {quote.get('change_pct', 0):+.2f}% |\n"
        if market == "CN-A":
            content += f"| 量比 | {quote.get('volume_ratio', 0):.2f} |\n"
            content += f"| 换手率 | {quote.get('turnover_rate', 0):.2f}% |\n"
            content += f"| 市盈率 | {quote.get('pe_ratio', 0):.2f} |\n"
        content += "\n"
    
    # 趋势评分
    score = TechnicalAnalyzer.calculate_trend_score(symbol, market)
    if "error" not in score:
        content += "### 趋势评分\n\n"
        content += f"**综合评分: {score.get('total_score', 0)}/100** {score.get('signal', '')}\n\n"
        
        # 评分明细
        breakdown = score.get("breakdown", {})
        if breakdown:
            content += "| 维度 | 得分 | 状态 |\n"
            content += "|:----:|:----:|:----:|\n"
            dimension_names = {
                "ma_alignment": "均线排列",
                "bias": "乖离率",
                "volume": "量能配合",
                "rsi": "RSI",
                "macd": "MACD"
            }
            for key, data in breakdown.items():
                name = dimension_names.get(key, key)
                s = data.get("score", 0)
                status = str(data.get("status", data.get("value", "")))[:20]
                content += f"| {name} | {s} | {status} |\n"
            content += "\n"
        
        # 检查清单
        checklist = score.get("checklist", [])
        if checklist:
            content += "### 检查清单\n\n"
            content += "| 检查项 | 状态 | 数值 |\n"
            content += "|:------:|:----:|:----:|\n"
            for item in checklist:
                status = item.get("status", "⚠️")
                name = item.get("name", "")
                value = str(item.get("value", ""))[:25]
                content += f"| {name} | {status} | {value} |\n"
            content += "\n"
    
    # 乖离率
    bias = TechnicalAnalyzer.calculate_bias(symbol, market)
    if "error" not in bias:
        content += "### 乖离率分析\n\n"
        content += f"- 当前价: {bias.get('current_price', 0):.2f}\n"
        content += f"- MA{bias.get('ma_period', 5)}: {bias.get('ma_value', 0):.2f}\n"
        content += f"- 乖离率: **{bias.get('bias', 0):+.2f}%** ({bias.get('status', '')})\n"
        content += f"- 建议: {bias.get('trading_advice', '')}\n\n"
    
    return content


def save_report(content: str, output_dir: str, date: str) -> str:
    """保存报告到文件"""
    year = date[:4]
    month = date[5:7]
    
    output_path = Path(output_dir) / year / month
    output_path.mkdir(parents=True, exist_ok=True)
    
    filename = f"{date}-market-overview.md"
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)


def print_market_overview(overview: MarketOverview):
    """打印大盘复盘数据到控制台"""
    market_names = {"CN-A": "A 股", "US": "美股", "HK": "港股"}
    market_name = market_names.get(overview.market, overview.market)
    
    print(f"\n{'='*60}")
    print(f"📊 {market_name} 大盘复盘 ({overview.date})")
    print(f"{'='*60}")
    
    # 主要指数
    if overview.indices:
        print("\n🏛️ 主要指数:")
        print(f"{'指数名称':<12} {'收盘':>10} {'涨跌幅':>10}")
        print("-" * 35)
        for idx in overview.indices:
            direction = "🟢" if idx.change_pct > 0 else "🔴" if idx.change_pct < 0 else "⚪"
            print(f"{idx.name:<12} {idx.current:>10.2f} {direction}{idx.change_pct:>+8.2f}%")
    
    # 市场概况
    print("\n📈 市场概况:")
    print(f"  上涨家数: {overview.up_count}")
    print(f"  下跌家数: {overview.down_count}")
    
    if overview.market == "CN-A":
        print(f"  涨停: {overview.limit_up_count}")
        print(f"  跌停: {overview.limit_down_count}")
        print(f"  两市成交额: {overview.total_amount:.0f} 亿")
        print(f"  北向资金: {overview.north_flow:+.2f} 亿")
    elif overview.market == "HK":
        print(f"  成交额: {overview.total_amount:.0f} 亿港元")
        print(f"  南向资金: {overview.south_flow:+.2f} 亿港元")
    
    # 板块表现
    if overview.top_sectors or overview.bottom_sectors:
        print("\n🏭 板块表现:")
        if overview.top_sectors:
            top_names = "、".join([f"{s.name}({s.change_pct:+.2f}%)" for s in overview.top_sectors[:3]])
            print(f"  领涨: {top_names}")
        if overview.bottom_sectors:
            bottom_names = "、".join([f"{s.name}({s.change_pct:+.2f}%)" for s in overview.bottom_sectors[:3]])
            print(f"  领跌: {bottom_names}")


def main():
    parser = argparse.ArgumentParser(description="大盘数据分析工具（含 AI 智能分析）")
    
    parser.add_argument(
        "--market",
        type=str,
        choices=["CN-A", "US", "HK", "all"],
        default="HK",
        help="市场类型：CN-A(A股), US(美股), HK(港股), all(全部)，默认 CN-A"
    )
    
    parser.add_argument(
        "--stock",
        type=str,
        help="分析指定股票代码"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="page/src/content/post/market",
        help="输出目录路径（默认: page/src/content/post/market）"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="仅打印到控制台，不保存文件"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="禁用 AI 智能分析"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude 模型名称（默认: claude-sonnet-4-20250514）"
    )
    
    args = parser.parse_args()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 60)
    print("📊 大盘数据分析工具 (Powered by akshare + Claude AI)")
    print("=" * 60)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not args.no_ai:
        if os.getenv("ANTHROPIC_API_KEY"):
            print(f"AI 分析: ✅ 已启用 (模型: {args.model})")
        else:
            print("AI 分析: ⚠️ 未设置 ANTHROPIC_API_KEY")
    else:
        print("AI 分析: ❌ 已禁用")
    
    try:
        # 确定市场列表
        markets = ["CN-A", "US", "HK"] if args.market == "all" else [args.market]
        stock_market = args.market if args.market != "all" else "CN-A"
        
        # 打印到控制台
        for market in markets:
            try:
                print(f"\n⏳ 正在获取 {market} 市场数据...")
                overview = MarketOverviewProvider.get_market_overview(market)
                print_market_overview(overview)
            except Exception as e:
                print(f"\n❌ 获取 {market} 数据失败: {e}")
        
        # 生成并保存报告
        if not args.no_save:
            print(f"\n⏳ 正在生成 Markdown 报告...")
            
            output_dir = str(PROJECT_ROOT / args.output_dir)
            report_content = generate_report(
                markets, 
                args.stock, 
                stock_market, 
                enable_ai=not args.no_ai
            )
            report_path = save_report(report_content, output_dir, today)
            
            print(f"\n✅ 报告已保存: {report_path}")
        
        print(f"\n{'='*60}")
        print("✅ 分析完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


