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
