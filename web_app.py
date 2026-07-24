#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值参考案例搜索工具 - 后端API (Render兼容版)

适配前端 searchService.ts 的接口契约：
- POST /api/search → {status, top3, all_cases, self_auction_count, total_count}
- GET /api/health → {status, timestamp}
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TAOBAO_CHROME_FETCHER_DIR = r"D:\宝宝课程资料"
if os.path.exists(TAOBAO_CHROME_FETCHER_DIR) and TAOBAO_CHROME_FETCHER_DIR not in sys.path:
    sys.path.insert(0, TAOBAO_CHROME_FETCHER_DIR)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# CORS 支持 - 允许浏览器直接调用后端
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, ngrok-skip-browser-warning'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

@app.route('/api/search', methods=['OPTIONS'])
@app.route('/api/valuate', methods=['OPTIONS'])
@app.route('/api/health', methods=['OPTIONS'])
@app.route('/api/export', methods=['OPTIONS'])
def cors_preflight():
    resp = app.make_response(('', 204))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, ngrok-skip-browser-warning'
    resp.headers['Access-Control-Max-Age'] = '86400'
    return resp

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


def map_raw_to_v1(raw_item, platform, index):
    """
    将原始搜索结果映射为前端 convertPythonCaseToCase 能识别的 V1 格式字段名。
    前端 converter 支持多种字段名变体，这里同时提供 V1 中文名和英文名。
    """
    title = raw_item.get('title', '')
    address = raw_item.get('address', '')
    link = raw_item.get('link', '')
    item_id = raw_item.get('item_id', '')
    source_text = '京东拍卖' if platform == 'jd' else '淘宝司法拍卖'
    
    # ★ 链接修复：无效链接→生成平台搜索链接
    if not link or link.endswith('?id=') or link.endswith('?id') or link == '':
        title = raw_item.get('title', '')
        search_kw = title[:30] if title else raw_item.get('address', '')[:30]
        if search_kw:
            from urllib.parse import quote_plus
            encoded = quote_plus(search_kw)
            if platform == 'jd':
                link = f'https://auction.jd.com/s/list.html?keyword={encoded}'
            else:
                link = f'https://sf.taobao.com/item/list.htm?q={encoded}'
        elif item_id:
            link = f'https://sf.taobao.com/sf_item/{item_id}.htm'

    # 价格处理
    current_price = raw_item.get('current_price', '')
    start_price = raw_item.get('start_price', '')

    # 尝试从价格字符串提取数值
    def parse_price_str(p):
        if not p:
            return 0.0
        try:
            # 去掉单位文字
            s = str(p).replace('万元', '').replace('万', '').replace('元', '')
            s = s.replace(',', '').replace('，', '').strip()
            val = float(s)
            if '万' in str(p):
                val *= 10000
            return val
        except:
            return 0.0

    price_val = parse_price_str(current_price)
    start_price_val = parse_price_str(start_price)

    # 面积
    # 优先从 title 中提取（很多标题直接包含"建筑面积XX㎡"）
    title = raw_item.get('title', '')
    building_area = 0.0
    title_area = re.search(r'建筑面积[：:]?\s*([\d,]+\.?\d*)\s*[㎡平方米]', title)
    if not title_area:
        title_area = re.search(r'([\d,]+\.?\d*)\s*[㎡平方米]', title)
    if title_area:
        try:
            building_area = float(title_area.group(1).replace(',', ''))
        except:
            pass
    # 如果 title 没有，从 area 字段提取
    if not building_area:
        area_str = raw_item.get('area', '')
        if area_str:
            try:
                s = str(area_str).replace('㎡', '').replace('平方米', '').replace('平', '').replace(',', '').strip()
                building_area = float(s)
            except:
                pass

    # 单价（如果有总价和面积，计算单价）
    unit_price = 0.0
    if price_val > 0 and building_area > 0:
        unit_price = price_val / building_area

    # 市场价值（万元） - 用起拍价或当前价估算
    market_value_wan = 0.0
    if price_val > 0:
        market_value_wan = price_val / 10000  # 转万元
    elif start_price_val > 0:
        market_value_wan = start_price_val / 10000

    # 参照物位置：用标题或地址
    ref_location = title if title else address

    # 备注
    remark_parts = []
    if start_price_val > 0:
        remark_parts.append(f"起拍价：{start_price_val:,.0f}元")
    if price_val > 0 and price_val != start_price_val:
        remark_parts.append(f"当前价：{price_val:,.0f}元")
    remark = '；'.join(remark_parts) if remark_parts else ''

    # 拍卖轮次
    auction_records = []
    stage = raw_item.get('current_stage', '') or raw_item.get('stage', '')
    status = raw_item.get('status', '')
    if stage or status:
        auction_records.append({
            'round': stage or '一拍',
            'date': '',
            'startPrice': start_price_val,
            'endPrice': price_val if status in ['已成交', '成交成功'] else 0,
            'status': status or '未知',
        })

    # 构建返回对象 - 同时提供 V1 中文字段名和英文字段名
    # 前端 convertPythonCaseToCase 会按优先级尝试各种字段名
    v1_case = {
        # V1 中文格式字段（前端 converter 的主要识别格式）
        '参照物位置': ref_location,
        '建筑面积(m²)': str(building_area) if building_area > 0 else '不适用',
        '土地面积(m²)': '不适用',
        '市场价值(万元)': str(round(market_value_wan, 2)) if market_value_wan > 0 else '不适用',
        '建筑单价(元/㎡)': str(round(unit_price, 2)) if unit_price > 0 else '不适用',
        '数据来源': link,  # ★ 完整URL（V1格式：数据来源存的是URL）
        '数据来源_链接': link,
        '备注': remark,
        '价格类型': '普通司法拍卖',

        # 英文字段名（前端 converter 的备用识别格式）
        'referenceLocation': ref_location,
        'buildingArea': building_area,
        'building_area': building_area,
        'land_area': 0,
        'marketValue': market_value_wan,
        'market_value': market_value_wan,
        'unitPrice': unit_price,
        'unit_price': unit_price,
        'address': address,
        'link': link,
        'source': link,
        'source_link': link,
        'source_text': source_text,
        'remark': remark,
        'priceType': '普通司法拍卖',
        'price_type': '普通司法拍卖',
        'item_id': item_id,

        # 拍卖记录
        'auctionRecords': auction_records,
        'auction_records': auction_records,

        # 元信息
        'platform': platform,
        'score': 50,  # 默认评分
        'distance_km': None,
        'is_self_auction': False,
        'price_anomaly': None,
    }

    # 如果有详情数据（来自 get_taobao_detail），覆盖上面字段
    detail = raw_item.get('detail', {})
    if detail and detail.get('success'):
        if detail.get('building_area', 0) > 0:
            v1_case['建筑面积(m²)'] = str(detail['building_area'])
            v1_case['buildingArea'] = detail['building_area']
            v1_case['building_area'] = detail['building_area']
        if detail.get('address'):
            v1_case['address'] = detail['address']
            # 更新参照物位置
            if not title:
                v1_case['参照物位置'] = detail['address']
                v1_case['referenceLocation'] = detail['address']
        if detail.get('deal_price', 0) > 0:
            v1_case['市场价值(万元)'] = str(round(detail['deal_price'] / 10000, 2))
            v1_case['marketValue'] = detail['deal_price'] / 10000
            v1_case['market_value'] = detail['deal_price'] / 10000
        elif detail.get('start_price', 0) > 0:
            v1_case['市场价值(万元)'] = str(round(detail['start_price'] / 10000, 2))
            v1_case['marketValue'] = detail['start_price'] / 10000
            v1_case['market_value'] = detail['start_price'] / 10000
        # 单价
        if detail.get('deal_price', 0) > 0 and detail.get('building_area', 0) > 0:
            v1_case['建筑单价(元/㎡)'] = str(round(detail['deal_price'] / detail['building_area'], 2))
            v1_case['unitPrice'] = detail['deal_price'] / detail['building_area']
            v1_case['unit_price'] = detail['deal_price'] / detail['building_area']
        elif detail.get('start_price', 0) > 0 and detail.get('building_area', 0) > 0:
            v1_case['建筑单价(元/㎡)'] = str(round(detail['start_price'] / detail['building_area'], 2))
            v1_case['unitPrice'] = detail['start_price'] / detail['building_area']
            v1_case['unit_price'] = detail['start_price'] / detail['building_area']
        # 状态
        if detail.get('current_stage'):
            v1_case['auctionRecords'] = [{
                'round': detail['current_stage'],
                'date': str(detail.get('start_date', '')) if detail.get('start_date') else '',
                'startPrice': detail.get('start_price', 0),
                'endPrice': detail.get('deal_price', 0) if detail.get('status') == '已成交' else 0,
                'status': detail.get('status', '未知'),
            }]
            v1_case['auction_records'] = v1_case['auctionRecords']
        # 备注
        remark_d = []
        if detail.get('current_stage'):
            remark_d.append(f"{detail['current_stage']}")
        if detail.get('start_price', 0) > 0:
            remark_d.append(f"起拍价：{detail['start_price']:,.0f}元")
        if detail.get('consult_price', 0) > 0:
            remark_d.append(f"评估价：{detail['consult_price']:,.0f}元")
        if detail.get('deal_price', 0) > 0 and detail.get('status') == '已成交':
            remark_d.append(f"成交价：{detail['deal_price']:,.0f}元")
        if detail.get('status'):
            remark_d.append(f"状态：{detail['status']}")
        if remark_d:
            v1_case['备注'] = '；'.join(remark_d)
            v1_case['remark'] = v1_case['备注']

    return v1_case


def fetch_detail_for_item(item, platform):
    """为单个搜索结果抓取详情页数据（仅淘宝支持）"""
    if platform == 'taobao' and item.get('item_id'):
        try:
            from taobao_chrome_fetcher import get_taobao_detail_with_chrome
            detail = get_taobao_detail_with_chrome(item['item_id'])
            item['detail'] = detail
        except Exception as e:
            print(f"Chrome详情抓取失败 {item.get('item_id')}: {e}")
            item['detail'] = {'success': False, 'error': str(e)}
    return item


def _expand_keywords(address: str) -> list:
    """将抵押物地址拆分成由近到远的分层关键词"""
    # 先清理地址中的特殊字符
    addr = address.strip()
    # 常见行政区划后缀
    districts = ['区', '市', '县', '镇', '街道', '乡']
    keywords = [addr]  # 第1层：完整地址（最精确）

    # 第2层：尝试提取小区/楼盘名
    import re
    # 尝试匹配小区/楼盘模式
    for sep in [' ', '，', ',', '、']:
        parts = addr.split(sep)
        if len(parts) > 1:
            main_part = parts[0].strip()
            if len(main_part) >= 2:
                keywords.append(main_part)
                break  # 只取第一个分隔符的分割

    # 尝试从地址开头提取"XX市XX区"作为模糊关键词
    area_match = re.match(r'([\u4e00-\u9fff]{2,4}(?:市|区|县|州))', addr)
    if area_match:
        area = area_match.group(1)
        if area not in keywords:
            keywords.append(area)

    # 第3层：提取"XX路"或"XX街道"
    road_match = re.search(r'[^\d]+路', addr)
    if road_match:
        keywords.append(road_match.group())

    # 第4层：提取行政区（XX区/XX市）
    for d in districts:
        idx = addr.find(d)
        if idx > 0 and idx < len(addr) - 1:
            district = addr[:idx+len(d)]
            keywords.append(district)

    # 第5层：提取城市名（从市级行政区）
    city_match = re.search(r'(.+?[市州])', addr)
    if city_match:
        city = city_match.group(1)
        if city not in keywords:
            keywords.append(city)

    # 去重并保留顺序
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result


def _search_items(address: str) -> list:
    """分层搜索：由近到远逐层搜淘宝/京东，去重合并"""
    all_raw = []
    keywords = _expand_keywords(address)
    seen_links = set()

    from asset_search_api import UnifiedAuctionSearcher
    searcher = UnifiedAuctionSearcher()

    for kw in keywords:
        try:
            items = searcher.search_all(kw, platforms=['jd', 'taobao'])
            for item in items:
                link = item.get('link', '')
                if link and link not in seen_links:
                    seen_links.add(link)
                    item['searchKeyword'] = kw  # 标记是哪个关键词搜到的
                    all_raw.append(item)
            if len(all_raw) >= 30:  # 够了就不搜更宽泛的关键词了
                break
        except Exception as e:
            print(f"关键词 '{kw}' 搜索失败: {e}")

    searcher.cleanup()

    # 如果API搜不到结果，fallback到Playwright
    if not all_raw:
        try:
            from playwright_searcher import PlaywrightAuctionSearcher
            pw = PlaywrightAuctionSearcher()
            for kw in keywords[:3]:  # Playwright只搜前三层
                items = pw.search_all(kw, platforms=['taobao', 'jd'])
                for item in items:
                    link = item.get('link', '')
                    if link and link not in seen_links:
                        seen_links.add(link)
                        item['searchKeyword'] = kw
                        all_raw.append(item)
            pw.stop()
        except Exception as e:
            print(f"Playwright 搜索也失败: {e}")

    return all_raw


def _dedup_items(items: list) -> list:
    """按链接去重"""
    seen = set()
    result = []
    for item in items:
        link = item.get('link', '')
        if link not in seen:
            seen.add(link)
            result.append(item)
    return result


def _filter_items(items: list) -> list:
    """排除明显不相关的非房产拍卖结果"""
    exclude_kw = ['公开选聘', '审计机构', '破产清算', '招募公告', '租赁权公告', '服务采购']
    kept = []
    for item in items:
        title = (item.get('title', '') or '')
        if any(kw in title for kw in exclude_kw):
            print(f"  过滤不相关: {title[:40]}")
            continue
        kept.append(item)
    return kept


def _enrich_details(items: list, max_items: int = 10):
    """使用本机已登录 Chrome 抓取淘宝详情页（最多max_items条）"""
    taobao_items = [i for i in items if i.get('platform') == 'taobao']
    fetch_limit = min(max_items, len(taobao_items))
    if fetch_limit == 0:
        return
    for i in range(fetch_limit):
        fetch_detail_for_item(taobao_items[i], 'taobao')


def _format_and_sort(raw_items: list, address: str) -> dict:
    """转V1格式、排序、检测自身拍卖，返回前端期望格式"""
    v1_cases = []
    for idx, raw in enumerate(raw_items):
        platform = raw.get('platform', 'unknown')
        v1_case = map_raw_to_v1(raw, platform, idx)
        v1_cases.append(v1_case)

    v1_cases.sort(key=lambda c: (
        -1 if isinstance(c.get('detail'), dict) and c['detail'].get('success') else 0,
        -1 if (c.get('buildingArea', 0) or c.get('building_area', 0) or 0) > 0 else 0,
        -1 if (c.get('marketValue', 0) or c.get('market_value', 0) or 0) > 0 else 0,
    ))

    top3 = v1_cases[:3]
    self_auction_ids = set()
    for case in v1_cases:
        case_addr = case.get('address', '') or ''
        if address in case_addr and len(address) > 5:
            case['is_self_auction'] = True
            self_auction_ids.add(case.get('item_id', ''))

    return {
        'status': 'success',
        'top3': top3,
        'all_cases': v1_cases,
        'self_auction_count': len(self_auction_ids),
        'total_count': len(v1_cases),
    }


def run_search(address, property_type=None, area=None):
    """执行搜索并返回前端期望格式"""
    try:
        all_raw = _search_items(address)
        unique_raw = _dedup_items(all_raw)
        filtered_raw = _filter_items(unique_raw)
        _enrich_details(filtered_raw)
        return _format_and_sort(filtered_raw, address)
    except Exception as e:
        print(f"搜索异常: {e}")
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'top3': [], 'all_cases': [],
            'self_auction_count': 0, 'total_count': 0,
            'error': '搜索服务暂时不可用，请稍后重试',
        }


@app.route('/api/search', methods=['POST'])
def search():
    """前端调用的主搜索接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'top3': [],
                'all_cases': [],
                'self_auction_count': 0,
                'total_count': 0,
                'error': '请求体为空或不是有效的JSON',
            }), 400

        address = data.get('address', '')
        if not address:
            return jsonify({
                'status': 'error',
                'top3': [],
                'all_cases': [],
                'self_auction_count': 0,
                'total_count': 0,
                'error': '地址不能为空',
            }), 400

        property_type = data.get('asset_type', data.get('propertyType', 'commercial'))
        area = data.get('building_area', data.get('area'))

        print(f"[API] 搜索请求: address={address}, type={property_type}, area={area}")
        result = run_search(address, property_type, area)

        if result.get('status') != 'success':
            print(f"[API] 搜索失败: {result.get('error', '未知错误')}")

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[API] 未处理异常: {e}")
        return jsonify({
            'status': 'error',
            'top3': [],
            'all_cases': [],
            'self_auction_count': 0,
            'total_count': 0,
            'error': '服务器内部错误，请联系管理员',
        }), 500


# 保留旧接口兼容性
@app.route('/api/valuate', methods=['POST'])
def valuate():
    """旧版接口（兼容）"""
    data = request.get_json()
    address = data.get('address', '')
    property_type = data.get('propertyType', 'commercial')
    area = data.get('area')
    result = run_search(address, property_type, area)
    # 转换为旧格式
    return jsonify({
        'success': result['status'] == 'success',
        'message': result.get('error', '搜索成功') if result['status'] != 'success' else '搜索成功',
        'data': result.get('all_cases', []),
        'total': result.get('total_count', 0),
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/debug', methods=['GET'])
def debug():
    """调试接口 - 测试各模块是否可用"""
    deps = {}
    try:
        import playwright
        deps['playwright'] = 'ok'
        from playwright.sync_api import sync_playwright
        deps['playwright_api'] = 'ok'
    except Exception as e:
        deps['playwright'] = str(e)
    try:
        import playwright_searcher
        deps['playwright_searcher'] = 'ok'
    except Exception as e:
        deps['playwright_searcher'] = str(e)
    return jsonify(deps)


@app.route('/', methods=['GET'])
def index():
    return "不良资产估值参考案例搜索服务 - API运行中"


@app.route('/api/export', methods=['POST'])
def export_excel():
    try:
        raw = request.get_data(as_text=True)
        if not raw:
            return jsonify({'success': False, 'message': '请求体为空'}), 400
        data = json.loads(raw)
        cases = data.get('cases', data.get('all_cases', []))
        if not cases:
            return jsonify({'success': False, 'message': '没有可导出的数据'}), 400

        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

        wb = Workbook()
        ws = wb.active
        ws.title = '估值案例'

        headers = ['参照物位置', '土地面积 (m2)', '建筑面积 (m2)', '市场价值(万元)',
                   '建筑单价(元/m2)', '数据来源', '备注', '价格类型']
        col_widths = [60, 15, 15, 15, 18, 50, 80, 15]

        hfill = PatternFill(start_color='1E40AF', end_color='1E40AF', fill_type='solid')
        hfont = Font(name='Microsoft YaHei', bold=True, color='FFFFFF', size=11)
        cfont = Font(name='Microsoft YaHei', size=10)
        border = Border(left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))
        calign = Alignment(horizontal='center', vertical='center', wrap_text=True)
        lalign = Alignment(horizontal='left', vertical='center', wrap_text=True)

        for ci, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=ci, value=h)
            cell.fill = hfill; cell.font = hfont; cell.alignment = calign; cell.border = border

        for ri, case in enumerate(cases, 2):
            vals = [
                case.get('referenceLocation') or case.get('参照物位置') or '',
                case.get('landArea') or case.get('土地面积') or '不适用',
                case.get('buildingArea') or case.get('建筑面积') or 0,
                case.get('marketValue') or case.get('市场价值') or 0,
                case.get('unitPrice') or case.get('建筑单价') or 0,
                case.get('link') or case.get('source') or case.get('数据来源') or '',
                case.get('remark') or case.get('备注') or '',
                case.get('priceType') or case.get('价格类型') or '普通司法拍卖',
            ]
            for ci, v in enumerate(vals, 1):
                cell = ws.cell(row=ri, column=ci, value=v)
                cell.font = cfont; cell.border = border
                cell.alignment = lalign if ci in (1, 6, 7) else calign
                if ci in (3, 4, 5):
                    try:
                        fv = float(v) if v not in ('-', '不适用', '', None) else 0
                        cell.value = fv
                    except: pass
                    cell.number_format = '#,##0.00'

        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = w
        ws.freeze_panes = 'A2'

        import io
        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)

        return Response(buf.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=npl_valuation_cases.xlsx'})
    except Exception as e:
        print(f'导出异常: {e}')
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': f'导出失败: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
