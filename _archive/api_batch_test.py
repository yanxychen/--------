#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API批量压力测试脚本

直接测试 Flask API，无需浏览器，更轻量更快速
"""

import requests
import json
import csv
import os
import time
import concurrent.futures
from datetime import datetime
from urllib.parse import quote


class APIBatchTester:
    """API批量测试器"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
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
    
    def test_single_case(self, test_case, index):
        """测试单个用例"""
        print(f"[{index+1:02d}] 测试: {test_case['address'][:25]}... - {test_case['asset_type']}")
        
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
            "status": None,
            "case_count": 0,
            "response_time": 0,
            "elapsed_time": 0,
            "result_id": None,
            "excel_downloaded": False,
            "json_downloaded": False
        }
        
        start_time = time.time()
        
        try:
            # 构建请求
            payload = {
                "address": test_case["address"],
                "asset_type": test_case["asset_type"],
                "max_results": 20
            }
            
            if test_case.get("sub_type"):
                payload["sub_type"] = test_case["sub_type"]
            if test_case.get("building_area"):
                payload["building_area"] = test_case["building_area"]
            if test_case.get("land_area"):
                payload["land_area"] = test_case["land_area"]
            
            # 发送请求
            resp = requests.post(
                f"{self.base_url}/api/valuate",
                json=payload,
                timeout=120
            )
            
            response_time = time.time() - start_time
            result["response_time"] = round(response_time, 2)
            
            if resp.status_code != 200:
                result["error"] = f"HTTP {resp.status_code}"
                result["status"] = "http_error"
                print(f"[{index+1:02d}] HTTP错误: {resp.status_code}")
                return result
            
            data = resp.json()
            result["status"] = data.get("status", "unknown")
            
            if data.get("status") == "success":
                result["success"] = True
                result["case_count"] = len(data.get("cases", []))
                result["result_id"] = data.get("result_id")
                
                stats = data.get("statistics", {})
                if stats:
                    result["avg_price"] = stats.get("reference_avg_price", "")
                
                print(f"[{index+1:02d}] 成功: {result['case_count']}案例, {response_time:.1f}s")
                
                # 测试Excel下载
                if result["result_id"]:
                    try:
                        excel_resp = requests.get(
                            f"{self.base_url}/api/download/excel/{result['result_id']}",
                            timeout=30
                        )
                        if excel_resp.status_code == 200:
                            result["excel_downloaded"] = True
                    except:
                        pass
                    
                    # 测试JSON下载
                    try:
                        json_resp = requests.get(
                            f"{self.base_url}/api/download/json/{result['result_id']}",
                            timeout=30
                        )
                        if json_resp.status_code == 200:
                            result["json_downloaded"] = True
                    except:
                        pass
                
            elif data.get("status") == "no_cases":
                result["success"] = True  # 无案例也算成功（API正常响应）
                result["error"] = data.get("message", "无匹配案例")[:80]
                print(f"[{index+1:02d}] 无案例: {test_case['asset_type']}")
                
            else:
                result["error"] = data.get("error", "未知错误")[:80]
                print(f"[{index+1:02d}] API错误: {result['error'][:40]}")
                
        except requests.Timeout:
            result["error"] = "请求超时(120s)"
            result["status"] = "timeout"
            print(f"[{index+1:02d}] 超时")
            
        except requests.ConnectionError:
            result["error"] = "连接失败"
            result["status"] = "connection_error"
            print(f"[{index+1:02d}] 连接失败")
            
        except Exception as e:
            result["error"] = str(e)[:80]
            result["status"] = "exception"
            print(f"[{index+1:02d}] 异常: {str(e)[:40]}")
        
        finally:
            result["elapsed_time"] = round(time.time() - start_time, 2)
            result["end_time"] = datetime.now().isoformat()
        
        return result
    
    def run_sequential_test(self):
        """顺序测试"""
        print("=" * 60)
        print("开始顺序压力测试")
        print(f"测试用例总数: {len(self.test_cases)}")
        print("=" * 60)
        
        results = []
        for idx, test_case in enumerate(self.test_cases):
            result = self.test_single_case(test_case, idx)
            results.append(result)
            time.sleep(0.3)  # 间隔
        
        self._generate_report(results, "sequential")
        return results
    
    def run_concurrent_test(self, max_workers=5):
        """并发测试"""
        print("=" * 60)
        print(f"开始并发压力测试 (并发数: {max_workers})")
        print(f"测试用例总数: {len(self.test_cases)}")
        print("=" * 60)
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.test_single_case, tc, idx): idx
                for idx, tc in enumerate(self.test_cases)
            }
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        # 按test_id排序
        results.sort(key=lambda x: x["test_id"])
        
        self._generate_report(results, f"concurrent_{max_workers}")
        return results
    
    def _generate_report(self, results, test_type):
        """生成测试报告"""
        os.makedirs("test_results", exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV报告
        csv_file = f"test_results/api_{test_type}_report_{timestamp}.csv"
        fieldnames = ["test_id", "address", "asset_type", "sub_type",
                     "building_area", "land_area", "success", "status",
                     "case_count", "response_time", "elapsed_time",
                     "result_id", "avg_price", "excel_downloaded", "json_downloaded", 
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
        json_file = f"test_results/api_{test_type}_detail_{timestamp}.json"
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
        
        excel_ok = sum(1 for r in results if r["excel_downloaded"])
        json_ok = sum(1 for r in results if r["json_downloaded"])
        
        # 按类型统计
        type_stats = {}
        for r in results:
            t = r["asset_type"]
            if t not in type_stats:
                type_stats[t] = {"total": 0, "success": 0, "cases": 0, "no_cases": 0}
            type_stats[t]["total"] += 1
            if r["success"]:
                type_stats[t]["success"] += 1
                type_stats[t]["cases"] += r["case_count"]
                if r["case_count"] == 0:
                    type_stats[t]["no_cases"] += 1
        
        report_content = f"""
================================================================================
                    API批量压力测试报告
================================================================================
测试类型: {test_type}
测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试地址: {self.base_url}
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

【下载功能测试】
  Excel下载成功: {excel_ok}/{success} ({excel_ok/success*100:.1f}%)
  JSON下载成功:  {json_ok}/{success} ({json_ok/success*100:.1f}%)

【各类型统计】
"""
        for t, stats in type_stats.items():
            rate = stats["success"] / stats["total"] * 100 if stats["total"] > 0 else 0
            report_content += f"  {t}: {stats['success']}/{stats['total']} ({rate:.0f}%) - {stats['cases']}案例, {stats['no_cases']}无案例\n"
        
        # 失败用例详情
        failed_cases = [r for r in results if not r["success"]]
        if failed_cases:
            report_content += "\n【失败用例】\n"
            for r in failed_cases[:10]:
                report_content += f"  #{r['test_id']}: {r['address'][:30]} - {r.get('error', '未知')[:40]}\n"
        
        report_content += f"""
================================================================================
详细报告文件:
  CSV: {csv_file}
  JSON: {json_file}
================================================================================
"""
        
        # 保存报告
        report_file = f"test_results/api_{test_type}_summary_{timestamp}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(report_content)
        print(f"报告已保存到: {report_file}")
        
        return {
            "total": total,
            "success": success,
            "avg_response": avg_response,
            "csv_file": csv_file,
            "json_file": json_file,
            "report_file": report_file
        }


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='API批量压力测试')
    parser.add_argument('--url', default='http://localhost:5000', help='测试URL')
    parser.add_argument('--mode', choices=['sequential', 'concurrent'], default='sequential',
                       help='测试模式')
    parser.add_argument('--workers', type=int, default=5, help='并发数')
    parser.add_argument('--limit', type=int, default=None, help='限制用例数')
    
    args = parser.parse_args()
    
    tester = APIBatchTester(args.url)
    
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