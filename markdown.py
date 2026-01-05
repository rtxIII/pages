# coding=utf-8
"""
HTML to Markdown 转换模块

将 index.html 热点新闻报告转换为 Hugo frontmatter 格式的 Markdown 文件
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from html.parser import HTMLParser


class NewsHTMLParser(HTMLParser):
    """解析新闻 HTML 报告"""
    
    def __init__(self):
        super().__init__()
        self.reset_state()
    
    def reset_state(self):
        """重置解析状态"""
        # 报告元数据
        self.report_type = ""
        self.news_count = 0
        self.hot_count = 0
        self.generate_time = ""
        
        # 热词分组数据
        self.word_groups: List[Dict] = []
        self.current_group: Optional[Dict] = None
        self.current_news: Optional[Dict] = None
        
        # div 深度追踪 - 用于正确匹配嵌套的 div 标签
        self._div_depth = 0
        self._word_group_div_depth = 0
        self._news_item_div_depth = 0
        
        # 解析状态
        self._in_header = False
        self._in_info_item = False
        self._in_info_label = False
        self._in_info_value = False
        self._current_label = ""
        
        self._in_word_group = False
        self._in_word_name = False
        self._in_word_count = False
        self._in_word_index = False
        
        self._in_news_item = False
        self._in_news_content = False
        self._in_news_header = False
        self._in_news_title = False
        self._in_news_link = False
        
        self._in_source_name = False
        self._in_rank_num = False
        self._in_time_info = False
        self._in_count_info = False
        
        # RSS 区域标记 - 跳过处理
        self._in_rss_section = False
        self._rss_div_depth = 0
    
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]):
        # 追踪 div 深度
        if tag == 'div':
            self._div_depth += 1
        
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get('class', '')
        
        # 跳过 RSS 区域
        if 'rss-section' in class_name:
            self._in_rss_section = True
            self._rss_div_depth = self._div_depth
            return
        
        if self._in_rss_section:
            return
        
        # 头部区域
        if 'header' in class_name and 'news-header' not in class_name and 'word-header' not in class_name:
            self._in_header = True
        elif 'info-item' in class_name:
            self._in_info_item = True
        elif 'info-label' in class_name:
            self._in_info_label = True
        elif 'info-value' in class_name:
            self._in_info_value = True
        
        # 热词分组
        elif 'word-group' in class_name:
            self._in_word_group = True
            self._word_group_div_depth = self._div_depth
            self.current_group = {
                'name': '',
                'count': 0,
                'index': '',
                'news': []
            }
        elif 'word-name' in class_name:
            self._in_word_name = True
        elif 'word-count' in class_name:
            self._in_word_count = True
        elif 'word-index' in class_name:
            self._in_word_index = True
        
        # 新闻条目
        elif 'news-item' in class_name:
            self._in_news_item = True
            self._news_item_div_depth = self._div_depth
            self.current_news = {
                'title': '',
                'url': '',
                'source': '',
                'rank': '',
                'time': '',
                'count': ''
            }
        elif 'news-content' in class_name:
            self._in_news_content = True
        elif 'news-header' in class_name:
            self._in_news_header = True
        elif 'news-title' in class_name:
            self._in_news_title = True
        elif tag == 'a' and 'news-link' in class_name:
            self._in_news_link = True
            if self.current_news:
                href = attrs_dict.get('href', '')
                # 解码 HTML 实体
                self.current_news['url'] = href.replace('&amp;', '&')
        
        # 新闻元信息
        elif 'source-name' in class_name:
            self._in_source_name = True
        elif 'rank-num' in class_name:
            self._in_rank_num = True
        elif 'time-info' in class_name:
            self._in_time_info = True
        elif 'count-info' in class_name:
            self._in_count_info = True
    
    def handle_endtag(self, tag: str):
        # RSS 区域结束检测
        if self._in_rss_section and tag == 'div':
            if self._div_depth == self._rss_div_depth:
                self._in_rss_section = False
            self._div_depth -= 1
            return
        
        if self._in_rss_section:
            if tag == 'div':
                self._div_depth -= 1
            return
        
        if tag == 'span':
            self._in_info_label = False
            self._in_info_value = False
            self._in_source_name = False
            self._in_rank_num = False
            self._in_time_info = False
            self._in_count_info = False
        elif tag == 'a':
            self._in_news_link = False
        elif tag == 'div':
            # 使用 div 深度来正确匹配关闭标签
            if self._in_news_item and self._div_depth == self._news_item_div_depth:
                self._in_news_item = False
                self._in_news_content = False
                self._in_news_header = False
                self._in_news_title = False
                if self.current_news and self.current_group:
                    self.current_group['news'].append(self.current_news)
                self.current_news = None
                
            elif self._in_word_group and self._div_depth == self._word_group_div_depth:
                self._in_word_group = False
                self._in_word_name = False
                self._in_word_count = False
                self._in_word_index = False
                if self.current_group and self.current_group['name']:
                    self.word_groups.append(self.current_group)
                self.current_group = None
                
            elif self._in_word_index:
                self._in_word_index = False
            elif self._in_word_count:
                self._in_word_count = False
            elif self._in_word_name:
                self._in_word_name = False
            elif self._in_news_title:
                self._in_news_title = False
            elif self._in_news_header:
                self._in_news_header = False
            elif self._in_news_content:
                self._in_news_content = False
            elif self._in_info_item:
                self._in_info_item = False
                self._current_label = ""
            elif self._in_header:
                self._in_header = False
            
            self._div_depth -= 1
    
    def handle_data(self, data: str):
        if self._in_rss_section:
            return
        
        data = data.strip()
        if not data:
            return
        
        # 处理头部信息
        if self._in_info_label:
            self._current_label = data
        elif self._in_info_value:
            if self._current_label == "报告类型":
                self.report_type = data
            elif self._current_label == "新闻总数":
                match = re.search(r'(\d+)', data)
                if match:
                    self.news_count = int(match.group(1))
            elif self._current_label == "热点新闻":
                match = re.search(r'(\d+)', data)
                if match:
                    self.hot_count = int(match.group(1))
            elif self._current_label == "生成时间":
                self.generate_time = data
        
        # 处理热词分组
        elif self._in_word_name and self.current_group:
            self.current_group['name'] = data
        elif self._in_word_count and self.current_group:
            match = re.search(r'(\d+)', data)
            if match:
                self.current_group['count'] = int(match.group(1))
        elif self._in_word_index and self.current_group:
            self.current_group['index'] = data
        
        # 处理新闻条目
        elif self._in_news_link and self.current_news:
            self.current_news['title'] = data
        elif self._in_source_name and self.current_news:
            self.current_news['source'] = data
        elif self._in_rank_num and self.current_news:
            self.current_news['rank'] = data
        elif self._in_time_info and self.current_news:
            self.current_news['time'] = data
        elif self._in_count_info and self.current_news:
            self.current_news['count'] = data


def parse_html_report(html_path: str) -> Optional[Dict]:
    """
    解析 HTML 报告文件
    
    Args:
        html_path: HTML 文件路径
        
    Returns:
        解析后的报告数据字典
    """
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        parser = NewsHTMLParser()
        parser.feed(html_content)
        
        return {
            'report_type': parser.report_type,
            'news_count': parser.news_count,
            'hot_count': parser.hot_count,
            'generate_time': parser.generate_time,
            'word_groups': parser.word_groups
        }
    except Exception as e:
        print(f"[HTML解析] 解析失败: {e}")
        return None


def parse_generate_time(time_str: str) -> Tuple[str, str]:
    """
    解析生成时间字符串，返回日期
    
    Args:
        time_str: 格式如 "01-05 11:02"
        
    Returns:
        (date_str, datetime_str) 如 ("2026-01-05", "2026-01-05T11:02:00")
    """
    now = datetime.now()
    current_year = now.year
    
    # 尝试解析 MM-DD HH:MM 格式
    match = re.match(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', time_str)
    if match:
        month, day, hour, minute = match.groups()
        date_str = f"{current_year}-{month}-{day}"
        datetime_str = f"{current_year}-{month}-{day}T{hour}:{minute}:00"
        return date_str, datetime_str
    
    # 回退使用当前日期
    date_str = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    return date_str, datetime_str


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """
    清理文件名，移除特殊字符
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        清理后的文件名
    """
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s-]', '', text)
    cleaned = re.sub(r'\s+', '-', cleaned.strip())
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def generate_filename(date: str, word_groups: List[Dict], max_keywords: int = 3) -> str:
    """
    生成动态文件名
    
    Args:
        date: 日期字符串 YYYY-MM-DD
        word_groups: 热词分组列表
        max_keywords: 最多包含的关键词数
        
    Returns:
        文件名，格式: YYYY-MM-DD-keyword1-keyword2.md
    """
    keywords = []
    for group in word_groups[:max_keywords]:
        name = group.get('name', '')
        if name:
            # 取第一个词
            first_word = name.split()[0] if ' ' in name else name
            cleaned = sanitize_filename(first_word, 15)
            if cleaned:
                keywords.append(cleaned)
    
    if keywords:
        keyword_part = '-'.join(keywords)
        filename = f"{date}-{keyword_part}.md"
    else:
        filename = f"{date}-trend.md"
    
    return filename


def format_frontmatter(date: str, title: str, description: str = "") -> str:
    """
    生成 Hugo frontmatter
    
    Args:
        date: 日期
        title: 标题
        description: 描述
        
    Returns:
        frontmatter 字符串
    """
    tags = ["trend", "news", "热点"]
    categories = ["news"]
    
    tags_str = ', '.join(f'"{tag}"' for tag in tags)
    categories_str = ', '.join(f'"{cat}"' for cat in categories)
    
    frontmatter = f'''+++
date = "{date}"
title = "{title}"
description = "{description}"
tags = [{tags_str}]
categories = [{categories_str}]
+++
'''
    return frontmatter


def format_word_group(group: Dict) -> str:
    """
    格式化单个热词分组为 Markdown
    
    Args:
        group: 热词分组数据
        
    Returns:
        Markdown 内容
    """
    name = group.get('name', '')
    count = group.get('count', 0)
    news_list = group.get('news', [])
    
    section = f"## {name} ({count}条)\n\n"
    
    for news in news_list:
        title = news.get('title', '')
        url = news.get('url', '')
        source = news.get('source', '')
        
        if url:
            section += f"- [{title}]({url})"
        else:
            section += f"- {title}"
        
        if source:
            section += f" - 来源: {source}"
        
        section += "\n"
    
    section += "\n"
    return section


def convert_html_to_markdown(
    html_path: str,
    output_base_dir: str,
    max_keywords: int = 10,
    category: str = "news"
) -> Optional[str]:
    """
    将 HTML 报告转换为 Markdown 文件
    
    Args:
        html_path: HTML 文件路径
        output_base_dir: 输出基础目录 (page/src/content/post)
        max_keywords: 最多包含的热词数
        category: 分类名称
        
    Returns:
        生成的文件路径，失败返回 None
    """
    print(f"[HTML转Markdown] 开始解析: {html_path}")
    
    # 解析 HTML
    report = parse_html_report(html_path)
    if not report:
        print("[HTML转Markdown] HTML 解析失败")
        return None
    
    word_groups = report.get('word_groups', [])
    if not word_groups:
        print("[HTML转Markdown] 未找到热词分组数据")
        return None
    
    print(f"[HTML转Markdown] 解析到 {len(word_groups)} 个热词分组")
    
    # 解析生成时间
    generate_time = report.get('generate_time', '')
    date_str, datetime_str = parse_generate_time(generate_time)
    print(f"[HTML转Markdown] 生成时间: {generate_time} -> {date_str}")
    
    # 从日期中提取年份和月份
    year = date_str[:4]  # YYYY
    month = date_str[5:7]  # MM
    
    # 构建动态输出目录: page/src/content/post/{category}/{year}/{month}/
    output_path = Path(output_base_dir) / category / year / month
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"[HTML转Markdown] 输出目录: {output_path}")
    
    # 生成文件名
    filename = generate_filename(date_str, word_groups, max_keywords=4)
    file_path = output_path / filename
    print(f"[HTML转Markdown] 输出文件: {file_path}")
    
    # 生成标题
    top_keywords = []
    for group in word_groups[:4]:
        name = group.get('name', '')
        if name:
            first_word = name.split()[0] if ' ' in name else name
            top_keywords.append(first_word)
    
    if len(top_keywords) > 3:
        title_keywords = ', '.join(top_keywords[:3]) + '等'
    else:
        title_keywords = ', '.join(top_keywords)
    
    title = f"热点新闻: {title_keywords}"
    
    # 生成描述
    description = f"基于{date_str}的热点新闻汇总"
    
    # 组装 Markdown 内容
    content = format_frontmatter(date_str, title, description)
    content += "\n# 热词统计\n\n"
    content += f"*生成时间: {generate_time}*\n\n"
    
    # 添加每个热词分组
    total_news = 0
    for group in word_groups[:max_keywords]:
        content += format_word_group(group)
        total_news += len(group.get('news', []))
    
    # 添加页脚
    content += "\n---\n\n"
    
    # 收集来源
    sources = set()
    for group in word_groups:
        for news in group.get('news', []):
            source = news.get('source', '')
            if source:
                sources.add(source)
    
    sources_list = list(sources)[:5]
    if sources_list:
        sources_str = '、'.join(sources_list)
        if len(sources) > 5:
            sources_str += '等'
        content += f"*数据来源: {sources_str} | 日期: {date_str}*\n"
    else:
        content += f"*日期: {date_str}*\n"
    
    # 写入文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[HTML转Markdown] 成功生成: {file_path}")
        print(f"[HTML转Markdown] 统计: {len(word_groups[:max_keywords])} 个热词, {total_news} 条新闻")
        return str(file_path)
    except Exception as e:
        print(f"[HTML转Markdown] 写入失败: {e}")
        return None


def main():
    """主函数 - 转换 root/index.html 到 page/src/content/post/{category}/{year}/{month}/"""
    import os
    
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.resolve()
    
    # 定义路径
    html_path = script_dir / "index.html"
    output_base_dir = script_dir / "page" / "src"/ "content" / "post"
    
    if not html_path.exists():
        print(f"[错误] HTML 文件不存在: {html_path}")
        return
    
    result = convert_html_to_markdown(
        html_path=str(html_path),
        output_base_dir=str(output_base_dir),
        max_keywords=10,
        category="news"
    )
    
    if result:
        print(f"\n[完成] Markdown 文件已生成: {result}")
    else:
        print("\n[失败] Markdown 文件生成失败")


if __name__ == "__main__":
    main()
