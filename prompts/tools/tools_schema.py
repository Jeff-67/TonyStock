"""Module defining schema and configuration for analysis tools."""


def tool_prompt_construct_anthropic() -> list:
    """Construct tool configuration for Anthropic models.

    Returns:
        dict: Tool configuration dictionary containing integrated research and technical analysis tools.
    """
    return [
        {
            "name": "research",
            "description": """Strategic news and market research tool that generates structured queries and returns comprehensive analysis results.

Key Features:
1. Systematic Research Framework:
   - Company-specific analysis (fundamentals, news, developments)
   - Industry chain analysis (upstream/downstream dynamics)
   - Market environment analysis (macro factors, regulations)
   - Competitive landscape analysis

2. Multi-source Integration:
   - News and press releases
   - Financial reports and filings
   - Industry reports and analysis
   - Expert opinions and market commentary
   - Social media and market sentiment

3. Temporal Analysis:
   - Historical development tracking
   - Current situation analysis
   - Future outlook and projections
   - Event timeline construction

4. Risk Assessment:
   - Operational risks
   - Market risks
   - Technology risks
   - Regulatory risks
   - Competition risks

Output Format:
[{
    "query": {
        "query": str,           # The actual search query
        "core_question": str,   # Which core question this addresses
        "purpose": str,         # What information we're looking for
        "expected_insights": str, # Expected insights from this query
        "reasoning": str,       # Why this query is relevant
        "category": str         # Analysis category (company/industry/market)
    },
    "search_results": [{
        "url": str,            # Source URL
        "title": str,          # Article/source title
        "date": str,           # Publication date
        "source_type": str,    # Type of source (news/report/filing)
        "reliability": float,  # Source reliability score
        "context": str,        # Relevant content
        "key_points": List[str] # Main takeaways
    }],
    "analysis": {
        "summary": str,        # High-level summary
        "impact": {
            "short_term": str,  # Short-term implications
            "long_term": str    # Long-term implications
        },
        "confidence": float,   # Analysis confidence score
        "related_factors": List[str] # Related market factors
    }
}]""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to research (e.g., '群聯', '京鼎')",
                    },
                    "user_message": {
                        "type": "string",
                        "description": "User's specific research request or focus area",
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis to perform (company, industry, market, comprehensive)",
                        "default": "comprehensive"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range for analysis (1d, 1w, 1m, 3m, 6m, 1y)",
                        "default": "1m"
                    }
                },
                "required": ["company_name", "user_message"],
            },
        },
        {
            "name": "chip_analysis",
            "description": """Professional semiconductor industry analysis tool providing comprehensive chip industry chain analysis.

Key Features:
1. Industry Chain Analysis:
   - Upstream: IP Providers, EDA Tool Vendors, Foundries
   - Midstream: IC Design, Packaging & Testing
   - Downstream: End Applications Market
   - Supply Chain Relationship Mapping

2. Technical Analysis:
   - Process Technology Development Tracking
   - Advanced Packaging Technology Analysis
   - Design Tool Evolution
   - Technical Barrier Assessment
   - Patent Portfolio Analysis

3. Market Analysis:
   - Market Size Forecast
   - Market Share Analysis
   - Competitive Landscape
   - Price Trends
   - Supply-Demand Balance

4. Application Domain Analysis:
   - Computing Chips (CPU/GPU/NPU/DPU)
   - Memory (DRAM/NAND/NOR)
   - Mobile Chips
   - Automotive Electronics
   - Industrial Applications
   - AI Accelerators

5. Capacity Analysis:
   - Capacity Utilization
   - Expansion Plan Tracking
   - Investment Amount Statistics
   - Yield Status
   - Capacity Bottleneck Analysis

6. Innovation Technology Tracking:
   - Advanced Process Development
   - New Material Applications
   - New Architecture Design
   - Heterogeneous Integration
   - Emerging Application Areas

7. Risk Assessment:
   - Technical Risks
   - Supply Chain Risks
   - Geopolitical Risks
   - Capacity Risks
   - Market Risks

Output Format:
{
    "industry_chain": {
        "upstream": {
            "ip_providers": List[str],
            "eda_vendors": List[str],
            "foundries": List[str]
        },
        "midstream": {
            "ic_design": List[str],
            "packaging_testing": List[str]
        },
        "downstream": {
            "applications": List[str],
            "end_markets": List[str]
        }
    },
    "technical_analysis": {
        "process_node": {
            "current": str,
            "next_gen": str,
            "timeline": str
        },
        "packaging": {
            "technologies": List[str],
            "capabilities": dict
        },
        "design_tools": {
            "current_gen": str,
            "limitations": List[str]
        },
        "patents": {
            "key_areas": List[str],
            "strength": float
        }
    },
    "market_analysis": {
        "market_size": {
            "current": float,
            "growth_rate": float,
            "forecast": dict
        },
        "market_share": {
            "company": float,
            "competitors": dict
        },
        "pricing_trends": {
            "current": str,
            "forecast": str
        }
    },
    "application_analysis": {
        "computing": {
            "cpu": dict,
            "gpu": dict,
            "npu": dict,
            "dpu": dict
        },
        "memory": {
            "dram": dict,
            "nand": dict,
            "nor": dict
        },
        "mobile": dict,
        "automotive": dict,
        "industrial": dict,
        "ai_accelerator": dict
    },
    "capacity_analysis": {
        "utilization_rate": float,
        "expansion_plans": List[dict],
        "investment": {
            "amount": float,
            "timeline": str
        },
        "yield_rate": {
            "current": float,
            "target": float
        }
    },
    "innovation_tracking": {
        "advanced_process": {
            "status": str,
            "challenges": List[str]
        },
        "new_materials": List[str],
        "architectures": List[str],
        "integration": {
            "technologies": List[str],
            "progress": str
        }
    },
    "risk_assessment": {
        "technical_risks": List[str],
        "supply_chain_risks": List[str],
        "geopolitical_risks": List[str],
        "capacity_risks": List[str],
        "market_risks": List[str]
    }
}""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the semiconductor company to analyze",
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Analysis type (industry_chain, technical, market, application, capacity, innovation, risk, comprehensive)",
                        "default": "comprehensive"
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Specific focus area (computing, memory, mobile, automotive, industrial, ai)",
                        "default": "all"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Analysis time range (1m, 3m, 6m, 1y)",
                        "default": "3m"
                    }
                },
                "required": ["company_name"],
            },
        },
        {
            "name": "technical_analysis",
            "description": """Comprehensive technical analysis tool using TA-Lib for advanced market analysis and trading signals.

Key Features:
1. Multi-timeframe Trend Analysis:
   - Primary trend (daily/weekly/monthly)
   - Secondary trend (intermediate)
   - Short-term trend (intraday)
   - Trend strength and reliability metrics

2. Advanced Momentum Analysis:
   - RSI with overbought/oversold signals
   - MACD with signal line crossovers
   - Stochastic oscillator (fast/slow)
   - ROC (Rate of Change)
   - MFI (Money Flow Index)

3. Enhanced Volatility Measures:
   - ATR with volatility bands
   - Bollinger Bands with %B
   - Keltner Channels
   - Standard Deviation
   - Historical Volatility

4. Volume Analysis:
   - OBV (On Balance Volume)
   - Volume Force Index
   - Chaikin Money Flow
   - Volume Weighted Average Price (VWAP)
   - Accumulation/Distribution Line

5. Pattern Recognition:
   - Candlestick patterns
   - Chart patterns (Head & Shoulders, Double Top/Bottom)
   - Fibonacci retracements
   - Elliott Wave patterns
   - Harmonic patterns

6. Support/Resistance Analysis:
   - Dynamic support/resistance levels
   - Pivot points (Standard, Fibonacci, Camarilla)
   - Price clusters
   - Historical price levels
   - Moving average crossovers

7. Market Breadth Indicators:
   - Advance/Decline ratio
   - New Highs vs New Lows
   - Arms Index (TRIN)
   - McClellan Oscillator

8. Risk Analysis:
   - Position sizing recommendations
   - Stop loss levels
   - Risk/Reward ratios
   - Maximum drawdown analysis
   - Volatility-based position sizing

9. Integration with Fundamental Analysis:
   - Technical vs Fundamental alignment check
   - Event impact analysis
   - News correlation analysis
   - Volume-news relationship
   - Institutional activity patterns

Output Format:
{
    "trend_analysis": {
        "overall_trend": str,
        "trend_strength": float,
        "moving_averages": {
            "SMA_20": float,
            "SMA_50": float,
            "SMA_200": float,
            "EMA_13": float,
            "EMA_21": float,
            "EMA_55": float
        },
        "trend_reliability": float
    },
    "momentum_indicators": {
        "RSI": {
            "value": float,
            "signal": str,
            "divergence": str
        },
        "MACD": {
            "macd": float,
            "signal": float,
            "histogram": float,
            "crossover_signal": str
        },
        "Stochastic": {
            "fastK": float,
            "fastD": float,
            "slowK": float,
            "slowD": float,
            "signal": str
        },
        "ROC": float,
        "MFI": float
    },
    "volatility_indicators": {
        "ATR": {
            "value": float,
            "percentile": float
        },
        "Bollinger_Bands": {
            "upper": float,
            "middle": float,
            "lower": float,
            "bandwidth": float,
            "%B": float
        },
        "Keltner_Channels": {
            "upper": float,
            "middle": float,
            "lower": float
        }
    },
    "volume_analysis": {
        "OBV": {
            "value": float,
            "trend": str
        },
        "Force_Index": float,
        "CMF": float,
        "VWAP": float,
        "volume_trend": str
    },
    "patterns": {
        "candlestick_patterns": List[str],
        "chart_patterns": List[str],
        "fibonacci_levels": {
            "retracement": List[float],
            "extension": List[float]
        },
        "elliott_wave": {
            "current_wave": str,
            "next_target": float
        }
    },
    "support_resistance": {
        "dynamic_levels": {
            "support": List[float],
            "resistance": List[float]
        },
        "pivot_points": {
            "daily": {
                "R3": float,
                "R2": float,
                "R1": float,
                "PP": float,
                "S1": float,
                "S2": float,
                "S3": float
            }
        },
        "price_clusters": List[float]
    },
    "risk_analysis": {
        "suggested_stop_loss": float,
        "risk_reward_ratio": float,
        "position_size": {
            "recommended": float,
            "max_position": float
        },
        "max_drawdown": float
    },
    "trading_signals": {
        "short_term": str,
        "intermediate": str,
        "long_term": str,
        "confidence": float
    },
    "fundamental_correlation": {
        "news_impact": {
            "recent_events": List[str],
            "price_reaction": str,
            "volume_reaction": str
        },
        "institutional_activity": {
            "buying_pressure": float,
            "selling_pressure": float,
            "net_flow": float
        },
        "technical_fundamental_alignment": {
            "price_targets": List[float],
            "support_levels": List[float],
            "risk_levels": List[float]
        }
    }
}""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol to analyze",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data to analyze (default: 200)",
                    },
                    "timeframe": {
                        "type": "string",
                        "description": "Analysis timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)",
                        "default": "1d"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis to perform (full, trend, momentum, volatility, volume, patterns, support_resistance, risk, fundamental)",
                        "default": "full"
                    },
                    "include_fundamental": {
                        "type": "boolean",
                        "description": "Whether to include fundamental correlation analysis",
                        "default": True
                    }
                },
                "required": ["symbol"],
            },
        },
    ]


def tool_prompt_construct_openai() -> list:
    """Construct tool configuration for OpenAI models.

    Returns:
        list: List of tool configurations in OpenAI format containing search engine,
            web scraper, and other tool specifications.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "research",
                "description": """Strategic news search tool that generates structured queries and returns search results.

Key Features:
1. Generates targeted search queries based on user's request
2. Follows systematic framework covering company, industry, and market aspects
3. Returns structured results with sources and context

Output Format:
[{
    "query": {
        "query": str,           # The actual search query
        "core_question": str,   # Which core question this addresses
        "purpose": str,         # What information we're looking for
        "expected_insights": str, # Expected insights from this query
        "reasoning": str        # Why this query is relevant
    },
    "search_results": [{
        "url": str,            # Source URL
        "context": str         # Relevant content
    }]
}]""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the company to research (e.g., '群聯', '京鼎')",
                        },
                        "user_message": {
                            "type": "string",
                            "description": "User's specific research request or focus area",
                        },
                    },
                    "required": ["company_name", "user_message"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "chip_analysis",
                "description": """Professional semiconductor industry analysis tool providing comprehensive chip industry chain analysis.

Key Features:
1. Industry Chain Analysis (Upstream/Midstream/Downstream)
2. Technical Analysis (Process, Packaging, Design)
3. Market Analysis (Size, Share, Trends)
4. Application Domain Analysis (Computing, Memory, Mobile, Automotive)
5. Capacity Analysis (Utilization, Expansion, Yield)
6. Innovation Tracking (New Technologies, Materials)
7. Risk Assessment

Output Format:
{
    "industry_chain": {
        "upstream": dict,
        "midstream": dict,
        "downstream": dict
    },
    "technical_analysis": {
        "process": dict,
        "packaging": dict,
        "design": dict
    },
    "market_analysis": {
        "size": dict,
        "share": dict,
        "trends": dict
    },
    "applications": {
        "computing": dict,
        "memory": dict,
        "mobile": dict,
        "automotive": dict
    },
    "capacity": {
        "utilization": float,
        "expansion": dict,
        "yield": dict
    },
    "innovation": {
        "technologies": List[str],
        "materials": List[str]
    },
    "risks": {
        "technical": List[str],
        "market": List[str],
        "supply_chain": List[str]
    }
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the semiconductor company to analyze",
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "Analysis type (industry_chain, technical, market, application, capacity, innovation, risk, comprehensive)",
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "Specific focus area (computing, memory, mobile, automotive, industrial, ai)",
                        }
                    },
                    "required": ["company_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "technical_analysis",
                "description": """Technical analysis tool using TA-Lib to analyze stock price patterns and indicators.

Key Features:
1. Trend analysis using moving averages
2. Momentum indicators (RSI, MACD, Stochastic)
3. Volatility measures (ATR, Bollinger Bands)
4. Volume analysis and pattern recognition
5. Support/resistance level identification

Output Format:
{
    "trend_analysis": {
        "overall_trend": str,
        "moving_averages": {
            "SMA_50": float,
            "SMA_200": float,
            "EMA_20": float
        }
    },
    "momentum_indicators": {
        "RSI": float,
        "MACD": {
            "macd": float,
            "signal": float,
            "histogram": float
        },
        "Stochastic": {
            "slowK": float,
            "slowD": float
        }
    },
    "volatility_indicators": {
        "ATR": float,
        "Bollinger_Bands": {
            "upper": float,
            "middle": float,
            "lower": float
        }
    },
    "volume_indicators": {
        "OBV": float
    },
    "patterns": List[str],
    "support_resistance": {
        "support_levels": List[float],
        "resistance_levels": List[float]
    }
}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Stock symbol to analyze",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days of historical data to analyze (default: 200)",
                        },
                    },
                    "required": ["symbol"],
                },
            },
        },
    ]
