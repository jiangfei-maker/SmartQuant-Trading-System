import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from technical_indicators import TechnicalIndicators

class TestTechnicalIndicators:
    """测试技术指标计算器"""
    
    def setup_method(self):
        """测试准备"""
        self.indicators = TechnicalIndicators()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=50)
        self.test_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 50),
            'high': np.random.uniform(110, 210, 50),
            'low': np.random.uniform(90, 190, 50),
            'close': np.random.uniform(100, 200, 50),
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
    
    def test_indicators_initialization(self):
        """测试指标计算器初始化"""
        assert isinstance(self.indicators, TechnicalIndicators)
    
    def test_calculate_macd_default_params(self):
        """测试默认参数的MACD计算"""
        result = self.indicators.calculate_macd(self.test_data)
        
        # 检查是否计算了MACD相关列
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns
        
        # 检查数据类型
        assert result['macd'].dtype == np.float64
        assert result['macd_signal'].dtype == np.float64
        assert result['macd_hist'].dtype == np.float64
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_macd_custom_params(self):
        """测试自定义参数的MACD计算"""
        result = self.indicators.calculate_macd(
            self.test_data, 
            fast_period=6, 
            slow_period=13, 
            signal_period=5
        )
        
        # 检查是否计算了MACD相关列
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_rsi_default_params(self):
        """测试默认参数的RSI计算"""
        result = self.indicators.calculate_rsi(self.test_data)
        
        # 检查是否计算了RSI列
        assert 'rsi' in result.columns
        
        # 检查数据类型
        assert result['rsi'].dtype == np.float64
        
        # 检查RSI值在合理范围内
        assert result['rsi'].min() >= 0
        assert result['rsi'].max() <= 100
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_rsi_custom_params(self):
        """测试自定义参数的RSI计算"""
        result = self.indicators.calculate_rsi(self.test_data, period=7)
        
        # 检查是否计算了RSI列
        assert 'rsi' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_bollinger_bands_default_params(self):
        """测试默认参数的布林带计算"""
        result = self.indicators.calculate_bollinger_bands(self.test_data)
        
        # 检查是否计算了布林带相关列
        assert 'bollinger_mid' in result.columns
        assert 'bollinger_upper' in result.columns
        assert 'bollinger_lower' in result.columns
        
        # 检查数据类型
        assert result['bollinger_mid'].dtype == np.float64
        assert result['bollinger_upper'].dtype == np.float64
        assert result['bollinger_lower'].dtype == np.float64
        
        # 检查上轨应该大于中轨，中轨应该大于下轨（忽略NaN值）
        valid_upper = result['bollinger_upper'].dropna()
        valid_mid = result['bollinger_mid'].dropna()
        valid_lower = result['bollinger_lower'].dropna()
        
        assert (valid_upper > valid_mid).all()
        assert (valid_mid > valid_lower).all()
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_bollinger_bands_custom_params(self):
        """测试自定义参数的布林带计算"""
        result = self.indicators.calculate_bollinger_bands(
            self.test_data, 
            period=10, 
            std_dev=1.5
        )
        
        # 检查是否计算了布林带相关列
        assert 'bollinger_mid' in result.columns
        assert 'bollinger_upper' in result.columns
        assert 'bollinger_lower' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_mavol_default_params(self):
        """测试默认参数的成交量均线计算"""
        result = self.indicators.calculate_mavol(self.test_data)
        
        # 检查是否计算了成交量均线列
        assert 'mavol_5' in result.columns
        
        # 检查数据类型
        assert result['mavol_5'].dtype == np.float64
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_mavol_custom_params(self):
        """测试自定义参数的成交量均线计算"""
        result = self.indicators.calculate_mavol(self.test_data, period=10)
        
        # 检查是否计算了成交量均线列
        assert 'mavol_10' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_obv(self):
        """测试OBV能量潮计算"""
        # 创建有趋势的数据
        trend_data = self.test_data.copy()
        trend_data['close'] = np.linspace(100, 200, 50)
        
        result = self.indicators.calculate_obv(trend_data)
        
        # 检查是否计算了OBV列
        assert 'obv' in result.columns
        
        # 检查数据类型（OBV可能是int64或float64）
        assert result['obv'].dtype in [np.int64, np.float64]
        
        # 检查OBV应该单调递增（因为价格一直在上涨）
        # 由于浮点精度问题，使用近似检查
        assert (result['obv'].diff().dropna() >= 0).all()
        
        # 检查数据长度一致
        assert len(result) == len(trend_data)
    
    def test_calculate_kdj_default_params(self):
        """测试默认参数的KDJ计算"""
        result = self.indicators.calculate_kdj(self.test_data)
        
        # 检查是否计算了KDJ相关列
        assert 'kdj_k' in result.columns
        assert 'kdj_d' in result.columns
        assert 'kdj_j' in result.columns
        
        # 检查数据类型
        assert result['kdj_k'].dtype == np.float64
        assert result['kdj_d'].dtype == np.float64
        assert result['kdj_j'].dtype == np.float64
        
        # 检查KDJ值在合理范围内（允许轻微超出边界）
        assert result['kdj_k'].min() >= -10  # 允许轻微负值
        assert result['kdj_k'].max() <= 110  # 允许轻微超过100
        assert result['kdj_d'].min() >= -10  # 允许轻微负值
        assert result['kdj_d'].max() <= 110  # 允许轻微超过100
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_kdj_custom_params(self):
        """测试自定义参数的KDJ计算"""
        result = self.indicators.calculate_kdj(
            self.test_data, 
            period=14, 
            k_period=5, 
            d_period=5
        )
        
        # 检查是否计算了KDJ相关列
        assert 'kdj_k' in result.columns
        assert 'kdj_d' in result.columns
        assert 'kdj_j' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_sar_default_params(self):
        """测试默认参数的SAR计算"""
        result = self.indicators.calculate_sar(self.test_data)
        
        # 检查是否计算了SAR列
        assert 'sar' in result.columns
        
        # 检查数据类型
        assert result['sar'].dtype == np.float64
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_sar_custom_params(self):
        """测试自定义参数的SAR计算"""
        result = self.indicators.calculate_sar(
            self.test_data, 
            af=0.01, 
            max_af=0.1
        )
        
        # 检查是否计算了SAR列
        assert 'sar' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)
    
    def test_calculate_indicator_valid(self):
        """测试计算有效指标"""
        indicators_to_test = [
            'macd',
            'rsi', 
            'bollinger',
            'mavol',
            'obv',
            'kdj',
            'sar'
        ]
        
        for indicator in indicators_to_test:
            result = self.indicators.calculate_indicator(self.test_data, indicator)
            assert result is not None
            assert len(result) == len(self.test_data)
    
    def test_calculate_indicator_invalid(self):
        """测试计算无效指标"""
        with pytest.raises(ValueError, match="不支持的指标"):
            self.indicators.calculate_indicator(self.test_data, 'invalid_indicator')
    
    def test_calculate_indicator_with_params(self):
        """测试带参数的计算指标"""
        result = self.indicators.calculate_indicator(
            self.test_data, 
            'rsi', 
            period=7
        )
        
        # 检查是否计算了RSI列
        assert 'rsi' in result.columns
        
        # 检查数据长度一致
        assert len(result) == len(self.test_data)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])