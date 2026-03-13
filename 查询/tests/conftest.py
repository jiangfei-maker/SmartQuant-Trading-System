import pytest
import os
import sys
import unittest.mock as mock

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 全局测试配置
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """每个测试函数运行前后的设置和清理"""
    # 测试前设置
    yield
    # 测试后清理
    # 这里可以添加需要的清理代码

# 模拟 Streamlit 环境
@pytest.fixture
def mock_streamlit():
    """模拟 Streamlit 模块"""
    with mock.patch('streamlit') as mock_st:
        mock_st.secrets = {'openai_api_key': 'test_key'}
        mock_st.sidebar = mock.MagicMock()
        mock_st.selectbox = mock.MagicMock(return_value='上证指数')
        mock_st.button = mock.MagicMock(return_value=False)
        mock_st.text_input = mock.MagicMock(return_value='test_input')
        mock_st.text_area = mock.MagicMock(return_value='test_area')
        mock_st.success = mock.MagicMock()
        mock_st.error = mock.MagicMock()
        yield mock_st

# 导入需要的模块
import openai