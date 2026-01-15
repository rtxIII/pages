# coding=utf-8
"""
===================================
A股自选股智能分析系统 - 远程存储后端
===================================

支持 S3 兼容协议的云存储（Cloudflare R2、阿里云 OSS、腾讯云 COS、AWS S3 等）
数据流程：下载远程 SQLite → 合并新数据 → 上传回远程
"""

import logging
import os
import sqlite3
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import pandas as pd

# boto3 可选导入
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None
    ClientError = Exception

from storage.base import StockStorageBackend, StockDaily

logger = logging.getLogger(__name__)


class RemoteStockStorage(StockStorageBackend):
    """
    远程云存储后端（S3 兼容协议）

    特点：
    - 使用 S3 兼容 API 访问远程存储
    - 支持 Cloudflare R2、阿里云 OSS、腾讯云 COS、AWS S3、MinIO 等
    - 数据流程：下载 → 本地操作 → 上传
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

    def __init__(
        self,
        bucket_name: str,
        access_key_id: str,
        secret_access_key: str,
        endpoint_url: str,
        region: str = "",
        remote_db_key: str = "stock/stock.db",
        temp_dir: Optional[str] = None,
    ):
        """
        初始化远程存储后端

        Args:
            bucket_name: 存储桶名称
            access_key_id: 访问密钥 ID
            secret_access_key: 访问密钥
            endpoint_url: 服务端点 URL
            region: 区域（某些服务需要）
            remote_db_key: 远程数据库文件的对象键
            temp_dir: 本地临时目录
        """
        if not HAS_BOTO3:
            raise ImportError("boto3 未安装，请运行: pip install boto3")

        self.bucket_name = bucket_name
        self.remote_db_key = remote_db_key
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "stock_storage"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 S3 客户端
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region or None,
        )

        self._connection: Optional[sqlite3.Connection] = None
        self._local_db_path: Optional[Path] = None
        self._db_modified = False

        logger.info(f"远程存储后端初始化完成: {endpoint_url}/{bucket_name}")

    @property
    def backend_name(self) -> str:
        return "remote_s3"

    def _get_local_db_path(self) -> Path:
        """获取本地临时数据库路径"""
        return self.temp_dir / "stock.db"

    def _check_object_exists(self, key: str) -> bool:
        """检查远程对象是否存在"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise

    def _download_database(self) -> bool:
        """
        从远程下载数据库文件

        Returns:
            是否下载成功（False 表示远程不存在，需要新建）
        """
        if not self._check_object_exists(self.remote_db_key):
            logger.info("远程数据库不存在，将创建新数据库")
            return False

        local_path = self._get_local_db_path()
        try:
            self.s3_client.download_file(
                Bucket=self.bucket_name,
                Key=self.remote_db_key,
                Filename=str(local_path)
            )
            logger.info(f"下载远程数据库成功: {self.remote_db_key}")
            return True
        except ClientError as e:
            logger.error(f"下载远程数据库失败: {e}")
            return False

    def _upload_database(self) -> bool:
        """
        上传本地数据库到远程

        Returns:
            是否上传成功
        """
        local_path = self._get_local_db_path()
        if not local_path.exists():
            logger.warning("本地数据库不存在，无法上传")
            return False

        try:
            self.s3_client.upload_file(
                Filename=str(local_path),
                Bucket=self.bucket_name,
                Key=self.remote_db_key
            )
            logger.info(f"上传数据库成功: {self.remote_db_key}")
            return True
        except ClientError as e:
            logger.error(f"上传数据库失败: {e}")
            return False

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接（自动下载远程数据库）"""
        if self._connection is None:
            # 尝试下载远程数据库
            self._download_database()

            local_path = self._get_local_db_path()
            self._local_db_path = local_path

            self._connection = sqlite3.connect(
                str(local_path),
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._connection.row_factory = sqlite3.Row

            # 初始化表结构
            cursor = self._connection.cursor()
            cursor.execute(self.CREATE_TABLE_SQL)
            cursor.execute(self.CREATE_INDEX_SQL)
            self._connection.commit()

        return self._connection

    def _sync_to_remote(self) -> bool:
        """同步本地更改到远程"""
        if self._db_modified and self._connection:
            self._connection.commit()
            result = self._upload_database()
            if result:
                self._db_modified = False
            return result
        return True

    def close(self) -> None:
        """关闭连接并同步到远程"""
        if self._connection:
            # 同步到远程
            self._sync_to_remote()

            self._connection.close()
            self._connection = None

            # 清理临时文件
            if self._local_db_path and self._local_db_path.exists():
                try:
                    self._local_db_path.unlink()
                except OSError:
                    pass

            logger.debug("远程存储连接已关闭")

    def __enter__(self) -> "RemoteStockStorage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # === 数据写入方法 ===

    def save_daily(self, data: StockDaily) -> bool:
        """保存单条日线数据"""
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
            self._db_modified = True
            return True
        except sqlite3.Error as e:
            logger.error(f"保存日线数据失败: {e}")
            return False

    def save_daily_batch(self, data_list: List[StockDaily]) -> int:
        """批量保存日线数据"""
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
            self._db_modified = True
            saved_count = cursor.rowcount
            logger.info(f"批量保存日线数据: {saved_count} 条")
            return saved_count
        except sqlite3.Error as e:
            logger.error(f"批量保存日线数据失败: {e}")
            return 0

    def save_from_dataframe(self, df: pd.DataFrame, code: str, data_source: str = "") -> int:
        """从 DataFrame 保存日线数据"""
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
        """查询日线数据"""
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
        """查询日线数据并返回 DataFrame"""
        data_list = self.get_daily(code, start_date, end_date)
        if not data_list:
            return pd.DataFrame()

        records = [asdict(d) for d in data_list]
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    def get_latest_date(self, code: str) -> Optional[str]:
        """获取指定股票的最新数据日期"""
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
        """获取数据库中所有股票代码"""
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
        """获取记录数量"""
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
        """删除指定股票的所有数据"""
        sql = "DELETE FROM stock_daily WHERE code = ?"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (code,))
            conn.commit()
            self._db_modified = True
            deleted_count = cursor.rowcount
            logger.info(f"删除股票 {code} 数据: {deleted_count} 条")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"删除数据失败: {e}")
            return 0

    def delete_before_date(self, date_str: str) -> int:
        """删除指定日期之前的所有数据"""
        sql = "DELETE FROM stock_daily WHERE date < ?"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, (date_str,))
            conn.commit()
            self._db_modified = True
            deleted_count = cursor.rowcount
            logger.info(f"删除 {date_str} 之前的数据: {deleted_count} 条")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"删除数据失败: {e}")
            return 0

    # === 远程特有方法 ===

    def sync(self) -> bool:
        """手动同步到远程"""
        return self._sync_to_remote()

    def pull(self) -> bool:
        """
        从远程拉取最新数据（覆盖本地）

        Returns:
            是否拉取成功
        """
        if self._connection:
            self._connection.close()
            self._connection = None

        return self._download_database()
