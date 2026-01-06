# coding=utf-8
"""
Function Calling 工具定义

定义所有可供 LLM 调用的函数及其 JSON Schema
"""

from typing import Dict, List
from .market_data import MarketDataProvider
from .technical import TechnicalAnalyzer


class FunctionToolRegistry:
    """Function Calling 工具注册表"""
    
    # ==================== 工具定义 ====================
    
    TOOLS = [
        # 1. 板块影响评估（结构化输出）
        {
            "type": "function",
            "function": {
                "name": "evaluate_sector_impact",
                "strict": True,
                "description": "评估新闻对特定市场板块的影响，返回结构化评分数据",
                "parameters": {
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
                            "minimum": 1,
                            "maximum": 10,
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
                            "description": "相关股票代码列表（可选）"
                        }
                    },
                    "required": ["sector", "direction", "impact_score", "confidence", "reasoning"],
                    "additionalProperties": False
                }
            }
        },
        
        # 2. 获取股票实时价格
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "获取指定股票的实时价格和涨跌幅数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码（A股6位数字，如000001；美股字母代码，如NVDA）"
                        },
                        "market": {
                            "type": "string",
                            "enum": ["CN-A", "US", "HK"],
                            "default": "CN-A",
                            "description": "市场类型：CN-A(A股), US(美股), HK(港股)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 3. 获取指数数据
        {
            "type": "function",
            "function": {
                "name": "get_index_price",
                "description": "获取股票指数的实时数据",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "指数代码（如 000001=上证指数, 399001=深证成指, 399006=创业板指）"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 4. 计算技术指标 - RSI
        {
            "type": "function",
            "function": {
                "name": "calculate_rsi",
                "description": "计算股票的RSI（相对强弱指标），判断超买超卖状态",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码"
                        },
                        "period": {
                            "type": "integer",
                            "default": 14,
                            "description": "RSI周期，默认14天"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 5. 计算技术指标 - MACD
        {
            "type": "function",
            "function": {
                "name": "calculate_macd",
                "description": "计算MACD指标，判断金叉死叉信号",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 6. 计算移动平均线
        {
            "type": "function",
            "function": {
                "name": "calculate_ma",
                "description": "计算股票的移动平均线（MA），分析趋势",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码"
                        },
                        "period": {
                            "type": "integer",
                            "default": 5,
                            "description": "MA周期：5(短期), 20(中期), 60(长期)"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 7. 综合技术分析
        {
            "type": "function",
            "function": {
                "name": "comprehensive_analysis",
                "description": "对股票进行综合技术分析，包含多个指标的综合评分",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码"
                        }
                    },
                    "required": ["symbol"]
                }
            }
        },
        
        # 8. 搜索股票
        {
            "type": "function",
            "function": {
                "name": "search_stock",
                "description": "根据关键词搜索股票，返回匹配的股票列表",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词（股票名称或代码）"
                        },
                        "market": {
                            "type": "string",
                            "enum": ["CN-A", "US", "HK"],
                            "default": "CN-A",
                            "description": "市场类型"
                        }
                    },
                    "required": ["keyword"]
                }
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
                period=arguments.get("period", 14)
            )
        
        # 计算 MACD
        elif function_name == "calculate_macd":
            return TechnicalAnalyzer.calculate_macd(
                symbol=arguments["symbol"]
            )
        
        # 计算 MA
        elif function_name == "calculate_ma":
            return TechnicalAnalyzer.calculate_ma(
                symbol=arguments["symbol"],
                period=arguments.get("period", 5)
            )
        
        # 综合技术分析
        elif function_name == "comprehensive_analysis":
            return TechnicalAnalyzer.comprehensive_analysis(
                symbol=arguments["symbol"]
            )
        
        # 搜索股票
        elif function_name == "search_stock":
            return MarketDataProvider.search_stock_by_name(
                keyword=arguments["keyword"],
                market=arguments.get("market", "CN-A")
            )
        
        else:
            return {"error": f"未知函数: {function_name}"}
    
    @classmethod
    def get_tools(cls) -> List[Dict]:
        """获取所有工具定义"""
        return cls.TOOLS
    
    @classmethod
    def get_tool_names(cls) -> List[str]:
        """获取所有工具名称"""
        return [tool["function"]["name"] for tool in cls.TOOLS]
