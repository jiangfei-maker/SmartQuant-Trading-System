#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试修复：验证data_processor.py和llm_service.py中的关键功能
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 配置日志
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("TestFixes")


def test_data_processor():
    """测试DataProcessor是否能够正常获取股票数据"""
    logger.info("=== 开始测试DataProcessor ===")
    try:
        from data_processor import DataProcessor
        processor = DataProcessor()
        
        # 使用工商银行(sh601398)作为测试股票代码
        stock_code = "sh601398"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        logger.info(f"尝试获取{stock_code}的股票数据(最近7天)")
        df = processor.fetch_stock_data(stock_code, start_date, end_date)
        
        if df is not None and not df.empty:
            logger.info(f"成功获取数据，数据形状: {df.shape}")
            logger.info(f"数据列名: {df.columns.tolist()}")
            logger.info("DataProcessor测试通过")
            return True
        else:
            logger.error("获取到空数据")
            return False
    except Exception as e:
        logger.error(f"DataProcessor测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_service():
    """测试LLM服务是否能够正常初始化"""
    logger.info("=== 开始测试LLM服务 ===")
    try:
        # 导入llm相关模块
        from llm_service import get_llm_processor
        from config.llm_config import get_llm_config
        
        # 获取配置
        config_obj = get_llm_config()
        logger.info("成功获取LLM配置")
        
        # 尝试获取处理器（不使用API密钥，仅测试初始化）
        config = config_obj.get_config()
        # 设置空的API密钥以避免实际调用API
        config['openrouter_api_key'] = None
        config['openai_api_key'] = None
        
        logger.info("尝试获取LLM处理器(测试模式)")
        # 由于没有API密钥，预期会抛出ValueError
        try:
            processor = get_llm_processor(config)
            logger.info("LLM处理器获取成功")
            return True
        except ValueError as e:
            if "API密钥未配置" in str(e):
                logger.info("预期的API密钥错误，LLM服务结构正常")
                return True
            else:
                logger.error(f"LLM处理器获取失败: {str(e)}")
                return False
    except Exception as e:
        logger.error(f"LLM服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_analyzer():
    """测试SmartAnalyzer初始化是否成功"""
    logger.info("=== 开始测试SmartAnalyzer ===")
    try:
        from smart_analyzer import SmartAnalyzer
        
        # 初始化SmartAnalyzer，不提供API密钥
        analyzer = SmartAnalyzer()
        logger.info("SmartAnalyzer初始化成功")
        
        # 检查sklearn是否正常导入
        if analyzer.has_sklearn:
            logger.info("scikit-learn导入成功")
        else:
            logger.warning("scikit-learn导入失败")
        
        # 检查LLM服务状态
        if analyzer.has_llm:
            logger.info("LLM服务初始化成功")
        else:
            logger.info("LLM服务未初始化(预期行为，未提供API密钥)")
        
        logger.info("SmartAnalyzer测试通过")
        return True
    except Exception as e:
        logger.error(f"SmartAnalyzer测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    logger.info("=== 开始修复验证测试 ===")
    
    # 测试各个模块
    results = {
        "data_processor": test_data_processor(),
        "llm_service": test_llm_service(),
        "smart_analyzer": test_smart_analyzer()
    }
    
    # 打印测试结果摘要
    logger.info("\n=== 测试结果摘要 ===")
    all_passed = True
    for module, passed in results.items():
        status = "通过" if passed else "失败"
        logger.info(f"{module}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 所有修复验证测试通过！")
    else:
        logger.warning("\n⚠️ 部分测试失败，请检查日志获取详细信息。")
    
    logger.info("=== 修复验证测试结束 ===")


if __name__ == "__main__":
    main()