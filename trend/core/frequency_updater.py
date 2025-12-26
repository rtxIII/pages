# coding=utf-8
"""
频率词自动更新模块

基于历史新闻数据自动识别新热词并追加到 frequency_words.txt
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from datetime import datetime


class KeywordCandidate:
    """热词候选对象"""
    
    def __init__(self, keyword: str):
        self.keyword = keyword
        self.frequency = 0  # 出现次数
        self.platforms: Set[str] = set()  # 出现的平台
        self.dates: Set[str] = set()  # 出现的日期
        self.ranks: List[int] = []  # 所有排名
        
    @property
    def platform_count(self) -> int:
        """平台覆盖度"""
        return len(self.platforms)
    
    @property
    def date_count(self) -> int:
        """时间持续性"""
        return len(self.dates)
    
    @property
    def avg_rank(self) -> float:
        """平均排名"""
        return sum(self.ranks) / len(self.ranks) if self.ranks else 50
    
    def calculate_score(self) -> float:
        """
        计算热词评分
        
        评分公式:
        总分 = (频次/10) * 0.4 + (平台数/5) * 0.3 + (天数/7) * 0.2 + (1 - 排名/50) * 0.1
        """
        freq_score = min(self.frequency / 10, 1.0) * 0.4
        platform_score = min(self.platform_count / 5, 1.0) * 0.3
        date_score = min(self.date_count / 7, 1.0) * 0.2
        rank_score = max(0, 1 - self.avg_rank / 50) * 0.1
        
        return freq_score + platform_score + date_score + rank_score


def extract_keywords_from_title(title: str, min_len: int = 2, max_len: int = 10) -> List[str]:
    """
    从标题中提取可能的关键词
    
    Args:
        title: 新闻标题
        min_len: 最小长度
        max_len: 最大长度
        
    Returns:
        关键词列表
    """
    keywords = []
    
    # 移除特殊字符和数字
    cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z\s]', ' ', title)
    
    # 分词(简单按空格和常见标点)
    words = re.split(r'[\s,，。！!？?、]+', cleaned)
    
    for word in words:
        word = word.strip()
        if min_len <= len(word) <= max_len:
            # 排除纯数字
            if not word.isdigit():
                keywords.append(word)
    
    return keywords


def load_existing_keywords(frequency_file: str) -> Set[str]:
    """
    加载已存在的频率词
    
    Args:
        frequency_file: 频率词文件路径
        
    Returns:
        已存在的关键词集合
    """
    existing = set()
    
    try:
        with open(frequency_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 移除特殊前缀
                if line and not line.startswith('['):
                    keyword = line.lstrip('!+@0123456789')
                    if keyword:
                        existing.add(keyword.lower())
    except FileNotFoundError:
        pass
    
    return existing


def get_stopwords() -> Set[str]:
    """
    获取停用词列表
    
    Returns:
        停用词集合
    """
    return {
        '消息', '报道', '最新', '今日', '昨日', '明日',
        '发布', '宣布', '表示', '称', '表明',
        '记者', '采访', '报告', '通知', '公告',
        '视频', '图片', '直播', '评论', '热议',
        '网友', '用户', '粉丝', '观众',
        '什么', '怎么', '如何', '为何', '哪些',
        '这个', '那个', '这些', '那些',
        '一个', '一些', '很多', '大量',
        '非常', '十分', '特别', '尤其',
        '已经', '正在', '即将', '将要',
        '可能', '或许', '也许', '大概',
        '关于', '对于', '由于', '因为',
        '但是', '然而', '不过', '只是',
        '以及', '还有', '同时', '此外',
    }


def analyze_historical_keywords(
    historical_data: Dict[str, any],
    existing_keywords: Set[str],
    stopwords: Set[str]
) -> Dict[str, KeywordCandidate]:
    """
    分析历史数据提取候选热词
    
    Args:
        historical_data: 历史数据 {date: NewsData}
        existing_keywords: 已存在的关键词
        stopwords: 停用词
        
    Returns:
        候选热词字典 {keyword: KeywordCandidate}
    """
    candidates: Dict[str, KeywordCandidate] = {}
    
    for date, news_data in historical_data.items():
        for platform_id, news_items in news_data.items.items():
            for item in news_items:
                # 提取关键词
                keywords = extract_keywords_from_title(item.title)
                
                for kw in keywords:
                    kw_lower = kw.lower()
                    
                    # 过滤条件
                    if kw_lower in existing_keywords:
                        continue
                    if kw_lower in stopwords:
                        continue
                    if len(kw) < 2 or len(kw) > 10:
                        continue
                    
                    # 记录候选词
                    if kw not in candidates:
                        candidates[kw] = KeywordCandidate(kw)
                    
                    candidate = candidates[kw]
                    candidate.frequency += 1
                    candidate.platforms.add(platform_id)
                    candidate.dates.add(date)
                    candidate.ranks.append(item.rank)
    
    return candidates


def filter_and_score_candidates(
    candidates: Dict[str, KeywordCandidate],
    score_threshold: float = 0.4,  # 降低默认阈值
    min_frequency: int = 2,  # 降低频次要求: 5 -> 2
    min_platforms: int = 2,  # 降低平台数要求: 3 -> 2
    min_dates: int = 1  # 降低为1天,支持单天数据
) -> List[Tuple[str, float]]:
    """
    过滤和评分候选词
    
    Args:
        candidates: 候选词字典
        score_threshold: 评分阈值
        min_frequency: 最小出现次数(默认2)
        min_platforms: 最小平台数(默认2)
        min_dates: 最小日期数(默认1天)
        
    Returns:
        [(keyword, score)] 列表,按评分降序排序
    """
    qualified = []
    
    for keyword, candidate in candidates.items():
        # 基础过滤
        if candidate.frequency < min_frequency:
            continue
        if candidate.platform_count < min_platforms:
            continue
        if candidate.date_count < min_dates:
            continue
        
        # 计算评分
        score = candidate.calculate_score()
        
        if score >= score_threshold:
            qualified.append((keyword, score))
    
    # 按评分降序排序
    qualified.sort(key=lambda x: x[1], reverse=True)
    
    return qualified


def analyze_keyword_usage(
    historical_data: Dict[str, any],
    existing_keywords: Set[str]
) -> Dict[str, int]:
    """
    分析现有关键词的使用情况
    
    Args:
        historical_data: 历史数据 {date: NewsData}
        existing_keywords: 已存在的关键词
        
    Returns:
        {关键词: 出现次数} 字典
    """
    keyword_usage = {kw: 0 for kw in existing_keywords}
    
    for date, news_data in historical_data.items():
        for platform_id, news_items in news_data.items.items():
            for item in news_items:
                title_lower = item.title.lower()
                # 检查每个关键词是否在标题中
                for kw in existing_keywords:
                    if kw in title_lower:
                        keyword_usage[kw] += 1
    
    return keyword_usage


def remove_outdated_keywords(
    frequency_file: str,
    historical_data: Dict[str, any],
    min_usage: int = 1
) -> int:
    """
    删除过时的关键词(在历史数据中出现次数为0的)
    
    Args:
        frequency_file: 频率词文件路径
        historical_data: 历史数据
        min_usage: 最小使用次数(低于此值则删除)
        
    Returns:
        删除的关键词数量
    """
    if not historical_data:
        print("[频率词清理] 没有历史数据,跳过清理")
        return 0
    
    try:
        file_path = Path(frequency_file)
        if not file_path.exists():
            return 0
        
        # 读取现有文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 加载现有关键词
        existing_keywords = load_existing_keywords(frequency_file)
        
        # 分析使用情况
        keyword_usage = analyze_keyword_usage(historical_data, existing_keywords)
        
        # 找出过时关键词
        outdated = [kw for kw, count in keyword_usage.items() if count < min_usage]
        
        if not outdated:
            print("[频率词清理] 没有发现过时关键词")
            return 0
        
        print(f"[频率词清理] 发现 {len(outdated)} 个过时关键词:")
        for kw in outdated:
            print(f"  - {kw} (出现{keyword_usage[kw]}次)")
        
        # 过滤掉过时关键词
        new_lines = []
        outdated_lower = {kw.lower() for kw in outdated}
        
        for line in lines:
            stripped = line.strip()
            # 保留注释和空行
            if not stripped or stripped.startswith('#') or stripped.startswith('['):
                new_lines.append(line)
                continue
            
            # 检查是否是过时关键词
            keyword = stripped.lstrip('!+@0123456789').lower()
            if keyword not in outdated_lower:
                new_lines.append(line)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"[频率词清理] 成功删除 {len(outdated)} 个过时关键词")
        return len(outdated)
        
    except Exception as e:
        print(f"[频率词清理] 删除失败: {e}")
        return 0


def append_to_frequency_file(
    frequency_file: str,
    new_keywords: List[Tuple[str, float]],
    max_append: int = 10
) -> int:
    """
    追加新热词到频率词文件
    
    Args:
        frequency_file: 频率词文件路径
        new_keywords: [(keyword, score)] 新热词列表
        max_append: 最大追加数量
        
    Returns:
        实际追加的数量
    """
    if not new_keywords:
        return 0
    
    try:
        # 限制追加数量
        to_append = new_keywords[:max_append]
        
        # 读取现有内容
        file_path = Path(frequency_file)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
        
        # 确保文件以换行结尾
        if content and not content.endswith('\n'):
            content += '\n'
        
        # 添加时间戳注释
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content += f"\n# 自动添加于 {timestamp}\n"
        
        # 追加新热词(每个词单独成组)
        for keyword, score in to_append:
            content += f"{keyword}\n\n"
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[频率词更新] 成功追加 {len(to_append)} 个新热词到 {frequency_file}")
        for kw, score in to_append:
            print(f"  - {kw} (评分: {score:.2f})")
        
        return len(to_append)
        
    except Exception as e:
        print(f"[频率词更新] 追加失败: {e}")
        return 0


def update_frequency_words(
    storage_backend: any,
    frequency_file: str,
    days: int = 7,
    score_threshold: float = 0.4,  # 降低默认阈值
    max_append: int = 10,
    enable_cleanup: bool = True
) -> int:
    """
    主函数: 自动更新频率词
    
    Args:
        storage_backend: 存储后端实例
        frequency_file: 频率词文件路径
        days: 分析天数
        score_threshold: 评分阈值
        max_append: 最大追加数量
        enable_cleanup: 是否启用过时关键词清理
        
    Returns:
        追加的关键词数量
    """
    print(f"[频率词更新] 开始分析过去 {days} 天的数据...")
    
    # 1. 获取历史数据
    historical_data = storage_backend.get_historical_data(days)
    if not historical_data:
        print("[频率词更新] 没有历史数据,跳过更新")
        return 0
    
    # 1.5 清理过时关键词(如果启用)
    if enable_cleanup:
        remove_outdated_keywords(frequency_file, historical_data, min_usage=1)
    
    # 2. 加载已存在的关键词
    existing_keywords = load_existing_keywords(frequency_file)
    print(f"[频率词更新] 已加载 {len(existing_keywords)} 个现有关键词")
    
    # 3. 获取停用词
    stopwords = get_stopwords()
    
    # 4. 分析候选词
    candidates = analyze_historical_keywords(historical_data, existing_keywords, stopwords)
    print(f"[频率词更新] 发现 {len(candidates)} 个候选关键词")
    
    # 5. 过滤和评分 (降低min_dates为1)
    qualified = filter_and_score_candidates(
        candidates, 
        score_threshold,
        min_dates=1  # 支持单天数据
    )
    print(f"[频率词更新] 筛选出 {len(qualified)} 个符合条件的关键词")
    
    # 6. 追加到文件
    if qualified:
        return append_to_frequency_file(frequency_file, qualified, max_append)
    else:
        print("[频率词更新] 没有符合条件的新热词")
        return 0
