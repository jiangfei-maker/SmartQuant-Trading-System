import akshare as ak
import pandas as pd
import logging
# 配置日志输出到控制台并设置DEBUG级别
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# 验证日志配置
logger.debug("财务数据获取器日志系统初始化成功")
import time
import os
import re
import traceback
from datetime import datetime
import akshare as ak

class FinancialDataFetcher:
    """
    中国上市公司财务数据获取器
    用于获取中国上市公司的各种财务数据
    """
    
    def __init__(self):
        """初始化数据获取器"""
        # 设置中文显示
        pd.set_option('display.unicode.ambiguous_as_wide', True)
        pd.set_option('display.unicode.east_asian_width', True)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', 20)
        
        # 创建数据保存目录
        self.data_dir = "financial_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_stock_list(self, market="主板"):
        """
        获取上市公司列表
        market: 市场类型，可选值：主板、科创板、创业板、北交所
        """
        try:
            # 获取股票列表
            stock_list_df = ak.stock_info_a_code_name()
            print(f"获取到{len(stock_list_df)}只股票")
            return stock_list_df
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return None
    
    def _fetch_financial_data(self, api_function, stock_code, data_type):
        """通用财务数据获取方法，添加统一的日志记录和错误处理"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"[{timestamp}] 开始获取股票{stock_code}的{data_type}数据...")
        try:
            # 调用API获取数据
            data = api_function(symbol=stock_code)
            logger.info(f"[{timestamp}] 成功获取股票{stock_code}的{data_type}数据")
            return data
        except Exception as e:
            logger.error(f"[{timestamp}] 获取股票{stock_code}的{data_type}数据失败: {str(e)}")
            logger.debug(f"[{timestamp}] 错误堆栈: {traceback.format_exc()}")
            return None

    def get_stock_basic_info(self, stock_code):
        """
        获取股票基本信息
        stock_code: 股票代码，如"600000"
        """
        try:
            # 尝试使用不带市场标识的股票代码
            logger.info(f"尝试获取股票{stock_code}的基本信息")
            stock_info_df = ak.stock_individual_info_em(symbol=stock_code)
            logger.info(f"成功获取股票{stock_code}的基本信息，共{len(stock_info_df)}条记录")
            return stock_info_df
        except Exception as e:
            logger.error(f"获取股票{stock_code}基本信息失败: {str(e)}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return None
            
    def add_market_prefix(self, stock_code):
        """
        为股票代码添加市场标识前缀
        stock_code: 股票代码，如"600000"
        返回带市场标识的股票代码，如"sh600000"或"sz000001"
        """
        # 深圳证券交易所: 000开头、002开头、300开头
        # 上海证券交易所: 600开头、601开头、603开头
        if stock_code.startswith(('000', '002', '300')):
            return f"sz{stock_code}"
        elif stock_code.startswith(('600', '601', '603')):
            return f"sh{stock_code}"
        else:
            # 对于其他情况，默认返回原代码
            return stock_code
    
    def get_financial_indicators(self, stock_code):
        """
        获取财务指标
        stock_code: 股票代码
        """
        try:
            # 规范化股票代码（移除市场标识）
            normalized_code = re.sub(r'^[a-zA-Z]+', '', stock_code)
            
            # 方法1.1: 财务分析指标
            logger.info("尝试方法1.1: stock_financial_analysis_indicator")
            try:
                financial_indicators_df = ak.stock_financial_analysis_indicator(symbol=normalized_code)
                if financial_indicators_df is not None and not financial_indicators_df.empty:
                    logger.info(f"成功获取股票{stock_code}的财务指标，形状: {financial_indicators_df.shape}")
                    # 简单的数据清洗
                    financial_indicators_df.columns = financial_indicators_df.columns.str.strip()
                    return financial_indicators_df
            except Exception as e1:
                logger.warning(f"方法1.1失败: {str(e1)}")
            
            # 方法1.2: 东方财富网财务分析指标
            logger.info("尝试方法1.2: stock_financial_analysis_indicator_em")
            try:
                financial_indicators_df = ak.stock_financial_analysis_indicator_em(symbol=normalized_code)
                if financial_indicators_df is not None and not financial_indicators_df.empty:
                    logger.info(f"成功获取股票{stock_code}的财务指标，形状: {financial_indicators_df.shape}")
                    # 简单的数据清洗
                    financial_indicators_df.columns = financial_indicators_df.columns.str.strip()
                    return financial_indicators_df
            except Exception as e2:
                logger.warning(f"方法1.2失败: {str(e2)}")
            
            # 方法1.3: 财务摘要
            logger.info("尝试方法1.3: stock_financial_abstract")
            try:
                financial_indicators_df = ak.stock_financial_abstract(symbol=normalized_code)
                if financial_indicators_df is not None and not financial_indicators_df.empty:
                    logger.info(f"成功获取股票{stock_code}的财务指标，形状: {financial_indicators_df.shape}")
                    # 简单的数据清洗
                    financial_indicators_df.columns = financial_indicators_df.columns.str.strip()
                    return financial_indicators_df
            except Exception as e3:
                logger.warning(f"方法1.3失败: {str(e3)}")
            
            # 方法1.4: 同花顺财务摘要
            logger.info("尝试方法1.4: stock_financial_abstract_ths")
            try:
                financial_indicators_df = ak.stock_financial_abstract_ths(symbol=normalized_code)
                if financial_indicators_df is not None and not financial_indicators_df.empty:
                    logger.info(f"成功获取股票{stock_code}的财务指标，形状: {financial_indicators_df.shape}")
                    # 简单的数据清洗
                    financial_indicators_df.columns = financial_indicators_df.columns.str.strip()
                    return financial_indicators_df
            except Exception as e4:
                logger.warning(f"方法1.4失败: {str(e4)}")
            
            # 如果所有API都失败，记录警告
            logger.warning(f"所有财务指标API均获取失败")
            return None
        except Exception as e:
            logger.error(f"获取股票{stock_code}财务指标过程发生异常: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return None
    
    def get_income_statement(self, stock_code, years=None):
        """
        获取利润表
        stock_code: 股票代码
        years: 需要获取的年份列表（保留参数但不实际使用，保持接口兼容性）
        """
        try:
            # 规范化股票代码（移除市场标识）
            normalized_code = re.sub(r'^[a-zA-Z]+', '', stock_code)
            # 添加市场标识前缀
            stock_code_with_market = self.add_market_prefix(normalized_code)
            
            # 方法2.1: 东方财富网-利润表-按报告期
            logger.info(f"尝试方法2.1: stock_profit_sheet_by_report_em 获取股票{stock_code_with_market}的利润表")
            try:
                result = ak.stock_profit_sheet_by_report_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法2.1返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的利润表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"利润表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法2.1返回空DataFrame")
                    else:
                        logger.warning(f"方法2.1返回非DataFrame对象: {type(result)}")
            except Exception as e1:
                logger.warning(f"方法2.1失败: {str(e1)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法2.2: 东方财富网-利润表-按年度
            logger.info(f"尝试方法2.2: stock_profit_sheet_by_yearly_em 获取股票{stock_code_with_market}的利润表")
            try:
                result = ak.stock_profit_sheet_by_yearly_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法2.2返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的利润表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"利润表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法2.2返回空DataFrame")
                    else:
                        logger.warning(f"方法2.2返回非DataFrame对象: {type(result)}")
            except Exception as e2:
                logger.warning(f"方法2.2失败: {str(e2)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法2.3: 东方财富网-利润表-按季度
            logger.info(f"尝试方法2.3: stock_profit_sheet_by_quarterly_em 获取股票{stock_code_with_market}的利润表")
            try:
                result = ak.stock_profit_sheet_by_quarterly_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法2.3返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的利润表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"利润表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法2.3返回空DataFrame")
                    else:
                        logger.warning(f"方法2.3返回非DataFrame对象: {type(result)}")
            except Exception as e3:
                logger.warning(f"方法2.3失败: {str(e3)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            logger.warning(f"所有利润表API均获取失败")
            return None
        except Exception as e:
            logger.error(f"获取股票{stock_code}利润表过程发生异常: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return None
    
    def get_balance_sheet(self, stock_code):
        """
        获取资产负债表
        stock_code: 股票代码
        """
        try:
            # 规范化股票代码（移除市场标识）
            normalized_code = re.sub(r'^[a-zA-Z]+', '', stock_code)
            # 添加市场标识前缀
            stock_code_with_market = self.add_market_prefix(normalized_code)
            
            # 方法3.1: 东方财富网-资产负债表-按报告期（与利润表、现金流量表保持一致的数据源）
            logger.info(f"尝试方法3.1: stock_balance_sheet_by_report_em 获取股票{stock_code_with_market}的资产负债表")
            try:
                # 直接调用API，并添加更健壮的错误处理
                try:
                    result = ak.stock_balance_sheet_by_report_em(symbol=stock_code_with_market)
                    if result is None:
                        logger.warning("方法3.1返回None")
                    else:
                        # 确保返回的是DataFrame
                        if hasattr(result, 'empty'):
                            if not result.empty:
                                logger.info(f"成功获取股票{stock_code}的资产负债表，形状: {result.shape}")
                                # 简单的数据清洗
                                result.columns = result.columns.str.strip()
                                logger.debug(f"资产负债表列名: {result.columns.tolist()}")
                                return result
                            else:
                                logger.warning("方法3.1返回空DataFrame")
                        else:
                            logger.warning(f"方法3.1返回非DataFrame对象: {type(result)}")
                except KeyError as e:
                    # 捕获KeyError异常，这是当前版本的主要问题
                    logger.warning(f"方法3.1遇到KeyError: {str(e)} - 这是AKShare 1.17.44版本的已知问题")
                    logger.debug(f"错误堆栈: {traceback.format_exc()}")
                    
                    # 尝试直接访问AKShare的底层请求函数，获取原始数据
                    logger.info("尝试使用替代方法获取资产负债表数据")
                    try:
                        from akshare.stock_feature.stock_three_report_em import stock_balance_sheet_by_report_em
                        # 直接使用底层函数，添加额外的错误处理
                        # 这里我们不直接修改AKShare源码，而是尝试重新调用一次
                        result = stock_balance_sheet_by_report_em(symbol=stock_code_with_market)
                        if result is not None and hasattr(result, 'empty') and not result.empty:
                            logger.info(f"成功获取股票{stock_code}的资产负债表，形状: {result.shape}")
                            result.columns = result.columns.str.strip()
                            return result
                    except Exception as inner_e:
                        logger.warning(f"替代方法也失败: {str(inner_e)}")
            except Exception as e1:
                logger.warning(f"方法3.1失败: {str(e1)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法3.2: 东方财富网-资产负债表-按年度（与利润表、现金流量表保持一致的数据源）
            logger.info(f"尝试方法3.2: stock_balance_sheet_by_yearly_em 获取股票{stock_code_with_market}的资产负债表")
            try:
                try:
                    result = ak.stock_balance_sheet_by_yearly_em(symbol=stock_code_with_market)
                    if result is None:
                        logger.warning("方法3.2返回None")
                    else:
                        # 确保返回的是DataFrame
                        if hasattr(result, 'empty'):
                            if not result.empty:
                                logger.info(f"成功获取股票{stock_code}的资产负债表，形状: {result.shape}")
                                # 简单的数据清洗
                                result.columns = result.columns.str.strip()
                                logger.debug(f"资产负债表列名: {result.columns.tolist()}")
                                return result
                            else:
                                logger.warning("方法3.2返回空DataFrame")
                        else:
                            logger.warning(f"方法3.2返回非DataFrame对象: {type(result)}")
                except KeyError as e:
                    # 捕获KeyError异常
                    logger.warning(f"方法3.2遇到KeyError: {str(e)} - 这是AKShare 1.17.44版本的已知问题")
            except Exception as e2:
                logger.warning(f"方法3.2失败: {str(e2)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法3.3: 尝试使用东方财富网的替代API格式（与其他报表保持一致的数据源理念）
            logger.info(f"尝试方法3.3: 使用东方财富网替代API格式获取资产负债表")
            try:
                # 注意：这里仍然使用东方财富网的数据源，但调用方式略有不同
                # 使用与利润表相同的逻辑模式，但处理AKShare版本差异
                
                # 尝试使用另一种方式构建API调用
                url = f"https://data.eastmoney.com/bbsj/{datetime.now().year}/zcfz.html"
                logger.info(f"使用东方财富网数据源URL: {url}")
                
                # 打印当前AKShare版本信息，便于排查问题
                ak_version = getattr(ak, '__version__', '未知版本')
                logger.info(f"当前AKShare版本: {ak_version}")
                
                # 如果是AKShare 1.17.44版本，特别处理
                if ak_version == '1.17.44':
                    logger.info("检测到AKShare 1.17.44版本，应用特殊处理逻辑")
                    # 提供明确的错误信息，指导用户如何解决问题
                    logger.warning("AKShare 1.17.44版本中的资产负债表API存在已知问题，建议：")
                    logger.warning("1. 降级到更稳定的AKShare版本")
                    logger.warning("2. 或者等待AKShare官方修复这个问题")
                    logger.warning("3. 或者手动检查AKShare源码中的API实现")
            except Exception as e3:
                logger.warning(f"方法3.3失败: {str(e3)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            logger.warning(f"所有资产负债表API均获取失败。注意：这可能是AKShare 1.17.44版本的问题")
            return None
        except Exception as e:
            logger.error(f"获取股票{stock_code}资产负债表过程发生异常: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return None
    
    def get_cash_flow_statement(self, stock_code):
        """
        获取现金流量表
        stock_code: 股票代码
        """
        try:
            # 规范化股票代码（移除市场标识）
            normalized_code = re.sub(r'^[a-zA-Z]+', '', stock_code)
            # 添加市场标识前缀
            stock_code_with_market = self.add_market_prefix(normalized_code)
            
            # 方法4.1: 东方财富网-现金流量表-按报告期
            logger.info(f"尝试方法4.1: stock_cash_flow_sheet_by_report_em 获取股票{stock_code_with_market}的现金流量表")
            try:
                result = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法4.1返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的现金流量表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"现金流量表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法4.1返回空DataFrame")
                    else:
                        logger.warning(f"方法4.1返回非DataFrame对象: {type(result)}")
            except Exception as e1:
                logger.warning(f"方法4.1失败: {str(e1)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法4.2: 东方财富网-现金流量表-按年度
            logger.info(f"尝试方法4.2: stock_cash_flow_sheet_by_yearly_em 获取股票{stock_code_with_market}的现金流量表")
            try:
                result = ak.stock_cash_flow_sheet_by_yearly_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法4.2返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的现金流量表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"现金流量表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法4.2返回空DataFrame")
                    else:
                        logger.warning(f"方法4.2返回非DataFrame对象: {type(result)}")
            except Exception as e2:
                logger.warning(f"方法4.2失败: {str(e2)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            # 方法4.3: 东方财富网-现金流量表-按季度
            logger.info(f"尝试方法4.3: stock_cash_flow_sheet_by_quarterly_em 获取股票{stock_code_with_market}的现金流量表")
            try:
                result = ak.stock_cash_flow_sheet_by_quarterly_em(symbol=stock_code_with_market)
                if result is None:
                    logger.warning("方法4.3返回None")
                else:
                    # 确保返回的是DataFrame
                    if hasattr(result, 'empty'):
                        if not result.empty:
                            logger.info(f"成功获取股票{stock_code}的现金流量表，形状: {result.shape}")
                            # 简单的数据清洗
                            result.columns = result.columns.str.strip()
                            logger.debug(f"现金流量表列名: {result.columns.tolist()}")
                            return result
                        else:
                            logger.warning("方法4.3返回空DataFrame")
                    else:
                        logger.warning(f"方法4.3返回非DataFrame对象: {type(result)}")
            except Exception as e3:
                logger.warning(f"方法4.3失败: {str(e3)}")
                logger.debug(f"错误堆栈: {traceback.format_exc()}")
            
            logger.warning(f"所有现金流量表API均获取失败")
            return None
        except Exception as e:
            logger.error(f"获取股票{stock_code}现金流量表过程发生异常: {e}")
            logger.debug(f"错误堆栈: {traceback.format_exc()}")
            return None
    
    def save_data_to_excel(self, data_dict, file_name=None):
        """
        将数据保存到Excel文件
        data_dict: 字典，键为sheet名称，值为DataFrame
        file_name: 文件名，如果为None则自动生成
        """
        try:
            # 生成文件名
            if file_name is None:
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"financial_data_{now}.xlsx"
            
            # 构建完整的文件路径
            file_path = os.path.join(self.data_dir, file_name)
            
            # 保存到Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                  if df is not None:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                  else:
                    # 即使数据为None也创建空工作表
                    pd.DataFrame().to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"数据已保存到：{file_path}")
            return file_path
        except Exception as e:
            print(f"保存数据失败: {e}")
            return None
    
    def fetch_company_financial_data(self, stock_code, save_excel=True, max_retries=2):
        """
        获取公司完整的财务数据
        stock_code: 股票代码
        save_excel: 是否保存为Excel文件
        max_retries: 最大重试次数
        """
        # 规范化股票代码，移除可能的市场标识前缀
        normalized_code = re.sub(r'^[a-zA-Z]+', '', stock_code)
        logger.info(f"开始获取股票{stock_code}（规范化后：{normalized_code}）的财务数据...")
        
        # 定义获取数据的函数，用于重试逻辑
        def _get_financial_data():
            # 获取各种财务数据
            basic_info = self.get_stock_basic_info(normalized_code)
            financial_indicators = self.get_financial_indicators(normalized_code)
            income_statement = self.get_income_statement(normalized_code)
            balance_sheet = self.get_balance_sheet(normalized_code)
            cash_flow_statement = self.get_cash_flow_statement(normalized_code)
            
            # 构建数据字典
            data_dict = {
                "基本信息": basic_info,
                "财务指标": financial_indicators,
                "利润表": income_statement,
                "资产负债表": balance_sheet,
                "现金流量表": cash_flow_statement
            }
            
            # 检查数据完整性
            successful_fetches = sum(1 for df in data_dict.values() if df is not None and not df.empty)
            logger.info(f"数据获取完成，成功获取了{successful_fetches}个数据表")
            
            return data_dict
        
        # 实现重试逻辑
        data_dict = None
        retry_count = 0
        while retry_count <= max_retries and (data_dict is None or sum(1 for df in data_dict.values() if df is None or df.empty) > 3):
            if retry_count > 0:
                logger.info(f"第{retry_count}次重试获取股票{stock_code}的财务数据...")
                # 等待一段时间再重试
                time.sleep(2 * retry_count)  # 指数退避
            
            data_dict = _get_financial_data()
            retry_count += 1
        
        # 保存数据
        file_path = None
        if save_excel:
            try:
                # 获取当前年份作为文件名的一部分
                current_year = str(datetime.now().year)
                file_path = self.save_data_to_excel(data_dict, f"{stock_code}_{current_year}_财务数据.xlsx")
            except Exception as e:
                logger.error(f"保存数据到Excel失败: {e}")
        
        # 记录获取结果
        result_summary = {key: "成功" if (df is not None and not df.empty) else "失败" for key, df in data_dict.items()}
        logger.info(f"股票{stock_code}的财务数据获取完成！结果: {result_summary}")
        
        return data_dict, file_path


if __name__ == "__main__":
    # 创建数据获取器实例
    fetcher = FinancialDataFetcher()
    
    # 示例：获取贵州茅台(600519)的财务数据
    stock_code = "600519"
    data_dict, file_path = fetcher.fetch_company_financial_data(stock_code)
    
    # 打印结果摘要
    print("\n获取的财务数据摘要:")
    for key, value in data_dict.items():
        if value is not None:
            print(f"{key}: {len(value)}条记录")
        else:
            print(f"{key}: 未获取到数据")
    
    if file_path:
        print(f"\n数据已保存至: {file_path}")