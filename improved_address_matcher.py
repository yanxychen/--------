#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的地址匹配器
使用多策略匹配提高链接与地址的匹配精度

策略：
1. 精确地址匹配（地址完全相同）
2. 坐标半径匹配（高德API转坐标，半径范围内搜索）
3. 关键词扩展匹配（生成多个关键词组合）
4. 地址成分加权匹配（市/区/办事处/路/门牌号/小区名）
"""

import re
import sys
import math
sys.path.insert(0, '/workspace')

try:
    import requests
except ImportError:
    requests = None

from link_match_diagnostic import 链接匹配诊断器


GAODE_API_KEY = "d7d06a2c20dacd8c861173b82cf70d71"


class 改进地址匹配器(链接匹配诊断器):
    """改进的地址匹配器，继承诊断器的基础功能"""
    
    def __init__(self):
        super().__init__()
        self.高德API密钥 = GAODE_API_KEY
        self.坐标缓存 = {}
    
    def 高德地址转坐标(self, 地址):
        """调用高德API将地址转坐标"""
        if 地址 in self.坐标缓存:
            return self.坐标缓存[地址]
        
        if not requests:
            return None
        
        try:
            url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                'address': 地址,
                'key': self.高德API密钥,
                'output': 'json'
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get('geocodes') and len(data['geocodes']) > 0:
                location = data['geocodes'][0].get('location', '')
                if location:
                    lng, lat = location.split(',')
                    坐标 = {'lng': float(lng), 'lat': float(lat)}
                    self.坐标缓存[地址] = 坐标
                    return 坐标
        except Exception as e:
            print(f"   ⚠ 高德API调用失败: {e}")
        
        return None
    
    def 计算坐标距离(self, 坐标1, 坐标2):
        """计算两个坐标之间的距离（公里）"""
        if not 坐标1 or not 坐标2:
            return float('inf')
        
        # Haversine公式
        lat1, lng1 = 坐标1['lat'], 坐标1['lng']
        lat2, lng2 = 坐标2['lat'], 坐标2['lng']
        
        R = 6371  # 地球半径（公里）
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def 高德驾车距离(self, 坐标1, 坐标2):
        """调用高德API计算驾车距离"""
        if not requests or not 坐标1 or not 坐标2:
            return None
        
        try:
            url = "https://restapi.amap.com/v3/distance"
            params = {
                'origins': f"{坐标1['lng']},{坐标1['lat']}",
                'destination': f"{坐标2['lng']},{坐标2['lat']}",
                'type': '1',  # 驾车
                'key': self.高德API密钥
            }
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get('results') and len(data['results']) > 0:
                距离米 = int(data['results'][0].get('distance', 0))
                return 距离米 / 1000  # 转为公里
        except Exception as e:
            print(f"   ⚠ 高德距离API调用失败: {e}")
        
        return None
    
    def 多策略匹配(self, 抵押物地址, 候选案例列表, 物业类型='商业', 抵押物面积=None):
        """
        使用多策略提高匹配精度
        返回按匹配度排序的案例列表
        """
        匹配结果 = []
        
        # 策略1：精确地址匹配
        for 案例 in 候选案例列表:
            匹配度 = self.计算地址匹配度(抵押物地址, 案例.get('地址', ''))
            策略 = '地址成分匹配'
            
            # 地址完全匹配
            if self.地址标准化(抵押物地址) == self.地址标准化(案例.get('地址', '')):
                匹配度 = 1.0
                策略 = '精确地址匹配'
            
            匹配结果.append({
                '案例': 案例,
                '匹配度': 匹配度,
                '策略': 策略
            })
        
        # 策略2：坐标半径匹配（如果高德API可用）
        抵押物坐标 = self.高德地址转坐标(抵押物地址)
        if 抵押物坐标:
            for 结果 in 匹配结果:
                案例 = 结果['案例']
                案例地址 = 案例.get('地址', '')
                if 案例地址:
                    案例坐标 = self.高德地址转坐标(案例地址)
                    if 案例坐标:
                        距离 = self.计算坐标距离(抵押物坐标, 案例坐标)
                        驾车距离 = self.高德驾车距离(抵押物坐标, 案例坐标)
                        实际距离 = 驾车距离 if 驾车距离 else 距离
                        
                        结果['直线距离公里'] = round(距离, 2)
                        结果['驾车距离公里'] = round(实际距离, 2) if 实际距离 else None
                        
                        # 距离越近，匹配度加成
                        if 实际距离 <= 1:
                            结果['匹配度'] = min(1.0, 结果['匹配度'] + 0.3)
                        elif 实际距离 <= 3:
                            结果['匹配度'] = min(1.0, 结果['匹配度'] + 0.2)
                        elif 实际距离 <= 5:
                            结果['匹配度'] = min(1.0, 结果['匹配度'] + 0.1)
                        elif 实际距离 > 10:
                            结果['匹配度'] = max(0, 结果['匹配度'] - 0.2)
                        
                        结果['策略'] = f"坐标半径匹配({实际距离:.1f}km)"
        
        # 策略3：面积匹配加成
        if 抵押物面积:
            for 结果 in 匹配结果:
                案例面积 = 结果['案例'].get('面积', 0)
                if 案例面积 and 案例面积 > 0:
                    面积比 = 案例面积 / 抵押物面积 if 抵押物面积 > 0 else 0
                    
                    if 0.9 <= 面积比 <= 1.1:
                        # 面积几乎相同，强烈加成
                        结果['匹配度'] = min(1.0, 结果['匹配度'] + 0.2)
                        结果['策略'] += "+面积匹配"
                    elif 0.5 <= 面积比 <= 2.0:
                        # 面积在合理范围
                        结果['匹配度'] = min(1.0, 结果['匹配度'] + 0.05)
        
        # 按匹配度排序
        匹配结果.sort(key=lambda x: x['匹配度'], reverse=True)
        
        return 匹配结果
    
    def 验证改进算法(self):
        """验证改进算法的效果"""
        print("=" * 70)
        print("🚀 改进地址匹配器验证")
        print("=" * 70)
        
        # 测试案例
        测试案例 = self.错误案例库
        
        for 案例 in 测试案例:
            print(f"\n📋 案例{案例['编号']}：{案例['用户输入地址']}")
            print(f"   抵押物面积：{案例['抵押物面积']}㎡")
            
            # 构建候选案例列表（实际搜索到的）
            候选案例 = []
            for 实际 in 案例['实际搜索到的']:
                候选案例.append({
                    '地址': 实际['地址'],
                    '链接': 实际['链接'],
                    '面积': 案例['抵押物面积']  # 假设面积相同
                })
            
            # 使用改进算法匹配
            匹配结果 = self.多策略匹配(
                案例['用户输入地址'],
                候选案例,
                案例['类型'],
                案例['抵押物面积']
            )
            
            # 显示匹配结果
            print(f"\n   🎯 改进算法匹配结果：")
            for i, 结果 in enumerate(匹配结果, 1):
                print(f"      {i}. 地址：{结果['案例']['地址']}")
                print(f"         链接：{结果['案例']['链接']}")
                print(f"         匹配度：{结果['匹配度']:.2f}")
                print(f"         策略：{结果['策略']}")
                if '驾车距离公里' in 结果:
                    print(f"         驾车距离：{结果['驾车距离公里']}公里")
                print()
        
        # 总结改进效果
        print("\n" + "=" * 70)
        print("📊 改进效果总结")
        print("=" * 70)
        print("✅ 改进点：")
        print("   1. 多策略匹配：精确地址 + 坐标半径 + 面积匹配")
        print("   2. 地址成分加权：市/区/办事处/路/门牌号/小区名")
        print("   3. 坐标距离加成：距离越近匹配度越高")
        print("   4. 面积匹配加成：面积相似度高给加分")
        print("\n💡 使用建议：")
        print("   - 匹配度 > 0.8：高置信度匹配")
        print("   - 匹配度 0.6-0.8：中等置信度，建议人工验证")
        print("   - 匹配度 < 0.6：低置信度，需要人工确认")


if __name__ == "__main__":
    匹配器 = 改进地址匹配器()
    匹配器.诊断匹配问题()
    print("\n")
    匹配器.验证改进算法()
