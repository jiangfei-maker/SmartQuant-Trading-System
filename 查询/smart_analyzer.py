import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Optional
from technical_indicators import TechnicalIndicators
from stock_info_query import StockInfoQuery

# LLM服务导入
try:
    from llm_service import LLMQueryProcessor, get_llm_processor
    from config.llm_config import get_llm_config
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SmartAnalyzer')

class SmartAnalyzer:
    """智能分析模块，提供股票数据分析和预测功能"""
    def __init__(self, llm_api_key: str = None, llm_config: Dict = None):
        logger.info("初始化智能分析模块")
        
        # 尝试导入机器学习库
        try:
            import sklearn
            self.has_sklearn = True
            logger.info(f"成功导入scikit-learn版本: {sklearn.__version__}")
        except ImportError:
            self.has_sklearn = False
            logger.warning("未找到scikit-learn库，部分功能将受限")
        
        # 初始化LLM服务
        self.has_llm = False
        self.llm_processor = None
        
        # 构建LLM配置
        llm_config = llm_config or {}
        if llm_api_key:
            # 如果提供了API密钥，优先使用OpenRouter配置
            llm_config.update({
                'api_provider': 'openrouter',
                'openrouter_api_key': llm_api_key,
                'model': 'google/gemma-2-9b-it',
                'base_url': 'https://openrouter.ai/api/v1/'
            })
        
        if llm_config:
            try:
                self.llm_processor = get_llm_processor(llm_config)
                self.has_llm = True
                logger.info("LLM服务初始化成功")
            except ImportError:
                logger.warning("llm_service模块不可用，LLM功能将禁用")
            except Exception as e:
                logger.warning(f"LLM服务初始化失败: {str(e)}")
        else:
            logger.info("未提供LLM配置，LLM功能禁用")
        
        # 初始化股票信息查询模块
        self.stock_info_query = StockInfoQuery()

    def fetch_stock_data(self, stock_code, days=365):
        """获取股票数据

        Args:
            stock_code (str): 股票代码
            days (int): 获取多少天的数据

        Returns:
            pd.DataFrame: 股票数据
        """
        logger.info(f"获取股票数据: {stock_code}, 天数: {days}")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            # 使用DataProcessor获取数据，确保缓存和代码处理逻辑一致
            from data_processor import DataProcessor
            processor = DataProcessor()
            df = processor.fetch_stock_data(stock_code, start_date, end_date)
            
            if df.empty:
                logger.warning(f"未获取到{stock_code}的有效数据")
                return None
            
            # 数据预处理
            df['涨跌幅'] = df['close'].pct_change() * 100
            df['成交量变化率'] = df['volume'].pct_change() * 100
            
            logger.info(f"成功获取{stock_code}的{len(df)}条数据")
            return df
        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            return None

    def calculate_technical_indicators(self, df):
        """计算技术指标

        Args:
            df (pd.DataFrame): 股票数据

        Returns:
            pd.DataFrame: 包含技术指标的股票数据
        """
        logger.info("计算技术指标")

        # 移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()

        # 相对强弱指数(RSI)
        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        df['MACD'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

        # 布林带
        df['BB_Mid'] = df['close'].rolling(window=20).mean()
        df['BB_Upper'] = df['BB_Mid'] + 2 * df['close'].rolling(window=20).std()
        df['BB_Lower'] = df['BB_Mid'] - 2 * df['close'].rolling(window=20).std()
        
        # 凤凰线指标
        ti = TechnicalIndicators()
        df = ti.calculate_phoenix_line(df)

        return df

    def analyze_market_trend(self, df):
        """分析市场趋势

        Args:
            df (pd.DataFrame): 包含技术指标的股票数据

        Returns:
            dict: 趋势分析结果
        """
        logger.info("分析市场趋势")

        result = {
            '趋势判断': '中性',
            '支撑位': None,
            '压力位': None,
            '交易量分析': '中性',
            '技术指标信号': []
        }

        # 简单趋势判断 (均线系统)
        if df['MA5'].iloc[-1] > df['MA10'].iloc[-1] > df['MA20'].iloc[-1] > df['MA60'].iloc[-1]:
            result['趋势判断'] = '强烈上涨'
        elif df['MA5'].iloc[-1] > df['MA10'].iloc[-1] and df['MA10'].iloc[-1] > df['MA20'].iloc[-1]:
            result['趋势判断'] = '上涨'
        elif df['MA5'].iloc[-1] < df['MA10'].iloc[-1] < df['MA20'].iloc[-1] < df['MA60'].iloc[-1]:
            result['趋势判断'] = '强烈下跌'
        elif df['MA5'].iloc[-1] < df['MA10'].iloc[-1] and df['MA10'].iloc[-1] < df['MA20'].iloc[-1]:
            result['趋势判断'] = '下跌'

        # 支撑位和压力位 (最近20日的最高价和最低价)
        result['支撑位'] = df['low'].tail(20).min()
        result['压力位'] = df['high'].tail(20).max()

        # 交易量分析
        avg_volume = df['volume'].tail(20).mean()
        if df['volume'].iloc[-1] > avg_volume * 1.5:
            result['交易量分析'] = '放量'
        elif df['volume'].iloc[-1] < avg_volume * 0.5:
            result['交易量分析'] = '缩量'

        # 技术指标信号
        if df['RSI'].iloc[-1] > 70:
            result['技术指标信号'].append('RSI超买')
        elif df['RSI'].iloc[-1] < 30:
            result['技术指标信号'].append('RSI超卖')

        if df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] <= df['MACD_Signal'].iloc[-2]:
            result['技术指标信号'].append('MACD金叉')
        elif df['MACD'].iloc[-1] < df['MACD_Signal'].iloc[-1] and df['MACD'].iloc[-2] >= df['MACD_Signal'].iloc[-2]:
            result['技术指标信号'].append('MACD死叉')

        return result

    def predict_price(self, df, days=5):
        """预测未来价格

        Args:
            df (pd.DataFrame): 股票数据
            days (int): 预测天数

        Returns:
            pd.DataFrame: 预测结果
        """
        logger.info(f"预测未来{days}天价格")

        if not self.has_sklearn:
            logger.warning("未找到scikit-learn库，无法进行预测")
            return None

        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.model_selection import train_test_split

            # 准备数据
            df['Date_Ordinal'] = pd.to_datetime(df.index).map(pd.Timestamp.toordinal)
            X = df[['Date_Ordinal', 'open', 'high', 'low', 'volume']]
            y = df['close']

            # 分割训练集和测试集
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # 训练模型
            model = LinearRegression()
            model.fit(X_train, y_train)

            # 预测未来价格
            last_date = df.index[-1]
            future_dates = [last_date + timedelta(days=i) for i in range(1, days+1)]
            future_dates_ordinal = [date.toordinal() for date in future_dates]

            # 使用最后一天的数据作为基准来预测未来
            last_data = X.iloc[-1].values.tolist()
            future_data = []
            for ordinal in future_dates_ordinal:
                future_row = last_data.copy()
                future_row[0] = ordinal  # 更新日期
                future_data.append(future_row)

            future_predictions = model.predict(future_data)

            # 创建预测结果DataFrame
            prediction_df = pd.DataFrame({
                '日期': future_dates,
                '预测价格': future_predictions
            })
            prediction_df = prediction_df.set_index('日期')

            logger.info(f"成功预测未来{days}天价格")
            return prediction_df
        except Exception as e:
            logger.error(f"预测价格失败: {str(e)}")
            return None

    def generate_llm_analysis(self, query: str, stock_code: str) -> Dict:
        """使用LLM生成智能分析"""
        
        if not self.has_llm or not self.llm_processor:
            return {"error": "LLM服务不可用"}
        
        logger.info(f"使用LLM分析股票: {stock_code}, 查询: {query}")
        
        try:
            # 获取基础分析数据
            analysis_data = self._prepare_analysis_data(stock_code)
            if 'error' in analysis_data:
                return analysis_data
            
            # 使用LLM处理查询
            result = self.llm_processor.process_natural_language_query(
                query, stock_code, analysis_data
            )
            
            logger.info("LLM分析完成")
            return result
            
        except Exception as e:
            logger.error(f"LLM分析失败: {str(e)}")
            return {"error": f"分析失败: {str(e)}"}
    
    def _prepare_analysis_data(self, stock_code: str) -> Dict:
        """准备分析数据"""
        
        # 获取技术分析数据
        df = self.fetch_stock_data(stock_code, 365)
        if df is None or df.empty:
            return {"error": f"无法获取{stock_code}的有效数据"}
        
        df_with_indicators = self.calculate_technical_indicators(df)
        technical_analysis = self.analyze_market_trend(df_with_indicators)
        
        # 获取基本面数据（占位符，实际需要实现）
        fundamental_data = self._get_fundamental_data(stock_code)
        
        # 获取市场情绪数据（占位符，实际需要实现）
        market_sentiment = self._get_market_sentiment(stock_code)
        
        return {
            'technical_analysis': technical_analysis,
            'fundamental_data': fundamental_data,
            'market_sentiment': market_sentiment,
            'timestamp': datetime.now().isoformat(),
            'data_points': len(df)
        }
    
    def _get_fundamental_data(self, stock_code: str) -> Dict:
        """获取基本面数据（通过StockInfoQuery获取）"""
        return self.stock_info_query._get_financial_data(stock_code)
    
    def _get_market_sentiment(self, stock_code: str) -> Dict:
        """获取市场情绪数据（通过StockInfoQuery获取）"""
        company_events = self.stock_info_query._get_company_events_and_risks(stock_code)
        extended_info = self.stock_info_query._get_extended_info(stock_code)
        
        return {
            'sentiment_score': 0.6 if extended_info.get('研报评级') == '买入' else 0.5,
            'news_sentiment': company_events.get('舆情信息', '中性'),
            'social_media_sentiment': '中性',
            'analyst_ratings': extended_info.get('研报评级', '持有')
        }

    def generate_insights(self, stock_code):
        """生成综合分析见解

        Args:
            stock_code (str): 股票代码

        Returns:
            dict: 综合分析结果
        """
        logger.info(f"生成{stock_code}的综合分析见解")

        # 获取数据
        df = self.fetch_stock_data(stock_code)
        if df is None or df.empty:
            return {'error': f'无法获取{stock_code}的有效数据'}

        # 计算技术指标
        df = self.calculate_technical_indicators(df)

        # 分析趋势
        trend_analysis = self.analyze_market_trend(df)

        # 预测未来价格
        prediction_df = self.predict_price(df)

        # 生成综合见解
        insights = {
            '股票代码': stock_code,
            '分析日期': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '趋势分析': trend_analysis,
            '预测数据': prediction_df.to_dict() if prediction_df is not None else None,
            '建议操作': self._generate_trading_advice(trend_analysis)
        }

        # 如果LLM可用，添加LLM深度分析
        if self.has_llm and self.llm_processor:
            try:
                llm_analysis = self.generate_llm_analysis(
                    "请基于技术指标和市场趋势给出深度分析和投资建议", 
                    stock_code
                )
                if 'error' not in llm_analysis:
                    insights['llm_analysis'] = llm_analysis
                    logger.info(f"成功添加LLM深度分析")
                else:
                    logger.warning(f"LLM分析失败: {llm_analysis['error']}")
            except Exception as e:
                logger.warning(f"LLM分析异常: {str(e)}")

        logger.info(f"成功生成{stock_code}的综合分析见解")
        return insights

    def _generate_trading_advice(self, trend_analysis):
        """根据趋势分析生成交易建议

        Args:
            trend_analysis (dict): 趋势分析结果

        Returns:
            str: 交易建议
        """
        if trend_analysis['趋势判断'] == '强烈上涨' and 'RSI超买' not in trend_analysis['技术指标信号']:
            return '看多：考虑买入或持有'
        elif trend_analysis['趋势判断'] == '上涨' and 'RSI超买' not in trend_analysis['技术指标信号']:
            return '谨慎看多：可以考虑小仓位买入'
        elif trend_analysis['趋势判断'] == '强烈下跌' and 'RSI超卖' not in trend_analysis['技术指标信号']:
            return '看空：考虑卖出或做空'
        elif trend_analysis['趋势判断'] == '下跌' and 'RSI超卖' not in trend_analysis['技术指标信号']:
            return '谨慎看空：可以考虑减仓'
        elif 'RSI超买' in trend_analysis['技术指标信号']:
            return '注意：RSI超买，可能面临回调'
        elif 'RSI超卖' in trend_analysis['技术指标信号']:
            return '注意：RSI超卖，可能接近底部'
        else:
            return '中性：观望为主'

    def plot_analysis(self, stock_code, insights):
        """绘制分析图表

        Args:
            stock_code (str): 股票代码
            insights (dict): 分析见解

        Returns:
            plotly.graph_objects.Figure: 分析图表
        """
        logger.info(f"绘制{stock_code}的分析图表")

        # 获取数据
        df = self.fetch_stock_data(stock_code)
        if df is None or df.empty:
            return None

        # 计算技术指标
        df = self.calculate_technical_indicators(df)

        # 创建子图
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                           subplot_titles=(f'{stock_code} 价格走势', 'MACD', 'RSI'))

        # 价格走势
        fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='收盘价', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5日均线', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20日均线', line=dict(color='green', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='布林带上轨', line=dict(color='red', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='布林带下轨', line=dict(color='red', width=1, dash='dash')), row=1, col=1)

        # 如果有预测数据，添加到图表
        prediction_df = insights.get('预测数据')
        if prediction_df is not None:
            prediction_dates = list(prediction_df['预测价格'].keys())
            prediction_prices = list(prediction_df['预测价格'].values())
            fig.add_trace(go.Scatter(x=prediction_dates, y=prediction_prices, name='预测价格', line=dict(color='purple', dash='dot')), row=1, col=1)

        # MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='orange')), row=2, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='Histogram', marker_color=['green' if x > 0 else 'red' for x in df['MACD_Hist']]), row=2, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=3, col=1)
        fig.add_hline(y=70, line_dash='dash', line_color='red', row=3, col=1)
        fig.add_hline(y=30, line_dash='dash', line_color='green', row=3, col=1)

        # 更新布局
        fig.update_layout(height=800, title_text=f'{stock_code} 技术分析图表')

        logger.info(f"成功绘制{stock_code}的分析图表")
        return fig

    def get_stock_complete_info(self, stock_code: str) -> Dict:
        """获取个股完整信息，整合多维度数据
        
        Args:
            stock_code (str): 股票代码
        
        Returns:
            Dict: 包含多维度数据的个股信息
        """
        logger.info(f"获取{stock_code}的完整信息")
        
        # 通过StockInfoQuery获取完整信息
        return self.stock_info_query.get_stock_complete_info(stock_code)

# 初始化智能分析器（供外部调用）
def get_smart_analyzer(llm_api_key: str = None, llm_config: Dict = None):
    """
    获取智能分析器实例
    
    Args:
        llm_api_key (str, optional): API密钥，如果提供则启用LLM功能
        llm_config (Dict, optional): LLM配置字典，可指定API提供商等参数
    
    Returns:
        SmartAnalyzer: 智能分析器实例
    """
    return SmartAnalyzer(llm_api_key=llm_api_key, llm_config=llm_config)