import re
import requests
import time
from typing import Optional, Tuple, List, Dict


class LocationService:
    """位置服务：高德地图API封装 + 地址解析 + 距离计算"""

    def __init__(self, gaode_api_key: str):
        self.api_key = gaode_api_key
        self._cache = {}

    def geocode(self, address: str) -> Optional[Dict]:
        """地址转坐标 + 结构化信息
        
        Returns:
            {
                'lng': 经度,
                'lat': 纬度,
                'province': 省份,
                'city': 城市,
                'district': 区县,
                'township': 乡镇/街道,
                'neighborhood': 社区,
                'building': 建筑物,
                'street': 街道,
                'number': 门牌号,
                'formatted_address': 格式化地址,
            }
        """
        if not address or not self.api_key:
            return None

        cache_key = f"geo_{address}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            'key': self.api_key,
            'address': address,
            'output': 'json',
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get('status') == '1' and data.get('geocodes'):
                geo = data['geocodes'][0]
                location_str = geo.get('location', '')
                if location_str:
                    lng, lat = location_str.split(',')
                    result = {
                        'lng': float(lng),
                        'lat': float(lat),
                        'province': geo.get('province', ''),
                        'city': geo.get('city', ''),
                        'district': geo.get('district', ''),
                        'township': geo.get('township', ''),
                        'neighborhood': geo.get('neighborhood', {}).get('name', '') if isinstance(geo.get('neighborhood'), dict) else '',
                        'building': geo.get('building', {}).get('name', '') if isinstance(geo.get('building'), dict) else '',
                        'street': geo.get('street', ''),
                        'number': geo.get('number', ''),
                        'formatted_address': geo.get('formatted_address', ''),
                    }
                    self._cache[cache_key] = result
                    return result
        except Exception as e:
            print(f"⚠ 地理编码失败: {e}")

        return None

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """获取地址的经纬度坐标"""
        geo = self.geocode(address)
        if geo:
            return (geo['lng'], geo['lat'])
        return None

    def extract_search_keywords(self, address: str, asset_type: str) -> List[str]:
        """从地址提取分层搜索关键词
        
        Returns:
            [小区名+类型, 街道/商圈+类型, 行政区+类型, 城市+类型]
        """
        geo = self.geocode(address)
        keywords = []

        if not geo:
            keywords.append(f"{address} {asset_type}")
            return keywords

        # 第1层：小区名 + 类型
        building = geo.get('building', '') or geo.get('neighborhood', '')
        if building and building != '[]':
            keywords.append(f"{building} {asset_type}")

        # 第2层：街道/乡镇 + 类型
        township = geo.get('township', '') or geo.get('street', '')
        if township and township != '[]':
            keywords.append(f"{township} {asset_type}")

        # 第3层：行政区 + 类型
        district = geo.get('district', '')
        if district:
            keywords.append(f"{district} {asset_type}")

        # 第4层：城市 + 类型
        city = geo.get('city', '')
        if city and city not in [k for k in keywords]:
            keywords.append(f"{city} {asset_type}")

        # 如果地址本身很具体，也作为一个关键词
        if address and address not in [k.split()[0] for k in keywords]:
            keywords.insert(0, f"{address} {asset_type}")

        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)

        return unique_keywords[:5]  # 最多5个关键词

    def get_driving_distance_meters(self, origin: Tuple[float, float], 
                                     dest: Tuple[float, float]) -> Optional[float]:
        """计算驾车距离（米）"""
        if not origin or not dest or not self.api_key:
            return None

        cache_key = f"drive_{origin[0]:.4f},{origin[1]:.4f}_{dest[0]:.4f},{dest[1]:.4f}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = "https://restapi.amap.com/v3/direction/driving"
        params = {
            'key': self.api_key,
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{dest[0]},{dest[1]}",
            'strategy': 2,  # 最短距离
            'output': 'json',
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data.get('status') == '1' and data.get('route', {}).get('paths'):
                distance = float(data['route']['paths'][0]['distance'])
                self._cache[cache_key] = distance
                return distance
        except Exception as e:
            print(f"⚠ 驾车距离计算失败: {e}")

        return None

    def format_distance(self, distance_meters: Optional[float]) -> str:
        """格式化距离显示
        
        - 1000米以内：显示 XX米
        - 1000米以上：显示 X.X公里
        """
        if distance_meters is None:
            return "距离未知"

        if distance_meters < 1000:
            return f"{int(distance_meters)}米"
        else:
            return f"{round(distance_meters / 1000, 1)}公里"

    def is_same_address(self, addr1: str, addr2: str) -> bool:
        """判断两个地址是否指向同一个位置"""
        if not addr1 or not addr2:
            return False

        # 简单清理
        def clean(addr):
            addr = re.sub(r'[^\u4e00-\u9fa5\d]', '', addr)
            return addr

        clean1 = clean(addr1)
        clean2 = clean(addr2)

        if clean1 == clean2:
            return True

        # 互相包含且长度大于5
        if len(clean1) > 5 and clean1 in clean2:
            return True
        if len(clean2) > 5 and clean2 in clean1:
            return True

        # 用高德坐标判断（如果都能解析到）
        geo1 = self.geocode(addr1)
        geo2 = self.geocode(addr2)
        if geo1 and geo2:
            dist = self._haversine_distance(
                (geo1['lng'], geo1['lat']),
                (geo2['lng'], geo2['lat'])
            )
            if dist < 100:  # 100米以内算同一个
                return True

        return False

    def _haversine_distance(self, origin: Tuple[float, float], 
                            dest: Tuple[float, float]) -> float:
        """Haversine直线距离（米），用于快速判断"""
        import math
        lon1, lat1 = origin
        lon2, lat2 = dest
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
