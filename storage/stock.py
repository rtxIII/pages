# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 股票数据存储层
===================================

职责：
1. 实现 StockStorageBackend 抽象基类
2. 管理 SQLite 数据库连接
3. 提供数据存取接口
4. 实现智能更新逻辑（断点续传）
"""

import logging
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import Optional, List
from pathlib import Path

import pandas as pd

from storage.base import StockStorageBackend, StockDaily

logger = logging.getLogger(__name__)


class StockStorage(StockStorageBackend):
    """
    股票数据 SQLite 存储实现

    功能：
    - 初始化数据库表
    - 保存/查询日线数据
    - 批量操作支持
    - 断点续传（智能更新）
    """

    # 表结构 SQL（与 schema.sql 保持一致）
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS stock_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        date DATE NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        amount REAL,
        pct_chg REAL,
        ma5 REAL,
        ma10 REAL,
        ma20 REAL,
        volume_ratio REAL,
        data_source TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(code, date)
    )
    """

    CREATE_INDEX_SQL = """
    CREATE INDEX IF NOT EXISTS ix_code_date ON stock_daily(code, date)
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化存储管理器

        Args:
            db_path: 数据库文件路径，默认为 data/stock.db
        """
        if db_path is None:
            db_path = "data/stock.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection: Optional[sqlite3.Connection] = None
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（单例模式）"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.db_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _init_database(self) -> None:
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(self.CREATE_TABLE_SQL)
        cursor.execute(self.CREATE_INDEX_SQL)

        conn.commit()
        logger.info(f"数据库初始化完成: {self.db_path}")

    def close(self) -> None:
        """关闭数据库连接"""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.debug("数据库连接已关闭")

    def __enter__(self) -> "StockStorage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def backend_name(self) -> str:
        """存储后端名称"""
        return "sqlite"

    # === 数据写入方法 ===

    def save_daily(self, data: StockDaily) -> bool:
        """
        保存单条日线数据（UPSERT 模式）

        Args:
            data: 股票日线数据

        Returns:
            是否保存成功
        """
        sql = """
        INSERT INTO stock_daily (code, date, open, high, low, close, volume, amount,
                                  pct_chg, ma5, ma10, ma20, volume_ratio, data_source)
        VALUES (:code, :date, :open, :high, :low, :close, :volume, :amount,
                :pct_chg, :ma5, :ma10, :ma20, :volume_ratio, :data_source)
        ON CONFLICT(code, date) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            volume = excluded.volume,
            amount = excluded.amount,
            pct_chg = excluded.pct_chg,
            ma5 = excluded.ma5,
            ma10 = excluded.ma10,
            ma20 = excluded.ma20,
            volume_ratio = excluded.volume_ratio,
            data_source = excluded.data_source,
            updated_at = CURRENT_TIMESTAMP
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, data.to_dict())
            conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"保存日线数据失败: {e}")
            return False

    def save_daily_batch(self, data_list: List[StockDaily]) -> int:
        """
        批量保存日线数据

        Args:
            data_list: 股票日线数据列表

        Returns:
            成功保存的记录数
        """
        if not data_list:
            return 0

        sql = """
        INSERT INTO stock_daily (code, date, open, high, low, close, volume, amount,
                                  pct_chg, ma5, ma10, ma20, volume_ratio, data_source)
        VALUES (:code, :date, :open, :high, :low, :close, :volume, :amount,
                :pct_chg, :ma5, :ma10, :ma20, :volume_ratio, :data_source)
        ON CONFLICT(code, date) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            volume = excluded.volume,
            amount = excluded.amount,
            pct_chg = excluded.pct_chg,
            ma5 = excluded.ma5,
            ma10 = excluded.ma10,
            ma20 = excluded.ma20,
            volume_ratio = excluded.volume_ratio,
            data_source = excluded.data_source,
            updated_at = CURRENT_TIMESTAMP
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.executemany(sql, [d.to_dict() for d in data_list])
            conn.commit()
            saved_count = cursor.rowcount
            logger.info(f"批量保存日线数据: {saved_count} 条")
            return saved_count
        except sqlite3.Error as e:
            logger.error(f"批量保存日线数据失败: {e}")
            return 0

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
        if df.empty:
            return 0

        data_list = []
        for _, row in df.iterrows():
            stock_daily = StockDaily(
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
            data_list.append(stock_daily)

        return self.save_daily_batch(data_list)

    # === 数据查询方法 ===

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
        sql = """
        SELECT * FROM stock_daily
        WHERE code = ? AND date BETWEEN ? AND ?
        ORDER BY date ASC
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (code, start_date, end_date))
            rows = cursor.fetchall()
            return [StockDaily.from_dict(dict(row)) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"查询日线数据失败: {e}")
            return []

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
        data_list = self.get_daily(code, start_date, end_date)
        if not data_list:
            return pd.DataFrame()

        records = [asdict(d) for d in data_list]
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    def get_latest_date(self, code: str) -> Optional[str]:
        """
        获取指定股票的最新数据日期

        用于断点续传：确定从哪个日期开始获取新数据

        Args:
            code: 股票代码

        Returns:
            最新日期字符串 (YYYY-MM-DD)，无数据时返回 None
        """
        sql = "SELECT MAX(date) as latest_date FROM stock_daily WHERE code = ?"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (code,))
            row = cursor.fetchone()
            return row["latest_date"] if row and row["latest_date"] else None
        except sqlite3.Error as e:
            logger.error(f"获取最新日期失败: {e}")
            return None

    def get_stock_codes(self) -> List[str]:
        """
        获取数据库中所有股票代码

        Returns:
            股票代码列表
        """
        sql = "SELECT DISTINCT code FROM stock_daily ORDER BY code"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [row["code"] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"获取股票代码列表失败: {e}")
            return []

    def get_record_count(self, code: Optional[str] = None) -> int:
        """
        获取记录数量

        Args:
            code: 股票代码（可选，不指定则统计全部）

        Returns:
            记录数量
        """
        if code:
            sql = "SELECT COUNT(*) as cnt FROM stock_daily WHERE code = ?"
            params = (code,)
        else:
            sql = "SELECT COUNT(*) as cnt FROM stock_daily"
            params = ()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        except sqlite3.Error as e:
            logger.error(f"获取记录数量失败: {e}")
            return 0

    # === 数据删除方法 ===

    def delete_by_code(self, code: str) -> int:
        """
        删除指定股票的所有数据

        Args:
            code: 股票代码

        Returns:
            删除的记录数
        """
        sql = "DELETE FROM stock_daily WHERE code = ?"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (code,))
            conn.commit()
            deleted_count = cursor.rowcount
            logger.info(f"删除股票 {code} 数据: {deleted_count} 条")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"删除数据失败: {e}")
            return 0

    def delete_before_date(self, date_str: str) -> int:
        """
        删除指定日期之前的所有数据

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            删除的记录数
        """
        sql = "DELETE FROM stock_daily WHERE date < ?"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (date_str,))
            conn.commit()
            deleted_count = cursor.rowcount
            logger.info(f"删除 {date_str} 之前的数据: {deleted_count} 条")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"删除数据失败: {e}")
            return 0


# === 模块级便捷函数 ===

_default_storage: Optional[StockStorage] = None


def get_stock_storage() -> StockStorage:
    """获取默认的股票存储管理器（单例模式）"""
    global _default_storage
    if _default_storage is None:
        _default_storage = StockStorage()
    return _default_storage


def close_stock_storage() -> None:
    """关闭默认的股票存储管理器"""
    global _default_storage
    if _default_storage is not None:
        _default_storage.close()
        _default_storage = None
