import pandas as pd
import numpy as np
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """技术指标计算类，提供多种常用技术指标的计算方法"""

    def __init__(self):
        pass

    def calculate_macd(self, df, fast_period=12, slow_period=26, signal_period=9):
        """计算MACD指标

        参数:
            df: 包含'close'列的DataFrame
            fast_period: 快速移动平均线周期
            slow_period: 慢速移动平均线周期
            signal_period: 信号线周期

        返回:
            df: 添加了'macd', 'macd_signal', 'macd_hist'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 计算EMA
        df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

        # 计算DIF线
        df['macd'] = df['ema_fast'] - df['ema_slow']

        # 计算DEA线（信号线）
        df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()

        # 计算MACD柱状图
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 移除中间列
        df = df.drop(['ema_fast', 'ema_slow'], axis=1)

        return df

    def calculate_rsi(self, df, period=14):
        """计算RSI指标

        参数:
            df: 包含'close'列的DataFrame
            period: 计算周期

        返回:
            df: 添加了'rsi'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 计算价格变化
        delta = df['close'].diff()

        # 分离上涨和下跌的变化
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """计算布林线指标

        参数:
            df: 包含'close'列的DataFrame
            period: 计算周期
            std_dev: 标准差倍数

        返回:
            df: 添加了'bollinger_mid', 'bollinger_upper', 'bollinger_lower'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 计算中轨（移动平均线）
        df['bollinger_mid'] = df['close'].rolling(window=period).mean()

        # 计算标准差
        df['bollinger_std'] = df['close'].rolling(window=period).std()

        # 计算上轨和下轨
        df['bollinger_upper'] = df['bollinger_mid'] + (df['bollinger_std'] * std_dev)
        df['bollinger_lower'] = df['bollinger_mid'] - (df['bollinger_std'] * std_dev)

        # 移除中间列
        df = df.drop(['bollinger_std'], axis=1)

        return df

    def calculate_mavol(self, df, period=5):
        """计算成交量均线

        参数:
            df: 包含'volume'列的DataFrame
            period: 计算周期

        返回:
            df: 添加了'mavol_{period}'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        column_name = f'mavol_{period}'
        df[column_name] = df['volume'].rolling(window=period).mean()
        return df

    def calculate_obv(self, df):
        """计算OBV能量潮

        参数:
            df: 包含'close'和'volume'列的DataFrame

        返回:
            df: 添加了'obv'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 初始化OBV
        df['obv'] = 0

        # 计算OBV
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                df['obv'].iloc[i] = df['obv'].iloc[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                df['obv'].iloc[i] = df['obv'].iloc[i-1] - df['volume'].iloc[i]
            else:
                df['obv'].iloc[i] = df['obv'].iloc[i-1]

        return df

    def calculate_kdj(self, df, period=9, k_period=3, d_period=3):
        """计算KDJ随机指标

        参数:
            df: 包含'high', 'low', 'close'列的DataFrame
            period: RSV计算周期
            k_period: K线计算周期
            d_period: D线计算周期

        返回:
            df: 添加了'kdj_k', 'kdj_d', 'kdj_j'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 计算RSV
        df['rsv'] = (df['close'] - df['low'].rolling(window=period).min()) / \
                    (df['high'].rolling(window=period).max() - df['low'].rolling(window=period).min()) * 100

        # 计算K线
        df['kdj_k'] = df['rsv'].rolling(window=k_period).mean()

        # 计算D线
        df['kdj_d'] = df['kdj_k'].rolling(window=d_period).mean()

        # 计算J线
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']

        return df

    def calculate_sar(self, df, af=0.02, max_af=0.2):
        """计算SAR抛物线指标

        参数:
            df: 包含'high', 'low', 'close'列的DataFrame
            af: 加速因子
            max_af: 最大加速因子

        返回:
            df: 添加了'sar'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        # 初始化SAR
        df['sar'] = 0.0
        ep = df['high'].iloc[0]  # 极端点
        trend = 1  # 趋势: 1=上涨, 0=下跌
        current_af = af

        # 计算SAR
        for i in range(1, len(df)):
            if trend == 1:
                # 上涨趋势
                df['sar'].iloc[i] = df['sar'].iloc[i-1] + current_af * (ep - df['sar'].iloc[i-1])
                # 检查是否反转
                if df['low'].iloc[i] < df['sar'].iloc[i]:
                    trend = 0
                    df['sar'].iloc[i] = ep
                    ep = df['low'].iloc[i]
                    current_af = af
                else:
                    # 未反转，更新极端点和加速因子
                    if df['high'].iloc[i] > ep:
                        ep = df['high'].iloc[i]
                        current_af = min(current_af + af, max_af)
            else:
                # 下跌趋势
                df['sar'].iloc[i] = df['sar'].iloc[i-1] + current_af * (ep - df['sar'].iloc[i-1])
                # 检查是否反转
                if df['high'].iloc[i] > df['sar'].iloc[i]:
                    trend = 1
                    df['sar'].iloc[i] = ep
                    ep = df['high'].iloc[i]
                    current_af = af
                else:
                    # 未反转，更新极端点和加速因子
                    if df['low'].iloc[i] < ep:
                        ep = df['low'].iloc[i]
                        current_af = min(current_af + af, max_af)

        return df

    def calculate_phoenix_line(self, df, period=5, volatility_period=8, n=1):
        """计算凤凰线指标

        参数:
            df: 包含'open', 'high', 'low', 'close'列的DataFrame
            period: 均线周期
            volatility_period: 波动率计算周期
            n: 参考期数

        返回:
            df: 添加了'phoenix_line_upper'(凰线)和'phoenix_line_lower'(凤线)列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        
        # 计算XOPEN (参考期的开盘价和收盘价的平均值)
        df['xopen'] = (df['open'].shift(n) + df['close'].shift(n)) / 2
        
        # 计算XHIGH和XLOW
        df['xhigh'] = df[['high', 'xopen']].max(axis=1)
        df['xlow'] = df[['low', 'xopen']].min(axis=1)
        
        # 计算波动率
        df['volatility'] = (df['xhigh'] - df['xlow']).rolling(window=volatility_period).mean()
        
        # 计算均线
        df['ma_close'] = df['close'].rolling(window=period).mean()
        
        # 计算凤凰线上下轨
        df['phoenix_line_upper'] = df['ma_close'] + df['volatility'] / 2
        df['phoenix_line_lower'] = df['ma_close'] - df['volatility'] / 2
        
        # 移除中间列
        df = df.drop(['xopen', 'xhigh', 'xlow', 'volatility', 'ma_close'], axis=1)
        
        return df

    def calculate_cci(self, df, period=20, constant=0.015):
        """计算CCI顺势指标

        参数:
            df: 包含'high', 'low', 'close'列的DataFrame
            period: 计算周期
            constant: 常数因子，通常为0.015

        返回:
            df: 添加了'cci'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        
        # 计算典型价格
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        # 计算移动平均典型价格
        df['sma_typical_price'] = df['typical_price'].rolling(window=period).mean()
        
        # 计算平均绝对偏差
        df['mean_deviation'] = abs(df['typical_price'] - df['sma_typical_price']).rolling(window=period).mean()
        
        # 计算CCI
        df['cci'] = (df['typical_price'] - df['sma_typical_price']) / (constant * df['mean_deviation'])
        
        # 移除中间列
        df = df.drop(['typical_price', 'sma_typical_price', 'mean_deviation'], axis=1)
        
        return df
    
    def calculate_williams_r(self, df, period=14):
        """计算威廉指标(W%R)

        参数:
            df: 包含'high', 'low', 'close'列的DataFrame
            period: 计算周期

        返回:
            df: 添加了'williams_r'列的DataFrame
        """
        df = df.copy()  # 创建副本以避免SettingWithCopyWarning
        
        # 计算威廉指标
        df['williams_r'] = (df['high'].rolling(window=period).max() - df['close']) / \
                          (df['high'].rolling(window=period).max() - df['low'].rolling(window=period).min()) * -100
        
        return df
    
    def calculate_indicator(self, df, indicator_name, **kwargs):
        """计算指定的技术指标

        参数:
            df: 原始数据DataFrame
            indicator_name: 指标名称
            **kwargs: 指标参数

        返回:
            df: 添加了对应指标列的DataFrame
        """
        indicators = {
            'macd': self.calculate_macd,
            'rsi': self.calculate_rsi,
            'bollinger': self.calculate_bollinger_bands,
            'mavol': self.calculate_mavol,
            'obv': self.calculate_obv,
            'kdj': self.calculate_kdj,
            'sar': self.calculate_sar,
            'phoenix_line': self.calculate_phoenix_line,
            'cci': self.calculate_cci,
            'williams_r': self.calculate_williams_r
        }

        if indicator_name.lower() not in indicators:
            raise ValueError(f"不支持的指标: {indicator_name}")

        try:
            return indicators[indicator_name.lower()](df, **kwargs)
        except Exception as e:
            logger.error(f"计算{indicator_name}指标失败: {str(e)}")
            raise