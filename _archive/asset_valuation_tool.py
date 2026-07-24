#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值工具 - 核心估值逻辑

功能:
- 多平台案例搜索（京东拍卖、淘宝司法拍卖）
- 高德地图坐标解析和距离计算
- 案例智能评分排序
- 8列标准格式输出
- Excel导出
"""

import requests
import json
import re
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from asset_search_api import UnifiedAuctionSearcher
from case_search_enhanced import EnhancedCaseSearch
from output_formatter import 输出格式化器, Excel生成器
from location_service import LocationService
from price_anomaly_detector import PriceAnomalyDetector


class AssetValuationTool:
    """不良资产估值工具"""
    
    def __init__(self, gaode_api_key: str = ""):
        self.gaode_api_key = gaode_api_key
        self.searcher = UnifiedAuctionSearcher()
        self.enhanced_searcher = EnhancedCaseSearch(gaode_api_key)
        self.格式化器 = 输出格式化器(gaode_api_key)
        self.excel生成器 = Excel生成器(gaode_api_key)
        self.location_service = LocationService(gaode_api_key)
        self.price_detector = PriceAnomalyDetector(threshold_ratio=0.5)
        self._current_mortgage_info: Dict = {}
        self.type_mapping = self._init_type_mapping()
        
    def _init_type_mapping(self) -> Dict:
        """初始化资产类型映射"""
        return {
            "住宅": ["住宅", "别墅", "公寓"],
            "商业": {
                "商铺": ["商铺", "商业用房", "门面"],
                "商场": ["商场", "购物中心", "商业广场"],
                "办公用房": ["办公用房", "写字楼", "办公楼"],
                "酒店": ["酒店", "宾馆", "旅馆"],
                "住宅底商": ["住宅底商", "底商"]
            },
            "工业": {
                "工业房地产": ["工业厂房", "工业用房", "厂房", "仓库"],
                "工业用地": ["工业用地"]
            },
            "土地": {
                "住宅用地": ["住宅用地"],
                "商业用地": ["商业用地"],
                "工业用地": ["工业用地"],
                "综合用地": ["综合用地"]
            },
            "特殊资产": {
                "采矿权": ["采矿权"],
                "林权": ["林权"],
                "海域使用权": ["海域使用权"]
            }
        }
    
    def get_sub_types(self, asset_type: str) -> List[str]:
        """获取资产子类型列表"""
        if asset_type == "住宅":
            return []
        elif asset_type in self.type_mapping:
            return list(self.type_mapping[asset_type].keys())
        return []
    
    def get_all_types(self) -> List[str]:
        """获取所有资产类型"""
        return list(self.type_mapping.keys())
    
    def search_cases(self, address: str, asset_type: str, 
                    sub_type: Optional[str] = None,
                    building_area: Optional[float] = None,
                    land_area: Optional[float] = None,
                    max_results: int = 50) -> Dict:
        """
        搜索参考案例（新版：分层搜索 + 驾车距离 + 多轮次合并 + 抵押物自身优先）
        
        Args:
            address: 目标地址
            asset_type: 资产类型（住宅/商业/工业/土地/特殊资产）
            sub_type: 子类型
            building_area: 建筑面积（平方米）
            land_area: 土地面积（平方米）
            max_results: 最大结果数
        
        Returns:
            搜索结果字典
        """
        print("\n" + "=" * 80)
        print("📊 不良资产估值工具 - 案例搜索（新版）")
        print("=" * 80)
        print(f"📍 目标地址: {address}")
        print(f"🏠 资产类型: {asset_type}" + (f" - {sub_type}" if sub_type else ""))
        if building_area:
            print(f"📐 建筑面积: {building_area} ㎡")
        print("=" * 80)

        # 存储抵押物信息
        self._current_mortgage_info = {
            'address': address,
            'building_area': building_area or 0,
            'land_area': land_area or 0,
            'total_area': (building_area or 0) + (land_area or 0),
            'property_type': asset_type,
            'sub_type': sub_type or '',
            'coordinates': None,
        }

        # ========== 第1步：定位抵押物 ==========
        target_coords = None
        search_keywords = []
        if self.gaode_api_key:
            target_coords = self.location_service.get_coordinates(address)
            if target_coords:
                print(f"✅ 地址定位成功: 经度={target_coords[0]:.6f}, 纬度={target_coords[1]:.6f}")
                self._current_mortgage_info['coordinates'] = target_coords
                # 提取分层搜索关键词
                search_keywords = self.location_service.extract_search_keywords(address, asset_type)
                print(f"🔑 分层搜索关键词: {len(search_keywords)} 个")
                for i, kw in enumerate(search_keywords):
                    print(f"   第{i+1}层: {kw}")
            else:
                print("⚠ 地址定位失败，将使用原始地址搜索")
                search_keywords = [f"{address} {asset_type}"]
        else:
            print("ℹ 未配置高德API Key，将使用原始地址搜索")
            search_keywords = [f"{address} {asset_type}"]

        # ========== 第2步：获取过滤参数 ==========
        distance_config = self._get_distance_config(asset_type)
        time_config = self._get_time_config(asset_type)

        print(f"⏱  首选时间范围: {time_config['primary_days']}天")
        if time_config.get('relaxed_days'):
            print(f"⏱  放宽时间范围: {time_config['relaxed_days']}天")
        print(f"📍 首选距离范围: {distance_config['primary_km']}公里")
        if distance_config.get('relaxed_km'):
            print(f"📍 放宽距离范围: {distance_config['relaxed_km']}公里")

        # ========== 第3步：分层搜索（先淘宝） ==========
        all_raw_cases = []
        seen_item_ids = set()

        print("\n🔍 开始分层搜索（淘宝优先）...")

        for layer_idx, keyword in enumerate(search_keywords):
            print(f"\n📝 第{layer_idx + 1}层搜索: {keyword}")
            
            # 搜索前3页
            for page in range(1, 4):
                tb_cases = self._search_taobao_with_detail(keyword, page=page)
                new_count = 0
                for case in tb_cases:
                    item_id = case.get('item_id', '')
                    if item_id and item_id not in seen_item_ids:
                        seen_item_ids.add(item_id)
                        all_raw_cases.append(case)
                        new_count += 1
                
                print(f"   第{page}页: 新增 {new_count} 个案例")
                
                if len(tb_cases) < 15:
                    break  # 本页结果少，不用翻下一页
            
            # 如果已经有不少案例了，可以考虑提前停止
            # 不过继续搜也没事，后面会过滤

        print(f"\n📊 淘宝搜索总计: {len(all_raw_cases)} 个案例（去重后）")

        # ========== 第4步：如果淘宝案例太少，补充京东 ==========
        if len(all_raw_cases) < 5:
            print("\n🔍 淘宝案例较少，补充京东搜索...")
            for layer_idx, keyword in enumerate(search_keywords):
                if len(all_raw_cases) >= 20:
                    break
                print(f"📝 京东第{layer_idx + 1}层: {keyword}")
                jd_cases = self._search_jd_simple(keyword)
                new_count = 0
                for case in jd_cases:
                    item_id = case.get('item_id', '')
                    if item_id and f"jd_{item_id}" not in seen_item_ids:
                        seen_item_ids.add(f"jd_{item_id}")
                        all_raw_cases.append(case)
                        new_count += 1
                print(f"   新增 {new_count} 个案例")

        print(f"\n📋 原始搜索结果总计: {len(all_raw_cases)} 个案例")

        if not all_raw_cases:
            return {
                "status": "no_cases",
                "message": "未找到任何相关案例",
                "cases": [],
                "raw_cases": [],
                "statistics": {},
                "top3": [],
                "all_cases": [],
            }

        # ========== 第5步：计算驾车距离 ==========
        if target_coords and self.gaode_api_key:
            print("\n🚗 计算驾车距离中...")
            # 第1步：先批量获取所有案例的坐标
            coord_count = 0
            for case in all_raw_cases:
                case_addr = case.get("address", "")
                if not case_addr:
                    case_addr = self._extract_address(case.get("title", ""))
                    case["address"] = case_addr

                if case_addr:
                    case_coords = self.location_service.get_coordinates(case_addr)
                    if case_coords:
                        case["coordinates"] = case_coords
                        coord_count += 1
            
            print(f"   📍 成功获取 {coord_count}/{len(all_raw_cases)} 个案例的坐标")
            
            # 第2步：先用直线距离快速过滤，只对可能符合的案例算驾车距离
            relaxed_km = distance_config.get('relaxed_km', distance_config['primary_km'] * 1.5)
            # 直线距离系数：驾车距离一般是直线的1.1-1.5倍，所以用1.8作为保守过滤阈值
            straight_threshold = relaxed_km * 1.8
            
            candidates = []
            for case in all_raw_cases:
                case_coords = case.get("coordinates")
                if case_coords:
                    straight_dist = self.location_service._haversine_distance(target_coords, case_coords)
                    straight_km = straight_dist / 1000
                    case["straight_distance"] = straight_dist
                    # 先粗略估算驾车距离（直线×1.3）
                    case["driving_distance"] = straight_dist * 1.3
                    case["distance_km"] = round(straight_dist * 1.3 / 1000, 1)
                    # 只有直线距离在阈值内的，才精确计算驾车距离
                    if straight_km <= straight_threshold:
                        candidates.append(case)
            
            print(f"   📏 直线距离过滤后，需精确计算驾车距离: {len(candidates)}/{len(all_raw_cases)} 个")
            
            # 第3步：对候选案例精确计算驾车距离
            driving_count = 0
            for case in candidates:
                case_coords = case.get("coordinates")
                if case_coords:
                    driving_distance = self.location_service.get_driving_distance_meters(
                        target_coords, case_coords
                    )
                    if driving_distance:
                        case["driving_distance"] = driving_distance
                        case["distance_km"] = round(driving_distance / 1000, 1)
                        driving_count += 1
            
            print(f"   ✅ 成功计算 {driving_count} 个案例的精确驾车距离")

        # ========== 第6步：识别抵押物自身拍卖（不受年限限制） ==========
        self_cases = []
        other_cases = []
        
        for case in all_raw_cases:
            is_self = self._is_self_auction_v2(
                address, building_area,
                case.get("address", ""),
                case.get("building_area", 0)
            )
            case["is_self_auction"] = is_self
            if is_self:
                self_cases.append(case)
            else:
                other_cases.append(case)

        print(f"\n🏠 抵押物自身拍卖案例: {len(self_cases)} 个")
        print(f"🏘  其他参考案例: {len(other_cases)} 个")

        # ========== 第7步：合并同一抵押物的多次拍卖 ==========
        print("\n🔄 合并同一抵押物的多次拍卖...")
        merged_self = self._merge_same_property_cases(self_cases)
        merged_others = self._merge_same_property_cases(other_cases)

        print(f"   自身拍卖合并后: {len(merged_self)} 个")
        print(f"   其他案例合并后: {len(merged_others)} 个")

        # ========== 第8步：过滤（时间 + 距离 + 类型） ==========
        print("\n🔍 应用过滤规则...")

        # 自身拍卖案例不受时间限制，但其他案例要过滤
        filtered_others = []
        for case in merged_others:
            # 类型过滤
            if not self._match_asset_type(case, asset_type, sub_type):
                continue

            # 时间过滤（先用首选时间）
            case_date = self._get_case_date(case)
            if case_date:
                days_diff = (datetime.now() - case_date).days
                if days_diff > time_config['primary_days']:
                    continue  # 超过时间范围，先跳过，后面不够再放宽

            # 距离过滤（先用首选距离）
            dist = case.get("driving_distance")
            if dist and dist > distance_config['primary_km'] * 1000:
                continue  # 超过距离范围，先跳过

            filtered_others.append(case)

        print(f"   首选条件过滤后: {len(filtered_others)} 个")

        # 如果不够3个，放宽距离
        if len(filtered_others) < 3 and distance_config.get('relaxed_km'):
            print(f"   案例不足3个，放宽距离到 {distance_config['relaxed_km']}公里...")
            relaxed_by_distance = []
            for case in merged_others:
                if case in filtered_others:
                    continue
                if not self._match_asset_type(case, asset_type, sub_type):
                    continue
                case_date = self._get_case_date(case)
                if case_date:
                    days_diff = (datetime.now() - case_date).days
                    if days_diff > time_config['primary_days']:
                        continue
                dist = case.get("driving_distance")
                if dist and dist <= distance_config['relaxed_km'] * 1000:
                    relaxed_by_distance.append(case)
            
            filtered_others.extend(relaxed_by_distance)
            print(f"   放宽距离后: {len(filtered_others)} 个")

        # 如果还不够3个，放宽时间（如果有放宽时间）
        if len(filtered_others) < 3 and time_config.get('relaxed_days'):
            print(f"   案例仍不足3个，放宽时间到 {time_config['relaxed_days']}天...")
            relaxed_by_time = []
            for case in merged_others:
                if case in filtered_others:
                    continue
                if not self._match_asset_type(case, asset_type, sub_type):
                    continue
                case_date = self._get_case_date(case)
                if case_date:
                    days_diff = (datetime.now() - case_date).days
                    if days_diff > time_config['relaxed_days']:
                        continue
                dist = case.get("driving_distance")
                if dist and dist <= distance_config['relaxed_km'] * 1000:
                    relaxed_by_time.append(case)
            
            filtered_others.extend(relaxed_by_time)
            print(f"   放宽时间后: {len(filtered_others)} 个")

        # ========== 第9步：评分排序 ==========
        print("\n⭐ 计算案例评分...")
        for case in filtered_others:
            score = self._calculate_score_v2(case, asset_type, building_area, land_area)
            case["score"] = score

        # 排序：评分高 → 距离近
        filtered_others.sort(key=lambda x: (-x.get("score", 0), x.get("driving_distance", 999999)))

        # ========== 第9.5步：对Top案例爬详情页补充面积和日期 ==========
        top_cases_for_detail = filtered_others[:20]
        if top_cases_for_detail:
            print(f"\n📄 对Top {len(top_cases_for_detail)} 个案例爬取详情页补充信息...")
            
            need_detail_cases = []
            for case in top_cases_for_detail:
                item_id = case.get('item_id', '')
                platform = case.get('platform', 'taobao')
                if item_id and platform == 'taobao':
                    need_detail = (case.get('building_area', 0) == 0 or 
                                   case.get('start_date') is None or
                                   not case.get('address', ''))
                    if need_detail:
                        need_detail_cases.append(case)
            
            if need_detail_cases:
                print(f"   需要补充信息的案例: {len(need_detail_cases)} 个")
                detail_count = self._enrich_cases_with_playwright(need_detail_cases)
                print(f"   ✅ 成功补充 {detail_count} 个案例的详情信息")
            else:
                print(f"   所有案例信息完整，无需补充")

        # ========== 第10步：价格异常检测 ==========
        print("\n💰 价格异常检测...")
        all_valid_cases = merged_self + filtered_others
        # 计算单价
        unit_prices = []
        for case in all_valid_cases:
            market_value = self._get_market_value(case)  # 万元
            area = case.get("building_area", 0)
            if market_value > 0 and area > 0:
                unit_price = market_value * 10000 / area
                case["unit_price"] = unit_price
                unit_prices.append(unit_price)
            else:
                case["unit_price"] = 0
                unit_prices.append(0)

        # 标记异常
        all_valid_cases = self.price_detector.mark_cases(all_valid_cases, 'unit_price')
        high_count = sum(1 for c in all_valid_cases if c.get('price_anomaly') == 'high')
        low_count = sum(1 for c in all_valid_cases if c.get('price_anomaly') == 'low')
        print(f"   价格偏高: {high_count} 个，价格偏低: {low_count} 个")

        # ========== 第11步：格式化输出 ==========
        print("\n📋 格式化输出...")

        # 全部案例（自身拍卖 + 其他，按时间排序）
        all_cases_formatted = []
        for idx, case in enumerate(all_valid_cases, 1):
            formatted = self._format_case_output_v2(idx, case, asset_type, sub_type)
            all_cases_formatted.append(formatted)

        # 按时间由近到远排序（全部案例的默认排序）
        def _get_sort_date(x):
            d = x.get('start_date')
            if d is None:
                return ''
            if hasattr(d, 'strftime'):
                return d.strftime('%Y-%m-%d')
            return str(d)
        
        all_cases_formatted.sort(
            key=_get_sort_date,
            reverse=True
        )

        # Top3 精选（自身拍卖在前，然后按评分）
        top3_cases = []
        self_formatted = [c for c in all_cases_formatted if c.get('is_self_auction')]
        other_formatted = [c for c in all_cases_formatted if not c.get('is_self_auction')]
        
        # 其他按评分排（处理 None 的情况）
        other_formatted.sort(key=lambda x: -(x.get('score') or 0))
        
        top3_cases = self_formatted + other_formatted
        top3_cases = top3_cases[:3]

        result = {
            "status": "success",
            "cases": top3_cases,  # 兼容旧接口，返回top3
            "raw_cases": all_valid_cases,
            "statistics": self._calculate_statistics_v2(all_cases_formatted, asset_type),
            "top3": top3_cases,
            "all_cases": all_cases_formatted,
            "self_auction_count": len(merged_self),
            "total_count": len(all_valid_cases),
        }

        print(f"\n✅ 搜索完成")
        print(f"   抵押物自身拍卖: {len(merged_self)} 个")
        print(f"   参考案例总数: {len(all_valid_cases)} 个")
        print(f"   Top3精选: {len(top3_cases)} 个")

        return result
    
    # ========== 新版辅助方法 ==========
    
    def _get_distance_config(self, asset_type: str) -> Dict:
        """获取距离配置"""
        configs = {
            "住宅": {"primary_km": 3, "relaxed_km": 5},
            "商业": {"primary_km": 3, "relaxed_km": 5},
            "工业": {"primary_km": 10},
            "土地": {"primary_km": 10},
            "特殊资产": {"primary_km": 10},
        }
        return configs.get(asset_type, configs["住宅"])
    
    def _get_time_config(self, asset_type: str) -> Dict:
        """获取时间配置 - 参考案例限制在1~2年内"""
        configs = {
            "住宅": {"primary_days": 730},
            "商业": {"primary_days": 730},
            "工业": {"primary_days": 730},
            "土地": {"primary_days": 730},
            "特殊资产": {"primary_days": 730},
        }
        return configs.get(asset_type, configs["住宅"])
    
    def _search_taobao_with_detail(self, keyword: str, page: int = 1) -> List[Dict]:
        """搜索淘宝（仅列表页数据，快速返回）"""
        cases = []
        tb_items = self.searcher.search_taobao(keyword, page=page, page_size=20)
        
        for item in tb_items:
            case = self._convert_detail_to_case(item, None, 'taobao')
            if case:
                cases.append(case)
        
        return cases
    
    def _search_jd_simple(self, keyword: str, page: int = 1) -> List[Dict]:
        """搜索京东（简单版，暂不爬详情页）"""
        cases = []
        jd_items = self.searcher.search_jd(keyword, page=page, page_size=20)
        
        for item in jd_items:
            case = {
                'item_id': item.get('item_id', ''),
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'platform': 'jd',
                'source': '京东拍卖',
                'address': item.get('address', ''),
                'building_area': 0,
                'land_area': 0,
                'start_price': 0,
                'deal_price': 0,
                'start_date': None,
                'current_stage': '一拍',
                'status': item.get('status', ''),
                'auction_history': [],
                'is_self_auction': False,
                'price_anomaly': None,
            }
            
            # 尝试解析价格
            try:
                price_str = str(item.get('start_price', '')).replace(',', '')
                if '万' in price_str:
                    case['start_price'] = float(price_str.replace('万', '')) * 10000
                elif price_str:
                    case['start_price'] = float(price_str)
            except:
                pass
            
            # 从标题提取面积
            title = item.get('title', '')
            area_match = re.search(r'(\d+[\.,]?\d*)\s*(?:㎡|平方米|平)', title)
            if area_match:
                try:
                    case['building_area'] = float(area_match.group(1).replace(',', ''))
                except:
                    pass
            
            if case['title']:
                cases.append(case)
        
        return cases
    
    def _convert_detail_to_case(self, item: Dict, detail: Optional[Dict], platform: str) -> Optional[Dict]:
        """将详情页数据转换为案例格式"""
        title = item.get('title', '')
        if not title and detail:
            title = detail.get('title', '')
        if not title:
            return None
        
        case = {
            'item_id': item.get('item_id', detail.get('item_id', '') if detail else ''),
            'title': title,
            'link': item.get('link', detail.get('link', '') if detail else ''),
            'platform': platform,
            'source': '淘宝司法拍卖' if platform == 'taobao' else '京东拍卖',
            'address': '',
            'building_area': 0,
            'land_area': 0,
            'start_price': 0,
            'deal_price': 0,
            'start_date': None,
            'current_stage': '一拍',
            'status': '未知',
            'auction_history': [],
            'is_self_auction': False,
            'price_anomaly': None,
            'unit_price': 0,
            'driving_distance': None,
            'distance_km': None,
            'coordinates': None,
            'score': 0,
        }
        
        # 先从列表item提取基础数据（即使详情页失败也有数据）
        # 提取起拍价
        item_start_price = item.get('start_price', '') or item.get('current_price', '')
        if item_start_price:
            price_val = self._parse_price_str(item_start_price)
            if price_val > 0:
                case['start_price'] = price_val
        
        # 提取状态
        item_status = item.get('status', '')
        if item_status:
            case['status'] = self._normalize_status(item_status)
        
        # 提取拍卖轮次（从标题）
        stage_match = re.search(r'(一拍|二拍|三拍|变卖)', title)
        if stage_match:
            case['current_stage'] = stage_match.group(1)
        
        if detail and detail.get('success'):
            # 详情页成功的话，用详情页的数据覆盖（更准确）
            if detail.get('address'):
                case['address'] = detail.get('address', '')
            if detail.get('building_area', 0) > 0:
                case['building_area'] = detail.get('building_area', 0)
            if detail.get('land_area', 0) > 0:
                case['land_area'] = detail.get('land_area', 0)
            if detail.get('start_price', 0) > 0:
                case['start_price'] = detail.get('start_price', 0)
            if detail.get('deal_price', 0) > 0:
                case['deal_price'] = detail.get('deal_price', 0)
            if detail.get('start_date'):
                case['start_date'] = detail.get('start_date')
            if detail.get('current_stage'):
                case['current_stage'] = detail.get('current_stage', '一拍')
            if detail.get('status') and detail.get('status') != '未知':
                case['status'] = detail.get('status', '未知')
            if detail.get('auction_history'):
                case['auction_history'] = detail.get('auction_history', [])
        
        # 如果详情页没拿到地址，从标题提取
        if not case['address']:
            case['address'] = self._extract_address(title)
        
        # 如果详情页没拿到面积，从标题提取
        if case['building_area'] == 0:
            area_match = re.search(r'(\d+[\.,]?\d*)\s*(?:㎡|平方米|平米|平|m2|M2|㎡|建面|建筑面积)', title)
            if area_match:
                try:
                    case['building_area'] = float(area_match.group(1).replace(',', ''))
                except:
                    pass
        
        # 如果还是没拿到，尝试从标题中找 "XX平方" 或 "XX㎡" 等其他格式
        if case['building_area'] == 0:
            area_match2 = re.search(r'(\d+[\.,]?\d*)\s*(?:平方|方)', title)
            if area_match2:
                try:
                    val = float(area_match2.group(1).replace(',', ''))
                    if val > 5 and val < 10000:  # 合理范围过滤
                        case['building_area'] = val
                except:
                    pass
        
        # 如果没有拍卖历史，手动建一条
        if not case['auction_history']:
            case['auction_history'] = [{
                'stage': case['current_stage'],
                'start_date': case['start_date'],
                'start_price': case['start_price'],
                'deal_price': case['deal_price'],
                'status': case['status'],
            }]
        
        return case
    
    def _parse_price_str(self, price_str: str) -> float:
        """解析价格字符串，返回元"""
        if not price_str:
            return 0.0
        try:
            price_str = str(price_str).replace(',', '').replace('，', '').strip()
            num_match = re.search(r'(\d+[\.,]?\d*)', price_str)
            if not num_match:
                return 0.0
            price = float(num_match.group(1).replace(',', ''))
            if '万' in price_str:
                price = price * 10000
            elif '亿' in price_str:
                price = price * 100000000
            return price
        except:
            return 0.0
    
    def _normalize_status(self, status: str) -> str:
        """标准化状态文本"""
        if not status:
            return '未知'
        status = str(status).strip().lower()
        
        status_map = {
            'ing': '正在进行',
            'before': '即将开始',
            'done': '已结束',
            'success': '已成交',
            'failed': '流拍',
            'aborted': '中止',
            'revoked': '撤回',
            'end': '已结束',
            'inviting': '招商中',
            'delay': '已暂缓',
        }
        if status in status_map:
            return status_map[status]
        
        if '成交' in status or '已成交' in status:
            return '已成交'
        if '流拍' in status:
            return '流拍'
        if '进行中' in status or '正在' in status:
            return '正在进行'
        if '即将开始' in status or '待开始' in status:
            return '即将开始'
        if '变卖' in status:
            return '变卖中'
        return status[:10] if len(status) > 10 else status
    
    def _is_self_auction_v2(self, target_address: str, target_area: Optional[float],
                            case_address: str, case_area: float) -> bool:
        """判断是否抵押物自身拍卖（地址 + 面积双重判断）"""
        if not target_address or not case_address:
            return False
        
        # 地址判断
        def clean_addr(addr):
            return re.sub(r'[^\u4e00-\u9fa5\d]', '', addr)
        
        target_clean = clean_addr(target_address)
        case_clean = clean_addr(case_address)
        
        addr_match = False
        if target_clean == case_clean:
            addr_match = True
        elif len(target_clean) > 5 and target_clean in case_clean:
            addr_match = True
        elif len(case_clean) > 5 and case_clean in target_clean:
            addr_match = True
        
        # 如果地址完全匹配，直接算
        if addr_match and not target_area:
            return True
        
        # 面积判断（±10%以内）
        if target_area and case_area > 0:
            area_diff = abs(target_area - case_area) / target_area
            if area_diff <= 0.1 and addr_match:
                return True
        
        # 用高德坐标判断
        if self.gaode_api_key and addr_match:
            is_same = self.location_service.is_same_address(target_address, case_address)
            if is_same:
                return True
        
        return False
    
    def _merge_same_property_cases(self, cases: List[Dict]) -> List[Dict]:
        """合并同一抵押物的多次拍卖"""
        if not cases:
            return []
        
        # 按地址+面积分组
        groups = {}
        
        for case in cases:
            addr = case.get('address', '')
            area = case.get('building_area', 0)
            
            # 生成分组key
            key = None
            for existing_key in groups.keys():
                existing_addr, existing_area = existing_key
                # 地址相似且面积相近
                if self._is_same_property(addr, area, existing_addr, existing_area):
                    key = existing_key
                    break
            
            if key is None:
                key = (addr, area)
                groups[key] = []
            
            groups[key].append(case)
        
        # 合并每组
        merged = []
        for key, group_cases in groups.items():
            if len(group_cases) == 1:
                merged.append(group_cases[0])
                continue
            
            # 按时间排序（从早到晚）
            dated_cases = []
            for c in group_cases:
                date = c.get('start_date')
                if date:
                    dated_cases.append((date, c))
                else:
                    dated_cases.append((datetime.min, c))
            
            dated_cases.sort(key=lambda x: x[0])
            
            # 取最新的作为主案例
            main_case = dated_cases[-1][1].copy()
            
            # 收集所有拍卖历史
            all_history = []
            seen_stages = set()
            
            for _, c in dated_cases:
                history = c.get('auction_history', [])
                for h in history:
                    stage = h.get('stage', '')
                    if stage not in seen_stages:
                        seen_stages.add(stage)
                        all_history.append(h)
            
            # 按轮次顺序排序
            stage_order = {'一拍': 1, '二拍': 2, '三拍': 3, '变卖': 4}
            all_history.sort(key=lambda x: stage_order.get(x.get('stage', ''), 99))
            
            main_case['auction_history'] = all_history
            
            # 更新当前阶段为最新的
            if all_history:
                main_case['current_stage'] = all_history[-1].get('stage', main_case['current_stage'])
                main_case['status'] = all_history[-1].get('status', main_case['status'])
            
            merged.append(main_case)
        
        return merged
    
    def _is_same_property(self, addr1: str, area1: float, addr2: str, area2: float) -> bool:
        """判断两个案例是否是同一个抵押物"""
        if not addr1 or not addr2:
            return False
        
        def clean(a):
            return re.sub(r'[^\u4e00-\u9fa5\d]', '', a)
        
        c1 = clean(addr1)
        c2 = clean(addr2)
        
        if not c1 or not c2:
            return False
        
        if c1 == c2:
            return True
        
        # 互相包含且长度够长
        if len(c1) > 8 and c1 in c2:
            return True
        if len(c2) > 8 and c2 in c1:
            return True
        
        # 面积都有的话，面积也要接近
        if area1 > 0 and area2 > 0:
            area_diff = abs(area1 - area2) / max(area1, area2)
            if area_diff <= 0.1:
                # 面积接近时，地址只要有一定相似度就算
                common_len = 0
                for i in range(min(len(c1), len(c2))):
                    if c1[i] == c2[i]:
                        common_len += 1
                    else:
                        break
                if common_len >= 6:
                    return True
        
        return False
    
    def _match_asset_type(self, case: Dict, asset_type: str, sub_type: Optional[str]) -> bool:
        """判断案例是否匹配资产类型"""
        title = case.get('title', '')
        if not title:
            return True  # 没标题的先保留，后面再过滤
        
        type_keywords = {
            "住宅": ["住宅", "公寓", "别墅", "小区", "花园", "家园", "苑", "府", "邸", "城", "庭"],
            "商业": ["商业", "商铺", "门面", "店铺", "商场", "购物中心", "写字楼", "办公", "酒店", "宾馆"],
            "工业": ["工业", "厂房", "仓库", "厂区", "工业园", "产业园"],
            "土地": ["土地", "用地", "地块", "宗地"],
        }
        
        keywords = type_keywords.get(asset_type, [])
        if not keywords:
            return True
        
        # 检查标题里是否有对应类型的关键词
        for kw in keywords:
            if kw in title:
                return True
        
        # 如果有建筑面积且是住宅类描述，也算住宅
        if asset_type == "住宅" and case.get('building_area', 0) > 0:
            for kw in ["室", "厅", "卧", "号", "栋"]:
                if kw in title:
                    return True
        
        return False
    
    def _get_case_date(self, case: Dict) -> Optional[datetime]:
        """获取案例的日期（起拍时间）"""
        # 优先从拍卖历史里找最早的
        history = case.get('auction_history', [])
        if history:
            for h in history:
                d = h.get('start_date')
                if d and isinstance(d, datetime):
                    return d
        
        # 其次用case的start_date
        d = case.get('start_date')
        if d and isinstance(d, datetime):
            return d
        
        return None
    
    def _calculate_score_v2(self, case: Dict, asset_type: str,
                             building_area: Optional[float],
                             land_area: Optional[float]) -> float:
        """计算案例评分（新版：距离50 + 面积30 + 时间20 = 100分）"""
        score = 0.0
        
        # 1. 距离分（50分）
        distance_config = self._get_distance_config(asset_type)
        primary_km = distance_config['primary_km']
        dist = case.get("driving_distance")
        
        if dist is not None and dist > 0:
            dist_km = dist / 1000
            if dist_km <= 0.5:
                score += 50
            elif dist_km <= 1:
                score += 45
            elif dist_km <= 2:
                score += 37.5
            elif dist_km <= primary_km:
                score += 30
            elif dist_km <= distance_config.get('relaxed_km', primary_km):
                score += 15
            else:
                score += 5
        else:
            score += 20  # 没有距离数据的给基础分
        
        # 2. 面积分（30分）
        target_area = building_area or land_area or 0
        case_area = case.get("building_area", 0) or case.get("land_area", 0)
        
        if target_area > 0 and case_area > 0:
            area_diff = abs(target_area - case_area) / target_area
            if area_diff <= 0.1:
                score += 30
            elif area_diff <= 0.2:
                score += 25.5
            elif area_diff <= 0.3:
                score += 21
            elif area_diff <= 0.5:
                score += 15
            else:
                score += 6
        else:
            score += 15  # 没有面积数据的给基础分
        
        # 3. 时间分（20分）
        case_date = self._get_case_date(case)
        if case_date and isinstance(case_date, datetime):
            days_diff = (datetime.now() - case_date).days
            if days_diff <= 90:
                score += 20
            elif days_diff <= 180:
                score += 18
            elif days_diff <= 365:
                score += 15
            elif days_diff <= 730:
                score += 10
            else:
                score += 3
        else:
            score += 10  # 没有时间数据的给基础分
        
        return round(score, 1)
    
    def _get_market_value(self, case: Dict) -> float:
        """获取市场价值（万元）
        - 已成交取成交价
        - 未成交取最新起拍价
        """
        history = case.get('auction_history', [])
        
        if history:
            # 取最新的一条
            latest = history[-1]
            status = latest.get('status', '')
            if status == '已成交' and latest.get('deal_price', 0) > 0:
                return latest['deal_price'] / 10000  # 转万元
            elif latest.get('start_price', 0) > 0:
                return latest['start_price'] / 10000
        
        # 兜底
        if case.get('deal_price', 0) > 0 and case.get('status') == '已成交':
            return case['deal_price'] / 10000
        if case.get('start_price', 0) > 0:
            return case['start_price'] / 10000
        
        return 0
    
    def _format_case_output_v2(self, index: int, case: Dict, 
                                asset_type: str, sub_type: Optional[str]) -> Dict:
        """格式化案例输出（新版8列格式）"""
        display_type = self._get_display_type(case, asset_type, sub_type)
        
        address = case.get("address", "")
        title = case.get("title", "")
        
        cleaned_address = address if address else self._extract_clean_address(title)
        display_address = cleaned_address if cleaned_address else "点击查看详情"
        
        market_value = self._get_market_value(case)
        building_area = case.get("building_area", 0)
        land_area = case.get("land_area", 0)
        
        building_area_str = f"{building_area:,.2f}" if building_area > 0 else "待确认"
        land_area_str = f"{land_area:,.2f}" if land_area > 0 else "不适用"
        
        unit_price = 0.0
        if building_area and building_area > 0 and market_value > 0:
            unit_price = market_value * 10000 / building_area
        
        unit_price_str = f"{unit_price:,.2f}" if unit_price > 0 else "待确认"
        
        remark = self._generate_remark(case)
        
        source_text = display_address
        source_link = case.get("link", "")
        
        formatted = {
            "index": index,
            "参照物位置": f"{index}、{display_type}-{display_address}",
            "土地面积(m²)": land_area_str,
            "建筑面积(m²)": building_area_str,
            "市场价值(万元)": f"{market_value:,.2f}" if market_value > 0 else "0.00",
            "建筑单价(元/㎡)": unit_price_str,
            "数据来源": source_text,
            "数据来源_链接": source_link,
            "备注": remark,
            "价格类型": "普通司法拍卖",
            # 额外字段
            "is_self_auction": case.get("is_self_auction", False),
            "price_anomaly": case.get("price_anomaly"),
            "unit_price_value": unit_price,
            "driving_distance": case.get("driving_distance"),
            "distance_km": case.get("distance_km"),
            "start_date": case.get("start_date"),
            "building_area_value": building_area,
            "score": case.get("score", 0),
            "link": source_link,
        }
        
        return formatted
    
    def _generate_remark(self, case: Dict) -> str:
        """生成备注（按时间顺序：一拍→二拍→变卖，最后是状态和距离）"""
        parts = []
        history = case.get('auction_history', [])
        
        if not history:
            stage = case.get('current_stage', '一拍')
            date = case.get('start_date')
            date_str = date.strftime('%Y年%m月%d日') if date and isinstance(date, datetime) else '详见详情页'
            price = self._get_market_value(case) * 10000
            price_str = f"{price:,.0f}元" if price > 0 else '详见详情页'
            
            part = f"{stage}：起拍时间：{date_str}，起拍价：{price_str}"
            parts.append(part)
        else:
            for h in history:
                stage = h.get('stage', '一拍')
                date = h.get('start_date')
                date_str = date.strftime('%Y年%m月%d日') if date and isinstance(date, datetime) else '详见详情页'
                start_price = h.get('start_price', 0)
                deal_price = h.get('deal_price', 0)
                status = h.get('status', '')
                
                start_price_str = f"{start_price:,.0f}元" if start_price > 0 else '详见详情页'
                deal_price_str = f"{deal_price:,.0f}元" if deal_price > 0 else ''
                
                part = f"{stage}：起拍时间：{date_str}，起拍价：{start_price_str}"
                if status == '已成交' and deal_price > 0:
                    part += f"，成交价：{deal_price_str}"
                
                parts.append(part)
        
        # 状态
        if history:
            status = history[-1].get('status', case.get('status', ''))
        else:
            status = case.get('status', '')
        parts.append(f"状态：{status}")
        
        # 距离
        if case.get('is_self_auction'):
            parts.append("距离抵押物约抵押物自身拍卖案例")
        else:
            dist = case.get('driving_distance')
            if dist and dist > 0:
                dist_str = self.location_service.format_distance(dist)
                parts.append(f"距离抵押物约{dist_str}")
            else:
                parts.append("距离未知")
        
        # 价格异常提示
        if case.get('price_anomaly') == 'high':
            parts.append("⚠️ 价格偏高，需注意")
        elif case.get('price_anomaly') == 'low':
            parts.append("⚠️ 价格偏低，需注意")
        
        return "，".join(parts)
    
    def _calculate_statistics_v2(self, cases: List[Dict], asset_type: str) -> Dict:
        """计算统计信息"""
        if not cases:
            return {}
        
        prices = []
        unit_prices = []
        areas = []
        
        for c in cases:
            try:
                mv = float(str(c.get('市场价值(万元)', '0')).replace(',', ''))
                if mv > 0:
                    prices.append(mv)
            except:
                pass
            
            try:
                up = float(str(c.get('建筑单价(元/㎡)', '0')).replace(',', ''))
                if up > 0:
                    unit_prices.append(up)
            except:
                pass
            
            try:
                ba = float(str(c.get('建筑面积(m²)', '0')).replace(',', ''))
                if ba > 0:
                    areas.append(ba)
            except:
                pass
        
        stats = {
            "case_count": len(cases),
        }
        
        if prices:
            stats["avg_price"] = round(sum(prices) / len(prices), 2)
            stats["min_price"] = round(min(prices), 2)
            stats["max_price"] = round(max(prices), 2)
            prices.sort()
            stats["median_price"] = round(prices[len(prices)//2], 2)
        
        if unit_prices:
            stats["avg_unit_price"] = round(sum(unit_prices) / len(unit_prices), 2)
            unit_prices.sort()
            stats["median_unit_price"] = round(unit_prices[len(unit_prices)//2], 2)
        
        if areas:
            stats["avg_area"] = round(sum(areas) / len(areas), 2)
        
        return stats

    def _get_search_keywords(self, asset_type: str, sub_type: Optional[str]) -> List[str]:
        """获取搜索关键词"""
        if asset_type == "住宅":
            return self.type_mapping["住宅"]
        elif asset_type in ["商业", "工业", "土地", "特殊资产"]:
            if sub_type and sub_type in self.type_mapping[asset_type]:
                return self.type_mapping[asset_type][sub_type]
            else:
                all_keywords = []
                for keywords in self.type_mapping[asset_type].values():
                    all_keywords.extend(keywords)
                return list(set(all_keywords))
        return [asset_type]
    
    def _search_platforms(self, keyword: str, page: int = 1) -> List[Dict]:
        """搜索所有平台（包含详情页爬取）"""
        cases = []
        
        # 京东拍卖
        jd_items = self.searcher.search_jd(keyword, page=page, page_size=20)
        for item in jd_items:
            case = self._convert_to_case(item, "jd")
            if case:
                cases.append(case)
        
        # 淘宝司法拍卖（必须爬取详情页）
        tb_items = self.searcher.search_taobao(keyword, page=page, page_size=20)
        for item in tb_items:
            # 爬取详情页获取完整数据
            detail = None
            item_id = item.get('item_id', '')
            if item_id:
                detail = self.searcher.get_taobao_detail(item_id)
            
            case = self._convert_to_case(item, "taobao", detail)
            if case:
                cases.append(case)
        
        return cases
    
    def _convert_to_case(self, item: Dict, platform: str, detail: Optional[Dict] = None) -> Optional[Dict]:
        """将搜索结果转换为案例格式（支持详情页数据）"""
        title = item.get('title', '')
        if not title:
            return None
        
        # 过滤明显不相关的案例
        irrelevant_keywords = [
            '律师事务所', '律所', '法院', '公证处', '公司', '集团',
            '股份', '有限', '银行', '保险', '证券', '基金',
            '学校', '医院', '政府', '机关', '村委会', '居委会'
        ]
        for kw in irrelevant_keywords:
            if kw in title:
                return None
        
        # 优先使用详情页地址
        address = ''
        if detail and detail.get('address'):
            address = detail['address']
        else:
            address = item.get('address', '') or self._extract_address(title)
        
        # 必须有地址或标题中包含地址信息
        if not address:
            has_location = any(key in title for key in ['市', '区', '县', '镇', '路', '街', '巷', '号'])
            if not has_location:
                return None
        
        start_price = self._parse_price(item.get('start_price', ''))
        current_price = self._parse_price(item.get('current_price', ''))
        
        # 京东公告数据质量低，要求必须有价格信息
        if platform == "jd" and start_price <= 0 and current_price <= 0:
            return None
        
        # 从详情页获取面积
        building_area = 0
        land_area = 0
        if detail:
            building_area = detail.get('building_area', 0)
            land_area = detail.get('land_area', 0)
        
        # 如果详情页没有面积，从标题提取
        if building_area <= 0:
            area_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(?:㎡|平方米|平米)', title)
            if area_match:
                try:
                    building_area = float(area_match.group(1).replace(',', ''))
                except:
                    pass
        
        case = {
            "title": title,
            "address": address,
            "link": item.get('link', ''),
            "source": "京东拍卖" if platform == "jd" else "淘宝司法拍卖",
            "source_url": item.get('link', ''),
            "platform": platform,
            "start_price": start_price,
            "current_price": current_price,
            "building_area": building_area,
            "land_area": land_area,
            "status": item.get('status', ''),
            "item_id": item.get('item_id', ''),
            "auction_records": detail.get('auction_records', []) if detail else [],
            "detail_success": detail.get('success', False) if detail else False,
            "unit_price": None,
            "date": detail.get('deal_date') if detail and detail.get('deal_date') else datetime.now(),
            "start_date": detail.get('start_date') if detail else None,
            "deal_date": detail.get('deal_date') if detail else None,
            "auction_stage": detail.get('current_stage', '一拍') if detail else '一拍',
            "auction_history": [],
        }
        
        # 计算单价（使用起拍价或当前价）
        market_value = case["current_price"] if case["current_price"] > 0 else case["start_price"]
        if case["building_area"] and case["building_area"] > 0 and market_value > 0:
            case["unit_price"] = market_value * 10000 / case["building_area"]
        
        return case
    
    def _parse_price(self, price_str) -> float:
        """解析价格字符串，返回万元"""
        if not price_str:
            return 0
        
        if isinstance(price_str, (int, float)):
            return float(price_str) / 10000 if price_str > 10000 else float(price_str)
        
        if isinstance(price_str, str):
            price_str = price_str.replace(',', '').replace(' ', '')
            
            # 万为单位
            if '万' in price_str:
                num_match = re.search(r'([\d\.]+)', price_str)
                if num_match:
                    return float(num_match.group(1))
            
            # 纯数字
            num_match = re.search(r'([\d\.]+)', price_str)
            if num_match:
                num = float(num_match.group(1))
                if num > 10000:
                    return num / 10000
                return num
        
        return 0
    
    def _extract_area(self, title: str, area_str: str = "") -> Optional[float]:
        """提取面积"""
        if area_str:
            area_match = re.search(r'([\d\.]+)', area_str)
            if area_match:
                return float(area_match.group(1))
        
        if title:
            patterns = [
                r'([\d\.]+)\s*(?:平方米|平米|㎡|m²|M²)',
                r'建面[:：]?\s*([\d\.]+)',
                r'面积[:：]?\s*([\d\.]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, title)
                if match:
                    return float(match.group(1))
        
        return None
    
    def _extract_address(self, title: str) -> str:
        """从标题中提取地址"""
        if not title:
            return ""
        
        addr_patterns = [
            r'([\u4e00-\u9fa5]+[市区县].*?\d+号楼?.*?\d+室?)',
            r'([\u4e00-\u9fa5]+[路街巷].*?\d+号)',
            r'位于(.{5,30}?[路街道号])',
        ]
        
        for pattern in addr_patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)
        
        return title[:30] if len(title) > 30 else title
    
    def _extract_clean_address(self, title: str) -> str:
        """从标题中提取干净的地址（去掉营销文案、特殊符号等）"""
        if not title:
            return ""
        
        cleaned = title
        
        cleaned = re.sub(r'[【\[].*?[】\]]', '', cleaned)
        cleaned = re.sub(r'[（(].*?[）)]', '', cleaned)
        cleaned = re.sub(r'[「『].*?[」』]', '', cleaned)
        
        marketing_keywords = [
            '特价', '捡漏', '笋盘', '优质', '稀缺', '抢手', '热卖', '爆款', '超值', '划算',
            '年租金', '年租', '租金', '回报', '地铁口', '学区', '精装', '毛坯', '南北通透',
            '急售', '亏本', '低价', '清盘', '首发', '上新', '限时', '秒杀', '折扣',
            '优惠', '赠送', '带租约', '可贷款', '不限购', '可落户', '拎包入住',
            '投资自住', '地段成熟', '配套成熟', '交通便利', '升值潜力', '近地铁口',
            '送家私家电', '发票价', '租约稳定', '带稳定租约', '可商可住',
            '资产处置', '低价处置', '甄选好房', '好房', '靓房', '笋价', '抄底',
            '捡漏价', '一口价', ' loft ', ' LOFT ', ' 千灯湖商圈', '金融新城',
        ]
        
        for kw in marketing_keywords:
            cleaned = cleaned.replace(kw, '')
        
        cleaned = re.sub(r'[，。、；：""''！？\s]+', ' ', cleaned).strip()
        cleaned = cleaned.strip(' -_—|/\\')
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if len(cleaned) < 6 or len(cleaned) > 60:
            return ""
        
        addr_keywords = ['市', '区', '县', '路', '街', '道', '号', '层', '室', '栋', '单元', '镇', '乡', '村', '广场', '大厦', '花园', '小区', '公寓', '写字楼', '商业中心']
        keyword_count = sum(1 for kw in addr_keywords if kw in cleaned)
        
        if keyword_count >= 2:
            return cleaned
        
        return ""
    
    def _enrich_cases_with_playwright(self, cases: List[Dict]) -> int:
        """使用 Playwright 爬取详情页，补充案例信息"""
        success_count = 0
        
        try:
            from taobao_playwright_crawler import TaobaoDetailCrawler
        except ImportError:
            print("   ⚠  Playwright 爬虫模块不可用，跳过详情页补充")
            return 0
        
        crawler = None
        try:
            crawler = TaobaoDetailCrawler(headless=True)
            crawler.start()
            
            if not crawler.is_logged_in():
                print("   ⚠  淘宝未登录，无法获取详情页完整数据")
                print("   💡 提示：请运行 python login_taobao.py 进行登录")
                return 0
            
            for i, case in enumerate(cases):
                item_id = case.get('item_id', '')
                if not item_id:
                    continue
                
                try:
                    detail = crawler.get_detail(item_id)
                    if detail and detail.get('success'):
                        updated = False
                        if detail.get('building_area', 0) > 0 and case.get('building_area', 0) == 0:
                            case['building_area'] = detail['building_area']
                            updated = True
                        if detail.get('start_date') and not case.get('start_date'):
                            case['start_date'] = detail['start_date']
                            updated = True
                        if detail.get('address') and not case.get('address'):
                            case['address'] = detail['address']
                            updated = True
                        if detail.get('deal_price', 0) > 0:
                            case['deal_price'] = detail['deal_price']
                            updated = True
                        if detail.get('auction_history'):
                            case['auction_history'] = detail['auction_history']
                            updated = True
                        if detail.get('current_stage'):
                            case['current_stage'] = detail['current_stage']
                            updated = True
                        if detail.get('status') and detail.get('status') != '未知':
                            case['status'] = detail['status']
                            updated = True
                        if updated:
                            success_count += 1
                except Exception as e:
                    print(f"   ⚠  爬取详情页失败 ({item_id}): {e}")
                
                if i < len(cases) - 1:
                    crawler.page.wait_for_timeout(500)
                    
        except Exception as e:
            print(f"   ⚠  Playwright 爬虫异常: {e}")
        finally:
            if crawler:
                try:
                    crawler.close()
                except:
                    pass
        
        return success_count
    
    def _extract_city_district(self, address: str) -> str:
        """从地址中提取城市+区/县信息，用于放宽搜索"""
        if not address:
            return ""
        
        # 匹配 "XX市XX区" 或 "XX市XX县" 或 "XX区" 等
        patterns = [
            r'([\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+[区县])',
            r'([\u4e00-\u9fa5]+市[\u4e00-\u9fa5]+镇)',
            r'([\u4e00-\u9fa5]+[区县][\u4e00-\u9fa5]+[路街道])',
            r'([\u4e00-\u9fa5]+市)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address)
            if match:
                return match.group(1)
        
        # 如果没有匹配到，返回前10个字符作为区域参考
        return address[:10] if len(address) > 10 else address
    
    def _get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """高德API地址转坐标"""
        if not self.gaode_api_key:
            return None
        
        url = f"https://restapi.amap.com/v3/geocode/geo?address={quote_plus(address)}&key={self.gaode_api_key}"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1" and data.get("geocodes"):
                location = data["geocodes"][0]["location"]
                lng, lat = map(float, location.split(","))
                return (lng, lat)
        except Exception as e:
            print(f"⚠ 坐标解析失败: {e}")
        
        return None
    
    def _calculate_driving_distance(self, origin: Tuple, destination: Tuple) -> float:
        """计算驾车距离（米）"""
        if not self.gaode_api_key:
            return self._calculate_haversine_distance(origin, destination)
        
        url = (f"https://restapi.amap.com/v3/direction/driving?"
               f"origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}"
               f"&key={self.gaode_api_key}")
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1" and data.get("route", {}).get("paths"):
                distance = float(data["route"]["paths"][0]["distance"])
                return distance
        except Exception as e:
            print(f"⚠ 距离计算失败: {e}")
        
        return self._calculate_haversine_distance(origin, destination)
    
    def _calculate_driving_distance_km(self, origin: Tuple, destination: Tuple) -> Optional[float]:
        """计算驾车距离（公里），使用高德API，失败返回None"""
        if not self.gaode_api_key:
            return None
        
        url = (f"https://restapi.amap.com/v3/direction/driving?"
               f"origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}"
               f"&key={self.gaode_api_key}")
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "1" and data.get("route", {}).get("paths"):
                distance_meters = float(data["route"]["paths"][0]["distance"])
                return round(distance_meters / 1000, 1)
        except Exception as e:
            print(f"⚠ 驾车距离计算失败: {e}")
        
        return None
    
    def _calculate_haversine_distance(self, origin: Tuple, destination: Tuple) -> float:
        """使用Haversine公式计算直线距离（米）"""
        R = 6371000
        
        lat1 = math.radians(origin[1])
        lat2 = math.radians(destination[1])
        dlat = math.radians(destination[1] - origin[1])
        dlng = math.radians(destination[0] - origin[0])
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _is_within_range(self, asset_type: str, distance: float) -> bool:
        """判断是否在搜索范围内"""
        if asset_type in ["住宅", "商业"]:
            return distance <= 5000
        else:
            return distance <= 10000
    
    def _calculate_case_score(self, case: Dict, asset_type: str, sub_type: Optional[str],
                             building_area: Optional[float], land_area: Optional[float]) -> float:
        """计算案例评分（0-300分）"""
        score = 0
        
        # 1. 距离分（0-100分）
        distance = case.get("distance")
        if distance is not None:
            if distance <= 1000:
                score += 100
            elif distance <= 3000:
                score += 80
            elif distance <= 5000:
                score += 60
            elif distance <= 10000:
                score += 40
            else:
                score += 20
        else:
            score += 50
        
        # 2. 价格合理性分（0-100分）
        if case.get("current_price", 0) > 0:
            score += 80
        elif case.get("start_price", 0) > 0:
            score += 60
        else:
            score += 30
        
        # 3. 面积相似分（0-100分）
        if building_area and case.get("building_area"):
            area_diff = abs(building_area - case["building_area"]) / building_area
            if area_diff <= 0.2:
                score += 100
            elif area_diff <= 0.5:
                score += 60
            else:
                score += 20
        elif building_area:
            score += 30
        else:
            score += 50
        
        return score
    
    def _is_self_auction(self, input_address: str, case_address: str) -> bool:
        """判断是否抵押物自身拍卖"""
        if not input_address or not case_address:
            return False
        
        input_clean = re.sub(r'[^\u4e00-\u9fa5\d]', '', input_address)
        case_clean = re.sub(r'[^\u4e00-\u9fa5\d]', '', case_address)
        
        if input_clean == case_clean:
            return True
        
        if len(input_clean) > 5 and input_clean in case_clean:
            return True
        
        if len(case_clean) > 5 and case_clean in input_clean:
            return True
        
        return False
    
    def _get_no_case_message(self, asset_type: str, sub_type: Optional[str]) -> str:
        """获取无案例提示信息"""
        type_name = sub_type if sub_type else asset_type
        if asset_type in ["住宅", "商业"]:
            return (f"【暂无可供参考的案例】\n"
                    f"搜索范围：{type_name}，2年内，5公里内\n"
                    f"说明：已穷尽搜索条件，未找到匹配案例")
        else:
            return (f"【暂无可供参考的案例】\n"
                    f"搜索范围：{type_name}，5年内，10公里内/同区域\n"
                    f"说明：已穷尽搜索条件，未找到匹配案例")
    
    def _format_case_output(self, index: int, case: Dict, 
                           asset_type: str, sub_type: Optional[str]) -> Dict:
        """格式化案例输出为8列格式（使用严格模板备注+统一数据来源）"""
        display_type = self._get_display_type(case, asset_type, sub_type)
        
        address = case.get("address", "")
        title = case.get("title", "")
        display_address = address if address else title[:30]
        
        market_value = case.get("current_price") or case.get("start_price") or 0
        building_area = case.get("building_area")
        land_area = case.get("land_area")
        
        building_area_str = self._format_area(building_area)
        land_area_str = self._format_area(land_area)
        
        unit_price = None
        if building_area and building_area > 0 and market_value > 0:
            unit_price = market_value * 10000 / building_area
        
        if building_area_str == "不适用":
            unit_price_str = "不适用"
        else:
            unit_price_str = self._format_unit_price(unit_price)
        
        # 使用严格模板生成备注
        备注 = self.excel生成器.生成备注_from_case(
            case, self._current_mortgage_info, asset_type, sub_type
        )
        
        # 统一数据来源名称
        原始来源 = case.get("source", "") or case.get("source_url", "") or case.get("link", "")
        统一来源 = self.格式化器.统一数据来源(原始来源)
        
        formatted = {
            "参照物位置": f"{index}、{display_type}-{display_address}",
            "参照物位置_链接": case.get("source_url", "") or case.get("link", ""),
            "土地面积(m²)": land_area_str,
            "建筑面积(m²)": building_area_str,
            "市场价值(万元)": self._format_value(market_value),
            "建筑单价(元/㎡)": unit_price_str,
            "数据来源": 统一来源,
            "备注": 备注,
            "价格类型": "普通司法拍卖"
        }
        
        return formatted
    
    def _get_display_type(self, case: Dict, asset_type: str, sub_type: Optional[str]) -> str:
        """获取显示类型"""
        if asset_type == "住宅":
            return "住宅"
        elif asset_type == "商业":
            return sub_type if sub_type else "商业"
        elif asset_type == "工业":
            if case.get("land_area") and not case.get("building_area"):
                return "工业用地"
            return sub_type if sub_type else "工业房地产"
        elif asset_type == "土地":
            return sub_type if sub_type else "土地"
        elif asset_type == "特殊资产":
            return sub_type if sub_type else "特殊资产"
        return asset_type
    
    def _format_area(self, value: Optional[float]) -> str:
        """格式化面积"""
        if value is None or value == 0:
            return "不适用"
        return f"{value:,.2f}"
    
    def _format_value(self, value: Optional[float]) -> str:
        """格式化价值"""
        if value is None or value <= 0:
            return "0.00"
        return f"{value:,.2f}"
    
    def _format_unit_price(self, value: Optional[float]) -> str:
        """格式化单价"""
        if value is None or value <= 0:
            return "0.00"
        return f"{value:,.2f}"
    
    def _format_remarks(self, case: Dict) -> str:
        """格式化备注
        
        备注格式必须包含：
        - 拍卖轮次：一拍/二拍/三拍/变卖
        - 时间：YYYY-MM-DD
        - 价格：已成交案例必须同时披露起拍价和成交价（元为单位，带千分符）
        - 距离：距离抵押物：1km以内显示XX米，1km以上显示X.X公里，抵押物自身写"抵押物自身拍卖案例"
        - 状态：正在进行流拍/已成交/变卖失败/正在进行/即将开始
        """
        remarks = []
        
        is_self = case.get("is_self_auction", False)
        
        # 1. 拍卖轮次（默认一拍，实际应从数据中获取）
        auction_stage = case.get("auction_stage", "一拍")
        remarks.append(f"拍卖轮次：{auction_stage}")
        
        # 2. 时间（YYYY-MM-DD格式）
        auction_date = case.get("date")
        if isinstance(auction_date, datetime):
            date_str = auction_date.strftime("%Y-%m-%d")
        elif isinstance(auction_date, str):
            date_str = auction_date[:10]
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")
        remarks.append(f"时间：{date_str}")
        
        # 3. 价格信息（以元为单位，带千分符）
        start_price_wan = case.get("start_price", 0)
        current_price_wan = case.get("current_price", 0)
        deal_price_wan = case.get("deal_price", 0)
        
        start_price_yuan = start_price_wan * 10000
        current_price_yuan = current_price_wan * 10000
        deal_price_yuan = deal_price_wan * 10000
        
        if start_price_yuan > 0:
            remarks.append(f"起拍价：{start_price_yuan:,.2f}元")
        
        # 已成交案例需要成交价
        status = str(case.get("status", ""))
        is_sold = status in ['3', '已成交', 'deal', 'sold'] or deal_price_yuan > 0
        if is_sold and deal_price_yuan > 0:
            remarks.append(f"成交价：{deal_price_yuan:,.2f}元")
        elif is_sold and current_price_yuan > 0:
            remarks.append(f"成交价：{current_price_yuan:,.2f}元")
        
        # 4. 距离
        if is_self:
            remarks.append("距离抵押物：抵押物自身拍卖案例")
        else:
            distance = case.get("distance")
            if distance is not None:
                if distance < 1000:
                    distance_text = f"{int(distance)}米"
                else:
                    distance_text = f"{distance/1000:.1f}公里"
                remarks.append(f"距离抵押物：{distance_text}")
            else:
                remarks.append("距离抵押物：未计算")
        
        # 5. 状态（5种之一：正在进行流拍/已成交/变卖失败/正在进行/即将开始）
        status_map = {
            'ing': '正在进行',
            '1': '正在进行',
            'auctioning': '正在进行',
            'before': '即将开始',
            '0': '即将开始',
            'pending': '即将开始',
            'end': '已成交',
            '2': '已成交',
            '3': '已成交',
            'sold': '已成交',
            'deal': '已成交',
            'failed': '正在进行流拍',
            '流拍': '正在进行流拍',
            'fail': '变卖失败',
            '变卖失败': '变卖失败',
            '拍卖中': '正在进行',
            '已结束': '已成交',
            '待开拍': '即将开始',
        }
        status_text = status_map.get(status, '正在进行')
        remarks.append(f"状态：{status_text}")
        
        return "；".join(remarks)
    
    def _calculate_statistics(self, cases: List[Dict], asset_type: str) -> Dict:
        """计算统计信息"""
        if not cases:
            return {}
        
        unit_prices = []
        market_values = []
        
        for case in cases:
            unit_price_str = case.get("建筑单价(元/㎡)", "")
            if unit_price_str and unit_price_str != "0.00":
                try:
                    price = float(unit_price_str.replace(",", "").split()[0])
                    if price > 0:
                        unit_prices.append(price)
                except:
                    pass
            
            value_str = case.get("市场价值(万元)", "")
            if value_str and value_str != "0.00":
                try:
                    value = float(value_str.replace(",", ""))
                    if value > 0:
                        market_values.append(value)
                except:
                    pass
        
        stats = {
            "case_count": len(cases),
        }
        
        if unit_prices:
            avg_price = sum(unit_prices) / len(unit_prices)
            filtered_prices = [p for p in unit_prices 
                             if avg_price * 0.5 <= p <= avg_price * 2.0]
            
            if filtered_prices:
                reference_avg = sum(filtered_prices) / len(filtered_prices)
                stats["reference_avg_price"] = f"{reference_avg:,.2f}"
                stats["normal_case_count"] = len(filtered_prices)
                stats["min_unit_price"] = f"{min(filtered_prices):,.2f}"
                stats["max_unit_price"] = f"{max(filtered_prices):,.2f}"
        
        if market_values:
            stats["avg_market_value"] = f"{sum(market_values)/len(market_values):,.2f}"
            stats["min_market_value"] = f"{min(market_values):,.2f}"
            stats["max_market_value"] = f"{max(market_values):,.2f}"
        
        return stats
    
    def print_results(self, result: Dict):
        """打印搜索结果"""
        if result.get("status") == "no_cases":
            print("\n" + "=" * 80)
            print(result.get("message", "未找到相关案例"))
            print("=" * 80)
            return
        
        cases = result.get("cases", [])
        stats = result.get("statistics", {})
        
        print("\n" + "=" * 80)
        print("📋 参考案例列表")
        print("=" * 80)
        
        for idx, case in enumerate(cases, 1):
            print(f"\n【案例 {idx}】")
            print(f"  位置: {case['参照物位置']}")
            print(f"  建筑面积: {case['建筑面积(m²)']}")
            print(f"  市场价值: {case['市场价值(万元)']} 万元")
            print(f"  建筑单价: {case['建筑单价(元/㎡)']} 元/㎡")
            print(f"  数据来源: {case['数据来源'][:60]}...")
            if case['备注']:
                print(f"  备注: {case['备注']}")
        
        if stats:
            print("\n" + "=" * 80)
            print("📊 统计信息")
            print("=" * 80)
            print(f"  案例数量: {stats.get('case_count', 0)} 个")
            if stats.get('reference_avg_price'):
                print(f"  参考均价: {stats['reference_avg_price']} 元/㎡")
                print(f"  价格区间: {stats.get('min_unit_price', '-')} ~ {stats.get('max_unit_price', '-')} 元/㎡")
            if stats.get('avg_market_value'):
                print(f"  平均市值: {stats['avg_market_value']} 万元")
        
        print("=" * 80)
    
    def cleanup(self):
        """清理资源"""
        self.searcher.cleanup()
    
    # ==================== 增强版搜索功能 ====================
    
    def search_cases_enhanced(self, address: str, asset_type: str,
                             sub_type: Optional[str] = None,
                             building_area: Optional[float] = None,
                             land_area: Optional[float] = None,
                             owner: Optional[str] = None,
                             certificate_no: Optional[str] = None,
                             max_results: int = 20,
                             use_dynamic_weight: bool = True) -> Dict:
        """
        增强版案例搜索（支持自身案例多维度匹配、动态面积权重、距离二次验证）
        
        Args:
            address: 目标地址
            asset_type: 资产类型
            sub_type: 子类型
            building_area: 建筑面积
            land_area: 土地面积
            owner: 产权人
            certificate_no: 权证号
            max_results: 最大结果数
            use_dynamic_weight: 是否使用动态权重
            
        Returns:
            增强版搜索结果
        """
        print("\n" + "=" * 80)
        print("🚀 不良资产估值工具 - 增强版案例搜索")
        print("=" * 80)
        print(f"📍 目标地址: {address}")
        print(f"🏠 资产类型: {asset_type}" + (f" - {sub_type}" if sub_type else ""))
        if building_area:
            print(f"📐 建筑面积: {building_area} ㎡")
        if land_area:
            print(f"📐 土地面积: {land_area} ㎡")
        if owner:
            print(f"👤 产权人: {owner}")
        
        # 先搜索案例
        basic_result = self.search_cases(
            address=address,
            asset_type=asset_type,
            sub_type=sub_type,
            building_area=building_area,
            land_area=land_area,
            max_results=max_results * 2  # 多搜一些，后面筛选
        )
        
        all_cases = basic_result.get("cases", [])
        
        if not all_cases:
            return {
                **basic_result,
                "enhanced": True,
                "self_cases": [],
                "similar_cases_ranked": []
            }
        
        # 构建抵押物信息
        mortgage_info = {
            'address': address,
            'full_address': address,
            'building_area': building_area or 0,
            'land_area': land_area or 0,
            'total_area': (building_area or 0) + (land_area or 0),
            'owner': owner or '',
            'owner_id': '',
            'certificate_no': certificate_no or '',
            'property_no': certificate_no or '',
            'property_type': asset_type,
            'sub_type': sub_type or '',
            'coordinates': basic_result.get("target_coordinates"),
            'split_info': []
        }
        
        # 1. 识别自身拍卖案例
        self_cases = []
        other_cases = []
        
        for case in all_cases:
            case_info = {
                'address': case.get("address", ""),
                'full_address': case.get("title", ""),
                'building_area': case.get("building_area", 0) or 0,
                'land_area': case.get("land_area", 0) or 0,
                'auction_area': case.get("building_area", 0) or 0,
                'owner': case.get("owner", ""),
                'owner_id': case.get("owner_id", ""),
                'certificate_no': case.get("certificate_no", ""),
                'property_no': case.get("property_no", ""),
                'property_type': case.get("asset_type", ""),
                'coordinates': case.get("coordinates"),
                'distance_km': case.get("distance", 999) / 1000 if case.get("distance") else 999
            }
            
            is_self, match_score, match_details = self.enhanced_searcher.is_self_auction_case(
                mortgage_info, case_info
            )
            
            case_with_enhanced = {
                **case,
                'is_self_case': is_self,
                'self_match_score': match_score,
                'self_match_details': match_details
            }
            
            if is_self:
                self_cases.append(case_with_enhanced)
            else:
                other_cases.append(case_with_enhanced)
        
        # 2. 使用动态权重排序相似案例
        similar_ranked = []
        if use_dynamic_weight and other_cases:
            # 转换为增强搜索需要的格式
            enhanced_cases = []
            for case in other_cases:
                enhanced_cases.append({
                    **case,
                    'building_area': case.get("building_area", 0) or 0,
                    'land_area': case.get("land_area", 0) or 0,
                    'coordinates': case.get("coordinates"),
                    'distance_km': case.get("distance", 999) / 1000 if case.get("distance") else 999,
                    'property_type': case.get("asset_type", ""),
                    'asset_type': case.get("asset_type", "")
                })
            
            ranked = self.enhanced_searcher.find_similar_cases_dynamic(
                mortgage_info, enhanced_cases, top_n=max_results
            )
            
            for item in ranked:
                case_data = item['case']
                similar_ranked.append({
                    **case_data,
                    'enhanced_score': item['total_score'],
                    'area_score': item['area_score'],
                    'distance_score': item['distance_score'],
                    'year_score': item['year_score'],
                    'weight_used': item['weight_used'],
                    'is_self_case': item['is_self_case'],
                    'self_match_score': item['self_match_score']
                })
        else:
            similar_ranked = other_cases[:max_results]
        
        # 3. 距离二次验证（如果有API key）
        distance_verification = []
        if self.gaode_api_key and basic_result.get("target_coordinates"):
            cases_to_verify = self_cases + similar_ranked[:10]
            enhanced_case_list = []
            for c in cases_to_verify:
                enhanced_case_list.append({
                    'id': c.get("id", ""),
                    'address': c.get("address", ""),
                    'coordinates': c.get("coordinates"),
                    'distance_km': c.get("distance", 999) / 1000 if c.get("distance") else 0
                })
            
            distance_verification = self.enhanced_searcher.batch_verify_distances(
                mortgage_info, enhanced_case_list
            )
        
        # 组装最终结果
        final_cases = self_cases + similar_ranked
        
        # 格式化输出
        formatted_cases = []
        for i, case in enumerate(final_cases[:max_results]):
            formatted = self._format_case_output(i + 1, case, asset_type, sub_type)
            
            # 添加增强信息
            if case.get('is_self_case'):
                formatted['备注'] = "抵押物自身拍卖案例，" + formatted['备注']
            
            formatted_cases.append(formatted)
        
        # 计算统计信息
        statistics = self._calculate_statistics(formatted_cases, asset_type)
        
        return {
            "success": True,
            "target_address": address,
            "asset_type": asset_type,
            "sub_type": sub_type,
            "cases": formatted_cases,
            "raw_cases": final_cases[:max_results],
            "statistics": statistics,
            "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "enhanced": True,
            "self_cases": self_cases,
            "self_case_count": len(self_cases),
            "similar_cases_ranked": similar_ranked,
            "dynamic_weights_used": self.enhanced_searcher.calculate_dynamic_weights(
                building_area or 0, asset_type
            ),
            "distance_verification": distance_verification,
            "no_case_message": basic_result.get("no_case_message", "")
        }
    
    def check_self_auction_cases(self, address: str, asset_type: str,
                                building_area: Optional[float] = None,
                                land_area: Optional[float] = None,
                                owner: Optional[str] = None,
                                certificate_no: Optional[str] = None) -> Dict:
        """
        专门检查抵押物自身拍卖案例
        
        Args:
            address: 抵押物地址
            asset_type: 资产类型
            building_area: 建筑面积
            land_area: 土地面积
            owner: 产权人
            certificate_no: 权证号
            
        Returns:
            自身案例检查结果
        """
        # 先搜索
        result = self.search_cases(
            address=address,
            asset_type=asset_type,
            building_area=building_area,
            land_area=land_area,
            max_results=50
        )
        
        all_cases = result.get("cases", [])
        
        if not all_cases:
            return {
                "has_self_case": False,
                "self_cases": [],
                "all_cases_count": 0,
                "message": "未找到任何拍卖案例"
            }
        
        # 构建抵押物信息
        mortgage_info = {
            'address': address,
            'full_address': address,
            'building_area': building_area or 0,
            'land_area': land_area or 0,
            'total_area': (building_area or 0) + (land_area or 0),
            'owner': owner or '',
            'owner_id': '',
            'certificate_no': certificate_no or '',
            'property_no': certificate_no or '',
            'property_type': asset_type,
            'split_info': []
        }
        
        # 逐个匹配
        self_cases = []
        for case in all_cases:
            case_info = {
                'address': case.get("address", ""),
                'full_address': case.get("title", ""),
                'building_area': case.get("building_area", 0) or 0,
                'land_area': case.get("land_area", 0) or 0,
                'auction_area': case.get("building_area", 0) or 0,
                'owner': case.get("owner", ""),
                'owner_id': case.get("owner_id", ""),
                'certificate_no': case.get("certificate_no", ""),
                'property_no': case.get("property_no", ""),
                'property_type': case.get("asset_type", "")
            }
            
            is_self, match_score, match_details = self.enhanced_searcher.is_self_auction_case(
                mortgage_info, case_info
            )
            
            if is_self:
                self_cases.append({
                    **case,
                    'match_score': match_score,
                    'match_details': match_details
                })
        
        # 按匹配分数排序
        self_cases.sort(key=lambda x: x['match_score'], reverse=True)
        
        return {
            "has_self_case": len(self_cases) > 0,
            "self_cases": self_cases,
            "self_case_count": len(self_cases),
            "all_cases_count": len(all_cases),
            "mortgage_info": mortgage_info,
            "message": f"找到 {len(self_cases)} 个自身拍卖案例" if self_cases else "未找到自身拍卖案例"
        }