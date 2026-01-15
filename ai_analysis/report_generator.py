# coding=utf-8
"""
分析报告生成器

将 AI 分析结果格式化为 Hugo Markdown 文档
"""

import re
from typing import Dict, List
from datetime import datetime
from pathlib import Path

from .market_scorer import MarketAnalysisResult, SectorImpact


class AnalysisReportGenerator:
    """分析报告生成器"""
    
    # 影响程度映射到星级
    SCORE_TO_STARS = {
        (1, 2): "⭐",
        (3, 4): "⭐⭐",
        (5, 6): "⭐⭐⭐",
        (7, 8): "⭐⭐⭐⭐",
        (9, 10): "⭐⭐⭐⭐⭐",
    }
    
    @staticmethod
    def _score_to_stars(score: int) -> str:
        """将分数转换为星级显示"""
        for (low, high), stars in AnalysisReportGenerator.SCORE_TO_STARS.items():
            if low <= score <= high:
                return stars
        return "⭐"
    
    @staticmethod
    def _parse_numbered_list(text: str) -> List[str]:
        """
        解析文本中的编号列表项
        
        支持格式: "1. xxx 2. xxx" 或 "1. xxx\n2. xxx"
        """
        if not text:
            return []
        
        # 尝试按编号分割 (1. xxx 2. xxx)
        pattern = r'(\d+)\.\s*\*?\*?([^0-9]+?)(?=\d+\.|$)'
        matches = re.findall(pattern, text)
        
        if matches:
            return [match[1].strip().rstrip('*').strip() for match in matches if match[1].strip()]
        
        # 如果没有匹配到编号格式，返回原文本作为单项
        return [text.strip()]
    
    @staticmethod
    def generate_frontmatter(
        date: str,
        title: str,
        description: str,
        sectors: List[str],
        sentiment: str = "neutral"
    ) -> str:
        """
        生成 Hugo frontmatter
        
        Args:
            date: 日期 YYYY-MM-DD
            title: 标题
            description: 描述
            sectors: 相关板块列表
            sentiment: 市场情绪 bullish/bearish/neutral
            
        Returns:
            frontmatter 字符串
        """
        tags = ["analysis", "ai", "market", sentiment]
        categories = ["analysis"]
        
        tags_str = ', '.join(f'"{tag}"' for tag in tags)
        categories_str = ', '.join(f'"{cat}"' for cat in categories)
        sectors_str = ', '.join(f'"{sector}"' for sector in sectors)
        
        frontmatter = f'''+++
date = "{date}"
title = "{title}"
description = "{description}"
tags = [{tags_str}]
categories = [{categories_str}]
sectors = [{sectors_str}]
sentiment = "{sentiment}"
+++
'''
        return frontmatter
    
    @staticmethod
    def format_key_points(key_points: List[str], max_points: int = 5) -> str:
        """
        格式化核心要点（精简版）
        
        Args:
            key_points: 核心要点列表
            max_points: 最多显示的要点数
        """
        if not key_points:
            return "## 📊 核心要点\n\n暂无核心要点\n\n"
        
        content = "## 📊 核心要点\n\n"
        
        # 只显示前 N 个要点作为摘要
        for i, point in enumerate(key_points[:max_points], 1):
            # 检查是否包含利好/利空标记，格式化为加粗
            if '利好' in point or '利空' in point or '中性' in point:
                # 尝试提取标题和说明
                parts = point.split(':', 1) if ':' in point else point.split('：', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    desc = parts[1].strip()
                    # 提取方向标记
                    direction = ""
                    if '利好' in title or '利好' in desc[:10]:
                        direction = "利好"
                    elif '利空' in title or '利空' in desc[:10]:
                        direction = "利空"
                    elif '中性' in title or '中性' in desc[:10]:
                        direction = "中性"
                    
                    # 清理标题中的方向标记
                    clean_title = re.sub(r'\*?\*?(利好|利空|中性)\*?\*?[：:]*\s*', '', title).strip()
                    clean_desc = re.sub(r'^\*?\*?(利好|利空|中性)\*?\*?[：:]*\s*', '', desc).strip()
                    
                    if direction:
                        content += f"{i}. **{clean_title}** - {direction}：{clean_desc}\n"
                    else:
                        content += f"{i}. **{clean_title}** - {clean_desc}\n"
                else:
                    content += f"{i}. {point}\n"
            else:
                content += f"{i}. {point}\n"
        
        content += "\n---\n\n"
        return content
    
    @staticmethod
    def format_sector_impacts(impacts: List[SectorImpact]) -> str:
        """格式化板块影响评估"""
        if not impacts:
            return "## 🎯 板块影响评估\n\n暂无板块评估数据\n\n"
        
        content = "## 🎯 板块影响评估\n\n"
        content += "| 板块 | 方向 | 影响程度 | 置信度 | 理由 |\n"
        content += "|:----:|:----:|:--------:|:------:|------|\n"
        
        for impact in impacts:
            stars = AnalysisReportGenerator._score_to_stars(impact.score)
            # 截断过长的理由
            reason = impact.reason
            if len(reason) > 60:
                reason = reason[:57] + "..."
            content += f"| {impact.sector} | {impact.direction} | {stars} | {impact.confidence} | {reason} |\n"
        
        content += "\n---\n\n"
        return content
    
    @staticmethod
    def format_advice(
        short_term: str,
        medium_term: str,
        risk_warning: str
    ) -> str:
        """格式化投资建议（改进版：自动识别并拆分编号列表）"""
        content = "## 💡 投资建议\n\n"
        
        # 短期建议
        if short_term:
            content += "### 短期（1-3天）\n\n"
            items = AnalysisReportGenerator._parse_numbered_list(short_term)
            for i, item in enumerate(items, 1):
                # 提取加粗的标题部分
                bold_match = re.match(r'\*\*(.+?)\*\*[：:]?\s*(.+)?', item)
                if bold_match:
                    title = bold_match.group(1)
                    desc = bold_match.group(2) or ""
                    content += f"{i}. **{title}**：{desc}\n"
                else:
                    content += f"{i}. {item}\n"
            content += "\n"
        
        # 中期建议
        if medium_term:
            content += "### 中期（1-2周）\n\n"
            items = AnalysisReportGenerator._parse_numbered_list(medium_term)
            for i, item in enumerate(items, 1):
                bold_match = re.match(r'\*\*(.+?)\*\*[：:]?\s*(.+)?', item)
                if bold_match:
                    title = bold_match.group(1)
                    desc = bold_match.group(2) or ""
                    content += f"{i}. **{title}**：{desc}\n"
                else:
                    content += f"{i}. {item}\n"
            content += "\n"
        
        content += "---\n\n"
        
        # 风险提示（改为表格形式）
        if risk_warning:
            content += "## ⚠️ 风险提示\n\n"
            items = AnalysisReportGenerator._parse_numbered_list(risk_warning)
            
            if len(items) > 1:
                # 多项时使用表格
                content += "| 风险类型 | 说明 |\n"
                content += "|:--------:|------|\n"
                for item in items:
                    # 尝试提取风险类型名称
                    bold_match = re.match(r'\*\*(.+?)\*\*[：:]?\s*(.+)?', item)
                    if bold_match:
                        risk_type = bold_match.group(1)
                        desc = bold_match.group(2) or ""
                        content += f"| {risk_type} | {desc} |\n"
                    else:
                        # 尝试从内容推断风险类型
                        if '估值' in item:
                            content += f"| 估值风险 | {item} |\n"
                        elif '政策' in item or '美联储' in item:
                            content += f"| 政策风险 | {item} |\n"
                        elif '地缘' in item:
                            content += f"| 地缘风险 | {item} |\n"
                        elif '数据' in item:
                            content += f"| 数据风险 | {item} |\n"
                        elif '技术' in item:
                            content += f"| 技术风险 | {item} |\n"
                        else:
                            content += f"| 其他风险 | {item} |\n"
                content += "\n"
            else:
                # 单项时使用普通文本
                content += f"> ⚠️ {items[0]}\n\n"
        
        return content
    
    @staticmethod
    def extract_filename_keyword(key_points: List[str], sector_impacts: List = None) -> str:
        """
        从核心要点中提取最重要的关键词用于文件名
        
        Args:
            key_points: 核心要点列表
            sector_impacts: 板块影响列表（可选）
            
        Returns:
            提取的关键词，如 "AI产业全面爆发"
        """
        if not key_points:
            return "market-analysis"
        
        first_point = key_points[0] if key_points else ""
        
        import re
        
        # 优先匹配 **xxx** 格式的加粗文本（实际核心要点格式）
        # 格式: "**AI产业全面爆发** - 利好：..."
        bold_match = re.search(r'\*\*([^*]+)\*\*', first_point)
        if bold_match:
            keyword = bold_match.group(1).strip()
            # 清理可能的特殊字符
            keyword = re.sub(r'[\[\]()（）【】]', '', keyword)
            if 3 <= len(keyword) <= 20:
                return keyword
        
        # 尝试匹配 "板块 - 利好：1. xxx" 格式
        numbered_match = re.search(r'[：:]\s*(?:\d+\.\s*)?([^：:;；\d][^：:;；]{2,15})', first_point)
        if numbered_match:
            keyword = numbered_match.group(1).strip()
            keyword = re.sub(r'[*\[\]()（）【】]', '', keyword)
            keyword = keyword.split('；')[0].split(';')[0]
            if 3 <= len(keyword) <= 20:
                return keyword
        
        # 回退到默认
        return "market-analysis"
    
    @staticmethod
    def generate_report(
        analysis_result: MarketAnalysisResult,
        date: str,
        title: str = None,
        description: str = None
    ) -> str:
        """
        生成完整的分析报告
        
        Args:
            analysis_result: 市场分析结果
            date: 日期
            title: 标题（可选）
            description: 描述（可选）
            
        Returns:
            完整的 Markdown 报告内容
        """
        # 提取板块列表
        sectors = list(set(impact.sector for impact in analysis_result.sector_impacts))
        
        # 计算整体情绪
        from .market_scorer import MarketImpactScorer
        sentiment_data = MarketImpactScorer.calculate_overall_sentiment(
            analysis_result.sector_impacts
        )
        sentiment = sentiment_data["sentiment"]
        
        # 生成默认标题和描述
        if not title:
            title = f"AI市场分析: {date}"
        if not description:
            description = f"基于 {date} 热点新闻的金融市场影响分析"
        
        # 组装报告
        report = AnalysisReportGenerator.generate_frontmatter(
            date=date,
            title=title,
            description=description,
            sectors=sectors,
            sentiment=sentiment
        )
        
        report += "\n"
        report += AnalysisReportGenerator.format_key_points(analysis_result.key_points)
        report += AnalysisReportGenerator.format_sector_impacts(analysis_result.sector_impacts)
        report += AnalysisReportGenerator.format_advice(
            analysis_result.short_term_advice,
            analysis_result.medium_term_advice,
            analysis_result.risk_warning
        )
        
        # 添加页脚
        report += "---\n\n"
        report += f"*分析生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        report += f"*免责声明: 本分析由 AI 自动生成，仅供参考，不构成投资建议*\n"
        
        return report
    
    @staticmethod
    def _ensure_index_files(output_dir: str, year: str, month: str) -> None:
        """
        确保 Hugo 所需的 _index.md 文件存在
        
        创建三个层级的索引文件：
        - analysis/_index.md（分类根目录）
        - analysis/{year}/_index.md（年份目录）
        - analysis/{year}/{month}/_index.md（月份目录）
        """
        base_path = Path(output_dir)
        
        # 1. 分类根目录索引
        category_index = base_path / "_index.md"
        if not category_index.exists():
            base_path.mkdir(parents=True, exist_ok=True)
            category_index.write_text(
                '+++\ntitle = "Analysis"\ndescription = "AI市场分析汇总"\n+++\n',
                encoding='utf-8'
            )
            print(f"[创建索引] {category_index}")
        
        # 2. 年份目录索引
        year_path = base_path / year
        year_index = year_path / "_index.md"
        if not year_index.exists():
            year_path.mkdir(parents=True, exist_ok=True)
            year_index.write_text(
                f'+++\ntitle = "{year}年AI市场分析"\ndescription = "{year}年AI市场分析汇总"\n+++\n',
                encoding='utf-8'
            )
            print(f"[创建索引] {year_index}")
        
        # 3. 月份目录索引
        month_path = year_path / month
        month_index = month_path / "_index.md"
        if not month_index.exists():
            month_path.mkdir(parents=True, exist_ok=True)
            month_index.write_text(
                f'+++\ntitle = "{year}年{int(month)}月AI市场分析汇总"\ndescription = "{year}年{int(month)}月AI市场分析汇总"\n+++\n',
                encoding='utf-8'
            )
            print(f"[创建索引] {month_index}")
    
    @staticmethod
    def save_report(
        report_content: str,
        output_dir: str,
        date: str,
        filename: str = None
    ) -> str:
        """
        保存报告到文件
        
        Args:
            report_content: 报告内容
            output_dir: 输出目录（如 page/src/content/post/analysis）
            date: 日期 YYYY-MM-DD
            filename: 文件名（可选，默认使用日期）
            
        Returns:
            保存的文件路径
        """
        # 解析日期
        year = date[:4]
        month = date[5:7]
        
        # 确保所有 _index.md 文件存在
        AnalysisReportGenerator._ensure_index_files(output_dir, year, month)
        
        # 构建输出路径
        output_path = Path(output_dir) / year / month
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if not filename:
            filename = f"{date}-market-analysis.md"
        
        file_path = output_path / filename
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(file_path)
    
    # ==================== 新增方法（参考 daily_stock_analysis）====================
    
    @staticmethod
    def format_market_overview(overview) -> str:
        """
        格式化大盘复盘模块
        
        Args:
            overview: MarketOverview 对象
            
        Returns:
            格式化的大盘复盘 Markdown 内容
        """
        content = f"## 📊 {overview.market} 大盘复盘 ({overview.date})\n\n"
        
        # 主要指数
        if overview.indices:
            content += "### 主要指数\n\n"
            content += "| 指数 | 收盘 | 涨跌幅 |\n"
            content += "|:----:|:----:|:------:|\n"
            
            for idx in overview.indices:
                direction = "🟢" if idx.change_pct > 0 else "🔴" if idx.change_pct < 0 else "⚪"
                content += f"| {idx.name} | {idx.current:.2f} | {direction}{idx.change_pct:+.2f}% |\n"
            content += "\n"
        
        # 市场概况
        content += "### 市场概况\n\n"
        content += "| 指标 | 数值 |\n"
        content += "|:----:|:----:|\n"
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
        else:
            content += f"| 成交额 | {overview.total_amount:.0f}亿 |\n"
        content += "\n"
        
        # 板块表现
        if overview.top_sectors or overview.bottom_sectors:
            content += "### 板块表现\n\n"
            if overview.top_sectors:
                top_names = "、".join([s.name for s in overview.top_sectors[:3]])
                content += f"- **领涨**: {top_names}\n"
            if overview.bottom_sectors:
                bottom_names = "、".join([s.name for s in overview.bottom_sectors[:3]])
                content += f"- **领跌**: {bottom_names}\n"
            content += "\n"
        
        content += "---\n\n"
        return content
    
    @staticmethod
    def format_trading_checklist(checklist: List[Dict]) -> str:
        """
        格式化交易检查清单
        
        Args:
            checklist: 检查清单列表，每项包含 name, status, value, note
            
        Returns:
            格式化的检查清单 Markdown 内容
        """
        if not checklist:
            return ""
        
        content = "## ✅ 决策检查清单\n\n"
        content += "| 检查项 | 状态 | 数值 | 备注 |\n"
        content += "|:------:|:----:|:----:|------|\n"
        
        for item in checklist:
            name = item.get("name", "")
            status = item.get("status", "⚠️")
            value = item.get("value", "")
            note = item.get("note", "")
            
            # 截断过长的内容
            if len(value) > 30:
                value = value[:27] + "..."
            if len(note) > 40:
                note = note[:37] + "..."
            
            content += f"| {name} | {status} | {value} | {note} |\n"
        
        content += "\n---\n\n"
        return content
    
    @staticmethod
    def format_trend_score(score_data: Dict) -> str:
        """
        格式化趋势评分结果
        
        Args:
            score_data: calculate_trend_score 返回的数据
            
        Returns:
            格式化的趋势评分 Markdown 内容
        """
        if not score_data or "error" in score_data:
            return ""
        
        content = "## 📈 趋势评分\n\n"
        
        symbol = score_data.get("symbol", "")
        total_score = score_data.get("total_score", 0)
        signal = score_data.get("signal", "")
        
        content += f"**{symbol}** 综合评分: **{total_score}/100** {signal}\n\n"
        
        # 评分细分
        breakdown = score_data.get("breakdown", {})
        if breakdown:
            content += "### 评分明细\n\n"
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
                score = data.get("score", 0)
                status = data.get("status", data.get("value", ""))
                content += f"| {name} | {score} | {status} |\n"
            content += "\n"
        
        # 检查清单
        checklist = score_data.get("checklist", [])
        if checklist:
            content += AnalysisReportGenerator.format_trading_checklist(checklist)
        
        return content

