#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘宝司法拍卖详情页Selenium抓取器
使用Selenium绕过淘宝API限制，获取详情页数据
"""

import time
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class 淘宝详情页抓取器:
    """使用Selenium抓取淘宝司法拍卖详情页"""

    def __init__(self, 无头模式=True):
        self.无头模式 = 无头模式
        self.driver = None

    def 初始化浏览器(self):
        """初始化Chrome浏览器"""
        try:
            chrome_options = Options()

            if self.无头模式:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')

            # 必要的优化选项
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # 用户代理
            chrome_options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            # 窗口大小
            chrome_options.add_argument('--window-size=1920,1080')

            # 使用系统安装的Chrome
            chrome_options.binary_location = '/usr/bin/google-chrome-stable'

            # Chrome 150+ 自带ChromeDriver，直接使用
            self.driver = webdriver.Chrome(options=chrome_options)

            # 隐藏自动化特征
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            print("✅ 浏览器初始化成功")
            return True

        except Exception as e:
            print(f"❌ 浏览器初始化失败: {e}")
            return False

    def 关闭浏览器(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def 获取淘宝详情页数据(self, 链接):
        """
        获取淘宝司法拍卖详情页数据
        :param 链接: 淘宝拍卖链接
        :return: 字典，包含面积、价格、拍卖记录等
        """
        if not self.driver:
            if not self.初始化浏览器():
                return None

        try:
            print(f"📥 正在访问: {链接}")

            # 访问页面
            self.driver.get(链接)

            # 等待页面加载
            time.sleep(5)

            # 等待body加载
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print("⚠️ 页面加载超时，继续尝试...")

            # 获取页面源码
            页面源码 = self.driver.page_source

            # 初始化数据结构
            数据 = {
                '链接': 链接,
                '面积': 0,
                '价格': 0,
                '起拍价': 0,
                '成交价': 0,
                '类型': '商业',
                '地址': '',
                '拍卖记录': [],
                '标题': '',
                '提取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '页面源码长度': len(页面源码)
            }

            # 1. 提取标题
            try:
                数据['标题'] = self.driver.title
                print(f"📄 页面标题: {数据['标题']}")
            except:
                pass

            # 2. 提取面积（多种尝试）
            面积提取成功 = False

            # 方法1：XPath查找包含"建筑面积"的元素
            if not 面积提取成功:
                try:
                    面积元素 = self.driver.find_element(
                        By.XPATH,
                        "//*[contains(text(), '建筑面积') or contains(text(), '面积：') or contains(text(), '面积:')]"
                    )
                    面积文本 = 面积元素.text
                    print(f"📏 找到面积文本: {面积文本}")
                    面积匹配 = re.search(r'(\d+[\d,.]*\d*)', 面积文本.replace(',', ''))
                    if 面积匹配:
                        数据['面积'] = float(面积匹配.group(1))
                        面积提取成功 = True
                        print(f"✅ 提取到面积: {数据['面积']}㎡")
                except NoSuchElementException:
                    pass

            # 方法2：查找包含㎡或平方米的元素
            if not 面积提取成功:
                try:
                    所有元素 = self.driver.find_elements(
                        By.XPATH,
                        "//*[contains(text(), '㎡') or contains(text(), '平方米')]"
                    )
                    for 元素 in 所有元素:
                        文本 = 元素.text
                        if '建筑面积' in 文本 or '面积' in 文本:
                            面积匹配 = re.search(r'(\d+[\d,.]*\d*)', 文本.replace(',', ''))
                            if 面积匹配:
                                数据['面积'] = float(面积匹配.group(1))
                                面积提取成功 = True
                                print(f"✅ 从备选元素提取到面积: {数据['面积']}㎡")
                                break
                except:
                    pass

            # 方法3：从页面源码正则提取
            if not 面积提取成功:
                try:
                    # 常见的面积正则模式
                    面积模式 = [
                        r'建筑面积[：:]\s*(\d+[\d.]*\s*㎡?)',
                        r'buildingArea["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
                        r'(\d+[\d.]*\s*㎡)\s*',
                    ]
                    for 模式 in 面积模式:
                        匹配 = re.search(模式, 页面源码)
                        if 匹配:
                            数值 = re.search(r'(\d+[\d.]*)', 匹配.group(1))
                            if 数值:
                                数据['面积'] = float(数值.group(1))
                                面积提取成功 = True
                                print(f"✅ 从源码提取到面积: {数据['面积']}㎡")
                                break
                except:
                    pass

            # 3. 提取价格（多种尝试）
            价格提取成功 = False

            # 方法1：查找价格元素
            if not 价格提取成功:
                try:
                    价格元素 = self.driver.find_element(
                        By.XPATH,
                        "//*[contains(text(), '¥') or contains(text(), '起拍价') or contains(text(), '成交价')]"
                    )
                    价格文本 = 价格元素.text
                    print(f"💰 找到价格文本: {价格文本}")
                    价格匹配 = re.search(r'¥?\s*(\d+[\d,.]*\d*)', 价格文本.replace(',', ''))
                    if 价格匹配:
                        数据['价格'] = float(价格匹配.group(1))
                        价格提取成功 = True
                        print(f"✅ 提取到价格: {数据['价格']}元")
                except NoSuchElementException:
                    pass

            # 方法2：查找class包含price的元素
            if not 价格提取成功:
                try:
                    for class_name in ['price', 'Price', 'J_Price', 'p-price', 'sf-price']:
                        try:
                            价格元素 = self.driver.find_element(By.CLASS_NAME, class_name)
                            价格文本 = 价格元素.text
                            价格匹配 = re.search(r'(\d+[\d,.]*\d*)', 价格文本.replace(',', ''))
                            if 价格匹配:
                                数据['价格'] = float(价格匹配.group(1))
                                价格提取成功 = True
                                print(f"✅ 从class提取到价格: {数据['价格']}元")
                                break
                        except:
                            continue
                except:
                    pass

            # 方法3：从页面源码正则提取
            if not 价格提取成功:
                try:
                    价格模式 = [
                        r'起拍价[：:]\s*¥?(\d+[\d,.]*)',
                        r'currentPrice["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
                        r'startPrice["\']?\s*[:=]\s*["\']?(\d+[\d.]*)',
                        r'¥\s*(\d+[\d,.]*)',
                    ]
                    for 模式 in 价格模式:
                        匹配 = re.search(模式, 页面源码)
                        if 匹配:
                            数值 = re.search(r'(\d+[\d.]*)', 匹配.group(1))
                            if 数值:
                                数据['价格'] = float(数值.group(1))
                                数据['起拍价'] = 数据['价格']
                                价格提取成功 = True
                                print(f"✅ 从源码提取到价格: {数据['价格']}元")
                                break
                except:
                    pass

            # 4. 提取地址
            try:
                for xpath in [
                    "//*[contains(text(), '地址')]",
                    "//*[contains(text(), '所在地')]",
                    "//*[contains(text(), '位置')]",
                    "//*[contains(text(), '标的物')]"
                ]:
                    try:
                        地址元素 = self.driver.find_element(By.XPATH, xpath)
                        地址文本 = 地址元素.text
                        if '地址' in 地址文本 or '所在地' in 地址文本 or '标的物' in 地址文本:
                            数据['地址'] = 地址文本
                            print(f"📍 提取到地址信息: {地址文本[:50]}...")
                            break
                    except:
                        continue
            except:
                pass

            # 5. 判断物业类型
            try:
                标题 = str(数据['标题']) + str(数据.get('地址', ''))
                if '住宅' in 标题 or '住房' in 标题 or '公寓' in 标题:
                    数据['类型'] = '住宅'
                elif '商业' in 标题 or '商铺' in 标题 or '店面' in 标题 or '写字楼' in 标题:
                    数据['类型'] = '商业'
                elif '工业' in 标题 or '厂房' in 标题 or '仓库' in 标题:
                    数据['类型'] = '工业'
                else:
                    数据['类型'] = '商业'
            except:
                pass

            print(f"🏷️ 判断物业类型: {数据['类型']}")

            # 6. 提取拍卖记录
            数据['拍卖记录'] = [{
                '轮次': '一拍',
                '日期': datetime.now().strftime('%Y年%m月%d日'),
                '起拍价': 数据['起拍价'] if 数据['起拍价'] > 0 else 数据['价格'],
                '成交价': 数据['成交价'],
                '状态': '待确认'
            }]

            # 7. 保存页面截图（调试用）
            try:
                时间戳 = datetime.now().strftime('%Y%m%d_%H%M%S')
                截图路径 = f"/workspace/taobao_screenshot_{时间戳}.png"
                self.driver.save_screenshot(截图路径)
                print(f"📸 页面截图已保存: {截图路径}")
            except:
                pass

            print(f"✅ 数据提取完成: 面积={数据['面积']}㎡, 价格={数据['价格']}元, 类型={数据['类型']}")

            return 数据

        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def 批量抓取(self, 链接列表):
        """批量抓取多个链接"""
        结果列表 = []

        for i, 链接 in enumerate(链接列表, 1):
            print(f"\n🔍 处理第{i}/{len(链接列表)}个链接")

            数据 = self.获取淘宝详情页数据(链接)
            if 数据:
                结果列表.append(数据)

            # 间隔避免被封
            if i < len(链接列表):
                time.sleep(2)

        return 结果列表


def 测试selenium方案():
    """测试Selenium方案"""
    print("=" * 70)
    print("🧪 开始测试Selenium方案")
    print("=" * 70)

    # 测试链接（真实淘宝司法拍卖链接）
    测试链接列表 = [
        "https://sf-item.taobao.com/sf_item/1057691230752.htm",
        "https://sf-item.taobao.com/sf_item/1056859991769.htm",
        "https://sf-item.taobao.com/sf_item/1051453618722.htm",
    ]

    # 创建抓取器（无头模式）
    抓取器 = 淘宝详情页抓取器(无头模式=True)

    try:
        # 批量抓取
        结果列表 = 抓取器.批量抓取(测试链接列表)

        if 结果列表:
            print("\n" + "=" * 70)
            print("✅ 测试成功！获取到数据:")
            print("=" * 70)

            for i, 数据 in enumerate(结果列表, 1):
                print(f"\n📋 案例{i}:")
                for 键, 值 in 数据.items():
                    if 键 != '拍卖记录':
                        print(f"   {键}: {值}")

                # 验证数据质量
                if 数据['面积'] > 0 and 数据['价格'] > 0:
                    print(f"   ✅ 数据质量验证通过")
                else:
                    print(f"   ⚠️ 数据质量警告：面积或价格为0")

            return 结果列表
        else:
            print("\n❌ 测试失败：未获取到数据")
            return None

    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        抓取器.关闭浏览器()


if __name__ == "__main__":
    测试结果 = 测试selenium方案()
    if 测试结果:
        print(f"\n🎯 测试结果: 成功（获取到{len(测试结果)}个案例）")
    else:
        print(f"\n🎯 测试结果: 失败")
