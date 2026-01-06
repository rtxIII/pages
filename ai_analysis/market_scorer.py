# coding=utf-8
"""
市场影响评分器

解析 AI 分析结果，提取结构化的市场影响评分数据
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SectorImpact:
    """板块影响数据"""
    sector: str          # 板块名称
    direction: str       # 方向：利好/利空/中性
    score: int           # 影响程度 1-10
    confidence: str      # 置信度：高/中/低
    reason: str          # 理由


@dataclass
class MarketAnalysisResult:
    """市场分析结果"""
    key_points: List[str]              # 核心要点
    sector_impacts: List[SectorImpact] # 板块影响
    short_term_advice: str             # 短期建议
    medium_term_advice: str            # 中期建议
    risk_warning: str                  # 风险提示
    raw_content: str                   # 原始分析内容


class MarketImpactScorer:
    """市场影响评分器"""
    
    @staticmethod
    def parse_analysis_result(ai_response: str) -> MarketAnalysisResult:
        """
        解析 AI 分析响应，提取结构化数据
        
        Args:
            ai_response: AI 返回的 Markdown 格式分析内容
            
        Returns:
            MarketAnalysisResult 对象
        """
        # 提取核心要点
        key_points = MarketImpactScorer._extract_key_points(ai_response)
        
        # 提取板块影响
        sector_impacts = MarketImpactScorer._extract_sector_impacts(ai_response)
        
        # 提取投资建议
        short_term, medium_term, risk_warning = MarketImpactScorer._extract_advice(ai_response)
        
        return MarketAnalysisResult(
            key_points=key_points,
            sector_impacts=sector_impacts,
            short_term_advice=short_term,
            medium_term_advice=medium_term,
            risk_warning=risk_warning,
            raw_content=ai_response
        )
    
    @staticmethod
    def _extract_key_points(content: str) -> List[str]:
        """提取核心要点"""
        key_points = []
        
        # 匹配 "## 📊 核心要点" 部分
        pattern = r'##\s*📊\s*核心要点\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            points_section = match.group(1)
            # 提取列表项（支持 1. 或 - 开头）
            point_pattern = r'(?:^\d+\.|^-)\s*\*\*(.+?)\*\*\s*[-:：]\s*(.+?)(?=\n(?:\d+\.|-)|$)'
            for m in re.finditer(point_pattern, points_section, re.MULTILINE):
                event = m.group(1).strip()
                impact = m.group(2).strip()
                key_points.append(f"{event}: {impact}")
        
        return key_points if key_points else ["未提取到核心要点"]
    
    @staticmethod
    def _extract_sector_impacts(content: str) -> List[SectorImpact]:
        """提取板块影响评估"""
        impacts = []
        
        # 匹配表格内容
        pattern = r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|'
        
        for match in re.finditer(pattern, content):
            sector = match.group(1).strip()
            direction = match.group(2).strip()
            score_str = match.group(3).strip()
            confidence = match.group(4).strip()
            reason = match.group(5).strip()
            
            # 跳过表头
            if sector in ["板块", "---"] or "---" in direction:
                continue
            
            # 提取分数
            score_match = re.search(r'(\d+)', score_str)
            score = int(score_match.group(1)) if score_match else 5
            
            impacts.append(SectorImpact(
                sector=sector,
                direction=direction,
                score=score,
                confidence=confidence,
                reason=reason
            ))
        
        return impacts
    
    @staticmethod
    def _extract_advice(content: str) -> tuple:
        """提取投资建议"""
        short_term = ""
        medium_term = ""
        risk_warning = ""
        
        # 提取短期建议
        short_pattern = r'\*\*短期[（(]1-3天[)）]\*\*[：:]\s*(.+?)(?=\n\*\*|\Z)'
        short_match = re.search(short_pattern, content, re.DOTALL)
        if short_match:
            short_term = short_match.group(1).strip()
        
        # 提取中期建议
        medium_pattern = r'\*\*中期[（(]1-2周[)）]\*\*[：:]\s*(.+?)(?=\n\*\*|\Z)'
        medium_match = re.search(medium_pattern, content, re.DOTALL)
        if medium_match:
            medium_term = medium_match.group(1).strip()
        
        # 提取风险提示
        risk_pattern = r'\*\*风险提示\*\*[：:]\s*(.+?)(?=\n##|\Z)'
        risk_match = re.search(risk_pattern, content, re.DOTALL)
        if risk_match:
            risk_warning = risk_match.group(1).strip()
        
        return short_term, medium_term, risk_warning
    
    @staticmethod
    def calculate_overall_sentiment(impacts: List[SectorImpact]) -> Dict:
        """
        计算整体市场情绪
        
        Args:
            impacts: 板块影响列表
            
        Returns:
            {"sentiment": "bullish/bearish/neutral", "score": float}
        """
        if not impacts:
            return {"sentiment": "neutral", "score": 0.0}
        
        direction_map = {"利好": 1, "利空": -1, "中性": 0}
        
        total_score = 0
        for impact in impacts:
            direction_weight = direction_map.get(impact.direction, 0)
            total_score += direction_weight * impact.score
        
        avg_score = total_score / len(impacts)
        
        if avg_score > 2:
            sentiment = "bullish"
        elif avg_score < -2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": round(avg_score, 2)
        }
