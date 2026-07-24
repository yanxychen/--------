#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值参考案例搜索工具
第一步：搜索功能实现

功能说明:
- 输入目标地址和资产类型
- 根据资产类型确定搜索参数（时间范围、距离范围）
- 搜索淘宝司法拍卖和京东拍卖
- 返回前10个符合条件的案例

技术说明:
- 淘宝司法拍卖(sf.taobao.com)和京东拍卖(auction.jd.com)都有反爬虫保护
- 当前版本实现了完整的搜索逻辑框架
- 实际使用时可能需要Selenium模拟浏览器或使用官方API

使用方法:
    python asset_search.py
    
    或在代码中调用:
    from asset_search import AssetSearchTool
    tool = AssetSearchTool()
    result = tool.search_cases("北京市朝阳区", "住宅")
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
import random
import json


class AssetSearchConfig:
    """资产类型配置类
    
    根据资产类型确定搜索的时间范围和距离范围
    """
    
    CONFIG = {
        "住宅": {
            "time_range": 365,    # 时间范围：1年内
            "distance": 5,        # 距离范围：5公里内
            "description": "住宅类资产，关注近期成交，距离较近"
        },
        "商业": {
            "time_range": 730,    # 时间范围：2年内
            "distance": 10,       # 距离范围：10公里内
            "description": "商业类资产，时间范围放宽，考虑商圈辐射"
        },
        "工业": {
            "time_range": 730,    # 时间范围：2年内
            "distance": 15,       # 距离范围：15公里内
            "description": "工业类资产，关注产业园区，距离范围更大"
        },
        "特殊": {
            "time_range": 1095,   # 时间范围：3年内
            "distance": 20,       # 距离范围：20公里内
            "description": "特殊类资产，案例较少，时间距离范围最大"
        }
    }
    
    @classmethod
    def get_config(cls, asset_type):
        """获取指定资产类型的配置"""
        return cls.CONFIG.get(asset_type, cls.CONFIG["住宅"])
    
    @classmethod
    def get_supported_types(cls):
        """获取支持的资产类型列表"""
        return list(cls.CONFIG.keys())


class BaseSearcher:
    """搜索器基类"""
    
    def __init__(self, name, base_url):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """设置请求头"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        })
    
    def search(self, keyword, max_results=10):
        """
        搜索方法（子类实现）
        
        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
        
        Returns:
            list: 搜索结果列表
        """
        raise NotImplementedError
    
    def _make_request(self, url, params=None, timeout=20):
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            params: 请求参数
            timeout: 超时时间
        
        Returns:
            Response对象或None
        """
        try:
            # 添加随机延迟，模拟人类行为
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(
                url,
                params=params,
                timeout=timeout,
                allow_redirects=True
            )
            
            return response
            
        except requests.exceptions.Timeout:
            print(f"    ⚠ 请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print(f"    ⚠ 连接错误")
            return None
        except requests.exceptions.RequestException as e:
            print(f"    ⚠ 请求异常: {e}")
            return None
    
    def _check_response(self, response):
        """
        检查响应是否有效
        
        Args:
            response: Response对象
        
        Returns:
            bool: 是否有效
        """
        if response is None:
            return False
        
        if response.status_code != 200:
            print(f"    ⚠ HTTP状态码: {response.status_code}")
            return False
        
        # 检查内容长度，过短可能是反爬虫拦截
        content_length = len(response.text)
        if content_length < 100:
            print(f"    ⚠ 响应内容过短 ({content_length}字符)，可能被反爬虫拦截")
            return False
        
        return True


class TaobaoSfSearcher(BaseSearcher):
    """淘宝司法拍卖搜索器"""
    
    def __init__(self):
        super().__init__("淘宝司法拍卖", "https://sf.taobao.com")
        self.search_url = "https://sf.taobao.com/item/search.htm"
    
    def search(self, keyword, max_results=10):
        """
        搜索淘宝司法拍卖
        
        Args:
            keyword: 地址关键词
            max_results: 最大返回结果数
        
        Returns:
            list: 搜索结果列表，每个元素为 {'title', 'link', 'address', 'source'}
        """
        results = []
        
        print(f"\n[{self.name}] 正在搜索...")
        print(f"    关键词: {keyword}")
        print(f"    URL: {self.search_url}?q={quote_plus(keyword)}")
        
        # 发送请求
        response = self._make_request(
            self.search_url,
            params={'q': keyword}
        )
        
        # 检查响应
        if not self._check_response(response):
            print(f"    ℹ️  提示: 淘宝司法拍卖有反爬虫保护")
            print(f"    💡 建议: 使用浏览器手动访问，或配置Selenium")
            return results
        
        print(f"    ✓ 响应成功，长度: {len(response.text)}字符")
        
        # 解析结果
        results = self._parse_results(response.text, max_results)
        
        return results
    
    def _parse_results(self, html, max_results):
        """解析HTML提取结果"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 淘宝司法拍卖的结果通常在特定的容器中
        # 这里是可能的选择器列表，需要根据实际页面结构调整
        selectors = [
            '.item-list .item',
            '.search-result-list .item',
            '.list-container .item',
            '[class*="item-"]',
        ]
        
        items = []
        for selector in selectors:
            items = soup.select(selector)
            if items:
                break
        
        if not items:
            print(f"    ⚠ 未找到结果容器")
            return results
        
        print(f"    找到 {len(items)} 个候选结果")
        
        for item in items[:max_results * 2]:  # 多解析一些，过滤后取需要的数量
            try:
                # 提取标题
                title_elem = item.select_one('a[title]') or item.select_one('a')
                if not title_elem:
                    continue
                
                title = title_elem.get('title', '') or title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                # 过滤无效标题
                if not title or len(title) < 5:
                    continue
                
                # 处理链接
                if link.startswith('//'):
                    link = 'https:' + link
                elif not link.startswith('http'):
                    link = self.base_url + link
                
                # 提取地址信息
                address_elem = item.select_one('.address') or item.select_one('.location')
                address = address_elem.get_text(strip=True) if address_elem else title
                
                results.append({
                    'title': title,
                    'link': link,
                    'address': address,
                    'source': self.name
                })
                
                if len(results) >= max_results:
                    break
                    
            except Exception as e:
                continue
        
        print(f"    ✓ 提取到 {len(results)} 个有效结果")
        return results


class JDAuctionSearcher(BaseSearcher):
    """京东拍卖搜索器"""
    
    def __init__(self):
        super().__init__("京东拍卖", "https://auction.jd.com")
        self.search_url = "https://search.jd.com/Search"
    
    def search(self, keyword, max_results=10):
        """
        搜索京东拍卖
        
        Args:
            keyword: 地址关键词
            max_results: 最大返回结果数
        
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        print(f"\n[{self.name}] 正在搜索...")
        print(f"    关键词: {keyword}")
        print(f"    URL: {self.search_url}?keyword={quote_plus(keyword)}")
        
        # 发送请求
        response = self._make_request(
            self.search_url,
            params={
                'keyword': keyword,
                'enc': 'utf-8',
            }
        )
        
        # 检查响应
        if not self._check_response(response):
            print(f"    ℹ️  提示: 京东有反爬虫保护")
            print(f"    💡 建议: 使用浏览器手动访问，或配置Selenium")
            return results
        
        print(f"    ✓ 响应成功，长度: {len(response.text)}字符")
        
        # 解析结果
        results = self._parse_results(response.text, max_results)
        
        return results
    
    def _parse_results(self, html, max_results):
        """解析HTML提取结果"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # 京东搜索结果的标准选择器
        items = soup.select('.gl-item')
        
        if not items:
            print(f"    ⚠ 未找到结果容器")
            return results
        
        print(f"    找到 {len(items)} 个候选结果")
        
        for item in items[:max_results * 2]:
            try:
                # 提取标题和链接
                title_elem = item.select_one('.p-name a') or item.select_one('.p-name')
                if not title_elem:
                    continue
                
                title = title_elem.get('title', '') or title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                if not title or len(title) < 5:
                    continue
                
                # 处理链接
                if link.startswith('//'):
                    link = 'https:' + link
                elif not link.startswith('http'):
                    link = 'https:' + link
                
                # 提取地址信息
                address = title
                
                results.append({
                    'title': title,
                    'link': link,
                    'address': address,
                    'source': self.name
                })
                
                if len(results) >= max_results:
                    break
                    
            except Exception:
                continue
        
        print(f"    ✓ 提取到 {len(results)} 个有效结果")
        return results


class AssetSearchTool:
    """不良资产案例搜索工具
    
    主搜索类，协调各平台搜索器
    """
    
    def __init__(self):
        """初始化搜索工具"""
        self.taobao_searcher = TaobaoSfSearcher()
        self.jd_searcher = JDAuctionSearcher()
        self.config = AssetSearchConfig
    
    def search_cases(self, address, asset_type="住宅", max_results=10):
        """
        搜索参考案例
        
        Args:
            address: 目标地址
            asset_type: 资产类型（住宅/商业/工业/特殊）
            max_results: 每个平台最大返回结果数
        
        Returns:
            dict: {
                'address': 目标地址,
                'asset_type': 资产类型,
                'config': 搜索配置,
                'total_results': 总结果数,
                'results': 结果列表
            }
        """
        # 验证和获取配置
        if asset_type not in self.config.get_supported_types():
            print(f"⚠ 不支持的资产类型: {asset_type}")
            print(f"支持的类型: {', '.join(self.config.get_supported_types())}")
            asset_type = "住宅"
        
        search_config = self.config.get_config(asset_type)
        
        # 打印搜索信息
        print("\n" + "=" * 80)
        print("🔍 不良资产估值参考案例搜索工具")
        print("=" * 80)
        print(f"📍 目标地址: {address}")
        print(f"🏠 资产类型: {asset_type}")
        print(f"⚙️  搜索参数:")
        print(f"    - 时间范围: {search_config['time_range']} 天 ({search_config['time_range']/365:.1f}年)")
        print(f"    - 距离范围: {search_config['distance']} 公里")
        print(f"    - 说明: {search_config['description']}")
        print("=" * 80)
        
        # 执行搜索
        all_results = []
        
        # 搜索淘宝司法拍卖
        taobao_results = self.taobao_searcher.search(address, max_results)
        all_results.extend(taobao_results)
        
        # 搜索京东拍卖
        jd_results = self.jd_searcher.search(address, max_results)
        all_results.extend(jd_results)
        
        # 去重（基于链接）
        unique_results = []
        seen_links = set()
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        # 构建返回结果
        return {
            'address': address,
            'asset_type': asset_type,
            'config': search_config,
            'total_results': len(unique_results),
            'results': unique_results
        }
    
    def print_results(self, search_result):
        """
        打印搜索结果
        
        Args:
            search_result: search_cases()返回的结果字典
        """
        print("\n" + "=" * 80)
        print("📋 搜索结果")
        print("=" * 80)
        
        results = search_result['results']
        
        if not results:
            print("⚠ 未找到相关案例")
            print("\n可能的原因:")
            print("  1. 网站有反爬虫保护，自动搜索被拦截")
            print("  2. 地址关键词不够准确")
            print("  3. 该地区暂无拍卖案例")
            print("\n💡 下一步建议:")
            print("  1. 手动访问网站:")
            print(f"     - 淘宝司法拍卖: https://sf.taobao.com/")
            print(f"     - 京东拍卖: https://auction.jd.com/")
            print("  2. 使用Selenium模拟浏览器:")
            print("     - 安装: pip install selenium webdriver-manager")
            print("     - 可以模拟真实浏览器，绕过反爬虫")
            print("  3. 尝试不同的地址关键词:")
            print("     - 使用更具体的地址")
            print("     - 或使用行政区划名称")
            return
        
        # 打印每个结果
        for idx, result in enumerate(results, 1):
            print(f"\n【案例 {idx}】来源: {result['source']}")
            
            # 标题（过长截断）
            title = result['title']
            if len(title) > 60:
                title = title[:60] + "..."
            print(f"  📌 标题: {title}")
            
            # 链接
            print(f"  🔗 链接: {result['link']}")
            
            # 地址
            address = result['address']
            if len(address) > 60:
                address = address[:60] + "..."
            print(f"  📍 地址: {address}")
        
        # 总结
        print("\n" + "=" * 80)
        print(f"✅ 共找到 {search_result['total_results']} 个相关案例")
        print("=" * 80)
    
    def save_results(self, search_result, filepath):
        """
        保存结果到JSON文件
        
        Args:
            search_result: 搜索结果
            filepath: 保存路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到: {filepath}")


def interactive_main():
    """交互式主函数"""
    print("\n🔍 不良资产估值参考案例搜索工具")
    print("=" * 80)
    
    # 输入地址
    address = input("\n请输入目标地址: ").strip()
    if not address:
        print("❌ 地址不能为空")
        return
    
    # 选择资产类型
    print("\n资产类型选项:")
    for idx, type_name in enumerate(AssetSearchConfig.get_supported_types(), 1):
        config = AssetSearchConfig.get_config(type_name)
        print(f"  {idx}. {type_name} - {config['description']}")
    
    type_input = input("\n请选择资产类型 (1-4, 默认1): ").strip()
    
    type_map = {'1': '住宅', '2': '商业', '3': '工业', '4': '特殊', '': '住宅'}
    asset_type = type_map.get(type_input, '住宅')
    
    # 执行搜索
    tool = AssetSearchTool()
    result = tool.search_cases(address, asset_type)
    
    # 打印结果
    tool.print_results(result)
    
    # 可选保存
    if result['total_results'] > 0:
        save = input("\n是否保存结果到文件? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"search_result_{address.replace('/', '_')}.json"
            tool.save_results(result, filename)


def demo_main():
    """演示主函数 - 使用预设参数"""
    print("\n🔍 不良资产估值参考案例搜索工具 - 演示模式")
    print("=" * 80)
    
    # 演示参数
    demo_cases = [
        ("北京市朝阳区望京", "住宅"),
        ("上海市浦东新区陆家嘴", "商业"),
    ]
    
    tool = AssetSearchTool()
    
    for address, asset_type in demo_cases:
        print(f"\n{'='*80}")
        print(f"演示案例: {address} ({asset_type})")
        
        result = tool.search_cases(address, asset_type)
        tool.print_results(result)


if __name__ == "__main__":
    import sys
    
    # 根据参数选择运行模式
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo_main()
    else:
        interactive_main()


# ============================================================================
# 使用说明
# ============================================================================
"""
使用方法:

1. 交互式使用:
   python asset_search.py
   
2. 演示模式:
   python asset_search.py --demo

3. 在代码中调用:
   
   from asset_search import AssetSearchTool
   
   tool = AssetSearchTool()
   result = tool.search_cases("北京市朝阳区", "住宅")
   
   # 打印结果
   tool.print_results(result)
   
   # 保存结果
   tool.save_results(result, "output.json")
   
   # 获取结果数据
   for item in result['results']:
       print(item['title'], item['link'])

下一步改进建议:

1. 使用Selenium模拟浏览器:
   - 可以绕过反爬虫检测
   - 可以处理JavaScript渲染的页面
   
2. 添加详情页解析:
   - 提取拍卖价格、拍卖时间等详细信息
   - 提取房屋面积、楼层等具体属性
   
3. 添加地理距离计算:
   - 使用地图API计算实际距离
   - 精确过滤距离范围内的案例
   
4. 添加时间过滤:
   - 根据拍卖时间筛选案例
   - 只保留时间范围内的案例
   
5. 数据持久化:
   - 将搜索结果保存到数据库
   - 历史案例数据积累
"""