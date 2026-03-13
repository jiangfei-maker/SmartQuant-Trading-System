import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import os
from logging.handlers import RotatingFileHandler

# 配置日志
logger = logging.getLogger('FinancialModeling')

class FinancialModeler:
    """财务建模模块，提供财务比率计算、预测和敏感性分析功能"""
    def __init__(self, company_code=None):
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建文件日志处理器
        log_file = os.path.join(log_dir, 'financial_modeling.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024*1024*5,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 添加处理器
        if not logger.handlers:
            logger.addHandler(file_handler)
            # 保留控制台输出
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
        logger.info("初始化财务建模模块")
        self.company_code = company_code
        # 加载历史财务数据
        self.historical_data = self._load_historical_data()
        self.financial_statements = self._generate_financial_statements()

    def _load_historical_data(self):
        """根据公司代码加载历史财务数据
        
        从数据文件中加载指定公司的历史财务数据，若未提供公司代码或数据不存在，
        则返回默认的模拟数据
        """
        if self.company_code:
            try:
                # 尝试从数据文件加载真实公司数据
                data_path = os.path.join('data', f'{self.company_code}_2020_2024.parquet')
                if os.path.exists(data_path):
                    logger.info(f"加载公司 {self.company_code} 的历史财务数据")
                    historical_data = pd.read_parquet(data_path)
                    # 确保数据按年份排序
                    historical_data = historical_data.sort_index()
                    return historical_data
                else:
                    logger.warning(f"公司 {self.company_code} 的数据文件不存在，使用模拟数据")
            except Exception as e:
                logger.error(f"加载公司 {self.company_code} 数据失败: {str(e)}")
        
        # 生成模拟数据作为备选
        logger.info("使用模拟财务数据")
        years = [2020, 2021, 2022, 2023, 2024]
        historical_data = {
            '总营收': [1000000, 1200000, 1440000, 1728000, 2073600],
            '营业成本': [600000, 720000, 864000, 1036800, 1244160],
            '销售费用': [80000, 96000, 115200, 138240, 165888],
            '管理费用': [120000, 144000, 172800, 207360, 248832],
            '财务费用': [50000, 55000, 60000, 65000, 70000],
            '税率': [0.25, 0.25, 0.25, 0.25, 0.25],
            '总资产': [1500000, 1800000, 2160000, 2592000, 3110400],
            '总负债': [500000, 600000, 720000, 864000, 1036800],
            '总股本': [10000000, 10000000, 10000000, 10000000, 10000000],
            '经营活动现金流': [250000, 300000, 360000, 432000, 518400],
            '投资活动现金流': [-100000, -120000, -144000, -172800, -207360],
            '筹资活动现金流': [-50000, -60000, -72000, -86400, -103680]
        }
        df = pd.DataFrame(historical_data, index=years)
        # 添加'年份'列以便直接访问
        df['年份'] = years
        return df

    def _load_historical_data(self):
        """从AKshare获取真实财务数据，若失败则使用模拟数据"""
        import akshare as ak
        import os
        
        if self.company_code:
            try:
                logger.info(f"通过AKshare获取{self.company_code}的真实财务数据")
                
                # 添加市场标识前缀
                def add_market_prefix(stock_code):
                    if stock_code.startswith(('000', '002', '300')):
                        return f"sz{stock_code}"
                    elif stock_code.startswith(('600', '601', '603')):
                        return f"sh{stock_code}"
                    return stock_code
                
                stock_code_with_market = add_market_prefix(self.company_code)
                
                # 获取利润表
                income_df = ak.stock_profit_sheet_by_report_em(symbol=stock_code_with_market)
                
                # 获取资产负债表
                balance_df = ak.stock_balance_sheet_by_report_em(symbol=stock_code_with_market)
                
                # 获取现金流量表
                cashflow_df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code_with_market)
                
                # 提取最近5年数据并转换格式
                years = sorted([int(y) for y in income_df.columns if y.isdigit()][-5:])
                historical_data = {
                    'revenue': [income_df.loc['营业收入', str(y)] for y in years],
                    'cost_of_goods_sold': [income_df.loc['营业成本', str(y)] for y in years],
                    'operating_expenses': [income_df.loc['销售费用', str(y)] + income_df.loc['管理费用', str(y)] for y in years],
                    'interest_expense': [income_df.loc['财务费用', str(y)] for y in years],
                    'tax_rate': [income_df.loc['所得税费用', str(y)] / income_df.loc['利润总额', str(y)] if income_df.loc['利润总额', str(y)] != 0 else 0.25 for y in years],
                    'total_assets': [balance_df.loc['资产总计', str(y)] for y in years],
                    'total_liabilities': [balance_df.loc['负债总计', str(y)] for y in years],
                    'total_equity': [balance_df.loc['所有者权益合计', str(y)] for y in years],
                    'cash_flow_operations': [cashflow_df.loc['经营活动产生的现金流量净额', str(y)] for y in years],
                    'cash_flow_investing': [cashflow_df.loc['投资活动产生的现金流量净额', str(y)] for y in years],
                    'cash_flow_financing': [cashflow_df.loc['筹资活动产生的现金流量净额', str(y)] for y in years],
                    'depreciation': [cashflow_df.loc['固定资产折旧、油气资产折耗、生产性生物资产折旧', str(y)] for y in years],
                    'capital_expenditure': [cashflow_df.loc['购建固定资产、无形资产和其他长期资产支付的现金', str(y)] for y in years],
                    'working_capital': [balance_df.loc['流动资产合计', str(y)] - balance_df.loc['流动负债合计', str(y)] for y in years]
                }
                
                # 转换为数值类型
                for key in historical_data:
                    historical_data[key] = [float(str(v).replace(',', '')) for v in historical_data[key]]
                
                logger.info(f"成功获取{self.company_code}的{len(years)}年财务数据")
                return pd.DataFrame(historical_data, index=years)
                
            except Exception as e:
                logger.error(f"AKshare数据获取失败: {str(e)}")
        
        # 生成模拟数据作为备选
        logger.info("使用模拟财务数据")
        years = [2020, 2021, 2022, 2023, 2024]
        historical_data = {
                'revenue': [1000000, 1200000, 1440000, 1728000, 2073600],
                'cost_of_goods_sold': [600000, 720000, 864000, 1036800, 1244160],
                'operating_expenses': [200000, 240000, 288000, 345600, 414720],
                'interest_expense': [50000, 55000, 60000, 65000, 70000],
                'tax_rate': [0.25, 0.25, 0.25, 0.25, 0.25],
                'total_assets': [1500000, 1800000, 2160000, 2592000, 3110400],
                'total_liabilities': [500000, 600000, 720000, 864000, 1036800],
                'total_equity': [1000000, 1200000, 1440000, 1728000, 2073600],
                'cash_flow_operations': [250000, 300000, 360000, 432000, 518400],
                'cash_flow_investing': [-100000, -120000, -144000, -172800, -207360],
                'cash_flow_financing': [-50000, -60000, -72000, -86400, -103680],
                'depreciation': [50000, 60000, 72000, 86400, 103680],
                'capital_expenditure': [120000, 144000, 172800, 207360, 248832],
                'working_capital': [300000, 360000, 432000, 518400, 622080]
            }
        return pd.DataFrame(historical_data, index=years)
        
    def _generate_financial_statements(self):
        """生成多年度财务报表"""
        if not hasattr(self, 'historical_data') or self.historical_data.empty:
            self.historical_data = self._load_historical_data()

        # 生成利润表
        income_statements = {}
        for year in self.historical_data.index:
            revenue = self.historical_data.loc[year, 'revenue']
            cogs = self.historical_data.loc[year, 'cost_of_goods_sold']
            operating_expenses = self.historical_data.loc[year, 'operating_expenses']
            interest = self.historical_data.loc[year, 'interest_expense']
            tax_rate = self.historical_data.loc[year, 'tax_rate']

            gross_profit = revenue - cogs
            operating_income = gross_profit - operating_expenses
            ebit = operating_income
            pretax_income = ebit - interest
            taxes = pretax_income * tax_rate
            net_income = pretax_income - taxes

            income_statements[year] = {
                'Revenue': revenue,
                'Cost of Goods Sold': cogs,
                'Gross Profit': gross_profit,
                'Operating Expenses': operating_expenses,
                'Operating Income': operating_income,
                'EBIT': ebit,
                'Interest Expense': interest,
                'Pretax Income': pretax_income,
                'Taxes': taxes,
                'Net Income': net_income
            }

        # 生成资产负债表
        balance_sheets = {}
        for year in self.historical_data.index:
            total_assets = self.historical_data.loc[year, 'total_assets']
            total_liabilities = self.historical_data.loc[year, 'total_liabilities']
            total_equity = self.historical_data.loc[year, 'total_equity']

            balance_sheets[year] = {
                'Total Assets': total_assets,
                'Total Liabilities': total_liabilities,
                'Total Equity': total_equity
            }

        # 生成现金流量表
        cash_flows = {}
        for year in self.historical_data.index:
            cash_flow_operations = self.historical_data.loc[year, 'cash_flow_operations']
            cash_flow_investing = self.historical_data.loc[year, 'cash_flow_investing']
            cash_flow_financing = self.historical_data.loc[year, 'cash_flow_financing']
            net_cash_flow = cash_flow_operations + cash_flow_investing + cash_flow_financing

            cash_flows[year] = {
                'Operating Cash Flow': cash_flow_operations,
                'Investing Cash Flow': cash_flow_investing,
                'Financing Cash Flow': cash_flow_financing,
                'Net Cash Flow': net_cash_flow
            }

        return {
            'income_statements': income_statements,
            'balance_sheets': balance_sheets,
            'cash_flows': cash_flows
        }

    def calculate_financial_ratios(self):
        """计算关键财务比率
        
        Returns:
            dict: 计算后的最新年度财务比率
        """
        # 获取最新一年的财务数据
        latest_year = self.historical_data.index[-1]
        data = self.historical_data.loc[latest_year]
        income_stmt = self.financial_statements['income_statements'][latest_year]

        revenue = data['revenue']
        cogs = data['cost_of_goods_sold']
        operating_expenses = data['operating_expenses']
        interest_expense = data['interest_expense']
        tax_rate = data['tax_rate']
        total_assets = data['total_assets']
        total_liabilities = data['total_liabilities']
        total_equity = data['total_equity']

        # 计算基本财务指标
        gross_profit = revenue - cogs
        ebit = gross_profit - operating_expenses
        net_income = income_stmt['Net Income']

        # 前一年数据用于计算增长率
        if len(self.historical_data) > 1:
            prev_year = self.historical_data.index[-2]
            prev_revenue = self.historical_data.loc[prev_year, 'revenue']
            revenue_growth = ((revenue - prev_revenue) / prev_revenue) * 100
        else:
            revenue_growth = 0

        ratios = {}

        # 盈利能力比率
        ratios['毛利率'] = (gross_profit / revenue) * 100 if revenue > 0 else 0
        ratios['净利率'] = (net_income / revenue) * 100 if revenue > 0 else 0
        ratios['EBIT利润率'] = (ebit / revenue) * 100 if revenue > 0 else 0
        ratios['营收增长率'] = revenue_growth

        # 偿债能力比率
        ratios['资产负债率'] = (total_liabilities / total_assets) * 100 if total_assets > 0 else 0
        # 简化计算，假设流动资产占总资产的50%，流动负债占总负债的50%
        ratios['流动比率'] = (total_assets * 0.5 / (total_liabilities * 0.5)) if total_liabilities > 0 else 0
        # 简化计算，假设速动资产占总资产的30%
        ratios['速动比率'] = (total_assets * 0.3 / (total_liabilities * 0.5)) if total_liabilities > 0 else 0
        ratios['利息保障倍数'] = ebit / interest_expense if interest_expense > 0 else 0

        # 运营能力比率 (简化计算)
        ratios['存货周转率'] = (cogs / (total_assets * 0.2)) if total_assets > 0 else 0
        ratios['应收账款周转率'] = (revenue / (total_assets * 0.3)) if total_assets > 0 else 0
        ratios['总资产周转率'] = (revenue / total_assets) if total_assets > 0 else 0

        # 投资回报比率
        ratios['ROE'] = (net_income / total_equity) * 100 if total_equity > 0 else 0
        ratios['ROA'] = (net_income / total_assets) * 100 if total_assets > 0 else 0
        ratios['ROIC'] = (ebit * (1 - tax_rate) / total_assets) * 100 if total_assets > 0 else 0

        # 保留两位小数
        for key, value in ratios.items():
            ratios[key] = round(value, 2)

        return ratios
    
    def _calculate_equity_cost(self):
        # 使用CAPM模型计算权益成本
        risk_free_rate = 0.03  # 无风险利率(3%)
        market_risk_premium = 0.08  # 市场风险溢价(8%)
        # 假设贝塔系数使用行业平均1.2
        beta = 1.2
        return risk_free_rate + beta * market_risk_premium

    def _calculate_debt_cost(self):
        # 从公司债券收益率计算债务成本，若无则使用行业平均债务成本
        return 0.045  # 4.5%

    def calculate_wacc(self):
        """计算加权平均资本成本(WACC)"""
        # 从公司财务数据计算WACC
        # 假设存在计算权益成本和债务成本的辅助方法
        equity_cost = self._calculate_equity_cost()
        debt_cost = self._calculate_debt_cost()
        # 从历史数据获取最新税率
        tax_rate = self.historical_data['tax_rate'].iloc[-1]
        # 计算资产负债率(总负债/总资产)
        total_liabilities = self.historical_data['total_liabilities'].iloc[-1]
        total_assets = self.historical_data['total_assets'].iloc[-1]
        debt_ratio = total_liabilities / total_assets
        equity_ratio = 1 - debt_ratio
        wacc = (equity_cost * equity_ratio) + (debt_cost * debt_ratio * (1 - tax_rate))
        return wacc

    def calculate_terminal_value(self, final_cash_flow, wacc):
        """计算终值(永续增长法)"""
        # 使用历史增长率计算永续增长率
        revenues = self.historical_data['revenue']
        revenue_growth_rates = revenues.pct_change().dropna()
        mean_growth = revenue_growth_rates.tail(3).mean()  # 最近3年平均增长率
        terminal_growth = min(mean_growth, 0.03)  # 永续增长率不超过3%
        if wacc <= terminal_growth:
            raise ValueError("WACC必须大于永续增长率")
        return final_cash_flow * (1 + terminal_growth) / (wacc - terminal_growth)

    def generate_cash_flow_model(self, forecast_data, tax_rate):
        """生成自由现金流模型"""
        cash_flows = []
        for i in range(len(forecast_data['年份'])):
            revenue = forecast_data['revenue'][i]
            ebit = revenue * 0.2  # 简化EBIT计算
            tax = ebit * (tax_rate / 100)
            nopat = ebit - tax
            depreciation = forecast_data['depreciation'][i]
            capex = forecast_data['capital_expenditure'][i]
            working_capital = forecast_data['working_capital'][i]
            fcff = nopat + depreciation - capex - working_capital
            cash_flows.append(round(fcff, 2))
        return cash_flows

    def get_historical_financial_statements(self):
        """获取历史财务报表数据"""
        return self.financial_statements

    def get_historical_ratios(self):
        """计算并返回历史财务比率"""
        # 使用索引获取年份
        years = self.historical_data.index.tolist()
        revenue = self.historical_data['revenue'].tolist()
        cost = self.historical_data['cost_of_goods_sold']
        net_profit = self.historical_data.get('net_profit', revenue * 0.15)  # 使用15%净利率作为默认
        assets = self.historical_data['total_assets']
        liabilities = self.historical_data['total_liabilities']
        equity = self.historical_data.get('total_equity', assets - liabilities)

        # 计算实际财务比率而非使用随机数
        ratios = {
            '年份': years,
            '毛利率': [(rev - cst)/rev*100 for rev, cst in zip(revenue, cost)],
            '净利率': [np / rev * 100 for np, rev in zip(net_profit, revenue)],
            '资产负债率': [liab / ast * 100 for liab, ast in zip(liabilities, assets)],
            'ROE': [np / eq * 100 for np, eq in zip(net_profit, equity)],
            'ROA': [np / ast * 100 for np, ast in zip(net_profit, assets)],
            '营收增长率': [0] + [(revenue[i]/revenue[i-1]-1)*100 for i in range(1, len(revenue))]
        }
        return pd.DataFrame(ratios)
        cash_flows = []
        for i in range(len(forecast_data['年份'])):
            ebit = forecast_data['总营收'][i] * 0.2  # 简化EBIT计算
            tax = ebit * tax_rate
            nopat = ebit - tax
            ocf = nopat + depreciation[i] - capex[i] - working_capital[i]
            cash_flows.append(round(ocf, 2))
        return cash_flows

    def forecast_financials(self, forecast_years=5):
        """基于历史数据预测未来财务数据
        
        Args:
            forecast_years (int): 预测年数
            
        Returns:
            pd.DataFrame: 包含预测结果的DataFrame
        """
        # 使用内部历史数据计算增长率和利润率
        historical_data = self.historical_data
        if historical_data.empty:
            raise ValueError("没有可用的历史数据进行预测")
        
        # 计算历史营收增长率
        revenues = historical_data['revenue']
        revenue_growth_rates = revenues.pct_change().dropna()
        revenue_growth = revenue_growth_rates.tail(3).mean()  # 最近3年平均增长率
        
        # 计算历史净利率
        latest_year = historical_data.index[-1]
        net_income = self.financial_statements['income_statements'][latest_year]['Net Income']
        net_margin = net_income / revenues.iloc[-1]
        
        # 税率
        tax_rate = historical_data['tax_rate'].iloc[-1]

        # 计算关键比率（使用最近3年平均值）
        depreciation_rate = historical_data['depreciation'].tail(3).mean() / revenues.tail(3).mean() if len(revenues) >=3 else 0.05
        capex_rate = historical_data['capital_expenditure'].tail(3).mean() / revenues.tail(3).mean() if len(revenues) >=3 else 0.08
        wc_rate = historical_data['working_capital'].tail(3).mean() / revenues.tail(3).mean() if len(revenues) >=3 else 0.12

        # 基础年份数据
        base_year = historical_data.index[-1]
        base_revenue = revenues.iloc[-1]
        
        # 生成预测
        forecast = {
            '年份': [],
            '总营收': [],
            '净利润': [],
            '每股收益': [],
            '折旧与摊销': [],
            '资本支出': [],
            '营运资本增加': [],
            '自由现金流': []
        }
        
        # 利润表项目占比
        cost_ratio = 0.6  # 营业成本占营收比例
        sga_ratio = 0.15  # 销售管理费用占比
        interest_ratio = 0.02  # 财务费用占比
        
        for i in range(forecast_years):
            year = base_year + i + 1
            revenue = base_revenue * (1 + revenue_growth) ** (i + 1)
            cost = revenue * cost_ratio
            gross_profit = revenue - cost
            sga = revenue * sga_ratio
            interest = revenue * interest_ratio
            ebt = gross_profit - sga - interest
            tax = ebt * tax_rate
            net_profit = ebt - tax
            eps = net_profit / historical_data.get('总股本', 10000000)
            depreciation = revenue * depreciation_rate
            capex = revenue * capex_rate
            working_capital = revenue * wc_rate
            
            forecast['year'].append(year)
            forecast['revenue'].append(round(revenue, 2))
            forecast['cost_of_goods_sold'].append(round(cost, 2))
            forecast['gross_profit'].append(round(gross_profit, 2))
            forecast['selling_expenses'].append(round(sga * 0.6, 2))
            forecast['administrative_expenses'].append(round(sga * 0.4, 2))
            forecast['financial_expenses'].append(round(interest, 2))
            forecast['total_profit'].append(round(ebt, 2))
            forecast['income_tax'].append(round(tax, 2))
            forecast['net_profit'].append(round(net_profit, 2))
            forecast['eps'].append(round(eps, 4))
            forecast['depreciation'].append(round(depreciation, 2))
            forecast['capital_expenditure'].append(round(capex, 2))
            forecast['working_capital'].append(round(working_capital, 2))
        
        for i in range(forecast_years):
            year = base_year + i + 1
            revenue = base_revenue * (1 + revenue_growth) ** (i + 1)
            net_profit = revenue * net_margin
            eps = net_profit / historical_data.get('总股本', 10000000)
            depreciation = revenue * depreciation_rate
            capex = revenue * capex_rate
            working_capital = revenue * wc_rate
            
            forecast['年份'].append(year)
            forecast['总营收'].append(round(revenue, 2))
            forecast['净利润'].append(round(net_profit, 2))
            forecast['每股收益'].append(round(eps, 4))
            forecast['折旧'].append(round(depreciation, 2))
            forecast['资本支出'].append(round(capex, 2))
            forecast['营运资本'].append(round(working_capital, 2))
        
        return forecast
    
    def create_forecast_chart(self, forecast_data):
        import plotly.express as px
        fig = px.line(forecast_data, x='Year', y=['Revenue', 'Net Profit'], markers=True)
        fig.update_layout(title='Financial Forecast', xaxis_title='Year', yaxis_title='Amount (万元)')
        return fig

    def create_sensitivity_chart(self, sensitivity_results):
        """创建敏感性分析图表

        Args:
            sensitivity_results (dict): 敏感性分析结果

        Returns:
            plotly.graph_objects.Figure: 可视化图表
        """
        import plotly.express as px
        import pandas as pd
        import logging
        logger = logging.getLogger(__name__)

        logger.info("开始创建敏感性分析图表")
        try:
            if not sensitivity_results or not isinstance(sensitivity_results, dict):
                logger.error("无效的敏感性分析结果数据")
                fig = px.line(title='无数据可显示 - 敏感性分析结果为空')
                return fig

            data = []
            for scenario, yearly_data in sensitivity_results.items():
                if not isinstance(yearly_data, list):
                    logger.warning(f"情景'{scenario}'数据格式不正确，跳过")
                    continue

                for year_data in yearly_data:
                    if not isinstance(year_data, dict) or 'year' not in year_data or 'revenue' not in year_data or 'net_profit' not in year_data:
                        logger.warning(f"情景'{scenario}'中的年度数据格式不正确，跳过")
                        continue

                    data.append({
                        'Scenario': scenario,
                        'Year': year_data['year'],
                        'Revenue': year_data['revenue'],
                        'Net Profit': year_data['net_profit']
                    })

            if not data:
                logger.warning("没有有效的敏感性分析数据可可视化")
                fig = px.line(title='无有效数据 - 敏感性分析')
                return fig

            df = pd.DataFrame(data)
            fig = px.line(df, x='Year', y=['Revenue', 'Net Profit'], color='Scenario',
                         title='不同收入增长率对财务表现的影响',
                         labels={'value': '金额 (万元)', 'variable': '指标'}, markers=True)
            logger.info("敏感性分析图表创建完成")
            return fig

        except Exception as e:
            logger.error(f"创建敏感性分析图表时出错: {str(e)}", exc_info=True)
            fig = px.line(title='创建敏感性分析图表失败')
            fig.add_annotation(text=f'错误: {str(e)}', showarrow=True, x=0.5, y=0.5, xref='paper', yref='paper')
            return fig
        """创建财务预测可视化图表
        
        Args:
            forecast_data (dict): 预测财务数据
            
        Returns:
            plotly.graph_objects.Figure: 可视化图表
        """
        fig = go.Figure()
        
        # 添加营收预测
        fig.add_trace(go.Bar(
            x=forecast_data['年份'],
            y=forecast_data['总营收'],
            name='总营收',
            marker_color='royalblue'
        ))
        
        # 添加净利润预测
        fig.add_trace(go.Bar(
            x=forecast_data['年份'],
            y=forecast_data['净利润'],
            name='净利润',
            marker_color='lightgreen'
        ))
        
        # 更新布局
        fig.update_layout(
            title='未来财务预测',
            xaxis_title='年份',
            yaxis_title='金额 (元)',
            barmode='group',
            template='plotly_white'
        )
        
        return fig
    
    def sensitivity_analysis(self, growth_rates=None, years=5):
        """进行收入增长率敏感性分析
        
        Args:
            growth_rates (list): 可选，自定义增长率列表
            years (int): 预测年数
        
        Returns:
            dict: 不同增长率情景下的各年财务数据
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("开始敏感性分析")

        if growth_rates is None:
            growth_rates = [0.05, 0.08, 0.1, 0.12, 0.15]
            logger.debug(f"使用默认增长率列表: {growth_rates}")
        else:
            logger.debug(f"使用自定义增长率列表: {growth_rates}")

        results = {}
        historical_data = self.historical_data

        try:
            # 处理历史数据为空的情况
            if historical_data.empty:
                logger.warning("历史数据为空，使用默认值进行敏感性分析")
                base_revenue = 10000000  # 默认基础收入
                base_margin = 0.15  # 默认利润率
                tax_rate = 0.25  # 默认税率
                latest_year = 2023  # 默认基准年份
            else:
                # 使用中文键名以保持一致性
                base_revenue = historical_data['总营收'].iloc[-1]
                base_margin = historical_data['净利润率'].iloc[-1] if '净利润率' in historical_data.columns else 0.15
                tax_rate = historical_data['所得税率'].iloc[-1] if '所得税率' in historical_data.columns else 0.25
                latest_year = int(historical_data.index[-1])
                logger.debug(f"基础数据 - 收入: {base_revenue}, 利润率: {base_margin}, 税率: {tax_rate}, 基准年份: {latest_year}")

            for rate in growth_rates:
                scenario_name = f'{rate*100:.1f}%增长率'
                results[scenario_name] = []
                revenue = base_revenue
                logger.debug(f"开始分析情景: {scenario_name}")
                
                for year_offset in range(1, years+1):
                    revenue *= (1 + rate)
                    net_profit = revenue * base_margin * (1 - tax_rate)
                    current_year = latest_year + year_offset
                    results[scenario_name].append({
                        'year': current_year,
                        'revenue': round(revenue, 2),
                        'net_profit': round(net_profit, 2)
                    })
                    logger.debug(f"  第{current_year}年 - 收入: {revenue:.2f}, 净利润: {net_profit:.2f}")

            logger.info("敏感性分析完成")
            return results
        except Exception as e:
            logger.error(f"敏感性分析出错: {str(e)}", exc_info=True)
            # 返回默认结构以避免应用崩溃
            return {"5%增长率": [{"year": 2024, "revenue": 0, "net_profit": 0}]}

# 创建工厂函数供外部调用
def get_financial_modeler(company_code) -> FinancialModeler:
    """
    获取财务建模实例
    
    Args:
        company_code: 公司代码
    
    Returns:
        FinancialModeler: 财务建模实例
    """
    return FinancialModeler(company_code)