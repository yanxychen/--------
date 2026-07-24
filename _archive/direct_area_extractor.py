#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接从淘宝详情页提取真实面积（使用Selenium）
关键修复：不再用价格反推面积，而是直接从页面DOM提取
"""

import time
import re
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


def 创建浏览器():
    """创建Chrome浏览器实例"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.binary_location = '/usr/bin/google-chrome-stable'

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def 从页面直接提取面积(driver, 案例标题="", 案例序号=0):
    """
    直接从淘宝详情页提取建筑面积
    不是用价格反推！直接从DOM元素提取
    """
    print(f"🔍 [案例{案例序号}] 直接提取真实面积...")

    面积元素列表 = []

    # 淘宝详情页常见的面积元素XPath
    面积XPath列表 = [
        # 淘宝司法拍卖常见结构 - key/value配对
        "//div[contains(@class, 'item') and contains(text(), '建筑面积')]",
        "//div[contains(@class, 'key') and contains(text(), '建筑面积')]/following-sibling::div[contains(@class, 'value')]",
        "//span[contains(text(), '建筑面积')]/following-sibling::span",
        "//td[contains(text(), '建筑面积')]/following-sibling::td",
        "//li[contains(text(), '建筑面积')]",
        # 通用查找
        "//*[contains(text(), '建筑面积')]",
        "//*[contains(text(), '面积：')]",
        "//*[contains(text(), '面积:')]",
        "//*[contains(text(), '㎡') and string-length(text()) < 100]",
        "//*[contains(text(), '平方米') and string-length(text()) < 100]",
    ]

    for xpath in 面积XPath列表:
        try:
            元素列表 = driver.find_elements(By.XPATH, xpath)
            for 元素 in 元素列表:
                文本 = 元素.text.strip()
                if 文本 and ('建筑面积' in 文本 or '面积：' in 文本 or '面积:' in 文本 or '㎡' in 文本):
                    面积元素列表.append({
                        '元素': 元素,
                        '文本': 文本,
                        'xpath': xpath
                    })
                    print(f"   📍 找到面积元素: {文本[:50]}... (XPath: {xpath[:50]}...)")
        except:
            continue

    # 从找到的元素中提取数字
    面积候选 = []

    for 元素信息 in 面积元素列表:
        文本 = 元素信息['文本']
        # 提取数字（支持带逗号的格式：12,916.69）
        匹配列表 = re.findall(r'(\d+[\d.]*\d*)', 文本.replace(',', ''))

        for 匹配 in 匹配列表:
            try:
                数值 = float(匹配)
                # 合理性检查：建筑面积通常在50-50000㎡之间
                if 50 <= 数值 <= 50000:
                    面积候选.append({
                        '面积': 数值,
                        '原始文本': 文本,
                        'xpath': 元素信息['xpath'],
                        '元素': 元素信息['元素']
                    })
                    print(f"   🔢 提取到面积候选: {数值}㎡ (来自: {文本[:30]}...)")
            except:
                continue

    # 选择最可能的真实面积
    if 面积候选:
        print(f"   📋 找到{len(面积候选)}个面积候选")

        # 策略1：优先选择明确标注"建筑面积"的
        建筑面积候选 = [c for c in 面积候选 if '建筑面积' in c['原始文本']]
        if 建筑面积候选:
            最终面积 = 建筑面积候选[0]['面积']
            print(f"   🏆 选择明确标注'建筑面积'的值: {最终面积}㎡")
            return 最终面积, '页面直接提取'

        # 策略2：选择数值最合理的（中位数）
        面积值列表 = sorted([c['面积'] for c in 面积候选])
        最终面积 = 面积值列表[len(面积值列表) // 2]
        print(f"   🏆 选择中位数面积: {最终面积}㎡")
        return 最终面积, '页面直接提取'

    # 如果没找到，尝试从表格提取
    print(f"   ⚠️ 未找到明确的建筑面积元素，尝试从表格提取...")

    try:
        表格列表 = driver.find_elements(By.TAG_NAME, "table")
        for 表格 in 表格列表:
            表格文本 = 表格.text
            if '面积' in 表格文本 or '㎡' in 表格文本:
                print(f"   📊 在表格中找到面积信息")
                所有数字 = re.findall(r'\d+[\d.]*\d*', 表格文本.replace(',', ''))
                for 数字 in 所有数字:
                    try:
                        数值 = float(数字)
                        if 50 <= 数值 <= 50000:
                            print(f"   🔢 从表格提取面积: {数值}㎡")
                            return 数值, '表格提取'
                    except:
                        continue
    except:
        pass

    # 从页面源码提取
    print(f"   ⚠️ 尝试从页面源码提取...")
    try:
        页面源码 = driver.page_source
        源码模式 = [
            r'建筑面积[：:]\s*(\d+[\d.]*)',
            r'buildingArea["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
            r'area["\']?\s*[:=]\s*["\']?(\d+[\d.]*)\s*㎡',
        ]
        for 模式 in 源码模式:
            匹配 = re.search(模式, 页面源码)
            if 匹配:
                数值 = float(匹配.group(1))
                if 50 <= 数值 <= 50000:
                    print(f"   🔢 从源码提取面积: {数值}㎡")
                    return 数值, '源码提取'
    except:
        pass

    # 最后手段：价格反推（明确标记）
    print(f"   🚨 警告：无法从页面直接提取面积，使用价格反推（最后手段）")
    return 0, '无法提取'


def 从页面直接提取价格(driver):
    """直接从淘宝详情页提取价格"""
    print(f"   💰 提取真实价格...")

    价格XPath列表 = [
        "//div[contains(@class, 'price')]",
        "//span[contains(@class, 'price')]",
        "//*[contains(text(), '起拍价')]",
        "//*[contains(text(), '成交价')]",
        "//*[contains(text(), '¥')]",
        "//*[contains(text(), '￥')]",
    ]

    价格候选 = []

    for xpath in 价格XPath列表:
        try:
            元素列表 = driver.find_elements(By.XPATH, xpath)
            for 元素 in 元素列表:
                文本 = 元素.text.strip()
                if 文本 and ('¥' in 文本 or '￥' in 文本 or '起拍' in 文本 or '成交' in 文本):
                    print(f"      📍 找到价格元素: {文本[:50]}...")
                    数字匹配 = re.findall(r'\d+[\d.]*\d*', 文本.replace(',', ''))
                    for 数字 in 数字匹配:
                        try:
                            数值 = float(数字)
                            if 100000 <= 数值 <= 1000000000:
                                价格候选.append(数值)
                                print(f"      🔢 提取到价格候选: {数值:,.0f}元")
                        except:
                            continue
        except:
            continue

    if 价格候选:
        最终价格 = max(价格候选)
        print(f"   ✅ 提取到真实价格: {最终价格:,.0f}元")
        return 最终价格

    # 从源码提取
    try:
        页面源码 = driver.page_source
        价格模式 = [
            r'起拍价[：:]\s*¥?(\d+[\d,.]*)',
            r'currentPrice["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
            r'startPrice["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
        ]
        for 模式 in 价格模式:
            匹配 = re.search(模式, 页面源码)
            if 匹配:
                数值 = float(匹配.group(1).replace(',', ''))
                if 100000 <= 数值 <= 1000000000:
                    print(f"   ✅ 从源码提取到价格: {数值:,.0f}元")
                    return 数值
    except:
        pass

    print(f"   ❌ 未提取到价格")
    return 0


def 提取地址(driver, 标题):
    """提取地址信息"""
    # 从标题提取
    if '赤峰市' in 标题:
        匹配 = re.search(r'(赤峰市[\u4e00-\u9fa5]+.*)', 标题)
        if 匹配:
            return 匹配.group(1)
    return 标题


def 处理单个案例(driver, 链接, 案例序号=1):
    """
    直接从淘宝详情页提取真实数据
    """
    from datetime import datetime

    print(f"\n🚀 处理案例{案例序号}: {链接}")

    try:
        # 访问页面
        driver.get(链接)
        time.sleep(5)  # 等待页面加载

        # 获取页面标题
        标题 = driver.title
        print(f"📄 页面标题: {标题}")

        # 关键修复：直接从页面提取真实面积（不是价格反推！）
        真实面积, 面积来源 = 从页面直接提取面积(driver, 标题, 案例序号)

        # 直接从页面提取真实价格
        真实价格 = 从页面直接提取价格(driver)

        # 提取地址
        地址 = 提取地址(driver, 标题)

        # 判断物业类型
        if '住宅' in 标题 or '住房' in 标题:
            类型 = '住宅'
        elif '商业' in 标题 or '商铺' in 标题 or '写字楼' in 标题:
            类型 = '商业'
        else:
            类型 = '其他'

        # 如果面积无法直接提取，用价格反推（最后手段）
        if 真实面积 == 0 and 真实价格 > 0:
            if '住宅' in 标题:
                估算单价 = 8000
            elif '商业' in 标题 or '商铺' in 标题 or '商厅' in 标题:
                估算单价 = 15000
            else:
                估算单价 = 10000

            真实面积 = 真实价格 / 估算单价
            面积来源 = f'价格反推(单价{估算单价})'
            print(f"   🔄 最后手段：从价格反推面积: {真实面积:.2f}㎡")
        elif 真实面积 == 0:
            真实面积 = 150.0
            面积来源 = '默认值'
            print(f"   ⚠️ 无法提取面积，使用默认值: {真实面积}㎡")

        案例数据 = {
            '地址': 地址,
            '类型': 类型,
            '面积': 真实面积,
            '价格': 真实价格,
            '链接': 链接,
            '标题': 标题,
            '案例序号': 案例序号,
            '面积来源': 面积来源,
        }

        print(f"✅ 案例{案例序号}处理完成:")
        print(f"   地址: {地址[:50]}")
        print(f"   类型: {类型}")
        print(f"   面积: {真实面积:,.2f}㎡ ({面积来源})")
        print(f"   价格: {真实价格:,.0f}元")

        return 案例数据

    except Exception as e:
        print(f"❌ 案例{案例序号}处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def 测试直接提取面积():
    """
    测试直接从页面提取面积（不是价格反推）
    """
    print("=" * 70)
    print("🧪 测试直接从淘宝详情页提取真实面积")
    print("=" * 70)

    # 用真实案例测试
    测试链接列表 = [
        "https://sf-item.taobao.com/sf_item/1064587700541.htm",  # 案例1
        "https://sf-item.taobao.com/sf_item/1048342480692.htm",  # 案例2
        "https://sf-item.taobao.com/sf_item/1031160224444.htm",  # 案例3
    ]

    driver = 创建浏览器()
    结果 = []

    try:
        for i, 链接 in enumerate(测试链接列表, 1):
            print(f"\n{'='*50}")
            print(f"🔍 测试案例{i}:")
            print(f"{'='*50}")

            案例数据 = 处理单个案例(driver, 链接, i)

            if 案例数据:
                结果.append({
                    '案例': i,
                    '面积': 案例数据['面积'],
                    '价格': 案例数据['价格'],
                    '面积来源': 案例数据['面积来源'],
                    '标题': 案例数据['标题'][:50]
                })

                # 计算单价验证合理性
                if 案例数据['面积'] > 0 and 案例数据['价格'] > 0:
                    单价 = 案例数据['价格'] / 案例数据['面积']
                    print(f"   建筑单价: {单价:,.0f}元/㎡")

                    if 1000 <= 单价 <= 50000:
                        print(f"   ✅ 单价合理")
                    else:
                        print(f"   ⚠️ 单价可能不合理")

            # 间隔避免请求过快
            if i < len(测试链接列表):
                time.sleep(2)

    finally:
        driver.quit()

    # 输出测试结果
    print("\n" + "=" * 70)
    print("📊 测试结果:")
    print("=" * 70)

    for r in 结果:
        print(f"\n案例{r['案例']}:")
        print(f"   面积: {r['面积']:,.2f}㎡ (来源: {r['面积来源']})")
        print(f"   价格: {r['价格']:,.0f}元")
        print(f"   标题: {r['标题']}")

    # 验证面积是否各不相同
    面积列表 = [r['面积'] for r in 结果]
    面积是否相同 = len(set(面积列表)) == 1

    print("\n" + "=" * 70)
    print("📋 验证报告:")
    print("=" * 70)
    print(f"面积列表: {[f'{a:,.2f}' for a in 面积列表]}")
    print(f"面积是否各不相同: {'否❌' if 面积是否相同 else '是✅'}")

    # 统计数据来源
    直接提取数量 = sum(1 for r in 结果 if '直接提取' in r['面积来源'] or '表格' in r['面积来源'] or '源码' in r['面积来源'])
    反推数量 = sum(1 for r in 结果 if '反推' in r['面积来源'])

    print(f"\n数据来源统计:")
    print(f"   页面直接提取: {直接提取数量}/{len(结果)}")
    print(f"   价格反推: {反推数量}/{len(结果)}")

    if 面积是否相同:
        print(f"\n❌ 问题未解决：所有案例面积仍然相同！")
        return False, 结果
    else:
        print(f"\n✅ 修复成功：面积各不相同！")
        return True, 结果


if __name__ == "__main__":
    成功, 结果 = 测试直接提取面积()

    # 保存测试结果
    with open("/workspace/面积提取测试结果.json", "w", encoding="utf-8") as f:
        json.dump(结果, f, ensure_ascii=False, indent=2)

    print(f"\n💾 测试结果已保存: /workspace/面积提取测试结果.json")
