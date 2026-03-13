import pytest
import unittest.mock as mock
import time

# 在模块级别模拟easytrader模块
mock_easytrader = mock.MagicMock()

# 模拟use函数
mock_client = mock.MagicMock()
mock_easytrader.use.return_value = mock_client

# 模拟refresh_strategies和grid_strategies
mock_refresh_strategies = mock.MagicMock()
mock_refresh_strategies.Toolbar = mock.MagicMock()
mock_easytrader.refresh_strategies = mock_refresh_strategies

mock_grid_strategies = mock.MagicMock()
mock_grid_strategies.WMCopy = mock.MagicMock()
mock_easytrader.grid_strategies = mock_grid_strategies

# 替换sys.modules中的easytrader模块
import sys
sys.modules['easytrader'] = mock_easytrader

# 现在导入THSTrader和get_ths_trader，它们会使用模拟的easytrader模块
from ths_trader import THSTrader, get_ths_trader


class TestTHSTrader:
    @pytest.fixture
    def trader(self):
        """创建THSTrader实例"""
        # 重置mock以确保测试之间的独立性
        mock_easytrader.reset_mock()
        
        # 配置模拟客户端
        mock_client = mock_easytrader.use.return_value
        mock_client.connect.return_value = True
        mock_client.balance = {'available': 10000}
        mock_client.position = [{'stock_code': '600000', 'amount': 100}]
        mock_client.sell.return_value = {'success': True}
        mock_client.buy.return_value = {'success': True}
        mock_client.cancel_entrust.return_value = {'success': True}
        
        # 创建并连接THSTrader实例
        trader = THSTrader(client_path='test_path')
        trader.connect()  # 调用connect方法以设置self.user
        return trader

    def test_singleton_pattern(self):
        """测试单例模式是否正常工作"""
        trader1 = get_ths_trader()
        trader2 = get_ths_trader()
        assert trader1 is trader2

    def test_connect(self):
        """测试连接同花顺客户端"""
        # 保存原始的connect实现和返回值
        original_connect = mock_easytrader.use.return_value.connect
        original_return_value = mock_easytrader.use.return_value.connect.return_value
        
        try:
            # 配置连接成功
            mock_easytrader.use.return_value.connect.return_value = True
            
            # 创建THSTrader实例并尝试连接
            trader = THSTrader(client_path='test_path')
            result = trader.connect()
            
            # 验证结果
            assert result is True
            assert trader.connected is True
            mock_easytrader.use.return_value.connect.assert_called_once_with('test_path')
        finally:
            # 恢复原始的connect实现和返回值
            mock_easytrader.use.return_value.connect = original_connect
            mock_easytrader.use.return_value.connect.return_value = original_return_value

    def test_connect_already_connected(self, trader):
        """测试已连接状态下的连接功能"""
        # 记录初始调用次数
        initial_call_count = trader.user.connect.call_count
        
        # 尝试再次连接
        result = trader.connect()
        
        # 验证结果
        assert result is True
        # 验证connect方法没有被再次调用
        assert trader.user.connect.call_count == initial_call_count

    def test_connect_failure(self):
        """测试连接失败情况"""
        # 保存原始的connect实现
        original_connect = mock_easytrader.use.return_value.connect
        
        try:
            # 配置连接失败
            mock_easytrader.use.return_value.connect.side_effect = Exception('Connection failed')
            
            # 创建THSTrader实例并尝试连接
            trader = THSTrader(client_path='test_path')
            result = trader.connect()
            
            # 验证结果
            assert result is False
            assert trader.connected is False
        finally:
            # 恢复原始的connect实现
            mock_easytrader.use.return_value.connect = original_connect

    def test_disconnect(self, trader):
        """测试断开连接功能"""
        trader.connected = True
        trader.disconnect()
        assert trader.connected is False
        assert trader.user is None

    def test_get_balance(self, trader):
        """测试获取资金信息"""
        mock_balance = {'总资产': 100000, '可用资金': 50000}
        trader.user.balance = mock_balance
        trader.connected = True
        result = trader.get_balance()
        assert result == mock_balance

    def test_get_balance_not_connected(self, trader):
        """测试未连接状态下获取资金信息"""
        trader.connected = False
        trader.user = None
        trader.connect = mock.MagicMock(return_value=True)
        result = trader.get_balance()
        assert result is None
        trader.connect.assert_called_once()

    def test_get_position(self, trader):
        """测试获取持仓信息"""
        mock_position = [{'股票代码': 'sh600000', '股票名称': '浦发银行', '持仓数量': 1000}]
        trader.user.position = mock_position
        trader.connected = True
        result = trader.get_position()
        assert result == mock_position

    def test_sell(self, trader):
        """测试卖出功能"""
        mock_result = {'委托编号': '123456'}
        trader.user.sell.return_value = mock_result
        trader.connected = True
        result = trader.sell('sh600000', 100, 10.0)
        assert result == mock_result
        trader.user.sell.assert_called_once_with('sh600000', price=10.0, amount=100)

    def test_buy(self, trader):
        """测试买入功能"""
        mock_result = {'委托编号': '123456'}
        trader.user.buy.return_value = mock_result
        trader.connected = True
        result = trader.buy('sh600000', 100, 10.0)
        assert result == mock_result
        trader.user.buy.assert_called_once_with('sh600000', price=10.0, amount=100)

    def test_cancel_entrust(self, trader):
        """测试撤单功能"""
        mock_result = {'状态': '成功'}
        trader.user.cancel_entrust.return_value = mock_result
        trader.connected = True
        result = trader.cancel_entrust('123456')
        assert result == mock_result
        trader.user.cancel_entrust.assert_called_once_with('123456')

    def test_interval_call(self, trader):
        """测试请求频率限制装饰器"""
        # 创建一个测试函数
        def test_func(self_param): return True

        # 使用装饰器包装函数
        wrapped_func = THSTrader._interval_call(test_func)

        # 第一次调用
        start_time = time.time()
        wrapped_func(trader)
        first_call_time = time.time() - start_time
        assert first_call_time < 1  # 第一次调用应该很快

        # 第二次调用应该等待至少5秒
        start_time = time.time()
        wrapped_func(trader)
        second_call_time = time.time() - start_time
        assert second_call_time >= 5  # 第二次调用应该等待至少5秒
        second_call_time = time.time() - start_time

        assert first_call_time < 1  # 第一次调用应该很快
        assert second_call_time >= 5  # 第二次调用应该等待至少5秒