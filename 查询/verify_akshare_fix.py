import akshare
import pandas as pd
import traceback

# 验证AKShare修复效果
def verify_akshare_fix():
    print("开始验证AKShare修复效果")
    print("=" * 60)
    
    # 检查AKShare版本
    try:
        version = akshare.__version__
        print(f"当前AKShare版本: {version}")
    except Exception as e:
        print(f"获取版本信息失败: {str(e)}")
        return
    
    # 测试基本股票数据API
    try:
        print("\n测试基本股票数据API:")
        # 获取A股实时行情
        stock_df = akshare.stock_zh_a_spot()
        print(f"成功获取A股实时行情数据，共{len(stock_df)}条记录")
        print(f"数据前5行:\n{stock_df.head()}")
    except Exception as e:
        print(f"A股实时行情获取失败: {str(e)}")
        traceback.print_exc()
    
    # 测试财务数据API
    print("\n测试财务数据API:")
    test_code = 'sh600000'  # 浦发银行
    
    # 测试资产负债表
    try:
        print(f"\n测试资产负债表(股票代码: {test_code}):")
        # 尝试使用financial_data_fetcher.py中使用的API
        balance_df = akshare.stock_balance_sheet_by_yearly_em(symbol=test_code)
        print(f"成功获取资产负债表数据，共{len(balance_df)}条记录")
        print(f"数据前5行:\n{balance_df.head()}")
    except Exception as e:
        print(f"资产负债表获取失败: {str(e)}")
        traceback.print_exc()
    
    # 测试利润表
    try:
        print(f"\n测试利润表(股票代码: {test_code}):")
        profit_df = akshare.stock_profit_sheet_by_yearly_em(symbol=test_code)
        print(f"成功获取利润表数据，共{len(profit_df)}条记录")
        print(f"数据前5行:\n{profit_df.head()}")
    except Exception as e:
        print(f"利润表获取失败: {str(e)}")
        traceback.print_exc()
    
    # 测试现金流量表
    try:
        print(f"\n测试现金流量表(股票代码: {test_code}):")
        cash_df = akshare.stock_cash_flow_sheet_by_yearly_em(symbol=test_code)
        print(f"成功获取现金流量表数据，共{len(cash_df)}条记录")
        print(f"数据前5行:\n{cash_df.head()}")
    except Exception as e:
        print(f"现金流量表获取失败: {str(e)}")
        traceback.print_exc()
    
    # 测试财务指标API
    try:
        print(f"\n测试财务指标API(股票代码: {test_code}):")
        indicator_df = akshare.stock_financial_analysis_indicator(symbol=test_code)
        print(f"成功获取财务指标数据，共{len(indicator_df)}条记录")
        print(f"数据前5行:\n{indicator_df.head()}")
    except Exception as e:
        print(f"财务指标获取失败: {str(e)}")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("验证完成")

if __name__ == "__main__":
    verify_akshare_fix()