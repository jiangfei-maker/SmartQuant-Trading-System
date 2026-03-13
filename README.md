# SmartQuant Trading System (智能量化交易系统)

基于 Streamlit 的一站式智能量化交易与财务分析平台。本项目集成了实时行情获取、全套技术指标分析、策略回测、LLM 智能市场分析以及增强型财务报表可视化功能，旨在为投资者提供专业的数据支持和决策辅助。

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

## 核心功能

### 1. 多市场实时行情
- 支持 **A股、港股、美股、期货** 等多市场实时数据查询。
- 提供分时、日K、周K、月K等多周期行情展示。

### 2. 深度技术分析
- 内置多种经典技术指标：
  - **趋势指标**：MACD, MA, BOLL (布林带), SAR
  - **摆动指标**：RSI, KDJ, CCI, WR (威廉指标)
  - **能量指标**：OBV, 成交量均线
- 支持交互式 K 线图与指标叠加分析。

### 3. 增强型财务分析
- **杜邦分析**：深入拆解净资产收益率 (ROE)。
- **财务报表可视化**：资产负债表、利润表、现金流量表的结构化展示。
- **风险评估**：基于财务数据的自动风险评分与预警。
- **行业对比**：个股与行业平均水平的对比分析。

### 4. 智能投研 (AI Powered)
- 集成 LLM (大语言模型) 服务，提供智能化的市场情绪分析。
- 自动生成个股分析报告与投资建议。
- 支持自然语言交互的财经新闻解读。

### 5. 策略回测
- 提供灵活的策略回测框架。
- 支持自定义交易策略并生成回测报告。

## 快速开始

### 环境要求
- Python 3.8+
- 建议使用虚拟环境

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/jiangfei-maker/SmartQuant-Trading-System.git
cd SmartQuant-Trading-System
```

2. 安装依赖
```bash
pip install -r 查询/requirements.txt
```

### 运行项目

进入项目根目录后，运行以下命令启动 Streamlit 应用：

```bash
streamlit run 查询/app.py
```

应用启动后，请在浏览器访问 `http://localhost:8501`。

## 项目结构

```
SmartQuant-Trading-System/
├── 查询/                   # 核心代码目录
│   ├── app.py             # 应用主入口
│   ├── stock_info_query.py # 个股信息查询模块
│   ├── financial_data_fetcher.py # 财务数据获取
│   ├── technical_indicators.py   # 技术指标计算
│   ├── smart_analyzer.py   # 智能分析模块
│   ├── backtester.py       # 回测引擎
│   └── ...
├── data/                   # 本地数据存储
├── charts/                 # 生成的图表文件
└── README.md               # 项目说明文档
```

## 免责声明

本项目提供的所有数据、分析及建议仅供参考，不构成任何投资建议。金融市场有风险，投资需谨慎。

## 许可证

MIT License
