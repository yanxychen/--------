"""
基于 Playwright 的淘宝拍卖详情页爬取模块
支持登录状态持久化，一次登录后全自动爬取
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext


class TaobaoDetailCrawler:
    def __init__(self, headless: bool = True, storage_path: str = None):
        self.headless = headless
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json'
        )
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def start(self):
        """启动浏览器"""
        if self.browser:
            return
            
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        if os.path.exists(self.storage_path):
            self.context = self.browser.new_context(
                storage_state=self.storage_path,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
        else:
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
        
        self.page = self.context.new_page()
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
    def close(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.browser = None
        self.context = None
        self.page = None
    
    def save_state(self):
        """保存登录状态"""
        if self.context:
            self.context.storage_state(path=self.storage_path)
            print(f"✅ 登录状态已保存到: {self.storage_path}")
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        if not self.page:
            return False
            
        try:
            self.page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=10000)
            self.page.wait_for_timeout(2000)
            
            title = self.page.title()
            print(f"页面标题: {title}")
            
            content = self.page.content()
            if '登录' in title or 'login' in title.lower():
                return False
            if len(content) < 5000:
                return False
            return True
        except Exception as e:
            print(f"检查登录状态失败: {e}")
            return False
    
    def interactive_login(self):
        """交互式登录（需要用户手动扫码或输入账号密码）"""
        print("\n🔐 请在打开的浏览器中登录淘宝账号...")
        print("登录成功后，回到终端按回车键继续...")
        
        self.page.goto('https://login.taobao.com/', timeout=30000)
        input("登录完成后按回车键继续...")
        
        self.save_state()
        print("✅ 登录状态已保存，后续可自动登录！")
    
    def get_detail(self, item_id: str) -> Dict:
        """爬取单个详情页"""
        if not self.page:
            self.start()
            
        result = {
            'item_id': item_id,
            'title': '',
            'link': f"https://sf-item.taobao.com/sf_item/{item_id}.htm",
            'address': '',
            'building_area': 0.0,
            'land_area': 0.0,
            'current_stage': '一拍',
            'start_date': None,
            'deal_date': None,
            'status': '未知',
            'start_price': 0.0,
            'deal_price': 0.0,
            'auction_history': [],
            'success': False,
            'error': ''
        }
        
        try:
            url = f"https://sf-item.taobao.com/sf_item/{item_id}.htm"
            self.page.goto(url, timeout=30000)
            self.page.wait_for_timeout(3000)
            
            content = self.page.content()
            
            title_match = re.search(r'<title>([^<]+)</title>', content)
            if title_match:
                result['title'] = title_match.group(1).strip()
            
            area_patterns = [
                r'建筑面积[：:]\s*([\d.,]+)\s*(?:㎡|平方米|平米|平|m2|M2)',
                r'(\d+[\.,]?\d*)\s*(?:㎡|平方米|平米|平)\s*(?:建面|建筑面积)',
                r'建筑面积.*?(\d+[\.,]?\d*)',
            ]
            for pattern in area_patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        val = float(match.group(1).replace(',', ''))
                        if 5 < val < 100000:
                            result['building_area'] = val
                            break
                    except:
                        pass
            
            addr_patterns = [
                r'坐落[：:]\s*([^<\n]+)',
                r'地址[：:]\s*([^<\n]+)',
                r'位置[：:]\s*([^<\n]+)',
                r'标的物位置[：:]\s*([^<\n]+)',
            ]
            for pattern in addr_patterns:
                match = re.search(pattern, content)
                if match:
                    addr = match.group(1).strip()
                    if len(addr) > 5 and len(addr) < 200:
                        result['address'] = addr
                        break
            
            price_match = re.search(r'起拍价[：:]\s*[￥¥]?\s*([\d,]+(?:\.\d+)?)', content)
            if price_match:
                try:
                    result['start_price'] = float(price_match.group(1).replace(',', ''))
                except:
                    pass
            
            date_patterns = [
                r'开拍时间[：:]\s*([\d\-年月日时分 :/]+)',
                r'拍卖时间[：:]\s*([\d\-年月日时分 :/]+)',
                r'开始时间[：:]\s*([\d\-年月日时分 :/]+)',
                r'变卖时间[：:]\s*([\d\-年月日时分 :/]+)',
                r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})[日号]?\s*([\d:]*\s*)?',
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, content)
                if date_match:
                    date_str = date_match.group(1).strip()
                    try:
                        for fmt in ['%Y年%m月%d日 %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', 
                                    '%Y年%m月%d日', '%Y/%m/%d %H:%M', '%Y/%m/%d',
                                    '%Y-%m-%d']:
                            try:
                                result['start_date'] = datetime.strptime(date_str, fmt)
                                break
                            except:
                                continue
                        if not result['start_date']:
                            try:
                                if '/' in date_str:
                                    parts = date_str.split('/')
                                    if len(parts) >= 3:
                                        result['start_date'] = datetime(
                                            int(parts[0]), int(parts[1]), int(parts[2].split()[0])
                                        )
                            except:
                                pass
                    except:
                        pass
                    if result['start_date']:
                        break
            
            if result['building_area'] > 0 or result['address'] or result['start_price'] > 0:
                result['success'] = True
            else:
                result['error'] = '数据提取失败，请确保已登录淘宝账号'
                
        except Exception as e:
            result['error'] = str(e)
            print(f"爬取详情页失败 {item_id}: {e}")
        
        return result
    
    def get_details_batch(self, item_ids: List[str]) -> Dict[str, Dict]:
        """批量爬取详情页"""
        results = {}
        for i, item_id in enumerate(item_ids):
            print(f"  爬取详情页 {i+1}/{len(item_ids)}: {item_id}")
            detail = self.get_detail(item_id)
            results[item_id] = detail
            if i < len(item_ids) - 1:
                self.page.wait_for_timeout(1000)
        return results


def test_crawler():
    """测试爬虫"""
    crawler = TaobaoDetailCrawler(headless=False)
    
    try:
        crawler.start()
        
        if not crawler.is_logged_in():
            print("⚠️  未检测到登录状态，需要手动登录一次")
            crawler.interactive_login()
        
        print("\n🔍 测试爬取详情页...")
        detail = crawler.get_detail('1057642038615')
        print(f"\n爬取结果:")
        print(f"  success: {detail['success']}")
        print(f"  title: {detail['title'][:60]}")
        print(f"  address: {detail['address']}")
        print(f"  building_area: {detail['building_area']}")
        print(f"  start_price: {detail['start_price']}")
        print(f"  start_date: {detail['start_date']}")
        print(f"  error: {detail['error']}")
        
    finally:
        crawler.close()


if __name__ == '__main__':
    test_crawler()
