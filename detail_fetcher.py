#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detail page fetcher using Playwright - extracts real round/status/price/date."""

from playwright.sync_api import sync_playwright
import json
import re
import time


def 获取详情真实信息(item_id, debug=False):
    """
    通过Playwright渲染详情页，从MTOP API响应中提取真实拍卖信息。
    关键：先访问sf.taobao.com建立session cookie，再访问详情页，可绕过captcha。

    返回字段：
    - 轮次: 一拍/二拍/三拍/变卖
    - 状态: 即将开始/正在进行/已成交/流拍
    - 起拍价: 元
    - 评估价: 元
    - 成交价: 元 (已成交时)
    - 开始时间: YYYY-MM-DD HH:MM:SS
    - 结束时间: YYYY-MM-DD HH:MM:SS
    - 标题: 完整标题
    """
    result = {
        '轮次': '', '状态': '', '起拍价': 0, '评估价': 0, '成交价': 0,
        '开始时间': '', '结束时间': '', '标题': '', '成功': False, '来源': '详情API'
    }

    raw_data = _fetch_detail_raw(item_id)
    if not raw_data:
        result['来源'] = '详情API失败'
        return result

    d = raw_data.get('data', {})
    if not d:
        result['来源'] = '详情API空数据'
        return result

    # 1. 轮次: titleTag.preTags[0].value
    title_tag = d.get('titleTag', {})
    pre_tags = title_tag.get('preTags', [])
    for tag in pre_tags:
        val = tag.get('value', '')
        if val in ('一拍', '二拍', '三拍', '变卖', '一拍流拍', '二拍流拍', '三拍流拍'):
            result['轮次'] = val
            break
    if not result['轮次']:
        # 从suffixTags找
        for tag in title_tag.get('suffixTags', []):
            val = tag.get('value', '')
            if val in ('一拍', '二拍', '三拍', '变卖'):
                result['轮次'] = val
                break
    if not result['轮次']:
        result['轮次'] = '一拍'  # 默认

    # 2. 标题
    result['标题'] = title_tag.get('title', '')

    # 3. 价格: chargeSummary.currentPrice
    charge = d.get('chargeSummary', {})
    current_price = charge.get('currentPrice', {})
    # propertyPlatformPrice 单位是分
    price_cent = current_price.get('propertyPlatformPrice', 0)
    if price_cent and price_cent > 0 and price_cent < 9223372036854775807:
        result['起拍价'] = price_cent / 100.0
    elif current_price.get('priceStr'):
        try:
            result['起拍价'] = float(str(current_price['priceStr']).replace(',', '').strip())
        except:
            pass

    # 评估价: consultPrice (单位分)
    consult = d.get('consultPrice', 0)
    if consult and consult > 0 and consult < 9223372036854775807:
        result['评估价'] = consult / 100.0

    # 4. 时间
    result['开始时间'] = d.get('startTime', '')
    result['结束时间'] = d.get('endTime', '')

    # 5. 状态: bidStatus + coreStatus.priceDescription
    bid_status = d.get('bidStatus', 0)
    core_status = d.get('coreStatus', {})
    price_desc = core_status.get('priceDescription', '')
    no_confirm = core_status.get('noConfirmReason', '')

    # bidStatus映射: 1=即将开始, 2=正在进行, 3=已结束
    # priceDescription: "起拍价"=即将开始/进行中, "成交价"=已成交, "当前价"=流拍(结束未成交)
    server_time = d.get('serverTime', '')
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    end_time = result['结束时间']

    已结束 = False
    if end_time:
        try:
            et = end_time.replace('-', '').replace(':', '').replace(' ', '')
            nt = now.replace('-', '').replace(':', '').replace(' ', '')
            已结束 = et < nt
        except:
            pass

    if '成交' in price_desc:
        result['状态'] = '已成交'
        # 成交价 = 当前价
        result['成交价'] = result['起拍价']
    elif '当前' in price_desc:
        # 当前价 + 已结束 = 流拍
        if 已结束:
            result['状态'] = '流拍'
        else:
            result['状态'] = '正在进行'
    elif '流拍' in price_desc or '流拍' in no_confirm:
        result['状态'] = '流拍'
    elif bid_status == 1 or '起拍' in price_desc:
        result['状态'] = '即将开始'
    elif bid_status == 2:
        result['状态'] = '正在进行'
    else:
        # 根据是否结束判断
        if 已结束:
            result['状态'] = '流拍'
        else:
            result['状态'] = '即将开始'

    # 如果已成交，成交价=起拍价（currentPrice即成交价）
    if result['状态'] == '已成交' and result['成交价'] == 0:
        result['成交价'] = result['起拍价']

    # 6. 确定拍卖日期：
    #    - 已流拍 / 已成交 的拍卖，使用结束时间（即流拍/成交发生的日期）
    #    - 即将开始 / 正在进行 的拍卖，使用开始时间
    日期来源 = result['开始时间']
    if result['状态'] in ('流拍', '已成交'):
        日期来源 = result['结束时间'] or result['开始时间']
    result['拍卖日期来源'] = 日期来源

    result['成功'] = True

    if debug:
        print(f'  [详情] {item_id}: 轮次={result["轮次"]}, 状态={result["状态"]}, '
              f'起拍价={result["起拍价"]:.0f}, 评估价={result["评估价"]:.0f}, '
              f'日期来源={日期来源}')

    return result


def _fetch_detail_raw(item_id, max_retries=2):
    """通过Playwright获取详情API原始JSON数据。"""
    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=[
                    '--no-sandbox', '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                ])
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
                               'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                    viewport={'width': 375, 'height': 812},
                    locale='zh-CN',
                )
                context.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                )
                page = context.new_page()

                real_body = [None]

                def on_response(response):
                    u = response.url
                    if 'queryhttpsitemdetail' in u and 'punish' not in u and 'report' not in u:
                        try:
                            b = response.text()
                            if len(b) > 1000 and 'RGV587' not in b:
                                real_body[0] = b
                        except:
                            pass

                page.on('response', on_response)

                # Step 1: 建立session（访问首页）
                try:
                    page.goto('https://sf.taobao.com/', timeout=20000, wait_until='domcontentloaded')
                    page.wait_for_timeout(2000)
                except:
                    pass

                # Step 2: 访问详情页
                detail_url = (f'https://pages-fast.m.taobao.com/wow/z/app/pm/dzc-ice/dzc-detail'
                              f'?x-ssr=true&disableNav=YES&x-preload=true&forceThemis=true'
                              f'&skeleton=true&uniapp_id=1100093&uniapp_page=ssr-dzc-detail&itemId={item_id}')
                try:
                    page.goto(detail_url, timeout=30000, wait_until='domcontentloaded')
                    page.wait_for_timeout(6000)
                except:
                    pass

                browser.close()

                if real_body[0]:
                    # 解析 mtopjsonpN({...})
                    m = re.search(r'mtopjsonp\d*\((.*)\)\s*$', real_body[0], re.DOTALL)
                    if m:
                        try:
                            return json.loads(m.group(1))
                        except:
                            pass
            # 重试前等待
            if attempt < max_retries - 1:
                time.sleep(2)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
    return None


if __name__ == '__main__':
    # 测试用户提到的3个案例（用户说是二拍流拍）
    test_ids = ['1064587700541', '1031160224444', '1062594789829']
    print('测试详情API获取轮次和状态...')
    print('=' * 70)
    for iid in test_ids:
        r = 获取详情真实信息(iid, debug=True)
        print(f'  结果: 轮次={r["轮次"]}, 状态={r["状态"]}, 起拍价={r["起拍价"]:.0f}元, '
              f'评估价={r["评估价"]:.0f}元, 开始={r["开始时间"]}, 来源={r["来源"]}')
        print()
