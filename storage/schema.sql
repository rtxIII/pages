-- ============================================
-- A股自选股智能分析系统 - 数据库表结构
-- ============================================

-- ============================================
-- 股票日线数据表
-- 存储每日行情数据和计算的技术指标
-- ============================================
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
);

-- ============================================
-- 索引定义
-- ============================================

-- 股票代码 + 日期联合索引（主查询索引）
CREATE INDEX IF NOT EXISTS ix_code_date ON stock_daily(code, date);
