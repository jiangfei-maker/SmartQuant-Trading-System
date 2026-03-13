import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtester import Strategy, SMACrossStrategy, RSIStrategy, BollingerBandStrategy, MACDStrategy, Backtester

class TestStrategyBase:
    """测试策略基类"""
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        strategy = Strategy()
        assert strategy.params == {}
        assert strategy.signals is None
        assert strategy.positions is None
        assert strategy.equity_curve is None
        assert strategy.trades == []
    
    def test_strategy_with_params(self):
        """测试带参数的策略初始化"""
        params = {'param1': 'value1', 'param2': 42}
        strategy = Strategy(params)
        assert strategy.params == params
    
    def test_generate_signals_not_implemented(self):
        """测试未实现的generate_signals方法"""
        strategy = Strategy()
        data = pd.DataFrame({'close': [100, 101, 102]})
        with pytest.raises(NotImplementedError):
            strategy.generate_signals(data)

class TestSMACrossStrategy:
    """测试均线交叉策略"""
    
    def setup_method(self):
        """测试准备"""
        self.data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        })
    
    def test_sma_cross_default_params(self):
        """测试默认参数的均线交叉策略"""
        strategy = SMACrossStrategy()
        strategy.generate_signals(self.data)
        
        # 检查是否计算了均线
        assert 'short_ma' in self.data.columns
        assert 'long_ma' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)
        assert strategy.signals.dtype == np.int64
    
    def test_sma_cross_custom_params(self):
        """测试自定义参数的均线交叉策略"""
        params = {'short_period': 5, 'long_period': 10}
        strategy = SMACrossStrategy(params)
        strategy.generate_signals(self.data)
        
        # 检查是否计算了均线
        assert 'short_ma' in self.data.columns
        assert 'long_ma' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)
    
    def test_sma_cross_backtest(self):
        """测试均线交叉策略的回测功能"""
        strategy = SMACrossStrategy()
        
        # 生成足够长的数据用于回测
        test_data = pd.DataFrame({
            'close': range(100, 200)
        }, index=pd.date_range('2023-01-01', periods=100))
        
        result = strategy.backtest(test_data, initial_capital=100000)
        
        # 检查回测结果
        assert 'equity_curve' in result
        assert 'trades' in result
        assert 'stats' in result
        assert 'data' in result
        
        # 检查绩效指标
        stats = result['stats']
        assert '总收益率(%)' in stats
        assert '最大回撤(%)' in stats
        assert '夏普比率' in stats
        assert '胜率(%)' in stats
        assert '交易次数' in stats

class TestRSIStrategy:
    """测试RSI策略"""
    
    def setup_method(self):
        """测试准备"""
        self.data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        })
    
    def test_rsi_strategy_default_params(self):
        """测试默认参数的RSI策略"""
        strategy = RSIStrategy()
        strategy.generate_signals(self.data)
        
        # 检查是否计算了RSI
        assert 'rsi' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)
        assert strategy.signals.dtype == np.int64
    
    def test_rsi_strategy_custom_params(self):
        """测试自定义参数的RSI策略"""
        params = {'rsi_period': 7, 'overbought': 80, 'oversold': 20}
        strategy = RSIStrategy(params)
        strategy.generate_signals(self.data)
        
        # 检查是否计算了RSI
        assert 'rsi' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)

class TestBollingerBandStrategy:
    """测试布林带策略"""
    
    def setup_method(self):
        """测试准备"""
        self.data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        })
    
    def test_bollinger_band_strategy_default_params(self):
        """测试默认参数的布林带策略"""
        strategy = BollingerBandStrategy()
        strategy.generate_signals(self.data)
        
        # 检查是否计算了布林带
        assert 'middle_band' in self.data.columns
        assert 'std' in self.data.columns
        assert 'upper_band' in self.data.columns
        assert 'lower_band' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)
        assert strategy.signals.dtype == np.int64
    
    def test_bollinger_band_strategy_custom_params(self):
        """测试自定义参数的布林带策略"""
        params = {'bb_period': 10, 'bb_std': 1.5}
        strategy = BollingerBandStrategy(params)
        strategy.generate_signals(self.data)
        
        # 检查是否计算了布林带
        assert 'middle_band' in self.data.columns
        assert 'std' in self.data.columns
        assert 'upper_band' in self.data.columns
        assert 'lower_band' in self.data.columns

class TestMACDStrategy:
    """测试MACD策略"""
    
    def setup_method(self):
        """测试准备"""
        self.data = pd.DataFrame({
            'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        })
    
    def test_macd_strategy_default_params(self):
        """测试默认参数的MACD策略"""
        strategy = MACDStrategy()
        strategy.generate_signals(self.data)
        
        # 检查是否计算了MACD
        assert 'fast_ema' in self.data.columns
        assert 'slow_ema' in self.data.columns
        assert 'macd' in self.data.columns
        assert 'signal_line' in self.data.columns
        
        # 检查信号生成
        assert len(strategy.signals) == len(self.data)
        assert strategy.signals.dtype == np.int64
    
    def test_macd_strategy_custom_params(self):
        """测试自定义参数的MACD策略"""
        params = {'macd_fast': 6, 'macd_slow': 13, 'macd_signal': 5}
        strategy = MACDStrategy(params)
        strategy.generate_signals(self.data)
        
        # 检查是否计算了MACD
        assert 'fast_ema' in self.data.columns
        assert 'slow_ema' in self.data.columns
        assert 'macd' in self.data.columns
        assert 'signal_line' in self.data.columns

class TestBacktester:
    """测试回测引擎"""
    
    def setup_method(self):
        """测试准备"""
        self.mock_data_processor = Mock()
        self.backtester = Backtester(self.mock_data_processor)
        
        # 准备测试数据
        self.test_data = pd.DataFrame({
            'close': range(100, 200),
            'open': range(99, 199),
            'high': range(101, 201),
            'low': range(98, 198),
            'volume': range(1000, 1100)
        }, index=pd.date_range('2023-01-01', periods=100))
    
    def test_backtester_initialization(self):
        """测试回测引擎初始化"""
        assert self.backtester.data_processor == self.mock_data_processor
        assert '均线交叉' in self.backtester.strategy_map
        assert 'RSI策略' in self.backtester.strategy_map
        assert '布林带策略' in self.backtester.strategy_map
        assert 'MACD策略' in self.backtester.strategy_map
    
    def test_run_backtest_success(self):
        """测试成功运行回测"""
        self.mock_data_processor.fetch_stock_data.return_value = self.test_data
        
        result = self.backtester.run_backtest(
            symbol='600000',
            start_date='2023-01-01',
            end_date='2023-04-10',
            strategy_type='均线交叉',
            initial_capital=100000
        )
        
        # 检查回测结果
        assert 'equity_curve' in result
        assert 'trades' in result
        assert 'stats' in result
        assert 'data' in result
        
        # 验证数据处理器被调用
        self.mock_data_processor.fetch_stock_data.assert_called_once_with(
            '600000', '2023-01-01', '2023-04-10'
        )
    
    def test_run_backtest_empty_data(self):
        """测试空数据情况"""
        self.mock_data_processor.fetch_stock_data.return_value = pd.DataFrame()
        
        with pytest.raises(ValueError, match="未获取到有效数据"):
            self.backtester.run_backtest(
                symbol='600000',
                start_date='2023-01-01',
                end_date='2023-04-10',
                strategy_type='均线交叉',
                initial_capital=100000
            )
    
    def test_run_backtest_invalid_strategy(self):
        """测试无效策略类型"""
        self.mock_data_processor.fetch_stock_data.return_value = self.test_data
        
        with pytest.raises(ValueError, match="不支持的策略类型"):
            self.backtester.run_backtest(
                symbol='600000',
                start_date='2023-01-01',
                end_date='2023-04-10',
                strategy_type='无效策略',
                initial_capital=100000
            )
    
    def test_run_backtest_with_custom_params(self):
        """测试带自定义参数的运行回测"""
        self.mock_data_processor.fetch_stock_data.return_value = self.test_data
        
        result = self.backtester.run_backtest(
            symbol='600000',
            start_date='2023-01-01',
            end_date='2023-04-10',
            strategy_type='均线交叉',
            initial_capital=100000,
            short_period=5,
            long_period=20
        )
        
        # 检查回测结果
        assert 'equity_curve' in result
        assert 'trades' in result
        assert 'stats' in result
        assert 'data' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])