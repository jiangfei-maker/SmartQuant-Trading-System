import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from pathlib import Path

# 设置最长等待时间（秒）
MAX_WAIT_TIME = 30

# 添加项目根目录到Python路径
import sys
sys.path.append(str(Path(__file__).parent.parent))

class TestE2E:
    @pytest.fixture(scope='class')
    def driver(self):
        """初始化Selenium WebDriver"""
        # 设置Chrome选项
        options = webdriver.ChromeOptions()
        # 禁用无头模式以便观察测试过程
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # 初始化WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        # 添加初始等待
        time.sleep(5)

        yield driver

        # 测试结束后关闭浏览器
        driver.quit()

    def test_app_loads(self, driver):
        """测试应用是否能够加载"""
        # 启动Streamlit应用（假设已经在运行）
        # 实际使用时，可能需要先启动应用
        driver.get('http://localhost:8502')

        # 使用显式等待应用加载
        try:
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.title_contains('智能量化交易系统')
            )
        except Exception as e:
            driver.save_screenshot('app_load_error.png')
            print(f"应用加载失败: {str(e)}")
            print(driver.page_source)
            raise

        # 验证应用标题
        assert '智能量化交易系统' in driver.title

    def test_navigate_to_watchlist(self, driver):
        """测试导航到自选股页面"""
        print("=== 运行test_navigate_to_watchlist测试 ===")
        driver.get('http://localhost:8502')
        print(f"已导航到: {driver.current_url}")
        print(f"当前页面标题: {driver.title}")
        
        # 保存初始页面截图
        try:
            driver.save_screenshot('navigate_initial.png')
            print("已保存初始页面截图: navigate_initial.png")
        except Exception as e:
            print(f"保存初始截图失败: {str(e)}")
        
        # 使用显式等待，确保应用完全加载
        try:
            print("等待功能导航加载...")
            # 增加等待时间并添加轮询间隔
            wait = WebDriverWait(driver, MAX_WAIT_TIME, poll_frequency=1)
            wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '功能导航')]"))
            )
            print("功能导航已加载")
            # 保存功能导航加载后的截图
            driver.save_screenshot('navigate_sidebar_loaded.png')
            print("已保存功能导航加载后截图: navigate_sidebar_loaded.png")
        except Exception as e:
            driver.save_screenshot('app_sidebar_load_error.png')
            print(f"侧边栏加载失败: {str(e)}")
            print("页面源码前5000字符:", driver.page_source[:5000])
            raise

        # 点击侧边栏的自选股选项 - 使用更通用的定位策略
        try:
            # 先找到功能导航下的选择模块下拉框
            print("查找功能导航下拉框...")
            # 增加等待时间并添加轮询间隔
            wait = WebDriverWait(driver, MAX_WAIT_TIME, poll_frequency=1)
            selectbox = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '功能导航')]/following::div[contains(@class, 'stSelectbox')]"))
            )
            print("功能导航下拉框已找到")
            # 保存下拉框找到后的截图
            driver.save_screenshot('navigate_selectbox_found.png')
            print("已保存下拉框找到后截图: navigate_selectbox_found.png")
            # 点击下拉框打开选项
            selectbox.click()
            print("已点击下拉框")
            # 等待选项加载
            time.sleep(2)
            print("等待选项加载...")
            wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'stSelectbox')]//div[text()='自选股']"))
            )
            print("自选股选项已加载")
            # 保存选项加载后的截图
            driver.save_screenshot('navigate_option_loaded.png')
            print("已保存选项加载后截图: navigate_option_loaded.png")
            # 在下拉框中找到自选股选项
            watchlist_option = driver.find_element(By.XPATH, "//div[contains(@class, 'stSelectbox')]//div[text()='自选股']")
            watchlist_option.click()
            print("已选择自选股选项")
        except Exception as e:
            # 保存截图以便调试
            driver.save_screenshot('navigate_to_watchlist_error.png')
            # 打印页面源码帮助调试
            print("页面源码前5000字符:", driver.page_source[:5000])
            raise e
        
        # 等待页面加载
        print("等待自选股页面加载...")
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '自选股管理')]"))
        )
        print("自选股页面已加载")

        # 验证是否导航到自选股页面
        assert '自选股管理' in driver.page_source
        print("test_navigate_to_watchlist测试通过")

    def test_add_stock_to_watchlist(self, driver):
        """测试添加股票到自选股"""
        print("=== 运行test_add_stock_to_watchlist测试 ===")
        driver.get('http://localhost:8502')
        print(f"已导航到: {driver.current_url}")
        print(f"当前页面标题: {driver.title}")
        
        # 保存初始页面截图
        try:
            driver.save_screenshot('add_stock_initial.png')
            print("已保存初始页面截图: add_stock_initial.png")
        except Exception as e:
            print(f"保存初始截图失败: {str(e)}")
        
        # 先导航到自选股页面
        self.test_navigate_to_watchlist(driver)

        # 等待添加新证券代码元素加载
        try:
            print("等待添加新证券代码元素加载...")
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '添加新证券代码')]"))
            )
            print("添加新证券代码元素已加载")
        except Exception as e:
            driver.save_screenshot('add_stock_element_error.png')
            print(f"添加新证券代码元素加载失败: {str(e)}")
            print(driver.page_source)
            raise

        # 输入股票代码
        try:
            # 定位添加新证券代码输入框
            print("定位股票代码输入框...")
            text_input = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '添加新证券代码')]/following::div[contains(@class, 'stTextInput')]//input"))
            )
            print("股票代码输入框已定位")
            stock_code = 'sh600000'
            text_input.send_keys(stock_code)
            print(f"已输入股票代码: {stock_code}")
            time.sleep(1)  # 等待输入生效
        except Exception as e:
            driver.save_screenshot('stock_input_error.png')
            print(driver.page_source)
            raise e

        # 点击保存按钮
        try:
            print("定位保存按钮...")
            save_button = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), '保存自选股')]"))
            )
            print("保存按钮已定位")
            save_button.click()
            print("已点击保存按钮")
        except Exception as e:
            driver.save_screenshot('add_button_error.png')
            print(driver.page_source)
            raise e
        
        # 等待保存完成
        print("等待保存完成...")
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '保存成功')]"))
        )
        print("保存成功")

        # 验证股票是否被添加
        assert 'sh600000' in driver.page_source
        print(f"验证股票代码 {stock_code} 已添加成功")
        print("test_add_stock_to_watchlist测试通过")

    def test_run_backtest(self, driver):
        """测试运行策略回测"""
        print("=== 运行test_run_backtest测试 ===")
        driver.get('http://localhost:8502')
        print(f"已导航到: {driver.current_url}")
        
        # 使用显式等待，确保应用完全加载
        try:
            print("等待功能导航加载...")
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '功能导航')]"))
            )
            print("功能导航已加载")
        except Exception as e:
            driver.save_screenshot('app_sidebar_load_error_3.png')
            print(f"侧边栏加载失败: {str(e)}")
            print("页面源码:", driver.page_source)
            raise

        # 导航到回测策略页面
        try:
            # 先找到功能导航下的选择模块下拉框
            print("尝试定位选择模块下拉框...")
            selectbox = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '功能导航')]/following::div[contains(@class, 'stSelectbox')]"))
            )
            print("选择模块下拉框已定位")
            # 点击下拉框打开选项
            selectbox.click()
            print("下拉框已点击")
            # 等待选项加载
            time.sleep(2)
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'stSelectbox')]//div[text()='回测策略']"))
            )
            print("回测策略选项已加载")
            # 在下拉框中找到回测策略选项
            backtest_option = driver.find_element(By.XPATH, "//div[contains(@class, 'stSelectbox')]//div[text()='回测策略']")
            backtest_option.click()
            print("已点击回测策略选项")
        except Exception as e:
            driver.save_screenshot('backtest_option_error.png')
            print("页面源码:", driver.page_source)
            raise e
        
        # 等待页面加载
        print("等待回测页面加载...")
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '证券代码')]"))
        )
        print("回测页面已加载")

        # 输入股票代码
        try:
            # 定位股票代码输入框
            print("尝试定位股票代码输入框...")
            text_input = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '证券代码')]/following::div[contains(@class, 'stTextInput')]//input"))
            )
            print("股票代码输入框已定位")
            stock_code = 'sh600000'
            text_input.send_keys(stock_code)
            print(f"已输入股票代码: {stock_code}")
            time.sleep(1)  # 等待输入生效
        except Exception as e:
            driver.save_screenshot('backtest_stock_input_error.png')
            print("页面源码:", driver.page_source)
            raise e

        # 点击运行回测按钮
        try:
            print("尝试定位运行回测按钮...")
            backtest_button = WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.visibility_of_element_located((By.XPATH, "//button[contains(text(), '运行回测')]"))
            )
            print("运行回测按钮已定位")
            backtest_button.click()
            print("已点击运行回测按钮")
        except Exception as e:
            driver.save_screenshot('backtest_button_error.png')
            print("页面源码:", driver.page_source)
            raise e
        
        # 等待回测完成
        print("等待回测完成...")
        WebDriverWait(driver, MAX_WAIT_TIME).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), '回测完成')]"))
        )
        print("回测已完成")

        # 验证回测是否完成
        assert '回测完成' in driver.page_source
        print("test_run_backtest测试通过")

if __name__ == '__main__':
    # 创建测试报告目录
    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(report_dir, exist_ok=True)

    # 运行测试并生成HTML报告
    pytest.main([
        'run_e2e_tests.py',
        '-v',
        '--html=tests/reports/e2e_test_report.html',
        '--self-contained-html'
    ])