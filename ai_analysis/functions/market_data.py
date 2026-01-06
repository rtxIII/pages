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
            symbol: 股票代码（如 000001, 600000）
            market: 市场类型 CN-A(A股) / US(美股) / HK(港股)
            
        Returns:
            {
                "symbol": "000001",
                "name": "平安银行",
                "price": 12.34,
                "change": 0.12,
                "change_pct": 0.98,
                "volume": 1234567,
                "turnover": 9.8
            }
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
            market: 市场类型
            
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
            else:
                return []
        except Exception as e:
            logger.error(f"搜索股票失败 {keyword}: {e}")
            return []
