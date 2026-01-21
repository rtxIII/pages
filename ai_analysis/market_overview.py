# coding=utf-8
"""
大盘复盘数据提供器

支持 A股、美股、港股 三个市场的市场全景数据获取
支持 akshare 和 yfinance 两种数据源，可通过配置切换
"""

import pandas as pd
from abc import ABC, abstractmethod
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


# ═══════════════════════════════════════════════════════════════
#                        抽象基类
# ═══════════════════════════════════════════════════════════════

class MarketOverviewProviderBase(ABC):
    """市场概览数据提供器抽象基类"""
    
    @abstractmethod
    def get_market_overview(self, market: str = "CN-A") -> MarketOverview:
        """获取市场概览"""
        pass


# ═══════════════════════════════════════════════════════════════
#                    Akshare 实现
# ═══════════════════════════════════════════════════════════════

class AkshareMarketOverviewProvider(MarketOverviewProviderBase):
    """大盘复盘数据提供器（基于 akshare）"""
    
    # A股主要指数代码
    A_INDICES = {
        "000001": "上证指数",
        "399001": "深证成指",
        "399006": "创业板指",
        "000688": "科创50",
        "000300": "沪深300",
    }
    
    def get_market_overview(self, market: str = "CN-A") -> MarketOverview:
        if market == "CN-A":
            return self._get_a_market_overview()
        elif market == "US":
            return self._get_us_market_overview()
        elif market == "HK":
            return self._get_hk_market_overview()
        else:
            raise ValueError(f"不支持的市场类型: {market}")
    
    def _get_a_market_overview(self) -> MarketOverview:
        """获取 A 股市场概览"""
        import akshare as ak
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="CN-A", date=today)
        
        try:
            # 1. 获取主要指数
            overview.indices = self._get_a_indices()
            
            # 2. 获取涨跌统计
            breadth = self._get_a_market_breadth()
            overview.up_count = breadth.get("up_count", 0)
            overview.down_count = breadth.get("down_count", 0)
            overview.flat_count = breadth.get("flat_count", 0)
            overview.limit_up_count = breadth.get("limit_up_count", 0)
            overview.limit_down_count = breadth.get("limit_down_count", 0)
            overview.total_amount = breadth.get("total_amount", 0)
            
            # 3. 获取北向资金
            overview.north_flow = self._get_north_flow()
            
            # 4. 获取板块涨跌
            sectors = self._get_a_sector_performance()
            overview.top_sectors = sectors.get("top", [])
            overview.bottom_sectors = sectors.get("bottom", [])
            
        except Exception as e:
            logger.error(f"获取 A 股市场概览失败: {e}")
        
        return overview
    
    def _get_a_indices(self) -> List[IndexData]:
        """获取 A 股主要指数"""
        import akshare as ak
        indices = []
        try:
            df = ak.stock_zh_index_spot_em()
            
            for code, name in self.A_INDICES.items():
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
    
    def _get_a_market_breadth(self) -> Dict:
        """获取 A 股涨跌家数统计"""
        import akshare as ak
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
            
            result["up_count"] = len(df[df['涨跌幅'] > 0])
            result["down_count"] = len(df[df['涨跌幅'] < 0])
            result["flat_count"] = len(df[df['涨跌幅'] == 0])
            result["limit_up_count"] = len(df[df['涨跌幅'] >= 9.9])
            result["limit_down_count"] = len(df[df['涨跌幅'] <= -9.9])
            
            if '成交额' in df.columns:
                result["total_amount"] = float(df['成交额'].sum()) / 1e8
                
        except Exception as e:
            logger.error(f"获取 A 股涨跌统计失败: {e}")
        
        return result
    
    def _get_north_flow(self) -> float:
        """获取北向资金净流入（亿元）"""
        import akshare as ak
        try:
            df = ak.stock_hsgt_fund_flow_summary_em()
            if not df.empty:
                north_df = df[df['资金方向'] == '北向']
                if not north_df.empty and '资金净流入' in north_df.columns:
                    return float(north_df['资金净流入'].sum()) / 1e8
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
        return 0.0
    
    def _get_a_sector_performance(self) -> Dict[str, List[SectorData]]:
        """获取 A 股板块涨跌排名"""
        import akshare as ak
        result = {"top": [], "bottom": []}
        
        try:
            df = ak.stock_board_industry_name_em()
            df_sorted = df.sort_values('涨跌幅', ascending=False)
            
            for _, row in df_sorted.head(5).iterrows():
                result["top"].append(SectorData(
                    name=row['板块名称'],
                    change_pct=float(row['涨跌幅']),
                    leader=row.get('领涨股票', '')
                ))
            
            for _, row in df_sorted.tail(5).iterrows():
                result["bottom"].append(SectorData(
                    name=row['板块名称'],
                    change_pct=float(row['涨跌幅']),
                    leader=row.get('领涨股票', '')
                ))
                
        except Exception as e:
            logger.error(f"获取 A 股板块涨跌失败: {e}")
        
        return result
    
    def _get_us_market_overview(self) -> MarketOverview:
        """获取美股市场概览"""
        import akshare as ak
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="US", date=today)
        
        try:
            # 获取主要指数
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
                    overview.indices.append(IndexData(
                        code=short_code,
                        name=name,
                        current=float(row['最新价']),
                        change=float(row['涨跌额']),
                        change_pct=float(row['涨跌幅'])
                    ))
            
            # 获取涨跌统计
            try:
                df = ak.stock_us_spot_em()
                if '涨跌幅' in df.columns:
                    overview.up_count = len(df[df['涨跌幅'] > 0])
                    overview.down_count = len(df[df['涨跌幅'] < 0])
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"获取美股市场概览失败: {e}")
        
        return overview
    
    def _get_hk_market_overview(self) -> MarketOverview:
        """获取港股市场概览"""
        import akshare as ak
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market="HK", date=today)
        
        try:
            # 获取主要指数
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
                    overview.indices.append(IndexData(
                        code=code,
                        name=name,
                        current=float(row['最新价']),
                        change=float(row['涨跌额']),
                        change_pct=float(row['涨跌幅'])
                    ))
            
            # 获取涨跌统计
            try:
                df = ak.stock_hk_spot_em()
                if '涨跌幅' in df.columns:
                    overview.up_count = len(df[df['涨跌幅'] > 0])
                    overview.down_count = len(df[df['涨跌幅'] < 0])
                if '成交额' in df.columns:
                    overview.total_amount = float(df['成交额'].sum()) / 1e8
            except Exception:
                pass
            
            # 获取南向资金
            try:
                df = ak.stock_hsgt_fund_flow_summary_em()
                if not df.empty:
                    south_df = df[df['资金方向'] == '南向']
                    if not south_df.empty and '资金净流入' in south_df.columns:
                        overview.south_flow = float(south_df['资金净流入'].sum()) / 1e8
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"获取港股市场概览失败: {e}")
        
        return overview


# ═══════════════════════════════════════════════════════════════
#                    YFinance 实现
# ═══════════════════════════════════════════════════════════════

class YFinanceMarketOverviewProvider(MarketOverviewProviderBase):
    """大盘复盘数据提供器（基于 yfinance）"""
    
    # 指数映射
    INDEX_MAPPING = {
        "CN-A": {
            "000001.SS": ("000001", "上证指数"),
            "399001.SZ": ("399001", "深证成指"),
            "399006.SZ": ("399006", "创业板指"),
        },
        "US": {
            "^DJI": ("DJIA", "道琼斯"),
            "^IXIC": ("NDX", "纳斯达克"),
            "^GSPC": ("SPX", "标普500"),
        },
        "HK": {
            "^HSI": ("HSI", "恒生指数"),
            "HSTECH.HK": ("HSTECH", "恒生科技"),
            "^HSCE": ("HSCEI", "国企指数"),
        }
    }
    
    def get_market_overview(self, market: str = "CN-A") -> MarketOverview:
        import yfinance as yf
        today = datetime.now().strftime("%Y-%m-%d")
        overview = MarketOverview(market=market, date=today)
        
        try:
            # 获取指数数据
            index_map = self.INDEX_MAPPING.get(market, {})
            
            for yf_symbol, (code, name) in index_map.items():
                try:
                    ticker = yf.Ticker(yf_symbol)
                    info = ticker.info
                    
                    if info and 'regularMarketPrice' in info:
                        overview.indices.append(IndexData(
                            code=code,
                            name=name,
                            current=float(info.get('regularMarketPrice', 0)),
                            change=float(info.get('regularMarketChange', 0)),
                            change_pct=float(info.get('regularMarketChangePercent', 0)),
                        ))
                except Exception as e:
                    logger.warning(f"获取指数 {yf_symbol} 失败: {e}")
            
            # yfinance 不支持涨跌家数统计，使用默认值
            # 用户需要知道这是 yfinance 的限制
            
        except Exception as e:
            logger.error(f"获取 {market} 市场概览失败: {e}")
        
        return overview


# ═══════════════════════════════════════════════════════════════
#                    工厂类
# ═══════════════════════════════════════════════════════════════

class MarketOverviewProvider:
    """
    市场概览数据提供器工厂
    
    根据配置返回对应的数据提供器实例
    """
    
    _providers = {
        "akshare": AkshareMarketOverviewProvider,
        "yfinance": YFinanceMarketOverviewProvider
    }
    
    _instance_cache: Dict[str, MarketOverviewProviderBase] = {}
    
    @classmethod
    def _get_config_source(cls) -> str:
        """从配置文件读取数据源设置"""
        try:
            import yaml
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent / "config" / "analysis.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    return config.get('ai_analysis', {}).get('data_source', 'akshare')
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
        
        return "akshare"
    
    @classmethod
    def get_provider(cls, source: str = None) -> MarketOverviewProviderBase:
        """获取数据提供器实例"""
        if source is None:
            source = cls._get_config_source()
        
        if source == "auto":
            source = "akshare"
        
        if source not in cls._providers:
            logger.warning(f"未知数据源 {source}，使用默认 akshare")
            source = "akshare"
        
        if source not in cls._instance_cache:
            cls._instance_cache[source] = cls._providers[source]()
        
        return cls._instance_cache[source]
    
    @classmethod
    def get_market_overview(cls, market: str = "CN-A") -> MarketOverview:
        """获取市场概览（兼容旧接口）"""
        return cls.get_provider().get_market_overview(market)
    
    # 兼容旧的类方法调用
    @classmethod
    def get_a_market_overview(cls) -> MarketOverview:
        return cls.get_provider().get_market_overview("CN-A")
    
    @classmethod
    def get_us_market_overview(cls) -> MarketOverview:
        return cls.get_provider().get_market_overview("US")
    
    @classmethod
    def get_hk_market_overview(cls) -> MarketOverview:
        return cls.get_provider().get_market_overview("HK")


# ═══════════════════════════════════════════════════════════════
#                    便捷函数
# ═══════════════════════════════════════════════════════════════

def get_market_overview(market: str = "CN-A") -> MarketOverview:
    """获取市场概览（便捷函数）"""
    return MarketOverviewProvider.get_market_overview(market)


def get_all_markets_overview() -> Dict[str, MarketOverview]:
    """获取所有市场概览"""
    return {
        "CN-A": MarketOverviewProvider.get_market_overview("CN-A"),
        "US": MarketOverviewProvider.get_market_overview("US"),
        "HK": MarketOverviewProvider.get_market_overview("HK"),
    }
