# coding=utf-8
"""
市场数据提供器

支持 akshare 和 yfinance 两种数据源，可通过配置切换
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#                        抽象基类
# ═══════════════════════════════════════════════════════════════

class DataProviderBase(ABC):
    """数据提供器抽象基类"""
    
    @abstractmethod
    def get_stock_price(self, symbol: str, market: str = "CN-A") -> Dict:
        """获取股票实时价格"""
        pass
    
    @abstractmethod
    def get_index_price(self, symbol: str) -> Dict:
        """获取指数实时数据"""
        pass
    
    @abstractmethod
    def get_stock_hist(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取股票历史数据"""
        pass
    
    @abstractmethod
    def search_stock_by_name(self, keyword: str, market: str = "CN-A") -> List[Dict]:
        """根据关键词搜索股票"""
        pass
    
    @abstractmethod
    def get_realtime_quote(self, symbol: str, market: str = "CN-A") -> Dict:
        """获取实时行情增强数据"""
        pass


# ═══════════════════════════════════════════════════════════════
#                    Akshare 数据提供器
# ═══════════════════════════════════════════════════════════════

class AkshareDataProvider(DataProviderBase):
    """市场数据提供器（基于 akshare）"""
    
    def get_stock_price(self, symbol: str, market: str = "CN-A") -> Dict:
        """
        获取股票实时价格
        
        Args:
            symbol: 股票代码（如 000001, 600000, 00100）
            market: 市场类型 CN-A(A股) / US(美股) / HK(港股)
            
        Returns:
        {'symbol': '00100', 'name': 'MINIMAX-WP', 'price': 356.4, 'change': -8.6, 'change_pct': -2.36, 'volume': 2601806}
        """
        import akshare as ak
        try:
            if market == "CN-A":
                df = ak.stock_zh_a_spot_em()
                stock_data = df[df['代码'] == symbol]
                
                if stock_data.empty:
                    return {"error": f"未找到股票 {symbol}"}
                
                row = stock_data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change": float(row['涨跌额']),
                    "change_pct": float(row['涨跌幅']),
                    "volume": int(row['成交量']),
                    "turnover": float(row['换手率']) if '换手率' in row else 0.0
                }
            
            elif market == "US":
                try:
                    df = ak.stock_us_spot_em()
                    stock_data = df[df['代码'] == symbol]
                    
                    if stock_data.empty:
                        return {"error": f"未找到美股 {symbol}"}
                    
                    row = stock_data.iloc[0]
                    return {
                        "symbol": symbol,
                        "name": row['名称'],
                        "price": float(row['最新价']),
                        "change": float(row['涨跌额']),
                        "change_pct": float(row['涨跌幅']),
                        "volume": int(row['成交量']) if '成交量' in row else 0
                    }
                except Exception as e:
                    logger.warning(f"美股数据获取失败: {e}")
                    return {"error": f"美股数据暂不可用: {str(e)}"}
            
            elif market == "HK":
                df = ak.stock_hk_spot_em()
                stock_data = df[df['代码'] == symbol]
                
                if stock_data.empty:
                    return {"error": f"未找到港股 {symbol}"}
                
                row = stock_data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change": float(row['涨跌额']),
                    "change_pct": float(row['涨跌幅']),
                    "volume": int(row['成交量']) if '成交量' in row else 0
                }
            
            else:
                return {"error": f"不支持的市场类型: {market}"}
                
        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_index_price(self, symbol: str) -> Dict:
        """
        获取指数实时数据
        
        Args:
            symbol: 指数代码（如 000001=上证指数, 399001=深证成指, 399006=创业板指）
        """
        import akshare as ak
        try:
            df = ak.stock_zh_index_spot_em()
            index_data = df[df['代码'] == symbol]
            
            if index_data.empty:
                return {"error": f"未找到指数 {symbol}"}
            
            row = index_data.iloc[0]
            return {
                "symbol": symbol,
                "name": row['名称'],
                "price": float(row['最新价']),
                "change": float(row['涨跌额']),
                "change_pct": float(row['涨跌幅'])
            }
        except Exception as e:
            logger.error(f"获取指数数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_stock_hist(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            period: 周期 daily/weekly/monthly
            adjust: 复权类型 qfq(前复权)/hfq(后复权)/""(不复权)
        """
        import akshare as ak
        try:
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust
            )
            
            return df
        except Exception as e:
            logger.error(f"获取历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def search_stock_by_name(self, keyword: str, market: str = "CN-A") -> List[Dict]:
        """
        根据关键词搜索股票
        
        Args:
            keyword: 搜索关键词（股票名称或代码）
            market: 市场类型 CN-A / US / HK
        """
        import akshare as ak
        try:
            if market == "CN-A":
                df = ak.stock_zh_a_spot_em()
                matches = df[
                    df['名称'].str.contains(keyword, na=False) | 
                    df['代码'].str.contains(keyword, na=False)
                ]
                
                results = []
                for _, row in matches.head(10).iterrows():
                    results.append({
                        "symbol": row['代码'],
                        "name": row['名称'],
                        "market": "CN-A"
                    })
                
                return results
            
            elif market == "US":
                df = ak.stock_us_spot_em()
                matches = df[
                    df['名称'].str.contains(keyword, na=False, case=False) | 
                    df['代码'].str.contains(keyword, na=False, case=False)
                ]
                
                results = []
                for _, row in matches.head(10).iterrows():
                    results.append({
                        "symbol": row['代码'],
                        "name": row['名称'],
                        "market": "US"
                    })
                
                return results
            
            elif market == "HK":
                df = ak.stock_hk_spot_em()
                matches = df[
                    df['名称'].str.contains(keyword, na=False) | 
                    df['代码'].str.contains(keyword, na=False)
                ]
                
                results = []
                for _, row in matches.head(10).iterrows():
                    results.append({
                        "symbol": row['代码'],
                        "name": row['名称'],
                        "market": "HK"
                    })
                
                return results
            
            else:
                return []
        except Exception as e:
            logger.error(f"搜索股票失败 {keyword}: {e}")
            return []
    
    def get_realtime_quote(self, symbol: str, market: str = "CN-A") -> Dict:
        """
        获取实时行情增强数据（量比、换手率、市盈率等）
        """
        import akshare as ak
        try:
            if market == "CN-A":
                df = ak.stock_zh_a_spot_em()
                stock_data = df[df['代码'] == symbol]
                
                if stock_data.empty:
                    return {"error": f"未找到股票 {symbol}"}
                
                row = stock_data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change_pct": float(row['涨跌幅']),
                    "volume_ratio": float(row['量比']) if '量比' in row and pd.notna(row['量比']) else 0,
                    "turnover_rate": float(row['换手率']) if '换手率' in row and pd.notna(row['换手率']) else 0,
                    "pe_ratio": float(row['市盈率-动态']) if '市盈率-动态' in row and pd.notna(row['市盈率-动态']) else 0,
                    "pb_ratio": float(row['市净率']) if '市净率' in row and pd.notna(row['市净率']) else 0,
                    "total_mv": float(row['总市值']) / 1e8 if '总市值' in row and pd.notna(row['总市值']) else 0,
                    "circ_mv": float(row['流通市值']) / 1e8 if '流通市值' in row and pd.notna(row['流通市值']) else 0,
                    "volume_ratio_desc": self._get_volume_ratio_desc(
                        float(row['量比']) if '量比' in row and pd.notna(row['量比']) else 0
                    )
                }
            
            elif market == "US":
                df = ak.stock_us_spot_em()
                stock_data = df[df['代码'].str.endswith(f".{symbol}")]
                
                if stock_data.empty:
                    stock_data = df[df['代码'] == symbol]
                
                if stock_data.empty:
                    return {"error": f"未找到美股 {symbol}"}
                
                row = stock_data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change_pct": float(row['涨跌幅']),
                    "volume": int(row['成交量']) if '成交量' in row and pd.notna(row['成交量']) else 0,
                    "total_mv": float(row['总市值']) / 1e8 if '总市值' in row and pd.notna(row['总市值']) else 0
                }
            
            elif market == "HK":
                df = ak.stock_hk_spot_em()
                stock_data = df[df['代码'] == symbol]
                
                if stock_data.empty:
                    return {"error": f"未找到港股 {symbol}"}
                
                row = stock_data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row['名称'],
                    "price": float(row['最新价']),
                    "change_pct": float(row['涨跌幅']),
                    "volume": int(row['成交量']) if '成交量' in row and pd.notna(row['成交量']) else 0,
                    "turnover_rate": float(row['换手率']) if '换手率' in row and pd.notna(row['换手率']) else 0,
                    "pe_ratio": float(row['市盈率']) if '市盈率' in row and pd.notna(row['市盈率']) else 0,
                    "total_mv": float(row['总市值']) / 1e8 if '总市值' in row and pd.notna(row['总市值']) else 0
                }
            
            else:
                return {"error": f"不支持的市场类型: {market}"}
                
        except Exception as e:
            logger.error(f"获取增强行情数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_volume_ratio_desc(volume_ratio: float) -> str:
        """根据量比获取描述"""
        if volume_ratio < 0.5:
            return "极度缩量"
        elif volume_ratio < 0.8:
            return "缩量"
        elif volume_ratio < 1.2:
            return "平量"
        elif volume_ratio < 2.0:
            return "温和放量"
        elif volume_ratio < 3.0:
            return "明显放量"
        else:
            return "巨量"
    
    def get_chip_distribution(self, symbol: str) -> Dict:
        """获取筹码分布数据（仅A股）"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
            df = self.get_stock_hist(symbol, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            current_price = float(df.iloc[-1]['收盘'])
            volumes = df['成交量'].values
            closes = df['收盘'].values
            total_volume = volumes.sum()
            
            if total_volume > 0:
                avg_cost = (volumes * closes).sum() / total_volume
            else:
                avg_cost = current_price
            
            profit_days = len(df[df['收盘'] <= current_price])
            profit_ratio = profit_days / len(df) if len(df) > 0 else 0.5
            
            volume_std = df['成交量'].std()
            volume_mean = df['成交量'].mean()
            concentration = volume_std / volume_mean if volume_mean > 0 else 0.5
            
            cost_diff = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
            
            if profit_ratio > 0.9 and cost_diff > 20:
                chip_status = "警惕"
            elif profit_ratio > 0.7:
                chip_status = "健康"
            elif profit_ratio > 0.5:
                chip_status = "一般"
            else:
                chip_status = "套牢区"
            
            return {
                "symbol": symbol,
                "profit_ratio": round(profit_ratio, 3),
                "avg_cost": round(avg_cost, 2),
                "concentration_90": round(concentration, 3),
                "concentration_70": round(concentration * 0.7, 3),
                "chip_status": chip_status,
                "cost_diff_pct": round(cost_diff, 2)
            }
            
        except Exception as e:
            logger.error(f"获取筹码分布失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_hist_with_ma(
        self,
        symbol: str,
        market: str = "CN-A",
        days: int = 60
    ) -> pd.DataFrame:
        """获取带均线的历史数据"""
        import akshare as ak
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days + 60)).strftime("%Y%m%d")
            
            if market == "CN-A":
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    period="daily",
                    adjust="qfq"
                )
            elif market == "US":
                us_symbol = symbol if "." in symbol else f"105.{symbol}"
                try:
                    df = ak.stock_us_hist(
                        symbol=us_symbol,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                except Exception:
                    us_symbol = f"106.{symbol}"
                    df = ak.stock_us_hist(
                        symbol=us_symbol,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
            elif market == "HK":
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
            else:
                return pd.DataFrame()
            
            if df.empty:
                return df
            
            close_col = '收盘' if '收盘' in df.columns else 'close'
            df['MA5'] = df[close_col].rolling(window=5).mean()
            df['MA10'] = df[close_col].rolling(window=10).mean()
            df['MA20'] = df[close_col].rolling(window=20).mean()
            df['MA60'] = df[close_col].rolling(window=60).mean()
            
            return df.tail(days)
            
        except Exception as e:
            logger.error(f"获取带均线历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_us_stock_hist(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """获取美股历史数据"""
        import akshare as ak
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            df = ak.stock_us_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            return df
        except Exception as e:
            logger.error(f"获取美股历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_hk_stock_hist(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """获取港股历史数据"""
        import akshare as ak
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
            
            df = ak.stock_hk_hist(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            return df
        except Exception as e:
            logger.error(f"获取港股历史数据失败 {symbol}: {e}")
            return pd.DataFrame()


# ═══════════════════════════════════════════════════════════════
#                    YFinance 数据提供器
# ═══════════════════════════════════════════════════════════════

class YFinanceDataProvider(DataProviderBase):
    """市场数据提供器（基于 yfinance）"""
    
    @staticmethod
    def _convert_symbol(symbol: str, market: str) -> str:
        """
        将股票代码转换为 Yahoo Finance 格式
        
        CN-A (上海): 600xxx → 600xxx.SS
        CN-A (深圳): 000xxx/300xxx → 000xxx.SZ/300xxx.SZ
        HK: 00700 → 0700.HK (保留4位数字)
        US: AAPL → AAPL (原样)
        """
        if market == "CN-A":
            if symbol.startswith('6'):
                return f"{symbol}.SS"
            else:
                return f"{symbol}.SZ"
        elif market == "HK":
            # 港股代码：去掉首位零，但保留至少4位数字
            # 00700 -> 0700.HK, 09988 -> 9988.HK
            clean_symbol = symbol.lstrip('0') or '0'
            # 确保至少4位
            if len(clean_symbol) < 4:
                clean_symbol = symbol[-4:]
            return f"{clean_symbol}.HK"
        elif market == "US":
            return symbol
        else:
            return symbol
    
    def get_stock_price(self, symbol: str, market: str = "CN-A") -> Dict:
        """
        获取股票实时价格
        """
        import yfinance as yf
        try:
            yf_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                return {"error": f"未找到股票 {symbol}"}
            
            return {
                "symbol": symbol,
                "name": info.get('shortName', info.get('longName', symbol)),
                "price": float(info.get('regularMarketPrice', 0)),
                "change": float(info.get('regularMarketChange', 0)),
                "change_pct": float(info.get('regularMarketChangePercent', 0)),
                "volume": int(info.get('regularMarketVolume', 0)),
                "turnover": 0.0  # yfinance 不直接提供换手率
            }
        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_index_price(self, symbol: str) -> Dict:
        """
        获取指数实时数据
        
        常用指数: ^GSPC(标普500), ^DJI(道琼斯), ^IXIC(纳斯达克), ^HSI(恒生)
        """
        import yfinance as yf
        try:
            # 中国指数代码映射
            index_mapping = {
                "000001": "000001.SS",  # 上证指数
                "399001": "399001.SZ",  # 深证成指
                "399006": "399006.SZ",  # 创业板指
            }
            
            yf_symbol = index_mapping.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                return {"error": f"未找到指数 {symbol}"}
            
            return {
                "symbol": symbol,
                "name": info.get('shortName', info.get('longName', symbol)),
                "price": float(info.get('regularMarketPrice', 0)),
                "change": float(info.get('regularMarketChange', 0)),
                "change_pct": float(info.get('regularMarketChangePercent', 0))
            }
        except Exception as e:
            logger.error(f"获取指数数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_stock_hist(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq",
        market: str = "CN-A"
    ) -> pd.DataFrame:
        """
        获取股票历史数据
        """
        import yfinance as yf
        try:
            yf_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yf_symbol)
            
            # 转换日期格式 YYYYMMDD → YYYY-MM-DD
            start = None
            end = None
            if start_date:
                start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            if end_date:
                end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            
            # 转换周期
            interval_map = {"daily": "1d", "weekly": "1wk", "monthly": "1mo"}
            interval = interval_map.get(period, "1d")
            
            if start and end:
                df = ticker.history(start=start, end=end, interval=interval)
            else:
                df = ticker.history(period="1y", interval=interval)
            
            if df.empty:
                return df
            
            # 重命名列以匹配 akshare 格式
            df = df.reset_index()
            df = df.rename(columns={
                'Date': '日期',
                'Open': '开盘',
                'High': '最高',
                'Low': '最低',
                'Close': '收盘',
                'Volume': '成交量'
            })
            
            return df
        except Exception as e:
            logger.error(f"获取历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def search_stock_by_name(self, keyword: str, market: str = "CN-A") -> List[Dict]:
        """
        根据关键词搜索股票
        """
        import yfinance as yf
        try:
            search = yf.Search(keyword)
            quotes = search.quotes if hasattr(search, 'quotes') else []
            
            results = []
            for quote in quotes[:10]:
                symbol = quote.get('symbol', '')
                
                # 确定市场类型
                if symbol.endswith('.SS') or symbol.endswith('.SZ'):
                    detected_market = "CN-A"
                    clean_symbol = symbol.split('.')[0]
                elif symbol.endswith('.HK'):
                    detected_market = "HK"
                    clean_symbol = symbol.split('.')[0].zfill(5)
                else:
                    detected_market = "US"
                    clean_symbol = symbol
                
                if market == "all" or market == detected_market:
                    results.append({
                        "symbol": clean_symbol,
                        "name": quote.get('shortname', quote.get('longname', symbol)),
                        "market": detected_market
                    })
            
            return results
        except Exception as e:
            logger.error(f"搜索股票失败 {keyword}: {e}")
            return []
    
    def get_realtime_quote(self, symbol: str, market: str = "CN-A") -> Dict:
        """
        获取实时行情增强数据
        """
        import yfinance as yf
        try:
            yf_symbol = self._convert_symbol(symbol, market)
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                return {"error": f"未找到股票 {symbol}"}
            
            return {
                "symbol": symbol,
                "name": info.get('shortName', info.get('longName', symbol)),
                "price": float(info.get('regularMarketPrice', 0)),
                "change_pct": float(info.get('regularMarketChangePercent', 0)),
                "volume_ratio": 0,  # yfinance 不直接提供
                "turnover_rate": 0,  # yfinance 不直接提供
                "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0,
                "pb_ratio": float(info.get('priceToBook', 0)) if info.get('priceToBook') else 0,
                "total_mv": float(info.get('marketCap', 0)) / 1e8 if info.get('marketCap') else 0,
                "circ_mv": float(info.get('marketCap', 0)) / 1e8 if info.get('marketCap') else 0,
                "volume_ratio_desc": "N/A"
            }
        except Exception as e:
            logger.error(f"获取增强行情数据失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_chip_distribution(self, symbol: str, market: str = "CN-A") -> Dict:
        """获取筹码分布数据（通过历史数据计算）"""
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
            df = self.get_stock_hist(symbol, start_date=start_date, end_date=end_date, market=market)
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            close_col = '收盘' if '收盘' in df.columns else 'Close'
            volume_col = '成交量' if '成交量' in df.columns else 'Volume'
            
            current_price = float(df.iloc[-1][close_col])
            volumes = df[volume_col].values
            closes = df[close_col].values
            total_volume = volumes.sum()
            
            if total_volume > 0:
                avg_cost = (volumes * closes).sum() / total_volume
            else:
                avg_cost = current_price
            
            profit_days = len(df[df[close_col] <= current_price])
            profit_ratio = profit_days / len(df) if len(df) > 0 else 0.5
            
            volume_std = df[volume_col].std()
            volume_mean = df[volume_col].mean()
            concentration = volume_std / volume_mean if volume_mean > 0 else 0.5
            
            cost_diff = (current_price - avg_cost) / avg_cost * 100 if avg_cost > 0 else 0
            
            if profit_ratio > 0.9 and cost_diff > 20:
                chip_status = "警惕"
            elif profit_ratio > 0.7:
                chip_status = "健康"
            elif profit_ratio > 0.5:
                chip_status = "一般"
            else:
                chip_status = "套牢区"
            
            return {
                "symbol": symbol,
                "profit_ratio": round(profit_ratio, 3),
                "avg_cost": round(avg_cost, 2),
                "concentration_90": round(concentration, 3),
                "concentration_70": round(concentration * 0.7, 3),
                "chip_status": chip_status,
                "cost_diff_pct": round(cost_diff, 2)
            }
            
        except Exception as e:
            logger.error(f"获取筹码分布失败 {symbol}: {e}")
            return {"error": str(e)}
    
    def get_hist_with_ma(
        self,
        symbol: str,
        market: str = "CN-A",
        days: int = 60
    ) -> pd.DataFrame:
        """获取带均线的历史数据"""
        try:
            start_date = (datetime.now() - timedelta(days=days + 60)).strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")
            
            df = self.get_stock_hist(symbol, start_date=start_date, end_date=end_date, market=market)
            
            if df.empty:
                return df
            
            close_col = '收盘' if '收盘' in df.columns else 'Close'
            df['MA5'] = df[close_col].rolling(window=5).mean()
            df['MA10'] = df[close_col].rolling(window=10).mean()
            df['MA20'] = df[close_col].rolling(window=20).mean()
            df['MA60'] = df[close_col].rolling(window=60).mean()
            
            return df.tail(days)
            
        except Exception as e:
            logger.error(f"获取带均线历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_us_stock_hist(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """获取美股历史数据"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        return self.get_stock_hist(symbol, start_date=start_date, end_date=end_date, market="US")
    
    def get_hk_stock_hist(self, symbol: str, days: int = 365) -> pd.DataFrame:
        """获取港股历史数据"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")
        return self.get_stock_hist(symbol, start_date=start_date, end_date=end_date, market="HK")


# ═══════════════════════════════════════════════════════════════
#                    数据提供器工厂
# ═══════════════════════════════════════════════════════════════

class MarketDataProvider:
    """
    市场数据提供器工厂
    
    根据配置返回对应的数据提供器实例
    """
    
    _providers = {
        "akshare": AkshareDataProvider,
        "yfinance": YFinanceDataProvider
    }
    
    _instance_cache: Dict[str, DataProviderBase] = {}
    
    @classmethod
    def get_provider(cls, source: str = None) -> DataProviderBase:
        """
        获取数据提供器实例
        
        Args:
            source: 数据源类型 akshare / yfinance / auto
                   如果为 None，从配置文件读取
        
        Returns:
            DataProviderBase 实例
        """
        if source is None:
            source = cls._get_config_source()
        
        if source == "auto":
            # 自动模式：优先使用 akshare，失败时回退到 yfinance
            source = "akshare"
        
        if source not in cls._providers:
            logger.warning(f"未知数据源 {source}，使用默认 akshare")
            source = "akshare"
        
        if source not in cls._instance_cache:
            cls._instance_cache[source] = cls._providers[source]()
        
        return cls._instance_cache[source]
    
    @classmethod
    def _get_config_source(cls) -> str:
        """从配置文件读取数据源设置"""
        try:
            import yaml
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent.parent / "config" / "analysis.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('ai_analysis', {}).get('data_source', 'akshare')
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
        
        return "akshare"
    
    # ==================== 静态方法兼容旧接口 ====================
    
    @staticmethod
    def get_stock_price(symbol: str, market: str = "CN-A") -> Dict:
        """获取股票实时价格（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_stock_price(symbol, market)
    
    @staticmethod
    def get_index_price(symbol: str) -> Dict:
        """获取指数实时数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_index_price(symbol)
    
    @staticmethod
    def get_stock_hist(
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "daily",
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """获取股票历史数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_stock_hist(
            symbol, start_date, end_date, period, adjust
        )
    
    @staticmethod
    def search_stock_by_name(keyword: str, market: str = "CN-A") -> List[Dict]:
        """根据关键词搜索股票（兼容旧接口）"""
        return MarketDataProvider.get_provider().search_stock_by_name(keyword, market)
    
    @staticmethod
    def get_realtime_quote(symbol: str, market: str = "CN-A") -> Dict:
        """获取实时行情增强数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_realtime_quote(symbol, market)
    
    @staticmethod
    def get_chip_distribution(symbol: str) -> Dict:
        """获取筹码分布数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_chip_distribution(symbol)
    
    @staticmethod
    def get_hist_with_ma(symbol: str, market: str = "CN-A", days: int = 60) -> pd.DataFrame:
        """获取带均线的历史数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_hist_with_ma(symbol, market, days)
    
    @staticmethod
    def get_us_stock_hist(symbol: str, days: int = 365) -> pd.DataFrame:
        """获取美股历史数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_us_stock_hist(symbol, days)
    
    @staticmethod
    def get_hk_stock_hist(symbol: str, days: int = 365) -> pd.DataFrame:
        """获取港股历史数据（兼容旧接口）"""
        return MarketDataProvider.get_provider().get_hk_stock_hist(symbol, days)
    
    @staticmethod
    def _get_volume_ratio_desc(volume_ratio: float) -> str:
        """根据量比获取描述（兼容旧接口）"""
        return AkshareDataProvider._get_volume_ratio_desc(volume_ratio)
