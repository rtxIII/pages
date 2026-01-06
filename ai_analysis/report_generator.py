# coding=utf-8
"""
分析报告生成器

将 AI 分析结果格式化为 Hugo Markdown 文档
"""

from typing import Dict, List
from datetime import datetime
from pathlib import Path

from .market_scorer import MarketAnalysisResult, SectorImpact


class AnalysisReportGenerator:
    """分析报告生成器"""
    
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
    def format_key_points(key_points: List[str]) -> str:
        """格式化核心要点"""
        if not key_points:
            return "## 📊 核心要点\n\n暂无核心要点\n\n"
        
        content = "## 📊 核心要点\n\n"
        for i, point in enumerate(key_points, 1):
            content += f"{i}. {point}\n"
        content += "\n"
        return content
    
    @staticmethod
    def format_sector_impacts(impacts: List[SectorImpact]) -> str:
        """格式化板块影响评估"""
        if not impacts:
            return "## 🎯 板块影响评估\n\n暂无板块评估数据\n\n"
        
        content = "## 🎯 板块影响评估\n\n"
        content += "| 板块 | 方向 | 影响程度 | 置信度 | 理由 |\n"
        content += "|------|------|----------|--------|------|\n"
        
        for impact in impacts:
            content += f"| {impact.sector} | {impact.direction} | {impact.score}/10 | {impact.confidence} | {impact.reason} |\n"
        
        content += "\n"
        return content
    
    @staticmethod
    def format_advice(
        short_term: str,
        medium_term: str,
        risk_warning: str
    ) -> str:
        """格式化投资建议"""
        content = "## 💡 投资建议\n\n"
        
        if short_term:
            content += f"**短期（1-3天）**：{short_term}\n\n"
        
        if medium_term:
            content += f"**中期（1-2周）**：{medium_term}\n\n"
        
        if risk_warning:
            content += f"**风险提示**：{risk_warning}\n\n"
        
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
        report += "\n---\n\n"
        report += f"*分析生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
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
