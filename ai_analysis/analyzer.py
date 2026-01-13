# coding=utf-8
"""
新闻分析引擎（支持 Function Calling）

核心分析器，整合新闻解析、Anthropic Claude API 调用、Function Calling、报告生成
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from anthropic import Anthropic

from .prompts import PromptTemplates
from .market_scorer import MarketImpactScorer
from .report_generator import AnalysisReportGenerator
from .functions.tools import FunctionToolRegistry


class NewsAnalysisEngine:
    """新闻分析引擎（支持 Function Calling）"""
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "claude-3-5-sonnet-20241022",
        focus_sectors: List[str] = None,
        enable_function_calling: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 20000
    ):
        """
        初始化分析引擎
        
        Args:
            api_key: Anthropic API 密钥（默认从环境变量读取）
            model: Claude 模型名称
            focus_sectors: 聚焦板块列表
            enable_function_calling: 是否启用 Function Calling
            temperature: 温度参数
            max_tokens: 最大 token 数
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("未设置 ANTHROPIC_API_KEY 环境变量")
        
        # 初始化 Anthropic 客户端
        self.client = Anthropic(api_key=self.api_key)
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.focus_sectors = focus_sectors or ["科技", "金融", "消费", "医疗"]
        self.enable_function_calling = enable_function_calling
        
        # Function Calling 工具集
        self.tools = FunctionToolRegistry.get_tools() if enable_function_calling else None
        self.function_results = {}  # 存储函数调用结果
    
    def parse_news_markdown(self, md_file_path: str) -> Dict:
        """
        解析新闻 Markdown 文件
        
        Args:
            md_file_path: Markdown 文件路径
            
        Returns:
            {
                "date": "2026-01-06",
                "hot_keywords": ["美国", "英伟达", ...],
                "news_items": [{"title": ..., "url": ..., "source": ...}]
            }
        """
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 frontmatter 日期
        date_match = re.search(r'date\s*=\s*"([^"]+)"', content)
        date = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")
        
        # 提取热词分组（## 标题）
        hot_keywords = []
        keyword_pattern = r'##\s+([^\n(]+)'
        for match in re.finditer(keyword_pattern, content):
            keyword = match.group(1).strip()
            # 跳过特殊标题
            if not keyword.startswith(('热词', '📊', '🎯', '💡')):
                # 提取第一个关键词
                first_keyword = keyword.split()[0] if ' ' in keyword else keyword
                hot_keywords.append(first_keyword)
        
        # 提取新闻条目（- [标题](链接) - 来源: xxx）
        news_items = []
        news_pattern = r'-\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*-\s*来源:\s*([^\n]+))?'
        for match in re.finditer(news_pattern, content):
            title = match.group(1).strip()
            url = match.group(2).strip()
            source = match.group(3).strip() if match.group(3) else ""
            
            news_items.append({
                "title": title,
                "url": url,
                "source": source
            })
        
        return {
            "date": date,
            "hot_keywords": hot_keywords[:15],  # 限制关键词数量
            "news_items": news_items
        }
    
    def call_claude_api_with_functions(self, messages: List[Dict]) -> Dict:
        """
        调用 Claude API（支持 Function Calling）
        
        Args:
            messages: 消息列表
            
        Returns:
            API 响应
        """
        try:
            # 构建请求参数
            request_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }
            
            # 添加 Function Calling 工具
            if self.enable_function_calling and self.tools:
                request_params["tools"] = self.tools
            
            # 调用 Claude API
            response = self.client.messages.create(**request_params)
            
            return response
            
        except Exception as e:
            print(f"[Claude API 调用失败] {e}")
            raise
    
    def execute_function_calls(self, tool_use_blocks: List) -> List[Dict]:
        """
        执行函数调用
        
        Args:
            tool_use_blocks: Claude 返回的工具使用块
            
        Returns:
            函数调用结果列表
        """
        results = []
        
        for tool_use in tool_use_blocks:
            if tool_use.type == "tool_use":
                function_name = tool_use.name
                arguments = tool_use.input
                
                print(f"[Function Calling] 执行: {function_name}({arguments})")
                
                # 执行函数
                result = FunctionToolRegistry.execute_function(function_name, arguments)
                
                # 存储结果
                self.function_results[function_name] = result
                
                # 特殊处理：存储板块评估结果
                if function_name == "evaluate_sector_impact":
                    self.sector_impact_results.append(arguments)
                
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
        
        return results
    
    def call_llm_api(self, prompt: str) -> str:
        """
        调用 Claude API（简化接口，内部处理 Function Calling）
        
        Args:
            prompt: 用户 Prompt
            
        Returns:
            AI 响应内容
        """
        # 构建初始消息
        system_messages = PromptTemplates.get_system_messages()
        system_prompt = system_messages[0]["content"] if system_messages else ""
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        max_iterations = 10  # 最多执行10轮 Function Calling
        iteration = 0
        response = None
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # 调用 Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_prompt,
                    messages=messages,
                    tools=self.tools if self.enable_function_calling else None
                )
                
                # 检查是否有函数调用
                tool_use_blocks = [block for block in response.content if hasattr(block, 'type') and block.type == "tool_use"]
                
                if not tool_use_blocks:
                    # 没有函数调用，提取文本内容
                    text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
                    return "\n".join(text_blocks) if text_blocks else ""
                
                # 有函数调用，执行函数
                print(f"[Function Calling] 第 {iteration} 轮调用，共 {len(tool_use_blocks)} 个函数")
                
                # 将 AI 的回复添加到消息历史
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                # 执行函数并获取结果
                function_results = self.execute_function_calls(tool_use_blocks)
                
                # 将函数结果添加到消息历史
                messages.append({
                    "role": "user",
                    "content": function_results
                })
                
                # 继续下一轮，让 AI 基于函数结果生成最终回复
                
            except Exception as e:
                print(f"[Claude API 调用失败] {e}")
                return self._generate_fallback_analysis()
        
        # 如果达到最大迭代次数，再调用一次让 Claude 生成最终文本响应
        print(f"[Function Calling] 达到最大迭代次数 {max_iterations}，获取最终响应...")
        try:
            # 最后一次调用，禁用工具以强制生成文本响应
            final_response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages,
                tools=None  # 禁用工具，强制生成文本
            )
            text_blocks = [block.text for block in final_response.content if hasattr(block, 'text')]
            if text_blocks:
                return "\n".join(text_blocks)
        except Exception as e:
            print(f"[Claude API 最终调用失败] {e}")
        
        return self._generate_fallback_analysis()
    
    def _generate_fallback_analysis(self) -> str:
        """生成降级分析（API 调用失败时使用）"""
        return """## 📊 核心要点

1. **API 调用失败** - 无法生成分析

## 🎯 板块影响评估

| 板块 | 方向 | 影响程度 | 置信度 | 理由 |
|------|------|----------|--------|------|
| 未知 | 中性 | 5/10 | 低 | API 调用失败，无法分析 |

## 💡 投资建议

**短期（1-3天）**：建议等待系统恢复后查看分析

**中期（1-2周）**：建议等待系统恢复后查看分析

**风险提示**：当前分析不可用
"""
    
    def analyze_news_file(self, news_md_path: str) -> Dict:
        """
        分析单个新闻文件
        
        Args:
            news_md_path: 新闻 Markdown 文件路径
            
        Returns:
            {
                "analysis_result": MarketAnalysisResult,
                "date": "2026-01-06",
                "sentiment": {...},
                "function_results": {...}  # Function Calling 结果
            }
        """
        print(f"[分析引擎] 开始分析: {news_md_path}")
        
        # 重置函数调用结果
        self.function_results = {}
        self.sector_impact_results = []  # 存储板块评估结果
        
        # 解析新闻文件
        news_data = self.parse_news_markdown(news_md_path)
        print(f"[分析引擎] 提取到 {len(news_data['news_items'])} 条新闻")
        print(f"[分析引擎] 热词: {', '.join(news_data['hot_keywords'][:5])}")
        
        # 构建 Prompt
        prompt = PromptTemplates.build_analysis_prompt(
            date=news_data["date"],
            hot_keywords=news_data["hot_keywords"],
            news_items=news_data["news_items"],
            focus_sectors=self.focus_sectors
        )
        
        # 调用 Claude（自动处理 Function Calling）
        print(f"[分析引擎] 调用 Claude API (Function Calling {'启用' if self.enable_function_calling else '禁用'})...")
        ai_response = self.call_llm_api(prompt)
        
        # 优先使用 Function Calling 返回的结构化数据
        if self.sector_impact_results:
            # 从 Function Calling 结果构建分析结果
            analysis_result = self._build_result_from_function_calls(ai_response)
        else:
            # 降级：解析 AI 响应文本
            analysis_result = MarketImpactScorer.parse_analysis_result(ai_response)
        
        # 计算情绪
        sentiment = MarketImpactScorer.calculate_overall_sentiment(
            analysis_result.sector_impacts
        )
        
        print(f"[分析引擎] 分析完成 - 情绪: {sentiment['sentiment']}")
        print(f"[分析引擎] 调用了 {len(self.function_results)} 个函数: {list(self.function_results.keys())}")
        
        return {
            "analysis_result": analysis_result,
            "date": news_data["date"],
            "sentiment": sentiment,
            "function_results": self.function_results  # 包含函数调用结果
        }
    
    def _build_result_from_function_calls(self, ai_response: str) -> "MarketAnalysisResult":
        """从 Function Calling 结果构建分析结果"""
        from .market_scorer import MarketAnalysisResult, SectorImpact
        
        # 构建板块影响列表
        sector_impacts = []
        for impact_data in self.sector_impact_results:
            sector_impacts.append(SectorImpact(
                sector=impact_data.get("sector", "未知"),
                direction=impact_data.get("direction", "中性"),
                score=impact_data.get("impact_score", 5),
                confidence=impact_data.get("confidence", "中"),
                reason=impact_data.get("reasoning", "")
            ))
        
        # 尝试从文本响应中提取建议
        short_term = ""
        medium_term = ""
        risk_warning = ""
        key_points = []
        
        if ai_response:
            # 尝试解析文本中的建议
            import re
            
            # 提取核心要点 - 支持多种格式
            points_patterns = [
                r'(?:^|\n)\d+\.\s*\*\*(.+?)\*\*\s*[-:：]\s*(.+?)(?=\n\d+\.|\n##|\Z)',
                r'(?:^|\n)\d+\.\s*(.+?)[：:]\s*(.+?)(?=\n\d+\.|\n##|\Z)',
            ]
            for pattern in points_patterns:
                for m in re.finditer(pattern, ai_response, re.DOTALL):
                    event = m.group(1).strip()
                    impact = m.group(2).strip()
                    key_points.append(f"{event}: {impact}")
                if key_points:
                    break
            
            # 提取投资建议 - 支持多种格式
            short_patterns = [
                r'\*\*短期[（(]1-3天[)）]\*\*[：:]\s*(.+?)(?=\n\*\*|\n##|$)',
                r'###?\s*短期[（(]1-3天[)）]\s*\n+(.+?)(?=\n###?|\n##|$)',
                r'短期[（(]1-3天[)）][：:]\s*(.+?)(?=\n|$)',
            ]
            for pattern in short_patterns:
                short_match = re.search(pattern, ai_response, re.DOTALL)
                if short_match:
                    short_term = short_match.group(1).strip()
                    break
            
            medium_patterns = [
                r'\*\*中期[（(]1-2周[)）]\*\*[：:]\s*(.+?)(?=\n\*\*|\n##|$)',
                r'###?\s*中期[（(]1-2周[)）]\s*\n+(.+?)(?=\n###?|\n##|$)',
                r'中期[（(]1-2周[)）][：:]\s*(.+?)(?=\n|$)',
            ]
            for pattern in medium_patterns:
                medium_match = re.search(pattern, ai_response, re.DOTALL)
                if medium_match:
                    medium_term = medium_match.group(1).strip()
                    break
            
            risk_patterns = [
                r'\*\*风险提示\*\*[：:]\s*(.+?)(?=\n##|$)',
                r'###?\s*风险提示\s*\n+(.+?)(?=\n###?|\n##|$)',
                r'风险提示[：:]\s*(.+?)(?=\n##|$)',
            ]
            for pattern in risk_patterns:
                risk_match = re.search(pattern, ai_response, re.DOTALL)
                if risk_match:
                    risk_warning = risk_match.group(1).strip()
                    break
        
        # 如果没有提取到核心要点，从板块分析中生成
        if not key_points and sector_impacts:
            for impact in sector_impacts[:5]:
                reason_short = impact.reason[:80] + "..." if len(impact.reason) > 80 else impact.reason
                key_points.append(f"{impact.sector}板块 - {impact.direction}: {reason_short}")
        
        # 如果没有提取到投资建议，基于板块分析自动生成
        if not short_term and sector_impacts:
            bullish_sectors = [s for s in sector_impacts if s.direction == "利好" and s.score >= 7]
            bearish_sectors = [s for s in sector_impacts if s.direction == "利空" and s.score >= 7]
            
            advices = []
            if bullish_sectors:
                sectors_str = "、".join([s.sector for s in bullish_sectors[:2]])
                advices.append(f"1. **关注{sectors_str}板块**：短期有利好支撑，可适当关注相关龙头标的")
            if bearish_sectors:
                sectors_str = "、".join([s.sector for s in bearish_sectors[:2]])
                advices.append(f"{len(advices)+1}. **规避{sectors_str}板块风险**：短期存在利空因素，建议谨慎操作")
            if not advices:
                advices.append("1. **关注市场情绪变化**：当前市场信号混杂，建议谨慎操作，控制仓位")
            
            short_term = "\n".join(advices)
        
        if not medium_term and sector_impacts:
            high_conf_sectors = [s for s in sector_impacts if s.confidence == "高"]
            
            advices = []
            if high_conf_sectors:
                for i, s in enumerate(high_conf_sectors[:2], 1):
                    advices.append(f"{i}. **{s.sector}板块**：{s.reason[:60]}...")
            if not advices:
                advices.append("1. **持续跟踪热点**：关注政策面和资金面变化，灵活调整持仓")
            
            medium_term = "\n".join(advices)
        
        if not risk_warning and sector_impacts:
            risks = []
            for s in sector_impacts:
                if s.score >= 6:
                    if "估值" in s.reason or "泡沫" in s.reason:
                        risks.append(f"1. **{s.sector}板块估值风险**：需警惕短期回调压力")
                    if "政策" in s.reason or "监管" in s.reason:
                        risks.append(f"{len(risks)+1}. **政策不确定性**：关注相关政策动向")
            if not risks:
                risks.append("1. **市场波动风险**：市场有风险，投资需谨慎")
            
            risk_warning = "\n".join(risks[:3])
        
        return MarketAnalysisResult(
            key_points=key_points if key_points else ["基于热点新闻的市场分析"],
            sector_impacts=sector_impacts,
            short_term_advice=short_term or "关注市场情绪变化，谨慎操作",
            medium_term_advice=medium_term or "持续跟踪热点板块发展",
            risk_warning=risk_warning or "市场有风险，投资需谨慎",
            raw_content=ai_response
        )
    
    def analyze_and_generate_report(
        self,
        news_md_path: str,
        output_dir: str,
        save: bool = True
    ) -> Optional[str]:
        """
        分析新闻并生成报告
        
        Args:
            news_md_path: 新闻 Markdown 文件路径
            output_dir: 输出目录
            save: 是否保存文件
            
        Returns:
            生成的报告文件路径（save=True 时）或报告内容（save=False 时）
        """
        # 执行分析
        result = self.analyze_news_file(news_md_path)
        
        # 生成报告
        report_content = AnalysisReportGenerator.generate_report(
            analysis_result=result["analysis_result"],
            date=result["date"]
        )
        
        if save:
            # 从核心要点提取关键词用于文件名
            keyword = AnalysisReportGenerator.extract_filename_keyword(
                result["analysis_result"].key_points
            )
            filename = f"{result['date']}-{keyword}.md"
            
            # 保存 Markdown 报告
            file_path = AnalysisReportGenerator.save_report(
                report_content=report_content,
                output_dir=output_dir,
                date=result["date"],
                filename=filename
            )
            print(f"[分析引擎] Markdown 报告已保存: {file_path}")
            
            # 保存 JSON 数据（包含函数调用结果）
            self._save_json_data(result, output_dir)
            
            return file_path
        else:
            return report_content
    
    def _save_json_data(self, analysis_result: Dict, output_dir: str):
        """保存 JSON 结构化数据"""
        try:
            from pathlib import Path
            import json
            
            date = analysis_result["date"]
            year = date[:4]
            month = date[5:7]
            
            json_dir = Path(output_dir).parent.parent.parent / "output" / "analysis_data" / year / month
            json_dir.mkdir(parents=True, exist_ok=True)
            
            json_file = json_dir / f"{date}-analysis.json"
            
            # 构建 JSON 数据
            json_data = {
                "date": date,
                "sentiment": analysis_result["sentiment"],
                "function_calls": self.function_results,
                "sector_impacts": [
                    {
                        "sector": impact.sector,
                        "direction": impact.direction,
                        "score": impact.score,
                        "confidence": impact.confidence,
                        "reason": impact.reason
                    }
                    for impact in analysis_result["analysis_result"].sector_impacts
                ]
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"[分析引擎] JSON 数据已保存: {json_file}")
            
        except Exception as e:
            print(f"[分析引擎] JSON 保存失败: {e}")
    
    def batch_analyze_news_dir(
        self,
        news_dir: str,
        output_dir: str,
        pattern: str = "*.md",
        limit: int = None
    ) -> List[str]:
        """
        批量分析新闻目录
        
        Args:
            news_dir: 新闻目录路径
            output_dir: 输出目录
            pattern: 文件匹配模式
            limit: 限制处理文件数量
            
        Returns:
            生成的报告文件路径列表
        """
        news_files = list(Path(news_dir).rglob(pattern))
        
        if limit:
            news_files = news_files[:limit]
        
        print(f"[分析引擎] 找到 {len(news_files)} 个新闻文件")
        
        report_paths = []
        for news_file in news_files:
            try:
                report_path = self.analyze_and_generate_report(
                    news_md_path=str(news_file),
                    output_dir=output_dir
                )
                report_paths.append(report_path)
            except Exception as e:
                print(f"[分析引擎] 处理失败 {news_file}: {e}")
                continue
        
        print(f"[分析引擎] 批量分析完成，生成 {len(report_paths)} 份报告")
        return report_paths
