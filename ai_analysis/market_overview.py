# coding=utf-8
"""
大盘复盘数据提供器

支持 A股、美股、港股 三个市场的市场全景数据获取
参考: ZhuLinsen/daily_stock_analysis
"""

import akshare as ak
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class IndexData:
    """指数数据模型"""
    code: str           # 指数代码
    name: str           # 指数名称
    current: float      # 当前点位
    change: float       # 涨跌额
    change_pct: float   # 涨跌幅(%)
    volume: float = 0   # 成交量
    amount: float = 0   # 成交额(亿)


@dataclass
class SectorData:
    """板块数据模型"""
    name: str           # 板块名称
    change_pct: float   # 涨跌幅(%)
    leader: str = ""    # 领涨股


@dataclass
class MarketOverview:
    """大盘复盘数据模型"""
    market: str                         # 市场类型: CN-A / US / HK
    date: str                           # 日期 YYYY-MM-DD
    indices: List[IndexData] = field(default_factory=list)  # 主要指数
    up_count: int = 0                   # 上涨家数
    down_count: int = 0                 # 下跌家数
    flat_count: int = 0                 # 平盘家数
    limit_up_count: int = 0             # 涨停家数（A股特有）
    limit_down_count: int = 0           # 跌停家数（A股特有）
    total_amount: float = 0             # 成交额（亿）
    north_flow: float = 0               # 北向资金（A股特有，亿）
    south_flow: float = 0               # 南向资金（港股特有，亿）
    top_sectors: List[SectorData] = field(default_factory=list)     # 领涨板块
    bottom_sectors: List[SectorData] = field(default_factory=list)  # 领跌板块


class MarketOverviewProvider:
    """
    大盘复盘数据提供器（多市场）
    
    支持:
    - CN-A: A股市场
    - US: 美股市场
    - HK: 港股市场
    """
    
    # A股主要指数代码
    A_INDICES = {
        "000001": "上证指数",
        "399001": "深证成指",
        "399006": "创业板指",
        "000688": "科创50",
        "000300": "沪深300",
    }
    
    # 美股主要指数
    US_INDICES = {
        "DJIA": "道琼斯",
        "NDX": "纳斯达克",
        "SPX": "标普500",
    }
    
    # 港股主要指数
    HK_INDICES = {
        "HSI": "恒生指数",
        "HSTECH": "恒生科技",
    }
    
    @classmethod
    def get_market_overview(cls, market: str = "CN-A") -> MarketOverview:
        """
        获取市场概览
        
        Args:
            market: 市场类型 CN-A / US / HK
            
        Returns:
            MarketOverview 对象
        """
        if market == "CN-A":
            return cls.get_a_market_overview()
        elif market == "US":
            return cls.get_us_market_overview()
        elif market == "HK":
            return cls.get_hk_market_overview()
        else:
            raise ValueError(f"不支持的市场类型: {market}")
    
    # ==================== A 股 ====================
    
    @classmethod
    def get_a_market_overview(cls) -> MarketOverview:
        """获取 A 股市场概览"""
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="CN-A", date=today)
        
        try:
            # 1. 获取主要指数
            overview.indices = cls._get_a_indices()
            
            # 2. 获取涨跌统计
            breadth = cls._get_a_market_breadth()
            overview.up_count = breadth.get("up_count", 0)
            overview.down_count = breadth.get("down_count", 0)
            overview.flat_count = breadth.get("flat_count", 0)
            overview.limit_up_count = breadth.get("limit_up_count", 0)
            overview.limit_down_count = breadth.get("limit_down_count", 0)
            overview.total_amount = breadth.get("total_amount", 0)
            
            # 3. 获取北向资金
            overview.north_flow = cls.get_north_flow()
            
            # 4. 获取板块涨跌
            sectors = cls.get_a_sector_performance()
            overview.top_sectors = sectors.get("top", [])
            overview.bottom_sectors = sectors.get("bottom", [])
            
        except Exception as e:
            logger.error(f"获取 A 股市场概览失败: {e}")
        
        return overview
    
    @classmethod
    def _get_a_indices(cls) -> List[IndexData]:
        """获取 A 股主要指数"""
        indices = []
        try:
            df = ak.stock_zh_index_spot_em()
            
            for code, name in cls.A_INDICES.items():
                row = df[df['代码'] == code]
                if not row.empty:
                    row = row.iloc[0]
                    indices.append(IndexData(
                        code=code,
                        name=name,
                        current=float(row['最新价']),
                        change=float(row['涨跌额']),
                        change_pct=float(row['涨跌幅']),
                        amount=float(row['成交额']) / 1e8 if '成交额' in row else 0
                    ))
        except Exception as e:
            logger.error(f"获取 A 股指数失败: {e}")
        
        return indices
    
    @classmethod
    def _get_a_market_breadth(cls) -> Dict:
        """获取 A 股涨跌家数统计"""
        result = {
            "up_count": 0,
            "down_count": 0,
            "flat_count": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
            "total_amount": 0
        }
        
        try:
            df = ak.stock_zh_a_spot_em()
            
            # 涨跌统计
            result["up_count"] = len(df[df['涨跌幅'] > 0])
            result["down_count"] = len(df[df['涨跌幅'] < 0])
            result["flat_count"] = len(df[df['涨跌幅'] == 0])
            
            # 涨跌停统计（涨跌幅接近 10% 或 20%）
            result["limit_up_count"] = len(df[df['涨跌幅'] >= 9.9])
            result["limit_down_count"] = len(df[df['涨跌幅'] <= -9.9])
            
            # 总成交额
            if '成交额' in df.columns:
                result["total_amount"] = float(df['成交额'].sum()) / 1e8
                
        except Exception as e:
            logger.error(f"获取 A 股涨跌统计失败: {e}")
        
        return result
    
    @classmethod
    def get_north_flow(cls) -> float:
        """获取北向资金净流入（亿元）"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            if not df.empty:
                # 筛选北向资金（沪股通 + 深股通）
                north_df = df[df['资金方向'] == '北向']
                if not north_df.empty and '资金净流入' in north_df.columns:
                    return float(north_df['资金净流入'].sum()) / 1e8
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
        return 0.0
    
    @classmethod
    def get_a_sector_performance(cls) -> Dict[str, List[SectorData]]:
        """获取 A 股板块涨跌排名"""
        result = {"top": [], "bottom": []}
        
        try:
            df = ak.stock_board_industry_name_em()
            
            # 按涨跌幅排序
            df_sorted = df.sort_values('涨跌幅', ascending=False)
            
            # 领涨板块（前5）
            for _, row in df_sorted.head(5).iterrows():
                result["top"].append(SectorData(
                    name=row['板块名称'],
                    change_pct=float(row['涨跌幅']),
                    leader=row.get('领涨股票', '')
                ))
            
            # 领跌板块（后5）
            for _, row in df_sorted.tail(5).iterrows():
                result["bottom"].append(SectorData(
                    name=row['板块名称'],
                    change_pct=float(row['涨跌幅']),
                    leader=row.get('领涨股票', '')
                ))
                
        except Exception as e:
            logger.error(f"获取 A 股板块涨跌失败: {e}")
        
        return result
    
    # ==================== 美股 ====================
    
    @classmethod
    def get_us_market_overview(cls) -> MarketOverview:
        """获取美股市场概览"""
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="US", date=today)
        
        try:
            # 1. 获取主要指数
            overview.indices = cls._get_us_indices()
            
            # 2. 获取涨跌统计
            breadth = cls._get_us_market_breadth()
            overview.up_count = breadth.get("up_count", 0)
            overview.down_count = breadth.get("down_count", 0)
            overview.total_amount = breadth.get("total_amount", 0)
            
            # 3. 获取板块涨跌（暂不实现）
            # overview.top_sectors = ...
            
        except Exception as e:
            logger.error(f"获取美股市场概览失败: {e}")
        
        return overview
    
    @classmethod
    def _get_us_indices(cls) -> List[IndexData]:
        """获取美股主要指数"""
        indices = []
        try:
            # 使用新浪接口获取美股指数
            df = ak.index_us_stock_sina()
            
            index_mapping = {
                ".DJI": ("DJIA", "道琼斯"),
                ".IXIC": ("NDX", "纳斯达克"),
                ".INX": ("SPX", "标普500"),
            }
            
            for code, (short_code, name) in index_mapping.items():
                row = df[df['代码'] == code]
                if not row.empty:
                    row = row.iloc[0]
                    indices.append(IndexData(
                        code=short_code,
                        name=name,
                        current=float(row['最新价']),
                        change=float(row['涨跌额']),
                        change_pct=float(row['涨跌幅'])
                    ))
        except Exception as e:
            logger.error(f"获取美股指数失败: {e}")
        
        return indices
    
    @classmethod
    def _get_us_market_breadth(cls) -> Dict:
        """获取美股涨跌统计"""
        result = {
            "up_count": 0,
            "down_count": 0,
            "total_amount": 0
        }
        
        try:
            df = ak.stock_us_spot_em()
            
            if '涨跌幅' in df.columns:
                result["up_count"] = len(df[df['涨跌幅'] > 0])
                result["down_count"] = len(df[df['涨跌幅'] < 0])
                
        except Exception as e:
            logger.error(f"获取美股涨跌统计失败: {e}")
        
        return result
    
    # ==================== 港股 ====================
    
    @classmethod
    def get_hk_market_overview(cls) -> MarketOverview:
        """获取港股市场概览"""
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="HK", date=today)
        
        try:
            # 1. 获取主要指数
            overview.indices = cls._get_hk_indices()
            
            # 2. 获取涨跌统计
            breadth = cls._get_hk_market_breadth()
            overview.up_count = breadth.get("up_count", 0)
            overview.down_count = breadth.get("down_count", 0)
            overview.total_amount = breadth.get("total_amount", 0)
            
            # 3. 获取南向资金
            overview.south_flow = cls.get_south_flow()
            
        except Exception as e:
            logger.error(f"获取港股市场概览失败: {e}")
        
        return overview
    
    @classmethod
    def _get_hk_indices(cls) -> List[IndexData]:
        """获取港股主要指数"""
        indices = []
        try:
            df = ak.stock_hk_index_spot_em()
            
            index_mapping = {
                "恒生指数": "HSI",
                "恒生科技指数": "HSTECH",
                "国企指数": "HSCEI",
            }
            
            for name, code in index_mapping.items():
                row = df[df['名称'].str.contains(name, na=False)]
                if not row.empty:
                    row = row.iloc[0]
                    indices.append(IndexData(
                        code=code,
                        name=name,
                        current=float(row['最新价']),
                        change=float(row['涨跌额']),
                        change_pct=float(row['涨跌幅'])
                    ))
        except Exception as e:
            logger.error(f"获取港股指数失败: {e}")
        
        return indices
    
    @classmethod
    def _get_hk_market_breadth(cls) -> Dict:
        """获取港股涨跌统计"""
        result = {
            "up_count": 0,
            "down_count": 0,
            "total_amount": 0
        }
        
        try:
            df = ak.stock_hk_spot_em()
            
            if '涨跌幅' in df.columns:
                result["up_count"] = len(df[df['涨跌幅'] > 0])
                result["down_count"] = len(df[df['涨跌幅'] < 0])
            
            if '成交额' in df.columns:
                result["total_amount"] = float(df['成交额'].sum()) / 1e8
                
        except Exception as e:
            logger.error(f"获取港股涨跌统计失败: {e}")
        
        return result
    
    @classmethod
    def get_south_flow(cls) -> float:
        """获取南向资金净流入（亿港元）"""
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            if not df.empty:
                # 筛选南向资金（港股通）
                south_df = df[df['资金方向'] == '南向']
                if not south_df.empty and '资金净流入' in south_df.columns:
                    return float(south_df['资金净流入'].sum()) / 1e8
        except Exception as e:
            logger.error(f"获取南向资金失败: {e}")
        return 0.0


# ==================== 便捷函数 ====================

def get_market_overview(market: str = "CN-A") -> MarketOverview:
    """获取市场概览（便捷函数）"""
    return MarketOverviewProvider.get_market_overview(market)


def get_all_markets_overview() -> Dict[str, MarketOverview]:
    """获取所有市场概览"""
    return {
        "CN-A": MarketOverviewProvider.get_a_market_overview(),
        "US": MarketOverviewProvider.get_us_market_overview(),
        "HK": MarketOverviewProvider.get_hk_market_overview(),
    }
