import streamlit as st
import sys
import os
import akshare as ak
import pandas as pd

# 页面配置
st.set_page_config(page_title="AKShare测试", layout="wide")
st.title("AKShare Streamlit环境测试")

# 显示Python和环境信息
st.subheader("环境信息")
st.write(f"Python版本: {sys.version}")
st.write(f"Python可执行文件: {sys.executable}")
st.write(f"当前工作目录: {os.getcwd()}")
st.write(f"模块搜索路径: {sys.path}")

# 显示akshare信息
st.subheader("AKShare信息")
try:
    st.write(f"AKShare版本: {ak.__version__}")
    st.write(f"AKShare模块路径: {ak.__file__}")
    st.write(f"AKShare属性数量: {len(dir(ak))}")
    
    # 检查stock_zh_a_minute函数
    st.write(f"'stock_zh_a_minute' 函数存在: {hasattr(ak, 'stock_zh_a_minute')}")
    if hasattr(ak, 'stock_zh_a_minute'):
        # 测试调用函数
        st.subheader("测试函数调用")
        stock_code = st.text_input("股票代码", value="sh600000")
        
        if st.button("获取分时数据"):
            try:
                with st.spinner("正在获取数据..."):
                    df = ak.stock_zh_a_minute(symbol=stock_code, period="1")
                st.success(f"数据获取成功! 共{len(df)}条记录")
                st.dataframe(df.head())
                
                # 绘制简单图表
                st.subheader("分时图")
                st.line_chart(df.set_index('day')['close'])
            except Exception as e:
                st.error(f"数据获取失败: {str(e)}")
                st.exception(e)

    # 检查app.py中使用的其他函数
    st.subheader("其他相关函数检查")
    function_checks = {
        'stock_zh_a_minute': hasattr(ak, 'stock_zh_a_minute'),
        'stock_zh_a_hist': hasattr(ak, 'stock_zh_a_hist'),
        'stock_zh_a_spot_em': hasattr(ak, 'stock_zh_a_spot_em')
    }
    st.dataframe(pd.DataFrame.from_dict(function_checks, orient='index', columns=['存在状态']))
    
    # 提供修复建议
    st.subheader("修复建议")
    if hasattr(ak, 'stock_zh_a_minute'):
        st.info("看起来AKShare在Streamlit环境中正常工作！")
        st.markdown("""
        ### 可能的修复方案
        如果原应用仍然报错，建议尝试以下方法：
        
        1. **修改导入方式**：在app.py中使用绝对导入
        ```python
        from akshare import stock_zh_a_minute
        # 然后使用
        k_df = stock_zh_a_minute(symbol=stock_code, period="1")
        ```
        
        2. **添加异常处理**：在调用处添加try-except块
        ```python
        try:
            k_df = ak.stock_zh_a_minute(symbol=stock_code, period="1")
        except AttributeError:
            # 尝试直接导入
            from akshare.stock.stock_zh_a_sina import stock_zh_a_minute as minute_func
            k_df = minute_func(symbol=stock_code, period="1")
        except Exception as e:
            st.error(f"获取分时数据失败: {str(e)}")
            k_df = pd.DataFrame()
        ```
        
        3. **重启Streamlit服务**：有时候Streamlit的缓存会导致问题
        
        4. **检查是否有多个akshare版本**：使用`pip show akshare`确认安装位置
        """)
    else:
        st.error("在Streamlit环境中无法找到stock_zh_a_minute函数")
        st.info("这表明Streamlit可能在不同的环境中运行，或者存在多个akshare版本")
except Exception as e:
    st.error(f"检查akshare信息失败: {str(e)}")
    st.exception(e)
    st.info("这可能表明Streamlit在不同的环境中运行")