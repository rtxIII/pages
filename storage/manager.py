# coding=utf-8
"""
===================================
A股自选股智能分析系统 - 存储管理器
===================================

统一管理存储后端，支持本地/远程存储切换
"""

import os
import logging
from typing import Optional, List

import pandas as pd

from storage.base import StockStorageBackend, StockDaily

logger = logging.getLogger(__name__)

# 存储管理器单例
_storage_manager: Optional["StockStorageManager"] = None


class StockStorageManager:
    """
    股票数据存储管理器

    功能：
    - 自动检测运行环境（GitHub Actions / Docker / 本地）
    - 根据配置选择存储后端（local / remote / auto）
    - 提供统一的存储接口
    """

    def __init__(
        self,
        backend_type: str = "local",
        db_path: Optional[str] = None,
        remote_config: Optional[dict] = None,
        retention_days: int = 0,
    ):
        """
        初始化存储管理器

        Args:
            backend_type: 存储后端类型 (local / remote / auto)
            db_path: 本地数据库路径
            remote_config: 远程存储配置，包含：
                - bucket_name: 存储桶名称
                - access_key_id: 访问密钥 ID
                - secret_access_key: 访问密钥
                - endpoint_url: 服务端点 URL
                - region: 区域（可选）
                - remote_db_key: 远程数据库对象键（可选，默认 stock/stock.db）
            retention_days: 数据保留天数（0 = 无限制）
        """
        self.backend_type = backend_type
        self.db_path = db_path
        self.remote_config = remote_config or {}
        self.retention_days = retention_days

        self._backend: Optional[StockStorageBackend] = None

    @staticmethod
    def is_github_actions() -> bool:
        """检测是否在 GitHub Actions 环境中运行"""
        return os.environ.get("GITHUB_ACTIONS") == "true"

    @staticmethod
    def is_docker() -> bool:
        """检测是否在 Docker 容器中运行"""
        if os.path.exists("/.dockerenv"):
            return True

        try:
            with open("/proc/1/cgroup", "r") as f:
                return "docker" in f.read()
        except (FileNotFoundError, PermissionError):
            pass

        return os.environ.get("DOCKER_CONTAINER") == "true"

    def _resolve_backend_type(self) -> str:
        """解析实际使用的后端类型"""
        if self.backend_type == "auto":
            if self.is_github_actions() and self._has_remote_config():
                return "remote"
            return "local"
        return self.backend_type

    def _has_remote_config(self) -> bool:
        """检查是否有有效的远程存储配置"""
        bucket_name = self.remote_config.get("bucket_name") or os.environ.get("S3_BUCKET_NAME")
        access_key = self.remote_config.get("access_key_id") or os.environ.get("S3_ACCESS_KEY_ID")
        secret_key = self.remote_config.get("secret_access_key") or os.environ.get("S3_SECRET_ACCESS_KEY")
        endpoint = self.remote_config.get("endpoint_url") or os.environ.get("S3_ENDPOINT_URL")

        has_config = bool(bucket_name and access_key and secret_key and endpoint)

        if not has_config:
            logger.debug(f"远程存储配置不完整: bucket={bool(bucket_name)}, key={bool(access_key)}, secret={bool(secret_key)}, endpoint={bool(endpoint)}")

        return has_config

    def _create_remote_backend(self) -> Optional[StockStorageBackend]:
        """创建远程存储后端"""
        try:
            from storage.remote import RemoteStockStorage

            return RemoteStockStorage(
                bucket_name=self.remote_config.get("bucket_name") or os.environ.get("S3_BUCKET_NAME", ""),
                access_key_id=self.remote_config.get("access_key_id") or os.environ.get("S3_ACCESS_KEY_ID", ""),
                secret_access_key=self.remote_config.get("secret_access_key") or os.environ.get("S3_SECRET_ACCESS_KEY", ""),
                endpoint_url=self.remote_config.get("endpoint_url") or os.environ.get("S3_ENDPOINT_URL", ""),
                region=self.remote_config.get("region") or os.environ.get("S3_REGION", ""),
                remote_db_key=self.remote_config.get("remote_db_key", "stock/stock.db"),
            )
        except ImportError as e:
            logger.error(f"远程后端导入失败: {e}")
            logger.error("请确保已安装 boto3: pip install boto3")
            return None
        except Exception as e:
            logger.error(f"远程后端初始化失败: {e}")
            return None

    def get_backend(self) -> StockStorageBackend:
        """获取存储后端实例"""
        if self._backend is None:
            resolved_type = self._resolve_backend_type()

            if resolved_type == "remote":
                self._backend = self._create_remote_backend()
                if self._backend:
                    logger.info("使用远程存储后端 (S3)")
                else:
                    logger.warning("远程后端创建失败，回退到本地存储")
                    resolved_type = "local"

            if resolved_type == "local" or self._backend is None:
                from storage.stock import StockStorage
                self._backend = StockStorage(db_path=self.db_path)
                logger.info(f"使用本地 SQLite 存储后端")

        return self._backend

    # === 数据写入方法 ===

    def save_daily(self, data: StockDaily) -> bool:
        """保存单条日线数据"""
        return self.get_backend().save_daily(data)

    def save_daily_batch(self, data_list: List[StockDaily]) -> int:
        """批量保存日线数据"""
        return self.get_backend().save_daily_batch(data_list)

    def save_from_dataframe(self, df: pd.DataFrame, code: str, data_source: str = "") -> int:
        """从 DataFrame 保存日线数据"""
        return self.get_backend().save_from_dataframe(df, code, data_source)

    # === 数据查询方法 ===

    def get_daily(self, code: str, start_date: str, end_date: str) -> List[StockDaily]:
        """查询日线数据"""
        return self.get_backend().get_daily(code, start_date, end_date)

    def get_daily_as_dataframe(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """查询日线数据并返回 DataFrame"""
        return self.get_backend().get_daily_as_dataframe(code, start_date, end_date)

    def get_latest_date(self, code: str) -> Optional[str]:
        """获取指定股票的最新数据日期"""
        return self.get_backend().get_latest_date(code)

    def get_stock_codes(self) -> List[str]:
        """获取数据库中所有股票代码"""
        return self.get_backend().get_stock_codes()

    def get_record_count(self, code: Optional[str] = None) -> int:
        """获取记录数量"""
        return self.get_backend().get_record_count(code)

    def has_today_data(self, code: str, check_date: Optional["date"] = None) -> bool:
        """
        检查指定股票是否有今日数据
        
        Args:
            code: 股票代码
            check_date: 检查日期（可选，默认今日）
            
        Returns:
            是否有数据
        """
        from datetime import date as date_type
        target_date = check_date or date_type.today()
        latest = self.get_latest_date(code)
        if latest is None:
            return False
        return latest == target_date.strftime("%Y-%m-%d")

    # === 数据删除方法 ===

    def delete_by_code(self, code: str) -> int:
        """删除指定股票的所有数据"""
        return self.get_backend().delete_by_code(code)

    def delete_before_date(self, date_str: str) -> int:
        """删除指定日期之前的所有数据"""
        return self.get_backend().delete_before_date(date_str)

    # === 资源管理方法 ===

    def sync(self) -> bool:
        """
        同步数据到远程（仅远程后端有效）

        Returns:
            是否同步成功
        """
        backend = self.get_backend()
        if hasattr(backend, 'sync'):
            return backend.sync()
        return True

    def close(self) -> None:
        """关闭存储后端"""
        if self._backend:
            self._backend.close()
            self._backend = None

    def __enter__(self) -> "StockStorageManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def backend_name(self) -> str:
        """获取当前后端名称"""
        return self.get_backend().backend_name


def get_stock_storage_manager(
    backend_type: str = "local",
    db_path: Optional[str] = None,
    remote_config: Optional[dict] = None,
    retention_days: int = 0,
    force_new: bool = False,
) -> StockStorageManager:
    """
    获取存储管理器单例

    Args:
        backend_type: 存储后端类型 (local / remote / auto)
        db_path: 本地数据库路径
        remote_config: 远程存储配置
        retention_days: 数据保留天数（0 = 无限制）
        force_new: 是否强制创建新实例

    Returns:
        StockStorageManager 实例
    """
    global _storage_manager

    if _storage_manager is None or force_new:
        _storage_manager = StockStorageManager(
            backend_type=backend_type,
            db_path=db_path,
            remote_config=remote_config,
            retention_days=retention_days,
        )

    return _storage_manager


def close_stock_storage_manager() -> None:
    """关闭存储管理器单例"""
    global _storage_manager
    if _storage_manager is not None:
        _storage_manager.close()
        _storage_manager = None
