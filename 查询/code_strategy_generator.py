#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 代码策略生成器

import sys
# 确保Python默认编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import json
from typing import List, Dict, Any, Optional
import openai
import os
import streamlit as st

class CodeStrategyGenerator:
    """AI代码策略生成器，用于根据用户需求生成代码策略"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化代码策略生成器
        
        Args:
            api_key: OpenRouter API密钥，如果不提供则尝试从环境变量或Streamlit secrets获取
        """
        # 初始化API密钥和配置
        try:
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or st.secrets["openrouter"]["api_key"]
            self.model = os.getenv("OPENROUTER_MODEL") or st.secrets["openrouter"].get("model", "google/gemma-2-9b-it")
            self.base_url = os.getenv("OPENROUTER_BASE_URL") or st.secrets["openrouter"].get("base_url", "https://openrouter.ai/api/v1")
        except (KeyError, AttributeError):
            raise ValueError("未提供OpenRouter配置，请在Streamlit secrets中配置openrouter部分")
        
        # 配置OpenAI客户端以使用OpenRouter
        self.client = openai.Client(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # 系统提示模板
        self.system_prompt = """
        你是一位资深软件工程师，擅长全栈开发。根据用户需求，你需要生成详细的代码实现策略。
        策略应包括：
        1. 需求分析
        2. 技术选型及理由
        3. 架构设计
        4. 代码实现步骤
        5. 测试策略
        6. 潜在风险及解决方案
        
        请确保策略详细、可行，并提供必要的代码示例。
        """
    
    def generate_strategy(self, user_requirement: str, language: str = "python", framework: Optional[str] = None) -> Dict[str, Any]:
        """生成代码策略
        
        Args:
            user_requirement: 用户的需求描述
            language: 代码语言
            framework: 使用的框架（可选）
        
        Returns:
            包含代码策略的字典
        """
        # 构建用户提示
        try:
            user_prompt = f"需求: {user_requirement}\n语言: {language}"
            if framework:
                user_prompt += f"\n框架: {framework}"
            # 确保用户提示是UTF-8编码的字符串
            if not isinstance(user_prompt, str):
                user_prompt = str(user_prompt, 'utf-8')
        except UnicodeEncodeError:
            # 如果格式化时出现编码错误，尝试手动编码每个部分
            user_requirement = user_requirement.encode('utf-8').decode('utf-8')
            language = language.encode('utf-8').decode('utf-8')
            user_prompt = f"需求: {user_requirement}\n语言: {language}"
            if framework:
                framework = framework.encode('utf-8').decode('utf-8')
                user_prompt += f"\n框架: {framework}"
        
        try:
            # 确保所有输入字符串都是Unicode
            user_prompt = user_prompt.encode('utf-8').decode('utf-8')
            self.system_prompt = self.system_prompt.encode('utf-8').decode('utf-8')
            # 调用OpenAI API (兼容v1.0.0+)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # 解析响应
            # 确保响应内容是Unicode
            strategy_text = response.choices[0].message.content
            strategy_text = strategy_text.encode('utf-8').decode('utf-8')
            
            # 将策略文本转换为结构化数据
            # 这里简化处理，实际应用中可能需要更复杂的解析
            strategy = {
                "raw_text": strategy_text,
                "需求分析": self._extract_section(strategy_text, "需求分析"),
                "技术选型": self._extract_section(strategy_text, "技术选型及理由"),
                "架构设计": self._extract_section(strategy_text, "架构设计"),
                "实现步骤": self._extract_section(strategy_text, "代码实现步骤"),
                "测试策略": self._extract_section(strategy_text, "测试策略"),
                "风险解决方案": self._extract_section(strategy_text, "潜在风险及解决方案")
            }
            
            return strategy
        except Exception as e:
            # 确保错误消息正确编码
            error_message = str(e).encode('utf-8').decode('utf-8')
            st.error(f"生成代码策略失败: {error_message}")
            return {"error": str(e)}
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """从文本中提取指定部分
        
        Args:
            text: 原始文本
            section_name: 部分名称
        
        Returns:
            提取的部分文本，如果未找到则返回None
        """
        start_marker = section_name
        end_markers = ["需求分析", "技术选型及理由", "架构设计", "代码实现步骤", "测试策略", "潜在风险及解决方案"]
        end_markers.remove(section_name)
        
        start_index = text.find(start_marker)
        if start_index == -1:
            return None
        
        # 找到起始位置后的所有文本
        content_start = start_index + len(start_marker)
        remaining_text = text[content_start:]
        
        # 找到下一个结束标记
        end_index = len(remaining_text)
        for marker in end_markers:
            idx = remaining_text.find(marker)
            if idx != -1 and idx < end_index:
                end_index = idx
        
        # 提取并清理内容
        content = remaining_text[:end_index].strip()
        return content

# 单例模式包装
_code_strategy_generator = None

def get_code_strategy_generator(api_key: Optional[str] = None) -> CodeStrategyGenerator:
    """获取代码策略生成器实例
    
    Args:
        api_key: OpenAI API密钥
    
    Returns:
        CodeStrategyGenerator实例
    """
    global _code_strategy_generator
    if _code_strategy_generator is None:
        _code_strategy_generator = CodeStrategyGenerator(api_key)
    return _code_strategy_generator