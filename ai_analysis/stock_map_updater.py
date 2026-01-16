# coding=utf-8
"""
Stock Map 自动更新模块

从 AI 分析结果中提取股票代码，自动更新 config.yaml 中的 stock_map
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

import yaml

logger = logging.getLogger(__name__)


def classify_stock_code(code: str) -> Optional[str]:
    """
    识别股票代码的市场类型
    
    Args:
        code: 股票代码
        
    Returns:
        市场类型: 'HK' / 'CN-A' / 'US' / None（无法识别）
    """
    code = code.strip().upper()
    
    # 纯字母 -> US
    if re.match(r'^[A-Z]{1,5}$', code):
        return 'US'
    
    # 5位数字 -> HK
    if re.match(r'^\d{5}$', code):
        return 'HK'
    
    # 6位数字 -> CN-A
    if re.match(r'^\d{6}$', code):
        return 'CN-A'
    
    # 带市场前缀的格式（如 HK.00100, US.AAPL）
    if '.' in code:
        parts = code.split('.', 1)
        market_prefix = parts[0].upper()
        if market_prefix in ('HK', 'CN-A', 'CN', 'US', 'SH', 'SZ'):
            if market_prefix in ('SH', 'SZ', 'CN'):
                return 'CN-A'
            return market_prefix
    
    return None


def extract_stocks_from_analysis(analysis_result: Dict) -> Dict[str, Set[str]]:
    """
    从分析结果中提取股票代码
    
    Args:
        analysis_result: AI 分析结果字典
        
    Returns:
        {market: {codes...}} 格式的股票映射
    """
    stocks_by_market: Dict[str, Set[str]] = {
        'HK': set(),
        'CN-A': set(),
        'US': set()
    }
    
    # 从 sector_impacts 中提取 related_stocks
    sector_impacts = analysis_result.get('sector_impacts', [])
    for impact in sector_impacts:
        related_stocks = impact.get('related_stocks', [])
        for code in related_stocks:
            if not code:
                continue
            
            # 清理代码格式
            code = str(code).strip()
            
            # 识别市场
            market = classify_stock_code(code)
            if market:
                # 提取纯代码（去掉市场前缀）
                pure_code = code.split('.')[-1] if '.' in code else code
                stocks_by_market[market].add(pure_code)
    
    # 同时检查 function_results
    function_results = analysis_result.get('function_results', {})
    for func_name, results in function_results.items():
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict) and 'related_stocks' in result:
                    for code in result['related_stocks']:
                        if not code:
                            continue
                        code = str(code).strip()
                        market = classify_stock_code(code)
                        if market:
                            pure_code = code.split('.')[-1] if '.' in code else code
                            stocks_by_market[market].add(pure_code)
    
    return stocks_by_market


def update_stock_map(
    new_stocks: Dict[str, Set[str]], 
    config_path: str = "config/analysis.yaml"
) -> Dict[str, List[str]]:
    """
    更新 config.yaml 中的 stock_map（只增加不减少）
    
    Args:
        new_stocks: {market: {codes...}} 格式的新股票
        config_path: 配置文件路径
        
    Returns:
        更新后的 stock_map
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_path}")
        return {}
    
    # 读取现有配置
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
        config = yaml.safe_load(content)
    
    # 获取现有 stock_map
    ai_analysis = config.get('ai_analysis', {})
    stock_map = ai_analysis.get('stock_map', {})
    
    # 合并新股票（只增加不减少）
    added_stocks = []
    for market, codes in new_stocks.items():
        if not codes:
            continue
        
        existing_codes = set(stock_map.get(market, []))
        new_codes = codes - existing_codes
        
        if new_codes:
            # 合并
            merged = sorted(existing_codes | codes)
            stock_map[market] = merged
            added_stocks.extend([f"{market}.{c}" for c in new_codes])
    
    if added_stocks:
        # 更新配置
        ai_analysis['stock_map'] = stock_map
        config['ai_analysis'] = ai_analysis
        
        # 保存配置（使用 ruamel.yaml 保留格式，或简单重写）
        _save_stock_map_to_yaml(config_file, stock_map)
        
        logger.info(f"[Stock Map] 新增股票: {', '.join(added_stocks)}")
    else:
        logger.info("[Stock Map] 无新增股票")
    
    return stock_map


def _save_stock_map_to_yaml(config_file: Path, stock_map: Dict[str, List[str]]) -> None:
    """
    安全更新 YAML 文件中的 stock_map 部分
    
    使用文本替换方式保留原文件格式和注释
    """
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建新的 stock_map YAML 内容
    new_stock_map_lines = ["  stock_map:"]
    for market in ['HK', 'CN-A', 'US']:
        codes = stock_map.get(market, [])
        if codes:
            new_stock_map_lines.append(f"    {market}:")
            for code in codes:
                new_stock_map_lines.append(f'      - "{code}"')
    
    new_stock_map_content = "\n".join(new_stock_map_lines)
    
    # 使用正则替换 stock_map 部分
    # 匹配从 "  stock_map:" 开始到下一个同级或更高级配置项
    pattern = r'(  stock_map:.*?)(?=\n\w|\n  \w(?!:.*?:)|\Z)'
    
    # 更简单的方式：找到 stock_map 的位置，替换到文件末尾或下一个配置块
    lines = content.split('\n')
    new_lines = []
    in_stock_map = False
    stock_map_indent = 0
    
    for line in lines:
        if '  stock_map:' in line and not line.strip().startswith('#'):
            in_stock_map = True
            stock_map_indent = len(line) - len(line.lstrip())
            # 添加新的 stock_map 内容
            new_lines.append(new_stock_map_content)
            continue
        
        if in_stock_map:
            # 检查是否还在 stock_map 块内
            if line.strip() == '':
                continue  # 跳过空行
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= stock_map_indent and line.strip() and not line.strip().startswith('-'):
                # 到达下一个配置块
                in_stock_map = False
                new_lines.append(line)
            # 否则跳过（stock_map 内的行已经被替换）
        else:
            new_lines.append(line)
    
    # 写回文件
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
