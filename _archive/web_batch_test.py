#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页批量压力测试脚本

功能:
- 30-50条测试用例覆盖各资产类型
- 顺序测试和并发测试两种模式
- 自动生成CSV报告和统计报告
- 保存截图和页面HTML
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import csv
import os
import re
from datetime import datetime
import concurrent.futures


class WebBatchTester:
    """网页批量测试器"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.driver = None
        self.test_cases = self._load_test_cases()
        
    def _load_test_cases(self):
        """加载测试用例"""
        return [
            # 住宅类 (10条)
            {"address": "北京市朝阳区建国门外大街1号", "asset_type": "住宅", "building_area": 100},
            {"address": "上海市黄浦区南京东路100号", "asset_type": "住宅", "building_area": 85.5},
            {"address": "广州市天河区珠江新城", "asset_type": "住宅", "building_area": 120},
            {"address": "深圳市南山区科技园", "asset_type": "住宅", "building_area": 89.3},
            {"address": "杭州市西湖区文三路", "asset_type": "住宅", "building_area": 75},
            {"address": "南京市鼓楼区中山路", "asset_type": "住宅", "building_area": 110},
            {"address": "武汉市江汉区建设大道", "asset_type": "住宅", "building_area": 95},
            {"address": "成都市锦江区春熙路", "asset_type": "住宅", "building_area": 80},
            {"address": "重庆市渝中区解放碑", "asset_type": "住宅", "building_area": 105},
            {"address": "西安市碑林区南大街", "asset_type": "住宅", "building_area": 90},
            
            # 商业类 (10条)
            {"address": "北京市海淀区中关村", "asset_type": "商业", "sub_type": "办公用房", "building_area": 200},
            {"address": "上海市静安区南京西路", "asset_type": "商业", "sub_type": "商铺", "building_area": 50},
            {"address": "广州市越秀区北京路", "asset_type": "商业", "sub_type": "商场", "building_area": 300},
            {"address": "深圳市福田区华强北", "asset_type": "商业", "sub_type": "商铺", "building_area": 45},
            {"address": "杭州市上城区湖滨路", "asset_type": "商业", "sub_type": "酒店", "building_area": 150},
            {"address": "南京市秦淮区夫子庙", "asset_type": "商业", "sub_type": "商铺", "building_area": 60},
            {"address": "武汉市武昌区楚河汉街", "asset_type": "商业", "sub_type": "商场", "building_area": 250},
            {"address": "成都市青羊区宽窄巷子", "asset_type": "商业", "sub_type": "商铺", "building_area": 55},
            {"address": "重庆市江北区观音桥", "asset_type": "商业", "sub_type": "商场", "building_area": 280},
            {"address": "西安市雁塔区小寨", "asset_type": "商业", "sub_type": "办公用房", "building_area": 180},
            
            # 工业类 (5条)
            {"address": "佛山市南海区狮山镇", "asset_type": "工业", "sub_type": "工业房地产", "building_area": 1000, "land_area": 2000},
            {"address": "东莞市松山湖", "asset_type": "工业", "sub_type": "工业用地", "land_area": 5000},
            {"address": "苏州市工业园区", "asset_type": "工业", "sub_type": "工业房地产", "building_area": 800, "land_area": 1500},
            {"address": "天津市滨海新区", "asset_type": "工业", "sub_type": "工业用地", "land_area": 8000},
            {"address": "青岛市黄岛区", "asset_type": "工业", "sub_type": "工业房地产", "building_area": 1200, "land_area": 2500},
            
            # 土地类 (5条)
            {"address": "成都市高新区", "asset_type": "土地", "sub_type": "商业用地", "land_area": 10000},
            {"address": "武汉市江夏区", "asset_type": "土地", "sub_type": "工业用地", "land_area": 20000},
            {"address": "长沙市岳麓区", "asset_type": "土地", "sub_type": "住宅用地", "land_area": 15000},
            {"address": "郑州市郑东新区", "asset_type": "土地", "sub_type": "综合用地", "land_area": 30000},
            {"address": "合肥市滨湖新区", "asset_type": "土地", "sub_type": "商业用地", "land_area": 12000},
            
            # 特殊资产类 (5条)
            {"address": "山西省大同市", "asset_type": "特殊资产", "sub_type": "采矿权"},
            {"address": "黑龙江省大兴安岭", "asset_type": "特殊资产", "sub_type": "林权"},
            {"address": "山东省烟台市", "asset_type": "特殊资产", "sub_type": "海域使用权"},
            {"address": "云南省昆明市", "asset_type": "特殊资产", "sub_type": "采矿权"},
            {"address": "内蒙古鄂尔多斯", "asset_type": "特殊资产", "sub_type": "采矿权"},
            
            # 边界测试 (5条)
            {"address": "新疆维吾尔自治区乌鲁木齐市", "asset_type": "住宅", "building_area": 150},
            {"address": "香港特别行政区中环", "asset_type": "商业", "sub_type": "办公用房", "building_area": 180},
            {"address": "澳门特别行政区", "asset_type": "商业", "sub_type": "酒店", "building_area": 200},
            {"address": "西藏自治区拉萨市", "asset_type": "住宅", "building_area": 80},
            {"address": "台湾省台北市", "asset_type": "商业", "sub_type": "商铺", "building_area": 60},
        ]
    
    def setup_driver(self):
        """初始化WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except:
            self.driver = webdriver.Chrome(options=options)
        
        self.driver.implicitly_wait(10)
    
    def test_single_case(self, test_case, index):
        """测试单个用例"""
        print(f"[{index+1:02d}] 开始测试: {test_case['address'][:20]}... - {test_case['asset_type']}")
        
        result = {
            "test_id": index + 1,
            "address": test_case["address"],
            "asset_type": test_case["asset_type"],
            "sub_type": test_case.get("sub_type", ""),
            "building_area": test_case.get("building_area", ""),
            "land_area": test_case.get("land_area", ""),
            "start_time": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "case_count": 0,
            "response_time": 0,
            "elapsed_time": 0,
            "has_excel": False,
            "has_json": False
        }
        
        start_time = time.time()
        
        try:
            # 访问主页
            self.driver.get(self.base_url)
            
            # 填写表单
            address_input = self.driver.find_element(By.ID, "address")
            address_input.clear()
            address_input.send_keys(test_case["address"])
            
            # 资产类型
            asset_type_select = Select(self.driver.find_element(By.ID, "asset_type"))
            asset_type_select.select_by_value(test_case["asset_type"])
            time.sleep(0.5)
            
            # 二级分类
            if test_case.get("sub_type"):
                sub_type_select = Select(self.driver.find_element(By.ID, "sub_type"))
                time.sleep(0.3)
                sub_type_select.select_by_value(test_case["sub_type"])
            
            # 建筑面积
            if test_case.get("building_area"):
                building_input = self.driver.find_element(By.ID, "building_area")
                building_input.clear()
                building_input.send_keys(str(test_case["building_area"]))
            
            # 土地面积
            if test_case.get("land_area"):
                land_input = self.driver.find_element(By.ID, "land_area")
                land_input.clear()
                land_input.send_keys(str(test_case["land_area"]))
            
            # 提交表单
            submit_btn = self.driver.find_element(By.ID, "submitBtn")
            submit_btn.click()
            
            # 等待结果
            wait = WebDriverWait(self.driver, 60)
            wait.until(
                EC.or_(
                    EC.presence_of_element_located((By.ID, "resultSection")),
                    EC.presence_of_element_located((By.CLASS_NAME, "error-message")),
                    EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
                )
            )
            
            response_time = time.time() - start_time
            result["response_time"] = round(response_time, 2)
            
            # 检查结果
            try:
                error_el = self.driver.find_element(By.CLASS_NAME, "error-message")
                if error_el.is_displayed() and error_el.text:
                    result["error"] = error_el.text[:100]
                    print(f"[{index+1:02d}] 有错误提示: {result['error'][:40]}...")
            except:
                pass
            
            # 检查成功消息
            try:
                success_el = self.driver.find_element(By.CLASS_NAME, "success-message")
                if success_el.is_displayed() and success_el.text:
                    match = re.search(r'(\d+)', success_el.text)
                    if match:
                        result["case_count"] = int(match.group(1))
                        result["success"] = True
                        print(f"[{index+1:02d}] 成功: {result['case_count']}案例, {response_time:.1f}s")
            except:
                pass
            
            # 检查结果区域
            try:
                result_section = self.driver.find_element(By.ID, "resultSection")
                if result_section.is_displayed():
                    # 从表格获取案例数
                    rows = self.driver.find_elements(By.CSS_SELECTOR, "#resultTableBody tr")
                    if rows:
                        result["case_count"] = len(rows)
                        result["success"] = True
                        
                        # 检查下载按钮
                        try:
                            excel_btn = self.driver.find_element(By.ID, "excelBtn")
                            result["has_excel"] = excel_btn.is_displayed()
                        except:
                            pass
                        
                        try:
                            json_btn = self.driver.find_element(By.ID, "jsonBtn")
                            result["has_json"] = json_btn.is_displayed()
                        except:
                            pass
                        
                        print(f"[{index+1:02d}] 成功: {result['case_count']}案例, {response_time:.1f}s")
            except:
                pass
            
            # 保存截图
            os.makedirs("test_results/screenshots", exist_ok=True)
            screenshot_path = f"test_results/screenshots/test_{index+1:03d}.png"
            self.driver.save_screenshot(screenshot_path)
            
        except TimeoutException:
            result["error"] = "页面加载超时(60s)"
            print(f"[{index+1:02d}] 超时")
            
        except Exception as e:
            result["error"] = str(e)[:100]
            print(f"[{index+1:02d}] 异常: {str(e)[:40]}...")
        
        finally:
            result["elapsed_time"] = round(time.time() - start_time, 2)
            result["end_time"] = datetime.now().isoformat()
            
            # 保存HTML
            os.makedirs("test_results/pages", exist_ok=True)
            html_path = f"test_results/pages/test_{index+1:03d}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
        
        return result
    
    def run_sequential_test(self):
        """顺序测试"""
        print("=" * 60)
        print("开始顺序压力测试")
        print(f"测试用例总数: {len(self.test_cases)}")
        print("=" * 60)
        
        self.setup_driver()
        results = []
        
        try:
            for idx, test_case in enumerate(self.test_cases):
                result = self.test_single_case(test_case, idx)
                results.append(result)
                time.sleep(0.5)
        finally:
            self.driver.quit()
        
        self._generate_report(results, "sequential")
        return results
    
    def run_concurrent_test(self, max_workers=3):
        """并发测试"""
        print("=" * 60)
        print(f"开始并发压力测试 (并发数: {max_workers})")
        print(f"测试用例总数: {len(self.test_cases)}")
        print("=" * 60)
        
        results = []
        groups = [self.test_cases[i:i+max_workers] 
                 for i in range(0, len(self.test_cases), max_workers)]
        
        for group_idx, group in enumerate(groups):
            print(f"\n--- 第 {group_idx+1}/{len(groups)} 组 ({len(group)}个并发) ---")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for idx_in_group, test_case in enumerate(group):
                    global_idx = group_idx * max_workers + idx_in_group
                    future = executor.submit(
                        self._run_single_with_new_driver, 
                        test_case, global_idx
                    )
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures):
                    results.append(future.result())
            
            if group_idx < len(groups) - 1:
                print("等待3秒...")
                time.sleep(3)
        
        self._generate_report(results, f"concurrent_{max_workers}")
        return results
    
    def _run_single_with_new_driver(self, test_case, index):
        """使用新driver运行单个测试"""
        tester = WebBatchTester(self.base_url)
        tester.setup_driver()
        try:
            return tester.test_single_case(test_case, index)
        finally:
            tester.driver.quit()
    
    def _generate_report(self, results, test_type):
        """生成测试报告"""
        os.makedirs("test_results", exist_ok=True)
        
        # CSV报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f"test_results/{test_type}_report_{timestamp}.csv"
        
        fieldnames = ["test_id", "address", "asset_type", "sub_type", 
                     "building_area", "land_area", "success", "case_count",
                     "response_time", "elapsed_time", "has_excel", "has_json",
                     "error", "start_time", "end_time"]
        
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = r.copy()
                if len(row["address"]) > 35:
                    row["address"] = row["address"][:32] + "..."
                writer.writerow(row)
        
        # JSON详细报告
        json_file = f"test_results/{test_type}_detail_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 统计报告
        total = len(results)
        success = sum(1 for r in results if r["success"])
        failed = total - success
        avg_response = sum(r["response_time"] for r in results) / total if total > 0 else 0
        avg_elapsed = sum(r["elapsed_time"] for r in results) / total if total > 0 else 0
        total_cases = sum(r["case_count"] for r in results)
        max_time = max(r["elapsed_time"] for r in results) if results else 0
        min_time = min(r["elapsed_time"] for r in results) if results else 0
        
        # 按类型统计
        type_stats = {}
        for r in results:
            t = r["asset_type"]
            if t not in type_stats:
                type_stats[t] = {"total": 0, "success": 0, "cases": 0}
            type_stats[t]["total"] += 1
            if r["success"]:
                type_stats[t]["success"] += 1
                type_stats[t]["cases"] += r["case_count"]
        
        report_content = f"""
================================================================================
                    网页批量压力测试报告
================================================================================
测试类型: {test_type}
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

【总体统计】
  测试用例总数: {total}
  成功用例数:   {success} ({success/total*100:.1f}%)
  失败用例数:   {failed} ({failed/total*100:.1f}%)
  找到案例总数: {total_cases}

【性能统计】
  平均响应时间: {avg_response:.2f} 秒
  平均总耗时:   {avg_elapsed:.2f} 秒
  最长耗时:     {max_time:.2f} 秒
  最短耗时:     {min_time:.2f} 秒

【各类型统计】
"""
        for t, stats in type_stats.items():
            rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            report_content += f"  {t}: {stats['success']}/{stats['total']} ({rate:.0f}%) - {stats['cases']}案例\n"
        
        # 失败用例详情
        failed_cases = [r for r in results if not r["success"]]
        if failed_cases:
            report_content += "\n【失败用例】\n"
            for r in failed_cases[:10]:
                report_content += f"  #{r['test_id']}: {r['address'][:30]} - {r['error'][:50]}\n"
        
        report_content += """
================================================================================
详细报告文件:
  CSV: {}
  JSON: {}
================================================================================
""".format(csv_file, json_file)
        
        # 保存报告
        report_file = f"test_results/{test_type}_summary_{timestamp}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(report_content)
        print(f"报告已保存到: {report_file}")
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "avg_response": avg_response,
            "total_cases": total_cases,
            "csv_file": csv_file,
            "json_file": json_file,
            "report_file": report_file
        }


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='网页批量压力测试')
    parser.add_argument('--url', default='http://localhost:5000', help='测试URL')
    parser.add_argument('--mode', choices=['sequential', 'concurrent'], default='sequential',
                       help='测试模式: sequential(顺序) 或 concurrent(并发)')
    parser.add_argument('--workers', type=int, default=3, help='并发测试的最大并发数')
    parser.add_argument('--limit', type=int, default=None, help='限制测试用例数量')
    
    args = parser.parse_args()
    
    tester = WebBatchTester(args.url)
    
    if args.limit:
        tester.test_cases = tester.test_cases[:args.limit]
    
    print(f"测试地址: {args.url}")
    print(f"测试用例: {len(tester.test_cases)}条")
    
    if args.mode == 'sequential':
        results = tester.run_sequential_test()
    else:
        results = tester.run_concurrent_test(args.workers)
    
    return results


if __name__ == '__main__':
    main()