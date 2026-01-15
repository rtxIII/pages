# coding=utf-8
"""
技术分析器

"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .market_data import MarketDataProvider

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self):
        
        # 初始化 funcat backend
        try:
            from funcat.data.backend import AkshareDataBackend
            set_data_backend(AkshareDataBackend())
        except Exception as e:
            logger.warning(f"AkshareDataBackend 初始化失败: {e}")
    
    @staticmethod
    def calculate_ma(symbol: str, period: int = 5, market: str = "CN-A", days: int = 30) -> Dict:
        """
        计算移动平均线（支持多市场）
        
        Args:
            symbol: 股票代码
            period: MA 周期
            market: 市场类型 CN-A / US / HK
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
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=max(days, period + 10))
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            
            # 计算 MA
            df['_MA'] = df[close_col].rolling(window=period).mean()
            
            if len(df) < 2 or pd.isna(df['_MA'].iloc[-1]):
                return {"error": "数据不足以计算 MA"}
            
            ma_value = float(df['_MA'].iloc[-1])
            ma_prev = float(df['_MA'].iloc[-2]) if len(df) >= 2 else ma_value
            
            # 判断趋势
            if ma_value > ma_prev * 1.001:
                trend = "up"
            elif ma_value < ma_prev * 0.999:
                trend = "down"
            else:
                trend = "flat"
            
            return {
                "symbol": symbol,
                "market": market,
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
    def calculate_rsi(symbol: str, period: int = 14, market: str = "CN-A") -> Dict:
        """
        计算 RSI 相对强弱指标（支持多市场）
        
        Args:
            symbol: 股票代码
            period: RSI 周期
            market: 市场类型 CN-A / US / HK
            
        Returns:
            {
                "symbol": "000001",
                "indicator": "RSI",
                "value": 68.5,
                "signal": "overbought/oversold/neutral"
            }
        """
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=period + 30)
            
            if df.empty or len(df) < period + 1:
                return {"error": "数据不足以计算 RSI"}
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            closes = df[close_col].values
            
            # 计算价格变动
            deltas = np.diff(closes)
            
            # 分离上涨和下跌
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # 计算平均涨跌幅（使用 EMA）
            avg_gain = pd.Series(gains).ewm(span=period, adjust=False).mean().iloc[-1]
            avg_loss = pd.Series(losses).ewm(span=period, adjust=False).mean().iloc[-1]
            
            if avg_loss == 0:
                rsi_value = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
            
            # 判断信号
            if rsi_value > 70:
                signal = "overbought"  # 超买
            elif rsi_value < 30:
                signal = "oversold"    # 超卖
            else:
                signal = "neutral"
            
            return {
                "symbol": symbol,
                "market": market,
                "indicator": "RSI",
                "period": period,
                "value": round(rsi_value, 2),
                "signal": signal
            }
        except Exception as e:
            logger.error(f"RSI 计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_macd(symbol: str, market: str = "CN-A") -> Dict:
        """
        计算 MACD 指标（支持多市场）
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            
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
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=60)
            
            if df.empty or len(df) < 35:
                return {"error": "数据不足以计算 MACD"}
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            closes = df[close_col]
            
            # 计算 EMA12 和 EMA26
            ema12 = closes.ewm(span=12, adjust=False).mean()
            ema26 = closes.ewm(span=26, adjust=False).mean()
            
            # DIFF = EMA12 - EMA26
            diff_series = ema12 - ema26
            
            # DEA = DIFF 的 9 日 EMA
            dea_series = diff_series.ewm(span=9, adjust=False).mean()
            
            # MACD = 2 * (DIFF - DEA)
            macd_series = 2 * (diff_series - dea_series)
            
            # 获取当前和前一天的值
            diff = float(diff_series.iloc[-1])
            dea = float(dea_series.iloc[-1])
            macd = float(macd_series.iloc[-1])
            
            diff_prev = float(diff_series.iloc[-2])
            dea_prev = float(dea_series.iloc[-2])
            
            # 判断金叉死叉
            if diff > dea and diff_prev <= dea_prev:
                signal = "golden_cross"  # 金叉
            elif diff < dea and diff_prev >= dea_prev:
                signal = "dead_cross"    # 死叉
            else:
                signal = "neutral"
            
            return {
                "symbol": symbol,
                "market": market,
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
    def calculate_boll(symbol: str, period: int = 20, std_num: int = 2, market: str = "CN-A") -> Dict:
        """
        计算布林带（支持多市场）
        
        Args:
            symbol: 股票代码
            period: 周期
            std_num: 标准差倍数
            market: 市场类型 CN-A / US / HK
            
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
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=period + 10)
            
            if df.empty or len(df) < period:
                return {"error": "数据不足以计算布林带"}
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            closes = df[close_col]
            
            # 计算中轨（MA）
            middle = closes.rolling(window=period).mean().iloc[-1]
            
            # 计算标准差
            std = closes.rolling(window=period).std().iloc[-1]
            
            # 计算上下轨
            upper = middle + std_num * std
            lower = middle - std_num * std
            
            current_price = float(closes.iloc[-1])
            
            # 判断位置
            if current_price >= upper:
                position = "upper"
            elif current_price <= lower:
                position = "lower"
            else:
                position = "middle"
            
            return {
                "symbol": symbol,
                "market": market,
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
    def check_ma_cross(symbol: str, fast_period: int = 5, slow_period: int = 20, market: str = "CN-A") -> Dict:
        """
        检查均线交叉（支持多市场）
        
        Args:
            symbol: 股票代码
            fast_period: 快线周期
            slow_period: 慢线周期
            market: 市场类型 CN-A / US / HK
            
        Returns:
            {
                "symbol": "000001",
                "signal": "golden_cross/dead_cross/none",
                "fast_ma": 12.5,
                "slow_ma": 12.0
            }
        """
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=slow_period + 10)
            
            if df.empty or len(df) < slow_period + 2:
                return {"error": "数据不足以检查均线交叉"}
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            closes = df[close_col]
            
            # 计算均线
            fast_ma_series = closes.rolling(window=fast_period).mean()
            slow_ma_series = closes.rolling(window=slow_period).mean()
            
            fast_ma = float(fast_ma_series.iloc[-1])
            slow_ma = float(slow_ma_series.iloc[-1])
            fast_ma_prev = float(fast_ma_series.iloc[-2])
            slow_ma_prev = float(slow_ma_series.iloc[-2])
            
            # 判断交叉
            if fast_ma > slow_ma and fast_ma_prev <= slow_ma_prev:
                signal = "golden_cross"
            elif fast_ma < slow_ma and fast_ma_prev >= slow_ma_prev:
                signal = "dead_cross"
            else:
                signal = "none"
            
            return {
                "symbol": symbol,
                "market": market,
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
    def comprehensive_analysis(symbol: str, market: str = "CN-A") -> Dict:
        """
        综合技术分析（支持多市场）
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            
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
            "market": market,
            "ma5": TechnicalAnalyzer.calculate_ma(symbol, 5, market),
            "ma20": TechnicalAnalyzer.calculate_ma(symbol, 20, market),
            "rsi": TechnicalAnalyzer.calculate_rsi(symbol, 14, market),
            "macd": TechnicalAnalyzer.calculate_macd(symbol, market),
            "boll": TechnicalAnalyzer.calculate_boll(symbol, 20, 2, market)
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
    
    # ==================== 交易理念核心方法 ====================
    # 参考: ZhuLinsen/daily_stock_analysis
    
    @staticmethod
    def calculate_bias(symbol: str, market: str = "CN-A", period: int = 5) -> Dict:
        """
        计算乖离率 BIAS
        
        公式: (现价 - MA) / MA × 100%
        
        交易理念:
        - 乖离率 < 2%: 最佳买点
        - 乖离率 2-5%: 可小仓介入
        - 乖离率 > 5%: 严禁追高！
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            period: 均线周期（默认5日）
            
        Returns:
            {
                "symbol": "000001",
                "bias": 3.25,             # 乖离率百分比
                "current_price": 12.5,
                "ma_value": 12.1,
                "status": "安全/警戒/危险",
                "trading_advice": "可小仓介入"
            }
        """
        try:
            # 获取带均线的历史数据
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=30)
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            # 获取最新数据
            latest = df.iloc[-1]
            close_col = '收盘' if '收盘' in df.columns else 'close'
            current_price = float(latest[close_col])
            
            # 获取对应均线值
            ma_col = f'MA{period}'
            if ma_col not in df.columns:
                return {"error": f"均线 {ma_col} 计算失败"}
            
            ma_value = float(latest[ma_col])
            
            if ma_value == 0:
                return {"error": "均线值为0"}
            
            # 计算乖离率
            bias = (current_price - ma_value) / ma_value * 100
            
            # 判断状态和建议（核心交易理念）
            if abs(bias) < 2:
                status = "安全"
                trading_advice = "最佳买点区间，可积极介入"
            elif abs(bias) < 5:
                status = "警戒"
                trading_advice = "可小仓介入，注意控制仓位"
            else:
                status = "危险"
                if bias > 0:
                    trading_advice = "⚠️ 严禁追高！乖离率过大，等待回调"
                else:
                    trading_advice = "超跌区域，可能有反弹机会"
            
            return {
                "symbol": symbol,
                "market": market,
                "bias": round(bias, 2),
                "current_price": round(current_price, 2),
                "ma_period": period,
                "ma_value": round(ma_value, 2),
                "status": status,
                "trading_advice": trading_advice
            }
            
        except Exception as e:
            logger.error(f"乖离率计算失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def check_ma_alignment(symbol: str, market: str = "CN-A") -> Dict:
        """
        检查均线排列状态
        
        多头排列: MA5 > MA10 > MA20（趋势向上）
        空头排列: MA5 < MA10 < MA20（趋势向下）
        缠绕震荡: 均线交织，方向不明
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            
        Returns:
            {
                "symbol": "000001",
                "is_bullish": True,        # 是否多头排列
                "is_bearish": False,       # 是否空头排列
                "alignment": "多头排列",   # 排列状态描述
                "ma5": 12.5,
                "ma10": 12.3,
                "ma20": 12.0,
                "trend_strength": 75,      # 趋势强度 0-100
                "trading_advice": "处于多头排列，趋势良好"
            }
        """
        try:
            df = MarketDataProvider.get_hist_with_ma(symbol, market, days=30)
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            latest = df.iloc[-1]
            
            ma5 = float(latest['MA5']) if pd.notna(latest['MA5']) else 0
            ma10 = float(latest['MA10']) if pd.notna(latest['MA10']) else 0
            ma20 = float(latest['MA20']) if pd.notna(latest['MA20']) else 0
            
            if ma5 == 0 or ma10 == 0 or ma20 == 0:
                return {"error": "均线数据不完整"}
            
            # 判断排列状态
            is_bullish = ma5 > ma10 > ma20
            is_bearish = ma5 < ma10 < ma20
            
            if is_bullish:
                alignment = "多头排列"
                trading_advice = "✅ 趋势良好，可顺势操作"
            elif is_bearish:
                alignment = "空头排列"
                trading_advice = "❌ 空头排列，建议规避或观望"
            else:
                alignment = "缠绕震荡"
                trading_advice = "⚠️ 方向不明，建议等待明确信号"
            
            # 计算趋势强度（基于均线间距）
            if is_bullish:
                # 多头强度：均线间距越大越强
                spread_5_10 = (ma5 - ma10) / ma10 * 100
                spread_10_20 = (ma10 - ma20) / ma20 * 100
                trend_strength = min(100, max(0, (spread_5_10 + spread_10_20) * 10 + 50))
            elif is_bearish:
                # 空头强度
                spread_5_10 = (ma10 - ma5) / ma5 * 100
                spread_10_20 = (ma20 - ma10) / ma10 * 100
                trend_strength = min(100, max(0, (spread_5_10 + spread_10_20) * 10 + 50))
            else:
                trend_strength = 50  # 缠绕时为中性
            
            return {
                "symbol": symbol,
                "market": market,
                "is_bullish": is_bullish,
                "is_bearish": is_bearish,
                "alignment": alignment,
                "ma5": round(ma5, 2),
                "ma10": round(ma10, 2),
                "ma20": round(ma20, 2),
                "trend_strength": round(trend_strength),
                "trading_advice": trading_advice
            }
            
        except Exception as e:
            logger.error(f"均线排列检查失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def calculate_trend_score(symbol: str, market: str = "CN-A") -> Dict:
        """
        计算趋势综合评分（0-100分）
        
        评分维度:
        - 均线排列 (+30分)
        - 乖离率安全 (+20分)
        - 量能配合 (+20分)
        - RSI 健康 (+15分)
        - MACD 金叉 (+15分)
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            
        Returns:
            {
                "symbol": "000001",
                "total_score": 75,
                "signal": "🟢买入",
                "breakdown": {
                    "ma_alignment": {"score": 30, "status": "多头排列"},
                    "bias": {"score": 20, "value": 1.5},
                    "volume": {"score": 15, "status": "温和放量"},
                    "rsi": {"score": 10, "value": 55},
                    "macd": {"score": 0, "status": "中性"}
                },
                "checklist": [
                    {"name": "多头排列", "status": "✅", "value": "MA5>MA10>MA20"},
                    {"name": "乖离率", "status": "✅", "value": "1.5%"},
                    ...
                ]
            }
        """
        try:
            result = {
                "symbol": symbol,
                "market": market,
                "total_score": 0,
                "breakdown": {},
                "checklist": []
            }
            
            # 1. 均线排列评分（满分30分）
            ma_result = TechnicalAnalyzer.check_ma_alignment(symbol, market)
            if "error" not in ma_result:
                if ma_result["is_bullish"]:
                    ma_score = 30
                    ma_status = "✅"
                elif ma_result["is_bearish"]:
                    ma_score = 0
                    ma_status = "❌"
                else:
                    ma_score = 15
                    ma_status = "⚠️"
                
                result["breakdown"]["ma_alignment"] = {
                    "score": ma_score,
                    "status": ma_result["alignment"]
                }
                result["checklist"].append({
                    "name": "多头排列",
                    "status": ma_status,
                    "value": f"MA5:{ma_result['ma5']} MA10:{ma_result['ma10']} MA20:{ma_result['ma20']}",
                    "note": ma_result["trading_advice"]
                })
                result["total_score"] += ma_score
            
            # 2. 乖离率评分（满分20分）
            bias_result = TechnicalAnalyzer.calculate_bias(symbol, market)
            if "error" not in bias_result:
                bias_value = abs(bias_result["bias"])
                if bias_value < 2:
                    bias_score = 20
                    bias_status = "✅"
                elif bias_value < 5:
                    bias_score = 10
                    bias_status = "⚠️"
                else:
                    bias_score = 0
                    bias_status = "❌"
                
                result["breakdown"]["bias"] = {
                    "score": bias_score,
                    "value": bias_result["bias"]
                }
                result["checklist"].append({
                    "name": "乖离率<5%",
                    "status": bias_status,
                    "value": f"{bias_result['bias']}%",
                    "note": bias_result["trading_advice"]
                })
                result["total_score"] += bias_score
            
            # 3. 量能配合评分（满分20分）- 仅A股
            if market == "CN-A":
                quote_result = MarketDataProvider.get_realtime_quote(symbol, market)
                if "error" not in quote_result:
                    volume_ratio = quote_result.get("volume_ratio", 1.0)
                    
                    if 0.8 <= volume_ratio <= 2.0:
                        volume_score = 20
                        volume_status = "✅"
                    elif 0.5 <= volume_ratio < 0.8 or 2.0 < volume_ratio <= 3.0:
                        volume_score = 10
                        volume_status = "⚠️"
                    else:
                        volume_score = 5
                        volume_status = "⚠️"
                    
                    result["breakdown"]["volume"] = {
                        "score": volume_score,
                        "status": quote_result.get("volume_ratio_desc", "未知")
                    }
                    result["checklist"].append({
                        "name": "量能配合",
                        "status": volume_status,
                        "value": f"量比{volume_ratio}",
                        "note": quote_result.get("volume_ratio_desc", "")
                    })
                    result["total_score"] += volume_score
            else:
                # 非A股默认给15分
                result["total_score"] += 15
                result["breakdown"]["volume"] = {"score": 15, "status": "N/A"}
            
            # 4. RSI 健康评分（满分15分）
            try:
                rsi_result = TechnicalAnalyzer.calculate_rsi(symbol, 14, market)
                if "error" not in rsi_result:
                    rsi_value = rsi_result.get("value", 50)
                    rsi_signal = rsi_result.get("signal", "neutral")
                    
                    if 30 <= rsi_value <= 70:
                        rsi_score = 15
                        rsi_status = "✅"
                    elif rsi_signal == "oversold":
                        rsi_score = 12  # 超卖可能有反弹
                        rsi_status = "⚠️"
                    else:
                        rsi_score = 5   # 超买风险
                        rsi_status = "❌"
                    
                    result["breakdown"]["rsi"] = {
                        "score": rsi_score,
                        "value": rsi_value
                    }
                    result["checklist"].append({
                        "name": "RSI健康",
                        "status": rsi_status,
                        "value": f"RSI={rsi_value}",
                        "note": rsi_signal
                    })
                    result["total_score"] += rsi_score
            except Exception:
                result["total_score"] += 7  # 默认中性分
            
            # 5. MACD 信号评分（满分15分）
            try:
                macd_result = TechnicalAnalyzer.calculate_macd(symbol, market)
                if "error" not in macd_result:
                    macd_signal = macd_result.get("signal", "neutral")
                    
                    if macd_signal == "golden_cross":
                        macd_score = 15
                        macd_status = "✅"
                    elif macd_signal == "dead_cross":
                        macd_score = 0
                        macd_status = "❌"
                    else:
                        macd_score = 7
                        macd_status = "⚠️"
                    
                    result["breakdown"]["macd"] = {
                        "score": macd_score,
                        "status": macd_signal
                    }
                    result["checklist"].append({
                        "name": "MACD金叉",
                        "status": macd_status,
                        "value": f"DIFF:{macd_result.get('diff', 0):.4f}",
                        "note": macd_signal
                    })
                    result["total_score"] += macd_score
            except Exception:
                result["total_score"] += 7  # 默认中性分
            
            # 判断最终信号
            total = result["total_score"]
            if total >= 80:
                result["signal"] = "🟢 强烈买入"
            elif total >= 60:
                result["signal"] = "🟢 买入"
            elif total >= 40:
                result["signal"] = "🟡 观望"
            else:
                result["signal"] = "🔴 卖出/减仓"
            
            return result
            
        except Exception as e:
            logger.error(f"趋势评分计算失败 {symbol}: {e}")
            return {"error": str(e)}

