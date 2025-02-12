class CapitalPromptGenerator:
    """Generate prompts for capital analysis."""
    
    @staticmethod
    def generate_prompt(analysis_data: Dict[str, Any]) -> str:
        """Generate analysis prompt.
        
        Args:
            analysis_data: Dictionary containing analysis data
            
        Returns:
            Analysis prompt
        """
        # Extract data
        stock_id = analysis_data["stock_id"]
        margin = analysis_data.get("margin", {})
        institutional = analysis_data.get("institutional", {})
        shareholding = analysis_data.get("shareholding", {})
        price = analysis_data.get("price", {})
        
        # Format prompt
        prompt = f"""請分析 {stock_id} 的籌碼面狀況。

市場資料：
1. 股價：
   - 收盤價: {price.get('close', 'N/A')}
   - 漲跌: {price.get('change', 'N/A')}
   - 成交量: {price.get('volume', 'N/A')}
   - 成交量變化: {price.get('volume_change', 'N/A')}

2. 融資融券：
   - 融資餘額: {margin.get('margin_balance', 'N/A')}
   - 融資變化: {margin.get('margin_change', 'N/A')}
   - 融券餘額: {margin.get('short_balance', 'N/A')}
   - 融券變化: {margin.get('short_change', 'N/A')}

3. 三大法人：
   - 外資買賣超: {institutional.get('foreign_buy_sell', 'N/A')}
   - 外資變化: {institutional.get('foreign_change', 'N/A')}
   - 投信買賣超: {institutional.get('trust_buy_sell', 'N/A')}
   - 投信變化: {institutional.get('trust_change', 'N/A')}
   - 自營商買賣超: {institutional.get('dealer_buy_sell', 'N/A')}
   - 自營商變化: {institutional.get('dealer_change', 'N/A')}

4. 持股分布：
   - 外資持股比例: {shareholding.get('foreign_ratio', 'N/A')}
   - 外資持股變化: {shareholding.get('foreign_ratio_change', 'N/A')}
   - 外資持股數: {shareholding.get('foreign_shares', 'N/A')}
   - 外資持股數變化: {shareholding.get('foreign_shares_change', 'N/A')}

請根據以上資料，分析：
1. 主力籌碼動向
2. 法人態度
3. 融資融券變化
4. 整體籌碼面評估

請以中文回答，並提供具體數據支持你的分析。"""

        return prompt 