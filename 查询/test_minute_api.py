import akshare
import pandas as pd

# 检查akshare版本
print(f"当前AKShare版本: {akshare.__version__}")

# 尝试直接调用stock_zh_a_minute函数
try:
    print("\n尝试调用stock_zh_a_minute函数...")
    # 使用默认参数测试
    df = akshare.stock_zh_a_minute()  # 使用默认的贵州茅台(sh600519)股票
    print(f"调用成功! 数据形状: {df.shape}")
    print("前5行数据:")
    print(df.head())
    
    # 尝试使用其他股票代码测试
    print("\n尝试使用工商银行(sh601398)测试...")
    df_icbc = akshare.stock_zh_a_minute(symbol='sh601398')
    print(f"工商银行数据形状: {df_icbc.shape}")
    
    # 检查app.py中出错的代码调用方式
    print("\n检查app.py中的调用方式...")
    test_symbol = 'sh600000'  # 测试一个常见的股票代码
    df_test = akshare.stock_zh_a_minute(symbol=test_symbol, period="1")
    print(f"使用app.py中的参数调用成功! 数据形状: {df_test.shape}")
    
    print("\nstock_zh_a_minute函数工作正常!")

except AttributeError as e:
    print(f"AttributeError: {e}")
    print("\n检查是否正确导入了akshare模块...")
    print(f"akshare模块路径: {akshare.__file__ if hasattr(akshare, '__file__') else '未知'}")
    print(f"akshare模块属性列表长度: {len(dir(akshare))}")
    print("\n尝试通过dir()函数确认stock_zh_a_minute是否存在:")
    print('stock_zh_a_minute' in dir(akshare))
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()