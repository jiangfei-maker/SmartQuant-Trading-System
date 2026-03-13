import akshare
import inspect

# 检查akshare版本
print(f"当前AKShare版本: {akshare.__version__}")
print("\n查找分钟线相关API...")

# 获取所有akshare属性
all_attributes = dir(akshare)

# 查找与分钟线相关的API
minute_apis = []
for attr_name in all_attributes:
    # 查找包含'minute'或类似含义的API
    if 'minute' in attr_name.lower():
        try:
            attr = getattr(akshare, attr_name)
            if callable(attr):
                minute_apis.append(attr_name)
                # 打印每个API的签名
                sig = inspect.signature(attr)
                print(f"- {attr_name}{sig}")
        except Exception as e:
            pass

print(f"\n找到的分钟线API数量: {len(minute_apis)}")

# 如果没有找到，尝试查找其他可能的K线API
if not minute_apis:
    print("\n尝试查找股票K线相关API:")
    kline_apis = [attr for attr in all_attributes if 'stock' in attr.lower() and 'k' in attr.lower()]
    for api in kline_apis[:20]:  # 显示前20个
        print(f"- {api}")
    print(f"\n找到的股票K线API总数: {len(kline_apis)}")