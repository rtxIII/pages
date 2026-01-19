#!/usr/bin/env python3
# coding=utf-8
"""
AI 新闻分析执行脚本

用法:
    python run_analysis.py                          # 分析今日新闻
    python run_analysis.py --date 2026-01-06        # 分析指定日期
    python run_analysis.py --file path/to/news.md   # 分析指定文件
    python run_analysis.py --batch --limit 5        # 批量分析最近5个文件
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent 
sys.path.insert(0, str(PROJECT_ROOT))

from ai_analysis import NewsAnalysisEngine

# Claude 模型配置（从环境变量获取，默认使用 claude-sonnet-4-20250514）
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


def find_news_file_by_date(news_dir: str, date: str) -> str:
    """根据日期查找新闻文件"""
    year, month = date[:4], date[5:7]
    search_dir = Path(news_dir) / year / month
    
    if not search_dir.exists():
        raise FileNotFoundError(f"未找到日期目录: {search_dir}")
    
    # 查找匹配日期的文件
    pattern = f"{date}-*.md"
    files = list(search_dir.glob(pattern))
    
    if not files:
        raise FileNotFoundError(f"未找到 {date} 的新闻文件")
    
    # 返回第一个匹配文件
    return str(files[0])


def main():
    parser = argparse.ArgumentParser(description="AI 新闻市场分析工具")
    
    parser.add_argument(
        "--date",
        type=str,
        help="分析指定日期的新闻 (格式: YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--file",
        type=str,
        help="分析指定新闻文件路径"
    )
    
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量分析模式"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="批量分析时限制文件数量"
    )
    
    parser.add_argument(
        "--news-dir",
        type=str,
        default="page/src/content/post/news",
        help="新闻目录路径（默认: page/src/content/post/news）"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="page/src/content/post/analysis",
        help="输出目录路径（默认: page/src/content/post/analysis）"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=ANTHROPIC_MODEL,
        help=f"Claude 模型名称（默认: {ANTHROPIC_MODEL}）"
    )
    
    args = parser.parse_args()
    
    # 初始化分析引擎
    print("=" * 60)
    print(f"AI 新闻市场分析工具 (AI: {args.model})")
    print("=" * 60)
    
    try:
        engine = NewsAnalysisEngine(
            model=args.model,
            focus_sectors=["科技", "金融", "消费", "医疗"]
        )
    except ValueError as e:
        print(f"\n❌ 初始化失败: {e}")
        print("\n请设置环境变量: export ANTHROPIC_API_KEY='your-api-key'")
        print("获取 API 密钥: https://console.anthropic.com/")
        return
    
    # 确定输入文件
    news_dir = str(PROJECT_ROOT / args.news_dir)
    output_dir = str(PROJECT_ROOT / args.output_dir)
    
    try:
        if args.batch:
            # 批量分析模式
            print(f"\n📁 批量分析模式")
            print(f"   新闻目录: {news_dir}")
            print(f"   输出目录: {output_dir}")
            if args.limit:
                print(f"   限制数量: {args.limit} 个文件")
            
            report_paths = engine.batch_analyze_news_dir(
                news_dir=news_dir,
                output_dir=output_dir,
                limit=args.limit
            )
            
            print(f"\n✅ 批量分析完成，生成 {len(report_paths)} 份报告")
            for path in report_paths:
                print(f"   - {path}")
        
        else:
            # 单文件分析模式
            if args.file:
                news_file = args.file
            elif args.date:
                news_file = find_news_file_by_date(news_dir, args.date)
            else:
                # 默认分析今日新闻
                today = datetime.now().strftime("%Y-%m-%d")
                news_file = find_news_file_by_date(news_dir, today)
            
            print(f"\n📄 分析文件: {news_file}")
            print(f"   输出目录: {output_dir}")
            
            report_path = engine.analyze_and_generate_report(
                news_md_path=news_file,
                output_dir=output_dir
            )
            
            print(f"\n✅ 分析完成")
            print(f"   报告路径: {report_path}")
    
    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
