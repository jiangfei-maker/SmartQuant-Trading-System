import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import logging
import chardet
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('news_processor')

class NewsProcessor:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Referer": "https://finance.sina.com.cn/"
        }
        self.news_sources = {
            'sina': {
                'name': '新浪财经',
                'url': 'https://finance.sina.com.cn/',
                'interval': 600  # 刷新间隔(秒)
            },
            'eastmoney': {
                'name': '东方财富',
                'url': 'https://finance.eastmoney.com/',
                'interval': 600
            },
            '163': {
                'name': '网易财经',
                'url': 'https://money.163.com/',
                'interval': 600
            }
        }
        self.last_fetch_time = {}
        self.news_cache = {}

    def fetch_news(self, source_id):
        """
        获取指定来源的新闻
        :param source_id: 新闻来源ID
        :return: 新闻列表，每条新闻包含标题、链接、发布时间等信息
        """
        if source_id not in self.news_sources:
            logger.error(f"未知的新闻来源: {source_id}")
            return []

        # 检查是否需要刷新
        current_time = time.time()
        if source_id in self.last_fetch_time and \
           current_time - self.last_fetch_time[source_id] < self.news_sources[source_id]['interval']:
            logger.info(f"使用缓存的{self.news_sources[source_id]['name']}新闻")
            return self.news_cache.get(source_id, [])

        try:
            source_info = self.news_sources[source_id]
            url = source_info['url']
            logger.info(f"正在获取{source_info['name']}的新闻: {url}")

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # 检测并设置正确的编码
            encoding = chardet.detect(response.content)['encoding'] or 'utf-8'
            html = response.content.decode(encoding, errors='replace')

            if source_id == 'sina':
                news_list = self._parse_sina_news(html)
            elif source_id == 'eastmoney':
                news_list = self._parse_eastmoney_news(html)
            elif source_id == '163':
                news_list = self._parse_163_news(html)
            else:
                news_list = []

            # 更新缓存
            self.news_cache[source_id] = news_list
            self.last_fetch_time[source_id] = current_time
            logger.info(f"成功获取{len(news_list)}条{source_info['name']}新闻")
            return news_list

        except Exception as e:
            logger.error(f"获取{self.news_sources.get(source_id, {}).get('name', source_id)}新闻失败: {str(e)}")
            return self.news_cache.get(source_id, [])

    def _parse_sina_news(self, html):
        """解析新浪财经新闻"""
        news_list = []
        soup = BeautifulSoup(html, 'html.parser')
        # 保存完整HTML内容到临时文件，以便分析
        with open('sina_finance_html_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        logger.info(f"新浪财经HTML内容已保存到sina_finance_html_debug.html文件")
        # 调试信息：查看HTML内容的前1000个字符
        logger.info(f"获取到的新浪财经HTML内容前1000字符: {html[:1000]}")

        # 更新选择器以适应新浪财经新的页面结构
        # 针对新浪财经主页的主要内容区域优化选择器
        selectors = [
            '#financeNews > div > ul > li',  # 财经新闻区域
            '#blk_1001 > div > ul > li',    # 重要新闻区域
            '.m-news-list li',              # 新闻列表
            '.m-top-news > ul > li',        # 顶部新闻
            '.news-item',                   # 通用新闻项
            '.list_009 li',                 # 列表项
            'li[data-id]',                  # 带data-id的列表项
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            logger.info(f"尝试{selector}选择器，匹配到: {len(items)}条")
            if len(items) > 3:
                break  # 降低匹配要求，至少匹配3条就认为有效

        # 如果所有选择器都失败，尝试直接从body中查找所有可能的新闻容器
        if len(items) < 3:
            logger.warning("未匹配到足够的新闻条目，可能新浪财经页面结构已更改")
            # 尝试查找所有可能包含新闻的容器
            containers = soup.select('div.container') or soup.select('div.wrapper') or soup.select('div.content')
            if containers:
                logger.info(f"尝试从容器中提取新闻，匹配到: {len(containers)}个容器")
                # 从第一个容器中尝试提取所有可能的新闻条目
                if containers[0]:
                    items = containers[0].find_all(recursive=False)
                    logger.info(f"从容器中提取到: {len(items)}个潜在新闻条目")
            
            # 如果仍然没有找到足够的条目，尝试查找所有a标签
            if len(items) < 3:
                items = soup.select('a[href]')
                logger.info(f"尝试所有a[href]标签，匹配到: {len(items)}条")
                
                # 如果还是不够，尝试提取所有文本块
                if len(items) < 3:
                    all_texts = [text for text in soup.stripped_strings if len(text) > 8]
                    logger.info(f"尝试提取所有文本块，匹配到: {len(all_texts)}条")
                    if len(all_texts) > 0:
                        # 创建临时的新闻条目
                        for text in all_texts[:30]:  # 取前30个文本块
                            fake_item = BeautifulSoup(f'<div>{text}</div>', 'html.parser')
                            items.append(fake_item)
                    else:
                        return news_list

        # 非新闻内容关键词过滤列表
        # 优化过滤词，减少误判
        non_news_keywords = [
            '新浪财经', '新闻首页', '新浪首页', '新浪导航', '登录', '意见反馈',
            '留言板', '新浪简介', 'About Sina', '广告服务', '联系我们', '招聘信息',
            '网站律师', 'SINA English', '通行证注册', '产品答疑', '版权所有',
            '返回顶部', '关闭', '首页', '导航', '分享', '收藏',
            '打印', '评论', '举报', '更多', '下载', '客户端', 'APP', '微博', '微信'
        ]

        # 新闻相关关键词列表（用于提高精准度）
        news_keywords = [
            '经济', '市场', '企业', '公司', '政策', '行业', '数据', '报告', '分析',
            '增长', '下降', '投资', '融资', '上市', '股价', '利润', '营收', '预测',
            '通胀', '利率', '汇率', '贸易', '合作', '竞争', '科技', '创新', '监管',
            '公告', '财报', '业绩', '并购', '重组', '减持', '增持', '分红', '配股',
            '涨停', '跌停', '上涨', '下跌', '政策', '措施', '会议', '讲话', '声明',
            '影响', '解读', '趋势', '前景', '风险', '机遇', '挑战', '变化', '改革',
            '调控', '刺激', '复苏', '下滑', '反弹', '持续', '加剧', '缓解', '维持'
        ]

        for item in items:
            try:
                # 标题和链接处理
                if hasattr(item, 'name') and item.name == 'a':
                    title_tag = item
                else:
                    # 尝试更多可能的标题标签
                    title_tag = item.select_one('a') or \
                                item.select_one('h1') or \
                                item.select_one('h2') or \
                                item.select_one('h3') or \
                                item.select_one('h4') or \
                                item.select_one('p') or \
                                item.select_one('.title') or \
                                item.select_one('.news-title') or \
                                item.select_one('.main-title') or \
                                item.select_one('.headline') or \
                                item.select_one('[class*="title"]') or \
                                item

                if not title_tag or not hasattr(title_tag, 'text'):
                    logger.warning(f"未找到有效标题标签: {item}")
                    continue

                title = title_tag.text.strip()
                if not title:
                    logger.warning(f"标题为空: {item}")
                    continue

                # 过滤非新闻内容
                if any(keyword in title for keyword in non_news_keywords):
                    logger.warning(f"过滤非新闻内容: {title}")
                    continue

                # 降低标题长度过滤阈值
                if len(title) < 6:
                    logger.warning(f"过滤过短标题: {title}")
                    continue

                # 提高新闻相关性：如果标题包含至少一个新闻关键词，则优先保留
                news_relevant = any(keyword in title for keyword in news_keywords)
                if not news_relevant:
                    logger.warning(f"标题可能不相关（无新闻关键词）: {title}")
                    # 降低不相关标题的优先级，但仍保留
                    # 放宽条件，获取更多可能的新闻
                    if len(news_list) >= 15:
                        continue

                # 处理链接
                link = ''
                if hasattr(title_tag, 'get'):
                    link = title_tag.get('href', '').strip()
                elif item.select_one('a'):
                    link = item.select_one('a').get('href', '').strip()
                elif item.select_one('link'):
                    link = item.select_one('link').get('href', '').strip()

                # 确保链接是完整的
                if link and not link.startswith('http'):
                    if link.startswith('/'):
                        link = 'https://finance.sina.com.cn' + link
                    else:
                        link = 'https://finance.sina.com.cn/' + link
                elif not link:
                    # 如果没有链接，使用新浪财经主页
                    link = 'https://finance.sina.com.cn'
                    logger.warning(f"链接为空，使用默认链接: {link}")

                # 时间 - 优化时间标签选择
                time_tag = item.select_one('.time') or \
                           item.select_one('span.time') or \
                           item.select_one('.news-time') or \
                           item.select_one('.m_time') or \
                           item.select_one('.time-source') or \
                           item.select_one('.publish-time') or \
                           item.select_one('span.date') or \
                           item.select_one('span[class*="time"]') or \
                           item.select_one('span[class*="date"]')

                time_str = time_tag.text.strip() if time_tag else ''
                # 增加从文本中提取时间的逻辑
                if not time_str:
                    # 尝试从item文本中提取可能的时间格式
                    import re
                    time_patterns = [
                        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}',  # 2025-08-21 14:30
                        r'\d{2}:\d{2}',                      # 14:30
                        r'\d{4}\.\d{2}\.\d{2}',          # 2025.08.21
                    ]
                    for pattern in time_patterns:
                        match = re.search(pattern, item.text)
                        if match:
                            time_str = match.group()
                            break
                logger.info(f"解析新浪财经时间字符串: {time_str}")

                # 处理时间格式
                pub_time = pd.Timestamp.now()
                try:
                    if not time_str:
                        logger.warning("时间字符串为空，使用当前时间")
                    elif '刚刚' in time_str:
                        pub_time = pd.Timestamp.now()
                    elif '今天' in time_str:
                        # 格式如 '今天 09:30'
                        time_part = time_str.replace('今天', '').strip()
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_part}")
                    elif '昨天' in time_str:
                        # 格式如 '昨天 14:45'
                        time_part = time_str.replace('昨天', '').strip()
                        pub_time = pd.Timestamp(f"{(pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')} {time_part}")
                    elif '小时前' in time_str or '分钟前' in time_str or '秒前' in time_str:
                        # 格式如 '1小时前', '30分钟前', '10秒前'
                        num = int(time_str.split('前')[0].replace('小时', '').replace('分钟', '').replace('秒', ''))
                        if '小时前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(hours=num)
                        elif '分钟前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(minutes=num)
                        else:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(seconds=num)
                    elif len(time_str) > 5:
                        # 格式如 '2023-08-12 09:30' 或 '2023/08/12 09:30' 或 '2023年08月12日 09:30'
                        time_str = time_str.replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '').replace('：', ':')
                        pub_time = pd.Timestamp(time_str)
                    else:
                        # 格式如 '09:30'
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_str}")
                except Exception as e:
                    # 如果解析失败，使用当前时间
                    logger.warning(f"解析新浪财经时间失败: {time_str}, 错误: {str(e)}")
                    pub_time = pd.Timestamp.now()

                # 来源
                source = '新浪财经'

                # 添加到新闻列表
                news_item = {
                    'title': title,
                    'url': link,
                    'pub_time': pub_time,
                    'source': source,
                    'relevant': news_relevant
                }
                news_list.append(news_item)
                logger.info(f"成功解析新闻: {title}")
            except Exception as e:
                logger.error(f"解析新闻条目失败: {str(e)}", exc_info=True)
                continue

        # 按相关性和时间排序
        news_list.sort(key=lambda x: (not x['relevant'], -x['pub_time'].timestamp()))

        # 去重（基于标题和链接）
        unique_news = {f"{news['title']}_{news['url']}": news for news in news_list}.values()
        news_list = list(unique_news)

        # 限制返回新闻数量，确保质量
        news_list = news_list[:20]

        logger.info(f"共解析{len(news_list)}条新浪财经新闻")
        return news_list
        
    def _parse_eastmoney_news(self, html):
        """解析东方财富新闻"""
        news_list = []
        soup = BeautifulSoup(html, 'html.parser')
        logger.info(f"获取到的东方财富HTML内容前500字符: {html[:500]}")

        # 更新选择器以适应东方财富新的页面结构
        selectors = [
            '.news_item',           # 主要选择器
            '.article-item',        # 备用选择器1
            '.list_item',           # 备用选择器2
            '.item',                # 备用选择器3
            '.finance_news_item',   # 新增选择器4
            '.common_news_item',    # 新增选择器5
            '.m-news-list li',      # 新增选择器6
            '.newslist li',         # 新增选择器7
            '.bd_i',                # 新增选择器8
            '.cell',                # 新增选择器9
            '.card',                # 新增选择器10
            '.news-card',           # 新增选择器11
            'div[class*="news"]', # 新增选择器12 (包含'news'的class)
            'div[class*="article"]', # 新增选择器13 (包含'article'的class)
            'div[class*="item"]', # 新增选择器14 (包含'item'的class)
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            logger.info(f"尝试{selector}选择器，匹配到: {len(items)}条")
            if len(items) > 5:
                break  # 至少匹配5条才认为有效

        # 如果所有选择器都失败，尝试直接从body中查找所有a标签作为最后的备选方案
        if len(items) < 5:
            logger.warning("未匹配到足够的新闻条目，可能东方财富页面结构已更改")
            # 尝试查找所有包含href属性的a标签
            items = soup.select('a[href]')
            logger.info(f"尝试所有a[href]标签，匹配到: {len(items)}条")
            if len(items) < 5:
                # 尝试提取所有文本块，然后筛选可能的新闻标题
                all_texts = [text for text in soup.stripped_strings if len(text) > 10]
                logger.info(f"尝试提取所有文本块，匹配到: {len(all_texts)}条")
                if len(all_texts) > 0:
                    # 创建临时的新闻条目
                    for text in all_texts[:20]:  # 取前20个文本块
                        fake_item = BeautifulSoup(f'<div>{text}</div>', 'html.parser')
                        items.append(fake_item)
                else:
                    return news_list

        # 非新闻内容关键词过滤列表
        non_news_keywords = [
            '东方财富', '财经首页', '首页', '导航', '登录', '意见反馈',
            '留言板', '关于我们', '广告服务', '联系我们', '招聘信息',
            '法律声明', '隐私保护', '征稿启事', '友情链接', '网站备案号',
            '沪公网安备', 'jubao@eastmoney.com', '邮箱', '举报', '返回顶部',
            '关闭', '财经', '股票', '基金', '期货', '债券',
            '外汇', '银行', '保险', '理财', '信托', '黄金'
        ]

        # 新闻相关关键词列表（用于提高精准度）
        news_keywords = [
            '经济', '市场', '企业', '公司', '政策', '行业', '数据', '报告', '分析',
            '增长', '下降', '投资', '融资', '上市', '股价', '利润', '营收', '预测',
            '通胀', '利率', '汇率', '贸易', '合作', '竞争', '科技', '创新', '监管'
        ]

        for item in items:
            try:
                # 标题和链接处理
                if hasattr(item, 'name') and item.name == 'a':
                    title_tag = item
                else:
                    title_tag = item.select_one('a') or \
                                item.select_one('h1') or \
                                item.select_one('h2') or \
                                item.select_one('h3') or \
                                item.select_one('h4') or \
                                item.select_one('p') or \
                                item

                if not title_tag or not hasattr(title_tag, 'text'):
                    logger.warning(f"未找到有效标题标签: {item}")
                    continue

                title = title_tag.text.strip()
                if not title:
                    logger.warning(f"标题为空: {item}")
                    continue

                # 过滤非新闻内容
                if any(keyword in title for keyword in non_news_keywords):
                    logger.warning(f"过滤非新闻内容: {title}")
                    continue

                # 过滤过短的标题（可能是非新闻链接）
                if len(title) < 8:
                    logger.warning(f"过滤过短标题: {title}")
                    continue

                # 提高新闻相关性：如果标题包含至少一个新闻关键词，则优先保留
                if not any(keyword in title for keyword in news_keywords):
                    logger.warning(f"标题可能不相关（无新闻关键词）: {title}")
                    # 仍然保留，但标记为低相关性

                # 处理链接
                link = ''
                if hasattr(title_tag, 'get'):
                    link = title_tag.get('href', '').strip()
                elif item.select_one('a'):
                    link = item.select_one('a').get('href', '').strip()

                # 确保链接是完整的
                if link and not link.startswith('http'):
                    if link.startswith('/'):
                        link = 'https://finance.eastmoney.com' + link
                    else:
                        link = 'https://finance.eastmoney.com/' + link
                elif not link:
                    # 如果没有链接，使用东方财富主页
                    link = 'https://finance.eastmoney.com'
                    logger.warning(f"链接为空，使用默认链接: {link}")

                # 时间 - 尝试多种可能的选择器
                time_tag = item.select_one('.time') or \
                           item.select_one('span.time') or \
                           item.select_one('.pubtime') or \
                           item.select_one('.news-time') or \
                           item.parent.select_one('.time') or \
                           item.find_previous_sibling(class_='time') or \
                           item.find_next_sibling(class_='time') or \
                           item.parent.parent.select_one('.time') or \
                           item.find(lambda tag: '发布时间' in tag.text)

                time_str = time_tag.text.strip() if time_tag else ''
                logger.info(f"解析东方财富时间字符串: {time_str}")

                # 处理时间格式
                pub_time = pd.Timestamp.now()
                try:
                    if not time_str:
                        logger.warning("时间字符串为空，使用当前时间")
                    elif '刚刚' in time_str:
                        pub_time = pd.Timestamp.now()
                    elif '今天' in time_str:
                        # 格式如 '今天 09:30'
                        time_part = time_str.replace('今天', '').strip()
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_part}")
                    elif '昨天' in time_str:
                        # 格式如 '昨天 14:45'
                        time_part = time_str.replace('昨天', '').strip()
                        pub_time = pd.Timestamp(f"{(pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')} {time_part}")
                    elif '小时前' in time_str or '分钟前' in time_str or '秒前' in time_str:
                        # 格式如 '1小时前', '30分钟前', '10秒前'
                        num = int(time_str.split('前')[0].replace('小时', '').replace('分钟', '').replace('秒', ''))
                        if '小时前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(hours=num)
                        elif '分钟前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(minutes=num)
                        else:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(seconds=num)
                    elif len(time_str) > 5:
                        # 格式如 '2023-08-12 09:30' 或 '2023/08/12 09:30' 或 '2023年08月12日 09:30'
                        time_str = time_str.replace('/', '-').replace('年', '-').replace('月', '-').replace('日', '')
                        pub_time = pd.Timestamp(time_str)
                    else:
                        # 格式如 '09:30'
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_str}")
                except Exception as e:
                    # 如果解析失败，使用当前时间
                    logger.warning(f"解析东方财富时间失败: {time_str}, 错误: {str(e)}")
                    pub_time = pd.Timestamp.now()

                # 来源
                source = '东方财富'

                # 添加到新闻列表
                news_item = {
                    'title': title,
                    'url': link,
                    'pub_time': pub_time,
                    'source': source
                }
                news_list.append(news_item)
                logger.info(f"成功解析东方财富新闻: {title}")
            except Exception as e:
                logger.error(f"解析东方财富新闻条目失败: {str(e)}", exc_info=True)
                continue

        # 去重（基于标题）
        unique_news = {news['title']: news for news in news_list}.values()
        news_list = list(unique_news)

        logger.info(f"共解析{len(news_list)}条东方财富新闻")
        return news_list

    def _parse_163_news(self, html):
        """解析网易财经新闻"""
        news_list = []
        soup = BeautifulSoup(html, 'html.parser')
        logger.info(f"获取到的网易财经HTML内容前500字符: {html[:500]}")

        # 尝试多种可能的选择器来匹配新闻条目
        selectors = [
            '.newsitem',            # 主要选择器
            '.article',             # 备用选择器1
            '.item',                # 备用选择器2
            '.mod_news'             # 备用选择器3
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            logger.info(f"尝试{selector}选择器，匹配到: {len(items)}条")
            if len(items) > 0:
                break

        if len(items) == 0:
            logger.warning("未匹配到任何网易财经新闻条目，可能页面结构已更改")
            # 尝试直接从body中查找所有a标签作为最后的备选方案
            items = soup.select('body a')
            logger.info(f"尝试body a选择器，匹配到: {len(items)}条")
            if len(items) == 0:
                return news_list

        for item in items:
            try:
                # 标题和链接
                title_tag = item.select_one('h3 a') or \
                            item.select_one('a.title') or \
                            item.select_one('a')

                if not title_tag or not hasattr(title_tag, 'text'):
                    logger.warning(f"未找到有效标题标签: {item}")
                    continue

                title = title_tag.text.strip()
                if not title:
                    logger.warning(f"标题为空: {item}")
                    continue

                link = title_tag.get('href', '').strip()
                if not link:
                    logger.warning(f"链接为空: {item}")
                    continue

                # 确保链接是完整的
                if not link.startswith('http'):
                    if link.startswith('/'):
                        link = 'https://money.163.com' + link
                    else:
                        link = 'https://money.163.com/' + link

                # 时间
                time_tag = item.select_one('.time') or \
                           item.select_one('span.time') or \
                           item.select_one('.post_time') or \
                           item.parent.select_one('.time') or \
                           item.find_previous_sibling(class_='time') or \
                           item.find_next_sibling(class_='time')

                time_str = time_tag.text.strip() if time_tag else ''
                logger.info(f"解析网易财经时间字符串: {time_str}")

                # 处理时间格式
                pub_time = pd.Timestamp.now()
                try:
                    if not time_str:
                        logger.warning("时间字符串为空，使用当前时间")
                    elif '刚刚' in time_str:
                        pub_time = pd.Timestamp.now()
                    elif '今天' in time_str:
                        time_part = time_str.replace('今天', '').strip()
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_part}")
                    elif '昨天' in time_str:
                        time_part = time_str.replace('昨天', '').strip()
                        pub_time = pd.Timestamp(f"{(pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')} {time_part}")
                    elif '小时前' in time_str or '分钟前' in time_str or '秒前' in time_str:
                        num = int(time_str.split('前')[0].replace('小时', '').replace('分钟', '').replace('秒', ''))
                        if '小时前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(hours=num)
                        elif '分钟前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(minutes=num)
                        else:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(seconds=num)
                    elif len(time_str) > 5:
                        time_str = time_str.replace('/', '-')
                        pub_time = pd.Timestamp(time_str)
                    else:
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_str}")
                except Exception as e:
                    logger.warning(f"解析网易财经时间失败: {time_str}, 错误: {str(e)}")
                    pub_time = pd.Timestamp.now()

                # 来源
                source = '网易财经'

                # 添加到新闻列表
                news_item = {
                    'title': title,
                    'url': link,
                    'pub_time': pub_time,
                    'source': source
                }
                news_list.append(news_item)
                logger.info(f"成功解析网易财经新闻: {title}")
            except Exception as e:
                logger.error(f"解析网易财经新闻条目失败: {str(e)}", exc_info=True)
                continue

        logger.info(f"共解析{len(news_list)}条网易财经新闻")
        return news_list

        logger.info(f"共解析{len(news_list)}条网易财经新闻")
        return news_list
        
    def _parse_163_news(self, html):
        """解析网易财经新闻"""
        news_list = []
        soup = BeautifulSoup(html, 'html.parser')
        logger.info(f"获取到的网易财经HTML内容前500字符: {html[:500]}")

        # 尝试多种可能的选择器来匹配新闻条目
        selectors = [
            '.newsitem',            # 主要选择器
            '.article',             # 备用选择器1
            '.item',                # 备用选择器2
            '.mod_news'             # 备用选择器3
        ]

        items = []
        for selector in selectors:
            items = soup.select(selector)
            logger.info(f"尝试{selector}选择器，匹配到: {len(items)}条")
            if len(items) > 0:
                break

        if len(items) == 0:
            logger.warning("未匹配到任何网易财经新闻条目，可能页面结构已更改")
            return news_list

        for item in items:
            try:
                # 标题和链接
                title_tag = item.select_one('h3 a') or \
                            item.select_one('a.title') or \
                            item.select_one('a')

                if not title_tag:
                    logger.warning(f"未找到标题标签: {item}")
                    continue

                title = title_tag.text.strip()
                link = title_tag['href'].strip()

                # 确保链接是完整的
                if not link.startswith('http'):
                    link = 'https://money.163.com' + link

                # 时间
                time_tag = item.select_one('.time') or \
                           item.select_one('span.time') or \
                           item.select_one('.post_time')

                time_str = time_tag.text.strip() if time_tag else ''
                logger.info(f"解析网易财经时间字符串: {time_str}")

                # 处理时间格式
                pub_time = pd.Timestamp.now()
                try:
                    if not time_str:
                        logger.warning("时间字符串为空，使用当前时间")
                    elif '刚刚' in time_str:
                        pub_time = pd.Timestamp.now()
                    elif '今天' in time_str:
                        time_part = time_str.replace('今天', '').strip()
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_part}")
                    elif '昨天' in time_str:
                        time_part = time_str.replace('昨天', '').strip()
                        pub_time = pd.Timestamp(f"{(pd.Timestamp.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')} {time_part}")
                    elif '小时前' in time_str or '分钟前' in time_str or '秒前' in time_str:
                        num = int(time_str.split('前')[0].replace('小时', '').replace('分钟', '').replace('秒', ''))
                        if '小时前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(hours=num)
                        elif '分钟前' in time_str:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(minutes=num)
                        else:
                            pub_time = pd.Timestamp.now() - pd.Timedelta(seconds=num)
                    elif len(time_str) > 5:
                        time_str = time_str.replace('/', '-')
                        pub_time = pd.Timestamp(time_str)
                    else:
                        pub_time = pd.Timestamp(f"{pd.Timestamp.now().strftime('%Y-%m-%d')} {time_str}")
                except Exception as e:
                    logger.warning(f"解析网易财经时间失败: {time_str}, 错误: {str(e)}")
                    pub_time = pd.Timestamp.now()

                # 来源
                source = '网易财经'

                # 添加到新闻列表
                news_item = {
                    'title': title,
                    'url': link,
                    'pub_time': pub_time,
                    'source': source
                }
                news_list.append(news_item)
                logger.info(f"成功解析网易财经新闻: {title}")
            except Exception as e:
                logger.error(f"解析网易财经新闻条目失败: {str(e)}", exc_info=True)
                continue

        logger.info(f"共解析{len(news_list)}条网易财经新闻")
        return news_list