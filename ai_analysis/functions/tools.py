# coding=utf-8
"""
Function Calling 工具定义

定义所有可供 Anthropic Claude 调用的函数及其 JSON Schema
使用 Anthropic 工具格式：https://docs.anthropic.com/en/docs/tool-use
"""

from typing import Dict, List
from .market_data import MarketDataProvider
from .technical import TechnicalAnalyzer

# 导入大盘复盘模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_analysis.market_overview import MarketOverviewProvider


class FunctionToolRegistry:
    """Function Calling 工具注册表（Anthropic Claude 格式）"""
    
    # ==================== 工具定义（Anthropic 格式） ====================
    
    TOOLS = [
        # 1. 板块影响评估（结构化输出）
        {
            "name": "evaluate_sector_impact",
            "description": "评估新闻对特定市场板块的影响，返回结构化评分数据",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sector": {
                        "type": "string",
                        "enum": ["科技", "金融", "消费", "医疗", "能源", "工业", "房地产"],
                        "description": "板块名称"
                    },
                    "direction": {
                        "type": "string",
                        "enum": ["利好", "利空", "中性"],
                        "description": "影响方向"
                    },
                    "impact_score": {
                        "type": "integer",
                        "description": "影响程度评分（1-10）"
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["高", "中", "低"],
                        "description": "评估置信度"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "影响评估的详细理由"
                    },
                    "related_stocks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "相关股票代码列表，格式如：A股6位数字(000001)、港股5位数字(00700)、美股字母代码(NVDA)"
                    }
                },
                "required": ["sector", "direction", "impact_score", "confidence", "reasoning", "related_stocks"]
            }
        },
        
        # 2. 获取股票实时价格
        {
            "name": "get_stock_price",
            "description": "获取指定股票的实时价格和涨跌幅数据",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码（A股6位数字，如000001；美股字母代码，如NVDA）"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型：CN-A(A股), US(美股), HK(港股)，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 3. 获取指数数据
        {
            "name": "get_index_price",
            "description": "获取股票指数的实时数据",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "指数代码（如 000001=上证指数, 399001=深证成指, 399006=创业板指）"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 4. 计算技术指标 - RSI
        {
            "name": "calculate_rsi",
            "description": "计算股票的RSI（相对强弱指标），判断超买超卖状态，支持A股/美股/港股",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "period": {
                        "type": "integer",
                        "description": "RSI周期，默认14天"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 5. 计算技术指标 - MACD
        {
            "name": "calculate_macd",
            "description": "计算MACD指标，判断金叉死叉信号，支持A股/美股/港股",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 6. 计算移动平均线
        {
            "name": "calculate_ma",
            "description": "计算股票的移动平均线（MA），分析趋势，支持A股/美股/港股",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "period": {
                        "type": "integer",
                        "description": "MA周期：5(短期), 20(中期), 60(长期)，默认5"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 7. 综合技术分析
        {
            "name": "comprehensive_analysis",
            "description": "对股票进行综合技术分析，包含多个指标的综合评分，支持A股/美股/港股",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 8. 搜索股票
        {
            "name": "search_stock",
            "description": "根据关键词搜索股票，返回匹配的股票列表",
            "input_schema": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（股票名称或代码）"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["keyword"]
            }
        },
        
        # ==================== 新增工具（参考 daily_stock_analysis）====================
        
        # 9. 大盘复盘
        {
            "name": "get_market_overview",
            "description": "获取当日大盘复盘数据，包括主要指数、涨跌统计、资金流向、板块表现",
            "input_schema": {
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型：CN-A(A股)、US(美股)、HK(港股)，默认HK"
                    }
                },
                "required": []
            }
        },
        
        # 10. 乖离率计算
        {
            "name": "calculate_bias",
            "description": "计算股票乖离率(BIAS)，判断是否处于追高风险区域。乖离率<2%为最佳买点，2-5%可小仓介入，>5%严禁追高",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    },
                    "period": {
                        "type": "integer",
                        "description": "均线周期，默认5"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 11. 均线排列检查
        {
            "name": "check_ma_alignment",
            "description": "检查股票均线排列状态。多头排列(MA5>MA10>MA20)表示趋势向上，空头排列表示趋势向下",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 12. 趋势综合评分
        {
            "name": "calculate_trend_score",
            "description": "计算股票趋势综合评分(0-100分)，包含均线排列、乖离率、量能、RSI、MACD五个维度的评分和检查清单",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 13. 增强行情数据
        {
            "name": "get_realtime_quote",
            "description": "获取股票实时行情增强数据，包括量比、换手率、市盈率、市净率、市值等",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码"
                    },
                    "market": {
                        "type": "string",
                        "enum": ["CN-A", "US", "HK"],
                        "description": "市场类型，默认HK"
                    }
                },
                "required": ["symbol"]
            }
        },
        
        # 14. 筹码分布（仅A股）
        {
            "name": "get_chip_distribution",
            "description": "获取A股股票筹码分布数据，包括获利比例、平均成本、集中度、筹码状态",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "A股股票代码"
                    }
                },
                "required": ["symbol"]
            }
        }
    ]
    
    # ==================== 函数执行器 ====================
    
    @staticmethod
    def execute_function(function_name: str, arguments: Dict) -> Dict:
        """
        执行函数调用
        
        Args:
            function_name: 函数名称
            arguments: 函数参数（JSON对象）
            
        Returns:
            函数执行结果
        """
        # 板块影响评估（结构化输出，直接返回参数）
        if function_name == "evaluate_sector_impact":
            return arguments
        
        # 获取股票价格
        elif function_name == "get_stock_price":
            return MarketDataProvider.get_stock_price(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 获取指数价格
        elif function_name == "get_index_price":
            return MarketDataProvider.get_index_price(
                symbol=arguments["symbol"]
            )
        
        # 计算 RSI
        elif function_name == "calculate_rsi":
            return TechnicalAnalyzer.calculate_rsi(
                symbol=arguments["symbol"],
                period=arguments.get("period", 14),
                market=arguments.get("market", "CN-A")
            )
        
        # 计算 MACD
        elif function_name == "calculate_macd":
            return TechnicalAnalyzer.calculate_macd(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 计算 MA
        elif function_name == "calculate_ma":
            return TechnicalAnalyzer.calculate_ma(
                symbol=arguments["symbol"],
                period=arguments.get("period", 5),
                market=arguments.get("market", "CN-A")
            )
        
        # 综合技术分析
        elif function_name == "comprehensive_analysis":
            return TechnicalAnalyzer.comprehensive_analysis(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 搜索股票
        elif function_name == "search_stock":
            return MarketDataProvider.search_stock_by_name(
                keyword=arguments["keyword"],
                market=arguments.get("market", "CN-A")
            )
        
        # ====== 新增函数 ======
        
        # 大盘复盘
        elif function_name == "get_market_overview":
            overview = MarketOverviewProvider.get_market_overview(
                market=arguments.get("market", "CN-A")
            )
            # 转换为字典格式
            return {
                "market": overview.market,
                "date": overview.date,
                "indices": [{"code": i.code, "name": i.name, "current": i.current, "change_pct": i.change_pct} for i in overview.indices],
                "up_count": overview.up_count,
                "down_count": overview.down_count,
                "limit_up_count": overview.limit_up_count,
                "limit_down_count": overview.limit_down_count,
                "total_amount": overview.total_amount,
                "north_flow": overview.north_flow,
                "south_flow": overview.south_flow,
                "top_sectors": [{"name": s.name, "change_pct": s.change_pct} for s in overview.top_sectors],
                "bottom_sectors": [{"name": s.name, "change_pct": s.change_pct} for s in overview.bottom_sectors]
            }
        
        # 乖离率
        elif function_name == "calculate_bias":
            return TechnicalAnalyzer.calculate_bias(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A"),
                period=arguments.get("period", 5)
            )
        
        # 均线排列
        elif function_name == "check_ma_alignment":
            return TechnicalAnalyzer.check_ma_alignment(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 趋势评分
        elif function_name == "calculate_trend_score":
            return TechnicalAnalyzer.calculate_trend_score(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 增强行情
        elif function_name == "get_realtime_quote":
            return MarketDataProvider.get_realtime_quote(
                symbol=arguments["symbol"],
                market=arguments.get("market", "CN-A")
            )
        
        # 筹码分布
        elif function_name == "get_chip_distribution":
            return MarketDataProvider.get_chip_distribution(
                symbol=arguments["symbol"]
            )
        
        else:
            return {"error": f"未知函数: {function_name}"}
    
    @classmethod
    def get_tools(cls) -> List[Dict]:
        """获取所有工具定义（Anthropic 格式）"""
        return cls.TOOLS
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """获取所有工具名称"""
        return [tool["name"] for tool in cls.TOOLS]
