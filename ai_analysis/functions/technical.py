# coding=utf-8
"""
技术分析器

使用 funcat3 进行技术指标计算和选股分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

try:
    from funcat import *
    from funcat.context import ExecutionContext
    FUNCAT_AVAILABLE = True
except ImportError:
    FUNCAT_AVAILABLE = False
    logging.warning("funcat3 未安装，技术分析功能不可用")

from .market_data import MarketDataProvider

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """技术分析器（基于 funcat3）"""
    
    def __init__(self):
        if not FUNCAT_AVAILABLE:
            raise ImportError("请安装 funcat3: pip install funcat3")
        
        # 初始化 funcat backend
        try:
            from funcat.data.backend import AkshareDataBackend
            set_data_backend(AkshareDataBackend())
        except Exception as e:
            logger.warning(f"AkshareDataBackend 初始化失败: {e}")
    
    @staticmethod
    def calculate_ma(symbol: str, period: int = 5, days: int = 30) -> Dict:
        """
        计算移动平均线
        
        Args:
            symbol: 股票代码
            period: MA 周期
            days: 数据天数
            
        Returns:
            {
                "symbol": "000001",
                "indicator": "MA",
                "period": 5,
                "current_value": 12.34,
                "trend": "up/down/flat"
            }
        """
        if not FUNCAT_AVAILABLE:
            return {"error": "funcat3 不可用"}
        
        try:
            S(symbol)
            ma_value = MA(C, period).value
            ma_prev = MA(C[1], period).value
            
            # 判断趋势
            if ma_value > ma_prev * 1.001:
                trend = "up"
            elif ma_value < ma_prev * 0.999:
                trend = "down"
            else:
                trend = "flat"
            
            return {
                "symbol": symbol,
                "indicator": "MA",
                "period": period,
                "current_value": round(ma_value, 2),
                "previous_value": round(ma_prev, 2),
                "trend": trend
            }
        except Exception as e:
            logger.error(f"MA 计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_rsi(symbol: str, period: int = 14) -> Dict:
        """
        计算 RSI 相对强弱指标
        
        Args:
            symbol: 股票代码
            period: RSI 周期
            
        Returns:
            {
                "symbol": "000001",
                "indicator": "RSI",
                "value": 68.5,
                "signal": "overbought/oversold/neutral"
            }
        """
        if not FUNCAT_AVAILABLE:
            return {"error": "funcat3 不可用"}
        
        try:
            S(symbol)
            rsi_value = RSI(period).value
            
            # 判断信号
            if rsi_value > 70:
                signal = "overbought"  # 超买
            elif rsi_value < 30:
                signal = "oversold"    # 超卖
            else:
                signal = "neutral"
            
            return {
                "symbol": symbol,
                "indicator": "RSI",
                "period": period,
                "value": round(rsi_value, 2),
                "signal": signal
            }
        except Exception as e:
            logger.error(f"RSI 计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_macd(symbol: str) -> Dict:
        """
        计算 MACD 指标
        
        Args:
            symbol: 股票代码
            
        Returns:
            {
                "symbol": "000001",
                "indicator": "MACD",
                "diff": 0.12,
                "dea": 0.08,
                "macd": 0.08,
                "signal": "golden_cross/dead_cross/neutral"
            }
        """
        if not FUNCAT_AVAILABLE:
            return {"error": "funcat3 不可用"}
        
        try:
            S(symbol)
            
            # 计算 MACD
            diff = (EMA(C, 12) - EMA(C, 26)).value
            dea = EMA(EMA(C, 12) - EMA(C, 26), 9).value
            macd = 2 * (diff - dea)
            
            # 判断金叉死叉
            diff_prev = (EMA(C[1], 12) - EMA(C[1], 26)).value
            dea_prev = EMA(EMA(C[1], 12) - EMA(C[1], 26), 9).value
            
            if diff > dea and diff_prev <= dea_prev:
                signal = "golden_cross"  # 金叉
            elif diff < dea and diff_prev >= dea_prev:
                signal = "dead_cross"    # 死叉
            else:
                signal = "neutral"
            
            return {
                "symbol": symbol,
                "indicator": "MACD",
                "diff": round(diff, 4),
                "dea": round(dea, 4),
                "macd": round(macd, 4),
                "signal": signal
            }
        except Exception as e:
            logger.error(f"MACD 计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_boll(symbol: str, period: int = 20, std_num: int = 2) -> Dict:
        """
        计算布林带
        
        Args:
            symbol: 股票代码
            period: 周期
            std_num: 标准差倍数
            
        Returns:
            {
                "symbol": "000001",
                "indicator": "BOLL",
                "upper": 13.5,
                "middle": 12.0,
                "lower": 10.5,
                "position": "upper/middle/lower"
            }
        """
        if not FUNCAT_AVAILABLE:
            return {"error": "funcat3 不可用"}
        
        try:
            S(symbol)
            
            middle = MA(C, period).value
            std = STD(C, period).value
            upper = middle + std_num * std
            lower = middle - std_num * std
            current_price = C.value
            
            # 判断位置
            if current_price >= upper:
                position = "upper"
            elif current_price <= lower:
                position = "lower"
            else:
                position = "middle"
            
            return {
                "symbol": symbol,
                "indicator": "BOLL",
                "upper": round(upper, 2),
                "middle": round(middle, 2),
                "lower": round(lower, 2),
                "current_price": round(current_price, 2),
                "position": position
            }
        except Exception as e:
            logger.error(f"BOLL 计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def check_ma_cross(symbol: str, fast_period: int = 5, slow_period: int = 20) -> Dict:
        """
        检查均线交叉
        
        Args:
            symbol: 股票代码
            fast_period: 快线周期
            slow_period: 慢线周期
            
        Returns:
            {
                "symbol": "000001",
                "signal": "golden_cross/dead_cross/none",
                "fast_ma": 12.5,
                "slow_ma": 12.0
            }
        """
        if not FUNCAT_AVAILABLE:
            return {"error": "funcat3 不可用"}
        
        try:
            S(symbol)
            
            fast_ma = MA(C, fast_period).value
            slow_ma = MA(C, slow_period).value
            
            fast_ma_prev = MA(C[1], fast_period).value
            slow_ma_prev = MA(C[1], slow_period).value
            
            # 判断交叉
            if fast_ma > slow_ma and fast_ma_prev <= slow_ma_prev:
                signal = "golden_cross"
            elif fast_ma < slow_ma and fast_ma_prev >= slow_ma_prev:
                signal = "dead_cross"
            else:
                signal = "none"
            
            return {
                "symbol": symbol,
                "signal": signal,
                "fast_ma": round(fast_ma, 2),
                "slow_ma": round(slow_ma, 2),
                "fast_period": fast_period,
                "slow_period": slow_period
            }
        except Exception as e:
            logger.error(f"均线交叉检查失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def comprehensive_analysis(symbol: str) -> Dict:
        """
        综合技术分析
        
        Args:
            symbol: 股票代码
            
        Returns:
            {
                "symbol": "000001",
                "ma5": {...},
                "ma20": {...},
                "rsi": {...},
                "macd": {...},
                "boll": {...},
                "overall_signal": "bullish/bearish/neutral",
                "score": 7.5
            }
        """
        results = {
            "symbol": symbol,
            "ma5": TechnicalAnalyzer.calculate_ma(symbol, 5),
            "ma20": TechnicalAnalyzer.calculate_ma(symbol, 20),
            "rsi": TechnicalAnalyzer.calculate_rsi(symbol),
            "macd": TechnicalAnalyzer.calculate_macd(symbol),
            "boll": TechnicalAnalyzer.calculate_boll(symbol)
        }
        
        # 计算综合评分
        score = 5.0  # 中性基准
        
        # MA 趋势加分
        if results["ma5"].get("trend") == "up":
            score += 0.5
        elif results["ma5"].get("trend") == "down":
            score -= 0.5
        
        # RSI 加分
        rsi_signal = results["rsi"].get("signal")
        if rsi_signal == "oversold":
            score += 1.0
        elif rsi_signal == "overbought":
            score -= 1.0
        
        # MACD 加分
        macd_signal = results["macd"].get("signal")
        if macd_signal == "golden_cross":
            score += 1.5
        elif macd_signal == "dead_cross":
            score -= 1.5
        
        # 综合信号
        if score >= 6.5:
            overall_signal = "bullish"
        elif score <= 4.5:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"
        
        results["overall_signal"] = overall_signal
        results["score"] = round(score, 1)
        
        return results
