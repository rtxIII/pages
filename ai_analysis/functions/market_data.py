# coding=utf-8
"""
市场数据提供器

使用 akshare 获取股票市场数据
"""

import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketDataProvider:
    """市场数据提供器（基于 akshare）"""
    
    @staticmethod
    def get_stock_price(symbol: str, market: str = "CN-A") -> Dict:
        """
        获取股票实时价格
        
        Args:
            symbol: 股票代码（如 000001, 600000, 00100）
            market: 市场类型 CN-A(A股) / US(美股) / HK(港股)
            
        Returns:
        {'symbol': '00100', 'name': 'MINIMAX-WP', 'price': 356.4, 'change': -8.6, 'change_pct': -2.36, 'volume': 2601806}
        """
        try:
            if market == "CN-A":
                # A股实时行情
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
                # 美股实时行情（需要股票代码如 AAPL）
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
                # 港股实时行情
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
    
    @staticmethod
    def get_index_price(symbol: str) -> Dict:
        """
        获取指数实时数据
        
        Args:
            symbol: 指数代码（如 000001=上证指数, 399001=深证成指, 399006=创业板指）
            
        Returns:
            {
                "symbol": "000001",
                "name": "上证指数",
                "price": 3234.56,
                "change_pct": 0.52
            }
        """
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
    
    @staticmethod
    def get_stock_hist(
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
            
        Returns:
            DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
        """
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
    
    @staticmethod
    def search_stock_by_name(keyword: str, market: str = "CN-A") -> List[Dict]:
        """
        根据关键词搜索股票
        
        Args:
            keyword: 搜索关键词（股票名称或代码）
            market: 市场类型 CN-A / US / HK
            
        Returns:
            [{"symbol": "000001", "name": "平安银行", "market": "CN-A"}]
        """
        try:
            if market == "CN-A":
                df = ak.stock_zh_a_spot_em()
                # 模糊搜索
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
    
    # ==================== 增强数据获取方法 ====================
    
    @staticmethod
    def get_realtime_quote(symbol: str, market: str = "CN-A") -> Dict:
        """
        获取实时行情增强数据（量比、换手率、市盈率等）
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            
        Returns:
            {
                "symbol": "000001",
                "name": "平安银行",
                "price": 12.34,
                "change_pct": 0.98,
                "volume_ratio": 1.2,       # 量比
                "turnover_rate": 2.5,      # 换手率
                "pe_ratio": 8.5,           # 市盈率
                "pb_ratio": 0.8,           # 市净率
                "total_mv": 2000,          # 总市值(亿)
                "circ_mv": 1500            # 流通市值(亿)
            }
        """
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
                    "volume_ratio_desc": MarketDataProvider._get_volume_ratio_desc(
                        float(row['量比']) if '量比' in row and pd.notna(row['量比']) else 0
                    )
                }
            
            elif market == "US":
                df = ak.stock_us_spot_em()
                # 美股代码格式为 105.AAPL，需要尝试多种匹配方式
                stock_data = df[df['代码'].str.endswith(f".{symbol}")]
                
                if stock_data.empty:
                    # 尝试直接匹配
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
    
    @staticmethod
    def get_chip_distribution(symbol: str) -> Dict:
        """
        获取筹码分布数据（仅A股）
        
        Args:
            symbol: 股票代码
            
        Returns:
            {
                "symbol": "000001",
                "profit_ratio": 0.75,      # 获利比例
                "avg_cost": 12.5,          # 平均成本
                "concentration_90": 0.15,  # 90%筹码集中度
                "concentration_70": 0.10,  # 70%筹码集中度
                "chip_status": "健康"      # 筹码状态
            }
        """
        # 注意: akshare 没有直接的筹码分布 API
        # 这里通过历史数据模拟计算
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
            df = MarketDataProvider.get_stock_hist(symbol, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            # 获取当前价格
            current_price = float(df.iloc[-1]['收盘'])
            
            # 计算加权平均成本（简化版）
            volumes = df['成交量'].values
            closes = df['收盘'].values
            total_volume = volumes.sum()
            
            if total_volume > 0:
                avg_cost = (volumes * closes).sum() / total_volume
            else:
                avg_cost = current_price
            
            # 计算获利比例（简化：当前价高于平均成本的天数占比）
            profit_days = len(df[df['收盘'] <= current_price])
            profit_ratio = profit_days / len(df) if len(df) > 0 else 0.5
            
            # 计算筹码集中度（简化：使用成交量标准差）
            volume_std = df['成交量'].std()
            volume_mean = df['成交量'].mean()
            concentration = volume_std / volume_mean if volume_mean > 0 else 0.5
            
            # 计算筹码状态
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
    
    @staticmethod
    def get_hist_with_ma(
        symbol: str,
        market: str = "CN-A",
        days: int = 60
    ) -> pd.DataFrame:
        """
        获取带均线的历史数据
        
        Args:
            symbol: 股票代码
            market: 市场类型 CN-A / US / HK
            days: 历史数据天数
            
        Returns:
            DataFrame with MA5, MA10, MA20, MA60 columns
        """
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
                # 美股需要交易所前缀，格式如 105.MSFT (纳斯达克) 或 106.XXX (纽交所)
                us_symbol = symbol if "." in symbol else f"105.{symbol}"
                try:
                    df = ak.stock_us_hist(
                        symbol=us_symbol,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                except Exception:
                    # 尝试纽交所前缀
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
            
            # 计算均线
            close_col = '收盘' if '收盘' in df.columns else 'close'
            df['MA5'] = df[close_col].rolling(window=5).mean()
            df['MA10'] = df[close_col].rolling(window=10).mean()
            df['MA20'] = df[close_col].rolling(window=20).mean()
            df['MA60'] = df[close_col].rolling(window=60).mean()
            
            # 只返回最近的数据
            return df.tail(days)
            
        except Exception as e:
            logger.error(f"获取带均线历史数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_us_stock_hist(
        symbol: str,
        days: int = 365
    ) -> pd.DataFrame:
        """
        获取美股历史数据
        
        Args:
            symbol: 美股代码（如 AAPL, NVDA, TSLA）
            days: 历史数据天数
            
        Returns:
            DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量
        """
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
    
    @staticmethod
    def get_hk_stock_hist(
        symbol: str,
        days: int = 365
    ) -> pd.DataFrame:
        """
        获取港股历史数据
        
        Args:
            symbol: 港股代码（如 00700, 09988）
            days: 历史数据天数
            
        Returns:
            DataFrame with columns: 日期, 开盘, 收盘, 最高, 最低, 成交量
        """
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

