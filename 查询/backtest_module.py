import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import akshare as ak
from datetime import datetime
from backtester import Backtester, Strategy
from data_processor import DataProcessor

def render_backtest_module():
    st.title("策略回测")
    st.sidebar.subheader("回测设置")
    
    # 回测参数设置
    stock_code = st.sidebar.text_input("证券代码", "sh600000")
    start_date = st.sidebar.date_input("开始日期", pd.to_datetime("2023-01-01"))
    end_date = st.sidebar.date_input("结束日期", pd.to_datetime("2024-01-01"))
    initial_capital = st.sidebar.number_input("初始资金", min_value=10000, value=100000)
    
    # 策略类型选择
    strategy_mode = st.sidebar.radio("策略模式", ["预设策略", "自定义策略"])
    
    strategy_type = None
    strategy_params = {}
    custom_strategy_code = ""
    
    if strategy_mode == "预设策略":
        # 预设策略选择
        strategy_type = st.sidebar.selectbox("策略类型", ["均线交叉", "RSI策略", "布林带策略", "MACD策略"])
        
        # 策略参数
        if strategy_type == "均线交叉":
            strategy_params['short_period'] = st.sidebar.slider("短期均线周期", min_value=5, max_value=50, value=10)
            strategy_params['long_period'] = st.sidebar.slider("长期均线周期", min_value=10, max_value=200, value=50)
        elif strategy_type == "RSI策略":
            strategy_params['rsi_period'] = st.sidebar.slider("RSI周期", min_value=5, max_value=30, value=14)
            strategy_params['overbought'] = st.sidebar.slider("超买阈值", min_value=60, max_value=90, value=70)
            strategy_params['oversold'] = st.sidebar.slider("超卖阈值", min_value=10, max_value=40, value=30)
        elif strategy_type == "布林带策略":
            strategy_params['bb_period'] = st.sidebar.slider("布林带周期", min_value=5, max_value=50, value=20)
            strategy_params['bb_std'] = st.sidebar.slider("标准差倍数", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
        elif strategy_type == "MACD策略":
            strategy_params['macd_fast'] = st.sidebar.slider("快速周期", min_value=5, max_value=20, value=12)
            strategy_params['macd_slow'] = st.sidebar.slider("慢速周期", min_value=20, max_value=50, value=26)
            strategy_params['macd_signal'] = st.sidebar.slider("信号线周期", min_value=5, max_value=20, value=9)
    else:
        # 自定义策略
        st.sidebar.subheader("自定义策略代码")
        st.sidebar.info("请输入Python策略代码，需继承Strategy基类并实现generate_signals方法")
        custom_strategy_code = st.sidebar.text_area(
            "策略代码",
            height=300,
            value="""from backtester import Strategy
import pandas as pd

class CustomStrategy(Strategy):
    def generate_signals(self, data):
        # 示例：5日均线和20日均线交叉策略
        data['short_ma'] = data['close'].rolling(window=5).mean()
        data['long_ma'] = data['close'].rolling(window=20).mean()
        
        self.signals = pd.Series(0, index=data.index)
        self.signals[data['short_ma'] > data['long_ma']] = 1
        self.signals[data['short_ma'] <= data['long_ma']] = 0
            """)
    
    # 运行回测按钮
    if st.sidebar.button("运行回测"):
        with st.spinner("正在执行回测..."):
            try:
                # 初始化数据处理器和回测引擎
                data_processor = DataProcessor()
                backtester = Backtester(data_processor)

                # 运行回测并捕获异常
                result = None
                try:
                    if strategy_mode == "预设策略":
                        result = backtester.run_backtest(
                            symbol=stock_code,
                            start_date=start_date,
                            end_date=end_date,
                            strategy_type=strategy_type,
                            initial_capital=initial_capital,
                            **strategy_params
                        )
                    else:
                        # 处理自定义策略
                        st.info("正在执行自定义策略...")

                        # 为自定义策略创建执行环境
                        exec_globals = {
                            '__builtins__': __builtins__,
                            'pd': pd,
                            'Strategy': Strategy
                        }

                        # 执行用户代码
                        try:
                            exec(custom_strategy_code, exec_globals)
                        except Exception as e:
                            st.error(f"策略代码执行错误: {str(e)}")
                            st.exception(e)
                            raise

                        # 检查是否定义了CustomStrategy类
                        if 'CustomStrategy' not in exec_globals:
                            st.error("策略代码中未定义CustomStrategy类")
                            raise ValueError("策略代码中未定义CustomStrategy类")

                        # 获取数据
                        data = data_processor.fetch_stock_data(stock_code, start_date, end_date)
                        if data.empty:
                            raise ValueError(f"未获取到'{stock_code}'的有效数据，请检查代码或日期范围")

                        # 创建自定义策略实例
                        custom_strategy_class = exec_globals['CustomStrategy']
                        try:
                            custom_strategy = custom_strategy_class(params=strategy_params)
                        except Exception as e:
                            st.error(f"创建策略实例失败: {str(e)}")
                            st.exception(e)
                            raise

                        # 运行回测
                        try:
                            result = custom_strategy.backtest(data, initial_capital)
                        except Exception as e:
                            st.error(f"策略回测执行失败: {str(e)}")
                            st.exception(e)
                            raise
                except Exception as e:
                    st.error(f"回测执行失败: {str(e)}")
                    # 打印完整错误信息以便调试
                    import traceback
                    st.text(f"详细错误信息:\n{traceback.format_exc()}")

                # 检查回测结果是否有效
                if result and isinstance(result, dict):
                    # 显示回测成功消息
                    st.success("回测完成！")
                    
                    # 显示回测结果
                    st.subheader("回测结果")

                    # 展示绩效指标
                    stats = result.get('stats', {})
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("总收益率", f"{stats.get('总收益率(%)', 0)}%")
                    col2.metric("最大回撤", f"{stats.get('最大回撤(%)', 0)}%")
                    col3.metric("夏普比率", f"{stats.get('夏普比率', 0):.2f}")
                    col4.metric("胜率", f"{stats.get('胜率(%)', 0)}%")

                    # 绘制净值曲线和交易信号
                    try:
                        fig = backtester.plot_results(result, stock_code, strategy_type if strategy_mode == "预设策略" else "自定义策略")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"绘制结果图表失败: {str(e)}")

                    # 显示交易记录
                    trades = result.get('trades', [])
                    if trades:
                        st.subheader("交易记录")
                        trades_df = pd.DataFrame(trades)
                        st.dataframe(trades_df)
                    else:
                        st.info("回测期间无交易")

                    # 显示策略参数
                    st.subheader("策略参数")
                    st.json(strategy_params)
                else:
                    st.warning("未获得有效的回测结果")
            except Exception as e:
                st.error(f"回测执行失败: {str(e)}")