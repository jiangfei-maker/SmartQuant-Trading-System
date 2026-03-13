import pandas as pd
from datetime import datetime
import logging
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Strategy:
    """策略基类"""
    def __init__(self, params=None):
        self.params = params or {}
        self.signals = None
        self.positions = None
        self.equity_curve = None
        self.trades = []

    def generate_signals(self, data):
        """生成交易信号"""
        raise NotImplementedError("子类必须实现generate_signals方法")

    def backtest(self, data, initial_capital=100000):
        """回测策略"""
        # 生成信号
        self.generate_signals(data)

        # 计算持仓
        self.positions = self.signals.shift(1).fillna(0)

        # 计算每日收益
        data['daily_return'] = data['close'].pct_change()
        data['strategy_return'] = self.positions * data['daily_return']

        # 计算累计收益
        data['cumulative_return'] = (1 + data['strategy_return']).cumprod()

        # 生成净值曲线
        self.equity_curve = data['cumulative_return'] * initial_capital

        # 生成交易记录
        self._generate_trades(data)

        # 计算绩效指标
        stats = self._calculate_stats(data, initial_capital)

        return {
            'equity_curve': self.equity_curve,
            'trades': self.trades,
            'stats': stats,
            'data': data
        }

    def _generate_trades(self, data):
        """生成交易记录"""
        position_changes = self.positions.diff()
        buy_signals = position_changes == 1
        sell_signals = position_changes == -1

        for date in data.index[buy_signals]:
            self.trades.append({
                'date': date,
                'type': '买入',
                'price': data.loc[date, 'close']
            })

        for date in data.index[sell_signals]:
            self.trades.append({
                'date': date,
                'type': '卖出',
                'price': data.loc[date, 'close']
            })

    def _calculate_stats(self, data, initial_capital):
        """计算绩效指标"""
        # 总收益率
        total_return = (self.equity_curve.iloc[-1] / initial_capital - 1) * 100

        # 最大回撤
        rolling_max = data['cumulative_return'].cummax()
        drawdown = (data['cumulative_return'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        # 夏普比率 (假设无风险利率为3%)
        risk_free_rate = 0.03
        daily_risk_free_rate = risk_free_rate / 252
        excess_returns = data['strategy_return'] - daily_risk_free_rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * (252 ** 0.5)

        # 胜率
        winning_trades = 0
        losing_trades = 0
        if len(self.trades) >= 2:
            for i in range(1, len(self.trades), 2):
                buy_price = self.trades[i-1]['price']
                sell_price = self.trades[i]['price']
                if sell_price > buy_price:
                    winning_trades += 1
                elif sell_price < buy_price:
                    losing_trades += 1
        win_rate = (winning_trades / (winning_trades + losing_trades)) * 100 if (winning_trades + losing_trades) > 0 else 0

        return {
            '总收益率(%)': round(total_return, 2),
            '最大回撤(%)': round(max_drawdown, 2),
            '夏普比率': round(sharpe_ratio, 2),
            '胜率(%)': round(win_rate, 2),
            '交易次数': len(self.trades)
        }

class SMACrossStrategy(Strategy):
    """均线交叉策略"""
    def generate_signals(self, data):
        short_period = self.params.get('short_period', 10)
        long_period = self.params.get('long_period', 50)

        # 计算均线
        data['short_ma'] = data['close'].rolling(window=short_period).mean()
        data['long_ma'] = data['close'].rolling(window=long_period).mean()

        # 生成信号
        self.signals = pd.Series(0, index=data.index)
        self.signals[data['short_ma'] > data['long_ma']] = 1
        self.signals[data['short_ma'] <= data['long_ma']] = 0

class RSIStrategy(Strategy):
    """RSI策略"""
    def generate_signals(self, data):
        rsi_period = self.params.get('rsi_period', 14)
        overbought = self.params.get('overbought', 70)
        oversold = self.params.get('oversold', 30)

        # 计算RSI
        delta = data['close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=rsi_period-1, adjust=True).mean()
        ema_down = down.ewm(com=rsi_period-1, adjust=True).mean()
        rs = ema_up / ema_down
        data['rsi'] = 100 - (100 / (1 + rs))

        # 生成信号
        self.signals = pd.Series(0, index=data.index)
        self.signals[data['rsi'] < oversold] = 1
        self.signals[data['rsi'] > overbought] = 0

class BollingerBandStrategy(Strategy):
    """布林带策略"""
    def generate_signals(self, data):
        bb_period = self.params.get('bb_period', 20)
        bb_std = self.params.get('bb_std', 2.0)

        # 计算布林带
        data['middle_band'] = data['close'].rolling(window=bb_period).mean()
        data['std'] = data['close'].rolling(window=bb_period).std()
        data['upper_band'] = data['middle_band'] + bb_std * data['std']
        data['lower_band'] = data['middle_band'] - bb_std * data['std']

        # 生成信号
        self.signals = pd.Series(0, index=data.index)
        self.signals[data['close'] < data['lower_band']] = 1
        self.signals[data['close'] > data['upper_band']] = 0

class MACDStrategy(Strategy):
    """MACD策略"""
    def generate_signals(self, data):
        macd_fast = self.params.get('macd_fast', 12)
        macd_slow = self.params.get('macd_slow', 26)
        macd_signal = self.params.get('macd_signal', 9)

        # 计算MACD
        data['fast_ema'] = data['close'].ewm(span=macd_fast, adjust=True).mean()
        data['slow_ema'] = data['close'].ewm(span=macd_slow, adjust=True).mean()
        data['macd'] = data['fast_ema'] - data['slow_ema']
        data['signal_line'] = data['macd'].ewm(span=macd_signal, adjust=True).mean()

        # 生成信号
        self.signals = pd.Series(0, index=data.index)
        self.signals[(data['macd'] > data['signal_line']) & (data['macd'].shift(1) <= data['signal_line'].shift(1))] = 1
        self.signals[(data['macd'] < data['signal_line']) & (data['macd'].shift(1) >= data['signal_line'].shift(1))] = 0

class Backtester:
    """回测引擎"""
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.strategy_map = {
            '均线交叉': SMACrossStrategy,
            'RSI策略': RSIStrategy,
            '布林带策略': BollingerBandStrategy,
            'MACD策略': MACDStrategy
        }

    def run_backtest(self, symbol, start_date, end_date, strategy_type, initial_capital, **kwargs):
        """运行回测"""
        try:
            # 获取数据
            data = self.data_processor.fetch_stock_data(symbol, start_date, end_date)

            # 检查数据
            if data.empty:
                raise ValueError("未获取到有效数据")

            # 创建策略实例
            if strategy_type not in self.strategy_map:
                raise ValueError(f"不支持的策略类型: {strategy_type}")

            strategy_class = self.strategy_map[strategy_type]
            strategy = strategy_class(params=kwargs)

            # 运行回测
            result = strategy.backtest(data, initial_capital)

            return result
        except Exception as e:
            logger.error(f"回测失败: {str(e)}")
            raise

    def plot_results(self, result, symbol, strategy_type):
        """绘制回测结果"""
        data = result['data']
        equity_curve = result['equity_curve']

        # 创建子图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=(f'{symbol} {strategy_type} 净值曲线', '交易信号'))

        # 添加净值曲线
        fig.add_trace(
            go.Scatter(x=equity_curve.index, y=equity_curve, name='净值曲线', line=dict(color='blue')),
            row=1, col=1
        )

        # 添加价格曲线
        fig.add_trace(
            go.Scatter(x=data.index, y=data['close'], name='收盘价', line=dict(color='black')),
            row=2, col=1
        )

        # 添加买入信号
        buy_signals = [trade for trade in result['trades'] if trade['type'] == '买入']
        if buy_signals:
            buy_dates = [trade['date'] for trade in buy_signals]
            buy_prices = [trade['price'] for trade in buy_signals]
            fig.add_trace(
                go.Scatter(x=buy_dates, y=buy_prices, mode='markers', name='买入信号',
                          marker=dict(color='green', size=10, symbol='triangle-up')),
                row=2, col=1
            )

        # 添加卖出信号
        sell_signals = [trade for trade in result['trades'] if trade['type'] == '卖出']
        if sell_signals:
            sell_dates = [trade['date'] for trade in sell_signals]
            sell_prices = [trade['price'] for trade in sell_signals]
            fig.add_trace(
                go.Scatter(x=sell_dates, y=sell_prices, mode='markers', name='卖出信号',
                          marker=dict(color='red', size=10, symbol='triangle-down')),
                row=2, col=1
            )

        # 更新布局
        fig.update_layout(height=800, title_text=f'{symbol} {strategy_type} 回测结果')
        fig.update_xaxes(title_text='日期', row=2, col=1)
        fig.update_yaxes(title_text='净值', row=1, col=1)
        fig.update_yaxes(title_text='价格', row=2, col=1)

        return fig