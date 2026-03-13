import os
import sys
import logging
import pandas as pd
from datetime import datetime

# 添加财务分析模块的路径到系统路径
sys.path.append("c:\\Users\\34657\\Desktop\\测试\\财务分析")

# 导入财务分析模块
from ultimate_financial_analyzer import UltimateFinancialAnalyzer

# 配置日志系统
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('FinancialAnalysisIntegrator')

class FinancialAnalysisIntegrator:
    """
    财务分析集成器
    用于将财务分析功能集成到现有项目中
    功能：读取财务数据文件，执行分析，并返回结果
    """
    
    def __init__(self, financial_data_dir="financial_data"):
        """
        初始化财务分析集成器
        
        参数:
            financial_data_dir: 财务数据文件所在目录
        """
        self.financial_data_dir = financial_data_dir
        self.analyzer = None
        self.logger = logger
        self.logger.info("财务分析集成器已初始化")
        
        # 确保分析结果目录存在
        self.analysis_results_dir = "financial_analysis_results"
        if not os.path.exists(self.analysis_results_dir):
            os.makedirs(self.analysis_results_dir)
            self.logger.info(f"已创建分析结果目录: {self.analysis_results_dir}")
    
    def get_available_files(self):
        """
        获取可用的财务数据文件列表
        
        返回:
            list: 文件路径列表
        """
        try:
            # 检查目录是否存在
            if not os.path.exists(self.financial_data_dir):
                self.logger.error(f"财务数据目录不存在: {self.financial_data_dir}")
                return []
            
            # 获取目录下所有Excel文件
            files = []
            for file in os.listdir(self.financial_data_dir):
                if file.endswith('.xlsx') or file.endswith('.xls'):
                    files.append(os.path.join(self.financial_data_dir, file))
            
            # 按修改时间排序，最新的在前
            files.sort(key=os.path.getmtime, reverse=True)
            
            self.logger.info(f"找到{len(files)}个可用的财务数据文件")
            return files
        except Exception as e:
            self.logger.error(f"获取可用文件列表失败: {str(e)}")
            return []
    
    def analyze_file(self, file_path):
        """
        分析指定的财务数据文件
        
        参数:
            file_path: 财务数据文件路径
        
        返回:
            dict: 分析结果
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return {
                    "success": False,
                    "error": f"文件不存在: {file_path}"
                }
            
            # 初始化分析器
            self.analyzer = UltimateFinancialAnalyzer()
            
            # 加载数据
            self.logger.info(f"开始加载文件: {file_path}")
            load_success = self.analyzer.load_data(file_path)
            if not load_success:
                self.logger.error(f"数据加载失败")
                return {
                    "success": False,
                    "error": "数据加载失败"
                }
            
            # 执行分析
            self.logger.info(f"开始分析文件: {file_path}")
            analysis_result = self.analyzer.run_full_analysis()
            
            # 获取综合结论
            comprehensive_conclusion = analysis_result.get("综合结论", {})
            
            # 导出报告
            file_name = os.path.basename(file_path)
            report_file_name = f"{os.path.splitext(file_name)[0]}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file_path = os.path.join(self.analysis_results_dir, report_file_name)
            
            self.analyzer.export_report(analysis_result, report_file_path)
            
            self.logger.info(f"分析完成，报告已保存至: {report_file_path}")
            
            # 构建分析摘要
            analysis_summary = self._generate_analysis_summary(comprehensive_conclusion)
            
            # 构建报告格式
            report = {
                "经营状况": comprehensive_conclusion.get("公司总体经营状况", "无法评估"),
                "竞争优势": "\n".join([f"{i}. {adv}" for i, adv in enumerate(comprehensive_conclusion.get("核心竞争优势", []), 1)]),
                "风险因素": "\n".join([f"{i}. {risk}" for i, risk in enumerate(comprehensive_conclusion.get("主要风险因素", []), 1)]),
                "投资建议": comprehensive_conclusion.get("综合建议", "无法提供建议")
            }
            
            # 返回分析结果
            return {
                "success": True,
                "file_path": file_path,
                "report_file_path": report_file_path,
                "analysis_summary": analysis_summary,
                "report": report,
                "full_analysis_result": analysis_result
            }
        except Exception as e:
            self.logger.error(f"分析文件时出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"分析出错: {str(e)}"
            }
    
    def _generate_analysis_summary(self, comprehensive_conclusion):
        """
        生成分析摘要
        
        参数:
            comprehensive_conclusion: 综合结论字典
        
        返回:
            str: 格式化的分析摘要
        """
        summary_parts = []
        
        summary_parts.append(f"### 📊 公司总体经营状况\n{comprehensive_conclusion.get('公司总体经营状况', '无法评估')}")
        
        advantages = comprehensive_conclusion.get('核心竞争优势', [])
        if advantages:
            advantages_text = "\n".join([f"- {adv}" for adv in advantages])
            summary_parts.append(f"### 🏆 核心竞争优势\n{advantages_text}")
        else:
            summary_parts.append("### 🏆 核心竞争优势\n暂无明显竞争优势")
        
        risks = comprehensive_conclusion.get('主要风险因素', [])
        if risks:
            risks_text = "\n".join([f"- {risk}" for risk in risks])
            summary_parts.append(f"### ⚠️ 主要风险因素\n{risks_text}")
        else:
            summary_parts.append("### ⚠️ 主要风险因素\n未发现明显风险因素")
        
        summary_parts.append(f"### 💡 投资价值评估\n{comprehensive_conclusion.get('投资价值评估', '无法评估')}")
        summary_parts.append(f"### 📝 综合建议\n{comprehensive_conclusion.get('综合建议', '无法提供建议')}")
        
        return "\n\n".join(summary_parts)
    
    def batch_analyze_files(self, file_paths=None):
        """
        批量分析多个财务数据文件
        
        参数:
            file_paths: 文件路径列表，如果为None则分析所有可用文件
        
        返回:
            dict: 分析结果字典，键为文件路径，值为分析结果
        """
        try:
            # 如果未提供文件列表，则获取所有可用文件
            if file_paths is None:
                file_paths = self.get_available_files()
            
            # 批量分析文件
            results = {}
            for file_path in file_paths:
                self.logger.info(f"开始批量分析文件: {file_path}")
                results[file_path] = self.analyze_file(file_path)
            
            return results
        except Exception as e:
            self.logger.error(f"批量分析文件时出错: {str(e)}")
            return {}

# 测试代码
if __name__ == "__main__":
    integrator = FinancialAnalysisIntegrator()
    
    # 获取可用文件
    files = integrator.get_available_files()
    print(f"可用的财务数据文件: {files}")
    
    # 分析第一个文件（如果有）
    if files:
        result = integrator.analyze_file(files[0])
        print(f"分析结果: {result}")