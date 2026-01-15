# coding=utf-8
"""
股票分析主流程调度器

改写版本：
- stock_map 从 config/config.yaml 中获取
- 数据存储使用 storage/ 模块
- 分析功能使用 ai_analysis/functions/ 模块
- AI 智能分析（调用 Claude API）
"""

import os
import json
import time
import yaml
import logging
from datetime import date
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 存储模块
from storage import get_stock_storage_manager, StockStorageManager

# AI 分析模块
from ai_analysis.functions.market_data import MarketDataProvider
from ai_analysis.functions.technical import TechnicalAnalyzer
from ai_analysis.prompts import PromptTemplates

logger = logging.getLogger(__name__)


def load_stock_map_from_config(config_path: str = "config/config.yaml") -> Dict[str, List[str]]:
    """
    从 config.yaml 加载 stock_map
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        {market: [codes...]} 格式的股票映射
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        stock_map = config.get('ai_analysis', {}).get('stock_map', {})
        
        # 处理 YAML 格式：将嵌套结构转为列表
        result = {}
        for market, codes in stock_map.items():
            if isinstance(codes, dict):
                result[market] = list(codes.keys())
            elif isinstance(codes, list):
                result[market] = codes
            elif isinstance(codes, (str, int)):
                result[market] = [str(codes)]
            else:
                result[market] = []
        
        return result
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}


class StockAnalysisPipeline:
    """
    股票分析主流程调度器
    
    职责：
    1. 管理整个分析流程
    2. 协调数据获取、存储、分析模块
    3. 实现并发控制和异常处理
    """
    
    def __init__(
        self,
        config_path: str = "config/config.yaml",
        max_workers: int = 3
    ):
        """
        初始化调度器
        
        Args:
            config_path: 配置文件路径
            max_workers: 最大并发线程数
        """
        self.config_path = config_path
        self.max_workers = max_workers
        
        # 从配置加载 stock_map
        self.stock_map = load_stock_map_from_config(config_path)
        
        # 初始化存储管理器
        self.storage = get_stock_storage_manager(backend_type="auto")
        
        logger.info(f"调度器初始化完成，最大并发数: {self.max_workers}")
        logger.info(f"股票列表: {self.stock_map}")
    
    def fetch_and_save_stock_data(
        self, 
        code: str,
        market: str = "CN-A",
        force_refresh: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        获取并保存单只股票数据
        
        断点续传逻辑：
        1. 检查数据库是否已有今日数据
        2. 如果有且不强制刷新，则跳过网络请求
        3. 否则从数据源获取并保存
        
        Args:
            code: 股票代码
            market: 市场类型 (CN-A / US / HK)
            force_refresh: 是否强制刷新（忽略本地缓存）
            
        Returns:
            Tuple[是否成功, 错误信息]
        """
        try:
            today = date.today()
            
            # 断点续传检查：如果今日数据已存在，跳过
            if not force_refresh and self.storage.has_today_data(code, today):
                logger.info(f"[{code}] 今日数据已存在，跳过获取（断点续传）")
                return True, None
            
            # 使用 MarketDataProvider 获取数据
            logger.info(f"[{code}] 开始从数据源获取数据...")
            df = MarketDataProvider.get_hist_with_ma(code, market, days=30)
            
            if df is None or df.empty:
                return False, "获取数据为空"
            
            # 列名映射：将中文列名转为英文
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_chg',
                '换手率': 'turnover_rate',
                'MA5': 'ma5',
                'MA10': 'ma10',
                'MA20': 'ma20',
                'MA60': 'ma60',
            }
            df = df.rename(columns=column_mapping)
            
            # 确保有 date 列
            if 'date' not in df.columns and '日期' not in df.columns:
                df = df.reset_index()
                if 'index' in df.columns:
                    df = df.rename(columns={'index': 'date'})
            
            # 添加缺失列的默认值
            if 'volume_ratio' not in df.columns:
                df['volume_ratio'] = None
            
            # 保存到数据库
            saved_count = self.storage.save_from_dataframe(df, code, "MarketDataProvider")
            logger.info(f"[{code}] 数据保存成功（新增 {saved_count} 条）")
            
            return True, None
            
        except Exception as e:
            error_msg = f"获取/保存数据失败: {str(e)}"
            logger.error(f"[{code}] {error_msg}")
            return False, error_msg
    
    def analyze_stock(self, code: str, market: str = "CN-A") -> Optional[Dict[str, Any]]:
        """
        分析单只股票
        
        使用 ai_analysis/functions/ 下的分析方法：
        1. 获取实时行情（量比、换手率）
        2. 获取筹码分布
        3. 进行均线排列分析
        4. 计算趋势综合评分
        
        Args:
            code: 股票代码
            market: 市场类型
            
        Returns:
            分析结果字典 或 None（如果分析失败）
        """
        try:
            result = {
                "code": code,
                "market": market,
                "timestamp": date.today().isoformat()
            }
            
            # Step 1: 获取实时行情
            realtime_quote = MarketDataProvider.get_realtime_quote(code, market)
            if "error" not in realtime_quote:
                result["realtime"] = realtime_quote
                result["name"] = realtime_quote.get("name", f"股票{code}")
                logger.info(f"[{code}] {result['name']} 实时行情: 价格={realtime_quote.get('price')}, "
                          f"量比={realtime_quote.get('volume_ratio')}, 换手率={realtime_quote.get('turnover_rate')}%")
            else:
                result["name"] = f"股票{code}"
                logger.warning(f"[{code}] 获取实时行情失败: {realtime_quote.get('error')}")
            
            # Step 2: 获取筹码分布（仅A股）
            if market == "CN-A":
                chip_data = MarketDataProvider.get_chip_distribution(code)
                if "error" not in chip_data:
                    result["chip"] = chip_data
                    logger.info(f"[{code}] 筹码分布: 获利比例={chip_data.get('profit_ratio')}, "
                              f"筹码状态={chip_data.get('chip_status')}")
                else:
                    logger.warning(f"[{code}] 获取筹码分布失败: {chip_data.get('error')}")
            
            # Step 3: 均线排列分析
            ma_alignment = TechnicalAnalyzer.check_ma_alignment(code, market)
            if "error" not in ma_alignment:
                result["ma_alignment"] = ma_alignment
                logger.info(f"[{code}] 均线排列: {ma_alignment.get('alignment')}, "
                          f"趋势强度={ma_alignment.get('trend_strength')}")
            else:
                logger.warning(f"[{code}] 均线排列分析失败: {ma_alignment.get('error')}")
            
            # Step 4: 趋势综合评分
            trend_score = TechnicalAnalyzer.calculate_trend_score(code, market)
            if "error" not in trend_score:
                result["trend_score"] = trend_score
                logger.info(f"[{code}] 趋势评分: {trend_score.get('total_score')}/100, "
                          f"信号={trend_score.get('signal')}")
            else:
                logger.warning(f"[{code}] 趋势评分计算失败: {trend_score.get('error')}")
            
            # Step 5: 综合技术分析
            comprehensive = TechnicalAnalyzer.comprehensive_analysis(code, market)
            if "error" not in comprehensive:
                result["comprehensive"] = comprehensive
                logger.info(f"[{code}] 综合分析: 信号={comprehensive.get('overall_signal')}, "
                          f"评分={comprehensive.get('score')}")
            
            return result
            
        except Exception as e:
            logger.error(f"[{code}] 分析失败: {e}")
            logger.exception(f"[{code}] 详细错误信息:")
            return None
    
    def process_single_stock(
        self, 
        code: str,
        market: str = "CN-A",
        skip_analysis: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        处理单只股票的完整流程
        
        包括：
        1. 获取数据
        2. 保存数据
        3. 技术分析
        
        Args:
            code: 股票代码
            market: 市场类型
            skip_analysis: 是否跳过分析
            
        Returns:
            分析结果 或 None
        """
        logger.info(f"========== 开始处理 {code} ({market}) ==========")
        
        try:
            # Step 1: 获取并保存数据
            success, error = self.fetch_and_save_stock_data(code, market)
            
            if not success:
                logger.warning(f"[{code}] 数据获取失败: {error}")
            
            # Step 2: 分析
            if skip_analysis:
                logger.info(f"[{code}] 跳过分析（dry-run 模式）")
                return None
            
            result = self.analyze_stock(code, market)
            
            if result:
                logger.info(f"[{code}] 分析完成")
            
            return result
            
        except Exception as e:
            logger.exception(f"[{code}] 处理过程发生未知异常: {e}")
            return None
    
    def run(
        self, 
        stock_codes: Optional[List[Tuple[str, str]]] = None,
        dry_run: bool = False
    ) -> List[Dict[str, Any]]:
        """
        运行完整的分析流程
        
        Args:
            stock_codes: [(code, market), ...] 列表（可选，默认使用配置中的股票）
            dry_run: 是否仅获取数据不分析
            
        Returns:
            分析结果列表
        """
        start_time = time.time()
        
        # 使用配置中的股票列表
        if stock_codes is None:
            stock_codes = []
            for market, codes in self.stock_map.items():
                for code in codes:
                    stock_codes.append((str(code), market))
        
        if not stock_codes:
            logger.error("未配置股票列表，请在 config.yaml 中设置 ai_analysis.stock_map")
            return []
        
        logger.info(f"===== 开始分析 {len(stock_codes)} 只股票 =====")
        logger.info(f"股票列表: {stock_codes}")
        logger.info(f"模式: {'仅获取数据' if dry_run else '完整分析'}")
        
        results: List[Dict[str, Any]] = []
        
        # 顺序处理（避免 SQLite 多线程问题）
        for code, market in stock_codes:
            try:
                result = self.process_single_stock(code, market, skip_analysis=dry_run)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"[{code}] 任务执行失败: {e}")
        
        # 统计
        elapsed_time = time.time() - start_time
        success_count = len(results)
        fail_count = len(stock_codes) - success_count
        
        logger.info(f"===== 分析完成 =====")
        logger.info(f"成功: {success_count}, 失败: {fail_count}, 耗时: {elapsed_time:.2f} 秒")
        
        return results
    
    def get_ai_stock_analysis(
        self, 
        results: List[Dict[str, Any]], 
        model: str = "claude-sonnet-4-20250514"
    ) -> Dict[str, str]:
        """
        使用 Claude AI 分析股票数据，生成投资建议
        
        Args:
            results: 股票分析结果列表
            model: Claude 模型名称
            
        Returns:
            {"title": AI生成的标题, "content": AI分析内容}
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"title": "", "content": "\n> ⚠️ 未设置 ANTHROPIC_API_KEY，跳过 AI 分析\n"}
        
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            
            # 构建股票数据摘要
            stock_summary = json.dumps(results, ensure_ascii=False, indent=2, default=str)
            
            # 使用系统角色中的交易理念
            system_prompt = PromptTemplates.SYSTEM_ROLE
            
            user_prompt = f"""请根据以下自选股技术分析数据生成投资建议：

## 股票分析数据
{stock_summary}

## 分析要求

**首先，请生成一个简短的报告标题**（10-20字），格式为：
TITLE: [你的标题]

标题要求：
- 简洁概括今日自选股整体状态
- 例如："多数个股偏弱，建议观望" 或 "平安银行现买点，可轻仓介入"

**然后，提供详细分析：**

1. **总体评估**（1-2句话）
   - 综合评估当前自选股的整体状态

2. **个股点评**（每只股票1-2句话）
   - 根据趋势评分、均线排列、筹码分布等指标点评
   - 明确给出操作建议：买入/持有/减仓/卖出

3. **风险提示**
   - 指出高风险股票
   - 提醒追高风险（乖离率>5%）

4. **短期策略**
   - 给出具体的仓位建议
   - 优先级排序：哪些股票值得重点关注

请用简洁的中文回答，使用 Markdown 格式。严格遵循"不追高"的交易理念。
评分说明：
- 80分以上：强烈买入
- 60-79分：买入/加仓
- 40-59分：观望/持有
- 40分以下：减仓/卖出
"""
            
            logger.info("[AI 分析] 正在调用 Claude API...")
            
            response = client.messages.create(
                model=model,
                max_tokens=3000,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            # 提取文本
            text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
            if text_blocks:
                full_text = "\n".join(text_blocks)
                
                # 解析标题
                title = ""
                content = full_text
                if "TITLE:" in full_text:
                    lines = full_text.split("\n")
                    for i, line in enumerate(lines):
                        if line.strip().startswith("TITLE:"):
                            title = line.replace("TITLE:", "").strip()
                            # 移除标题行
                            content = "\n".join(lines[:i] + lines[i+1:]).strip()
                            break
                
                logger.info(f"[AI 分析] 分析完成，标题: {title}")
                return {
                    "title": title,
                    "content": "\n## 🤖 AI 智能分析\n\n" + content + "\n"
                }
            
            return {"title": "", "content": "\n> ⚠️ AI 分析结果为空\n"}
            
        except Exception as e:
            logger.error(f"[AI 分析] 调用失败: {e}")
            return {"title": "", "content": f"\n> ⚠️ AI 分析调用失败: {str(e)}\n"}
    
    def generate_report_md(
        self, 
        results: List[Dict[str, Any]], 
        ai_title: str = "",
        ai_analysis: str = ""
    ) -> str:
        """
        将分析结果转换为 Markdown 格式
        
        Args:
            results: 分析结果列表
            ai_title: AI 生成的标题（可选）
            ai_analysis: AI 分析内容（可选）
            
        Returns:
            Markdown 格式的报告内容
        """
        from datetime import datetime
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 使用 AI 标题或默认标题
        title = ai_title if ai_title else f"自选股分析 {today}"
        
        # Frontmatter
        content = f'''+++
title = "{title}"
date = "{today}"
description = "股票技术分析报告"
[taxonomies]
categories = ["stock"]
tags = ["技术分析", "自选股"]
+++

'''
        
        content += "## 📊 分析摘要\n\n"
        content += "| 股票 | 名称 | 市场 | 评分 | 信号 |\n"
        content += "|:----:|:----:|:----:|:----:|:----:|\n"
        
        for r in results:
            code = r.get("code", "")
            name = r.get("name", "")
            market = r.get("market", "")
            score = r.get("trend_score", {}).get("total_score", 0)
            signal = r.get("trend_score", {}).get("signal", "N/A")
            content += f"| {code} | {name} | {market} | {score} | {signal} |\n"
        
        content += "\n---\n\n"
        
        # 每只股票的详细分析
        for r in results:
            code = r.get("code", "")
            name = r.get("name", code)
            market = r.get("market", "")
            
            content += f"## 📈 {name} ({code})\n\n"
            
            # 实时行情
            realtime = r.get("realtime", {})
            if realtime:
                content += "### 实时行情\n\n"
                content += "| 指标 | 数值 |\n"
                content += "|:----:|-----:|\n"
                content += f"| 价格 | {realtime.get('price', 0):.2f} |\n"
                content += f"| 涨跌幅 | {realtime.get('change_pct', 0):+.2f}% |\n"
                if market == "CN-A":
                    content += f"| 量比 | {realtime.get('volume_ratio', 0):.2f} |\n"
                    content += f"| 换手率 | {realtime.get('turnover_rate', 0):.2f}% |\n"
                    content += f"| 市盈率 | {realtime.get('pe_ratio', 0):.2f} |\n"
                content += "\n"
            
            # 趋势评分
            trend_score = r.get("trend_score", {})
            if trend_score and "error" not in trend_score:
                content += "### 趋势评分\n\n"
                content += f"**综合评分: {trend_score.get('total_score', 0)}/100** {trend_score.get('signal', '')}\n\n"
                
                # 评分明细
                breakdown = trend_score.get("breakdown", {})
                if breakdown:
                    content += "| 维度 | 得分 | 状态 |\n"
                    content += "|:----:|:----:|:----:|\n"
                    dimension_names = {
                        "ma_alignment": "均线排列",
                        "bias": "乖离率",
                        "volume": "量能配合",
                        "rsi": "RSI",
                        "macd": "MACD"
                    }
                    for key, data in breakdown.items():
                        dim_name = dimension_names.get(key, key)
                        s = data.get("score", 0)
                        status = str(data.get("status", data.get("value", "")))[:20]
                        content += f"| {dim_name} | {s} | {status} |\n"
                    content += "\n"
                
                # 检查清单
                checklist = trend_score.get("checklist", [])
                if checklist:
                    content += "### 检查清单\n\n"
                    content += "| 检查项 | 状态 | 数值 |\n"
                    content += "|:------:|:----:|:----:|\n"
                    for item in checklist:
                        status = item.get("status", "⚠️")
                        item_name = item.get("name", "")
                        value = str(item.get("value", ""))[:25]
                        content += f"| {item_name} | {status} | {value} |\n"
                    content += "\n"
            
            # 均线排列
            ma_alignment = r.get("ma_alignment", {})
            if ma_alignment and "error" not in ma_alignment:
                content += "### 均线排列分析\n\n"
                content += f"- 排列状态: **{ma_alignment.get('alignment', 'N/A')}**\n"
                content += f"- MA5: {ma_alignment.get('ma5', 0):.2f}\n"
                content += f"- MA10: {ma_alignment.get('ma10', 0):.2f}\n"
                content += f"- MA20: {ma_alignment.get('ma20', 0):.2f}\n"
                content += f"- 趋势强度: {ma_alignment.get('trend_strength', 0)}\n"
                content += f"- 建议: {ma_alignment.get('trading_advice', '')}\n\n"
            
            # 筹码分布（仅A股）
            chip = r.get("chip", {})
            if chip and "error" not in chip:
                content += "### 筹码分布\n\n"
                content += f"- 获利比例: {chip.get('profit_ratio', 0):.1%}\n"
                content += f"- 平均成本: {chip.get('avg_cost', 0):.2f}\n"
                content += f"- 筹码状态: **{chip.get('chip_status', 'N/A')}**\n\n"
            
            content += "---\n\n"
        
        # 添加 AI 分析内容
        if ai_analysis:
            content += ai_analysis
        
        return content
    
    def save_report(self, content: str, output_dir: str = "page/src/content/post/stock") -> str:
        """
        保存报告到文件
        
        Args:
            content: Markdown 报告内容
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        from pathlib import Path
        from datetime import datetime
        
        today = datetime.now().strftime("%Y-%m-%d")
        year = today[:4]
        month = today[5:7]
        
        output_path = Path(output_dir) / year / month
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{today}-stock-analysis.md"
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已保存: {file_path}")
        return str(file_path)
    
    def close(self):
        """关闭资源"""
        if self.storage:
            self.storage.close()


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="股票分析调度器")
    parser.add_argument("--dry-run", action="store_true", help="仅获取数据，不进行分析")
    parser.add_argument("--no-ai", action="store_true", help="禁用 AI 智能分析")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--workers", type=int, default=1, help="并发线程数")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # 运行
    pipeline = StockAnalysisPipeline(
        config_path=args.config,
        max_workers=args.workers
    )
    
    try:
        results = pipeline.run(dry_run=args.dry_run)
        
        # 打印结果摘要
        if results:
            print("\n===== 分析结果摘要 =====")
            for r in results:
                signal = r.get("trend_score", {}).get("signal", "N/A")
                score = r.get("trend_score", {}).get("total_score", 0)
                print(f"  {r.get('code')} ({r.get('name')}): {signal} (评分: {score})")
            
            # AI 智能分析
            ai_title = ""
            ai_content = ""
            if not args.no_ai:
                ai_result = pipeline.get_ai_stock_analysis(results)
                ai_title = ai_result.get("title", "")
                ai_content = ai_result.get("content", "")
                if ai_title:
                    print(f"\n🤖 AI 分析已生成，标题: {ai_title}")
                else:
                    print("\n🤖 AI 分析已生成")
            
            # 生成并保存 Markdown 报告
            report_content = pipeline.generate_report_md(results, ai_title, ai_content)
            report_path = pipeline.save_report(report_content)
            print(f"\n📄 报告已保存: {report_path}")
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()
