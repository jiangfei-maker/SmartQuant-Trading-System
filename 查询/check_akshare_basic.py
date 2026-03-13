import akshare
import sys

# 检查akshare模块的基本信息
def check_akshare_basic():
    print("检查akshare模块基本信息:")
    print("=" * 60)
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查akshare模块的路径
    print(f"akshare模块路径: {akshare.__file__ if hasattr(akshare, '__file__') else '未知'}")
    
    # 检查akshare模块的所有公共属性
    print("\nakshare模块的公共属性:")
    attrs = [attr for attr in dir(akshare) if not attr.startswith('_')]
    if attrs:
        for i, attr in enumerate(attrs[:50]):  # 只显示前50个
            print(f"- {attr}")
        if len(attrs) > 50:
            print(f"... 还有 {len(attrs) - 50} 个属性未显示")
    else:
        print("未找到任何公共属性")
    
    # 尝试获取一些基本数据（如果可能的话）
    print("\n尝试获取一些基本数据:")
    try:
        # 检查是否有market模块
        if hasattr(akshare, 'market'):
            print("找到market模块")
            market_attrs = [attr for attr in dir(akshare.market) if not attr.startswith('_')]
            print(f"market模块属性: {market_attrs}")
        else:
            print("未找到market模块")
    except Exception as e:
        print(f"检查market模块时出错: {str(e)}")
    
    try:
        # 检查是否有fund模块
        if hasattr(akshare, 'fund'):
            print("找到fund模块")
            fund_attrs = [attr for attr in dir(akshare.fund) if not attr.startswith('_')]
            print(f"fund模块属性: {fund_attrs[:10]}...")  # 只显示前10个
        else:
            print("未找到fund模块")
    except Exception as e:
        print(f"检查fund模块时出错: {str(e)}")
    
    # 尝试获取版本信息的其他方法
    print("\n尝试通过其他方式获取版本信息:")
    try:
        import importlib.metadata
        version = importlib.metadata.version('akshare')
        print(f"通过importlib.metadata获取到版本: {version}")
    except Exception as e:
        print(f"通过importlib.metadata获取版本失败: {str(e)}")

if __name__ == "__main__":
    check_akshare_basic()