import akshare
import inspect

# 检查akshare版本
print(f"当前AKShare版本: {akshare.__version__}")
print("\n查找股票相关API...")

# 获取所有akshare属性
all_attributes = dir(akshare)

# 初始化stock_apis列表
stock_apis = []
for attr_name in all_attributes:
    if 'stock' in attr_name.lower() and ('k' in attr_name.lower() or 'minute' in attr_name.lower()):
        try:
            attr = getattr(akshare, attr_name)
            if callable(attr):
                stock_apis.append(attr_name)
                # 打印每个API的签名
                sig = inspect.signature(attr)
                print(f"- {attr_name}{sig}")
        except Exception as e:
            pass

print(f"\n找到的股票K线/分钟线API数量: {len(stock_apis)}")

# 如果没有找到，尝试更广泛的搜索
if not stock_apis:
    print("\n尝试查找所有包含'stock'的API:")
    stock_apis = [attr for attr in all_attributes if 'stock' in attr.lower()]
    for api in stock_apis[:10]:  # 只显示前10个
        print(f"- {api}")
    print(f"\n找到的包含'stock'的API总数: {len(stock_apis)}")