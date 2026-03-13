#!/usr/bin/env python3
"""LLM服务层 - 云端API集成"""

import os
import json
import logging
from typing import Dict, List, Optional
import openai

logger = logging.getLogger(__name__)

class OpenAIService:
    """OpenAI兼容API服务（支持OpenAI和OpenRouter）"""
    
    def __init__(self, config: Dict):
        """初始化API服务"""
        self.config = config
        
        # 根据配置选择API提供商
        api_provider = config.get('api_provider', 'openai')
        
        if api_provider == 'openrouter':
            self.api_key = config.get('openrouter_api_key') or os.getenv('OPENROUTER_API_KEY')
            self.base_url = config.get('base_url', 'https://openrouter.ai/api/v1/')
            if not self.api_key:
                raise ValueError("OpenRouter API密钥未配置")
        elif api_provider == 'openai':
            self.api_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
            self.base_url = config.get('base_url', 'https://api.openai.com/v1')
            if not self.api_key:
                raise ValueError("OpenAI API密钥未配置")
        else:
            raise ValueError(f"不支持的API提供商: {api_provider}")
        
        # 保存配置参数
        self.api_provider = api_provider
        self.model = config.get('model', 'gpt-4')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
        
        # 配置OpenAI库
        openai.api_key = self.api_key
        if self.api_provider == 'openrouter':
            openai.api_base = self.base_url
        
        logger.info(f"API服务初始化成功，提供商: {api_provider}, 模型: {self.model}")
    
    def analyze_stock(self, query: str, analysis_data: Dict) -> Dict:
        """使用LLM分析股票数据"""
        try:
            # 构建提示词
            prompt = self._build_stock_analysis_prompt(query, analysis_data)
            
            # 调用API (使用旧版本OpenAI API)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的股票分析师，擅长技术分析、基本面分析和市场情绪分析。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                # 注意：旧版本不支持response_format参数，需要在提示词中要求返回JSON
            )
            
            # 解析响应
            result = json.loads(response['choices'][0]['message']['content'])
            logger.info("LLM股票分析完成")
            return result
            
        except Exception as e:
            logger.error(f"LLM分析失败: {str(e)}")
            return {"error": f"分析失败: {str(e)}"}
    
    def _build_stock_analysis_prompt(self, query: str, analysis_data: Dict) -> str:
        """构建股票分析提示词"""
        technical_analysis = analysis_data.get('technical_analysis', {})
        fundamental_data = analysis_data.get('fundamental_data', {})
        market_sentiment = analysis_data.get('market_sentiment', {})
        
        prompt = f"""
请基于以下数据对股票进行综合分析，并回答用户的查询：{query}

## 技术分析数据
{json.dumps(technical_analysis, indent=2, ensure_ascii=False)}

## 基本面数据
{json.dumps(fundamental_data, indent=2, ensure_ascii=False)}

## 市场情绪
{json.dumps(market_sentiment, indent=2, ensure_ascii=False)}

请以JSON格式返回分析结果，包含以下字段：
1. analysis_summary: 综合分析总结
2. technical_insights: 技术面见解
3. fundamental_insights: 基本面见解  
4. sentiment_insights: 市场情绪见解
5. investment_recommendation: 投资建议（买入/持有/卖出）
6. confidence_level: 置信度（高/中/低）
7. risk_assessment: 风险评估
8. time_horizon: 建议持有期限

请确保分析专业、客观，并基于提供的数据进行推理。
"""
        
        return prompt

class LLMQueryProcessor:
    """LLM查询处理器"""
    
    def __init__(self, config: Dict):
        """初始化查询处理器"""
        self.llm_service = OpenAIService(config)
        
    def process_natural_language_query(self, query: str, stock_code: str, 
                                     analysis_data: Dict) -> Dict:
        """处理自然语言查询"""
        logger.info(f"处理自然语言查询: {query}, 股票: {stock_code}")
        
        try:
            # 使用LLM进行分析
            result = self.llm_service.analyze_stock(query, analysis_data)
            
            if 'error' in result:
                return result
            
            # 添加元数据
            result['query'] = query
            result['stock_code'] = stock_code
            result['analysis_timestamp'] = analysis_data.get('timestamp')
            
            return result
            
        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")
            return {"error": f"查询处理失败: {str(e)}"}

def get_llm_processor(config: Optional[Dict] = None) -> LLMQueryProcessor:
    """获取LLM处理器实例"""
    if config is None:
        from config.llm_config import get_llm_config
        config_obj = get_llm_config()
        config = config_obj.get_config()
    
    return LLMQueryProcessor(config)