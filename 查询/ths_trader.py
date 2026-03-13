# -*- coding: utf-8 -*-  

import easytrader
import time
import threading
import json
import requests
from loguru import logger
import functools

class THSTrader:
    def __init__(self, client_path=None):
        """
        初始化同花顺交易客户端
        
        Args:
            client_path: 同花顺客户端路径，默认为None将尝试使用默认路径
        """
        self.client_path = client_path or 'C:/同花顺软件/同花顺/xiadan.exe'
        self.user = None
        self.connected = False
        self.lock = threading.Lock()
        self.next_time = 0
        self.interval = 5  # 5秒请求间隔限制
        
        # 初始化日志
        logger.add('./logs/ths_trader_{time}.log', rotation='00:00', encoding='utf-8')
        
    def connect(self):
        """连接同花顺客户端"""
        if self.connected:
            logger.info("已经连接到同花顺客户端，无需重复连接")
            return True
            
        try:
            logger.info(f"准备连接同花顺客户端: {self.client_path}")
            self.user = easytrader.use('universal_client')
            self.user.connect(self.client_path)
            # 配置同花顺客户端
            self.user.refresh_strategy = easytrader.refresh_strategies.Toolbar(refresh_btn_index=4)
            self.user.grid_strategy = easytrader.grid_strategies.WMCopy
            self.user.enable_type_keys_for_editor()
            self.connected = True
            logger.info("同花顺客户端连接成功")
            return True
        except Exception as e:
            logger.error(f"连接同花顺客户端失败: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开同花顺客户端连接"""
        # easytrader没有提供显式断开连接的方法
        self.connected = False
        self.user = None
        logger.info("已断开同花顺客户端连接")
    
    @staticmethod
    def _interval_call(func):
        """限制请求频率的装饰器"""
        next_time = 0
        interval = 5  # 5秒请求间隔限制
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            nonlocal next_time
            with lock:
                now = time.time()
                if now < next_time:
                    time.sleep(next_time - now)
                try:
                    result = func(self, *args, **kwargs)
                except Exception as e:
                    logger.error(f"执行{func.__name__}异常: {str(e)}")
                    result = None
                next_time = time.time() + interval
                return result
        return wrapper
    
    @_interval_call
    def get_balance(self):
        """获取账户资金信息"""
        if not self.connected and not self.connect():
            return None
        try:
            data = self.user.balance
            logger.info("成功获取账户资金信息")
            return data
        except Exception as e:
            logger.error(f"获取账户资金信息失败: {str(e)}")
            return None
    
    @_interval_call
    def get_position(self):
        """获取账户持仓信息"""
        if not self.connected and not self.connect():
            return None
        try:
            data = self.user.position
            logger.info("成功获取账户持仓信息")
            return data
        except Exception as e:
            logger.error(f"获取账户持仓信息失败: {str(e)}")
            return None
    
    @_interval_call
    def get_today_trades(self):
        """查询当日成交"""
        if not self.connected and not self.connect():
            return None
        try:
            data = self.user.today_trades
            logger.info("成功获取当日成交信息")
            return data
        except Exception as e:
            logger.error(f"获取当日成交信息失败: {str(e)}")
            return None
    
    @_interval_call
    def get_today_entrusts(self):
        """查询当日委托 (包括已成交/未成交/已撤单)"""
        if not self.connected and not self.connect():
            return None
        try:
            data = self.user.today_entrusts
            logger.info("成功获取当日委托信息")
            return data
        except Exception as e:
            logger.error(f"获取当日委托信息失败: {str(e)}")
            return None
    
    @_interval_call
    def sell(self, stock_code, amount, price=None, is_market=False):
        """
        卖出股票
        
        Args:
            stock_code: 股票代码
            amount: 卖出数量
            price: 卖出价格，默认为None
            is_market: 是否市价委托，默认为False
        
        Returns:
            委托结果
        """
        if not self.connected and not self.connect():
            return None
        try:
            if is_market:
                data = self.user.market_sell(stock_code, amount=int(amount))
            else:
                data = self.user.sell(stock_code, price=price, amount=int(amount))
            logger.info(f"卖出 {stock_code} {amount} 股成功")
            return data
        except Exception as e:
            logger.error(f"卖出 {stock_code} {amount} 股失败: {str(e)}")
            return None
    
    @_interval_call
    def buy(self, stock_code, amount, price=None, is_market=False):
        """
        买入股票
        
        Args:
            stock_code: 股票代码
            amount: 买入数量
            price: 买入价格，默认为None
            is_market: 是否市价委托，默认为False
        
        Returns:
            委托结果
        """
        if not self.connected and not self.connect():
            return None
        try:
            if is_market:
                data = self.user.market_buy(stock_code, amount=int(amount))
            else:
                data = self.user.buy(stock_code, price=price, amount=int(amount))
            logger.info(f"买入 {stock_code} {amount} 股成功")
            return data
        except Exception as e:
            logger.error(f"买入 {stock_code} {amount} 股失败: {str(e)}")
            return None
    
    @_interval_call
    def cancel_entrust(self, entrust_no):
        """
        撤单
        
        Args:
            entrust_no: 委托编号
        
        Returns:
            撤单结果
        """
        if not self.connected and not self.connect():
            return None
        try:
            data = self.user.cancel_entrust(entrust_no)
            logger.info(f"撤单 {entrust_no} 成功")
            return data
        except Exception as e:
            logger.error(f"撤单 {entrust_no} 失败: {str(e)}")
            return None


# 简单的单例模式包装
_ths_trader_instance = None

def get_ths_trader(client_path=None):
    """获取同花顺交易客户端单例"""
    global _ths_trader_instance
    if _ths_trader_instance is None:
        _ths_trader_instance = THSTrader(client_path)
    return _ths_trader_instance