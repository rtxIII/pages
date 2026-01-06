# coding=utf-8
"""
AI 新闻分析模块

基于热点新闻数据，利用 Anthropic Claude 3.5 进行金融市场影响分析
支持 Function Calling 实时获取市场数据和技术指标
"""

__version__ = "1.0.0"

from .analyzer import NewsAnalysisEngine
from .market_scorer import MarketImpactScorer
from .report_generator import AnalysisReportGenerator

__all__ = [
    "NewsAnalysisEngine",
    "MarketImpactScorer", 
    "AnalysisReportGenerator",
]
