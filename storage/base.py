# coding=utf-8
"""
===================================
A股自选股智能分析系统 - 存储后端抽象基类
===================================

定义统一的存储接口，所有存储后端都需要实现这些方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd


@dataclass
class StockDaily:
    """
    股票日线数据模型

    对应 schema.sql 中的 stock_daily 表
    """

    code: str                           # 股票代码
    date: str                           # 日期 (YYYY-MM-DD)
    open: Optional[float] = None        # 开盘价
    high: Optional[float] = None        # 最高价
    low: Optional[float] = None         # 最低价
    close: Optional[float] = None       # 收盘价
    volume: Optional[float] = None      # 成交量
    amount: Optional[float] = None      # 成交额
    pct_chg: Optional[float] = None     # 涨跌幅
    ma5: Optional[float] = None         # 5日均线
    ma10: Optional[float] = None        # 10日均线
    ma20: Optional[float] = None        # 20日均线
    volume_ratio: Optional[float] = None  # 量比
    data_source: Optional[str] = None   # 数据来源
    id: Optional[int] = None            # 主键ID（数据库自动生成）
    created_at: Optional[str] = None    # 创建时间
    updated_at: Optional[str] = None    # 更新时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（排除自动生成字段，保留 None 值供 SQL 绑定）"""
        result = {}
        for key, value in asdict(self).items():
            if key not in ('id', 'created_at', 'updated_at'):
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockDaily":
        """从字典创建"""
        return cls(
            code=data.get("code", ""),
            date=data.get("date", ""),
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            close=data.get("close"),
            volume=data.get("volume"),
            amount=data.get("amount"),
            pct_chg=data.get("pct_chg"),
            ma5=data.get("ma5"),
            ma10=data.get("ma10"),
            ma20=data.get("ma20"),
            volume_ratio=data.get("volume_ratio"),
            data_source=data.get("data_source"),
            id=data.get("id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_dataframe_row(cls, row: pd.Series, code: str, data_source: str = "") -> "StockDaily":
        """从 DataFrame 行创建"""
        return cls(
            code=code,
            date=str(row.get("date", row.name))[:10],
            open=row.get("open"),
            high=row.get("high"),
            low=row.get("low"),
            close=row.get("close"),
            volume=row.get("volume"),
            amount=row.get("amount"),
            pct_chg=row.get("pct_chg"),
            ma5=row.get("ma5"),
            ma10=row.get("ma10"),
            ma20=row.get("ma20"),
            volume_ratio=row.get("volume_ratio"),
            data_source=data_source,
        )


class StockStorageBackend(ABC):
    """
    股票存储后端抽象基类

    所有存储后端都需要实现这些方法，以支持:
    - 保存日线数据
    - 查询日线数据
    - 断点续传（获取最新日期）
    - 数据清理
    """

    # === 数据写入方法 ===

    @abstractmethod
    def save_daily(self, data: StockDaily) -> bool:
        """
        保存单条日线数据（UPSERT 模式）

        Args:
            data: 股票日线数据

        Returns:
            是否保存成功
        """
        pass

    @abstractmethod
    def save_daily_batch(self, data_list: List[StockDaily]) -> int:
        """
        批量保存日线数据

        Args:
            data_list: 股票日线数据列表

        Returns:
            成功保存的记录数
        """
        pass

    @abstractmethod
    def save_from_dataframe(self, df: pd.DataFrame, code: str, data_source: str = "") -> int:
        """
        从 DataFrame 保存日线数据

        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源

        Returns:
            成功保存的记录数
        """
        pass

    # === 数据查询方法 ===

    @abstractmethod
    def get_daily(self, code: str, start_date: str, end_date: str) -> List[StockDaily]:
        """
        查询日线数据

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            日线数据列表
        """
        pass

    @abstractmethod
    def get_daily_as_dataframe(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        查询日线数据并返回 DataFrame

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            包含日线数据的 DataFrame
        """
        pass

    @abstractmethod
    def get_latest_date(self, code: str) -> Optional[str]:
        """
        获取指定股票的最新数据日期

        用于断点续传：确定从哪个日期开始获取新数据

        Args:
            code: 股票代码

        Returns:
            最新日期字符串 (YYYY-MM-DD)，无数据时返回 None
        """
        pass

    @abstractmethod
    def get_stock_codes(self) -> List[str]:
        """
        获取数据库中所有股票代码

        Returns:
            股票代码列表
        """
        pass

    @abstractmethod
    def get_record_count(self, code: Optional[str] = None) -> int:
        """
        获取记录数量

        Args:
            code: 股票代码（可选，不指定则统计全部）

        Returns:
            记录数量
        """
        pass

    # === 数据删除方法 ===

    @abstractmethod
    def delete_by_code(self, code: str) -> int:
        """
        删除指定股票的所有数据

        Args:
            code: 股票代码

        Returns:
            删除的记录数
        """
        pass

    @abstractmethod
    def delete_before_date(self, date_str: str) -> int:
        """
        删除指定日期之前的所有数据

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            删除的记录数
        """
        pass

    # === 资源管理方法 ===

    @abstractmethod
    def close(self) -> None:
        """关闭存储连接"""
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """存储后端名称"""
        pass


def convert_dataframe_to_stock_daily_list(
    df: pd.DataFrame,
    code: str,
    data_source: str = ""
) -> List[StockDaily]:
    """
    将 DataFrame 转换为 StockDaily 列表

    Args:
        df: 包含日线数据的 DataFrame
        code: 股票代码
        data_source: 数据来源

    Returns:
        StockDaily 列表
    """
    if df.empty:
        return []

    data_list = []
    for _, row in df.iterrows():
        stock_daily = StockDaily.from_dataframe_row(row, code, data_source)
        data_list.append(stock_daily)

    return data_list


def convert_stock_daily_list_to_dataframe(data_list: List[StockDaily]) -> pd.DataFrame:
    """
    将 StockDaily 列表转换为 DataFrame

    Args:
        data_list: StockDaily 列表

    Returns:
        包含日线数据的 DataFrame
    """
    if not data_list:
        return pd.DataFrame()

    records = [asdict(d) for d in data_list]
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df
