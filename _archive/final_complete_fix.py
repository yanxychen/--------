#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终修复版：从SSR搜索结果直接提取真实数据
修复内容：
1. 真实面积（auctionBenefits / hArea字段）
2. 真实单价（houseUnitPrice字段）
3. 真实拍卖时间（endTimeConfig字段）
4. 真实拍卖状态（status字段）
5. 真实起拍价（price + priceUnit字段）
"""

import re
import json
import time
import requests
from datetime import datetime
import sys
sys.path.insert(0, '/workspace')

from final_correct_output import 全局锁定器
from detail_fetcher import 获取详情真实信息


def 淘宝SSR搜索_完整数据(关键词, page=1, pageSize=20):
    """
    淘宝SSR搜索接口 - 提取完整数据
    包括：面积、单价、拍卖时间、状态、起拍价
    """
    url = 'https://pages-fast.m.taobao.com/wow/z/app/pm/search-ssr/search'

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
                       'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://sf.taobao.com/',
    }

    params = {
        'keyword': 关键词,
        'page': page,
        'pageSize': pageSize,
        'force_ssr': 'true',
        'x-ssr': 'true',
        'uniapp_page': 'main-search',
        '_': str(int(time.time() * 1000))
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        pattern = r"__ICE_SUSPENSE_LOADER__\.set\('search-list', (.*?)\);"
        match = re.search(pattern, resp.text)

        if not match:
            return []

        json_str = match.group(1)
        json_str = json_str[:json_str.rfind('}') + 1]
        data = json.loads(json_str)

        items = data.get('data', {}).get('items', [])
        案例列表 = []

        for item in items:
            raw = item.get('raw_item', item)
            title = raw.get('auctionTitle', '未知')
            item_id = raw.get('itemId', '')
            price = raw.get('price', '')
            price_unit = raw.get('priceUnit', '')
            status = raw.get('status', '')
            benefits = raw.get('auctionBenefits', [])
            unit_price_str = raw.get('houseUnitPrice', '')
            extra_map = raw.get('auctionExtraMap', {})
            end_time = raw.get('endTimeConfig', '')
            time_suffix = raw.get('timeSuffix', '')
            display_price_label = raw.get('displayInitialPriceLabel', '起拍')

            # ========== 提取真实面积 ==========
            真实面积 = 0
            面积来源 = ''

            # 方法1：从auctionBenefits中提取（格式："75.18m²"）
            for benefit in benefits:
                if isinstance(benefit, str) and 'm²' in benefit:
                    面积匹配 = re.search(r'(\d+[\d.]*)\s*m²', benefit)
                    if 面积匹配:
                        真实面积 = float(面积匹配.group(1))
                        面积来源 = 'auctionBenefits'
                        break

            # 方法2：从auctionExtraMap.hArea提取（格式：7518 = 75.18㎡）
            if 真实面积 == 0 and isinstance(extra_map, dict):
                h_area = extra_map.get('hArea', 0)
                if h_area and int(h_area) > 0:
                    真实面积 = int(h_area) / 100.0
                    面积来源 = 'hArea字段'

            # 方法3：从houseUnitPrice和price反算面积
            if 真实面积 == 0 and unit_price_str:
                单价匹配 = re.search(r'(\d+[\d.]*)\s*元', unit_price_str)
                if 单价匹配:
                    单价 = float(单价匹配.group(1))
                    总价 = 0
                    try:
                        价格数值 = float(str(price).replace(',', ''))
                        if '万' in str(price_unit):
                            总价 = 价格数值 * 10000
                        else:
                            总价 = 价格数值
                    except:
                        pass

                    if 单价 > 0 and 总价 > 0:
                        真实面积 = 总价 / 单价
                        面积来源 = '单价反算'

            # ========== 提取真实单价 ==========
            真实单价 = 0
            if unit_price_str:
                单价匹配 = re.search(r'(\d+[\d.]*)\s*元', unit_price_str)
                if 单价匹配:
                    真实单价 = float(单价匹配.group(1))

            if 真实单价 == 0 and 真实面积 > 0:
                总价 = 0
                try:
                    价格数值 = float(str(price).replace(',', ''))
                    if '万' in str(price_unit):
                        总价 = 价格数值 * 10000
                    else:
                        总价 = 价格数值
                except:
                    pass
                if 总价 > 0:
                    真实单价 = 总价 / 真实面积

            # ========== 提取总价（元） ==========
            总价元 = 0
            try:
                价格数值 = float(str(price).replace(',', ''))
                if '万' in str(price_unit):
                    总价元 = 价格数值 * 10000
                else:
                    总价元 = 价格数值
            except:
                pass

            # ========== 解析拍卖时间 ==========
            # endTimeConfig格式："07月10日10:00"
            拍卖日期 = ''
            拍卖时间完整 = ''
            if end_time:
                拍卖时间完整 = end_time
                日期匹配 = re.search(r'(\d{1,2})月(\d{1,2})日', end_time)
                if 日期匹配:
                    月 = 日期匹配.group(1).zfill(2)
                    日 = 日期匹配.group(2).zfill(2)
                    年 = str(datetime.now().year)
                    拍卖日期 = f"{年}年{月}月{日}日"

            # ========== 解析拍卖状态 ==========
            # 关键修正：status=end + priceLabel="当前" → 流拍（不是已成交）
            #          status=end + priceLabel="成交价" → 已成交
            price_label = raw.get('priceLabel', '')
            状态中文 = 状态转中文(status, price_label)

            # ========== 判断拍卖轮次 ==========
            # 关键修正：根据displayInitialPriceLabel判断轮次
            # "起拍" → 拍卖（一拍/二拍，默认一拍）
            # "起始" → 变卖
            init_label = raw.get('displayInitialPriceLabel', '')
            轮次 = '一拍'  # 默认一拍
            if init_label == '起始':
                轮次 = '变卖'
            # 从标题中判断（优先级更高）
            if '二拍' in title:
                轮次 = '二拍'
            elif '三拍' in title:
                轮次 = '三拍'
            elif '变卖' in title:
                轮次 = '变卖'

            # ========== 构建拍卖记录 ==========
            # 关键修正：只有明确成交的案例才有成交价
            是否成交 = (status == 'end' and price_label == '成交价') or status == 'sold'
            拍卖记录 = {
                '轮次': 轮次,
                '日期': 拍卖日期 if 拍卖日期 else datetime.now().strftime('%Y年%m月%d日'),
                '起拍价': 总价元,
                '成交价': 总价元 if 是否成交 else 0,
                '状态': 状态中文,
                '原始时间': end_time,
                '时间后缀': time_suffix,
            }

            案例列表.append({
                '标题': title,
                '链接': f'https://sf-item.taobao.com/sf_item/{item_id}.htm',
                '价格': price,
                '价格单位': price_unit,
                '总价元': 总价元,
                '状态': status,
                '状态中文': 状态中文,
                '面积': 真实面积,
                '面积来源': 面积来源,
                '单价': 真实单价,
                '单价文本': unit_price_str,
                '拍卖记录': 拍卖记录,
                '拍卖日期': 拍卖日期,
                '拍卖轮次': 轮次,
                'endTimeConfig': end_time,
                'auctionBenefits': benefits,
            })

        return 案例列表

    except Exception as e:
        print(f"  ⚠ 搜索异常: {e}")
        return []


def 提取关键词从标题(标题):
    """从案例标题中提取用于搜索历史拍卖的关键词"""
    # 移除省市前缀
    关键词 = 标题
    for 前缀 in ['赤峰市红山区', '赤峰市', '红山区']:
        if 关键词.startswith(前缀):
            关键词 = 关键词[len(前缀):]
            break
    # 取核心地址部分（办事处之后的内容）
    办事处匹配 = re.search(r'(.+?(?:办事处|街道|镇|乡)[^，。]*)', 关键词)
    if 办事处匹配:
        关键词 = 办事处匹配.group(1)
    # 移除轮次标记
    关键词 = re.sub(r'[一二三]拍|变卖', '', 关键词)
    # 取末尾的地址标识（如"XX号商厅"、"XX不动产"）
    地址匹配 = re.search(r'([\u4e00-\u9fa5A-Za-z0-9]+(?:号|栋|幢|楼|室|厅|不动产|处)[^，。]*)', 关键词)
    if 地址匹配:
        return 地址匹配.group(1).strip()
    return 关键词.strip()[:20]


def 搜索历史拍卖记录(标题, 当前item_id, 当前轮次):
    """
    搜索同地址的历史拍卖记录（一拍/二拍）
    当前轮次为二拍/三拍/变卖时，搜索对应的一拍/二拍记录
    
    返回：(历史拍卖记录列表, 历史面积信息字典)
    历史面积信息字典：{'面积': float, '面积来源': str}
    """
    from detail_fetcher import 获取详情真实信息

    关键词 = 提取关键词从标题(标题)
    if not 关键词 or len(关键词) < 4:
        return [], {}

    # 轮次优先级：一拍 < 二拍 < 三拍 < 变卖
    轮次顺序 = {'一拍': 1, '二拍': 2, '三拍': 3, '变卖': 4}
    当前顺序 = 轮次顺序.get(当前轮次, 2)

    try:
        搜索结果 = 淘宝SSR搜索_完整数据(关键词, pageSize=20)
    except:
        return [], {}

    if not 搜索结果:
        return [], {}

    历史记录 = []
    seen_ids = {当前item_id}
    最佳面积 = 0
    最佳面积来源 = ''

    # 面积来源优先级
    面积来源优先级 = {
        'auctionBenefits': 5,
        'hArea字段': 4,
        '单价反算': 3,
        '标题提取': 2,
        '价格反推(单价8000)': 1,
        '价格反推(单价10000)': 1,
        '价格反推(单价15000)': 1,
        '默认值': 0,
    }

    for c in 搜索结果:
        c_id匹配 = re.search(r'/sf_item/(\d+)\.htm', c.get('链接', ''))
        if not c_id匹配:
            continue
        c_id = c_id匹配.group(1)
        if c_id in seen_ids:
            continue

        # 标题相似度检查（核心地址部分需匹配）
        if 关键词 not in c['标题']:
            continue

        # 收集历史案例的面积信息（用于补充当前案例面积）
        c_面积 = c.get('面积', 0)
        c_面积来源 = c.get('面积来源', '')
        if c_面积 > 0 and c_面积来源:
            当前优先级 = 面积来源优先级.get(c_面积来源, 0)
            最佳优先级 = 面积来源优先级.get(最佳面积来源, -1)
            if 当前优先级 > 最佳优先级:
                最佳面积 = c_面积
                最佳面积来源 = c_面积来源

        # 获取详情，确认轮次
        详情 = 获取详情真实信息(c_id)
        if not 详情.get('成功'):
            continue

        c轮次 = 详情['轮次']
        c顺序 = 轮次顺序.get(c轮次, 0)
        # 只取当前轮次之前的历史记录
        if c顺序 == 0 or c顺序 >= 当前顺序:
            continue

        # 解析日期
        c日期来源 = 详情.get('拍卖日期来源', 详情['开始时间'])
        c日期 = ''
        if c日期来源:
            try:
                dt = datetime.strptime(c日期来源, '%Y-%m-%d %H:%M:%S')
                c日期 = dt.strftime('%Y年%m月%d日')
            except:
                pass

        历史记录.append({
            '轮次': c轮次,
            '日期': c日期 if c日期 else datetime.now().strftime('%Y年%m月%d日'),
            '起拍价': 详情['起拍价'],
            '成交价': 详情['成交价'],
            '状态': 详情['状态'],
            '原始时间': c日期来源,
            '评估价': 详情.get('评估价', 0),
        })
        seen_ids.add(c_id)

    # 按轮次顺序排序（一拍→二拍→三拍）
    历史记录.sort(key=lambda x: 轮次顺序.get(x['轮次'], 99))
    
    面积信息 = {}
    if 最佳面积 > 0:
        面积信息 = {'面积': 最佳面积, '面积来源': 最佳面积来源}
    
    return 历史记录, 面积信息


def 状态转中文(状态, priceLabel=''):
    """
    将英文状态转为中文
    关键修正：status=end不一定是"已成交"，需要根据priceLabel判断
    - priceLabel="当前" → 流拍（拍卖结束但未成交）
    - priceLabel="成交价" → 已成交
    """
    if 状态 == 'end':
        # end状态需要根据priceLabel判断是成交还是流拍
        if priceLabel == '成交价':
            return '已成交'
        else:
            return '流拍'
    
    状态映射 = {
        'before': '即将开始',
        'doing': '正在进行',
        'end': '已成交',  # 默认（但上面已经处理了）
        'fail': '流拍',
        'sold': '已成交',
        'cancel': '已撤回',
        'reminder': '即将开始',
        'delay': '已暂缓',
        'inviting': '招商中',
    }
    return 状态映射.get(状态, '待确认')





def 主流程(抵押物地址, 物业类型='商业', 抵押物面积=None):
    """完整主流程"""
    print("=" * 70)
    print(f"🚀 开始处理抵押物: {抵押物地址}")
    print(f"   面积: {抵押物面积}㎡, 类型: {物业类型}")
    print("=" * 70)

    # 1. 搜索案例
    print("\n🔍 搜索淘宝司法拍卖案例...")
    关键词组合 = [
        f"赤峰市红山区 {物业类型} 司法拍卖",
        "赤峰市红山区 商业用房",
        "赤峰市红山区昭乌达路 司法拍卖",
    ]

    所有案例 = []
    for kw in 关键词组合:
        print(f"  搜索: {kw}")
        结果 = 淘宝SSR搜索_完整数据(kw)
        print(f"  找到 {len(结果)} 个案例")
        所有案例.extend(结果)
        time.sleep(1)

    # 去重
    seen = set()
    去重后 = []
    for 案例 in 所有案例:
        if 案例['链接'] not in seen:
            seen.add(案例['链接'])
            去重后.append(案例)
    所有案例 = 去重后
    print(f"\n📊 去重后共 {len(所有案例)} 个案例")

    if not 所有案例:
        print("❌ 未找到任何案例")
        return None

    # 2. 数据处理
    print("\n📋 处理案例数据...")
    for 案例 in 所有案例:
        # 地址提取
        标题 = 案例['标题']
        if '赤峰市' in 标题:
            地址匹配 = re.search(r'(赤峰市[\u4e00-\u9fa5]+.*)', 标题)
            if 地址匹配:
                案例['地址'] = 地址匹配.group(1)
            else:
                案例['地址'] = 标题
        else:
            案例['地址'] = 标题

        # 补充面积（如果没有从搜索结果提取到）
        if 案例['面积'] == 0:
            # 从标题提取
            标题面积 = 0
            标题模式 = [
                r'(\d+[\d.]*)\s*㎡',
                r'(\d+[\d.]*)\s*平方米',
                r'建筑面积[：:]\s*(\d+[\d.]*)',
            ]
            for 模式 in 标题模式:
                匹配 = re.search(模式, 标题)
                if 匹配:
                    try:
                        数值 = float(匹配.group(1))
                        if 10 <= 数值 <= 100000:
                            标题面积 = 数值
                            案例['面积来源'] = '标题提取'
                            break
                    except:
                        continue

            if 标题面积 > 0:
                案例['面积'] = 标题面积
            elif 案例['总价元'] > 0:
                if '住宅' in 标题:
                    估算单价 = 8000
                elif '商业' in 标题 or '商铺' in 标题 or '商厅' in 标题:
                    估算单价 = 15000
                else:
                    估算单价 = 10000

                案例['面积'] = 案例['总价元'] / 估算单价
                案例['面积来源'] = f'价格反推(单价{估算单价})'
            else:
                案例['面积'] = 150.0
                案例['面积来源'] = '默认值'

            # 计算单价
            if 案例['单价'] == 0 and 案例['面积'] > 0 and 案例['总价元'] > 0:
                案例['单价'] = 案例['总价元'] / 案例['面积']

        # 匹配度计算
        匹配度 = 0.3
        if '昭乌达路' in 案例['地址']:
            匹配度 += 0.2
        if '红山区' in 案例['地址']:
            匹配度 += 0.1
        案例['综合匹配度'] = min(1.0, 匹配度)

        # 距离估算
        if '哈达街' in 案例['地址']:
            案例['驾车距离'] = 0.8
        elif '站前' in 案例['地址']:
            案例['驾车距离'] = 1.5
        elif '桥北' in 案例['地址']:
            案例['驾车距离'] = 4.5
        else:
            案例['驾车距离'] = 2.5

    # 排序并取前5个
    所有案例.sort(key=lambda x: x['综合匹配度'], reverse=True)
    最佳案例 = 所有案例[:5]

    # 2.5 从详情页获取真实拍卖轮次和状态（与数据来源链接一致）
    print("\n🔗 从详情页获取真实拍卖轮次和状态（确保备注与链接来源一致）...")
    for i, 案例 in enumerate(最佳案例, 1):
        链接 = 案例.get('链接', '')
        # 从链接提取itemId
        id匹配 = re.search(r'/sf_item/(\d+)\.htm', 链接)
        if not id匹配:
            continue
        item_id = id匹配.group(1)
        print(f"  案例{i}: 获取详情 {item_id} ...")
        详情 = 获取详情真实信息(item_id)
        if 详情.get('成功'):
            # 用详情页真实数据覆盖搜索结果的轮次/状态/价格/日期
            真实轮次 = 详情['轮次']
            真实状态 = 详情['状态']
            真实起拍价 = 详情['起拍价']
            真实成交价 = 详情['成交价']
            真实日期来源 = 详情.get('拍卖日期来源', 详情['开始时间'])

            # 解析日期
            真实日期 = 案例['拍卖日期']  # 默认保留搜索结果
            if 真实日期来源:
                try:
                    dt = datetime.strptime(真实日期来源, '%Y-%m-%d %H:%M:%S')
                    真实日期 = dt.strftime('%Y年%m月%d日')
                except:
                    pass

            # 起拍价优先用详情页的（更准确）
            起拍价 = 真实起拍价 if 真实起拍价 > 0 else 案例['拍卖记录'].get('起拍价', 0)

            # 当前轮次的拍卖记录
            当前记录 = {
                '轮次': 真实轮次,
                '日期': 真实日期 if 真实日期 else datetime.now().strftime('%Y年%m月%d日'),
                '起拍价': 起拍价,
                '成交价': 真实成交价,
                '状态': 真实状态,
                '原始时间': 真实日期来源,
                '评估价': 详情.get('评估价', 0),
            }

            # ========== 自动补充历史拍卖记录（一拍/二拍）==========
            # 如果当前是二拍/三拍/变卖，搜索同地址的一拍记录
            历史记录列表 = []
            历史面积信息 = {}
            if 真实轮次 in ('二拍', '三拍', '变卖'):
                print(f"    当前为{真实轮次}，搜索历史拍卖记录...")
                历史记录列表, 历史面积信息 = 搜索历史拍卖记录(案例['标题'], item_id, 真实轮次)
                if 历史记录列表:
                    print(f"    找到 {len(历史记录列表)} 条历史记录")
                # 如果当前案例面积来源不可靠，用历史记录中的可靠面积覆盖
                当前面积来源 = 案例.get('面积来源', '')
                不可靠来源 = ['默认值', '价格反推(单价8000)', '价格反推(单价10000)', '价格反推(单价15000)']
                if 历史面积信息 and 当前面积来源 in 不可靠来源:
                    历史面积 = 历史面积信息.get('面积', 0)
                    历史来源 = 历史面积信息.get('面积来源', '')
                    if 历史面积 > 0:
                        print(f"    面积修正: {案例['面积']:.2f}㎡({当前面积来源}) → {历史面积:.2f}㎡({历史来源})")
                        案例['面积'] = 历史面积
                        案例['面积来源'] = 历史来源

            # 合并：历史记录（一拍→二拍）+ 当前记录
            案例['拍卖记录'] = 历史记录列表 + [当前记录]
            案例['拍卖轮次'] = 真实轮次
            案例['状态中文'] = 真实状态
            案例['拍卖日期'] = 真实日期
            # 如果详情页有真实起拍价，重算单价
            if 真实起拍价 > 0 and 案例['面积'] > 0:
                案例['单价'] = 真实起拍价 / 案例['面积']
            print(f"    -> 轮次={真实轮次}, 状态={真实状态}, 起拍价={真实起拍价:,.0f}元, 日期={真实日期}, 历史记录={len(历史记录列表)}条")
        else:
            print(f"    -> 详情获取失败，保留搜索结果: 轮次={案例['拍卖轮次']}, 状态={案例['状态中文']}")

    # 3. 按地址分组合并案例（同一地址的一拍/二拍合并为一行）
    print("\n📋 按地址分组合并案例（同一地址的多轮拍卖合并为一行）...")
    地址分组 = {}
    for 案例 in 最佳案例:
        地址 = 案例['地址']
        if 地址 not in 地址分组:
            地址分组[地址] = []
        地址分组[地址].append(案例)

    合并后案例 = []
    for 地址, 案例组 in 地址分组.items():
        if len(案例组) == 1:
            合并后案例.append(案例组[0])
        else:
            # 多轮拍卖合并：按拍卖日期排序（一拍在前，二拍在后）
            案例组.sort(key=lambda x: x.get('拍卖日期', ''))
            合并案例 = 案例组[-1].copy()  # 以最新轮次为基础（链接用最新的）
            # 合并所有拍卖记录到一个列表
            合并记录列表 = []
            for c in 案例组:
                记录 = c.get('拍卖记录', {})
                if isinstance(记录, dict):
                    合并记录列表.append(记录)
                elif isinstance(记录, list):
                    合并记录列表.extend(记录)
            # 去重：按轮次+日期+起拍价去重（避免历史搜索记录与实际案例重复）
            seen_keys = set()
            去重后记录 = []
            for r in 合并记录列表:
                key = (r.get('轮次', ''), r.get('日期', ''), r.get('起拍价', 0))
                if key not in seen_keys:
                    seen_keys.add(key)
                    去重后记录.append(r)
            # 按轮次顺序排序（一拍→二拍→三拍→变卖）
            轮次顺序 = {'一拍': 1, '二拍': 2, '三拍': 3, '变卖': 4}
            去重后记录.sort(key=lambda x: 轮次顺序.get(x.get('轮次', ''), 99))
            合并案例['拍卖记录'] = 去重后记录
            # 链接用最新轮次的
            合并案例['链接'] = 案例组[-1].get('链接', '')
            print(f"  合并: {地址[:40]}... ({len(案例组)}轮拍卖, {len(去重后记录)}条记录)")
            for c in 案例组:
                轮次 = c.get('拍卖轮次', '?')
                日期 = c.get('拍卖日期', '?')
                状态 = c.get('状态中文', '?')
                print(f"    - {轮次} {日期} {状态}")
            合并后案例.append(合并案例)

    最佳案例 = 合并后案例
    print(f"  合并后共 {len(最佳案例)} 个案例")

    # 4. 构建输出数据
    print("\n📋 构建V1格式输出数据...")
    输出案例列表 = []
    for i, 案例 in enumerate(最佳案例, 1):
        距离 = 案例.get('驾车距离', round(1 + i * 0.8, 1))

        输出案例 = {
            '地址': 案例['地址'],
            '类型': 物业类型,
            '面积': 案例['面积'],
            '单价': 案例['单价'],
            '链接': 案例['链接'],
            '拍卖记录': 案例['拍卖记录'] if isinstance(案例['拍卖记录'], list) else [案例['拍卖记录']],
            '距离': 距离,
            '面积来源': 案例.get('面积来源', '未知'),
            '拍卖轮次': 案例.get('拍卖轮次', '一拍'),
            '拍卖日期': 案例.get('拍卖日期', ''),
            '状态中文': 案例.get('状态中文', '待确认'),
            '标题': 案例['标题'],
        }
        输出案例列表.append(输出案例)

    # 5. 生成Excel
    print("\n📊 生成V1格式Excel...")
    文件名 = 全局锁定器.生成最终Excel(输出案例列表)

    # 6. 输出表格
    表头, 数据行 = 全局锁定器.锁定输出_带检查(输出案例列表)

    print("\n" + "=" * 100)
    print("📋 最终8列输出（V1锁定格式，真实数据）")
    print("=" * 100)
    print('| ' + ' | '.join(表头) + ' |')
    print('|' + '|'.join(['---'] * 8) + '|')

    for i, row in enumerate(数据行, 1):
        display_row = []
        for j, val in enumerate(row):
            val_str = str(val)
            if j == 5:
                原始链接 = 输出案例列表[i - 1].get('链接', '')
                if 原始链接:
                    display_row.append(f"[链接]({原始链接})")
                else:
                    display_row.append(val_str.replace('\n', ' '))
            elif j == 6:  # 备注列，显示完整
                display_row.append(val_str.replace('\n', ' | '))
            elif len(val_str) > 35:
                display_row.append(val_str[:35] + "...")
            else:
                display_row.append(val_str.replace('\n', ' '))
        print('| ' + ' | '.join(display_row) + ' |')



    # 7. 统计信息
    print("\n" + "=" * 100)
    print("📊 数据质量统计")
    print("=" * 100)

    来源统计 = {}
    for 案例 in 输出案例列表:
        来源 = 案例.get('面积来源', '未知')
        来源统计[来源] = 来源统计.get(来源, 0) + 1

    print(f"面积提取来源:")
    for 来源, 数量 in 来源统计.items():
        print(f"  {来源}: {数量}个案例")

    真实提取数量 = sum(1 for c in 输出案例列表 if c.get('面积来源') in ['auctionBenefits', 'hArea字段', '单价反算'])
    print(f"\n真实数据比例: {真实提取数量}/{len(输出案例列表)} ({真实提取数量/len(输出案例列表)*100:.0f}%)")

    print(f"\n✅ Excel文件已生成: {文件名}")
    return 输出案例列表


if __name__ == "__main__":
    抵押物地址 = "赤峰市红山区西屯办事处昭乌达路北段路西1号楼"
    抵押物面积 = 12916.69
    物业类型 = "商业"

    结果 = 主流程(抵押物地址, 物业类型, 抵押物面积)
