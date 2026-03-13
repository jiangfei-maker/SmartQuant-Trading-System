import pytest
import unittest.mock as mock
import os
import openai
from code_strategy_generator import CodeStrategyGenerator, get_code_strategy_generator


class TestCodeStrategyGenerator:
    def test_singleton_pattern(self):
        """测试单例模式是否正常工作"""
        # 重置全局实例以确保测试的纯净环境
        global _code_strategy_generator
        _code_strategy_generator = None

        generator1 = get_code_strategy_generator(api_key='test_key')
        generator2 = get_code_strategy_generator(api_key='different_key')
        assert generator1 is generator2
        assert generator1.api_key == 'test_key'  # 第一次设置的key应该被保留

    def test_initialization_with_api_key(self):
        """测试使用API密钥初始化"""
        generator = CodeStrategyGenerator(api_key='test_key')
        assert generator.api_key == 'test_key'
        assert openai.api_key == 'test_key'  # 检查是否正确设置了OpenAI API密钥

    @mock.patch('os.getenv')
    def test_initialization_with_env_var(self, mock_getenv):
        """测试使用环境变量初始化"""
        mock_getenv.return_value = 'env_key'
        generator = CodeStrategyGenerator()
        assert generator.api_key == 'env_key'

    @mock.patch('os.getenv')
    @mock.patch('streamlit.secrets')
    def test_initialization_with_streamlit_secret(self, mock_secrets, mock_getenv):
        """测试使用Streamlit secrets初始化"""
        mock_getenv.return_value = None
        mock_secrets.get.return_value = 'secret_key'
        generator = CodeStrategyGenerator()
        assert generator.api_key == 'secret_key'

    @mock.patch('os.getenv')
    @mock.patch('streamlit.secrets')
    def test_initialization_without_api_key(self, mock_secrets, mock_getenv):
        """测试没有API密钥的情况"""
        mock_getenv.return_value = None
        mock_secrets.get.return_value = None
        with pytest.raises(ValueError, match='未提供OpenAI API密钥'):
            CodeStrategyGenerator()

    @mock.patch('openai.ChatCompletion.create')
    def test_generate_strategy(self, mock_chat_completion):
        """测试生成策略功能"""
        # 设置mock返回值
        mock_response = mock.MagicMock()
        mock_response.choices[0].message.content = """需求分析
这是需求分析内容

技术选型及理由
这是技术选型内容

架构设计
这是架构设计内容

代码实现步骤
这是实现步骤内容

测试策略
这是测试策略内容

潜在风险及解决方案
这是风险解决方案内容"""
        mock_chat_completion.return_value = mock_response

        generator = CodeStrategyGenerator(api_key='test_key')
        result = generator.generate_strategy('测试需求', 'python', 'streamlit')

        # 验证API调用参数
        mock_chat_completion.assert_called_once()
        args, kwargs = mock_chat_completion.call_args
        assert kwargs['model'] == 'gpt-3.5-turbo'
        assert kwargs['temperature'] == 0.7
        assert kwargs['max_tokens'] == 2000
        assert any(msg['role'] == 'system' for msg in kwargs['messages'])
        assert any(msg['role'] == 'user' and '测试需求' in msg['content'] for msg in kwargs['messages'])

        # 验证结果
        assert 'raw_text' in result
        assert result['需求分析'] == '这是需求分析内容'
        assert result['技术选型'] == '这是技术选型内容'
        assert result['架构设计'] == '这是架构设计内容'
        assert result['实现步骤'] == '这是实现步骤内容'
        assert result['测试策略'] == '这是测试策略内容'
        assert result['风险解决方案'] == '这是风险解决方案内容'

    @mock.patch('openai.ChatCompletion.create')
    def test_generate_strategy_with_error(self, mock_chat_completion):
        """测试生成策略时的错误处理"""
        mock_chat_completion.side_effect = Exception('API错误')
        generator = CodeStrategyGenerator(api_key='test_key')
        result = generator.generate_strategy('测试需求')
        assert 'error' in result
        assert result['error'] == 'API错误'

    def test_extract_section(self):
        """测试提取部分功能"""
        generator = CodeStrategyGenerator(api_key='test_key')
        text = """需求分析
这是需求分析内容

技术选型及理由
这是技术选型内容

架构设计
这是架构设计内容"""

        # 测试提取存在的部分
        assert generator._extract_section(text, '需求分析') == '这是需求分析内容'
        assert generator._extract_section(text, '技术选型及理由') == '这是技术选型内容'
        assert generator._extract_section(text, '架构设计') == '这是架构设计内容'

        # 测试提取不存在的部分（使用不在end_markers中的名称）
        assert generator._extract_section(text, '代码实现步骤') is None

# 导入时需要修复的全局变量引用问题
global _code_strategy_generator
_code_strategy_generator = None