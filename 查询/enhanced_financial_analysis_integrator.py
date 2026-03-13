import os
import logging
from datetime import datetime
import json
from enhanced_financial_analyzer import EnhancedFinancialAnalyzer

# 配置日志系统
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EnhancedFinancialAnalysisIntegrator')

class EnhancedFinancialAnalysisIntegrator:
    """
    增强版财务分析集成器
    基于增强版财务分析器，提供文件管理、分析执行和结果导出的完整功能
    """
    
    def __init__(self, data_dir=None, results_dir=None):
        """
        初始化增强版财务分析集成器
        
        参数:
            data_dir: 数据文件目录，默认为None
            results_dir: 结果文件保存目录，默认为None
        """
        self.logger = logger
        self.logger.info("增强版财务分析集成器已初始化")
        
        # 设置数据目录和结果目录
        # 优先使用financial_data目录，这是系统中财务数据的标准存储位置
        self.data_dir = data_dir if data_dir else os.path.join(os.getcwd(), 'financial_data')
        self.results_dir = results_dir if results_dir else os.path.join(os.getcwd(), 'results')
        
        # 确保目录存在
        for dir_path in [self.data_dir, self.results_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.logger.info(f"已创建目录: {dir_path}")
    
    def get_available_files(self):
        """
        获取可用的财务数据文件列表
        
        返回:
            list: 文件路径列表
        """
        try:
            self.logger.info(f"开始获取可用的财务数据文件，目录: {self.data_dir}")
            
            # 获取目录下的所有文件
            files = []
            for file_name in os.listdir(self.data_dir):
                file_path = os.path.join(self.data_dir, file_name)
                # 检查是否为文件且是支持的格式
                if os.path.isfile(file_path) and self._is_supported_file(file_name):
                    files.append(file_path)
            
            # 按文件修改时间排序（最新的在前）
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            self.logger.info(f"成功获取{len(files)}个可用的财务数据文件")
            return files
        except Exception as e:
            self.logger.error(f"获取可用文件时出错: {str(e)}")
            return []
    
    def _is_supported_file(self, file_name):
        """
        检查文件是否为支持的格式
        
        参数:
            file_name: 文件名
            
        返回:
            bool: 是否支持该文件格式
        """
        supported_extensions = ['.xlsx', '.xls', '.csv', '.json']
        file_ext = os.path.splitext(file_name)[1].lower()
        return file_ext in supported_extensions
    
    def analyze_file(self, file_path):
        """
        分析单个财务数据文件
        
        参数:
            file_path: 财务数据文件路径
            
        返回:
            dict: 分析结果字典，包含成功状态、分析摘要和完整分析结果
        """
        try:
            self.logger.info(f"开始分析文件: {file_path}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.logger.error(f"文件不存在: {file_path}")
                return {"success": False, "error": "文件不存在"}
            
            # 创建增强版财务分析器实例
            analyzer = EnhancedFinancialAnalyzer()
            
            # 加载数据
            if not analyzer.load_data(file_path):
                self.logger.error(f"加载文件失败: {file_path}")
                return {"success": False, "error": "数据加载失败"}
            
            # 执行完整分析
            self.logger.info("开始执行完整财务分析")
            analysis_result = analyzer.run_full_analysis()
            
            # 检查分析结果
            if "error" in analysis_result:
                self.logger.error(f"分析过程出错: {analysis_result['error']}")
                return {"success": False, "error": analysis_result['error']}
            
            # 导出分析报告
            report_file_path = self._export_analysis_report(analysis_result, file_path)
            
            # 生成分析摘要
            analysis_summary = self._generate_analysis_summary(analysis_result)
            
            self.logger.info(f"文件分析完成: {file_path}")
            return {
                "success": True,
                "summary": analysis_summary,
                "analysis_summary": analysis_summary,  # 添加这个键以兼容app.py中的访问
                "report_path": report_file_path,
                "full_analysis_result": analysis_result
            }
        except Exception as e:
            self.logger.error(f"分析文件时出错: {str(e)}")
            import traceback
            self.logger.error(f"错误堆栈: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}
    
    def _export_analysis_report(self, analysis_result, original_file_path):
        """
        导出分析报告
        
        参数:
            analysis_result: 分析结果字典
            original_file_path: 原始文件路径
            
        返回:
            str: 导出的报告文件路径
        """
        try:
            self.logger.info("开始导出分析报告")
            
            # 获取原始文件名（不含扩展名）
            original_file_name = os.path.splitext(os.path.basename(original_file_path))[0]
            
            # 生成报告文件名（包含时间戳，避免覆盖）
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file_name = f"analysis_report_{original_file_name}_{current_time}.json"
            
            # 构建完整的报告文件路径
            report_file_path = os.path.join(self.results_dir, report_file_name)
            
            # 创建增强版财务分析器实例用于导出报告
            analyzer = EnhancedFinancialAnalyzer()
            
            # 导出报告
            if analyzer.export_report(analysis_result, report_file_path):
                self.logger.info(f"分析报告已导出至: {report_file_path}")
                return report_file_path
            else:
                self.logger.error("导出分析报告失败")
                return ""
        except Exception as e:
            self.logger.error(f"导出分析报告时出错: {str(e)}")
            return ""
    
    def _generate_analysis_summary(self, analysis_result):
        """
        生成分析摘要
        
        参数:
            analysis_result: 分析结果字典
            
        返回:
            str: 格式化的分析摘要（Markdown格式）
        """
        try:
            self.logger.info("开始生成分析摘要")
            
            # 获取综合结论
            comprehensive_conclusion = analysis_result.get("综合结论", {})
            
            # 构建Markdown格式的摘要
            summary = "# 财务分析摘要\n\n"
            
            # 添加公司信息
            company_info = analysis_result.get("公司信息", {})
            if company_info:
                summary += "## 公司信息\n"
                for key, value in company_info.items():
                    summary += f"- **{key}**: {value}\n"
                summary += "\n"
            
            # 添加总体经营状况
            overall_status = comprehensive_conclusion.get("公司总体经营状况", "无法评估")
            summary += f"## 公司总体经营状况\n{overall_status}\n\n"
            
            # 添加核心竞争优势
            advantages = comprehensive_conclusion.get("核心竞争优势", [])
            if advantages:
                summary += "## 核心竞争优势\n"
                for i, advantage in enumerate(advantages, 1):
                    summary += f"{i}. {advantage}\n"
                summary += "\n"
            
            # 添加主要风险因素
            risks = comprehensive_conclusion.get("主要风险因素", [])
            if risks:
                summary += "## 主要风险因素\n"
                for i, risk in enumerate(risks, 1):
                    summary += f"{i}. {risk}\n"
                summary += "\n"
            
            # 添加投资价值评估
            investment_value = comprehensive_conclusion.get("投资价值评估", "无法评估")
            summary += f"## 投资价值评估\n{investment_value}\n\n"
            
            # 添加综合建议
            recommendations = comprehensive_conclusion.get("综合建议", "无法提供建议")
            summary += f"## 综合建议\n{recommendations}\n\n"
            
            # 添加时间戳
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary += f"---\n*生成时间: {current_time}*\n"
            
            self.logger.info("分析摘要生成完成")
            return summary
        except Exception as e:
            self.logger.error(f"生成分析摘要时出错: {str(e)}")
            return "生成分析摘要失败: " + str(e)
    
    def batch_analyze_files(self, file_paths=None):
        """
        批量分析多个财务数据文件
        
        参数:
            file_paths: 文件路径列表，如果为None则分析所有可用文件
            
        返回:
            dict: 批量分析结果，包含成功和失败的文件信息
        """
        try:
            self.logger.info("开始批量分析财务数据文件")
            
            # 如果未提供文件路径，则获取所有可用文件
            if file_paths is None:
                file_paths = self.get_available_files()
            
            # 初始化结果
            results = {
                "total_files": len(file_paths),
                "success_count": 0,
                "failure_count": 0,
                "success_files": [],
                "failure_files": []
            }
            
            # 逐个分析文件
            for file_path in file_paths:
                try:
                    # 分析单个文件
                    result = self.analyze_file(file_path)
                    
                    # 根据分析结果更新统计信息
                    if result["success"]:
                        results["success_count"] += 1
                        results["success_files"].append({
                            "file_path": file_path,
                            "report_path": result["report_path"]
                        })
                    else:
                        results["failure_count"] += 1
                        results["failure_files"].append({
                            "file_path": file_path,
                            "error": result["error"]
                        })
                except Exception as e:
                    self.logger.error(f"分析文件{file_path}时出错: {str(e)}")
                    results["failure_count"] += 1
                    results["failure_files"].append({
                        "file_path": file_path,
                        "error": str(e)
                    })
            
            self.logger.info(f"批量分析完成，成功: {results['success_count']}，失败: {results['failure_count']}")
            return results
        except Exception as e:
            self.logger.error(f"批量分析文件时出错: {str(e)}")
            return {"error": str(e)}

# 测试代码
if __name__ == "__main__":
    # 创建增强版财务分析集成器实例
    integrator = EnhancedFinancialAnalysisIntegrator()
    
    # 获取可用文件
    available_files = integrator.get_available_files()
    print(f"找到{len(available_files)}个可用的财务数据文件")
    
    # 如果有可用文件，分析第一个文件
    if available_files:
        print(f"正在分析第一个文件: {available_files[0]}")
        result = integrator.analyze_file(available_files[0])
        
        # 打印分析结果
        if result["success"]:
            print("分析成功!")
            print(f"报告保存路径: {result['report_path']}")
            print("\n分析摘要:\n")
            print(result['summary'])
        else:
            print(f"分析失败: {result['error']}")
    else:
        print("没有找到可用的财务数据文件")