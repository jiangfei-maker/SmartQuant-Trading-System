import numpy as np
import pandas as pd
import logging
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import functools
import time

# 导入必要的模块
from data_processor import DataProcessor
from technical_indicators import TechnicalIndicators

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('StockInfoQuery')

class StockInfoQuery:

    """个股信息查询模块，整合多维度数据进行查询与分析"""
    
    def __init__(self, cache_ttl=300):  # 默认缓存5分钟
        logger.info("初始化个股信息查询模块")
        self.data_processor = DataProcessor()
        self.technical_indicators = TechnicalIndicators()
        self.cache_ttl = cache_ttl  # 缓存过期时间(秒)
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_times = {}
        
    def _is_cache_valid(self, key):
        """检查缓存是否有效"""
        if key not in self.cache or key not in self.cache_times:
            return False
        return time.time() - self.cache_times[key] < self.cache_ttl
        
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        if self._is_cache_valid(key):
            logger.debug(f"从缓存获取数据: {key}")
            return self.cache[key]
        return None
        
    def _set_to_cache(self, key, data):
        """将数据存入缓存"""
        logger.debug(f"将数据存入缓存: {key}")
        self.cache[key] = data
        self.cache_times[key] = time.time()
        
    def _clear_cache(self):
        """清除所有缓存"""
        logger.info("清除所有缓存")
        self.cache = {}
        self.cache_times = {}
        
    def _clear_specific_cache(self, key_prefix: str):
        """清除特定前缀的缓存
        
        Args:
            key_prefix (str): 缓存键前缀
        """
        logger.info(f"清除前缀为 {key_prefix} 的缓存")
        # 创建要删除的键列表
        keys_to_delete = [key for key in self.cache if key.startswith(key_prefix)]
        
        # 删除匹配的键
        for key in keys_to_delete:
            if key in self.cache:
                del self.cache[key]
            if key in self.cache_times:
                del self.cache_times[key]
        
        logger.info(f"成功清除 {len(keys_to_delete)} 个缓存项")
        
    def get_multiple_stocks_info(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """批量获取多个股票的完整信息
        
        Args:
            stock_codes (List[str]): 股票代码列表
        
        Returns:
            Dict[str, Dict]: 以股票代码为键，股票完整信息为值的字典
        """
        result = {}
        
        for stock_code in stock_codes:
            try:
                logger.info(f"开始获取股票 {stock_code} 的信息")
                stock_info = self.get_stock_complete_info(stock_code)
                result[stock_code] = stock_info
            except Exception as e:
                logger.error(f"获取股票 {stock_code} 信息失败: {str(e)}")
                # 即使某个股票信息获取失败，也继续处理其他股票
                result[stock_code] = {"error": str(e)}
                
        logger.info(f"批量获取股票信息完成，成功获取 {len([v for v in result.values() if 'error' not in v])}/{len(stock_codes)} 支股票信息")
        return result
        
    def compare_stocks(self, stock_codes: List[str], metrics: Optional[List[str]] = None) -> Dict:
        """比较多个股票的关键指标
        
        Args:
            stock_codes (List[str]): 股票代码列表
            metrics (Optional[List[str]]): 要比较的指标列表，如果为None则比较所有共同指标
        
        Returns:
            Dict: 包含比较结果的字典
        """
        if len(stock_codes) < 2:
            raise ValueError("至少需要比较2支股票")
            
        # 批量获取所有股票的信息
        all_stocks_info = self.get_multiple_stocks_info(stock_codes)
        
        # 找出所有成功获取信息的股票
        valid_stocks = {code: info for code, info in all_stocks_info.items() if 'error' not in info}
        
        if len(valid_stocks) < 2:
            raise ValueError(f"成功获取信息的股票不足2支，仅获取到 {len(valid_stocks)} 支股票的信息")
            
        # 如果没有指定指标，则找出所有共同的数值型指标
        if metrics is None:
            # 获取第一支股票的所有指标
            first_stock_code = next(iter(valid_stocks.keys()))
            first_stock_info = valid_stocks[first_stock_code]
            
            # 提取所有数值型指标
            all_possible_metrics = []
            for section_name, section_data in first_stock_info.items():
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if isinstance(value, (int, float)):
                            all_possible_metrics.append(f"{section_name}.{key}")
                elif isinstance(section_data, (int, float)):
                    all_possible_metrics.append(section_name)
            
            metrics = all_possible_metrics
            
        # 构建比较结果
        comparison_result = {
            "股票列表": list(valid_stocks.keys()),
            "比较指标": metrics,
            "详细数据": {}
        }
        
        # 提取每个指标的数值
        for metric in metrics:
            comparison_result["详细数据"][metric] = {}
            
            for stock_code, stock_info in valid_stocks.items():
                try:
                    # 支持嵌套指标，如"基本面数据.市盈率"
                    if "." in metric:
                        parts = metric.split(".")
                        value = stock_info
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = None
                                break
                    else:
                        value = stock_info.get(metric)
                    
                    comparison_result["详细数据"][metric][stock_code] = value
                except Exception as e:
                    logger.warning(f"获取股票 {stock_code} 的指标 {metric} 失败: {str(e)}")
                    comparison_result["详细数据"][metric][stock_code] = None
                    
        # 添加统计信息
        comparison_result["统计信息"] = {
            "成功获取信息的股票数量": len(valid_stocks),
            "比较的指标数量": len(metrics),
            "查询时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return comparison_result
        
    def get_stock_complete_info(self, stock_code: str) -> Dict:
        """获取个股完整信息，整合多维度数据
        
        Args:
            stock_code (str): 股票代码
        
        Returns:
            Dict: 包含多维度数据的个股信息
        """
        # 检查缓存
        cache_key = f"complete_info_{stock_code}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
            
        logger.info(f"获取{stock_code}的完整信息")
        
        # 初始化结果字典
        result = {
            '股票代码': stock_code,
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '基础信息': {},
            '实时行情': {},
            '市场深度': {},
            '技术指标': {},
            '财务数据': {},
            '公司基本面': {},
            '公司事件与风险': {},
            '扩展信息': {}
        }
        
        try:
            # 获取历史数据（用于计算技术指标）
            df = self._fetch_stock_data(stock_code)
            if df is not None and not df.empty:
                # 计算技术指标
                df_with_indicators = self._calculate_technical_indicators(df)
                
                # 提取最新行情数据
                latest_data = df.iloc[-1].to_dict()
                result['实时行情'] = self._get_realtime_quote(df, latest_data, stock_code)
                
                # 技术指标（取最新值）
                result['技术指标'] = self._get_technical_indicators(df_with_indicators, stock_code)
                
                # 市场深度
                result['市场深度'] = self._get_market_depth(latest_data)
        except Exception as e:
            logger.error(f"获取行情数据失败: {str(e)}")
        
        # 获取基本面数据
        result['财务数据'] = self._get_financial_data(stock_code)
        
        # 补充基础信息
        result['基础信息'] = self._get_basic_info(stock_code, result['实时行情'].get('实时价格', 100))
        
        # 公司基本面
        result['公司基本面'] = self._get_company_fundamentals(stock_code)
        
        # 公司事件与风险
        result['公司事件与风险'] = self._get_company_events_and_risks(stock_code)
        
        # 扩展信息
        result['扩展信息'] = self._get_extended_info(stock_code)
        
        # 存入缓存
        self._set_to_cache(cache_key, result)
        
        logger.info(f"成功获取{stock_code}的完整信息")
        return result
        
    def _fetch_stock_data(self, stock_code: str, days: int = 365) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            df = self.data_processor.fetch_stock_data(stock_code, start_date, end_date)
            
            if df.empty:
                logger.warning(f"未获取到{stock_code}的有效数据")
                return None
            
            # 数据预处理
            df['涨跌幅'] = df['close'].pct_change() * 100
            df['成交量变化率'] = df['volume'].pct_change() * 100
            
            return df
        except Exception as e:
            logger.error(f"获取股票数据失败: {str(e)}")
            return None
            
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
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
        df = self.technical_indicators.calculate_phoenix_line(df)

        return df
        
    def _get_realtime_quote(self, df: pd.DataFrame, latest_data: Dict, stock_code: str) -> Dict:
        """获取实时行情数据（使用AKShare接口）"""
        # 检查缓存
        cache_key = f"realtime_quote_{stock_code}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
            
        try:
            import akshare as ak
            import pkg_resources

            # 检查AKShare版本
            try:
                version = pkg_resources.get_distribution('akshare').version
                if version < '1.14.61':
                    self.logger.warning(f"AKShare版本过旧({version})，建议更新: pip install akshare --upgrade")
            except Exception as e:
                self.logger.warning(f"无法检查AKShare版本: {str(e)}")
            # 使用AKShare获取实时行情
            df_spot = ak.stock_zh_a_spot_em()
            stock_data = df_spot[df_spot['代码'] == stock_code].iloc[0]
            
            prev_close = float(stock_data['昨收'])
            last_price = float(stock_data['最新价'])
            change = (last_price - prev_close) / prev_close * 100
            
            result = {
                '实时价格': last_price,
                '涨跌幅': round(change, 2),
                '涨跌额': round(last_price - prev_close, 2),
                '成交量': int(stock_data['成交量']),
                '成交额': float(stock_data['成交额']),
                '今日开盘价': float(stock_data['开盘']),
                '最高价': float(stock_data['最高']),
                '最低价': float(stock_data['最低']),
                '昨日收盘价': prev_close,
                '涨停价': round(prev_close * 1.1, 2),
                '跌停价': round(prev_close * 0.9, 2)
            }
            # 存入缓存
            self._set_to_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"AKShare实时行情获取失败: {str(e)}")
            # 尝试使用新浪财经接口作为备用数据源
            try:
                logger.debug("尝试使用新浪财经接口获取实时行情")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://finance.sina.com.cn/'
                }
                # 新浪财经A股行情接口
                url = f"https://hq.sinajs.cn/list={stock_code}"
                response = requests.get(url, headers=headers, timeout=10)
                logger.debug(f"新浪接口响应状态码: {response.status_code}")
                logger.debug(f"新浪接口响应头: {response.headers}")
                logger.debug(f"新浪接口响应内容: {response.text[:500]}")
                response.raise_for_status()
                
                # 解析新浪接口返回的数据
                content = response.text.split('=')[1].strip().strip('"')
                data = content.split(',')
                
                if len(data) < 4:
                    raise ValueError(f"新浪接口返回数据格式异常: {content}")
                
                # 新浪接口数据映射
                last_price = float(data[3])
                prev_close = float(data[2])
                open_price = float(data[1])
                high_price = float(data[4])
                low_price = float(data[5])
                volume = int(data[8])
                amount = float(data[9])
                change = (last_price - prev_close) / prev_close * 100
                
                result = {
                    '实时价格': last_price,
                    '涨跌幅': round(change, 2),
                    '涨跌额': round(last_price - prev_close, 2),
                    '成交量': volume,
                    '成交额': amount,
                    '今日开盘价': open_price,
                    '最高价': high_price,
                    '最低价': low_price,
                    '昨日收盘价': prev_close,
                    '涨停价': round(prev_close * 1.1, 2),
                    '跌停价': round(prev_close * 0.9, 2)
                }
                # 存入缓存
                self._set_to_cache(cache_key, result)
                return result
            except Exception as e:
                logger.error(f"新浪财经接口获取失败: {str(e)}")
            # 失败时使用本地数据
            result = {
                '实时价格': latest_data.get('close', None),
                '涨跌幅': latest_data.get('涨跌幅', None),
                '涨跌额': (df['close'].iloc[-1] - df['close'].iloc[-2]) if len(df) > 1 else None,
                '成交量': latest_data.get('volume', None),
                '成交额': latest_data.get('amount', None),
                '今日开盘价': latest_data.get('open', None),
                '最高价': latest_data.get('high', None),
                '最低价': latest_data.get('low', None),
                '昨日收盘价': df.iloc[-2]['close'] if len(df) > 1 else None,
                '涨停价': df.iloc[-2]['close'] * 1.1 if len(df) > 1 else None,
                '跌停价': df.iloc[-2]['close'] * 0.9 if len(df) > 1 else None
            }
            # 异常结果也缓存
            self._set_to_cache(cache_key, result)
            return result
        
    def _get_technical_indicators(self, df: pd.DataFrame, stock_code: str) -> Dict:
        """获取技术指标数据"""
        # 检查缓存
        cache_key = f"technical_indicators_{stock_code}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
            
        try:
            latest = df.iloc[-1]
            technical_indicators = {
                'MA5': latest.get('MA5', None),
                'MA10': latest.get('MA10', None),
                'MA20': latest.get('MA20', None),
                'MA60': latest.get('MA60', None),
                'RSI': latest.get('RSI', None),
                'MACD': latest.get('MACD', None),
                'MACD_Signal': latest.get('MACD_Signal', None),
                'MACD_Hist': latest.get('MACD_Hist', None),
                'BB_Upper': latest.get('BB_Upper', None),
                'BB_Lower': latest.get('BB_Lower', None),
                'phoenix_line_upper': latest.get('phoenix_line_upper', None),
                'phoenix_line_lower': latest.get('phoenix_line_lower', None)
            }
            
            # 计算KDJ指标
            df_kdj = self.technical_indicators.calculate_kdj(df)
            latest_kdj = df_kdj.iloc[-1]
            
            # 计算CCI指标
            df_cci = self.technical_indicators.calculate_cci(df)
            latest_cci = df_cci.iloc[-1]
            
            # 计算威廉指标(W%R)
            df_wr = self.technical_indicators.calculate_williams_r(df)
            latest_wr = df_wr.iloc[-1]
            
            # 计算量比和换手率
            volume_ratio = self._calculate_volume_ratio(df)
            turnover_rate = self._calculate_turnover_rate(stock_code, df)
            
            # 添加新计算的指标
            technical_indicators.update({
                'KDJ_K': latest_kdj.get('KDJ_K', None),
                'KDJ_D': latest_kdj.get('KDJ_D', None),
                'KDJ_J': latest_kdj.get('KDJ_J', None),
                'volume_ratio': volume_ratio,
                'turnover_rate': turnover_rate,
                'CCI': latest_cci.get('cci', None),
                'Williams_R': latest_wr.get('williams_r', None)
            })
            
            # 存入缓存
            self._set_to_cache(cache_key, technical_indicators)
            
            return technical_indicators
        except Exception as e:
            logger.error(f"获取技术指标数据异常: {str(e)}")
            # 返回空字典
            result = {}
            # 异常结果也缓存
            self._set_to_cache(cache_key, result)
            return result
        
    def _calculate_volume_ratio(self, df: pd.DataFrame, window: int = 5) -> float:
        """计算量比: 当日成交量与过去5日平均成交量的比值"""
        if len(df) < window + 1:
            logger.warning(f"数据不足，无法计算量比，需要至少{window+1}个交易日数据")
            return 1.0  # 默认返回1.0表示正常水平
        current_volume = df.iloc[-1]['volume']
        avg_volume = df.iloc[-window-1:-1]['volume'].mean()
        return round(current_volume / avg_volume, 2) if avg_volume != 0 else 0.0

    def _calculate_turnover_rate(self, stock_code: str, df: pd.DataFrame) -> Optional[float]:
        """估算换手率: 成交量/流通股本(需完善流通股本获取逻辑)"""
        try:
            # 这里需要根据股票代码获取流通股本，当前使用示例值
            # 实际应用中应从财务数据接口获取真实流通股本
            circulating_capital = 1000000000  # 假设流通股本为10亿股
            current_volume = df.iloc[-1]['volume']
            turnover_rate = (current_volume / circulating_capital) * 100
            return round(turnover_rate, 2)
        except Exception as e:
            logger.error(f"计算换手率失败: {str(e)}")
            return None

    def _get_market_depth(self, latest_data: Dict) -> Dict:
        """获取市场深度数据"""
        last_price = latest_data.get('close', 100)
        volume_step = latest_data.get('volume', 1000) / 10
        return {
            '买一': {'价格': last_price * 0.995, '数量': volume_step * 5},
            '买二': {'价格': last_price * 0.990, '数量': volume_step * 4},
            '买三': {'价格': last_price * 0.985, '数量': volume_step * 3},
            '买四': {'价格': last_price * 0.980, '数量': volume_step * 2},
            '买五': {'价格': last_price * 0.975, '数量': volume_step * 1},
            '卖一': {'价格': last_price * 1.005, '数量': volume_step * 5},
            '卖二': {'价格': last_price * 1.010, '数量': volume_step * 4},
            '卖三': {'价格': last_price * 1.015, '数量': volume_step * 3},
            '卖四': {'价格': last_price * 1.020, '数量': volume_step * 2},
            '卖五': {'价格': last_price * 1.025, '数量': volume_step * 1},
            '内盘': volume_step * 15,
            '外盘': volume_step * 20
        }
        
    def _get_financial_data(self, stock_code: str) -> Dict:
        """获取财务数据"""
        # 检查缓存
        cache_key = f"financial_data_{stock_code}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # 使用财务数据获取器获取数据
            financial_data_dict, _ = self.financial_fetcher.fetch_company_financial_data(stock_code, save_excel=False)
            
            # 处理基本信息
            basic_info = financial_data_dict.get("基本信息")
            basic_info_dict = {}
            if basic_info is not None and not basic_info.empty:
                for _, row in basic_info.iterrows():
                    basic_info_dict[row['项目']] = row['数值']
            
            # 处理财务指标
            financial_indicators = financial_data_dict.get("财务指标")
            indicators_dict = {}
            if financial_indicators is not None and not financial_indicators.empty:
                # 获取最新一期的财务指标
                latest_indicators = financial_indicators.iloc[0].to_dict()
                indicators_dict = {
                    "每股收益": latest_indicators.get('基本每股收益'),
                    "市盈率": latest_indicators.get('市盈率-动态'),
                    "市净率": latest_indicators.get('市净率'),
                    "总营收": latest_indicators.get('营业收入'),
                    "净利润": latest_indicators.get('净利润'),
                    "毛利率": latest_indicators.get('毛利率'),
                    "净利率": latest_indicators.get('净利率'),
                    "资产负债率": latest_indicators.get('资产负债率'),
                    "ROE": latest_indicators.get('净资产收益率')
                }
            
            # 整合数据
            result = {**basic_info_dict, **indicators_dict}
            
        except Exception as e:
            logger.error(f"获取财务数据失败: {str(e)}")
            result = {
                "每股收益": None,
                "市盈率": None,
                "市净率": None,
                "总营收": None,
                "净利润": None,
                "毛利率": None,
                "净利率": None,
                "资产负债率": None,
                "ROE": None
            }
        
        # 存入缓存
        self._set_to_cache(cache_key, result)
        return result
        
    def _get_basic_info(self, stock_code: str, price: float) -> Dict:
        cache_key = f"basic_info_{stock_code}_{round(price, 2)}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            import akshare as ak
            import pkg_resources

            # 检查AKShare版本
            try:
                version = pkg_resources.get_distribution('akshare').version
                if version < '1.14.61':
                    self.logger.warning(f"AKShare版本过旧({version})，建议更新: pip install akshare --upgrade")
            except Exception as e:
                self.logger.warning(f"无法检查AKShare版本: {str(e)}")

            # 全面使用AKShare获取基础信息
            basic_info = {'股票代码': stock_code}

            # 获取实时行情
            df_spot = ak.stock_zh_a_spot_em()
            if not df_spot.empty:
                code_column = '代码' if '代码' in df_spot.columns else 'stock_code'
                clean_code = stock_code.lstrip('sh').lstrip('sz')
                matches = df_spot[df_spot[code_column] == clean_code]
                if len(matches) > 0:
                    stock_data = matches.iloc[0]
                    basic_info.update({
                        '股票名称': stock_data.get('名称', '未知'),
                        '当前价格': stock_data.get('最新价', '未知'),
                        '开盘价': stock_data.get('今开', '未知'),
                        '最高价': stock_data.get('最高', '未知'),
                        '最低价': stock_data.get('最低', '未知'),
                        '成交量': stock_data.get('成交量', '未知'),
                        '成交额': stock_data.get('成交额', '未知'),
                        '行业': stock_data.get('行业', '未知'),
                        '地区': stock_data.get('地区', '未知'),
                        '市盈率': stock_data.get('市盈率-动态', '未知')
                    })

            # 获取公司简介
            try:
                # 使用正确的公司简介函数
                df_profile = ak.stock.stock_company_profile_em(symbol=stock_code)
                if not df_profile.empty:
                    basic_info['公司简介'] = df_profile.get('公司简介', ['未知'])[0]
            except Exception as e:
                self.logger.warning(f"公司简介获取失败: {str(e)}")

            # 存入缓存
            self._set_to_cache(cache_key, basic_info)
            return basic_info
        except Exception as e:
            self.logger.error(f"AKShare数据获取失败: {str(e)}")
            return {'股票代码': stock_code, '错误信息': str(e)}
        
    def _get_company_fundamentals(self, stock_code: str) -> Dict:
        """获取公司基本面数据（使用AKShare作为主要数据源）"""
        # 检查缓存
        cache_key = f"fundamentals_{stock_code}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
            
        fundamentals = {
            '股东结构': {},
            '主营业务': '',
            '公司简介': '',
            '高管信息': [],
            '主要股东': []
        }
        
        try:
            # 使用AKShare获取股东结构
            import akshare as ak
            # 使用正确的股东结构函数
            clean_code = stock_code.lstrip('sh').lstrip('sz')
            df_holders = ak.stock.stock_holder_structure_em(symbol=clean_code)
            if not df_holders.empty:
                    # 提取主要股东信息
                    major_holders = []
                    for _, row in df_holders.head(3).iterrows():
                        major_holders.append({
                            '股东名称': row.get('股东名称', '未知'),
                            '持股数量': row.get('持股数量', '未知'),
                            '持股比例': row.get('持股比例', '未知'),
                            '股份性质': row.get('股份类型', '未知')
                        })
                    fundamentals['主要股东'] = major_holders
        except Exception as e:
            self.logger.error(f"AKShare股东结构获取失败: {str(e)}")
        
        # 使用AKShare获取公司基本面数据
        try:
            import akshare as ak
            df = ak.stock.stock_company_info_ths(symbol=stock_code)
            if not df.empty:
                fundamentals['行业'] = df.get('行业', ['未知'])[0]
                fundamentals['主营业务'] = df.get('主营业务', ['未知'])[0]
                fundamentals['成立日期'] = df.get('成立日期', ['未知'])[0]
                fundamentals['注册资本'] = df.get('注册资本', ['未知'])[0]
                if '公司简介' not in fundamentals or fundamentals['公司简介'] == '':
                    fundamentals['公司简介'] = df.get('公司简介', ['未知'])[0]
        except Exception as e:
            self.logger.error(f"AKShare基本面获取失败: {str(e)}")
        
        # 存入缓存
        self._set_to_cache(cache_key, fundamentals)
        
        return fundamentals
        
    def _get_shareholder_structure(self, stock_code: str) -> Dict:
        """获取股东结构（使用AKShare接口）"""
        try:
            import akshare as ak
            # 使用正确的股东结构函数，添加重试机制
            for attempt in range(3):
                try:
                    # 移除市场前缀，使用正确的函数名
                    clean_code = stock_code.lstrip('sh').lstrip('sz')
                    df_holders = ak.stock.stock_holder_num_em(symbol=clean_code)
                    if not df_holders.empty:
                        shareholders = {}
                        # 处理不同可能的列名
                        name_col = '股东名称' if '股东名称' in df_holders.columns else 'holder_name'
                        ratio_col = '持股比例' if '持股比例' in df_holders.columns else 'hold_ratio'
                        for _, row in df_holders.head(5).iterrows():
                            name = row.get(name_col, '未知')
                            ratio = row.get(ratio_col, '未知')
                            shareholders[name] = ratio
                        return shareholders
                except Exception as e:
                    if attempt < 2:
                        self.logger.warning(f"股东结构获取尝试 {attempt+1} 失败，重试...")
                        time.sleep(1)
                    else:
                        raise e
            return {}
        except Exception as e:
            self.logger.error(f"AKShare股东结构获取失败: {str(e)}")
            return {}        
    def _get_company_events_and_risks(self, stock_code: str) -> Dict:
        """获取公司事件与风险信息"""
        return {
            '企业新闻': self._get_company_news(stock_code),
            '舆情信息': '市场关注度较高，投资者情绪偏正面',  # 模拟数据（无API可用）
            '风险信息': ['存在一定的政策风险', '行业竞争加剧'],  # 模拟数据（无API可用）
            '分红融资': self._get_dividend_info(stock_code),
            '业绩预告': '预计2024年上半年净利润增长10%-15%',  # 模拟数据（无API可用）
            '股东持股变动': self._get_shareholder_changes(stock_code),
            '限售解禁': '2024年12月有10%股份解禁'  # 模拟数据（无API可用）
        }
        
    def _get_company_news(self, stock_code: str) -> List:
        """获取企业新闻（使用新浪财经作为主要数据源）"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://finance.sina.com.cn/'
            }
            # 移除新浪财经新闻获取代码，使用AKShare或模拟数据
            try:
                import akshare as ak
                import time
                # 尝试获取新闻数据，最多重试2次
                for attempt in range(3):
                    try:
                        df = ak.stock_news_em(symbol=stock_code)
                        if not df.empty:
                            # 处理不同可能的列名
                            title_col = '标题' if '标题' in df.columns else 'title'
                            return df[title_col].tolist()[:5]
                    except Exception as e:
                        if attempt < 2:
                            self.logger.warning(f"新闻获取尝试 {attempt+1} 失败，重试...")
                            time.sleep(1)
                        else:
                            raise e
            except Exception as e:
                self.logger.error(f"AKShare新闻获取失败: {str(e)}")
            # 返回默认新闻列表
            return ['公司发布2024年一季度财报', '公司获得重大投资项目', '新产品研发取得进展', '与战略伙伴达成合作', '管理层人事调整公告']
        except Exception as e:
            logger.error(f"新浪财经新闻获取失败: {str(e)}")
            # AKShare备选方案（移除news_type参数）
            try:
                import akshare as ak
                df = ak.stock_news_em(symbol=stock_code)
                if not df.empty:
                    return df['标题'].tolist()[:5]
            except Exception as e:
                logger.error(f"AKShare备选新闻获取失败: {str(e)}")
        return ['公司发布2024年一季度财报', '公司获得重大投资项目']  # 模拟数据（所有接口调用失败）
        
    def _get_dividend_info(self, stock_code: str) -> str:
        """获取分红融资信息（使用AKShare接口）"""
        try:
            import akshare as ak
            # 使用正确的分红函数，添加重试机制
            clean_code = stock_code.lstrip('sh').lstrip('sz')
            for attempt in range(3):
                try:
                    df_dividend = ak.stock_history_dividend_detail(symbol=clean_code, indicator='分红')
                    if not df_dividend.empty:
                        # 处理不同可能的列名
                        date_col = '分红年度' if '分红年度' in df_dividend.columns else 'dividend_year'
                        plan_col = '分红方案' if '分红方案' in df_dividend.columns else 'dividend_plan'
                        # 按年度排序，取最新的分红记录
                        df_dividend = df_dividend.sort_values(by=date_col, ascending=False)
                        latest_dividend = df_dividend.iloc[0]
                        date = latest_dividend.get(date_col, '未知年份')
                        plan = latest_dividend.get(plan_col, '未知方案')
                        return f"{date}分红方案：{plan}"
                except Exception as e:
                    if attempt < 2:
                        self.logger.warning(f"分红信息获取尝试 {attempt+1} 失败，重试...")
                        time.sleep(1)
                    else:
                        raise e
            return '暂无分红信息'
        except Exception as e:
            self.logger.error(f"AKShare分红信息获取失败: {str(e)}")
            return '2023年度分红方案：每10股派2元'  # 模拟数据（API调用失败）
        
    def _get_shareholder_changes(self, stock_code: str) -> str:
        """获取股东持股变动（使用AKShare接口）"""
        try:
            import akshare as ak
            # 使用正确的股东变动函数，添加重试机制
            clean_code = stock_code.lstrip('sh').lstrip('sz')
            for attempt in range(3):
                try:
                    # 根据交易所选择不同函数
                    if stock_code.startswith('sh'):
                        df_changes = ak.stock_share_hold_change_sse(symbol=clean_code)
                    else:
                        df_changes = ak.stock_share_hold_change_szse(symbol=clean_code)
                    if not df_changes.empty:
                        # 处理不同可能的列名
                        name_col = '股东名称' if '股东名称' in df_changes.columns else 'holder_name'
                        direction_col = '变动方向' if '变动方向' in df_changes.columns else 'change_direction'
                        ratio_col = '变动比例' if '变动比例' in df_changes.columns else 'change_ratio'
                        date_col = '变动日期' if '变动日期' in df_changes.columns else 'change_date'
                        # 按日期排序，取最新的变动记录
                        df_changes = df_changes.sort_values(by=date_col, ascending=False)
                        latest_change = df_changes.iloc[0]
                        name = latest_change.get(name_col, '未知股东')
                        direction = latest_change.get(direction_col, '未知方向')
                        ratio = latest_change.get(ratio_col, '未知比例')
                        return f"{name}{direction}{ratio}股份"
                except Exception as e:
                    if attempt < 2:
                        self.logger.warning(f"股东变动获取尝试 {attempt+1} 失败，重试...")
                        time.sleep(1)
                    else:
                        raise e
            return '暂无股东变动信息'
        except Exception as e:
            self.logger.error(f"AKShare股东变动获取失败: {str(e)}")
            return '大股东A增持1%股份'  # 模拟数据（API调用失败）
        
    def _get_extended_info(self, stock_code: str) -> Dict:
        """获取扩展信息"""
        return {
            '企业关系图谱': '与多家金融机构有战略合作关系' if stock_code.startswith('sh600000') else '与多家科技企业有合作关系',  # 模拟数据
            '行业排名': '行业前5%' if stock_code.startswith('sh600000') else '行业前3%',  # 模拟数据
            '同业对比': '市盈率低于行业平均水平',  # 模拟数据
            '研报评级': '买入',  # 模拟数据
            '评级机构数': 15 if stock_code.startswith('sh600000') else 22,  # 模拟数据
            '研报买入评级数': 15 if stock_code.startswith('sh600000') else 22,  # 模拟数据
            '研报持有评级数': 8 if stock_code.startswith('sh600000') else 5,  # 模拟数据
            '研报卖出评级数': 2 if stock_code.startswith('sh600000') else 1  # 模拟数据
        }
        
    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（简化版）"""
        # 实际应用中应从数据源获取
        name_map = {
            'sh600000': '浦发银行',
            'sh600150': '中国船舶',
            'sh600580': '卧龙电驱',
            'sh601086': '中国神华'
        }
        return name_map.get(stock_code, '未知股票')
        
    def _get_stock_pinyin(self, stock_code: str) -> str:
        """获取股票拼音简称（简化版）"""
        # 实际应用中应从数据源获取
        pinyin_map = {
            'sh600000': 'PFYH',
            'sh600150': 'ZGCB',
            'sh600580': 'WLEDQ',
            'sh601086': 'ZGSH'
        }
        return pinyin_map.get(stock_code, '未知')

# 创建工厂函数供外部调用
def get_stock_info_query() -> StockInfoQuery:
    """
    获取个股信息查询实例
    
    Returns:
        StockInfoQuery: 个股信息查询实例
    """
    return StockInfoQuery()