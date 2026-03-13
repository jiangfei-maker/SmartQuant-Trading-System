import akshare
import pandas as pd
import traceback
import akshare as ak

# 测试函数
def test_financial_apis():
    # 测试不同的财务数据API
    test_codes = ['sh600000', 'sh600036', 'sz000001']  # 测试多个股票代码
    results = {}
    
    print("开始测试AKShare财务数据API")
    print("=" * 60)
    
    # 测试方法1: 资产负债表
    print("\n测试资产负债表API:")
    try:
        # 尝试获取最新的版本信息
        import pkg_resources
        akshare_version = pkg_resources.get_distribution("akshare").version
        print(f"当前AKShare版本: {akshare_version}")
    except:
        print("无法获取AKShare版本信息")
    
    for code in test_codes:
        results[code] = {}
        print(f"\n测试股票: {code}")
        
        # 测试资产负债表 - 方法1
        try:
            print("  测试资产负债表(stock_balance_sheet_by_yearly_em)")
            df = akshare.stock_balance_sheet_by_yearly_em(symbol=code)
            print(f"  成功获取数据，行数: {len(df)}")
            results[code]['balance_sheet_1'] = "成功"
        except Exception as e:
            print(f"  失败: {str(e)}")
            results[code]['balance_sheet_1'] = f"失败: {str(e)}"
        
        # 测试利润表
        try:
            print("  测试利润表(stock_profit_sheet_by_yearly_em)")
            df = akshare.stock_profit_sheet_by_yearly_em(symbol=code)
            print(f"  成功获取数据，行数: {len(df)}")
            results[code]['profit_sheet'] = "成功"
        except Exception as e:
            print(f"  失败: {str(e)}")
            results[code]['profit_sheet'] = f"失败: {str(e)}"
        
        # 测试现金流量表
        try:
            print("  测试现金流量表(stock_cash_flow_sheet_by_yearly_em)")
            df = akshare.stock_cash_flow_sheet_by_yearly_em(symbol=code)
            print(f"  成功获取数据，行数: {len(df)}")
            results[code]['cash_flow'] = "成功"
        except Exception as e:
            print(f"  失败: {str(e)}")
            results[code]['cash_flow'] = f"失败: {str(e)}"
        
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    for code, result in results.items():
        print(f"\n{code}:")
        for api, status in result.items():
            print(f"  {api}: {status}")

def test_stock_historical_data():
    # 测试股票历史行情数据API
    print("\n" + "=" * 60)
    print("测试股票历史行情数据API")
    print("=" * 60)
    
    # 检查是否存在stock_zh_a_hist函数
    print(f"是否存在stock_zh_a_hist函数: {'stock_zh_a_hist' in dir(ak)}")
    
    # 列出ak中以stock开头的函数，查看是否有相关的替代函数
    print("\nakshare中以'stock'开头的函数（前20个）:")
    stock_functions = [func for func in dir(ak) if func.startswith('stock')]
    for func in stock_functions[:20]:
        print(f"- {func}")
    
    # 尝试获取数据
    if 'stock_zh_a_hist' in dir(ak):
        try:
            print("\n尝试获取股票历史数据...")
            df = ak.stock_zh_a_hist(symbol="600000", period="daily", start_date="20240101", end_date="20240110", adjust="qfq")
            print(f"成功获取数据，数据形状: {df.shape}")
            print("数据样例:")
            print(df.head())
        except Exception as e:
            print(f"获取数据失败: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    test_financial_apis()
    test_stock_historical_data()