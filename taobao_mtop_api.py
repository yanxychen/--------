#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝司法拍卖 MTOP API 破解版
- 搜索：移动端SSR页面（已有）
- 详情：MTOP网关 mtop.taobao.gov.auction.third.detail.get
- 签名：MD5(_m_h5_tk + & + timestamp + & + appKey + & + data)
"""

import requests
import time
import hashlib
import json
import re

MTOP_APP_KEY = '12574478'
MTOP_DOMAIN = 'https://h5api.m.taobao.com'
MTOP_DETAIL_API = 'mtop.taobao.gov.auction.third.detail.get'


def get_mtop_token(session: requests.Session) -> str:
    """从h5api获取 _m_h5_tk token"""
    # 请求h5api域名，cookie会在Set-Cookie中返回
    session.get(
        'https://h5api.m.taobao.com/h5/mtop.taobao.gov.auction.third.detail.get/1.0/',
        params={'jsv': '2.7.2', 'appKey': MTOP_APP_KEY, 't': '1', 'v': '1.0'},
        timeout=10
    )
    token_cookie = session.cookies.get('_m_h5_tk', domain='.taobao.com') or \
                   session.cookies.get('_m_h5_tk', domain='taobao.com')
    if token_cookie and '_' in token_cookie:
        return token_cookie.split('_')[0]
    return ''


def mtop_sign(token: str, timestamp: str, data: str) -> str:
    """MTOP签名: MD5(token + & + timestamp + & + appKey + & + data)"""
    raw = f"{token}&{timestamp}&{MTOP_APP_KEY}&{data}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_taobao_detail_mtop(item_id: str) -> dict:
    """通过MTOP API获取淘宝拍卖详情"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) '
                      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    })

    # 1. 获取token
    token = get_mtop_token(session)
    if not token:
        return {'success': False, 'error': '获取token失败'}

    # 2. 构造请求参数
    timestamp = str(int(time.time() * 1000))
    # type=1 表示司法拍卖详情
    data = json.dumps({
        "itemId": item_id,
        "type": 1  # 1=司法拍卖, 2=资产拍卖?
    }, separators=(',', ':'))
    
    sign = mtop_sign(token, timestamp, data)

    params = {
        'jsv': '2.7.2',
        'appKey': MTOP_APP_KEY,
        't': timestamp,
        'sign': sign,
        'api': MTOP_DETAIL_API,
        'v': '1.0',
        'data': data,
        'type': 'jsonp',
    }

    resp = session.get(f"{MTOP_DOMAIN}/h5/{MTOP_DETAIL_API}/1.0/", params=params, timeout=20)
    
    return parse_mtop_response(resp.text, item_id)


def parse_mtop_response(raw: str, item_id: str) -> dict:
    """解析MTOP返回的数据（支持callback/jsonp两种格式）"""
    result = {
        'item_id': item_id, 'success': False,
        'building_area': 0.0, 'start_price': 0.0,
        'consult_price': 0.0, 'deal_price': 0.0,
        'address': '', 'status': '', 'current_stage': '',
        'title': '', 'land_area': 0.0, 'start_date': '',
    }
    
    # 剥离外壳: callback({...}) 或 mtopjsonp1({...}) 或 {...}
    json_match = re.search(r'(?:callback|mtopjsonp\d*)\s*\(\s*(\{.*\})\s*\)\s*;?\s*$', raw, re.DOTALL)
    if json_match:
        raw_json = json_match.group(1)
    else:
        raw_json = raw.strip()
    
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        result['error'] = f'JSON解析失败: {e}'
        return result
    
    if data.get('ret'):
        ret_str = str(data['ret'])
        if 'SUCCESS' not in ret_str:
            result['error'] = ret_str
            return result
    
    # data字段可能在 data.data 或 data.data.result 下
    detail = data.get('data', {})
    detail_data = detail.get('data', detail) if isinstance(detail, dict) else detail
    
    # 字段提取（适配多种命名）
    result['title'] = detail_data.get('title', '') or detail_data.get('itemTitle', '')
    result['address'] = detail_data.get('address', '') or detail_data.get('location', '') or detail_data.get('loc', '')
    result['status'] = detail_data.get('statusDesc', '') or detail_data.get('status', '')
    result['current_stage'] = detail_data.get('round', '') or detail_data.get('currentRound', '')
    result['start_date'] = (detail_data.get('startTime', '') or detail_data.get('startDate', '') or '')[:19]
    
    # 面积
    for f in ['buildingArea', 'area', 'estateArea', 'structureArea', 'constructArea']:
        v = detail_data.get(f)
        if v: 
            try: result['building_area'] = float(v); break
            except: pass
    
    for f in ['landArea', 'landAreaSize', 'landUseArea']:
        v = detail_data.get(f)
        if v:
            try: result['land_area'] = float(v); break
            except: pass
    
    # 价格（MTOP返回单位是分，÷100转为元）
    for f in ['startPrice', 'currentPrice', 'initialPrice', 'reservePrice']:
        v = detail_data.get(f)
        if v:
            try: result['start_price'] = round(float(v) / 100, 2); break
            except: pass
    
    for f in ['consultPrice', 'appraisalPrice', 'evaluationPrice', 'assessedPrice']:
        v = detail_data.get(f)
        if v:
            try: result['consult_price'] = round(float(v) / 100, 2); break
            except: pass
    
    for f in ['dealPrice', 'finalPrice', 'hammerPrice', 'transactionPrice']:
        v = detail_data.get(f)
        if v:
            try: result['deal_price'] = round(float(v) / 100, 2); break
            except: pass
    
    result['success'] = bool(result['title'] or result['building_area'] > 0 or result['start_price'] > 0)
    return result


if __name__ == '__main__':
    import sys
    item_id = sys.argv[1] if len(sys.argv) > 1 else '1062933060280'
    print(f"正在通过MTOP API获取 {item_id} ...")
    result = get_taobao_detail_mtop(item_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result['success']:
        print(f"\n✅ 抓取成功！起拍价: {result['start_price']} 元")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")
