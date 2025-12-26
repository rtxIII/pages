# coding=utf-8
"""
Markdown 报告生成模块

生成符合 Hugo frontmatter 格式的 Markdown 新闻报告
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    清理文件名,移除特殊字符
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        清理后的文件名
    """
    # 移除特殊字符
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s-]', '', text)
    # 替换空格为连字符
    cleaned = re.sub(r'\s+', '-', cleaned.strip())
    # 限制长度
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def generate_filename(
    date: str,
    top_keywords: List[str],
    max_keywords: int = 3
) -> str:
    """
    生成动态文件名
    
    Args:
        date: 日期字符串 YYYY-MM-DD
        top_keywords: 热词列表
        max_keywords: 最多包含的关键词数
        
    Returns:
        文件名,格式: YYYY-MM-DD-keyword1-keyword2.md
    """
    # 限制关键词数量
    keywords = top_keywords[:max_keywords]
    
    # 清理关键词
    cleaned_keywords = [sanitize_filename(kw, 15) for kw in keywords]
    
    # 组合文件名
    if cleaned_keywords:
        keyword_part = '-'.join(cleaned_keywords)
        filename = f"{date}-{keyword_part}.md"
    else:
        filename = f"{date}-trend.md"
    
    return filename


def format_frontmatter(
    date: str,
    title: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    categories: Optional[List[str]] = None
) -> str:
    """
    生成 Hugo frontmatter
    
    Args:
        date: 日期
        title: 标题
        description: 描述
        tags: 标签列表
        categories: 分类列表
        
    Returns:
        frontmatter 字符串
    """
    if tags is None:
        tags = ["trend", "news", "热点"]
    if categories is None:
        categories = ["news"]
    
    # 格式化标签和分类
    tags_str = ', '.join(f'"{tag}"' for tag in tags)
    categories_str = ', '.join(f'"{cat}"' for cat in categories)
    
    frontmatter = f"""+++
date = "{date}"
title = "{title}"
description = "{description}"
tags = [{tags_str}]
categories = [{categories_str}]
+++
"""
    return frontmatter


def format_keyword_section(
    keyword: str,
    news_items: List[Dict],
    max_items: int = 20
) -> str:
    """
    格式化单个热词章节
    
    Args:
        keyword: 热词
        news_items: 新闻列表
        max_items: 最多显示条数
        
    Returns:
        Markdown 章节内容
    """
    # 限制条数
    items = news_items[:max_items]
    count = len(news_items)
    
    section = f"## {keyword} ({count}条)\n\n"
    
    for item in items:
        title = item.get('title', '')
        url = item.get('url', '')
        source = item.get('source_name', '')
        rank = item.get('rank', 0)
        
        # 格式化新闻条目
        if url:
            section += f"- [{title}]({url})"
        else:
            section += f"- {title}"
        
        # 添加元信息
        meta_parts = []
        if source:
            meta_parts.append(f"来源: {source}")
        if rank:
            meta_parts.append(f"排名: #{rank}")
        
        if meta_parts:
            section += f" - {' | '.join(meta_parts)}"
        
        section += "\n"
    
    section += "\n"
    return section


def generate_markdown_report(
    stats: List[Dict],
    output_dir: str,
    date: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    max_keywords: int = 10,
    max_news_per_keyword: int = 20
) -> Optional[str]:
    """
    生成 Markdown 报告
    
    Args:
        stats: 统计数据列表
        output_dir: 输出目录
        date: 报告日期
        start_date: 统计开始日期
        end_date: 统计结束日期
        platforms: 平台列表
        max_keywords: 最多包含的热词数
        max_news_per_keyword: 每个热词最多显示的新闻数
        
    Returns:
        生成的文件路径
    """
    if not stats:
        print("[Markdown报告] 没有统计数据,跳过生成")
        return None
    
    try:
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 提取热词列表(用于标题和文件名)
        top_keywords = [stat['group_key'] for stat in stats[:max_keywords]]
        
        # 生成文件名
        filename = generate_filename(date, top_keywords, max_keywords=3)
        file_path = output_path / filename
        
        # 生成标题
        if len(top_keywords) > 3:
            title_keywords = ', '.join(top_keywords[:3]) + '等'
        else:
            title_keywords = ', '.join(top_keywords)
        
        title = f"热点新闻: {title_keywords}"
        
        # 生成描述
        if start_date and end_date:
            period = f"{start_date} 至 {end_date}"
        else:
            period = date
        description = f"基于{period}的热点新闻汇总"
        
        # 生成 frontmatter
        content = format_frontmatter(date, title, description)
        
        # 添加主标题
        content += f"\n# 热词统计\n\n"
        
        # 添加统计说明
        if start_date and end_date:
            content += f"*统计周期: {start_date} 至 {end_date}*\n\n"
        
        # 添加每个热词章节
        for stat in stats[:max_keywords]:
            keyword = stat['group_key']
            news_items = stat.get('news', [])
            
            if news_items:
                content += format_keyword_section(
                    keyword,
                    news_items,
                    max_news_per_keyword
                )
        
        # 添加页脚
        content += "\n---\n\n"
        
        # 数据来源
        if platforms:
            platform_str = '、'.join(platforms[:5])
            if len(platforms) > 5:
                platform_str += '等'
            content += f"*数据来源: {platform_str}"
        else:
            content += "*数据来源: 多个新闻平台"
        
        # 统计周期
        if start_date and end_date:
            content += f" | 统计周期: {start_date} 至 {end_date}*\n"
        else:
            content += f" | 日期: {date}*\n"
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[Markdown报告] 已生成: {file_path}")
        return str(file_path)
        
    except Exception as e:
        print(f"[Markdown报告] 生成失败: {e}")
        return None


def generate_markdown_from_analysis(
    stats: List[Dict],
    output_dir: str,
    historical_days: int = 7,
    max_keywords: int = 10,
    max_news_per_keyword: int = 20
) -> Optional[str]:
    """
    从分析结果生成 Markdown 报告(便捷函数)
    
    Args:
        stats: 统计数据
        output_dir: 输出目录
        historical_days: 历史天数
        max_keywords: 最多热词数
        max_news_per_keyword: 每个热词最多新闻数
        
    Returns:
        生成的文件路径
    """
    from datetime import datetime, timedelta
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=historical_days - 1)
    
    date_str = end_date.strftime("%Y-%m-%d")
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # 提取平台列表
    platforms = set()
    for stat in stats:
        for news in stat.get('news', []):
            source = news.get('source_name')
            if source:
                platforms.add(source)
    
    return generate_markdown_report(
        stats=stats,
        output_dir=output_dir,
        date=date_str,
        start_date=start_str,
        end_date=end_str,
        platforms=list(platforms),
        max_keywords=max_keywords,
        max_news_per_keyword=max_news_per_keyword
    )
