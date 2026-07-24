"""
增强版案例搜索逻辑
解决：1.抵押物自身案例多维度匹配 2.动态面积权重 3.距离二次验证
"""

import re
from typing import Dict, List, Tuple, Optional
import math
import requests
from urllib.parse import quote_plus


class EnhancedCaseSearch:
    def __init__(self, gaode_api_key: str = ""):
        self.gaode_api_key = gaode_api_key
        
    # ==================== 问题1：抵押物自身拍卖案例多维度匹配 ====================
    def is_self_auction_case(self, mortgage: Dict, auction_case: Dict) -> Tuple[bool, float, Dict]:
        """
        判断是否为抵押物自身拍卖案例（多维度匹配）
        返回：(是否自身案例, 匹配分数, 各维度详情)
        """
        scores = {}
        details = {}
        
        # 1. 地址相似度（40分）
        addr_score, addr_detail = self._calculate_address_similarity(
            mortgage.get('address', ''),
            mortgage.get('full_address', ''),
            auction_case.get('address', ''),
            auction_case.get('full_address', '')
        )
        scores['address'] = addr_score * 40
        details['address'] = addr_detail
        
        # 2. 面积匹配度（30分）
        area_score, area_detail = self._calculate_area_match(
            mortgage.get('land_area', 0),
            mortgage.get('building_area', 0),
            mortgage.get('total_area', 0),
            mortgage.get('split_info', []),
            auction_case.get('land_area', 0),
            auction_case.get('building_area', 0),
            auction_case.get('auction_area', 0)
        )
        scores['area'] = area_score * 30
        details['area'] = area_detail
        
        # 3. 产权人匹配（20分）
        owner_score, owner_detail = self._calculate_owner_match(
            mortgage.get('owner', ''),
            mortgage.get('owner_id', ''),
            auction_case.get('owner', ''),
            auction_case.get('owner_id', '')
        )
        scores['owner'] = owner_score * 20
        details['owner'] = owner_detail
        
        # 4. 权证号匹配（10分）
        cert_score, cert_detail = self._calculate_certificate_match(
            mortgage.get('certificate_no', ''),
            mortgage.get('property_no', ''),
            auction_case.get('certificate_no', ''),
            auction_case.get('property_no', '')
        )
        scores['certificate'] = cert_score * 10
        details['certificate'] = cert_detail
        
        # 计算总分
        total_score = sum(scores.values())
        score_details = {k: round(v, 2) for k, v in scores.items()}
        
        # 判断是否为自身案例（阈值80分）
        is_self = total_score >= 80
        
        return is_self, round(total_score, 2), {
            'total_score': round(total_score, 2),
            'score_details': score_details,
            'match_details': details,
            'is_self_case': is_self
        }
    
    def _calculate_address_similarity(self, mortgage_addr: str, mortgage_full: str, 
                                     case_addr: str, case_full: str) -> Tuple[float, str]:
        """计算地址相似度（0-1）"""
        if not mortgage_addr or not case_addr:
            return 0.0, "地址为空"
        
        # 标准化地址
        addr1 = self._standardize_address(mortgage_addr)
        addr2 = self._standardize_address(case_addr)
        
        # 完全匹配
        if addr1 == addr2:
            return 1.0, "地址完全匹配"
        
        # 包含关系
        if addr1 in addr2 or addr2 in addr1:
            return 0.8, "地址包含关系"
        
        # 提取关键部分（街道、门牌号）
        key_parts1 = self._extract_address_key_parts(addr1)
        key_parts2 = self._extract_address_key_parts(addr2)
        
        # 关键部分匹配
        common_parts = set(key_parts1) & set(key_parts2)
        if common_parts:
            match_ratio = len(common_parts) / max(len(key_parts1), len(key_parts2))
            return match_ratio, f"关键部分匹配：{common_parts}"
        
        return 0.0, "地址无匹配"
    
    def _calculate_area_match(self, mortgage_land: float, mortgage_building: float,
                             mortgage_total: float, mortgage_split: List,
                             case_land: float, case_building: float,
                             case_total: float) -> Tuple[float, str]:
        """计算面积匹配度（考虑大证拆分）"""
        # 主要比较建筑面积
        target_area = mortgage_building or mortgage_total
        case_area = case_building or case_total
        
        if target_area == 0 or case_area == 0:
            return 0.0, "面积为零"
        
        # 1. 直接匹配（误差10%以内）
        if abs(case_area - target_area) / target_area <= 0.1:
            return 1.0, f"面积直接匹配：{target_area}≈{case_area}"
        
        # 2. 大证拆分匹配（拍卖面积是抵押物的一部分）
        if mortgage_split:
            for split_area in mortgage_split:
                if abs(case_area - split_area) / split_area <= 0.15:
                    return 0.9, f"匹配拆分面积：{split_area}≈{case_area}"
        
        # 3. 比例匹配（如案例面积是抵押物面积的1/2、1/3等）
        ratio = case_area / target_area
        common_ratios = [0.5, 0.33, 0.25, 0.2, 0.1]
        for cr in common_ratios:
            if abs(ratio - cr) / cr <= 0.1:
                return 0.8, f"比例匹配：{ratio:.2f}:1"
        
        # 4. 范围匹配（在合理范围内）
        min_area = target_area * 0.3
        max_area = target_area * 3.0
        if min_area <= case_area <= max_area:
            match_ratio = 1 - abs(case_area - target_area) / target_area
            return max(0.3, match_ratio), f"范围匹配：{min_area:.0f}-{max_area:.0f}"
        
        return 0.0, f"面积不匹配：{target_area} vs {case_area}"
    
    def _calculate_owner_match(self, mortgage_owner: str, mortgage_owner_id: str,
                              case_owner: str, case_owner_id: str) -> Tuple[float, str]:
        """计算产权人匹配度"""
        if not mortgage_owner or not case_owner:
            return 0.0, "产权人信息为空"
        
        # ID完全匹配
        if mortgage_owner_id and case_owner_id and mortgage_owner_id == case_owner_id:
            return 1.0, "产权人ID完全匹配"
        
        # 名称完全匹配
        if mortgage_owner == case_owner:
            return 1.0, "产权人名称完全匹配"
        
        # 名称包含关系
        if mortgage_owner in case_owner or case_owner in mortgage_owner:
            return 0.7, "产权人名称包含"
        
        # 提取公司名关键词
        mortgage_keywords = self._extract_company_keywords(mortgage_owner)
        case_keywords = self._extract_company_keywords(case_owner)
        
        if mortgage_keywords and case_keywords:
            common_keywords = set(mortgage_keywords) & set(case_keywords)
            if common_keywords:
                return 0.5, f"公司关键词匹配：{common_keywords}"
        
        return 0.0, "产权人不匹配"
    
    def _calculate_certificate_match(self, mortgage_cert: str, mortgage_prop: str,
                                    case_cert: str, case_prop: str) -> Tuple[float, str]:
        """计算权证号匹配度"""
        cert_numbers = []
        if mortgage_cert:
            cert_numbers.append(mortgage_cert)
        if mortgage_prop:
            cert_numbers.append(mortgage_prop)
        
        case_numbers = []
        if case_cert:
            case_numbers.append(case_cert)
        if case_prop:
            case_numbers.append(case_prop)
        
        for cert in cert_numbers:
            for case_cert in case_numbers:
                if cert == case_cert:
                    return 1.0, f"权证号完全匹配：{cert}"
                if cert in case_cert or case_cert in cert:
                    return 0.8, f"权证号包含关系"
        
        return 0.0, "权证号不匹配"
    
    # ==================== 问题2：动态面积权重 ====================
    def calculate_dynamic_weights(self, mortgage_area: float, property_type: str = "商业") -> Dict:
        """
        根据抵押物面积动态调整权重
        """
        if mortgage_area <= 100:  # 小面积（<100㎡）
            return {
                'area_weight': 0.6,
                'distance_weight': 0.3,
                'year_weight': 0.1,
                'area_range': (max(10, mortgage_area * 0.5), mortgage_area * 2.0)
            }
        elif mortgage_area <= 1000:  # 中等面积（100-1000㎡）
            return {
                'area_weight': 0.4,
                'distance_weight': 0.4,
                'year_weight': 0.2,
                'area_range': (mortgage_area * 0.3, mortgage_area * 3.0)
            }
        else:  # 大面积（>1000㎡）
            return {
                'area_weight': 0.3,
                'distance_weight': 0.5,
                'year_weight': 0.2,
                'area_range': (mortgage_area * 0.2, mortgage_area * 5.0)
            }
    
    def find_similar_cases_dynamic(self, mortgage: Dict, all_cases: List[Dict], top_n: int = 10) -> List[Dict]:
        """
        动态权重找相似案例
        """
        mortgage_area = mortgage.get('building_area', mortgage.get('land_area', 0))
        weights = self.calculate_dynamic_weights(mortgage_area, mortgage.get('property_type', '商业'))
        
        scored_cases = []
        
        for case in all_cases:
            # 跳过明显不匹配的
            if not self._is_case_relevant(mortgage, case):
                continue
            
            # 计算各维度得分
            area_score = self._calculate_area_similarity_score(
                mortgage, case, weights['area_range']
            )
            
            distance_score = self._calculate_distance_score(
                mortgage.get('coordinates'),
                case.get('coordinates'),
                case.get('distance_km', 999)
            )
            
            year_score = self._calculate_year_similarity_score(
                mortgage.get('build_year'),
                case.get('build_year')
            )
            
            # 计算总分
            total_score = (
                area_score * weights['area_weight'] +
                distance_score * weights['distance_weight'] +
                year_score * weights['year_weight']
            )
            
            # 自身案例加分
            is_self, self_score, self_details = self.is_self_auction_case(mortgage, case)
            if is_self:
                total_score *= 1.5  # 自身案例权重提高50%
            
            scored_cases.append({
                'case': case,
                'total_score': round(total_score, 4),
                'area_score': round(area_score, 4),
                'distance_score': round(distance_score, 4),
                'year_score': round(year_score, 4),
                'is_self_case': is_self,
                'self_match_score': self_score,
                'self_match_details': self_details,
                'weight_used': weights
            })
        
        # 按总分排序，返回top_n
        scored_cases.sort(key=lambda x: x['total_score'], reverse=True)
        return scored_cases[:top_n]
    
    def _calculate_area_similarity_score(self, mortgage: Dict, case: Dict, area_range: Tuple) -> float:
        """计算面积相似度得分"""
        mortgage_area = mortgage.get('building_area', mortgage.get('land_area', 0))
        case_area = case.get('building_area', case.get('land_area', 0))
        
        if mortgage_area == 0 or case_area == 0:
            return 0.0
        
        # 检查是否在合理范围内
        min_area, max_area = area_range
        if not (min_area <= case_area <= max_area):
            return 0.0
        
        # 计算相似度（越接近得分越高）
        ratio = case_area / mortgage_area
        if ratio > 1:
            ratio = 1 / ratio  # 对称处理
        
        # 相似度曲线（越接近1得分越高）
        score = math.exp(-5 * (ratio - 1) ** 2)
        return score
    
    def _calculate_distance_score(self, origin_coords: Optional[Tuple], 
                                  dest_coords: Optional[Tuple],
                                  reported_distance_km: float) -> float:
        """计算距离得分"""
        if reported_distance_km <= 0:
            return 0.5  # 默认中间分
        
        # 距离越近得分越高
        if reported_distance_km <= 1:
            return 1.0
        elif reported_distance_km <= 3:
            return 0.8
        elif reported_distance_km <= 5:
            return 0.6
        elif reported_distance_km <= 10:
            return 0.4
        elif reported_distance_km <= 20:
            return 0.2
        else:
            return 0.1
    
    def _calculate_year_similarity_score(self, mortgage_year: Optional[int], 
                                         case_year: Optional[int]) -> float:
        """计算建筑年限相似度得分"""
        if not mortgage_year or not case_year:
            return 0.5  # 默认中间分
        
        year_diff = abs(mortgage_year - case_year)
        
        if year_diff <= 2:
            return 1.0
        elif year_diff <= 5:
            return 0.8
        elif year_diff <= 10:
            return 0.6
        elif year_diff <= 20:
            return 0.4
        else:
            return 0.2
    
    def _is_case_relevant(self, mortgage: Dict, case: Dict) -> bool:
        """检查案例是否相关（基础过滤）"""
        # 物业类型匹配
        mortgage_type = mortgage.get('property_type', '').lower()
        case_type = case.get('property_type', case.get('asset_type', '')).lower()
        
        if mortgage_type and case_type:
            if mortgage_type != case_type:
                # 检查子类型
                mortgage_sub = mortgage.get('sub_type', '').lower()
                case_sub = case.get('sub_type', '').lower()
                if mortgage_sub and case_sub and mortgage_sub != case_sub:
                    return False
        
        return True
    
    # ==================== 问题3：驾车距离二次验证 ====================
    def verify_driving_distance(self, origin_coords: Tuple[float, float], 
                                dest_coords: Tuple[float, float], 
                                reported_distance_km: float) -> Dict:
        """
        用高德API验证驾车距离
        """
        try:
            # 调用高德API获取真实驾车距离
            real_distance = self._get_gaode_driving_distance(origin_coords, dest_coords)
            
            if real_distance is None:
                return {
                    'is_valid': False,
                    'error': '高德API调用失败',
                    'reported_distance': reported_distance_km,
                    'real_distance': None,
                    'error_rate': None
                }
            
            # 计算误差率
            if reported_distance_km <= 0:
                return {
                    'is_valid': False,
                    'error': '报告距离为0',
                    'reported_distance': reported_distance_km,
                    'real_distance': real_distance,
                    'error_rate': None
                }
            
            error_rate = abs(real_distance - reported_distance_km) / reported_distance_km
            
            return {
                'is_valid': error_rate <= 0.3,  # 误差不超过30%
                'reported_distance': reported_distance_km,
                'real_distance': real_distance,
                'error_rate': round(error_rate, 4),
                'message': f'报告{reported_distance_km}km，实际{real_distance}km，误差{error_rate:.1%}'
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
                'reported_distance': reported_distance_km,
                'real_distance': None,
                'error_rate': None
            }
    
    def batch_verify_distances(self, mortgage_data: Dict, similar_cases: List[Dict]) -> List[Dict]:
        """
        批量验证所有相似案例的距离
        """
        verification_results = []
        mortgage_coords = mortgage_data.get('coordinates')
        
        if not mortgage_coords:
            return verification_results
        
        for case in similar_cases:
            case_coords = case.get('coordinates')
            reported_distance = case.get('distance_km', 0)
            
            if not case_coords or reported_distance == 0:
                continue
            
            verification = self.verify_driving_distance(
                mortgage_coords, case_coords, reported_distance
            )
            
            verification_results.append({
                'case_id': case.get('id'),
                'case_address': case.get('address'),
                'verification': verification
            })
        
        return verification_results
    
    def _get_gaode_driving_distance(self, origin: Tuple[float, float], 
                                    dest: Tuple[float, float]) -> Optional[float]:
        """调用高德API获取驾车距离（公里）"""
        if not self.gaode_api_key:
            return None
        
        try:
            url = (
                f"https://restapi.amap.com/v3/direction/driving?"
                f"origin={origin[0]},{origin[1]}&destination={dest[0]},{dest[1]}"
                f"&key={self.gaode_api_key}"
            )
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("status") == "1" and data.get("route", {}).get("paths"):
                distance_meters = float(data["route"]["paths"][0]["distance"])
                return round(distance_meters / 1000, 2)  # 转换为公里
                
        except Exception as e:
            print(f"高德API调用失败: {e}")
        
        return None
    
    # ==================== 辅助函数 ====================
    def _standardize_address(self, address: str) -> str:
        """标准化地址"""
        if not address:
            return ""
        
        # 移除空格、特殊字符
        address = re.sub(r'\s+', '', address)
        address = re.sub(r'[（）()]', '', address)
        
        # 统一替换
        replacements = {
            '号幢': '号',
            '幢号': '号',
            '号楼': '号',
            '栋号': '号',
            '单元': '',
            '室': '',
            '楼': '',
            '栋': '',
            '幢': '',
        }
        
        for old, new in replacements.items():
            address = address.replace(old, new)
        
        return address
    
    def _extract_address_key_parts(self, address: str) -> List[str]:
        """提取地址关键部分"""
        parts = []
        
        # 提取街道
        street_match = re.search(r'(.*?街道|.*?路|.*?大道|.*?街)', address)
        if street_match:
            parts.append(street_match.group(1))
        
        # 提取门牌号
        number_match = re.search(r'(\d+号)', address)
        if number_match:
            parts.append(number_match.group(1))
        
        # 提取小区/大厦名
        building_match = re.search(r'([^0-9]+小区|[^0-9]+大厦|[^0-9]+广场)', address)
        if building_match:
            parts.append(building_match.group(1))
        
        return parts
    
    def _extract_company_keywords(self, company_name: str) -> List[str]:
        """提取公司名关键词"""
        if not company_name:
            return []
        
        # 移除有限公司、有限责任公司等后缀
        name = re.sub(r'(有限公司|有限责任公司|股份公司|集团公司|分公司|支行|分行|营业部)$', '', company_name)
        
        # 提取中文关键词（2-4字）
        keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', name)
        
        return keywords


# 使用示例
if __name__ == "__main__":
    searcher = EnhancedCaseSearch()
    
    # 测试自身案例匹配
    mortgage = {
        'address': '北京市朝阳区建国门外大街1号',
        'building_area': 200.0,
        'owner': '张三',
        'certificate_no': '京朝字第12345号',
        'property_type': '住宅'
    }
    
    auction_case = {
        'address': '北京市朝阳区建国门外大街1号',
        'building_area': 200.0,
        'owner': '张三',
        'certificate_no': '京朝字第12345号'
    }
    
    is_self, score, details = searcher.is_self_auction_case(mortgage, auction_case)
    print(f"是否自身案例: {is_self}")
    print(f"匹配分数: {score}")
    print(f"详情: {details}")
    
    # 测试动态权重
    weights = searcher.calculate_dynamic_weights(150, '住宅')
    print(f"\n动态权重（150㎡住宅）: {weights}")
