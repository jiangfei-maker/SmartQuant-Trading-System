import akshare
import re

# 检查akshare模块中所有以stock开头且包含financial或balance或profit或cashflow的函数
def check_financial_apis():
    print("当前akshare模块可用的财务相关API:")
    print("=" * 70)
    
    # 获取akshare模块中的所有属性
    all_attrs = [attr for attr in dir(akshare) if not attr.startswith('_')]
    
    # 筛选财务相关API
    financial_patterns = [
        'stock.*balance', 'stock.*profit', 'stock.*cash',
        'stock.*financial', 'stock.*finance',
        'stock.*sheet', 'stock.*statement'
    ]
    
    financial_apis = []
    for attr in all_attrs:
        for pattern in financial_patterns:
            if re.match(pattern, attr, re.IGNORECASE):
                financial_apis.append(attr)
                break
    
    # 显示结果
    if financial_apis:
        for api in sorted(financial_apis):
            print(f"- {api}")
        print(f"\n总共找到 {len(financial_apis)} 个财务相关API")
    else:
        print("未找到任何财务相关API")
    
    print("=" * 70)
    print("\n其他可能有用的股票相关API:")
    print("=" * 70)
    
    # 显示一些可能有用的股票相关API
    stock_apis = [attr for attr in all_attrs if attr.startswith('stock')][:20]  # 只显示前20个
    for api in sorted(stock_apis):
        print(f"- {api}")
    
    print(f"\n显示了前20个，总共有 {len([attr for attr in all_attrs if attr.startswith('stock')])} 个股票相关API")

if __name__ == "__main__":
    check_financial_apis()