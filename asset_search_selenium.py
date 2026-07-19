#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值参考案例搜索工具 - Selenium版
使用Selenium模拟浏览器，绕过反爬虫保护

支持平台:
- 京东拍卖 (pmsearch.jd.com) - 已验证可用
- 淘宝司法拍卖 (sf.taobao.com) - 反爬虫较严，可能需要手动验证
"""

import time
import random
import json
import re
import os
import shutil
import subprocess
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False


class AssetSearchConfig:
    """资产类型配置类
    
    根据资产类型确定搜索的时间范围和距离范围
    """
    
    CONFIG = {
        "住宅": {
            "time_range": 365,
            "distance": 5,
            "description": "住宅类资产，关注近期成交，距离较近"
        },
        "商业": {
            "time_range": 730,
            "distance": 10,
            "description": "商业类资产，时间范围放宽，考虑商圈辐射"
        },
        "工业": {
            "time_range": 730,
            "distance": 15,
            "description": "工业类资产，关注产业园区，距离范围更大"
        },
        "特殊": {
            "time_range": 1095,
            "distance": 20,
            "description": "特殊类资产，案例较少，时间距离范围最大"
        }
    }
    
    @classmethod
    def get_config(cls, asset_type):
        return cls.CONFIG.get(asset_type, cls.CONFIG["住宅"])
    
    @classmethod
    def get_supported_types(cls):
        return list(cls.CONFIG.keys())


def find_chromedriver():
    """查找ChromeDriver路径"""
    common_paths = [
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/usr/lib/chromium-browser/chromedriver',
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    in_path = shutil.which('chromedriver')
    if in_path:
        return in_path
    
    if HAS_WEBDRIVER_MANAGER:
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            if driver_path and os.path.exists(driver_path):
                return driver_path
        except Exception:
            pass
    
    return None


def get_chrome_version():
    """获取Chrome版本"""
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
        if match:
            return match.group(1)
    except Exception:
        pass
    return '120.0.0.0'


class SeleniumBaseSearcher:
    """Selenium搜索器基类
    
    反爬虫优化:
    - 多维度CDP命令隐藏自动化特征
    - 随机User-Agent和浏览器指纹
    - 人类行为模拟（随机滚动、鼠标移动、停留）
    - 随机延迟和请求间隔
    """
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    def __init__(self, name, base_url, headless=True):
        self.name = name
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.wait = None
        self._stealth_enabled = True
    
    def _init_driver(self):
        """初始化Chrome驱动（增强反爬虫）"""
        if self.driver:
            return
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--lang=zh-CN')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--profile-directory=Default')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        user_agent = random.choice(self.USER_AGENTS)
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 1,
            'intl.accept_languages': 'zh-CN,zh;q=0.9,en;q=0.8',
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        elif HAS_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.set_page_load_timeout(60)
        self.driver.set_script_timeout(30)
        
        if self._stealth_enabled:
            self._apply_stealth_settings()
        
        self.wait = WebDriverWait(self.driver, 20)
    
    def _apply_stealth_settings(self):
        """应用Stealth设置，隐藏自动化特征"""
        stealth_script = '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({ state: 'granted' })
                })
            });
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            Object.defineProperty(screen, 'width', { get: () => 1920 });
            Object.defineProperty(screen, 'height', { get: () => 1080 });
            Object.defineProperty(screen, 'availWidth', { get: () => 1920 });
            Object.defineProperty(screen, 'availHeight', { get: () => 1040 });
            Object.defineProperty(screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(screen, 'pixelDepth', { get: () => 24 });
            
            window.outerWidth = 1920;
            window.outerHeight = 1080;
            
            if (window.navigator.__proto__) {
                delete window.navigator.__proto__.webdriver;
            }
            
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };
        '''
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_script
        })
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_;
                delete window.cdc_asdjflasutopfhvcZLmcfl_;
                delete window.cdc_bhKmnxMjvWmeMkKjRkqC_;
            '''
        })
    
    def _random_sleep(self, min_seconds=0.5, max_seconds=2.0):
        """随机睡眠，模拟人类行为"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _human_scroll(self, target_position=None, steps=10):
        """模拟人类滚动行为"""
        current_position = self.driver.execute_script("return window.pageYOffset;")
        
        if target_position is None:
            target_position = self.driver.execute_script(
                "return document.body.scrollHeight * 0.6;"
            )
        
        distance = target_position - current_position
        step_size = distance / steps
        
        for i in range(steps):
            current_position += step_size + random.uniform(-20, 20)
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.05, 0.15))
        
        time.sleep(random.uniform(0.3, 0.8))
    
    def _close_driver(self):
        """关闭驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
            self.wait = None
    
    def _scroll_page(self, scroll_times=3, delay=1.5):
        """滚动页面加载更多内容（人类行为模式）"""
        for i in range(scroll_times):
            self._human_scroll(
                self.driver.execute_script(
                    "return document.body.scrollHeight * " + str(0.5 + i * 0.15)
                )
            )
            time.sleep(delay + random.uniform(-0.5, 0.5))
    
    def _safe_find_all(self, by, value, timeout=10):
        """安全查找所有元素"""
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            return []
    
    def _safe_find_element(self, by, value, timeout=10):
        """安全查找单个元素"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def save_screenshot(self, filepath):
        """保存截图（调试用）"""
        if self.driver:
            try:
                self.driver.save_screenshot(filepath)
            except Exception:
                pass
    
    def save_page_source(self, filepath):
        """保存页面源码（调试用）"""
        if self.driver:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
            except Exception:
                pass
    
    def get_detail_info(self, url):
        """获取详情页信息（子类实现）"""
        raise NotImplementedError
    
    def search(self, keyword, max_results=10):
        """搜索方法（子类实现）"""
        raise NotImplementedError
    
    def cleanup(self):
        """清理资源"""
        self._close_driver()


class JDAuctionSeleniumSearcher(SeleniumBaseSearcher):
    """京东拍卖Selenium搜索器
    
    搜索地址: https://pmsearch.jd.com/search?keyword=xxx
    结果结构: .goods-list-container li -> .goods-container -> .item-name
    """
    
    def __init__(self, headless=True):
        super().__init__("京东拍卖", "https://auction.jd.com", headless)
        self.search_url = "https://pmsearch.jd.com/search"
    
    def search(self, keyword, asset_type="住宅", max_results=10):
        """搜索京东拍卖
        
        Args:
            keyword: 搜索关键词（地址）
            asset_type: 资产类型（住宅/商业/工业/特殊）
            max_results: 最大返回结果数
        
        Returns:
            list: 搜索结果列表
        """
        results = []
        
        # 资产类型映射到京东的分类名
        category_map = {
            "住宅": "住宅用房",
            "商业": "商业用房",
            "工业": "工业用房",
            "特殊": "其他用房",
        }
        jd_category = category_map.get(asset_type, "住宅用房")
        
        print(f"\n[{self.name}] 正在搜索...")
        print(f"    关键词: {keyword}")
        print(f"    资产类型: {asset_type} -> {jd_category}")
        
        try:
            self._init_driver()
            
            url = f"{self.search_url}?keyword={quote_plus(keyword)}"
            print(f"    URL: {url}")
            
            self.driver.get(url)
            
            time.sleep(random.uniform(5, 8))
            
            page_title = self.driver.title
            print(f"    页面标题: {page_title}")
            
            if 'login' in self.driver.current_url.lower() or '登录' in page_title:
                print(f"    ⚠ 跳转到登录页面")
                return results
            
            # 点击资产类型筛选
            print(f"    筛选资产类型: {jd_category}")
            self._select_category(jd_category)
            
            self._scroll_page(scroll_times=4, delay=2)
            time.sleep(3)
            
            results = self._parse_results(max_results)
            
        except Exception as e:
            print(f"    ❌ 搜索异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._close_driver()
        
        return results
    
    def _select_category(self, category_name):
        """选择标的物类型筛选
        
        Args:
            category_name: 类型名称（如: 住宅用房）
        """
        try:
            # 查找分类区域
            category_area = self._safe_find_all(
                By.CSS_SELECTOR, 
                '.s-category span, .s-category a',
                timeout=10
            )
            
            for elem in category_area:
                text = elem.text.strip()
                if text == category_name:
                    # 滚动到可见
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        elem
                    )
                    time.sleep(1)
                    
                    try:
                        elem.click()
                        time.sleep(3)
                        print(f"    ✓ 已筛选: {category_name}")
                        return True
                    except Exception:
                        # 尝试JS点击
                        self.driver.execute_script("arguments[0].click();", elem)
                        time.sleep(3)
                        print(f"    ✓ 已筛选(JS点击): {category_name}")
                        return True
            
            print(f"    ⚠ 未找到筛选选项: {category_name}")
            return False
            
        except Exception as e:
            print(f"    ⚠ 筛选失败: {e}")
            return False
    
    def _parse_results(self, max_results):
        """解析搜索结果"""
        results = []
        
        items = self._safe_find_all(
            By.CSS_SELECTOR, 
            '.goods-list-container li .goods-container',
            timeout=10
        )
        
        if not items:
            items = self._safe_find_all(
                By.CSS_SELECTOR,
                '.goods-list-container li',
                timeout=5
            )
        
        if not items:
            print(f"    ⚠ 未找到结果列表")
            return results
        
        print(f"    找到 {len(items)} 个结果")
        
        for idx, item in enumerate(items[:max_results * 2]):
            try:
                title = ""
                link = ""
                address = ""
                price = ""
                
                if item.tag_name == 'a':
                    link = item.get_attribute('href')
                else:
                    try:
                        link_elem = item.find_element(By.TAG_NAME, 'a')
                        link = link_elem.get_attribute('href')
                    except NoSuchElementException:
                        continue
                
                try:
                    name_elem = item.find_element(By.CSS_SELECTOR, '.item-name')
                    title = name_elem.get_attribute('title') or name_elem.text.strip()
                except NoSuchElementException:
                    continue
                
                try:
                    loc_elem = item.find_element(By.CSS_SELECTOR, '.item-location em')
                    address = loc_elem.text.strip()
                except NoSuchElementException:
                    address = title
                
                try:
                    price_elem = item.find_element(By.CSS_SELECTOR, '.item-price-curr b')
                    price = price_elem.text.strip()
                except NoSuchElementException:
                    pass
                
                if not title or len(title) < 2:
                    continue
                
                if link and link.startswith('//'):
                    link = 'https:' + link
                
                results.append({
                    'title': title,
                    'link': link,
                    'address': address,
                    'price': price,
                    'source': self.name
                })
                
                if len(results) >= max_results:
                    break
                    
            except StaleElementReferenceException:
                continue
            except Exception:
                continue
        
        print(f"    提取到 {len(results)} 个有效结果")
        return results
    
    def get_detail_info(self, url):
        """获取京东拍卖详情页信息
        
        Args:
            url: 详情页URL
        
        Returns:
            dict: 详情信息（面积、楼层、年代、朝向、装修等）
        """
        detail_info = {
            'area': '',
            'floor': '',
            'total_floor': '',
            'year_built': '',
            'orientation': '',
            'decoration': '',
            'property_type': '',
            'full_address': '',
        }
        
        try:
            self._init_driver()
            
            print(f"    正在获取详情页: {url[:60]}...")
            self.driver.get(url)
            time.sleep(random.uniform(5, 8))
            
            self._scroll_page(scroll_times=4, delay=1.5)
            time.sleep(random.uniform(1, 2))
            
            detail_containers = [
                '.pm-parameter',
                '.parameter-box',
                '.detail-parameter',
                '.info-parameter',
                '.goods-parameter',
                '[class*="parameter"]',
                '.pm-detail',
                '.item-detail',
            ]
            
            detail_text = ''
            
            for selector in detail_containers:
                elements = self._safe_find_all(By.CSS_SELECTOR, selector, timeout=5)
                for elem in elements:
                    try:
                        text = elem.text.strip()
                        if len(text) > len(detail_text):
                            detail_text = text
                    except Exception:
                        continue
                if detail_text:
                    break
            
            if not detail_text:
                try:
                    body_elem = self.driver.find_element(By.TAG_NAME, 'body')
                    detail_text = body_elem.text
                except Exception:
                    pass
            
            patterns = {
                'area': [
                    r'建筑面积\s*[:：]?\s*(\d+\.?\d*)\s*(?:㎡|平方米|平|m²)',
                    r'房屋面积\s*[:：]?\s*(\d+\.?\d*)\s*(?:㎡|平方米|平|m²)',
                    r'面积\s*[:：]?\s*(\d+\.?\d*)\s*(?:㎡|平方米|平|m²)',
                    r'(\d+\.?\d*)\s*(?:㎡|平方米)\s*\(?',
                ],
                'floor': [
                    r'所在楼层\s*[:：]?\s*(\d+)\s*层',
                    r'楼层\s*[:：]?\s*(\d+)\s*层',
                    r'第\s*(\d+)\s*层',
                    r'(\d+)\s*层\s*\(',
                ],
                'total_floor': [
                    r'总楼层\s*[:：]?\s*(\d+)\s*层',
                    r'共\s*(\d+)\s*层',
                    r'地上层数\s*[:：]?\s*(\d+)',
                ],
                'year_built': [
                    r'建成年代\s*[:：]?\s*(\d{4})\s*年',
                    r'建筑年代\s*[:：]?\s*(\d{4})\s*年',
                    r'建成时间\s*[:：]?\s*(\d{4})\s*年',
                    r'(\d{4})\s*年建成',
                    r'(\d{4})\s*年建',
                ],
                'orientation': [
                    r'朝向\s*[:：]?\s*([东南西北前后左右南北通透]+)',
                    r'房屋朝向\s*[:：]?\s*([东南西北前后左右南北通透]+)',
                ],
                'decoration': [
                    r'装修情况\s*[:：]?\s*([\u4e00-\u9fa5]{2,6})',
                    r'装修状况\s*[:：]?\s*([\u4e00-\u9fa5]{2,6})',
                    r'装修\s*[:：]?\s*(毛坯|简装|精装|豪装|中装|普通装修|精装修|豪华装修)',
                ],
                'property_type': [
                    r'房屋类型\s*[:：]?\s*([\u4e00-\u9fa5]{2,8})',
                    r'房产类型\s*[:：]?\s*([\u4e00-\u9fa5]{2,8})',
                    r'用途\s*[:：]?\s*([\u4e00-\u9fa5]{2,6})',
                ],
                'full_address': [
                    r'详细地址\s*[:：]?\s*([^\n\r]{5,50})',
                    r'房屋坐落\s*[:：]?\s*([^\n\r]{5,50})',
                    r'标的物位置\s*[:：]?\s*([^\n\r]{5,50})',
                    r'位置\s*[:：]?\s*([^\n\r]{5,50})',
                ],
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, detail_text)
                    if match:
                        value = match.group(1).strip()
                        if len(value) <= 30:
                            detail_info[key] = value
                            break
            
            if not detail_info['full_address']:
                try:
                    addr_selectors = [
                        '.address',
                        '.addr',
                        '.location',
                        '[class*="address"]',
                        '[class*="location"]',
                    ]
                    for sel in addr_selectors:
                        addr_elem = self._safe_find_element(By.CSS_SELECTOR, sel, timeout=3)
                        if addr_elem and addr_elem.text.strip():
                            detail_info['full_address'] = addr_elem.text.strip()
                            break
                except Exception:
                    pass
            
            has_info = any(v for k, v in detail_info.items() if k != 'full_address')
            if has_info:
                print(f"    ✓ 提取到详情信息")
            else:
                print(f"    ⚠ 未提取到有效详情信息")
            
        except Exception as e:
            print(f"    ❌ 获取详情失败: {e}")
            import traceback
            traceback.print_exc()
        
        return detail_info


class TaobaoSfSeleniumSearcher(SeleniumBaseSearcher):
    """淘宝司法拍卖Selenium搜索器
    
    注意: 淘宝司法拍卖反爬虫较严格，采用以下策略:
    1. 先访问首页建立会话
    2. 多次重试机制
    3. 人类行为模拟
    4. 失败时保存截图和页面源码用于分析
    """
    
    def __init__(self, headless=True):
        super().__init__("淘宝司法拍卖", "https://sf.taobao.com", headless)
        self.search_url = "https://sf.taobao.com/item/search.htm"
        self.max_retries = 3
    
    def search(self, keyword, asset_type="住宅", max_results=10):
        """搜索淘宝司法拍卖（通过首页搜索框搜索，绕过反爬虫）
        
        Args:
            keyword: 搜索关键词（地址）
            asset_type: 资产类型（住宅/商业/工业/特殊）
            max_results: 最大返回结果数
        """
        results = []
        
        print(f"\n[{self.name}] 正在搜索...")
        print(f"    关键词: {keyword}")
        print(f"    资产类型: {asset_type}")
        
        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                print(f"    第 {attempt} 次重试...")
                time.sleep(random.uniform(3, 6))
            
            try:
                self._init_driver()
                
                # 先访问首页
                self._visit_homepage()
                
                # 通过首页搜索框搜索
                print(f"    通过首页搜索框搜索...")
                success = self._search_from_homepage(keyword)
                
                if not success:
                    # 兜底：直接访问搜索URL
                    print(f"    搜索框方式失败，尝试直接访问...")
                    url = f"{self.search_url}?q={quote_plus(keyword)}"
                    self.driver.get(url)
                    time.sleep(random.uniform(8, 12))
                
                page_title = self.driver.title
                current_url = self.driver.current_url
                print(f"    页面标题: {page_title}")
                
                if 'login' in current_url.lower() or '验证' in page_title or '安全' in page_title:
                    print(f"    ⚠ 遇到登录或验证码拦截")
                    self._save_debug_info(f'taobao_blocked_attempt{attempt}')
                    if attempt < self.max_retries:
                        self._close_driver()
                        continue
                    else:
                        print(f"    ℹ️  淘宝司法拍卖反爬虫较严格，建议在本地非无头模式下运行")
                        return results
                
                page_len = len(self.driver.page_source)
                if page_len < 2000:
                    print(f"    ⚠ 响应内容过短 ({page_len}字符)，可能被拦截")
                    self._save_debug_info(f'taobao_short_attempt{attempt}')
                    if attempt < self.max_retries:
                        self._close_driver()
                        continue
                    else:
                        return results
                
                # 选择资产类型筛选
                self._select_asset_category(asset_type)
                
                self._scroll_page(scroll_times=5, delay=2)
                time.sleep(random.uniform(2, 4))
                
                results = self._parse_results(max_results)
                
                if results:
                    print(f"    ✓ 成功获取 {len(results)} 个结果")
                    break
                else:
                    print(f"    ⚠ 本次未提取到结果")
                    if attempt < self.max_retries:
                        self._close_driver()
                        continue
                
            except Exception as e:
                print(f"    ❌ 搜索异常: {e}")
                import traceback
                traceback.print_exc()
                self._save_debug_info(f'taobao_error_attempt{attempt}')
                if attempt < self.max_retries:
                    self._close_driver()
                    continue
        
        return results
    
    def _visit_homepage(self):
        """先访问首页建立会话，降低被拦截概率"""
        try:
            print(f"    访问首页建立会话...")
            self.driver.get(self.base_url)
            time.sleep(random.uniform(4, 6))
            
            page_len = len(self.driver.page_source)
            print(f"    首页加载完成 ({page_len}字符)")
            
            self._human_scroll(target_position=300, steps=5)
            time.sleep(random.uniform(1, 2))
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.5, 1))
        except Exception as e:
            print(f"    ⚠ 访问首页失败: {e}")
    
    def _search_from_homepage(self, keyword):
        """从首页搜索框搜索
        
        Returns:
            bool: 是否成功执行搜索
        """
        try:
            search_input = None
            selectors = [
                'input[type="text"]',
                'input[class*="search"]',
                '#q',
                '.search-input',
                'input[placeholder*="搜索"]',
                '.J_SearchInput',
                'input[name="q"]',
            ]
            
            for sel in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if elem.is_displayed() and elem.is_enabled():
                        search_input = elem
                        break
                except Exception:
                    continue
            
            if not search_input:
                print(f"    ⚠ 未找到搜索框")
                return False
            
            search_input.click()
            time.sleep(random.uniform(0.5, 1))
            
            search_input.clear()
            time.sleep(random.uniform(0.3, 0.5))
            
            for char in keyword:
                search_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(random.uniform(0.5, 1))
            search_input.send_keys(Keys.ENTER)
            
            time.sleep(random.uniform(8, 12))
            
            page_len = len(self.driver.page_source)
            if page_len > 2000:
                print(f"    搜索成功 ({page_len}字符)")
                return True
            else:
                print(f"    搜索后页面过短 ({page_len}字符)")
                return False
                
        except Exception as e:
            print(f"    ⚠ 搜索框搜索失败: {e}")
            return False
    
    def _select_asset_category(self, asset_type):
        """选择资产类型筛选
        
        Args:
            asset_type: 资产类型
        """
        try:
            category_map = {
                "住宅": "住宅用房",
                "商业": "商业用房",
                "工业": "工业用房",
                "特殊": "其他用房",
            }
            category_name = category_map.get(asset_type, "住宅用房")
            
            category_links = self._safe_find_all(
                By.CSS_SELECTOR,
                '.category a, .filter-item a, .nav a, [class*="category"] a',
                timeout=5
            )
            
            for link in category_links:
                text = link.text.strip()
                if category_name in text or asset_type in text:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        link
                    )
                    time.sleep(1)
                    try:
                        link.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", link)
                    time.sleep(random.uniform(3, 5))
                    print(f"    ✓ 已筛选: {category_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"    ⚠ 筛选类型失败: {e}")
            return False
    
    def _save_debug_info(self, prefix):
        """保存调试信息（截图和页面源码）"""
        try:
            debug_dir = '/workspace/debug'
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = int(time.time())
            self.save_screenshot(f'{debug_dir}/{prefix}_{timestamp}.png')
            self.save_page_source(f'{debug_dir}/{prefix}_{timestamp}.html')
        except Exception:
            pass
    
    def _parse_results(self, max_results):
        """解析淘宝搜索结果"""
        results = []
        
        selectors = [
            (By.CSS_SELECTOR, '.sf-pai-item-list .pai-item'),
            (By.CSS_SELECTOR, '.sf-item-list .pai-item'),
            (By.CSS_SELECTOR, '.item-list .pai-item'),
            (By.CSS_SELECTOR, 'li.pai-item'),
            (By.CSS_SELECTOR, '.item-list .item'),
            (By.CSS_SELECTOR, '.search-result-list .item'),
        ]
        
        items = []
        for by, selector in selectors:
            items = self._safe_find_all(by, selector, timeout=5)
            if items:
                # 过滤掉没有拍卖链接的item
                valid_items = []
                for item in items:
                    try:
                        link = item.find_element(By.CSS_SELECTOR, 'a[href*="sf_item"], a[href*="sf.taobao.com/item"]')
                        valid_items.append(item)
                    except NoSuchElementException:
                        pass
                if valid_items:
                    items = valid_items
                    print(f"    找到 {len(items)} 个结果 (选择器: {selector})")
                    break
        
        if not items:
            all_links = self._safe_find_all(
                By.CSS_SELECTOR, 
                'a[href*="sf_item"], a[href*="sf.taobao.com/item"]',
                timeout=5
            )
            if all_links:
                print(f"    找到 {len(all_links)} 个拍卖链接")
                for link in all_links[:max_results * 2]:
                    try:
                        href = link.get_attribute('href')
                        full_text = link.text.strip()
                        lines = full_text.split('\n')
                        title = lines[0] if lines else full_text
                        
                        price = ''
                        for line in lines:
                            if '当前价' in line or '起拍价' in line or '¥' in line:
                                price_match = re.search(r'[¥￥]\s*([\d,.]+万?[\d,.]*)', line)
                                if price_match:
                                    price = price_match.group(0)
                                    break
                        
                        if title and len(title) >= 5:
                            if href.startswith('//'):
                                href = 'https:' + href
                            results.append({
                                'title': title,
                                'link': href,
                                'address': title,
                                'price': price,
                                'source': self.name
                            })
                            if len(results) >= max_results:
                                break
                    except Exception:
                        continue
        
        if items:
            for idx, item in enumerate(items[:max_results * 2]):
                try:
                    link_elem = None
                    try:
                        link_elem = item.find_element(By.CSS_SELECTOR, 'a.link-wrap')
                    except NoSuchElementException:
                        try:
                            link_elem = item.find_element(By.CSS_SELECTOR, 'a[href*="sf_item"]')
                        except NoSuchElementException:
                            try:
                                link_elem = item.find_element(By.CSS_SELECTOR, 'a')
                            except NoSuchElementException:
                                continue
                    
                    if not link_elem:
                        continue
                    
                    link = link_elem.get_attribute('href')
                    
                    full_text = link_elem.text.strip()
                    lines = full_text.split('\n')
                    
                    title = ''
                    for line in lines:
                        line = line.strip()
                        if line and '当前价' not in line and '评估价' not in line and '预计' not in line and '起拍价' not in line:
                            title = line
                            break
                    
                    if not title:
                        title = lines[0] if lines else ''
                    
                    if not title or len(title) < 5:
                        continue
                    
                    if link.startswith('//'):
                        link = 'https:' + link
                    elif not link.startswith('http'):
                        link = self.base_url + link
                    
                    address = title
                    
                    price = ''
                    try:
                        price_elem = item.find_element(
                            By.CSS_SELECTOR,
                            '.price, .current-price, .pai-current-price, [class*="current-price"]'
                        )
                        if price_elem and price_elem.text.strip():
                            price = price_elem.text.strip()
                    except NoSuchElementException:
                        for line in lines:
                            if '当前价' in line or '起拍价' in line:
                                price_match = re.search(r'[¥￥]\s*[\d,.]+万?[\d,.]*', line)
                                if price_match:
                                    price = price_match.group(0)
                                    break
                    
                    results.append({
                        'title': title,
                        'link': link,
                        'address': address,
                        'price': price,
                        'source': self.name
                    })
                    
                    if len(results) >= max_results:
                        break
                        
                except StaleElementReferenceException:
                    continue
                except Exception:
                    continue
        
        print(f"    提取到 {len(results)} 个有效结果")
        return results
    
    def get_detail_info(self, url):
        """获取淘宝司法拍卖详情页信息
        
        Args:
            url: 详情页URL
        
        Returns:
            dict: 详情信息
        """
        detail_info = {
            'area': '',
            'floor': '',
            'total_floor': '',
            'year_built': '',
            'orientation': '',
            'decoration': '',
            'property_type': '',
            'full_address': '',
        }
        
        try:
            self._init_driver()
            self.driver.get(url)
            time.sleep(random.uniform(5, 8))
            
            self._scroll_page(scroll_times=3, delay=1.5)
            time.sleep(random.uniform(1, 2))
            
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            
            patterns = {
                'area': [
                    r'建筑面积[:：]\s*(\d+\.?\d*)\s*[平㎡平方米]',
                    r'房屋面积[:：]\s*(\d+\.?\d*)\s*[平㎡平方米]',
                    r'(\d+\.?\d*)\s*[平㎡平方米]',
                ],
                'floor': [
                    r'所在楼层[:：]\s*(\d+)\s*层',
                    r'楼层[:：]\s*(\d+)\s*层',
                    r'第\s*(\d+)\s*层',
                ],
                'total_floor': [
                    r'总楼层[:：]\s*(\d+)\s*层',
                    r'共\s*(\d+)\s*层',
                ],
                'year_built': [
                    r'建成年代[:：]\s*(\d{4})年',
                    r'建筑年代[:：]\s*(\d{4})年',
                    r'(\d{4})年建',
                ],
                'orientation': [
                    r'朝向[:：]\s*([东南西北前后左右]+)',
                    r'房屋朝向[:：]\s*([东南西北前后左右]+)',
                ],
                'decoration': [
                    r'装修情况[:：]\s*([\u4e00-\u9fa5]+)',
                    r'装修状况[:：]\s*([\u4e00-\u9fa5]+)',
                ],
                'property_type': [
                    r'房屋类型[:：]\s*([\u4e00-\u9fa5]+)',
                    r'房产类型[:：]\s*([\u4e00-\u9fa5]+)',
                ],
            }
            
            for key, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, page_text)
                    if match:
                        detail_info[key] = match.group(1)
                        break
            
            try:
                addr_elem = self._safe_find_element(
                    By.CSS_SELECTOR,
                    '.address, .addr, .location, [class*="address"]'
                )
                if addr_elem:
                    detail_info['full_address'] = addr_elem.text.strip()
            except Exception:
                pass
            
        except Exception as e:
            print(f"    ❌ 获取详情失败: {e}")
        
        return detail_info


class SeleniumAssetSearchTool:
    """基于Selenium的不良资产案例搜索工具
    
    主要功能:
    - 输入目标地址和资产类型
    - 根据资产类型确定搜索参数
    - 搜索京东拍卖和淘宝司法拍卖
    - 返回前N个符合条件的案例
    """
    
    def __init__(self, headless=True):
        self.jd_searcher = JDAuctionSeleniumSearcher(headless=headless)
        self.taobao_searcher = TaobaoSfSeleniumSearcher(headless=headless)
        self.config = AssetSearchConfig
        self.headless = headless
    
    def search_cases(self, address, asset_type="住宅", max_results=10, fetch_details=False):
        """搜索参考案例
        
        Args:
            address: 目标地址
            asset_type: 资产类型（住宅/商业/工业/特殊）
            max_results: 每个平台最大返回结果数
            fetch_details: 是否获取详情页信息
        
        Returns:
            dict: 包含搜索配置和结果
        """
        if asset_type not in self.config.get_supported_types():
            print(f"⚠ 不支持的资产类型: {asset_type}")
            asset_type = "住宅"
        
        search_config = self.config.get_config(asset_type)
        
        print("\n" + "=" * 80)
        print("🔍 不良资产估值参考案例搜索工具 (Selenium版)")
        print("=" * 80)
        print(f"📍 目标地址: {address}")
        print(f"🏠 资产类型: {asset_type}")
        print(f"⚙️  搜索参数:")
        print(f"    - 时间范围: {search_config['time_range']} 天 ({search_config['time_range']/365:.1f}年)")
        print(f"    - 距离范围: {search_config['distance']} 公里")
        print(f"    - 说明: {search_config['description']}")
        if fetch_details:
            print(f"    - 详情页提取: 开启")
        print("=" * 80)
        
        all_results = []
        
        jd_results = self.jd_searcher.search(address, asset_type, max_results)
        all_results.extend(jd_results)
        
        taobao_results = self.taobao_searcher.search(address, asset_type, max_results)
        all_results.extend(taobao_results)
        
        unique_results = []
        seen_links = set()
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        if fetch_details and unique_results:
            print(f"\n📄 正在获取详情页信息...")
            print(f"    共 {len(unique_results)} 个案例需要提取详情")
            for idx, result in enumerate(unique_results, 1):
                print(f"\n    [{idx}/{len(unique_results)}] ", end="")
                detail_info = self.get_case_detail(result)
                result['detail'] = detail_info
        
        return {
            'address': address,
            'asset_type': asset_type,
            'config': search_config,
            'total_results': len(unique_results),
            'results': unique_results
        }
    
    def get_case_detail(self, case_data):
        """获取单个案例的详情页信息
        
        Args:
            case_data: 案例数据字典（包含source和link）
        
        Returns:
            dict: 详情信息
        """
        source = case_data.get('source', '')
        link = case_data.get('link', '')
        
        if not link:
            return {}
        
        if '京东' in source:
            return self.jd_searcher.get_detail_info(link)
        elif '淘宝' in source:
            return self.taobao_searcher.get_detail_info(link)
        else:
            return {}
    
    def print_results(self, search_result, show_details=True):
        """打印搜索结果
        
        Args:
            search_result: 搜索结果字典
            show_details: 是否显示详情信息
        """
        print("\n" + "=" * 80)
        print("📋 搜索结果")
        print("=" * 80)
        
        results = search_result['results']
        
        if not results:
            print("⚠ 未找到相关案例")
            print("\n可能的原因:")
            print("  1. 该地区相关拍卖案例较少")
            print("  2. 关键词需要调整（尝试更具体或更宽泛的地址）")
            print("\n建议:")
            print("  - 尝试使用城市名+区名（如: 北京朝阳）")
            print("  - 或使用具体小区/街道名称")
            return
        
        for idx, result in enumerate(results, 1):
            print(f"\n【案例 {idx}】来源: {result['source']}")
            
            title = result['title']
            if len(title) > 70:
                title = title[:70] + "..."
            print(f"  📌 标题: {title}")
            
            print(f"  🔗 链接: {result['link']}")
            
            address = result['address']
            if len(address) > 50:
                address = address[:50] + "..."
            print(f"  📍 地址: {address}")
            
            if result.get('price'):
                print(f"  💰 价格: {result['price']}")
            
            if show_details and result.get('detail'):
                detail = result['detail']
                detail_items = []
                if detail.get('area'):
                    detail_items.append(f"面积: {detail['area']}㎡")
                if detail.get('floor') and detail.get('total_floor'):
                    detail_items.append(f"楼层: {detail['floor']}/{detail['total_floor']}层")
                elif detail.get('floor'):
                    detail_items.append(f"楼层: {detail['floor']}层")
                elif detail.get('total_floor'):
                    detail_items.append(f"总楼层: {detail['total_floor']}层")
                if detail.get('year_built'):
                    detail_items.append(f"年代: {detail['year_built']}年")
                if detail.get('orientation'):
                    detail_items.append(f"朝向: {detail['orientation']}")
                if detail.get('decoration'):
                    detail_items.append(f"装修: {detail['decoration']}")
                if detail.get('property_type'):
                    detail_items.append(f"类型: {detail['property_type']}")
                if detail.get('full_address') and detail['full_address'] != result.get('address'):
                    full_addr = detail['full_address']
                    if len(full_addr) > 50:
                        full_addr = full_addr[:50] + "..."
                    detail_items.append(f"详细地址: {full_addr}")
                
                if detail_items:
                    print(f"  📊 详情: {' | '.join(detail_items)}")
        
        print("\n" + "=" * 80)
        print(f"✅ 共找到 {search_result['total_results']} 个相关案例")
        print("=" * 80)
    
    def save_results(self, search_result, filepath):
        """保存结果到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到: {filepath}")
    
    def cleanup(self):
        """清理所有资源"""
        self.jd_searcher.cleanup()
        self.taobao_searcher.cleanup()


def interactive_main():
    """交互式主函数"""
    print("\n🔍 不良资产估值参考案例搜索工具 (Selenium版)")
    print("=" * 80)
    
    address = input("\n请输入目标地址: ").strip()
    if not address:
        print("❌ 地址不能为空")
        return
    
    print("\n资产类型选项:")
    for idx, type_name in enumerate(AssetSearchConfig.get_supported_types(), 1):
        config = AssetSearchConfig.get_config(type_name)
        print(f"  {idx}. {type_name} - {config['description']}")
    
    type_input = input("\n请选择资产类型 (1-4, 默认1): ").strip()
    
    type_map = {'1': '住宅', '2': '商业', '3': '工业', '4': '特殊', '': '住宅'}
    asset_type = type_map.get(type_input, '住宅')
    
    headless_input = input("是否使用无头模式(不显示浏览器)? (y/n, 默认y): ").strip().lower()
    headless = headless_input != 'n'
    
    tool = SeleniumAssetSearchTool(headless=headless)
    
    try:
        result = tool.search_cases(address, asset_type)
        tool.print_results(result)
        
        if result['total_results'] > 0:
            save = input("\n是否保存结果到文件? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"search_result_{address.replace('/', '_')}.json"
                tool.save_results(result, filename)
    finally:
        tool.cleanup()


def demo_main():
    """演示模式"""
    print("\n🔍 不良资产估值参考案例搜索工具 - Selenium演示模式")
    print("=" * 80)
    
    demo_cases = [
        ("北京朝阳", "住宅"),
    ]
    
    tool = SeleniumAssetSearchTool(headless=True)
    
    try:
        for address, asset_type in demo_cases:
            print(f"\n{'='*80}")
            print(f"演示案例: {address} ({asset_type})")
            
            result = tool.search_cases(address, asset_type)
            tool.print_results(result)
    finally:
        tool.cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo_main()
    else:
        interactive_main()