import sys
import os
import akshare
import inspect
import pandas as pd
from importlib import reload

# 检查Python版本和路径
print(f"Python版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")
print(f"当前工作目录: {os.getcwd()}")
print(f"模块搜索路径: {sys.path}")

# 检查akshare模块信息
print(f"\nakshare模块版本: {akshare.__version__ if hasattr(akshare, '__version__') else '未知'}")
print(f"akshare模块文件路径: {akshare.__file__ if hasattr(akshare, '__file__') else '未知'}")
print(f"akshare模块属性数量: {len(dir(akshare))}")

# 检查是否能直接获取stock_zh_a_minute函数
print("\n直接检查stock_zh_a_minute函数:")
print(f"'stock_zh_a_minute' in dir(akshare): {hasattr(akshare, 'stock_zh_a_minute')}")
if hasattr(akshare, 'stock_zh_a_minute'):
    func = akshare.stock_zh_a_minute
    print(f"函数类型: {type(func)}")
    print(f"函数签名: {inspect.signature(func)}")
    print(f"函数模块: {func.__module__}")

# 检查app.py中使用的其他相关函数
print("\n检查app.py中使用的其他函数:")
for func_name in ['stock_zh_a_hist', 'stock_zh_a_spot_em']:
    print(f"- {func_name} 存在: {hasattr(akshare, func_name)}")

# 尝试以不同方式导入akshare
print("\n尝试以不同方式导入akshare:")
try:
    import akshare as ak_new
    print(f"as别名方式导入成功: {hasattr(ak_new, 'stock_zh_a_minute')}")
except Exception as e:
    print(f"as别名方式导入失败: {e}")

try:
    from akshare import stock_zh_a_minute as minute_func
    print(f"直接导入函数成功: {callable(minute_func)}")
except Exception as e:
    print(f"直接导入函数失败: {e}")

# 尝试重新加载模块
print("\n尝试重新加载akshare模块:")
try:
    reload(akshare)
    print(f"重新加载后函数存在: {hasattr(akshare, 'stock_zh_a_minute')}")
except Exception as e:
    print(f"重新加载失败: {e}")

# 检查是否存在命名冲突
print("\n检查是否存在命名冲突:")
if 'ak' in dir():
    print(f"'ak'变量存在于当前命名空间，类型: {type(ak) if 'ak' in dir() else '不存在'}")

# 测试实际调用
print("\n测试实际调用stock_zh_a_minute:")
try:
    if hasattr(akshare, 'stock_zh_a_minute'):
        df = akshare.stock_zh_a_minute(symbol='sh600000', period='1')
        print(f"调用成功! 数据形状: {df.shape}")
    else:
        print("函数不存在，无法调用")
except Exception as e:
    print(f"调用失败: {e}")
    import traceback
    traceback.print_exc()

print("\n诊断完成!")