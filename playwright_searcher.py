#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于 Playwright 的拍卖搜索器
用真实浏览器访问淘宝/京东拍卖搜索页面，绕过反爬虫
"""
import re
import json
from typing import Dict, List, Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright


class PlaywrightAuctionSearcher:
    """基于 Playwright 的拍卖搜索器 - 真实浏览器渲染"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright = None
        self._browser = None

    def start(self):
        if self._browser:
            return
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )

    def stop(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    def _new_page(self):
        context = self._browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
        )
        page = context.new_page()
        # 反检测
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)
        return page

    def search_taobao(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """用 Playwright 搜索淘宝司法拍卖"""
        self.start()
        page = self._new_page()
        results = []
        try:
            search_url = f"https://sf.taobao.com/item/list.htm?q={quote_plus(keyword)}&_input_charset=utf-8"
            print(f"  [Playwright] 访问淘宝: {search_url}")
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)

            # 尝试多种选择器提取结果
            items = page.query_selector_all('div.item, div.list-item, div[class*="item"], li[class*="item"], table tr')
            print(f"  [Playwright] 淘宝页面找到 {len(items)} 个元素")

            for item in items[:max_results]:
                try:
                    title_el = item.query_selector('a[title], a[class*="title"], h3 a, .title a')
                    link_el = item.query_selector('a[href*="sf_item"], a[href*="item"]')
                    price_el = item.query_selector('[class*="price"], [class*="Price"], span[class*="money"]')
                    area_el = item.query_selector('[class*="area"], [class*="square"], td:nth-child(3)')

                    title = title_el.inner_text().strip() if title_el else ''
                    link = link_el.get_attribute('href') if link_el else ''
                    price = price_el.inner_text().strip() if price_el else ''
                    area_text = area_el.inner_text().strip() if area_el else ''

                    if not title and not link:
                        continue

                    # 提取 item_id
                    item_id = ''
                    id_match = re.search(r'sf_item/(\d+)', link or '')
                    if id_match:
                        item_id = id_match.group(1)

                    if link and not link.startswith('http'):
                        link = 'https:' + link if link.startswith('//') else 'https://sf.taobao.com' + link

                    results.append({
                        'title': title,
                        'item_id': item_id,
                        'link': link or f"https://sf.taobao.com/sf_item/{item_id}.htm",
                        'current_price': price,
                        'area': area_text,
                        'platform': 'taobao',
                        'source': 'playwright',
                    })
                except Exception as e:
                    print(f"    [Playwright] 解析条目出错: {e}")
                    continue

            print(f"  [Playwright] 淘宝搜索完成: {len(results)} 条结果")
        except Exception as e:
            print(f"  [Playwright] 淘宝搜索异常: {e}")
        finally:
            page.context.close()

        return results

    def search_jd(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """用 Playwright 搜索京东拍卖"""
        self.start()
        page = self._new_page()
        results = []
        try:
            search_url = f"https://auction.jd.com/s/list.html?keyword={quote_plus(keyword)}"
            print(f"  [Playwright] 访问京东: {search_url}")
            page.goto(search_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)

            items = page.query_selector_all('div[class*="item"], li[class*="item"], div.goods-item, div.p-item, table tr')
            print(f"  [Playwright] 京东页面找到 {len(items)} 个元素")

            for item in items[:max_results]:
                try:
                    title_el = item.query_selector('a[title], a[class*="title"], .name a, .p-name a')
                    link_el = item.query_selector('a[href*="paimai"], a[href*="item"]')
                    price_el = item.query_selector('[class*="price"], [class*="Price"], i')
                    area_el = item.query_selector('[class*="area"], [class*="square"]')

                    title = title_el.inner_text().strip() if title_el else ''
                    link = link_el.get_attribute('href') if link_el else ''

                    if not title and not link:
                        continue

                    # 提取 item_id
                    item_id = ''
                    id_match = re.search(r'/(\d+)\.html', link or '')
                    if id_match:
                        item_id = id_match.group(1)

                    if link and not link.startswith('http'):
                        link = 'https:' + link if link.startswith('//') else 'https:' + link

                    price = price_el.inner_text().strip() if price_el else ''

                    results.append({
                        'title': title,
                        'item_id': item_id,
                        'link': link or '',
                        'current_price': price,
                        'area': '',
                        'platform': 'jd',
                        'source': 'playwright',
                    })
                except Exception as e:
                    print(f"    [Playwright] 解析条目出错: {e}")
                    continue

            print(f"  [Playwright] 京东搜索完成: {len(results)} 条结果")
        except Exception as e:
            print(f"  [Playwright] 京东搜索异常: {e}")
        finally:
            page.context.close()

        return results

    def search_all(self, keyword: str, platforms: List[str] = ['taobao', 'jd']) -> List[Dict]:
        """搜索所有平台"""
        all_results = []
        for platform in platforms:
            if platform == 'taobao':
                items = self.search_taobao(keyword)
                self._enrich_with_details(items)
                for item in items:
                    normalized = self._normalize(item, 'taobao')
                    all_results.append(normalized)
            elif platform == 'jd':
                items = self.search_jd(keyword)
                for item in items:
                    normalized = self._normalize(item, 'jd')
                    all_results.append(normalized)
        return all_results

    def _enrich_with_details(self, items: List[Dict], max_items: int = 5):
        """打开详情页提取面积、价格等核心数据"""
        for item in items[:max_items]:
            item_id = item.get('item_id', '')
            link = item.get('link', '')
            if not item_id and not link:
                continue
            detail_url = link or f"https://sf-item.taobao.com/sf_item/{item_id}.htm"
            try:
                print(f"  [Playwright] 抓取详情: {detail_url}")
                page = self._new_page()
                page.goto(detail_url, wait_until='networkidle', timeout=25000)
                page.wait_for_timeout(2000)
                
                # 提取页面文本
                text = page.inner_text('body')
                
                # 解析面积
                area_match = re.search(r'建筑面积[：:]\s*([\d,]+\.?\d*)\s*[㎡平方米]', text)
                if not area_match:
                    area_match = re.search(r'([\d,]+\.?\d*)\s*㎡', text)
                if area_match:
                    item['building_area'] = float(area_match.group(1).replace(',', ''))
                
                # 解析价格
                price_match = re.search(r'起拍价[：:]\s*([\d,]+\.?\d*)', text)
                if price_match:
                    item['current_price_yuan'] = float(price_match.group(1).replace(',', ''))
                
                # 解析地址
                addr_match = re.search(r'标的地址[：:]\s*(.+?)(?:\n|$)', text)
                if addr_match:
                    item['address'] = addr_match.group(1).strip()
                
                print(f"    → 面积:{item.get('building_area',0)} ㎡, 价格:{item.get('current_price_yuan',0)} 元")
                page.context.close()
            except Exception as e:
                print(f"    [Playwright] 详情抓取失败: {e}")
                try:
                    page.context.close()
                except:
                    pass

    @staticmethod
    def _normalize(item: Dict, platform: str) -> Dict:
        """标准化输出"""
        building_area = item.get('building_area', 0) or 0
        price_yuan = item.get('current_price_yuan', 0) or 0
        
        return {
            'title': item.get('title', ''),
            'item_id': item.get('item_id', ''),
            'link': item.get('link', ''),
            'current_price': item.get('current_price', ''),
            'current_price_yuan': price_yuan,
            'address': item.get('address', ''),
            'area': item.get('area', ''),
            'building_area': float(building_area) if building_area else 0,
            'status': item.get('status', ''),
            'platform': platform,
        }
