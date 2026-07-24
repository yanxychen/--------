#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输出格式化器 - 严格按模板生成备注、调用高德API计算驾车距离、统一数据来源
"""

import re
from typing import Dict, List, Optional
import requests


class 输出格式化器:
    """严格按模板生成备注，禁止自由发挥"""
    
    def __init__(self, 高德api_key: str = ""):
        self.高德api_key = 高德api_key
        self._坐标缓存: Dict[str, Dict] = {}
    
    def 生成备注(self, 案例信息: Dict) -> str:
        """
        严格按照模板生成备注，禁止自由发挥
        
        模板：
        1、物业类型-详细地址
        2、拍卖状态（一拍/二拍/变卖，起拍价/成交价，状态）
        3、距离抵押物约X公里（或"抵押物自身拍卖"）
        """
        备注行 = []
        
        # 第1行：物业类型-详细地址
        物业类型 = self.标准化物业类型(案例信息.get('物业类型', '未知'))
        详细地址 = self.清理地址(案例信息.get('详细地址', '地址未知'))
        备注行.append(f"1、{物业类型}-{详细地址}")
        
        # 第2行：拍卖状态
        拍卖记录 = 案例信息.get('拍卖记录', [])
        if not 拍卖记录:
            备注行.append("2、拍卖信息缺失")
        else:
            拍卖信息列表 = []
            for 记录 in 拍卖记录:
                轮次 = 记录.get('轮次', '未知')
                日期 = 记录.get('日期', '日期未知')
                价格类型 = 记录.get('价格类型', '价格未知')
                价格 = 记录.get('价格', 0)
                状态 = 记录.get('状态', '状态未知')
                
                价格格式化 = f"{价格:,.0f}" if isinstance(价格, (int, float)) else str(价格)
                
                拍卖信息 = f"{轮次}：{日期}，{价格类型}：{价格格式化}元，状态：{状态}"
                拍卖信息列表.append(拍卖信息)
            
            备注行.append("2、" + "；".join(拍卖信息列表))
        
        # 第3行：距离信息
        是否自身案例 = 案例信息.get('是否自身案例', False)
        if 是否自身案例:
            备注行.append("3、抵押物自身拍卖")
        else:
            抵押物地址 = 案例信息.get('抵押物地址', '')
            案例地址 = 案例信息.get('案例地址', '')
            抵押物坐标 = 案例信息.get('抵押物坐标')
            案例坐标 = 案例信息.get('案例坐标')
            
            if (抵押物地址 or 抵押物坐标) and (案例地址 or 案例坐标) and self.高德api_key:
                距离 = self.计算驾车距离_坐标(抵押物坐标, 案例坐标, 抵押物地址, 案例地址)
                if 距离:
                    备注行.append(f"3、距离抵押物约{距离}公里")
                else:
                    备注行.append("3、距离计算失败")
            else:
                备注行.append("3、距离信息缺失")
        
        return "\n".join(备注行)
    
    def 标准化物业类型(self, 原始类型: str) -> str:
        """统一物业类型名称"""
        映射 = {
            '住宅': '住宅用房',
            '商业': '商业用房',
            '商铺': '商业用房',
            '商业用房': '商业用房',
            '商业用房用房': '商业用房',
            '办公': '办公用房',
            '写字楼': '办公用房',
            '办公用房': '办公用房',
            '办公用房用房': '办公用房',
            '工业': '工业用房',
            '厂房': '工业用房',
            '仓库': '工业用房',
            '工业房地产': '工业用房',
            '工业用房': '工业用房',
            '工业用房用房': '工业用房',
            '工业用地': '工业用地',
            '公寓': '住宅用房',
            '别墅': '住宅用房',
            '住宅用房': '住宅用房',
            '住宅底商': '商业用房',
            '酒店': '商业用房',
            '商场': '商业用房',
            '土地': '土地',
        }
        return 映射.get(原始类型, 原始类型 if '用房' in 原始类型 or '用地' in 原始类型 or 原始类型 == '土地' else (原始类型 + '用房' if 原始类型 else '未知用房'))
    
    def 清理地址(self, 地址: str) -> str:
        """清理地址中的多余空格和特殊字符"""
        if not 地址:
            return "地址未知"
        
        地址 = re.sub(r'\s+', '', 地址)
        地址 = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\-号]', '', 地址)
        
        return 地址 if 地址 else "地址未知"
    
    def 计算驾车距离(self, 地址1: str, 地址2: str) -> Optional[str]:
        """
        调用高德API计算驾车距离
        返回格式："X.Xkm" 或 "Xkm"
        """
        try:
            坐标1 = self.地址转坐标(地址1)
            坐标2 = self.地址转坐标(地址2)
            
            if not 坐标1 or not 坐标2:
                return None
            
            url = "https://restapi.amap.com/v3/direction/driving"
            params = {
                'origin': f"{坐标1['lng']},{坐标1['lat']}",
                'destination': f"{坐标2['lng']},{坐标2['lat']}",
                'key': self.高德api_key,
                'strategy': '0'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('route'):
                距离_米 = int(data['route']['paths'][0]['distance'])
                距离_公里 = 距离_米 / 1000
                
                if 距离_公里 < 10:
                    return f"{距离_公里:.1f}km"
                else:
                    return f"{int(round(距离_公里))}km"
            else:
                return None
                
        except Exception as e:
            print(f"高德API驾车距离调用失败: {e}")
            return None
    
    def 地址转坐标(self, 地址: str) -> Optional[Dict]:
        """地址转经纬度（带缓存）"""
        if not 地址 or not self.高德api_key:
            return None
        
        if 地址 in self._坐标缓存:
            return self._坐标缓存[地址]
        
        try:
            url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                'address': 地址,
                'key': self.高德api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get('status') == '1' and data.get('geocodes'):
                位置 = data['geocodes'][0]['location'].split(',')
                result = {
                    'lng': float(位置[0]),
                    'lat': float(位置[1])
                }
                self._坐标缓存[地址] = result
                return result
            return None
        except Exception as e:
            print(f"高德API地址解析失败: {e}")
            return None
    
    def 计算驾车距离_坐标(self, 坐标1: Optional[Dict], 坐标2: Optional[Dict],
                          地址1: str = "", 地址2: str = "") -> Optional[str]:
        """
        用坐标计算驾车距离，坐标缺失时回退到地址解析
        返回格式："X.Xkm" 或 "Xkm"
        """
        if not 坐标1 and 地址1:
            坐标1 = self.地址转坐标(地址1)
        if not 坐标2 and 地址2:
            坐标2 = self.地址转坐标(地址2)
        
        if not 坐标1 or not 坐标2:
            return None
        
        try:
            url = "https://restapi.amap.com/v3/direction/driving"
            params = {
                'origin': f"{坐标1['lng']},{坐标1['lat']}",
                'destination': f"{坐标2['lng']},{坐标2['lat']}",
                'key': self.高德api_key,
                'strategy': '0'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') == '1' and data.get('route'):
                距离_米 = int(data['route']['paths'][0]['distance'])
                距离_公里 = 距离_米 / 1000
                
                if 距离_公里 < 10:
                    return f"{距离_公里:.1f}km"
                else:
                    return f"{int(round(距离_公里))}km"
            else:
                return None
        except Exception as e:
            print(f"高德API驾车距离调用失败: {e}")
            return None
    
    def 统一数据来源(self, 原始来源: str) -> str:
        """统一数据来源名称"""
        if not 原始来源:
            return "普通司法拍卖"
        if 'taobao.com' in 原始来源 or '淘宝' in 原始来源:
            return "淘宝司法拍卖"
        elif 'jd.com' in 原始来源 or '京东' in 原始来源:
            return "京东司法拍卖"
        else:
            return "普通司法拍卖"


class Excel生成器:
    """生成严格八列Excel数据的生成器"""
    
    def __init__(self, 高德api_key: str = ""):
        self.格式化器 = 输出格式化器(高德api_key)
    
    def 生成备注_from_case(self, case: Dict, mortgage_info: Dict, 
                            asset_type: str, sub_type: Optional[str] = None) -> str:
        """
        从内部case数据结构生成严格模板备注
        """
        # 物业类型
        物业类型 = self._获取物业类型(asset_type, sub_type, case)
        
        # 详细地址
        详细地址 = case.get("address", "") or case.get("title", "")[:50]
        
        # 拍卖记录
        拍卖记录 = self._构建拍卖记录(case)
        
        # 是否自身案例
        是否自身案例 = self.判断是否自身案例(mortgage_info, case, asset_type)
        
        案例信息 = {
            '物业类型': 物业类型,
            '详细地址': 详细地址,
            '拍卖记录': 拍卖记录,
            '是否自身案例': 是否自身案例,
            '抵押物地址': mortgage_info.get('address', ''),
            '案例地址': 详细地址,
            '抵押物坐标': self._转换坐标格式(mortgage_info.get('coordinates')),
            '案例坐标': self._转换坐标格式(case.get('coordinates'))
        }
        
        return self.格式化器.生成备注(案例信息)
    
    def _获取物业类型(self, asset_type: str, sub_type: Optional[str], case: Dict) -> str:
        """获取物业类型"""
        if asset_type == "住宅":
            return "住宅用房"
        elif asset_type == "商业":
            if sub_type:
                return self.格式化器.标准化物业类型(sub_type)
            return "商业用房"
        elif asset_type == "工业":
            if case.get("land_area") and not case.get("building_area"):
                return "工业用地"
            return "工业用房"
        elif asset_type == "土地":
            return sub_type if sub_type else "土地"
        return self.格式化器.标准化物业类型(asset_type)
    
    def _构建拍卖记录(self, case: Dict) -> List[Dict]:
        """从case数据构建拍卖记录（优先使用详情页数据）"""
        # 优先使用详情页获取的拍卖记录
        详情拍卖记录 = case.get("auction_records", [])
        if 详情拍卖记录 and isinstance(详情拍卖记录, list) and len(详情拍卖记录) > 0:
            增强记录 = []
            for 记录 in 详情拍卖记录:
                增强记录.append({
                    '轮次': 记录.get('轮次', case.get('auction_stage', '一拍')),
                    '日期': self._获取拍卖日期(case, 记录.get('轮次')),
                    '价格类型': 记录.get('价格类型', '起拍价'),
                    '价格': 记录.get('价格', 0),
                    '状态': 记录.get('状态', '已成交')
                })
            return 增强记录
        
        记录列表 = []
        
        # 解析状态
        status = str(case.get("status", ""))
        status_map = {
            'ing': '正在进行', '1': '正在进行', 'auctioning': '正在进行',
            'before': '即将开始', '0': '即将开始', 'pending': '即将开始',
            'end': '已成交', '2': '已成交', '3': '已成交', 'sold': '已成交', 'deal': '已成交',
            'failed': '正在进行流拍', '流拍': '正在进行流拍', 'fail': '变卖失败',
            '变卖失败': '变卖失败', '拍卖中': '正在进行', '已结束': '已成交', '待开拍': '即将开始',
        }
        状态文本 = status_map.get(status, '正在进行')
        
        # 拍卖轮次
        轮次 = case.get("auction_stage", case.get("拍卖轮次", "一拍"))
        
        # 日期（优先使用成交日期，其次是开始日期，最后是默认）
        日期 = self._获取拍卖日期(case, 轮次)
        
        # 价格（万元转元）
        start_price_wan = case.get("start_price", 0) or 0
        current_price_wan = case.get("current_price", 0) or 0
        deal_price_wan = case.get("deal_price", 0) or 0
        
        # 判断是否成交
        is_sold = status in ['3', '已成交', 'deal', 'sold', '2', 'end'] or deal_price_wan > 0 or case.get('deal_date') is not None
        
        # 起拍价记录
        if start_price_wan > 0:
            记录列表.append({
                '轮次': 轮次,
                '日期': 日期,
                '价格类型': '起拍价',
                '价格': start_price_wan * 10000,
                '状态': 状态文本
            })
        
        # 成交价记录
        if is_sold:
            成交价 = deal_price_wan if deal_price_wan > 0 else current_price_wan
            if 成交价 > 0:
                记录列表.append({
                    '轮次': 轮次,
                    '日期': 日期,
                    '价格类型': '成交价',
                    '价格': 成交价 * 10000,
                    '状态': '已成交'
                })
        
        return 记录列表 if 记录列表 else [{
            '轮次': 轮次,
            '日期': 日期,
            '价格类型': '起拍价',
            '价格': 0,
            '状态': 状态文本
        }]
    
    def _获取拍卖日期(self, case: Dict, 轮次: str = "") -> str:
        """获取拍卖日期，优先使用详情页提取的日期"""
        from datetime import datetime
        
        # 优先使用成交日期
        if case.get('deal_date'):
            deal_date = case['deal_date']
            if isinstance(deal_date, datetime):
                return deal_date.strftime("%Y-%m-%d")
            elif isinstance(deal_date, str) and len(deal_date) >= 10:
                return deal_date[:10]
        
        # 其次使用开始日期
        if case.get('start_date'):
            start_date = case['start_date']
            if isinstance(start_date, datetime):
                return start_date.strftime("%Y-%m-%d")
            elif isinstance(start_date, str) and len(start_date) >= 10:
                return start_date[:10]
        
        # 最后使用case中的date字段
        auction_date = case.get("date")
        if isinstance(auction_date, datetime):
            return auction_date.strftime("%Y-%m-%d")
        elif isinstance(auction_date, str) and len(auction_date) >= 10:
            return auction_date[:10]
        
        return "日期未知"
    
    def 判断是否自身案例(self, 抵押物信息: Dict, 案例信息: Dict, asset_type: str = "") -> bool:
        """判断是否自身案例：地址高度相似 + 面积高度相似"""
        抵押物地址 = 抵押物信息.get('address', '').replace(' ', '')
        案例地址 = (案例信息.get('address', '') or 案例信息.get('title', '')).replace(' ', '')
        
        地址相似 = False
        if 抵押物地址 and 案例地址:
            关键部分 = ['号楼', '单元', '室', '座', '栋']
            for 关键词 in 关键部分:
                if 关键词 in 抵押物地址 and 关键词 in 案例地址:
                    抵押物楼号 = self.提取楼号(抵押物地址)
                    案例楼号 = self.提取楼号(案例地址)
                    if 抵押物楼号 and 案例楼号 and 抵押物楼号 == 案例楼号:
                        地址相似 = True
                        break
            
            if not 地址相似:
                from case_search_enhanced import EnhancedCaseSearch
                searcher = EnhancedCaseSearch()
                is_self, _, _ = searcher.is_self_auction_case(抵押物信息, 案例信息)
                if is_self:
                    地址相似 = True
        
        面积相似 = False
        抵押物面积 = 抵押物信息.get('building_area', 0) or 抵押物信息.get('area', 0) or 0
        案例面积 = 案例信息.get('building_area', 0) or 0
        
        if isinstance(抵押物面积, (int, float)) and isinstance(案例面积, (int, float)):
            if 抵押物面积 > 0 and 案例面积 > 0:
                误差率 = abs(抵押物面积 - 案例面积) / 抵押物面积
                面积相似 = 误差率 < 0.2
        
        return 地址相似 and 面积相似
    
    def 提取楼号(self, 地址: str) -> Optional[str]:
        """从地址中提取楼号/单元号"""
        模式 = r'(\d+)[号楼单元室座栋]'
        匹配 = re.search(模式, 地址)
        return 匹配.group(1) if 匹配 else None
    
    def _转换坐标格式(self, coords) -> Optional[Dict]:
        """将tuple坐标转换为dict格式"""
        if coords and isinstance(coords, (tuple, list)) and len(coords) == 2:
            return {'lng': float(coords[0]), 'lat': float(coords[1])}
        if coords and isinstance(coords, dict):
            return coords
        return None
    
    def 统一数据来源(self, 原始来源: str) -> str:
        """统一数据来源"""
        return self.格式化器.统一数据来源(原始来源)
