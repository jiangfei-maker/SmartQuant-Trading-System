import pytest
import unittest.mock as mock
import pandas as pd
from pathlib import Path
from datetime import datetime
from data_processor import DataProcessor


class TestDataProcessor:
    @pytest.fixture
    def data_processor(self):
        return DataProcessor(data_dir='test_data')

    @pytest.fixture
    def mock_akshare(self):
        with mock.patch('akshare.stock_zh_a_hist') as mock_hist:
            # 创建模拟数据
            mock_data = pd.DataFrame({
                '日期': ['2023-01-01', '2023-01-02', '2023-01-03'],
                '开盘': [10.0, 11.0, 12.0],
                '最高': [10.5, 11.5, 12.5],
                '最低': [9.5, 10.5, 11.5],
                '收盘': [10.2, 11.2, 12.2],
                '成交量': [1000000, 1200000, 1500000],
                '成交额': [10200000, 13440000, 18300000]
            })
            mock_hist.return_value = mock_data
            yield mock_hist

    def test_init(self, data_processor):
        """测试初始化功能"""
        assert isinstance(data_processor.data_dir, Path)
        assert data_processor.data_dir.name == 'test_data'
        assert data_processor.data_dir.exists()

    def test_fetch_stock_data_cache(self, data_processor, mock_akshare, tmp_path):
        """测试从缓存获取数据功能"""
        # 创建测试缓存文件
        symbol = 'sh600000'
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)
        start_date_str = start_date.strftime('%Y%m%d')
        end_date_str = end_date.strftime('%Y%m%d')
        cache_path = data_processor.data_dir / f"{symbol}_{start_date_str}_{end_date_str}.parquet"

        # 创建模拟缓存数据
        mock_cache_data = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'open': [10.0, 11.0, 12.0],
            'high': [10.5, 11.5, 12.5],
            'low': [9.5, 10.5, 11.5],
            'close': [10.2, 11.2, 12.2],
            'volume': [1000000, 1200000, 1500000],
            'amount': [10200000, 13440000, 18300000]
        }).set_index('date')

        # 保存模拟缓存数据
        data_processor.save_to_cache(mock_cache_data, cache_path)

        # 调用fetch_stock_data，应该从缓存加载
        result = data_processor.fetch_stock_data(symbol, start_date, end_date)

        # 验证结果
        pd.testing.assert_frame_equal(result, mock_cache_data)
        mock_akshare.assert_not_called()

    def test_fetch_stock_data_new(self, data_processor, mock_akshare):
        """测试获取新数据功能"""
        symbol = 'sh600000'
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)

        # 调用fetch_stock_data
        result = data_processor.fetch_stock_data(symbol, start_date, end_date)

        # 验证结果
        assert not result.empty
        assert list(result.columns) == ['open', 'high', 'low', 'close', 'volume', 'amount']
        assert result.index.name == 'date'
        mock_akshare.assert_called_once_with(
            symbol='600000',  # 应该移除市场前缀
            period='daily',
            start_date='20230101',
            end_date='20230103',
            adjust='qfq'
        )

    def test_clean_data(self, data_processor):
        """测试数据清洗功能"""
        # 创建测试数据
        raw_data = pd.DataFrame({
            '日期': ['2023-01-01', '2023-01-02', '2023-01-03'],
            '开盘': [10.0, 11.0, 12.0],
            '最高': [10.5, 11.5, 12.5],
            '最低': [9.5, 10.5, 11.5],
            '收盘': [10.2, 11.2, 12.2],
            '成交量': [1000000, 1200000, 1500000],
            '成交额': [10200000, 13440000, 18300000]
        })

        # 调用clean_data
        cleaned_data = data_processor.clean_data(raw_data)

        # 验证结果
        assert list(cleaned_data.columns) == ['open', 'high', 'low', 'close', 'volume', 'amount']
        assert cleaned_data.index.name == 'date'
        assert cleaned_data.index.dtype == 'datetime64[ns]'

    def test_save_and_load_cache(self, data_processor, tmp_path):
        """测试保存和加载缓存功能"""
        # 创建测试数据
        test_data = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
            'open': [10.0, 11.0, 12.0],
            'high': [10.5, 11.5, 12.5],
            'low': [9.5, 10.5, 11.5],
            'close': [10.2, 11.2, 12.2],
            'volume': [1000000, 1200000, 1500000],
            'amount': [10200000, 13440000, 18300000]
        }).set_index('date')

        # 保存到缓存
        cache_path = tmp_path / 'test_cache.parquet'
        data_processor.save_to_cache(test_data, cache_path)

        # 从缓存加载
        loaded_data = data_processor.load_from_cache(cache_path)

        # 验证结果
        pd.testing.assert_frame_equal(test_data, loaded_data)

    def test_fetch_stock_data_error(self, data_processor):
        """测试数据获取失败情况"""
        symbol = 'invalid_symbol'
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 3)

        # 模拟akshare抛出异常
        with mock.patch('akshare.stock_zh_a_hist') as mock_hist:
            mock_hist.side_effect = ValueError('Invalid symbol')

            # 验证异常是否被正确捕获和抛出
            with pytest.raises(ValueError, match='数据获取失败'):
                data_processor.fetch_stock_data(symbol, start_date, end_date)