#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值参考案例搜索工具 - API版

使用requests直接调用移动端API，比Selenium更快更稳定

支持平台:
- 京东拍卖 (通过移动端API)
- 淘宝司法拍卖 (通过SSR页面解析)
"""

import requests
import json
import time
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

class UnifiedAuctionSearcher:
    """统一拍卖搜索器 - 基于API的方案"""
    
    def __init__(self, use_proxy=False):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://paimai.jd.com/',
        }
        
        self.use_proxy = use_proxy
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_jd(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """搜索京东拍卖"""
        print(f"🔍 [京东拍卖] 搜索: {keyword}")
        
        try:
            items = self._search_jd_api(keyword, page, page_size)
            
            if not items:
                items = self._search_jd_announcement(keyword, page, page_size)
            
            print(f"✅ [京东拍卖] 找到 {len(items)} 个项目")
            return items
                
        except Exception as e:
            print(f"❌ [京东拍卖] 搜索异常: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _search_jd_api(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """通过京东API搜索"""
        params = {
            'appid': 'paimai',
            'functionId': 'paimai_unifiedSearch',
            'body': json.dumps({
                'keyword': keyword,
                'page': page,
                'pageSize': page_size,
                'sortType': 0,
                'filter': {
                    'auctionStatus': '0,1,2,3',
                    'priceRange': '',
                    'areaRange': ''
                }
            }, ensure_ascii=False),
            't': str(int(time.time() * 1000))
        }
        
        response = self.session.get('https://api.m.jd.com/api', params=params, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get('data', {}).get('list', [])
                
                if items:
                    result = []
                    for item in items:
                        result.append({
                            'title': item.get('title', ''),
                            'item_id': str(item.get('itemId', '')),
                            'link': f"https://paimai.jd.com/{item.get('itemId', '')}",
                            'current_price': item.get('currentPrice', ''),
                            'start_price': item.get('startPrice', ''),
                            'address': item.get('address', ''),
                            'area': item.get('area', ''),
                            'status': item.get('auctionStatus', ''),
                        })
                    return result
            except json.JSONDecodeError:
                pass
        
        return []
    
    def _search_jd_announcement(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """通过京东公告API搜索"""
        params = {
            'appid': 'AuctionTreasure',
            'functionId': 'listAnnouncementByCondi',
            'body': json.dumps({
                'keyword': keyword,
                'page': page,
                'pageSize': page_size
            }, ensure_ascii=False),
            't': str(int(time.time() * 1000))
        }
        
        response = self.session.get('https://api.m.jd.com/api', params=params, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                items = data.get('data', {}).get('data', [])
                
                if items:
                    result = []
                    for item in items:
                        title = item.get('announcementTitle', '')
                        if title:
                            result.append({
                                'title': title,
                                'item_id': str(item.get('businessId', '')),
                                'link': f"https://paimai.jd.com/announcement/detail?id={item.get('businessId', '')}",
                                'address': item.get('address', ''),
                                'status': item.get('announcementStatus', ''),
                            })
                    return result
            except json.JSONDecodeError:
                pass
        
        return []
    
    def _parse_jd_html(self, html: str) -> List[Dict]:
        """解析京东搜索结果HTML"""
        items = []
        
        try:
            link_pattern = r'<a[^>]*?href=\"([^\"]*?/(\d+)[^\"]*)\"[^>]*?>([^<]+)</a>'
            links = re.findall(link_pattern, html)
            
            for link, item_id, text in links[:20]:
                if 'paimai' in link.lower() and len(text.strip()) > 5:
                    if link.startswith('//'):
                        link = 'https:' + link
                    items.append({
                        'title': text.strip(),
                        'item_id': item_id,
                        'link': link,
                    })
        
        except Exception as e:
            print(f"⚠ 京东HTML解析异常: {e}")
        
        return items
    
    def search_taobao(self, keyword: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """搜索淘宝拍卖 - SSR模式"""
        print(f"🔍 [淘宝拍卖] 搜索: {keyword}")
        
        params = {
            'keyword': keyword,
            'page': str(page),
            'pageSize': str(page_size),
            'force_ssr': 'true',
            'x-ssr': 'true',
            'uniapp_page': 'main-search',
            '_': str(int(time.time() * 1000))
        }
        
        try:
            response = self.session.get(
                'https://pages-fast.m.taobao.com/wow/z/app/pm/search-ssr/search',
                params=params,
                timeout=15,
            )
            
            if response.status_code == 200:
                items = self._parse_taobao_ssr(response.text)
                print(f"✅ [淘宝拍卖] 找到 {len(items)} 个项目")
                return items
            else:
                print(f"❌ [淘宝拍卖] 搜索失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ [淘宝拍卖] 搜索异常: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_taobao_ssr(self, html: str) -> List[Dict]:
        """解析淘宝SSR页面"""
        items = []
        
        pattern = r"__ICE_SUSPENSE_LOADER__\.set\('search-list', (.*?)\);"
        matches = re.findall(pattern, html, re.DOTALL)
        
        if matches:
            try:
                data_str = matches[0]
                last_brace = data_str.rfind('}')
                if last_brace > 0:
                    data_str = data_str[:last_brace + 1]
                
                data = json.loads(data_str)
                raw_items = data.get('data', {}).get('items', [])
                
                for raw_item in raw_items:
                    item = {
                        'title': raw_item.get('auctionTitle', ''),
                        'link': f"https://sf-item.taobao.com/sf_item/{raw_item.get('itemId', '')}.htm",
                        'item_id': str(raw_item.get('itemId', '')),
                        'current_price': f"{raw_item.get('price', '')} {raw_item.get('priceUnit', '')}",
                        'start_price': f"{raw_item.get('displayInitialPrice', '')} {raw_item.get('displayInitialPriceUnit', '')}",
                        'status': raw_item.get('status', ''),
                        'biz_type': raw_item.get('bizType', ''),
                        'view_count': raw_item.get('heatCentre', 0),
                        'seller': raw_item.get('shopName', ''),
                    }
                    
                    if item['title']:
                        items.append(item)
                        
            except json.JSONDecodeError as e:
                print(f"⚠ 淘宝JSON解析错误: {e}")
                try:
                    items = self._parse_taobao_fallback(html)
                except Exception:
                    pass
        
        return items
    
    def _parse_taobao_fallback(self, html: str) -> List[Dict]:
        """淘宝JSON解析失败时的备用解析"""
        items = []
        
        item_pattern = r'<div[^>]*?class="[^"]*?auction-item[^"]*?"[^>]*?>.*?</div>'
        item_matches = re.findall(item_pattern, html, re.DOTALL)
        
        for item_html in item_matches:
            item = {}
            
            title_match = re.search(r'<h3[^>]*?>([^<]+)</h3>', item_html)
            if title_match:
                item['title'] = title_match.group(1).strip()
            
            price_match = re.search(r'起拍价[^>]*?>([^<]+)<', item_html)
            if price_match:
                item['start_price'] = price_match.group(1).strip()
            
            addr_match = re.search(r'地址[^>]*?>([^<]+)<', item_html)
            if addr_match:
                item['address'] = addr_match.group(1).strip()
            
            if item.get('title'):
                items.append(item)
        
        return items
    
    def get_taobao_detail(self, item_id: str) -> Dict:
        """
        获取淘宝拍卖详情页数据
        
        Returns:
            {
                'item_id': str,
                'title': str,
                'link': str,
                'address': str,
                'building_area': float,  # 建筑面积（平方米）
                'land_area': float,      # 土地面积（平方米）
                'current_stage': str,    # 当前轮次：一拍/二拍/三拍/变卖
                'start_date': datetime,  # 起拍时间
                'deal_date': datetime,   # 成交时间（如果已成交）
                'status': str,           # 状态：已成交/正在进行/即将开始/流拍/变卖失败
                'start_price': float,    # 当前起拍价（元）
                'deal_price': float,     # 成交价（元，已成交时）
                'auction_history': [     # 历史拍卖记录（按时间顺序：一拍→二拍→变卖）
                    {
                        'stage': '一拍',
                        'start_date': datetime,
                        'start_price': float,
                        'deal_price': float,
                        'status': str,
                    }
                ],
                'success': bool,
                'error': str,
            }
        """
        detail = {
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
            'error': '',
        }

        url = detail['link']

        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                detail['error'] = f"HTTP {response.status_code}"
                return detail

            html = response.text

            # 检查是否需要登录，尝试移动端
            if 'login' in html.lower() and 'redirect' in html.lower() and 'taobao' in html.lower():
                mobile_url = f"https://m.sf-item.taobao.com/sf_item/{item_id}.htm"
                response = self.session.get(mobile_url, timeout=20)
                html = response.text

            # 1. 提取标题
            title_match = re.search(r'<title>([^<]+)</title>', html)
            if title_match:
                detail['title'] = title_match.group(1).strip()

            # 2. 提取建筑面积
            area_patterns = [
                r'建筑面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'房屋面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'总面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'"buildingArea"\s*:\s*"([\d,]+(?:\.\d+)?)"',
                r'建面[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'(\d+[\.,]?\d*)\s*平方米',
                r'(\d+[\.,]?\d*)\s*㎡',
            ]

            for pattern in area_patterns:
                match = re.search(pattern, html)
                if match:
                    try:
                        val = float(match.group(1).replace(',', ''))
                        if val > 0 and val < 100000:
                            detail['building_area'] = val
                            break
                    except:
                        continue

            # 3. 提取土地面积
            land_patterns = [
                r'土地面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'宗地面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
                r'占地面积[：:]\s*([\d,]+(?:\.\d+)?)\s*[㎡平]',
            ]

            for pattern in land_patterns:
                match = re.search(pattern, html)
                if match:
                    try:
                        val = float(match.group(1).replace(',', ''))
                        if val > 0 and val < 1000000:
                            detail['land_area'] = val
                            break
                    except:
                        continue

            # 4. 提取详细地址
            address_patterns = [
                r'标的物所在地[：:]\s*([^<\n]+)',
                r'标的位置[：:]\s*([^<\n]+)',
                r'详细地址[：:]\s*([^<\n]+)',
                r'地址[：:]\s*([^<\n]+)',
                r'"address"\s*:\s*"([^"]+)"',
                r'所在地[：:]\s*([^<\n]+)',
            ]

            for pattern in address_patterns:
                match = re.search(pattern, html)
                if match:
                    addr = match.group(1).strip()
                    addr = re.sub(r'\s+', '', addr)
                    addr = re.sub(r'[，。、；]', '', addr)
                    if len(addr) > 3:
                        detail['address'] = addr
                        break

            # 5. 提取拍卖轮次
            stage_patterns = [
                r'(一拍|二拍|三拍|变卖)',
                r'第([一二三四])拍',
            ]
            for pattern in stage_patterns:
                match = re.search(pattern, html)
                if match:
                    stage = match.group(1)
                    if stage in ['一', '二', '三', '四']:
                        stage_map = {'一': '一拍', '二': '二拍', '三': '三拍', '四': '四拍'}
                        detail['current_stage'] = stage_map[stage]
                    else:
                        detail['current_stage'] = stage
                    break

            # 6. 提取日期（起拍时间、成交时间、结束时间等）
            dates_info = self._extract_dates_from_html(html)

            # 7. 提取价格
            prices_info = self._extract_prices_from_html(html)

            # 8. 提取状态
            status = self._extract_status_from_html(html)
            detail['status'] = status

            # 9. 组装拍卖历史
            auction_history = self._build_auction_history(dates_info, prices_info, detail['current_stage'], status)
            detail['auction_history'] = auction_history

            # 10. 从拍卖历史中回填主要字段
            if auction_history:
                latest = auction_history[-1]
                detail['start_date'] = latest.get('start_date')
                detail['start_price'] = latest.get('start_price', 0)
                if latest.get('deal_price'):
                    detail['deal_price'] = latest['deal_price']
                if latest.get('deal_date'):
                    detail['deal_date'] = latest['deal_date']

            # 确保至少有一个日期
            if not detail['start_date'] and dates_info.get('all_dates'):
                detail['start_date'] = dates_info['all_dates'][0]

            if not detail['start_price'] and prices_info.get('start_price'):
                detail['start_price'] = prices_info['start_price']

            # 判断是否成功
            if detail['title'] or detail['address'] or detail['building_area'] > 0:
                detail['success'] = True
            else:
                detail['error'] = "数据提取失败，可能需要登录"

        except Exception as e:
            detail['error'] = str(e)
            import traceback
            traceback.print_exc()

        return detail

    def _parse_date_str(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None

        date_str = str(date_str).strip()

        # 清理
        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
        date_str = date_str.replace('/', '-').replace('.', '-')

        # 去掉时间部分
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        elif ' ' in date_str:
            date_str = date_str.split(' ')[0]

        # 只取前10个字符（YYYY-MM-DD）
        date_str = date_str[:10]

        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            pass

        return None

    def _parse_price_str(self, price_str: str, unit: str = '') -> float:
        """解析价格字符串，返回元"""
        if not price_str:
            return 0.0

        try:
            price_str = str(price_str).replace(',', '').replace('，', '').strip()
            price = float(price_str)

            # 单位转换
            if '万' in unit or '万元' in str(price_str):
                price = price * 10000
            elif '亿' in unit:
                price = price * 100000000

            return price
        except:
            return 0.0

    def _extract_dates_from_html(self, html: str) -> Dict:
        """从HTML中提取所有日期"""
        result = {
            'start_dates': [],      # 开拍/开始时间
            'end_dates': [],        # 结束/成交时间
            'all_dates': [],        # 所有日期（按时间排序）
        }

        date_patterns = [
            # 带标签的模式
            (r'开拍时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?[\s\d:：]*)', 'start'),
            (r'开始时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?[\s\d:：]*)', 'start'),
            (r'起拍时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?[\s\d:：]*)', 'start'),
            (r'结束时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?[\s\d:：]*)', 'end'),
            (r'成交时间[：:]\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?[\s\d:：]*)', 'end'),
            # JSON字段
            (r'"startTime"\s*:\s*["\']?(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2})', 'start'),
            (r'"endTime"\s*:\s*["\']?(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2})', 'end'),
            (r'"dealTime"\s*:\s*["\']?(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2})', 'end'),
            # 通用日期时间格式
            (r'(\d{4}年\d{1,2}月\d{1,2}日)\s*\d{1,2}[:：]\d{2}', 'unknown'),
            (r'(\d{4}-\d{2}-\d{2})\s+\d{2}:\d{2}:\d{2}', 'unknown'),
        ]

        all_dates = []

        for pattern, date_type in date_patterns:
            matches = re.findall(pattern, html)
            for date_str in matches:
                parsed = self._parse_date_str(date_str)
                if parsed:
                    all_dates.append((parsed, date_type))
                    if date_type == 'start':
                        result['start_dates'].append(parsed)
                    elif date_type == 'end':
                        result['end_dates'].append(parsed)

        # 去重并排序
        all_dates.sort(key=lambda x: x[0])
        unique_dates = []
        seen = set()
        for dt, typ in all_dates:
            key = dt.strftime('%Y%m%d')
            if key not in seen:
                seen.add(key)
                unique_dates.append(dt)

        result['all_dates'] = unique_dates
        result['start_dates'] = sorted(list(set(result['start_dates'])))
        result['end_dates'] = sorted(list(set(result['end_dates'])))

        return result

    def _extract_prices_from_html(self, html: str) -> Dict:
        """从HTML中提取价格信息"""
        result = {
            'start_price': 0.0,      # 起拍价（元）
            'deal_price': 0.0,       # 成交价（元）
            'current_price': 0.0,    # 当前价（元）
            'assessment_price': 0.0, # 评估价（元）
            'stage_prices': {},       # 各轮次价格 {'一拍': 1000000, '二拍': 800000, ...}
        }

        # 起拍价
        start_price_patterns = [
            r'起拍价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)',
            r'起拍价[：:]\s*￥?([\d,]+(?:\.\d+)?)',
            r'"initialPrice"\s*:\s*(\d+\.?\d*)',
            r'"startPrice"\s*:\s*(\d+\.?\d*)',
        ]

        for pattern in start_price_patterns:
            match = re.search(pattern, html)
            if match:
                unit = match.group(2) if match.lastindex and match.lastindex >= 2 else ''
                price = self._parse_price_str(match.group(1), unit)
                if price > 0:
                    result['start_price'] = price
                    break

        # 成交价
        deal_price_patterns = [
            r'成交价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)',
            r'成交价格[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)',
            r'"dealPrice"\s*:\s*(\d+\.?\d*)',
            r'"finalPrice"\s*:\s*(\d+\.?\d*)',
        ]

        for pattern in deal_price_patterns:
            match = re.search(pattern, html)
            if match:
                unit = match.group(2) if match.lastindex and match.lastindex >= 2 else ''
                price = self._parse_price_str(match.group(1), unit)
                if price > 0:
                    result['deal_price'] = price
                    break

        # 当前价
        current_price_patterns = [
            r'当前价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)',
            r'"currentPrice"\s*:\s*(\d+\.?\d*)',
            r'"price"\s*:\s*(\d+\.?\d*)',
        ]

        for pattern in current_price_patterns:
            match = re.search(pattern, html)
            if match:
                unit = match.group(2) if match.lastindex and match.lastindex >= 2 else ''
                price = self._parse_price_str(match.group(1), unit)
                if price > 0:
                    result['current_price'] = price
                    break

        # 各轮次价格
        stage_price_patterns = [
            (r'一拍[^。；\n]*?起?拍价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)', '一拍'),
            (r'二拍[^。；\n]*?起?拍价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)', '二拍'),
            (r'三拍[^。；\n]*?起?拍价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)', '三拍'),
            (r'变卖[^。；\n]*?起?拍价[：:]\s*([\d,]+(?:\.\d+)?)\s*(万元|元|万)', '变卖'),
            (r'第[一二三四]拍[^。；\n]*?([\d,]+(?:\.\d+)?)\s*(万元|元|万)', 'unknown'),
        ]

        for pattern, stage in stage_price_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple):
                    price = self._parse_price_str(match[0], match[1] if len(match) > 1 else '')
                else:
                    price = self._parse_price_str(match, '')
                if price > 0 and stage not in result['stage_prices']:
                    result['stage_prices'][stage] = price

        return result

    def _extract_status_from_html(self, html: str) -> str:
        """从HTML中提取拍卖状态"""
        # 关键词匹配
        if '已成交' in html or '成交成功' in html or 'deal success' in html.lower():
            return '已成交'
        if '流拍' in html or 'failed' in html.lower():
            return '流拍'
        if '变卖失败' in html:
            return '变卖失败'
        if '正在进行' in html or '拍卖中' in html or 'ongoing' in html.lower():
            return '正在进行'
        if '即将开始' in html or '待开拍' in html or 'pending' in html.lower():
            return '即将开始'
        if '已结束' in html or 'end' in html.lower():
            return '已结束'

        # JSON字段
        status_match = re.search(r'"status"\s*:\s*"?(\d+|[\u4e00-\u9fa5]+)"?', html)
        if status_match:
            status_val = status_match.group(1)
            status_map = {
                '0': '即将开始', '1': '正在进行', '2': '已成交',
                '3': '已成交', 'end': '已成交', 'deal': '已成交',
                'fail': '流拍', 'failed': '流拍',
            }
            if status_val in status_map:
                return status_map[status_val]

        return '未知'

    def _build_auction_history(self, dates_info: Dict, prices_info: Dict, 
                                current_stage: str, status: str) -> List[Dict]:
        """构建拍卖历史记录（按时间顺序：一拍→二拍→变卖）"""
        history = []

        all_dates = dates_info.get('all_dates', [])
        start_dates = dates_info.get('start_dates', [])
        end_dates = dates_info.get('end_dates', [])
        stage_prices = prices_info.get('stage_prices', {})

        # 轮次顺序
        stage_order = ['一拍', '二拍', '三拍', '变卖']

        # 根据当前轮次确定有哪些轮次
        stages = []
        for s in stage_order:
            stages.append(s)
            if s == current_stage:
                break

        # 如果只有一个轮次且没有历史价格，就只建一条
        if not stage_prices and len(stages) <= 1:
            record = {
                'stage': current_stage,
                'start_date': start_dates[0] if start_dates else (all_dates[0] if all_dates else None),
                'start_price': prices_info.get('start_price', 0),
                'deal_price': prices_info.get('deal_price', 0),
                'status': status,
            }
            if record['start_price'] > 0 or record['start_date']:
                history.append(record)
            return history

        # 有各轮次价格的情况
        date_idx = 0
        for stage in stages:
            price = stage_prices.get(stage, 0)
            if price == 0 and stage == current_stage:
                price = prices_info.get('start_price', 0)

            start_date = None
            if date_idx < len(start_dates):
                start_date = start_dates[date_idx]
            elif date_idx < len(all_dates):
                start_date = all_dates[date_idx]

            deal_price = 0
            deal_date = None
            record_status = '未知'

            if stage == current_stage:
                # 当前轮次
                record_status = status
                if status == '已成交':
                    deal_price = prices_info.get('deal_price', 0)
                    if end_dates:
                        deal_date = end_dates[-1]
            else:
                # 历史轮次，默认流拍（因为进入下一轮了）
                record_status = '流拍'

            record = {
                'stage': stage,
                'start_date': start_date,
                'start_price': price,
                'deal_price': deal_price,
                'deal_date': deal_date,
                'status': record_status,
            }

            if price > 0 or start_date:
                history.append(record)
                date_idx += 1

        return history
    
    def normalize_item(self, raw_item: Dict, platform: str) -> Dict:
        """标准化拍卖数据"""
        normalized = {
            'platform': platform,
            'source': '京东拍卖' if platform == 'jd' else '淘宝司法拍卖',
            'item_id': raw_item.get('item_id', ''),
            'title': raw_item.get('title', ''),
            'link': raw_item.get('link', ''),
            'address': raw_item.get('address', ''),
            'price': raw_item.get('current_price', '') or raw_item.get('price', ''),
            'detail': {},
        }
        
        return normalized
    
    def search_all(self, keyword: str, platforms: List[str] = ['jd', 'taobao']) -> List[Dict]:
        """搜索所有平台"""
        all_results = []
        
        for platform in platforms:
            if platform == 'jd':
                jd_items = self.search_jd(keyword)
                for item in jd_items:
                    normalized = self.normalize_item(item, 'jd')
                    all_results.append(normalized)
            
            elif platform == 'taobao':
                tb_items = self.search_taobao(keyword)
                for item in tb_items:
                    normalized = self.normalize_item(item, 'taobao')
                    all_results.append(normalized)
        
        print(f"\n📊 总计找到 {len(all_results)} 个项目")
        return all_results
    
    def cleanup(self):
        """清理资源"""
        self.session.close()


class APIAssetSearchTool:
    """基于API的不良资产案例搜索工具"""
    
    def __init__(self):
        self.searcher = UnifiedAuctionSearcher()
        self.config = AssetSearchConfig()
    
    def search_cases(self, address, asset_type="住宅", max_results=10):
        """搜索参考案例"""
        if asset_type not in self.config.get_supported_types():
            print(f"⚠ 不支持的资产类型: {asset_type}")
            asset_type = "住宅"
        
        search_config = self.config.get_config(asset_type)
        
        print("\n" + "=" * 80)
        print("🔍 不良资产估值参考案例搜索工具 (API版)")
        print("=" * 80)
        print(f"📍 目标地址: {address}")
        print(f"🏠 资产类型: {asset_type}")
        print(f"⚙️  搜索参数:")
        print(f"    - 时间范围: {search_config['time_range']} 天 ({search_config['time_range']/365:.1f}年)")
        print(f"    - 距离范围: {search_config['distance']} 公里")
        print(f"    - 说明: {search_config['description']}")
        print("=" * 80)
        
        all_results = self.searcher.search_all(address, platforms=['jd', 'taobao'])
        
        # 去重和限制数量
        unique_results = []
        seen_links = set()
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
                if len(unique_results) >= max_results:
                    break
        
        return {
            'address': address,
            'asset_type': asset_type,
            'config': search_config,
            'total_results': len(unique_results),
            'results': unique_results
        }
    
    def print_results(self, search_result):
        """打印搜索结果"""
        print("\n" + "=" * 80)
        print("📋 搜索结果")
        print("=" * 80)
        
        results = search_result['results']
        
        if not results:
            print("⚠ 未找到相关案例")
            return
        
        for idx, result in enumerate(results, 1):
            print(f"\n【案例 {idx}】来源: {result['source']}")
            
            title = result['title']
            if len(title) > 70:
                title = title[:70] + "..."
            print(f"  📌 标题: {title}")
            
            print(f"  🔗 链接: {result['link']}")
            
            if result.get('address'):
                address = result['address']
                if len(address) > 50:
                    address = address[:50] + "..."
                print(f"  📍 地址: {address}")
            
            if result.get('price'):
                print(f"  💰 价格: {result['price']}")
        
        print("\n" + "=" * 80)
        print(f"✅ 共找到 {search_result['total_results']} 个相关案例")
        print("=" * 80)
    
    def save_results(self, search_result, filepath):
        """保存结果到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(search_result, f, ensure_ascii=False, indent=2)
        print(f"\n✓ 结果已保存到: {filepath}")
    
    def cleanup(self):
        """清理资源"""
        self.searcher.cleanup()


class AssetSearchConfig:
    """资产类型配置类"""
    
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


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: asset_search_api.py <地址> [资产类型]")
        print("资产类型: 住宅/商业/工业/特殊")
        return
    
    address = sys.argv[1]
    asset_type = sys.argv[2] if len(sys.argv) > 2 else "住宅"
    
    tool = APIAssetSearchTool()
    
    try:
        result = tool.search_cases(address, asset_type)
        tool.print_results(result)
        
        if result['total_results'] > 0:
            tool.save_results(result, f"api_search_result_{address}.json")
    finally:
        tool.cleanup()


if __name__ == "__main__":
    main()