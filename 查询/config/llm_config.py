#!/usr/bin/env python3
"""LLM配置管理"""

import os
from typing import Dict, Any

class LLMConfig:
    """LLM配置类"""
    
    def __init__(self):
        self.config = {
            'api_provider': 'openrouter',  # openai 或 openrouter
            'openrouter_api_key': os.getenv('OPENROUTER_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'google/gemma-2-9b-it',  # OpenRouter模型格式
            'base_url': 'https://openrouter.ai/api/v1/',
            'max_tokens': 2000,
            'temperature': 0.3,
            'timeout': 30,
            'max_retries': 3,
            'enable_cache': True,
            'cache_ttl': 3600,  # 1小时
            'default_language': 'zh',
            'analysis_timeout': 60  # 分析超时时间(秒)
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(new_config)
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        if self.config['api_provider'] == 'openrouter':
            if not self.config['openrouter_api_key']:
                raise ValueError("OpenRouter API密钥未配置")
        elif self.config['api_provider'] == 'openai':
            if not self.config['openai_api_key']:
                raise ValueError("OpenAI API密钥未配置")
        else:
            raise ValueError("不支持的API提供商")
        
        if self.config['max_tokens'] > 4000:
            raise ValueError("max_tokens不能超过4000")
            
        if not 0 <= self.config['temperature'] <= 1:
            raise ValueError("temperature必须在0-1之间")
            
        return True

def get_llm_config() -> LLMConfig:
    """获取LLM配置实例"""
    return LLMConfig()