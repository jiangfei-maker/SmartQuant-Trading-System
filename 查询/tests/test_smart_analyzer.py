import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smart_analyzer import SmartAnalyzer

class TestSmartAnalyzer:
    """测试智能分析器"""
    
    def setup_method(self):
        """测试准备"""
        self.analyzer = SmartAnalyzer()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=50)
        self.test_data = pd.DataFrame({
            '开盘': np.random.uniform(100, 200, 50),
            '最高': np.random.uniform(110, 210, 50),
            '最低': np.random.uniform(90, 190, 50),
            '收盘': np.random.uniform(100, 200, 50),
            '成交量': np.random.randint(1000, 10000, 50)
        }, index=dates)
    
    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        assert hasattr(self.analyzer, 'has_sklearn')
    
    @patch('smart_analyzer.ak.stock_zh_a_hist')
    def test_fetch_stock_data_success(self, mock_akshare):
        """测试成功获取股票数据"""
        # 模拟akshare返回数据
        mock_data = pd.DataFrame({
            '日期': pd.date_range('2023-01-01', periods=10),
            '开盘': range(100, 110),
            '最高': range(110, 120),
            '最低': range(90, 100),
            '收盘': range(105, 115),
            '成交量': range(1000, 1010)
        })
        mock_akshare.return_value = mock_data
        
        result = self.analyzer.fetch_stock_data('600000', 10)
        
        assert result is not None
        assert len(result) == 10
        assert '开盘' in result.columns
        assert '最高' in result.columns
        assert '最低' in result.columns
        assert '收盘' in result.columns
        assert '成交量' in result.columns
    
    @patch('smart_analyzer.ak.stock_zh_a_hist')
    def test_fetch_stock_data_failure(self, mock_akshare):
        """测试获取股票数据失败"""
        mock_akshare.return_value = pd.DataFrame()
        
        result = self.analyzer.fetch_stock_data('600000', 10)
        
        assert result is None
    
    def test_calculate_technical_indicators(self):
        """测试计算技术指标"""
        result = self.analyzer.calculate_technical_indicators(self.test_data)
        
        # 检查是否计算了所有技术指标
        assert 'MA5' in result.columns
        assert 'MA20' in result.columns
        assert 'RSI' in result.columns
        assert 'MACD' in result.columns
        assert 'MACD_Signal' in result.columns
        assert 'MACD_Hist' in result.columns
        assert 'BB_Upper' in result.columns
        assert 'BB_Mid' in result.columns
        assert 'BB_Lower' in result.columns
        
        # 检查数据类型
        assert result['MA5'].dtype == np.float64
        assert result['RSI'].dtype == np.float64
        assert result['MACD'].dtype == np.float64
    
    def test_analyze_market_trend(self):
        """测试市场趋势分析"""
        # 准备有趋势的数据
        dates = pd.date_range('2023-01-01', periods=50)
        trend_data = pd.DataFrame({
            '开盘': np.linspace(100, 200, 50),
            '最高': np.linspace(110, 210, 50),
            '最低': np.linspace(90, 190, 50),
            '收盘': np.linspace(105, 205, 50),
            '成交量': np.random.randint(1000, 10000, 50),
            'MA5': np.linspace(100, 200, 50),
            'MA10': np.linspace(95, 195, 50),
            'MA20': np.linspace(90, 190, 50),
            'MA60': np.linspace(85, 185, 50),
            'RSI': np.full(50, 60),
            'MACD': np.linspace(-1, 1, 50),
            'MACD_Signal': np.linspace(-0.5, 0.5, 50),
            'MACD_Hist': np.linspace(-0.5, 0.5, 50),
            'BB_Mid': np.linspace(100, 200, 50),
            'BB_Upper': np.linspace(110, 210, 50),
            'BB_Lower': np.linspace(90, 190, 50)
        }, index=dates)
        
        result = self.analyzer.analyze_market_trend(trend_data)
        
        # 检查返回结果结构
        assert '趋势判断' in result
        assert '支撑位' in result
        assert '压力位' in result
        assert '交易量分析' in result
        assert '技术指标信号' in result
        
        # 检查技术指标信号是列表
        assert isinstance(result['技术指标信号'], list)
    
    @patch('smart_analyzer.LinearRegression', create=True)
    @patch('smart_analyzer.train_test_split', create=True)
    def test_predict_price_with_sklearn(self, mock_train_test_split, mock_linear_regression):
        """测试使用scikit-learn预测价格"""
        # 模拟scikit-learn存在
        self.analyzer.has_sklearn = True
        
        # 准备预测数据
        dates = pd.date_range('2023-01-01', periods=30)
        predict_data = pd.DataFrame({
            '开盘': np.linspace(100, 130, 30),
            '最高': np.linspace(110, 140, 30),
            '最低': np.linspace(90, 120, 30),
            '收盘': np.linspace(105, 135, 30),
            '成交量': np.random.randint(1000, 10000, 30)
        }, index=dates)
        
        # 模拟模型预测
        mock_model = Mock()
        mock_model.predict.return_value = np.array([140, 141, 142, 143, 144])
        mock_linear_regression.return_value = mock_model
        
        # 模拟训练测试分割
        mock_train_test_split.return_value = (
            pd.DataFrame(), pd.DataFrame(), pd.Series(), pd.Series()
        )
        
        result = self.analyzer.predict_price(predict_data, days=5)
        
        assert result is not None
        assert len(result) == 5
        assert '预测价格' in result.columns
    
    def test_predict_price_without_sklearn(self):
        """测试没有scikit-learn时的价格预测"""
        # 模拟scikit-learn不存在
        self.analyzer.has_sklearn = False
        
        result = self.analyzer.predict_price(self.test_data)
        
        assert result is None
    
    @patch.object(SmartAnalyzer, 'fetch_stock_data')
    @patch.object(SmartAnalyzer, 'calculate_technical_indicators')
    @patch.object(SmartAnalyzer, 'analyze_market_trend')
    @patch.object(SmartAnalyzer, 'predict_price')
    def test_generate_insights_success(self, mock_predict, mock_analyze, mock_calculate, mock_fetch):
        """测试成功生成综合分析见解"""
        # 模拟各个方法
        mock_fetch.return_value = self.test_data
        mock_calculate.return_value = self.test_data
        mock_analyze.return_value = {
            '趋势判断': '上涨',
            '支撑位': 100.0,
            '压力位': 200.0,
            '交易量分析': '正常',
            '技术指标信号': []
        }
        mock_predict.return_value = pd.DataFrame({
            '预测价格': [210, 215, 220]
        }, index=pd.date_range('2023-02-01', periods=3))
        
        result = self.analyzer.generate_insights('600000')
        
        # 检查返回结果结构
        assert '股票代码' in result
        assert '分析日期' in result
        assert '趋势分析' in result
        assert '预测数据' in result
        assert '建议操作' in result
        
        # 验证各个方法被调用
        mock_fetch.assert_called_once_with('600000')
        mock_calculate.assert_called_once_with(self.test_data)
        mock_analyze.assert_called_once_with(self.test_data)
        mock_predict.assert_called_once_with(self.test_data)
    
    @patch.object(SmartAnalyzer, 'fetch_stock_data')
    def test_generate_insights_failure(self, mock_fetch):
        """测试生成见解失败（数据为空）"""
        mock_fetch.return_value = None
        
        result = self.analyzer.generate_insights('600000')
        
        assert 'error' in result
        assert '无法获取' in result['error']
    
    def test_generate_trading_advice(self):
        """测试生成交易建议"""
        test_cases = [
            # (趋势分析, 预期建议)
            ({'趋势判断': '强烈上涨', '技术指标信号': []}, '看多：考虑买入或持有'),
            ({'趋势判断': '上涨', '技术指标信号': []}, '谨慎看多：可以考虑小仓位买入'),
            ({'趋势判断': '强烈下跌', '技术指标信号': []}, '看空：考虑卖出或做空'),
            ({'趋势判断': '下跌', '技术指标信号': []}, '谨慎看空：可以考虑减仓'),
            ({'趋势判断': '上涨', '技术指标信号': ['RSI超买']}, '注意：RSI超买，可能面临回调'),
            ({'趋势判断': '下跌', '技术指标信号': ['RSI超卖']}, '注意：RSI超卖，可能接近底部'),
            ({'趋势判断': '震荡', '技术指标信号': []}, '中性：观望为主')
        ]
        
        for trend_analysis, expected_advice in test_cases:
            advice = self.analyzer._generate_trading_advice(trend_analysis)
            assert advice == expected_advice
    
    @patch.object(SmartAnalyzer, 'fetch_stock_data')
    @patch.object(SmartAnalyzer, 'calculate_technical_indicators')
    def test_plot_analysis(self, mock_calculate, mock_fetch):
        """测试绘制分析图表"""
        # 准备包含技术指标的测试数据
        plot_data = self.test_data.copy()
        plot_data['MA5'] = plot_data['收盘'].rolling(window=5).mean()
        plot_data['MA10'] = plot_data['收盘'].rolling(window=10).mean()
        plot_data['MA20'] = plot_data['收盘'].rolling(window=20).mean()
        plot_data['RSI'] = 50
        plot_data['MACD'] = 0
        plot_data['MACD_Signal'] = 0
        plot_data['MACD_Hist'] = 0
        plot_data['BB_Mid'] = plot_data['收盘'].rolling(window=20).mean()
        plot_data['BB_Upper'] = plot_data['BB_Mid'] + 2 * plot_data['收盘'].rolling(window=20).std()
        plot_data['BB_Lower'] = plot_data['BB_Mid'] - 2 * plot_data['收盘'].rolling(window=20).std()
        
        mock_fetch.return_value = plot_data
        mock_calculate.return_value = plot_data
        
        insights = {
            '预测数据': None
        }
        
        fig = self.analyzer.plot_analysis('600000', insights)
        
        # 检查是否返回了图表对象
        assert fig is not None
        # 检查图表是否有正确的子图数量
        assert len(fig.data) >= 8  # 至少应该有8个trace（价格、均线、布林带、MACD、RSI等）

if __name__ == '__main__':
    pytest.main([__file__, '-v'])