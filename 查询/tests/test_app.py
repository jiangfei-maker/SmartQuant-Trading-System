import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import datetime
from pathlib import Path

# 添加项目根目录到Python路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

# 导入被测试的应用
import app

@pytest.fixture(scope='module')
def at():
    """创建AppTest实例"""
    at = AppTest.from_file('app.py', default_timeout=10)
    return at

@pytest.fixture
@patch('app.ak')
@patch('app.DataProcessor')
@patch('app.NewsProcessor')
@patch('app.Backtester')
@patch('app.get_code_strategy_generator')
def mock_app_dependencies(mock_code_gen, mock_backtester, mock_news_processor, mock_data_processor, mock_ak):
    """模拟app.py的依赖"""
    # 模拟akshare
    mock_ak.stock_zh_a_spot.return_value = pd.DataFrame({
        'symbol': ['sh600000', 'sz000001'],
        'name': ['浦发银行', '平安银行'],
        'close': [8.5, 12.3],
        'open': [8.4, 12.0],
        'high': [8.6, 12.5],
        'low': [8.3, 11.9],
        'volume': [1000000, 2000000]
    })

    mock_ak.stock_hk_spot.return_value = pd.DataFrame({
        'code': ['00001.HK', '00002.HK'],
        'name': ['长和', '中电控股'],
        'close': [50.2, 65.8],
        'open': [49.8, 65.0],
        'high': [50.5, 66.0],
        'low': [49.5, 64.5],
        'volume': [500000, 300000]
    })

    mock_ak.stock_us_spot.return_value = pd.DataFrame({
        'symbol': ['AAPL', 'MSFT'],
        'name': ['苹果', '微软'],
        'close': [180.5, 370.2],
        'open': [179.8, 368.5],
        'high': [181.0, 371.0],
        'low': [179.0, 367.0],
        'volume': [50000000, 30000000]
    })

    # 模拟DataProcessor
    mock_data_processor_instance = MagicMock()
    mock_data_processor.return_value = mock_data_processor_instance
    mock_data_processor_instance.fetch_stock_data.return_value = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', periods=10),
        'open': np.random.rand(10) * 10 + 100,
        'high': np.random.rand(10) * 10 + 105,
        'low': np.random.rand(10) * 10 + 95,
        'close': np.random.rand(10) * 10 + 100,
        'volume': np.random.randint(1000000, 5000000, 10)
    }).set_index('date')

    # 模拟NewsProcessor
    mock_news_processor_instance = MagicMock()
    mock_news_processor.return_value = mock_news_processor_instance
    mock_news_processor_instance.fetch_news.return_value = [{
        'title': '测试新闻标题',
        'url': 'https://example.com/news',
        'pub_time': datetime.datetime.now(),
        'source': '测试来源'
    }]

    # 模拟Backtester
    mock_backtester_instance = MagicMock()
    mock_backtester.return_value = mock_backtester_instance
    mock_backtester_instance.run_backtest.return_value = {
        'equity_curve': pd.Series(np.cumprod(np.random.rand(10) * 0.02 + 1) * 100000),
        'trades': [{'date': datetime.datetime(2023, 1, 2), 'type': '买入', 'price': 100}],
        'stats': {
            '总收益率(%)': 10.5,
            '最大回撤(%)': 5.2,
            '夏普比率': 1.8,
            '胜率(%)': 60.0,
            '交易次数': 5
        },
        'data': pd.DataFrame()
    }

    # 模拟CodeStrategyGenerator
    mock_code_gen_instance = MagicMock()
    mock_code_gen.return_value = mock_code_gen_instance
    mock_code_gen_instance.generate_strategy.return_value = {
        '需求分析': '测试需求分析',
        '技术选型': '测试技术选型',
        '架构设计': '测试架构设计',
        '实现步骤': '测试实现步骤',
        '测试策略': '测试测试策略',
        '风险解决方案': '测试风险解决方案'
    }

    return {
        'ak': mock_ak,
        'data_processor': mock_data_processor_instance,
        'news_processor': mock_news_processor_instance,
        'backtester': mock_backtester_instance,
        'code_generator': mock_code_gen_instance
    }

def test_app_initialization(at):
    """测试应用初始化"""
    # 运行应用
    at.run()

    # 验证应用标题
    assert at.title[0].value == '智能量化交易系统'

    # 验证侧边栏导航
    assert at.sidebar.selectbox[0].label == '功能导航'
    assert at.sidebar.selectbox[0].options == ['行情', '自选股', '交易', '策略回测', '新闻资讯', '代码策略生成']

def test_market_data_display(at, mock_app_dependencies):
    """测试行情数据显示"""
    # 运行应用
    at.run()

    # 验证默认显示A股行情
    assert at.selectbox[0].label == '市场选择'
    assert at.selectbox[0].options == ['A股', '港股', '美股']
    assert at.selectbox[0].value == 'A股'

    # 验证数据表格显示
    assert at.dataframe[0].value.shape == (2, 7)  # 2只股票，7列数据

    # 测试切换到港股
    at.selectbox[0].set_value('港股').run()
    assert at.dataframe[0].value.shape == (2, 7)

    # 测试切换到美股
    at.selectbox[0].set_value('美股').run()
    assert at.dataframe[0].value.shape == (2, 7)

def test_watchlist_functionality(at):
    """测试自选股功能"""
    # 运行应用并切换到自选股标签
    at.sidebar.selectbox[0].set_value('自选股').run()

    # 验证自选股界面元素
    assert at.text_input[0].label == '添加股票代码'
    assert at.button[0].label == '添加'
    assert at.button[1].label == '移除选中'

    # 测试添加股票
    at.text_input[0].set_value('sh600000').run()
    at.button[0].click().run()

    # 验证股票被添加
    assert 'sh600000' in at.dataframe[0].value['symbol'].values

def test_trading_functionality(at):
    """测试交易功能"""
    # 运行应用并切换到交易标签
    at.sidebar.selectbox[0].set_value('交易').run()

    # 验证交易界面元素
    assert at.selectbox[0].label == '选择股票'
    assert at.number_input[0].label == '买入价格'
    assert at.number_input[1].label == '买入数量'
    assert at.button[0].label == '买入'
    assert at.button[1].label == '卖出'

def test_backtesting_functionality(at, mock_app_dependencies):
    """测试策略回测功能"""
    # 运行应用并切换到策略回测标签
    at.sidebar.selectbox[0].set_value('策略回测').run()

    # 验证回测界面元素
    assert at.text_input[0].label == '股票代码'
    assert at.date_input[0].label == '开始日期'
    assert at.date_input[1].label == '结束日期'
    assert at.selectbox[0].label == '选择策略'
    assert at.number_input[0].label == '初始资金'
    assert at.button[0].label == '运行回测'

    # 测试运行回测
    at.text_input[0].set_value('sh600000').run()
    at.date_input[0].set_value(datetime.date(2023, 1, 1)).run()
    at.date_input[1].set_value(datetime.date(2023, 1, 10)).run()
    at.button[0].click().run()

    # 验证回测结果显示
    assert at.success[0].value == '回测完成！'
    assert at.dataframe[0].value.shape == (5, 1)  # 5个绩效指标

def test_news_functionality(at, mock_app_dependencies):
    """测试新闻资讯功能"""
    # 运行应用并切换到新闻资讯标签
    at.sidebar.selectbox[0].set_value('新闻资讯').run()

    # 验证新闻界面元素
    assert at.selectbox[0].label == '新闻来源'
    assert at.button[0].label == '获取新闻'

    # 测试获取新闻
    at.button[0].click().run()

    # 验证新闻显示
    assert at.expander[0].label.startswith('测试新闻标题')

def test_code_strategy_generation(at, mock_app_dependencies):
    """测试代码策略生成功能"""
    # 运行应用并切换到代码策略生成标签
    at.sidebar.selectbox[0].set_value('代码策略生成').run()

    # 验证代码策略生成界面元素
    assert at.text_area[0].label == '输入您的需求'
    assert at.selectbox[0].label == '选择语言'
    assert at.selectbox[1].label == '选择框架(可选)'
    assert at.button[0].label == '生成策略'

    # 测试生成策略
    at.text_area[0].set_value('创建一个简单的均线交叉策略').run()
    at.button[0].click().run()

    # 验证策略显示
    assert at.expander[0].label == '需求分析'
    assert at.expander[1].label == '技术选型'
    assert at.expander[2].label == '架构设计'
    assert at.expander[3].label == '实现步骤'
    assert at.expander[4].label == '测试策略'
    assert at.expander[5].label == '风险解决方案'

if __name__ == '__main__':
    pytest.main(['-v', 'test_app.py'])