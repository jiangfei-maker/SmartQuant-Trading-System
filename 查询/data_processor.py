import akshare as ak
import pandas as pd
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import logging
import akshare as ak

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def fetch_stock_data(self, symbol, start_date, end_date):
        """获取A股日线数据并缓存"""
        # 格式化日期为YYYYMMDD
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        
        cache_path = self.data_dir / f"{symbol}_{start_date_str}_{end_date_str}.parquet"
        if cache_path.exists():
            logger.info(f"从缓存加载数据: {cache_path}")
            return self.load_from_cache(cache_path)
        
        # 清理股票代码，移除市场前缀
        cleaned_symbol = symbol.replace('sh', '').replace('sz', '')
        logger.info(f"使用清理后的股票代码: {cleaned_symbol}")
        
        try:
            # 使用清理后的代码调用Akshare
            stock_df = ak.stock_zh_a_hist(symbol=cleaned_symbol, period="daily", start_date=start_date_str, end_date=end_date_str, adjust="qfq")
            logger.info(f"获取到数据形状: {stock_df.shape}, 列名: {stock_df.columns.tolist()}")
            
            if stock_df.empty:
                raise ValueError(f"未获取到 {cleaned_symbol} 的数据")
            
            processed_df = self.clean_data(stock_df)
            self.save_to_cache(processed_df, cache_path)
            return processed_df
        except Exception as e:
            logger.error(f"数据获取失败: {str(e)}")
            # 打印Akshare版本信息
            logger.info(f"Akshare版本: {ak.__version__}")
            raise

    def clean_data(self, df):
        # 打印当前DataFrame的列名，用于调试列映射问题
        logger.info("DataFrame columns: %s", df.columns.tolist())
        """数据清洗与标准化"""
        # 处理缺失值
        df = df.dropna()
        
        # 统一列名
        # 根据实际列名选择并映射
        if all(col in df.columns for col in ['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额']):
            df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量', '成交额']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        elif all(col in df.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume']):
            # 处理没有amount列的情况
            df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
            df['amount'] = 0  # 添加默认amount列
        elif all(col in df.columns for col in ['day', 'open', 'high', 'low', 'close', 'volume']):
            # 处理day作为时间列的情况
            df = df[['day', 'open', 'high', 'low', 'close', 'volume']]
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df['amount'] = 0  # 添加默认amount列
        elif all(col in df.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']):
            pass  # 已经是标准列名
        else:
            raise ValueError(f"数据列名不符合预期: {df.columns.tolist()}")
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        
        # 设置日期索引
        df = df.set_index('date')
        return df

    def save_to_cache(self, df, path):
        """保存数据到Parquet格式"""
        table = pa.Table.from_pandas(df)
        pq.write_table(table, path)
        logger.info(f"数据已保存到缓存: {path}")

    def load_from_cache(self, path):
        """从缓存加载数据"""
        table = pq.read_table(path)
        return table.to_pandas()