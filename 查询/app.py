import os
import sys
print("=== 应用启动 ===")
print(f"Python版本: {sys.version}")
import akshare as ak
# 检查akshare版本信息
try:
    import pkg_resources
    ak_version = pkg_resources.get_distribution("akshare").version
    print(f"AKShare版本: {ak_version}")
except Exception:
    print("AKShare版本信息无法获取")
import traceback
import streamlit as st
import plotly.graph_objects as go
print("Streamlit导入成功")
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
import requests
from datetime import datetime
# 使用标准库的JSONDecodeError替代akshare中的版本
import json
JSONDecodeError = json.JSONDecodeError
from data_processor import DataProcessor
from backtester import Backtester, Strategy
from news_processor import NewsProcessor
from ths_trader import get_ths_trader
from code_strategy_generator import get_code_strategy_generator
from backtest_module import render_backtest_module
from technical_indicators import TechnicalIndicators
from smart_analyzer import get_smart_analyzer
from financial_data_fetcher import FinancialDataFetcher
from enhanced_financial_analysis_integrator import EnhancedFinancialAnalysisIntegrator
# 暂时停用Kronos功能
# from kronos.predictor import KronosPredictor

# 页面配置
st.set_page_config(page_title="智能量化交易系统", layout="wide", initial_sidebar_state="expanded", page_icon=":chart_with_upwards_trend:")

# 初始化全局状态（确保所有模块可访问）
try:
    # 尝试创建一个临时变量来确保session_state被正确初始化
    _ = st.session_state
    # 直接设置session_state变量，不使用条件检查
    st.session_state['market'] = 'A股'
    st.session_state['period'] = '分时'
    st.session_state['indicator'] = "无"
    st.session_state['trader_connected'] = False
    # 个股信息查询模块状态
    st.session_state['stock_info_stock_code'] = 'sh600000'
except Exception as e:
    print(f"初始化session_state时发生异常: {str(e)}")
    # 如果出现异常，使用备用方法
    import streamlit as st
    st.session_state = {}
    st.session_state['market'] = 'A股'
    st.session_state['period'] = '分时'
    st.session_state['indicator'] = "无"
    st.session_state['trader_connected'] = False
    st.session_state['stock_info_stock_code'] = 'sh600000'

# 侧边栏
st.sidebar.title("功能导航")
module = st.sidebar.selectbox("选择模块", ["行情", "自选股", "交易", "代码策略", "设置", "回测策略", "新闻", "智能分析", "公司/行业研究", "财务数据获取", "财务数据分析"], index=8)
print(f"=== 模块选择结果: {module} ===")



if module == "行情":
    st.sidebar.subheader("市场筛选")
    market = st.sidebar.selectbox("选择市场", ["A股", "港股", "美股", "期货"])
    stock_code = st.sidebar.text_input("输入证券代码（如sh600000/hk00700/usAAPL）", "sh600000")
    period = st.sidebar.selectbox("时间周期", ["分时", "日K", "周K", "月K"])
    # 将多选型改为单选型，实现指标切换
    indicator = st.sidebar.selectbox("选择指标", ["无", "MACD", "RSI", "布林线", "成交量均线", "OBV能量潮", "KDJ随机指标", "SAR抛物线"])
    # 保存状态防止刷新丢失
    st.session_state.market = market
    st.session_state.period = period
    st.session_state.indicator = indicator
    st.session_state.stock_code = stock_code

elif module == "自选股":
    st.sidebar.subheader("自选股管理")
    new_stock = st.sidebar.text_input("添加新证券代码")
    if st.sidebar.button("保存自选股"):
        if new_stock not in st.session_state.get("watchlist", []):
            st.session_state.watchlist = st.session_state.get("watchlist", []) + [new_stock]
    st.sidebar.subheader("当前自选股")
    for stock in st.session_state.get("watchlist", []):
        st.sidebar.text(stock)

elif module == "设置":
    st.sidebar.subheader("个性化设置")
    theme = st.sidebar.selectbox("主题模式", ["默认", "深色"])
    if theme == "深色":
        st.set_page_config(page_title="AKShare证券助手", layout="wide", initial_sidebar_state="expanded", page_icon=":chart_with_upwards_trend:")
        st.markdown("<style>body {background-color: #1E1E1E;}</style>", unsafe_allow_html=True)

# 初始化交易客户端
trader = get_ths_trader()
# 使用字典方式访问session_state，避免属性访问问题
market = st.session_state.get('market', 'A股')
period = st.session_state.get('period', '分时')
indicator = st.session_state.get('indicator', '无')

# 主页面
if module == "行情":
    # 同步侧边栏状态到全局
    st.session_state.market = market
    st.session_state.period = period
    st.session_state.indicator = indicator
    st.session_state.market = market  # 保存状态避免刷新丢失
    st.title(f"{market}行情 - {stock_code}")
    # 获取实时行情数据
    # 获取实时行情数据
    if market == "A股":
        try:
            # 模拟浏览器请求头（新增Referer字段）
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Referer": "https://finance.sina.com.cn/"  # 新浪财经官网Referer，绕过反爬限制
            }
            try:
                url = f"https://hq.sinajs.cn/list=s_{stock_code}"
                response = requests.get(url, headers=headers, timeout=10)
                # 显式处理403状态码（避免被raise_for_status吞掉）
                if response.status_code == 403:
                    st.error("获取实时行情失败：接口拒绝访问（可能因反爬限制），请稍后重试或更换请求头")
                    df = pd.DataFrame()
                else:
                    response.raise_for_status()  # 检查其他HTTP错误状态码
                    # 记录原始响应日志
                    try:
                        logger.debug(f"API响应原始内容: {response.text[:500]}")
                    except Exception as e:
                        st.error(f"日志记录失败: {str(e)}")
                    # 检查响应内容是否为HTML（新浪错误页以<开头）
                    if response.text.lstrip().startswith('<'):
                        st.error(f"获取实时行情失败：接口返回异常内容（可能为维护页面）\n原始响应前50字符：{response.text[:50]}")
                        df = pd.DataFrame()
                    else:
                        # 解析新浪接口数据（增强鲁棒性）
                        try:
                            # 提取等号后的数据部分（处理可能的空响应）
                            # 解析新浪接口数据（增强鲁棒性，适配不同返回格式）
                            try:
                                data_str_parts = response.text.split('=')
                                if len(data_str_parts) < 2:
                                    st.error("获取实时行情失败：接口返回数据格式异常（无等号分隔符）")
                                    df = pd.DataFrame()
                                else:
                                    data_str = data_str_parts[1].strip(';"')
                                    if not data_str:
                                        st.error("获取实时行情失败：接口返回空数据字符串（可能为非交易时间）")
                                        df = pd.DataFrame()
                                    else:
                                        data = data_str.split(',')
                                        # 根据实际返回字段数量动态处理
                                        if len(data) >= 1:
                                            # 至少有1个字段（名称）
                                            actual_columns = ['代码', '名称']
                                            full_data = [stock_code, data[0]]
                                             
                                            # 动态添加可用字段
                                            field_mapping = [
                                                ('当前价', 1),
                                                ('涨跌额', 2),
                                                ('涨跌幅', 3),
                                                ('成交量', 4),
                                                ('成交额', 5)
                                            ]
                                             
                                            for field_name, index in field_mapping:
                                                if index < len(data) and data[index]:
                                                    actual_columns.append(field_name)
                                                    full_data.append(data[index])
                                             
                                            df = pd.DataFrame([full_data], columns=actual_columns)
                                            # 记录解析结果日志
                                            logger.debug(f"成功解析数据: {df.to_dict()}")
                                              
                                            # 如果字段不足，显示警告而非错误
                                            if len(data) < 6:
                                                st.warning(f"获取实时行情完成，但字段不足（期望6个，实际{len(data)}个）")
                                        else:
                                            st.error("获取实时行情失败：接口返回空数据数组")
                                            df = pd.DataFrame()
                            except Exception as e:
                                st.error(f"数据解析异常：{str(e)}，原始数据：{response.text[:100]}")
                                df = pd.DataFrame()
                        except Exception as e:
                            st.error(f"数据解析异常：{str(e)}，原始数据：{response.text[:100]}")
                            df = pd.DataFrame()
            except requests.exceptions.RequestException as e:
                st.error(f"网络请求异常：{str(e)}，请检查网络连接或稍后重试")
                df = pd.DataFrame()
            # 数据有效性校验（避免空数据进入后续流程）
            if df.empty:
                st.error("获取实时行情失败，接口未返回有效数据")
            else:
                # 确保代码匹配（避免输入错误代码导致显示其他数据）
                if df['代码'].iloc[0] != stock_code:
                    st.error(f"警告：接口返回数据代码不匹配（期望：{stock_code}，实际：{df['代码'].iloc[0]}）")
                    df = pd.DataFrame()
        except Exception as e:
            st.error(f"获取实时行情失败（未知错误）：{str(e)}，请联系管理员")
            df = pd.DataFrame()
    elif market == "港股":
        try:
            df = ak.stock_hk_spot()
        except Exception as e:
            st.error(f"获取港股行情失败：{str(e)}")
            df = pd.DataFrame()
    elif market == "美股":
        try:
            df = ak.stock_us_spot()
        except Exception as e:
            st.error(f"获取美股行情失败：{str(e)}")
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()
    if not df.empty:
        st.subheader("实时行情")
        st.dataframe(df[df['代码']==stock_code].iloc[0])

        # 获取K线数据
        if period == "分时":
            # 获取分时数据并处理空值，添加健壮的异常处理
            try:
                k_df = ak.stock_zh_a_minute(symbol=stock_code, period="1")
                if k_df.empty:
                    st.error('分时数据为空，请检查证券代码或重试')
                    k_df = pd.DataFrame()
            except AttributeError:
                # 备选方案1：尝试直接从子模块导入
                st.info("尝试使用备选导入方式...")
                try:
                    from akshare.stock.stock_zh_a_sina import stock_zh_a_minute as minute_func
                    k_df = minute_func(symbol=stock_code, period="1")
                except Exception as e2:
                    # 备选方案2：使用日K数据作为替代
                    st.warning(f"无法获取分时数据: {str(e2)}，使用最新日K数据替代")
                    try:
                        end_date = pd.Timestamp.now().strftime('%Y%m%d')
                        start_date = (pd.Timestamp.now() - pd.DateOffset(days=30)).strftime('%Y%m%d')
                        k_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                                  start_date=start_date, end_date=end_date, adjust="qfq")
                    except Exception as e3:
                        st.error(f"获取替代数据失败: {str(e3)}")
                        k_df = pd.DataFrame()
            except Exception as e:
                st.error(f"获取分时数据失败: {str(e)}")
                k_df = pd.DataFrame()
        else:
            # 建立周期参数映射（AKShare要求英文参数）
            period_mapping = {"日K": "daily", "周K": "weekly", "月K": "monthly"}
            ak_period = period_mapping.get(period, "daily")  # 默认使用日K
            # 添加异常处理和数据空值提示
            try:
                # 对于周K和月K，需要指定起始日期以获取足够数据
                # 对于所有周期，先获取日K数据
                end_date = pd.Timestamp.now().strftime('%Y%m%d')
                start_date = (pd.Timestamp.now() - pd.DateOffset(years=3)).strftime('%Y%m%d')
                st.info(f"正在获取日K数据: 代码={stock_code}, 开始日期={start_date}, 结束日期={end_date}")
                try:
                    k_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
                    st.info(f"日K数据获取完成，共{len(k_df)}条记录")
                except Exception as e:
                    st.error(f"日K数据获取异常: {str(e)}")
                    k_df = pd.DataFrame()

                # 如果需要周K或月K数据，则手动聚合
                if ak_period == "weekly" and not k_df.empty:
                    # 转换日期列为索引
                    k_df['日期'] = pd.to_datetime(k_df['日期'])
                    k_df = k_df.set_index('日期')
                    # 按周聚合
                    weekly_df = k_df.resample('W').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    })
                    # 重置索引
                    weekly_df = weekly_df.reset_index()
                    k_df = weekly_df
                elif ak_period == "monthly" and not k_df.empty:
                    # 转换日期列为索引
                    k_df['日期'] = pd.to_datetime(k_df['日期'])
                    k_df = k_df.set_index('日期')
                    # 按月聚合
                    monthly_df = k_df.resample('M').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    })
                    # 重置索引
                    monthly_df = monthly_df.reset_index()
                    k_df = monthly_df

                if k_df.empty:
                    st.error(f"获取{period}K线数据失败：证券代码 {stock_code} 无效或接口无数据（可能为非交易时间/代码错误）")
                    st.info(f"尝试获取数据参数: 代码={stock_code}, 周期={ak_period}")
            except Exception as e:
                st.error(f"获取{period}K线数据异常：{str(e)}")
                st.info(f"尝试获取数据参数: 代码={stock_code}, 周期={ak_period}")
                k_df = pd.DataFrame()
        
        # 检查数据有效性（避免空数据导致后续错误）
        if not k_df.empty:
            st.info(f"成功获取{period}K线数据，共{len(k_df)}条记录")
            st.info(f"数据列名: {k_df.columns.tolist()}")
            st.info(f"数据前5行: {k_df.head().to_dict('records')}")
            # 检查并重命名日期列（兼容更多可能的列名）
            if 'date' in k_df.columns:
                k_df.rename(columns={'date': '日期'}, inplace=True)
            elif '交易日期' in k_df.columns:
                k_df.rename(columns={'交易日期': '日期'}, inplace=True)
            elif 'day' in k_df.columns:  # 适配分时数据的"day"列
                k_df.rename(columns={'day': '日期'}, inplace=True)
            elif '时间' in k_df.columns:  # 适配可能的其他中文列名
                k_df.rename(columns={'时间': '日期'}, inplace=True)
            else:
                st.error('未获取到有效日期列，请检查数据接口返回字段。当前列名：' + str(k_df.columns.tolist()))
                k_df = pd.DataFrame()
            # 仅当日期列存在时转换格式
            if '日期' in k_df.columns:
                k_df["日期"] = pd.to_datetime(k_df["日期"])
            else:
                k_df = pd.DataFrame()  # 确保数据为空时不继续执行
        else:
            st.error("K线数据为空，无法继续绘制图表")
        
        # 绘制K线图（仅当数据有效时执行）
        if not k_df.empty and '日期' in k_df.columns and 'open' in k_df.columns and 'high' in k_df.columns and 'low' in k_df.columns and 'close' in k_df.columns:
            # 确保数据列是数值类型
            k_df['open'] = pd.to_numeric(k_df['open'], errors='coerce')
            k_df['high'] = pd.to_numeric(k_df['high'], errors='coerce')
            k_df['low'] = pd.to_numeric(k_df['low'], errors='coerce')
            k_df['close'] = pd.to_numeric(k_df['close'], errors='coerce')
            k_df['volume'] = pd.to_numeric(k_df['volume'], errors='coerce')
            # 删除包含NaN值的行
            k_df = k_df.dropna()

            # 初始化技术指标计算器
            ti = TechnicalIndicators()

            # 创建K线图、成交量图和指标图三个子图
            fig_k = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, 
                                subplot_titles=(f'{period}K线图', '成交量', f'指标: {indicator}'), 
                                row_heights=[0.5, 0.2, 0.3])

            # 为了只显示有数据的交易日并将它们连起来，我们将使用索引作为x轴，然后自定义tick文本
            # 保存原始日期值用于自定义tick
            dates = k_df['日期'].dt.strftime('%Y-%m-%d').tolist()

            # 添加K线图数据，使用索引作为x轴
            fig_k.add_trace(
                go.Candlestick(x=list(range(len(k_df))),
                            open=k_df['open'],
                            high=k_df['high'],
                            low=k_df['low'],
                            close=k_df['close'],
                            name='K线'),
                row=1, col=1
            )

            # 添加成交量，使用索引作为x轴
            fig_k.add_trace(
                go.Bar(x=list(range(len(k_df))), y=k_df['volume'], name='成交量'),
                row=2, col=1
            )

            # 处理指标（使用technical_indicators.py中的计算方法）
            if indicator == 'MACD':
                # 计算MACD指标
                k_df = ti.calculate_macd(k_df)

                # 添加MACD指标到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['macd_signal'], name='Signal', line=dict(color='orange')), row=3, col=1)
                # 使用条件列表设置直方图颜色
                colors = ['green' if val > 0 else 'red' for val in k_df['macd_hist']]
                fig_k.add_trace(go.Bar(x=list(range(len(k_df))), y=k_df['macd_hist'], name='Histogram', marker_color=colors, showlegend=False), row=3, col=1)

                # 设置MACD子图的y轴范围，确保能看到所有数据
                fig_k.update_yaxes(row=3, col=1, autorange=True)

            elif indicator == 'RSI':
                # 计算RSI指标
                k_df = ti.calculate_rsi(k_df)

                # 添加RSI到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['rsi'], name='RSI', line=dict(color='purple')), row=3, col=1)
                fig_k.add_hline(y=70, line_dash='dash', line_color='red', row=3, col=1)
                fig_k.add_hline(y=30, line_dash='dash', line_color='green', row=3, col=1)

            elif indicator == '布林线':
                # 计算布林线指标
                k_df = ti.calculate_bollinger_bands(k_df)

                # 添加布林线到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['bollinger_mid'], name='中轨', line=dict(color='blue')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['bollinger_upper'], name='上轨', line=dict(color='red', dash='dash')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['bollinger_lower'], name='下轨', line=dict(color='green', dash='dash')), row=3, col=1)

            elif indicator == '成交量均线':
                # 计算成交量均线
                k_df = ti.calculate_mavol(k_df, period=5)
                k_df = ti.calculate_mavol(k_df, period=10)

                # 添加成交量均线到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['volume'], name='成交量', line=dict(color='blue')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['mavol_5'], name='5日均量', line=dict(color='orange')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['mavol_10'], name='10日均量', line=dict(color='green')), row=3, col=1)

            elif indicator == 'OBV能量潮':
                # 计算OBV能量潮
                k_df = ti.calculate_obv(k_df)

                # 添加OBV到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['obv'], name='OBV', line=dict(color='purple')), row=3, col=1)

            elif indicator == 'KDJ随机指标':
                # 计算KDJ随机指标
                k_df = ti.calculate_kdj(k_df)

                # 添加KDJ到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['kdj_k'], name='K线', line=dict(color='blue')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['kdj_d'], name='D线', line=dict(color='orange')), row=3, col=1)
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['kdj_j'], name='J线', line=dict(color='green')), row=3, col=1)
                fig_k.add_hline(y=80, line_dash='dash', line_color='red', row=3, col=1)
                fig_k.add_hline(y=20, line_dash='dash', line_color='green', row=3, col=1)

            elif indicator == 'SAR抛物线':
                # 计算SAR抛物线指标
                k_df = ti.calculate_sar(k_df)

                # 添加SAR到第三个子图，使用索引作为x轴
                fig_k.add_trace(go.Scatter(x=list(range(len(k_df))), y=k_df['sar'], name='SAR', line=dict(color='purple')), row=3, col=1)

            # 更新x轴，使用自定义tick文本显示日期
            # 为了避免x轴标签过于拥挤，我们可以只显示一部分日期
            # 计算要显示的tick位置（每隔一定数量的点显示一个日期）
            tick_step = max(1, len(k_df) // 10)  # 最多显示10个日期标签
            tick_positions = list(range(0, len(k_df), tick_step))
            tick_texts = [dates[i] for i in tick_positions]

            # 更新布局
            # 如果是分时图，则显示为日K线图
            display_period = "日" if period == "分时" else period
            fig_k.update_layout(height=1000, title_text=f'{stock_code} {display_period}K线图')
            fig_k.update_xaxes(rangeslider_visible=False, 
                              tickmode='array',
                              tickvals=tick_positions,
                              ticktext=tick_texts,
                              row=1, col=1)
            fig_k.update_xaxes(rangeslider_visible=False, 
                              tickmode='array',
                              tickvals=tick_positions,
                              ticktext=tick_texts,
                              row=2, col=1)
            fig_k.update_xaxes(rangeslider_visible=False, 
                              tickmode='array',
                              tickvals=tick_positions,
                              ticktext=tick_texts,
                              row=3, col=1)
            # 添加错误处理，确保图表正确渲染
            try:
                if fig_k is not None and hasattr(fig_k, 'update_layout'):
                    st.plotly_chart(fig_k, use_container_width=True)
            except Exception as e:
                st.error(f"绘制K线图失败: {str(e)}")

elif module == "回测策略":
    render_backtest_module()

elif module == "代码策略":
    st.title("AI代码策略生成器")
    
    # API密钥配置
    st.sidebar.subheader("OpenAI API配置")
    api_key = st.sidebar.text_input("OpenAI API密钥", type="password")
    
    # 需求输入
    st.subheader("需求描述")
    user需求 = st.text_area("请详细描述您的代码需求", height=200)
    
    # 技术选择
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("编程语言", ["python", "javascript", "java", "c++", "c#", "go"])
    with col2:
        framework = st.text_input("使用框架（可选）")
    
    # 生成策略按钮
    if st.button("生成代码策略"):
        if not user需求.strip():
            st.error("请输入代码需求")
        else:
            try:
                with st.spinner("正在生成代码策略..."):
                    # 初始化代码策略生成器
                    generator = get_code_strategy_generator(api_key)
                    
                    # 生成策略
                    strategy = generator.generate_strategy(user需求, language, framework)
                    
                    # 展示结果
                    if "error" in strategy:
                        st.error(strategy["error"])
                    else:
                        st.success("代码策略生成成功")
                        
                        # 展示原始文本
                        with st.expander("查看完整策略"):
                            st.text(strategy["raw_text"])
                        
                        # 展示结构化数据
                        if strategy["需求分析"]:
                            st.subheader("需求分析")
                            st.write(strategy["需求分析"])
                        
                        if strategy["技术选型"]:
                            st.subheader("技术选型")
                            st.write(strategy["技术选型"])
                        
                        if strategy["架构设计"]:
                            st.subheader("架构设计")
                            st.write(strategy["架构设计"])
                        
                        if strategy["实现步骤"]:
                            st.subheader("代码实现步骤")
                            st.write(strategy["实现步骤"])
                        
                        if strategy["测试策略"]:
                            st.subheader("测试策略")
                            st.write(strategy["测试策略"])
                        
                        if strategy["风险解决方案"]:
                            st.subheader("潜在风险及解决方案")
                            st.write(strategy["风险解决方案"])
            except Exception as e:
                st.error(f"生成代码策略时出错: {str(e)}")

elif module == "交易":
    st.title("同花顺交易系统")
    
    # 连接状态显示
    status_color = "绿色" if st.session_state.trader_connected else "红色"
    st.markdown(f"### 连接状态: <span style='color:{status_color}'>{'已连接' if st.session_state.trader_connected else '未连接'}</span>", unsafe_allow_html=True)
    
    # 连接/断开按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("连接同花顺客户端") and not st.session_state.trader_connected:
            try:
                trader.connect()
                st.session_state.trader_connected = True
                st.success("成功连接同花顺客户端")
            except Exception as e:
                st.error(f"连接失败: {str(e)}")
    with col2:
        if st.button("断开连接") and st.session_state.trader_connected:
            try:
                trader.disconnect()
                st.session_state.trader_connected = False
                st.success("已断开连接")
            except Exception as e:
                st.error(f"断开连接失败: {str(e)}")
    
    if st.session_state.trader_connected:
        # 账户资金信息
        st.subheader("账户资金信息")
        try:
            balance = trader.get_balance()
            if balance:
                st.write(f"总资产: {balance.get('总资产', 'N/A')}")
                st.write(f"可用资金: {balance.get('可用资金', 'N/A')}")
                st.write(f"持仓市值: {balance.get('持仓市值', 'N/A')}")
                st.write(f"可取资金: {balance.get('可取资金', 'N/A')}")
            else:
                st.warning("未获取到资金信息")
        except Exception as e:
            st.error(f"获取资金信息失败: {str(e)}")
        
        # 持仓查询
        st.subheader("持仓查询")
        try:
            positions = trader.get_position()
            if positions:
                df_positions = pd.DataFrame(positions)
                st.dataframe(df_positions)
            else:
                st.info("当前无持仓")
        except Exception as e:
            st.error(f"获取持仓信息失败: {str(e)}")
        
        # 交易操作
        st.subheader("交易操作")
        trade_type = st.radio("交易类型", ["买入", "卖出"])
        stock_code = st.text_input("证券代码", placeholder="请输入证券代码")
        stock_name = st.text_input("证券名称", placeholder="请输入证券名称")
        price = st.number_input("价格", min_value=0.01, step=0.01)
        quantity = st.number_input("数量", min_value=1, step=1)
        
        if st.button(f"确认{trade_type}"):
            try:
                if trade_type == "买入":
                    result = trader.buy(stock_code, stock_name, price, quantity)
                else:
                    result = trader.sell(stock_code, stock_name, price, quantity)
                st.success(f"{trade_type}成功: {result}")
            except Exception as e:
                st.error(f"{trade_type}失败: {str(e)}")
        
        # 撤单功能
        st.subheader("撤单功能")
        try:
            orders = trader.get_entrust()
            if orders:
                df_orders = pd.DataFrame(orders)
                st.dataframe(df_orders)
                order_id = st.text_input("委托编号", placeholder="请输入要撤销的委托编号")
                if st.button("撤销委托"):
                    try:
                        result = trader.cancel_order(order_id)
                        st.success(f"撤单成功: {result}")
                    except Exception as e:
                        st.error(f"撤单失败: {str(e)}")
            else:
                st.info("当前无委托")
        except Exception as e:
            st.error(f"获取委托信息失败: {str(e)}")
        
        # 当日成交
        st.subheader("当日成交")
        try:
            deals = trader.get_deal()
            if deals:
                df_deals = pd.DataFrame(deals)
                st.dataframe(df_deals)
            else:
                st.info("当前无成交记录")
        except Exception as e:
            st.error(f"获取成交信息失败: {str(e)}")
    else:
        st.info("请先连接同花顺客户端")

elif module == "新闻":
    st.title("财经新闻")
    st.sidebar.subheader("新闻设置")
    
    # 初始化新闻处理器
    if 'news_processor' not in st.session_state:
        st.session_state.news_processor = NewsProcessor()
    news_processor = st.session_state.news_processor
    
    # 显示调试信息选项
    show_debug_info = st.sidebar.checkbox("显示调试信息", value=False)
    
    # 新闻来源选择
    source_id = st.sidebar.selectbox(
        "选择新闻来源", 
        list(news_processor.news_sources.keys()),
        format_func=lambda x: news_processor.news_sources[x]['name']
    )
    
    # 刷新按钮
    if st.sidebar.button("刷新新闻"):
        st.session_state.news_cache = None
        st.session_state.cache_timestamp = None
        st.info("正在刷新新闻...")
    
    # 获取并显示新闻
    try:
        # 检查缓存和过期时间（设置5分钟过期）
        cache_expired = True
        if 'cache_timestamp' in st.session_state and st.session_state.cache_timestamp is not None:
            cache_age = (time.time() - st.session_state.cache_timestamp) / 60
            cache_expired = cache_age > 5
            if show_debug_info:
                st.sidebar.text(f"缓存年龄: {cache_age:.1f}分钟")
        
        if 'news_cache' not in st.session_state or st.session_state.news_cache is None or cache_expired:
            st.info(f"正在获取{news_processor.news_sources[source_id]['name']}的新闻...")
            # 显示正在使用的URL
            source_url = news_processor.news_sources[source_id]['url']
            if show_debug_info:
                st.sidebar.text(f"请求URL: {source_url}")
                
            try:
                news_list = news_processor.fetch_news(source_id)
                st.session_state.news_cache = news_list
                st.session_state.cache_timestamp = time.time()
                if show_debug_info:
                    st.sidebar.success(f"新闻获取成功，共{len(news_list)}条")
            except requests.exceptions.RequestException as e:
                st.error(f"网络请求错误: {str(e)}")
                if show_debug_info:
                    st.exception(e)
                news_list = []
            except ValueError as e:
                st.error(f"数据解析错误: {str(e)}")
                if show_debug_info:
                    st.exception(e)
                news_list = []
            except Exception as e:
                st.error(f"获取新闻时发生未知错误: {str(e)}")
                if show_debug_info:
                    st.exception(e)
                news_list = []
        else:
            news_list = st.session_state.news_cache
            st.info(f"使用缓存数据 (最后更新于 {datetime.fromtimestamp(st.session_state.cache_timestamp).strftime('%Y-%m-%d %H:%M:%S')})")
            if show_debug_info:
                st.sidebar.info(f"缓存数据量: {len(news_list)}条")
        
        if not news_list:
            st.warning("暂无新闻数据，请稍后重试")
            # 显示详细调试信息
            if show_debug_info:
                st.error("新闻列表为空，可能的原因:\n1. 网络连接问题\n2. 网站结构变化\n3. 解析器错误")
                # 显示新闻处理器状态
                st.sidebar.subheader("新闻处理器状态")
                st.sidebar.text(f"支持的来源数: {len(news_processor.news_sources)}")
                st.sidebar.text(f"当前来源: {news_processor.news_sources[source_id]['name']}")
        else:
            st.success(f"成功获取{len(news_list)}条新闻")
            
            # 显示新闻列表
            for i, news in enumerate(news_list[:20]):  # 只显示前20条
                with st.expander(f"{i+1}. {news['title']}", expanded=False):
                    # 确保pub_time是datetime对象
                    if isinstance(news['pub_time'], datetime):
                        pub_time_str = news['pub_time'].strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        pub_time_str = str(news['pub_time'])
                    st.markdown(f"**发布时间**: {pub_time_str}")
                    st.markdown(f"**来源**: {news['source']}")
                    if 'summary' in news and news['summary']:
                        st.markdown(f"**摘要**: {news['summary']}")
                    elif 'content' in news and news['content']:
                        # 如果没有摘要但有内容，显示前100个字符
                        st.markdown(f"**内容预览**: {news['content'][:100]}...")
                    # 确保URL有效
                    if 'url' in news and news['url'].startswith(('http://', 'https://')):
                        st.markdown(f"[阅读原文]({news['url']})", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**原文链接**: {news['url']}")
                    
                    # 显示原始数据结构（调试模式）
                    if show_debug_info:
                        with st.expander("查看原始数据", expanded=False):
                            st.json(news)
    except Exception as e:
        st.error(f"获取新闻失败: {str(e)}")
        # 显示详细错误信息
        if show_debug_info:
            st.error(f"错误详情: {str(e)}")
            st.exception(e)  # 显示完整的异常堆栈
            # 显示环境信息
            st.sidebar.subheader("环境信息")
            import sys
            st.sidebar.text(f"Python版本: {sys.version[:5]}")
            st.sidebar.text(f"Streamlit版本: {st.__version__}")
            st.sidebar.text(f"Requests版本: {requests.__version__}")

        # 获取当日分时数据（添加异常处理和健壮的数据处理）
        try:
            # 检查stock_code是否已定义
            if 'stock_code' not in locals() and 'stock_code' not in st.session_state:
                st.error("请先在行情模块中设置证券代码")
            else:
                # 使用session_state中的stock_code或当前作用域中的stock_code
                current_stock_code = st.session_state.get('stock_code', stock_code if 'stock_code' in locals() else '')
                if not current_stock_code:
                    st.error("未设置证券代码，请先在行情模块中输入")
                else:
                    stock_zh_a_minute_df = ak.stock_zh_a_minute(symbol=current_stock_code, period="1")
            
            # 检查数据是否为空
            if stock_zh_a_minute_df.empty:
                st.error("分时数据为空，请检查证券代码或非交易时间")
            else:
                # 尝试找到时间列（支持多种可能的列名）
                time_column = None
                for col in ['time', '日期', '时间', 'day']:
                    if col in stock_zh_a_minute_df.columns:
                        time_column = col
                        break
                
                # 尝试找到价格列（支持多种可能的列名）
                price_column = None
                for col in ['open', '开盘价', '价格', 'close', '收盘价']:
                    if col in stock_zh_a_minute_df.columns:
                        price_column = col
                        break
                
                # 检查是否找到必要的列
                if time_column is None or price_column is None:
                    missing_cols = []
                    if time_column is None:
                        missing_cols.append("时间列")
                    if price_column is None:
                        missing_cols.append("价格列")
                    st.error(f"分时数据格式异常，未找到有效{', '.join(missing_cols)}。")
                else:
                    # 数据清洗与标准化
                    df = stock_zh_a_minute_df.copy()
                    
                    # 转换时间格式
                    try:
                        df[time_column] = pd.to_datetime(df[time_column])
                    except Exception as e:
                        st.error(f"时间格式转换失败: {str(e)}")
                        df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
                        if df[time_column].isnull().any():
                            st.warning("部分时间数据转换失败，已用NaT代替")
                    
                    # 绘制分时图
                    fig_minute = go.Figure()
                    
                    # 保存原始时间值用于自定义tick
                    times = df[time_column].dt.strftime('%H:%M').tolist()
                    
                    # 使用索引作为x轴，确保连续显示
                    fig_minute.add_trace(go.Scatter(
                        x=list(range(len(df))), 
                        y=df[price_column], 
                        name="价格", 
                        line=dict(color='blue')
                    ))
                    
                    # 添加均线
                    df['MA5'] = df[price_column].rolling(window=5).mean()
                    fig_minute.add_trace(go.Scatter(
                        x=list(range(len(df))), 
                        y=df['MA5'], 
                        name="5分钟均线", 
                        line=dict(color='orange', dash='dash')
                    ))
                    
                    # 更新x轴，使用自定义tick文本显示时间
                    tick_step = max(1, len(df) // 8)  # 最多显示8个时间标签
                    tick_positions = list(range(0, len(df), tick_step))
                    tick_texts = [times[i] for i in tick_positions]
                    
                    # 更新布局
                    fig_minute.update_layout(title="当日分时图", height=400)
                    fig_minute.update_xaxes(
                        tickmode='array',
                        tickvals=tick_positions,
                        ticktext=tick_texts
                    )
                    st.plotly_chart(fig_minute, use_container_width=True)
        except Exception as e:
            st.error(f"获取分时数据失败：{str(e)}")
            # 打印AKShare版本信息，帮助调试
            import akshare
            st.write(f"AKShare版本: {akshare.__version__}")

elif module == "自选股":
    st.title("自选股分析")
    if st.session_state.get("watchlist"):
        for stock in st.session_state.watchlist:
            st.subheader(stock)
            # 获取实时行情数据
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Referer": "https://finance.sina.com.cn/"
                }
                url = f"https://hq.sinajs.cn/list=s_{stock}"
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 403:
                    st.error("获取实时行情失败：接口拒绝访问")
                else:
                    response.raise_for_status()
                    if response.text.lstrip().startswith('<'):
                        st.error("获取实时行情失败：接口返回异常内容")
                    else:
                        data_str_parts = response.text.split('=')
                        if len(data_str_parts) < 2:
                            st.error("获取实时行情失败：数据格式异常")
                        else:
                            data_str = data_str_parts[1].strip(';"')
                            if not data_str:
                                st.error("获取实时行情失败：返回空数据")
                            else:
                                data = data_str.split(',')
                                if len(data) >= 1:
                                    stock_name = data[0]
                                    st.subheader(f"{stock} - {stock_name}")
                                    actual_columns = ['代码', '名称']
                                    full_data = [stock, stock_name]
                                    field_mapping = [
                                        ('当前价', 1),
                                        ('涨跌额', 2),
                                        ('涨跌幅', 3),
                                        ('成交量', 4),
                                        ('成交额', 5)
                                    ]
                                    for field_name, index in field_mapping:
                                        if index < len(data) and data[index]:
                                            actual_columns.append(field_name)
                                            full_data.append(data[index])
                                    df = pd.DataFrame([full_data], columns=actual_columns)
                                    st.dataframe(df.iloc[0])
                                else:
                                    st.error("获取实时行情失败：数据为空")
            except Exception as e:
                st.error(f"获取实时行情失败：{str(e)}")
            
            # 获取分时数据并绘制分时图
            try:
                st.subheader(f"{stock} 分时图")
                # 获取分时数据
                k_df = ak.stock_zh_a_minute(symbol=stock, period="1")
                if k_df.empty:
                    st.error('分时数据为空，请检查证券代码或非交易时间')
                else:
                    # 尝试找到时间列和价格列
                    time_column = None
                    for col in ['time', '日期', '时间', 'day']:
                        if col in k_df.columns:
                            time_column = col
                            break
                    
                    price_column = None
                    for col in ['open', '开盘价', '价格', 'close', '收盘价']:
                        if col in k_df.columns:
                            price_column = col
                            break
                    
                    if time_column is None or price_column is None:
                        missing_cols = []
                        if time_column is None:
                            missing_cols.append("时间列")
                        if price_column is None:
                            missing_cols.append("价格列")
                        st.error(f"分时数据格式异常，未找到有效{', '.join(missing_cols)}。")
                    else:
                        # 数据清洗与标准化
                        df = k_df.copy()
                        
                        # 转换时间格式
                        try:
                            df[time_column] = pd.to_datetime(df[time_column])
                        except Exception as e:
                            st.error(f"时间格式转换失败: {str(e)}")
                            df[time_column] = pd.to_datetime(df[time_column], errors='coerce')
                            if df[time_column].isnull().any():
                                st.warning("部分时间数据转换失败，已用NaT代替")
                        
                        # 绘制分时图
                        fig_minute = go.Figure()
                        
                        # 保存原始时间值用于自定义tick
                        times = df[time_column].dt.strftime('%H:%M').tolist()
                        
                        # 使用索引作为x轴，确保连续显示
                        fig_minute.add_trace(go.Scatter(
                            x=list(range(len(df))), 
                            y=df[price_column], 
                            name="价格", 
                            line=dict(color='blue')
                        ))
                        
                        # 添加均线
                        df['MA5'] = df[price_column].rolling(window=5).mean()
                        fig_minute.add_trace(go.Scatter(
                            x=list(range(len(df))), 
                            y=df['MA5'], 
                            name="5分钟均线", 
                            line=dict(color='orange', dash='dash')
                        ))
                        
                        # 更新x轴，使用自定义tick文本显示时间
                        tick_step = max(1, len(df) // 8)  # 最多显示8个时间标签
                        tick_positions = list(range(0, len(df), tick_step))
                        tick_texts = [times[i] for i in tick_positions]
                        
                        # 更新布局
                        fig_minute.update_layout(title="当日分时图", height=400)
                        fig_minute.update_xaxes(
                            tickmode='array',
                            tickvals=tick_positions,
                            ticktext=tick_texts
                        )
                        st.plotly_chart(fig_minute, use_container_width=True)
            except Exception as e:
                st.error(f"获取分时数据或绘制分时图失败：{str(e)}")
            
            # 获取新闻数据
            news_df = ak.stock_news_em(symbol=stock)
            if not news_df.empty:
                st.caption("最新新闻：")
                st.dataframe(news_df.head(3), column_config={"内容":"新闻内容"})
            # 简单AI分析示例（涨跌幅）
            hist_df = ak.stock_zh_a_hist(symbol=stock, period="daily", adjust="qfq")
            if not hist_df.empty:
                recent_change = (hist_df["收盘"].iloc[-1] - hist_df["收盘"].iloc[-5])/hist_df["收盘"].iloc[-5]*100
                st.metric("近5日涨跌幅", f"{recent_change:.2f}%")
            
            # 添加分隔线
            st.markdown("---")

elif module == "设置":
    st.title("个性化设置")
    st.write("当前主题：", theme)

elif module == "回测策略":
    render_backtest_module()
    exec_globals = {
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
        # 打印完整错误信息以便调试
        import traceback
        st.text(f"详细错误信息:\n{traceback.format_exc()}")
        raise

    # 检查回测结果是否有效
    if result and isinstance(result, dict):
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



# 分时数据处理代码已移动到行情模块

elif market == "深圳证券交易所":
    # 获取深交所证券类别统计数据（示例日期）
    szse_df = ak.stock_szse_summary(date="202412")
    # 显示表格
    st.subheader("深圳证券交易所证券类别统计")
    st.dataframe(szse_df)
    # 可视化：各类证券成交金额占比
    fig = px.pie(szse_df, values="成交金额", names="证券类别", title="各类证券成交金额占比")
    st.plotly_chart(fig)

elif module == "智能分析":
    st.title("智能分析模块")
    from smart_analyzer import get_smart_analyzer
    import streamlit as st

    # 从secrets加载LLM配置
    try:
        openrouter_config = st.secrets["openrouter"]
        llm_config = {
            'api_provider': 'openrouter',
            'openrouter_api_key': openrouter_config["api_key"],
            'model': openrouter_config["model"],
            'base_url': openrouter_config["base_url"]
        }
    except KeyError as e:
        st.error(f"LLM配置错误: 缺少必要的密钥 - {str(e)}")
        llm_config = None

    # 初始化智能分析器
    analyzer = get_smart_analyzer(llm_config=llm_config) if llm_config else get_smart_analyzer()

    # 侧边栏配置
    st.sidebar.subheader("分析设置")
    stock_code = st.sidebar.text_input("输入证券代码", "sh600000")
    analysis_type = st.sidebar.selectbox("分析类型", ["综合分析", "趋势分析", "价格预测", "技术指标分析"])
    
    # 主内容区
    st.subheader(f"{analysis_type} - {stock_code}")
    
    if st.button("开始分析"):
        with st.spinner("正在进行分析，请稍候..."):
            if analysis_type == "综合分析":
                insights = analyzer.generate_insights(stock_code)
                if 'error' in insights:
                    st.error(insights['error'])
                else:
                    # 显示分析结果
                    st.info(f"分析日期: {insights['分析日期']}")
                    
                    # 趋势分析结果
                    st.subheader("趋势分析")
                    st.write(f"趋势判断: {insights['趋势分析']['趋势判断']}")
                    st.write(f"支撑位: {insights['趋势分析']['支撑位']:.2f}")
                    st.write(f"压力位: {insights['趋势分析']['压力位']:.2f}")
                    st.write(f"交易量分析: {insights['趋势分析']['交易量分析']}")
                    
                    # 技术指标信号
                    if insights['趋势分析']['技术指标信号']:
                        st.subheader("技术指标信号")
                        for signal in insights['趋势分析']['技术指标信号']:
                            st.write(f"- {signal}")
                    else:
                        st.write("无明显技术指标信号")
                    
                    # 交易建议
                    st.subheader("交易建议")
                    st.write(insights['建议操作'])
                    
                    # 绘制分析图表
                    st.subheader("分析图表")
                    fig = analyzer.plot_analysis(stock_code, insights)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.error("无法绘制分析图表")
            elif analysis_type == "趋势分析":
                # 获取数据
                df = analyzer.fetch_stock_data(stock_code)
                if df is None:
                    st.error(f"无法获取{stock_code}的有效数据")
                else:
                    # 计算技术指标
                    df = analyzer.calculate_technical_indicators(df)
                    
                    # 分析趋势
                    trend_analysis = analyzer.analyze_market_trend(df)
                    
                    # 显示结果
                    st.subheader("趋势分析结果")
                    st.write(f"趋势判断: {trend_analysis['趋势判断']}")
                    st.write(f"支撑位: {trend_analysis['支撑位']:.2f}")
                    st.write(f"压力位: {trend_analysis['压力位']:.2f}")
                    st.write(f"交易量分析: {trend_analysis['交易量分析']}")
                    
                    # 技术指标信号
                    if trend_analysis['技术指标信号']:
                        st.subheader("技术指标信号")
                        for signal in trend_analysis['技术指标信号']:
                            st.write(f"- {signal}")
                    else:
                        st.write("无明显技术指标信号")
                    
                    # 绘制价格走势图
                    st.subheader("价格走势图")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='收盘价'))
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5日均线'))
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20日均线'))
                    fig.update_layout(title=f'{stock_code} 价格走势', height=400)
                    st.plotly_chart(fig, use_container_width=True)
            elif analysis_type == "价格预测":
                # 获取数据
                df = analyzer.fetch_stock_data(stock_code)
                if df is None:
                    st.error(f"无法获取{stock_code}的有效数据")
                else:
                    # 预测价格
                    prediction_df = analyzer.predict_price(df)
                    
                    if prediction_df is None:
                        st.error("无法进行价格预测，请确保已安装scikit-learn库")
                    else:
                        # 显示预测结果
                        st.subheader("价格预测结果")
                        st.dataframe(prediction_df)
                        
                        # 绘制预测图表
                        st.subheader("价格预测图表")
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='历史价格'))
                        fig.add_trace(go.Scatter(x=prediction_df.index, y=prediction_df['预测价格'], name='预测价格', line=dict(color='red', dash='dot')))
                        fig.update_layout(title=f'{stock_code} 价格预测', height=400)
                        st.plotly_chart(fig, use_container_width=True)
            elif analysis_type == "技术指标分析":
                # 获取数据
                df = analyzer.fetch_stock_data(stock_code)
                if df is None:
                    st.error(f"无法获取{stock_code}的有效数据")
                else:
                    # 计算技术指标
                    df = analyzer.calculate_technical_indicators(df)
                    
                    # 创建技术指标图表
                    st.subheader("技术指标分析")
                    
                    # MACD
                    st.subheader("MACD指标")
                    fig_macd = go.Figure()
                    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD'))
                    fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal'))
                    fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=['green' if x > 0 else 'red' for x in df['MACD_Hist']]))
                    fig_macd.update_layout(height=300)
                    st.plotly_chart(fig_macd, use_container_width=True)
                    
                    # RSI
                    st.subheader("RSI指标")
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI'))
                    fig_rsi.add_hline(y=70, line_dash='dash', line_color='red')
                    fig_rsi.add_hline(y=30, line_dash='dash', line_color='green')
                    fig_rsi.update_layout(height=300)
                    st.plotly_chart(fig_rsi, use_container_width=True)
                    
                    # 布林带
                    st.subheader("布林带指标")
                    fig_bb = go.Figure()
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['close'], name='收盘价'))
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='上轨', line=dict(color='red', dash='dash')))
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='下轨', line=dict(color='red', dash='dash')))
                    fig_bb.add_trace(go.Scatter(x=df.index, y=df['BB_Mid'], name='中轨', line=dict(color='blue', dash='dash')))
                    fig_bb.update_layout(height=300)
                    st.plotly_chart(fig_bb, use_container_width=True)
                    
                    # 凤凰线指标
                    st.subheader("凤凰线指标")
                    fig_phoenix = go.Figure()
                    fig_phoenix.add_trace(go.Scatter(x=df.index, y=df['close'], name='收盘价'))
                    fig_phoenix.add_trace(go.Scatter(x=df.index, y=df['phoenix_line_upper'], name='凰线', line=dict(color='orange', dash='dash')))
                    fig_phoenix.add_trace(go.Scatter(x=df.index, y=df['phoenix_line_lower'], name='凤线', line=dict(color='purple', dash='dash')))
                    fig_phoenix.update_layout(height=300)
                    st.plotly_chart(fig_phoenix, use_container_width=True)


elif module == "公司/行业研究":
    # 现有公司/行业研究模块代码
    pass

elif module == "K线预测":
    st.title("Kronos K线预测")
    st.markdown("基于Kronos模型的股票价格趋势预测，支持未来1-30天的K线走势预测")
    
    # 输入区域
    col1, col2 = st.columns(2)
    with col1:
        stock_code = st.text_input("股票代码", "sh600000", help="输入格式如: sh600000 或 sz000001")
    with col2:
        predict_days = st.slider("预测天数", 1, 30, 7, help="选择要预测的天数，最多30天")
    
    # 模型选择
    model_option = st.selectbox(
        "选择模型",
        ("kronos-mini (快速)", "kronos-small (平衡)", "kronos-base (精准)"),
        index=0,
        help="mini模型速度快，base模型预测更精准但耗时较长"
    )
    model_name = model_option.split()[0]
    
    # 预测按钮
    if st.button("开始预测", use_container_width=True):
        if not stock_code:
            st.error("请输入有效的股票代码")
        else:
            try:
                with st.spinner(f"正在加载{model_option}模型并预测..."):
                    # 初始化预测器
                    predictor = KronosPredictor(model_name=model_name)
                    
                    # 检查模型是否加载成功
                    if not predictor.model_loaded:
                        st.error(f"模型加载失败: {predictor.model_error or '未知错误'}")
                    else:
                        # 执行预测
                        result_df = predictor.predict(stock_code, predict_days)
                        
                        # 检查预测结果是否包含错误
                        if 'error' in result_df.columns:
                            st.error(f"预测失败: {result_df['error'].iloc[0]}")
                        else:
                            # 显示预测结果
                            st.success(f"成功预测{stock_code}未来{predict_days}天K线走势")
                            
                            # 绘制预测K线图
                            st.subheader("预测K线图")
                            fig = go.Figure(data=[go.Candlestick(
                                x=result_df.index,
                                open=result_df['open'],
                                high=result_df['high'],
                                low=result_df['low'],
                                close=result_df['close'],
                                name='预测K线'
                            )])
                            fig.update_layout(
                                title=f"{stock_code} {predict_days}天K线预测",
                                xaxis_title="日期",
                                yaxis_title="价格",
                                xaxis_rangeslider_visible=False
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 显示预测数据表格
                            st.subheader("预测详细数据")
                            st.dataframe(result_df.style.format("{:.2f}"), use_container_width=True)
                            
                            # 预测说明
                            st.info("- 预测结果基于历史数据模式，仅供参考，不构成投资建议\n- 模型精度会受市场波动、突发新闻等因素影响\n- 长期预测(>14天)的不确定性显著增加")
            except Exception as e:
                st.error(f"预测过程出错: {str(e)}")
                st.exception(e)
    elif module == "公司/行业研究":
            st.title("公司/行业研究分析")
            st.write("该模块提供公司或行业信息查询及研究报告生成功能")

            # 导入公司研究工具
            from company_research import get_company_researcher

            # 创建侧边栏选项
            st.sidebar.subheader("研究设置")
            target_type = st.sidebar.radio("研究对象类型", ["公司", "行业"])
            
            # 输入框
            default_target = "腾讯控股" if target_type == "公司" else "互联网行业"
            target_name = st.text_input(f"请输入{target_type}名称", value=default_target)
            
            # 初始化研究器
            researcher = get_company_researcher()
            
            # 查询和生成报告按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("查询信息"):
                    with st.spinner(f"正在获取{target_type}信息，请稍候..."):
                        try:
                            if target_type == "公司":
                                info = researcher.search_company_info(target_name)
                            else:
                                info = researcher.search_industry_info(target_name)
                            
                            # 存储到会话状态
                            st.session_state.company_research_info = info
                            st.session_state.company_research_target_type = target_type
                            st.success(f"成功获取{target_name}的信息")
                        except Exception as e:
                            st.error(f"查询过程中发生错误: {str(e)}")
            
            with col2:
                if st.button("生成研究报告"):
                    with st.spinner(f"正在生成{target_type}研究报告，请稍候..."):
                        try:
                            # 检查是否已有信息，如果没有则先查询
                            if 'company_research_info' not in st.session_state or \
                               st.session_state.company_research_target_type != target_type or \
                               (target_type == "公司" and st.session_state.company_research_info.get('company_name') != target_name) or \
                               (target_type == "行业" and st.session_state.company_research_info.get('industry_name') != target_name):
                                if target_type == "公司":
                                    info = researcher.search_company_info(target_name)
                                else:
                                    info = researcher.search_industry_info(target_name)
                                st.session_state.company_research_info = info
                                st.session_state.company_research_target_type = target_type
                            
                            # 生成报告
                            report = researcher.generate_research_report(target_name, 'company' if target_type == '公司' else 'industry')
                            
                            # 存储报告
                            st.session_state.company_research_report = report
                            st.success(f"{target_name}研究报告生成成功")
                        except Exception as e:
                            st.error(f"生成报告过程中发生错误: {str(e)}")
            
            # 显示查询结果
            if 'company_research_info' in st.session_state and \
               st.session_state.company_research_target_type == target_type and \
               ((target_type == "公司" and st.session_state.company_research_info.get('company_name') == target_name) or \
                (target_type == "行业" and st.session_state.company_research_info.get('industry_name') == target_name)):
                
                info = st.session_state.company_research_info
                
                if target_type == "公司":
                    # 显示公司信息
                    st.subheader(f"{info.get('company_name', '')} - 基本信息")
                    
                    # 公司基本信息卡片
                    basic_info = info.get('basic_info', {})
                    col1, col2 = st.columns(2)
                    with col1:
                        for key, value in list(basic_info.items())[:len(basic_info)//2 + 1]:
                            st.text(f"{key}: {value}")
                    with col2:
                        for key, value in list(basic_info.items())[len(basic_info)//2 + 1:]:
                            st.text(f"{key}: {value}")
                    
                    # 财务摘要
                    financial = info.get('financial_summary', {})
                    if financial:
                        st.subheader("财务摘要")
                        financial_df = pd.DataFrame(list(financial.items()), columns=['指标', '数值'])
                        st.dataframe(financial_df, use_container_width=True)
                
                # 行业信息
                industry = info.get('industry_info', {})
                if industry:
                    st.subheader("行业信息")
                    for key, value in industry.items():
                        st.text(f"{key}: {value}")
                
                # 最新动态
                news = info.get('news', [])
                if news:
                    st.subheader("最新动态")
                    news_df = pd.DataFrame(news)
                    st.dataframe(news_df, use_container_width=True)
                
                # 风险提示
                risks = info.get('risks', [])
                if risks:
                    st.subheader("风险提示")
                    for risk in risks:
                        st.warning(f"- {risk}")
                
            else:
                # 显示行业信息
                st.subheader(f"{info.get('industry_name', '')} - 行业概览")
                st.write(info.get('overview', ''))
                
                # 市场规模
                market_size = info.get('market_size', {})
                if market_size:
                    st.subheader("市场规模")
                    market_size_df = pd.DataFrame(list(market_size.items()), columns=['年份', '规模(亿元)'])
                    st.dataframe(market_size_df, use_container_width=True)
                
                # 重点企业
                key_companies = info.get('key_companies', [])
                if key_companies:
                    st.subheader("重点企业")
                    for i, company in enumerate(key_companies, 1):
                        st.text(f"{i}. {company}")
                
                # 发展趋势
                growth_trend = info.get('growth_trend', {})
                if growth_trend:
                    st.subheader("发展趋势")
                    for key, value in growth_trend.items():
                        if key == 'drivers':
                            st.text(f"增长驱动因素:")
                            for driver in value:
                                st.text(f"  - {driver}")
                        else:
                            st.text(f"{key}: {value}")
                
                # 政策环境
                policies = info.get('policies', [])
                if policies:
                    st.subheader("政策环境")
                    for policy in policies:
                        st.text(f"- {policy}")
                
                # 风险分析
                risks = info.get('risks', [])
                if risks:
                    st.subheader("风险分析")
                    for risk in risks:
                        st.warning(f"- {risk}")
        
            # 显示研究报告
            if 'company_research_report' in st.session_state:
                st.subheader("研究报告")
                report = st.session_state.company_research_report
                
                # 显示报告内容
                st.markdown(report)
                
                # 提供下载功能
                st.download_button(
                    label="下载研究报告",
                    data=report,
                    file_name=f"{target_name}_{datetime.now().strftime('%Y%m%d')}_研究报告.txt",
                    mime="text/plain"
            )
        
            # 如果没有数据，显示提示信息
            if 'company_research_info' not in st.session_state:
                st.info("请输入公司或行业名称，然后点击'查询信息'或'生成研究报告'按钮")
    
elif module == "财务数据获取":
    st.title("财务数获取")
    st.write("获取上市公司财务数据，包括资产负债表、利润表和现金流量表等")
    
    # 创建财务数据获取器实例
    fetcher = FinancialDataFetcher()
    
    # 侧边栏输入
    st.sidebar.subheader("财务数据参数")
    stock_code = st.sidebar.text_input("输入股票代码（如sh600000）", "sh600000")
    fetch_button = st.sidebar.button("获取财务数据")
    save_excel = st.sidebar.checkbox("保存为Excel文件", value=True)
    
    if fetch_button:
        with st.spinner("正在获取财务数据..."):
            try:
                # 获取财务数据
                data_dict, file_path = fetcher.fetch_company_financial_data(stock_code, save_excel)
                
                # 显示基本信息
                st.subheader("公司基本信息")
                if data_dict["基本信息"] is not None:
                    st.dataframe(data_dict["基本信息"])
                else:
                    st.warning("无法获取公司基本信息")
                
                # 显示财务指标
                st.subheader("财务指标")
                if data_dict["财务指标"] is not None:
                    st.dataframe(data_dict["财务指标"])
                else:
                    st.warning("无法获取财务指标数据")
                
                # 显示利润表
                st.subheader("利润表")
                if data_dict["利润表"] is not None:
                    st.dataframe(data_dict["利润表"])
                else:
                    st.warning("无法获取利润表数据")
                
                # 显示资产负债表
                st.subheader("资产负债表")
                if data_dict["资产负债表"] is not None:
                    st.dataframe(data_dict["资产负债表"])
                else:
                    st.warning("无法获取资产负债表数据")
                
                # 显示现金流量表
                st.subheader("现金流量表")
                if data_dict["现金流量表"] is not None:
                    st.dataframe(data_dict["现金流量表"])
                else:
                    st.warning("无法获取现金流量表数据")
                
                # 显示保存路径
                if file_path:
                    st.success(f"财务数据已保存至: {file_path}")
            except Exception as e:
                st.error(f"获取财务数据失败: {str(e)}")
                logger.error(f"财务数据获取错误: {traceback.format_exc()}")

elif module == "财务数据分析":
    st.title("财务数据分析")
    st.write("分析已下载的财务数据文件，生成财务分析报告")
    
    # 创建财务分析集成器实例
    integrator = EnhancedFinancialAnalysisIntegrator()
    
    # 侧边栏输入
    st.sidebar.subheader("财务数据分析参数")
    
    # 获取可用的财务数据文件
    available_files = integrator.get_available_files()
    
    if available_files:
        # 显示文件选择下拉框
        file_options = {os.path.basename(f): f for f in available_files}
        selected_file = st.sidebar.selectbox("选择财务数据文件", list(file_options.keys()))
        analyze_button = st.sidebar.button("开始分析")
        
        # 显示文件信息
        file_path = file_options[selected_file]
        file_size = os.path.getsize(file_path) / 1024  # KB
        file_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        st.sidebar.markdown(f"**文件信息**<br>文件大小: {file_size:.2f} KB<br>修改时间: {file_time}", unsafe_allow_html=True)
        
        if analyze_button:
            with st.spinner(f"正在分析文件: {selected_file}..."):
                try:
                    # 执行分析
                    result = integrator.analyze_file(file_path)
                    
                    if result["success"]:
                        st.success("财务数据分析完成")
                        
                        # 显示分析摘要
                        st.subheader("分析摘要")
                        analysis_summary = result["analysis_summary"]
                        if analysis_summary:
                            st.markdown(analysis_summary)
                        
                        # 显示详细分析报告
                        st.subheader("详细分析报告")
                        report = result["report"]
                        if report:
                            # 以可折叠的方式显示报告
                            with st.expander("经营状况分析"):
                                st.markdown(report.get("经营状况", "无经营状况分析数据"))
                            
                            with st.expander("竞争优势分析"):
                                st.markdown(report.get("竞争优势", "无竞争优势分析数据"))
                            
                            with st.expander("风险因素分析"):
                                st.markdown(report.get("风险因素", "无风险因素分析数据"))
                            
                            with st.expander("投资建议"):
                                st.markdown(report.get("投资建议", "无投资建议数据"))
                        
                        # 显示报告保存路径
                        if result["report_file_path"]:
                            st.info(f"分析报告已保存至: {result['report_file_path']}")
                            
                            # 提供下载功能
                            with open(result["report_file_path"], 'r', encoding='utf-8') as f:
                                report_content = f.read()
                            
                            st.download_button(
                                label="下载分析报告",
                                data=report_content,
                                file_name=os.path.basename(result["report_file_path"]),
                                mime="application/json"
                            )
                    else:
                        st.error(f"分析失败: {result.get('error', '未知错误')}")
                        logger.error(f"财务分析错误: {result.get('error', '未知错误')}")
                except Exception as e:
                    st.error(f"分析过程中发生错误: {str(e)}")
                    logger.error(f"财务分析异常: {traceback.format_exc()}")
    else:
        st.warning("未找到可用的财务数据文件，请先使用'财务数据获取'模块下载数据")
        st.sidebar.info("请先使用'财务数据获取'模块下载财务数据")
   