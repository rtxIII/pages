# coding=utf-8
"""
===================================
A股自选股智能分析系统 - 存储模块
===================================

支持的存储后端:
- local: 本地 SQLite 存储
- remote: 远程云存储（S3 兼容协议：R2/OSS/COS/S3 等）
- auto: 根据环境自动选择（GitHub Actions 用 remote，其他用 local）
"""

from storage.base import (
    StockStorageBackend,
    StockDaily,
    convert_dataframe_to_stock_daily_list,
    convert_stock_daily_list_to_dataframe,
)
from storage.stock import StockStorage, get_stock_storage, close_stock_storage
from storage.manager import (
    StockStorageManager,
    get_stock_storage_manager,
    close_stock_storage_manager,
)

# 远程后端可选导入（需要 boto3）
try:
    from storage.remote import RemoteStockStorage
    HAS_REMOTE = True
except ImportError:
    RemoteStockStorage = None
    HAS_REMOTE = False

__all__ = [
    # 抽象基类
    "StockStorageBackend",
    # 数据模型
    "StockDaily",
    # 转换函数
    "convert_dataframe_to_stock_daily_list",
    "convert_stock_daily_list_to_dataframe",
    # 本地存储
    "StockStorage",
    "get_stock_storage",
    "close_stock_storage",
    # 远程存储
    "RemoteStockStorage",
    "HAS_REMOTE",
    # 存储管理器
    "StockStorageManager",
    "get_stock_storage_manager",
    "close_stock_storage_manager",
]
