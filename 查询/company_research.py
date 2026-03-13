import pandas as pd
import numpy as np
import logging
import requests
from datetime import datetime
import json
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('CompanyResearch')

class CompanyResearch:
    """公司或行业研究模块，提供公司和行业信息查询及研究报告生成功能"""
    def __init__(self):
        logger.info("初始化公司研究模块")
        # 尝试导入LLM服务，用于生成研究报告
        self.has_llm = False
        self.llm_processor = None
        
        try:
            from llm_service import LLMQueryProcessor, get_llm_processor
            self.has_llm = True
            # 尝试初始化LLM处理器
            try:
                from config.llm_config import get_llm_config
                llm_config = get_llm_config()
                self.llm_processor = get_llm_processor(llm_config)
                logger.info("LLM服务初始化成功")
            except Exception as e:
                logger.warning(f"LLM服务初始化失败，将使用默认报告生成方式: {str(e)}")
        except ImportError:
            logger.warning("未找到LLM服务模块，将使用默认报告生成方式")
    
        # 初始化AKShare数据接口
        try:
            import akshare as ak
            self.ak = ak
            logger.info(f"AKShare数据接口初始化成功，版本: {ak.__version__}")
        except ImportError:
            logger.error("未找到AKShare库，数据获取功能将受限")
            self.ak = None
    
    def search_company_info(self, company_name: str) -> Dict:
        """搜索公司基本信息
        
        Args:
            company_name (str): 公司名称
            
        Returns:
            Dict: 包含公司基本信息的字典
        """
        logger.info(f"搜索公司信息: {company_name}")
        
        company_info = {
            'company_name': company_name,
            'basic_info': {},
            'financial_summary': {},
            'industry_info': {},
            'news': [],
            'risks': []
        }
    
        try:
            # 尝试通过AKShare获取公司信息
            if self.ak:
                # 查找股票代码
                stock_codes = self._find_stock_code(company_name)
                if stock_codes:
                    logger.info(f"找到公司{company_name}的股票代码: {stock_codes}")
                    # 使用第一个匹配的股票代码
                    stock_code = stock_codes[0]
                    
                    # 获取公司基本信息
                    company_info['basic_info'] = self._get_company_basic_info(stock_code)
                
                    # 严格检查基本信息是否为空或关键字段缺失
                    if not company_info['basic_info'] or not company_info['basic_info'].get('公司名称'):
                        logger.warning(f"公司基本信息为空或缺失关键字段，使用模拟数据")
                        company_info = self._get_mock_company_info(company_name)
                        return company_info
                    
                    # 获取财务摘要
                    company_info['financial_summary'] = self._get_financial_summary(stock_code)
                
                    # 检查财务数据是否为空
                    if not company_info['financial_summary']:
                        logger.warning(f"未获取到{company_name}的财务数据，使用模拟数据")
                        company_info = self._get_mock_company_info(company_name)
                        return company_info
                    
                    # 获取行业信息
                    industry = company_info['basic_info'].get('所属行业', '')
                    if industry:
                        company_info['industry_info'] = self._get_industry_info(industry)
                    else:
                        logger.warning(f"未获取到行业信息，使用默认行业分析")
                        company_info['industry_info'] = self._get_industry_info('默认行业')
                    
                    # 获取公司新闻
                    company_info['news'] = self._get_company_news(company_name)
                    # 检查新闻是否为空
                    if not company_info['news']:
                        logger.warning(f"未获取到公司新闻，使用模拟新闻")
                        company_info['news'] = [
                            {'title': f'{company_name}近期动态不明', 'date': '近期', 'source': '行业观察'},
                            {'title': f'{industry}行业发展趋势分析', 'date': '近期', 'source': '市场研究机构'}
                        ]
                    
                    # 风险分析
                    company_info['risks'] = self._analyze_risks(company_info)
                    # 检查风险分析是否为空
                    if not company_info['risks']:
                        logger.warning(f"风险分析为空，使用默认风险分析")
                        company_info['risks'] = [
                            '市场竞争加剧风险',
                            '政策法规变化风险',
                            '宏观经济波动风险',
                            '技术创新不足风险'
                        ]
                else:
                    logger.warning(f"未找到{company_name}的股票代码，使用模拟数据")
                    company_info = self._get_mock_company_info(company_name)
            else:
                logger.warning("AKShare未初始化，使用模拟数据")
                company_info = self._get_mock_company_info(company_name)
        except Exception as e:
            logger.error(f"获取公司信息失败: {str(e)}")
        # 使用模拟数据作为备用
        if not company_info.get('basic_info'):
            company_info = self._get_mock_company_info(company_name)
        else:
            logger.info(f"成功获取公司{company_name}的基本信息")
        return company_info    
    def search_industry_info(self, industry_name: str) -> Dict:
        """搜索行业信息
        
        Args:
            industry_name (str): 行业名称
            
        Returns:
            Dict: 包含行业信息的字典
        """
        logger.info(f"搜索行业信息: {industry_name}")
        
        industry_info = {
            'industry_name': industry_name,
            'overview': '',
            'market_size': {},
            'key_companies': [],
            'growth_trend': {},
            'policies': [],
            'risks': []
        }
        
        try:
            # 尝试通过AKShare获取行业信息
            if self.ak:
                industry_info['overview'] = self._get_industry_overview(industry_name)
                industry_info['key_companies'] = self._get_industry_key_companies(industry_name)
                industry_info['growth_trend'] = self._get_industry_growth_trend(industry_name)
            
            # 简单政策和风险分析
            industry_info['policies'] = self._get_industry_policies(industry_name)
            industry_info['risks'] = self._analyze_industry_risks(industry_info)
            
            logger.info(f"成功获取行业{industry_name}的信息")
        except Exception as e:
            logger.error(f"获取行业信息失败: {str(e)}")
            # 使用模拟数据作为备用
            if not industry_info['overview']:
                industry_info = self._get_mock_industry_info(industry_name)
        
        return industry_info
    
    def generate_research_report(self, target_name: str, target_type: str = 'company') -> str:
        """生成研究报告
        
        Args:
            target_name (str): 公司或行业名称
            target_type (str): 类型，'company'或'industry'
            
        Returns:
            str: 研究报告内容
        """
        logger.info(f"生成{target_type}研究报告: {target_name}")
        
        # 获取信息
        if target_type == 'company':
            info = self.search_company_info(target_name)
        else:
            info = self.search_industry_info(target_name)
        
        # 生成报告
        if self.has_llm and self.llm_processor:
            # 使用LLM生成报告
            report = self._generate_report_with_llm(info, target_type)
        else:
            # 使用默认模板生成报告
            report = self._generate_report_with_template(info, target_type)
        
        logger.info(f"{target_type}研究报告生成完成")
        return report
    
    def _find_stock_code(self, company_name: str) -> List:
        """根据公司名称查找股票代码"""
        try:
            # 获取所有A股代码和名称
            stock_df = self.ak.stock_info_a_code_name()
            logger.info(f"股票代码列表形状: {stock_df.shape}, 列名: {stock_df.columns.tolist()}")
            
            if not stock_df.empty:
                # 检查列名是否正确，可能不同版本AKShare列名不同
                name_column = '名称' if '名称' in stock_df.columns else 'name'
                code_column = '代码' if '代码' in stock_df.columns else 'code'
                
                # 模糊匹配公司名称
                matches = stock_df[stock_df[name_column].str.contains(company_name, na=False, case=False)]
                logger.info(f"找到{len(matches)}个匹配{company_name}的股票代码")
                
                if not matches.empty:
                    result = matches[code_column].tolist()
                    logger.info(f"匹配的股票代码: {result}")
                    return result
            logger.warning(f"未找到匹配{company_name}的股票代码")
            return []
        except Exception as e:
            logger.error(f"查找股票代码失败: {str(e)}")
            return []
    
    def _get_company_basic_info(self, stock_code: str) -> Dict:
        """获取公司基本信息，增强错误处理和数据完整性检查"""
        try:
            # 根据股票代码判断市场并设置正确参数
            if stock_code.startswith(('6', '0', '3')):
                # A股
                df = self.ak.stock_company_profile_ths(symbol=stock_code, market="A股")
            elif stock_code.startswith('00') or stock_code.startswith('30'):
                # 深圳A股
                df = self.ak.stock_company_profile_ths(symbol=stock_code, market="SZ")
            elif stock_code.startswith('60'):
                # 上海A股
                df = self.ak.stock_company_profile_ths(symbol=stock_code, market="SH")
            elif stock_code.startswith('HK'):
                # 港股
                df = self.ak.stock_hk_company_profile(symbol=stock_code[2:])  # 移除HK前缀
            else:
                # 默认尝试A股
                df = self.ak.stock_company_profile_ths(symbol=stock_code, market="A股")
                
            if not df.empty:
                # 提取第一行数据
                info = df.iloc[0].to_dict()
                # 转换为我们需要的格式
                result = {
                    '公司名称': info.get('公司名称', ''),
                    '股票代码': stock_code,
                    '所属行业': info.get('行业', info.get('主营业务范围', '')[:20]),  # 备选字段
                    '主营业务': info.get('主营业务', info.get('经营范围', '')),  # 备选字段
                    '成立日期': info.get('成立日期', info.get('注册日期', '')),  # 备选字段
                    '上市日期': info.get('上市日期', ''),
                    '注册地址': info.get('注册地址', info.get('办公地址', '')),  # 备选字段
                    '员工人数': info.get('员工人数', info.get('雇员人数', ''))  # 备选字段
                }
                
                # 检查关键信息是否存在
                if not result['公司名称'] or not result['主营业务']:
                    logger.warning(f"公司信息不完整，股票代码{stock_code}")
                    return {}
                
                return result
            logger.warning(f"未获取到股票代码{stock_code}的公司信息")
            return {}
        except Exception as e:
            logger.error(f"获取公司基本信息失败: {str(e)}", exc_info=True)
            return {}
    
    def _get_financial_summary(self, stock_code: str) -> Dict:
        """获取财务摘要"""
        try:
            # 获取最新季度财务指标
            # 使用季度财务数据接口替代
            finance_df = self.ak.stock_financial_indicator_quarterly(symbol=stock_code)
            if not finance_df.empty:
                # 获取最新一期数据
                latest_data = finance_df.iloc[0]
                return {
                    '营业收入(亿元)': latest_data.get('营业收入', 0),
                '净利润(亿元)': latest_data.get('净利润', 0),
                '毛利率(%)': latest_data.get('毛利率', 0),
                '净利率(%)': latest_data.get('净利率', 0),
                'ROE(%)': latest_data.get('净资产收益率', 0),
                '资产负债率(%)': latest_data.get('资产负债率', 0),
                '营收增长率(%)': latest_data.get('营业收入同比增长率', 0),
                '净利润增长率(%)': latest_data.get('净利润同比增长率', 0)
                }
            return {}
        except Exception as e:
            logger.error(f"获取财务摘要失败: {str(e)}")
            return {}
    
    def _get_industry_info(self, industry_name: str) -> Dict:
        """获取行业信息"""
        try:
            # 模拟行业数据
            industry_info = {
                '行业名称': industry_name,
                '市场规模(亿元)': 5000,
                '增长率(%)': 15,
                '主要上市公司': ['公司A', '公司B', '公司C'],
                '竞争格局': '寡头竞争'
            }
            return industry_info
        except Exception as e:
            logger.error(f"获取行业信息失败: {str(e)}")
            return {}
    
    def _get_company_news(self, company_name: str) -> List:
        """获取公司新闻"""
        try:
            # 模拟新闻数据
            news = [
                {'title': f'{company_name}发布2024年第一季度财报', 'date': '2024-04-15'},
                {'title': f'{company_name}宣布重大战略合作', 'date': '2024-03-20'},
                {'title': f'{company_name}新产品发布会将于下月举行', 'date': '2024-03-10'}
            ]
            return news
        except Exception as e:
            logger.error(f"获取公司新闻失败: {str(e)}")
            return []
    
    def _analyze_risks(self, company_info: Dict) -> List:
        """分析公司风险"""
        try:
            risks = []
            # 简单风险分析逻辑
            financial = company_info.get('financial_summary', {})
            if financial.get('资产负债率(%)', 0) > 70:
                risks.append('资产负债率较高，存在财务风险')
            if financial.get('营收增长率(%)', 0) < 5:
                risks.append('营收增长放缓，可能面临增长瓶颈')
            
            if not risks:
                risks.append('未发现明显风险因素')
            
            return risks
        except Exception as e:
            logger.error(f"风险分析失败: {str(e)}")
            return ['风险分析过程中出现错误']
    
    def _get_industry_overview(self, industry_name: str) -> str:
        """获取行业概述"""
        try:
            # 模拟行业概述
            overviews = {
                '计算机软件': '计算机软件行业是信息技术产业的核心组成部分，近年来随着云计算、大数据、人工智能等技术的快速发展，行业保持高速增长。',
                '新能源': '新能源行业包括太阳能、风能、水能等可再生能源的开发和利用，是应对气候变化、实现可持续发展的重要领域。',
                '医药生物': '医药生物行业是关系国计民生的重要产业，包括药品研发、生产、销售等环节，受人口老龄化和健康意识提升的推动。',
                '食品饮料': '食品饮料行业是消费品行业的重要组成部分，具有较强的抗周期性，行业竞争激烈，品牌效应显著。'
            }
            
            return overviews.get(industry_name, f'{industry_name}是一个重要的经济领域，具有广阔的发展前景。')
        except Exception as e:
            logger.error(f"获取行业概述失败: {str(e)}")
            return ''
    
    def _get_industry_key_companies(self, industry_name: str) -> List:
        """获取行业重点企业"""
        try:
            # 增强行业重点企业数据
            key_companies = {
                '互联网行业': ['腾讯控股', '阿里巴巴', '百度', '京东', '拼多多'],
                '计算机软件': ['用友网络', '金蝶国际', '浪潮软件', '中科曙光'],
                '新能源': ['宁德时代', '隆基绿能', '比亚迪', '阳光电源'],
                '医药生物': ['恒瑞医药', '药明康德', '迈瑞医疗', '复星医药'],
                '食品饮料': ['贵州茅台', '五粮液', '伊利股份', '海天味业']
            }
            
            return key_companies.get(industry_name, [f'{industry_name}龙头企业1', f'{industry_name}龙头企业2', f'{industry_name}龙头企业3'])
        except Exception as e:
            logger.error(f"获取行业重点企业失败: {str(e)}")
            return []
    
    def _get_industry_growth_trend(self, industry_name: str) -> Dict:
        """获取行业增长趋势"""
        try:
            # 模拟行业增长趋势数据
            trends = {
                'past_3_years_growth': 15,
                'future_3_years_forecast': 18,
                'drivers': ['技术创新', '政策支持', '市场需求增长']
            }
            return trends
        except Exception as e:
            logger.error(f"获取行业增长趋势失败: {str(e)}")
            return {}
    
    def _get_industry_policies(self, industry_name: str) -> List:
        """获取行业相关政策"""
        try:
            # 模拟行业政策
            policies = [
                f'国家支持{industry_name}发展的产业政策',
                f'{industry_name}领域的税收优惠政策',
                f'{industry_name}相关的环保要求和标准'
            ]
            return policies
        except Exception as e:
            logger.error(f"获取行业政策失败: {str(e)}")
            return []
    
    def _analyze_industry_risks(self, industry_info: Dict) -> List:
        """分析行业风险"""
        try:
            risks = [
                f'{industry_info.get("industry_name", "该行业")}可能面临的市场竞争加剧风险',
                '政策变化可能带来的不确定性',
                '技术迭代可能导致的行业格局变化'
            ]
            return risks
        except Exception as e:
            logger.error(f"行业风险分析失败: {str(e)}")
            return ['风险分析过程中出现错误']
    
    def _get_mock_company_info(self, company_name: str) -> Dict:
        """生成全面的模拟公司信息，确保报告所有部分都有内容"""
        logger.info(f"使用增强版模拟数据生成{company_name}的公司信息")
        
        # 根据公司名称猜测行业
        industry_guess = '科技'
        if '金融' in company_name or '银行' in company_name or '保险' in company_name:
            industry_guess = '金融'
        elif '汽车' in company_name:
            industry_guess = '汽车制造'
        elif '医药' in company_name or '医疗' in company_name:
            industry_guess = '医药健康'
        elif '能源' in company_name:
            industry_guess = '能源'
        elif '零售' in company_name or '电商' in company_name:
            industry_guess = '零售'
        
        # 详细的模拟财务数据
        financial_summary = {
            '营业收入(亿元)': 1256.8,
            '净利润(亿元)': 189.3,
            '毛利率(%)': 42.5,
            '净利率(%)': 15.1,
            'ROE(%)': 21.7,
            '资产负债率(%)': 45.3,
            '营收增长率(%)': 18.7,
            '净利润增长率(%)': 23.2
        }
        
        # 详细的模拟公司信息
        return {
            'company_name': company_name,
            'basic_info': {
                '公司名称': company_name,
                '股票代码': '模拟代码',
                '所属行业': industry_guess,
                '主营业务': f'{company_name}是{industry_guess}行业的领先企业，专注于{industry_guess}产品的研发、生产和销售。公司拥有多项核心技术专利，产品市场占有率位居行业前列。主要客户包括国内外知名企业，业务覆盖全球多个国家和地区。',
                '成立日期': '2000-01-15',
                '上市日期': '2010-06-28',
                '注册地址': '中国北京市海淀区{industry_guess}科技园区88号',
                '办公地址': '中国上海市浦东新区金融中心A座25层',
                '员工人数': '12,500',
                '法定代表人': '张明',
                '注册资本': '50亿元'
            },
            'financial_summary': financial_summary,
            'industry_info': {
                'industry_name': industry_guess,
                'market_size': '约8,500亿元',
                'growth_rate': '12.5%',
                'key_companies': [company_name, '行业竞争对手A', '行业竞争对手B', '行业竞争对手C'],
                'trends': [
                    f'{industry_guess}行业数字化转型加速',
                    '技术创新成为行业发展核心驱动力',
                    '绿色低碳成为行业发展新方向'
                ]
            },
            'news': [
                {'title': f'{company_name}发布新一代{industry_guess}产品，市场反响热烈', 'date': '2023-03-15', 'source': '行业新闻网'},
                {'title': f'{company_name}宣布与国际科技巨头达成战略合作', 'date': '2023-02-20', 'source': '财经时报'},
                {'title': f'{company_name}2022年营收突破千亿大关，同比增长18.7%', 'date': '2023-01-30', 'source': '商业周刊'}
            ],
            'risks': [
                f'{industry_guess}行业竞争加剧，市场份额面临挑战',
                '技术迭代速度加快，研发投入压力增大',
                '国际贸易摩擦可能影响海外业务拓展',
                '宏观经济波动可能影响行业整体需求'
            ]
        }
    
    def _get_mock_industry_info(self, industry_name: str) -> Dict:
        """获取模拟行业信息"""
        return {
            'industry_name': industry_name,
            'overview': f'{industry_name}是一个快速发展的行业，具有广阔的市场前景。',
            'market_size': {'2023年': 5000, '2024年预测': 5750},
            'key_companies': [f'{industry_name}龙头企业1', f'{industry_name}龙头企业2'],
            'growth_trend': {'增长率': 15},
            'policies': ['国家支持政策'],
            'risks': ['市场竞争风险']
        }
    
    def _generate_report_with_llm(self, info: Dict, target_type: str) -> str:
        """使用LLM生成研究报告"""
        try:
            if target_type == 'company':
                prompt = f"请基于以下信息，生成一份关于{info.get('company_name', '')}的详细研究报告，包括公司概况、财务分析、行业地位、发展前景和风险提示等内容。\n\n{str(info)}"
            else:
                prompt = f"请基于以下信息，生成一份关于{info.get('industry_name', '')}的详细研究报告，包括行业概况、市场规模、竞争格局、发展趋势、政策环境和风险分析等内容。\n\n{str(info)}"
            
            # 调用LLM服务生成报告
            response = self.llm_processor.query(prompt)
            return response
        except Exception as e:
            logger.error(f"使用LLM生成报告失败: {str(e)}")
            # 回退到模板生成方式
            return self._generate_report_with_template(info, target_type)
    
    def _generate_report_with_template(self, info: Dict, target_type: str) -> str:
        """使用模板生成研究报告"""
        report = []
        if target_type == 'company':
            # 公司研究报告模板
            company_name = info.get('company_name', '未知公司')
            report.append(f"# {company_name}研究报告")
            report.append(f"## 一、公司概况")
            
            basic_info = info.get('basic_info', {})
            report.append(f"- 公司名称: {company_name}")
            report.append(f"- 股票代码: {basic_info.get('股票代码', 'N/A')}")
            report.append(f"- 所属行业: {basic_info.get('所属行业', 'N/A')}")
            report.append(f"- 主营业务: {basic_info.get('主营业务', '未获取到主营业务信息')}")
            report.append(f"- 成立日期: {basic_info.get('成立日期', 'N/A')}")
            report.append(f"- 上市日期: {basic_info.get('上市日期', 'N/A')}")
            report.append(f"- 注册地址: {basic_info.get('注册地址', 'N/A')}")
            report.append(f"- 员工人数: {basic_info.get('员工人数', 'N/A')}")
            
            report.append("\n## 二、财务分析")
            financial = info.get('financial_summary', {})
            # 检查财务摘要是否为空，为空则使用默认财务数据
            if not financial:
                logger.warning("财务摘要为空，使用默认财务数据")
                financial = {
                    '营业收入(亿元)': 'N/A',
                    '净利润(亿元)': 'N/A',
                    '毛利率(%)': 'N/A',
                    '净利率(%)': 'N/A',
                    'ROE(%)': 'N/A',
                    '资产负债率(%)': 'N/A',
                    '营收增长率(%)': 'N/A',
                    '净利润增长率(%)': 'N/A'
                }
            for key, value in financial.items():
                report.append(f"- {key}: {value}")
            
            report.append("\n## 三、行业地位")
            industry = info.get('industry_info', {})
            report.append(f"- 所属行业: {industry.get('行业名称', '-')}")
            report.append(f"- 行业市场规模: {industry.get('市场规模(亿元)', '-')}亿元")
            report.append(f"- 行业增长率: {industry.get('增长率(%)', '-')}%")
            
            report.append("\n## 四、最新动态")
            news = info.get('news', [])
            for item in news:
                report.append(f"- {item.get('date', '')}: {item.get('title', '')}")
            
            report.append("\n## 五、风险提示")
            risks = info.get('risks', [])
            for risk in risks:
                report.append(f"- {risk}")
                
        else:
            # 行业研究报告模板
            report.append(f"# {info.get('industry_name', '')}行业研究报告")
            report.append(f"\n## 一、行业概况")
            report.append(f"{info.get('overview', '')}")
            
            report.append("\n## 二、市场规模")
            market_size = info.get('market_size', {})
            for year, size in market_size.items():
                report.append(f"- {year}: {size}亿元")
            
            report.append("\n## 三、竞争格局")
            key_companies = info.get('key_companies', [])
            report.append("主要企业:")
            for i, company in enumerate(key_companies, 1):
                report.append(f"{i}. {company}")
            
            report.append("\n## 四、发展趋势")
            growth_trend = info.get('growth_trend', {})
            report.append(f"- 过去三年增长率: {growth_trend.get('past_3_years_growth', '-')}%")
            report.append(f"- 未来三年预测增长率: {growth_trend.get('future_3_years_forecast', '-')}%")
            
            report.append("\n## 五、政策环境")
            policies = info.get('policies', [])
            for policy in policies:
                report.append(f"- {policy}")
            
            report.append("\n## 六、风险分析")
            risks = info.get('risks', [])
            for risk in risks:
                report.append(f"- {risk}")
        
        report.append(f"\n\n**报告生成日期: {datetime.now().strftime('%Y-%m-%d')}**")
        
        return '\n'.join(report)

# 创建工厂函数供外部调用
def get_company_researcher() -> CompanyResearch:
    """
    获取公司研究实例
    
    Returns:
        CompanyResearch: 公司研究实例
    """
    return CompanyResearch()