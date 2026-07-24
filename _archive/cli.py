#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不良资产估值工具 - 命令行界面

用法:
    asset_valuation valuation <地址> --type 住宅 [--sub-type 商铺] [--building-area 100] [--max 20] [--excel output.xlsx]
    asset_valuation search <地址> [--type 住宅|商业|工业|特殊] [--max 10]
    asset_valuation interactive
    asset_valuation info
"""

import argparse
import sys
import json
import os


def create_parser():
    parser = argparse.ArgumentParser(
        prog='asset_valuation',
        description='不良资产估值工具 - 搜索京东拍卖和淘宝司法拍卖参考案例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 估值模式（推荐）- 8列标准格式+Excel导出）
  asset_valuation valuation 北京 --type 住宅 --building-area 100 --excel result.xlsx

  # 商业地产估值（子类型
  asset_valuation valuation 上海 --type 商业 --sub-type 商铺 --excel result.xlsx

  # 普通搜索模式
  asset_valuation search 北京 --type 住宅

  # 交互式模式
  asset_valuation interactive

资产类型:
  住宅 - 时间范围1年，距离范围5公里
  商业 - 时间范围2年，距离范围10公里（商铺/商场/办公用房/酒店/住宅底商
  工业 - 时间范围2年，距离范围15公里（工业房地产/工业用地）
  土地 - 时间范围3年，距离范围20公里（住宅/商业/工业/综合用地
  特殊资产 - 时间范围3年，距离范围20公里（采矿权/林权/海域使用权
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # valuation 子命令（估值模式）
    val_parser = subparsers.add_parser(
        'valuation',
        help='估值模式（8列标准格式）',
        description='根据地址和资产类型搜索参考案例，输出8列标准格式，支持Excel导出'
    )
    val_parser.add_argument(
        'address',
        help='目标地址（如: 北京朝阳区、上海浦东、深圳南山）'
    )
    val_parser.add_argument(
        '--type', '-t',
        choices=['住宅', '商业', '工业', '土地', '特殊资产'],
        default='住宅',
        help='资产类型（默认: 住宅）'
    )
    val_parser.add_argument(
        '--sub-type', '-s',
        help='资产子类型（如: 商铺、工业厂房等）'
    )
    val_parser.add_argument(
        '--building-area', '-b',
        type=float,
        help='建筑面积（平方米）'
    )
    val_parser.add_argument(
        '--land-area', '-l',
        type=float,
        help='土地面积（平方米）'
    )
    val_parser.add_argument(
        '--max', '-m',
        type=int,
        default=20,
        help='最大结果数（默认: 20）'
    )
    val_parser.add_argument(
        '--excel', '-e',
        help='导出到Excel文件'
    )
    val_parser.add_argument(
        '--gaode-key',
        help='高德地图API Key（可选，用于距离计算）'
    )
    val_parser.add_argument(
        '--output', '-o',
        help='保存结果到JSON文件'
    )
    
    # search 子命令（普通搜索）
    search_parser = subparsers.add_parser(
        'search',
        help='普通搜索模式',
        description='根据地址和资产类型搜索拍卖案例'
    )
    search_parser.add_argument(
        'address',
        help='目标地址（如: 北京、上海浦东、深圳南山）'
    )
    search_parser.add_argument(
        '--type', '-t',
        choices=['住宅', '商业', '工业', '特殊'],
        default='住宅',
        help='资产类型（默认: 住宅）'
    )
    search_parser.add_argument(
        '--max', '-m',
        type=int,
        default=10,
        help='每个平台最大结果数（默认: 10）'
    )
    search_parser.add_argument(
        '--api',
        action='store_true',
        default=True,
        help='使用API模式（快速，推荐）'
    )
    search_parser.add_argument(
        '--selenium',
        action='store_true',
        help='使用Selenium模式（更稳定，需要浏览器）'
    )
    search_parser.add_argument(
        '--output', '-o',
        help='保存结果到JSON文件'
    )
    search_parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='无头模式运行（不显示浏览器窗口，默认开启）'
    )
    search_parser.add_argument(
        '--show-browser',
        action='store_true',
        help='显示浏览器窗口（调试用）'
    )
    
    # interactive 子命令
    interactive_parser = subparsers.add_parser(
        'interactive',
        help='交互式模式',
        description='通过问答方式输入参数'
    )
    interactive_parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='无头模式运行（默认开启）'
    )
    
    # info 子命令
    info_parser = subparsers.add_parser(
        'info',
        help='显示配置信息',
        description='显示各资产类型的搜索配置'
    )
    
    return parser


def cmd_valuation(args):
    """执行估值命令"""
    from asset_valuation_tool import AssetValuationTool
    from excel_renderer import ExcelRenderer
    
    gaode_key = args.gaode_key or os.environ.get('GAODE_API_KEY', '')
    
    tool = AssetValuationTool(gaode_api_key=gaode_key)
    
    try:
        result = tool.search_cases(
            address=args.address,
            asset_type=args.type,
            sub_type=args.sub_type,
            building_area=args.building_area,
            land_area=args.land_area,
            max_results=args.max
        )
        
        tool.print_results(result)
        
        # 导出Excel
        if args.excel and result.get('status') == 'success':
            renderer = ExcelRenderer()
            cases = result.get('cases', [])
            stats = result.get('statistics', {})
            renderer.render_to_excel(
                cases=cases,
                output_path=args.excel,
                title=f"不良资产估值 - {args.address} - {args.type}",
                statistics=stats
            )
        
        # 保存JSON
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n✓ 结果已保存到: {args.output}")
        
        return 0 if result.get('status') == 'success' else 1
        
    except KeyboardInterrupt:
        print('\n用户中断')
        return 130
    except Exception as e:
        print(f'\n错误: {e}')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tool.cleanup()


def cmd_search(args):
    """执行搜索命令"""
    headless = not args.show_browser
    
    if args.selenium or not args.api:
        try:
            from asset_search_selenium import SeleniumAssetSearchTool
            tool = SeleniumAssetSearchTool(headless=headless)
            
            result = tool.search_cases(
                address=args.address,
                asset_type=args.type,
                max_results=args.max,
                fetch_details=False
            )
            
            tool.print_results(result)
            
            if args.output:
                tool.save_results(result, args.output)
            
            return 0 if result['total_results'] > 0 else 1
            
        except ImportError:
            print('错误: Selenium模式需要安装selenium库')
            print('请运行: pip install selenium webdriver-manager')
            return 1
        except Exception as e:
            print(f'\n错误: {e}')
            return 1
        finally:
            try:
                tool.cleanup()
            except:
                pass
    else:
        from asset_search_api import APIAssetSearchTool
        
        tool = APIAssetSearchTool()
        
        try:
            result = tool.search_cases(
                address=args.address,
                asset_type=args.type,
                max_results=args.max
            )
            
            tool.print_results(result)
            
            if args.output:
                tool.save_results(result, args.output)
            
            return 0 if result['total_results'] > 0 else 1
            
        except KeyboardInterrupt:
            print('\n用户中断')
            return 130
        except Exception as e:
            print(f'\n错误: {e}')
            return 1
        finally:
            tool.cleanup()


def cmd_interactive(args):
    """执行交互式命令"""
    print('\n' + '=' * 60)
    print('📊 不良资产估值工具')
    print('=' * 60)
    
    while True:
        address = input('\n请输入目标地址: ').strip()
        if address:
            break
        print('地址不能为空，请重新输入')
    
    from asset_valuation_tool import AssetValuationTool
    
    tool = AssetValuationTool()
    
    print('\n资产类型选项:')
    types = tool.get_all_types()
    for idx, type_name in enumerate(types, 1):
        print(f'  {idx}. {type_name}')
    
    while True:
        type_input = input(f'\n请选择资产类型 (1-{len(types)}, 默认1): ').strip()
        if not type_input:
            asset_type = types[0]
            break
        if type_input.isdigit() and 1 <= int(type_input) <= len(types):
            asset_type = types[int(type_input) - 1]
            break
        print('无效选项，请重新输入')
    
    sub_type = None
    sub_types = tool.get_sub_types(asset_type)
    if sub_types:
        print(f'\n{asset_type}子类型:')
        for idx, st in enumerate(sub_types, 1):
            print(f'  {idx}. {st}')
        sub_input = input(f'\n请选择子类型 (直接回车跳过): ').strip()
        if sub_input.isdigit() and 1 <= int(sub_input) <= len(sub_types):
            sub_type = sub_types[int(sub_input) - 1]
    
    building_area = None
    area_input = input('\n请输入建筑面积(㎡，直接回车跳过): ').strip()
    if area_input and area_input.replace('.', '').isdigit():
        building_area = float(area_input)
    
    max_input = input('最大结果数 (默认20): ').strip()
    max_results = int(max_input) if max_input.isdigit() else 20
    
    excel_input = input('\n是否导出Excel? (y/n, 默认y): ').strip().lower()
    export_excel = excel_input != 'n'
    
    try:
        result = tool.search_cases(
            address=address,
            asset_type=asset_type,
            sub_type=sub_type,
            building_area=building_area,
            max_results=max_results
        )
        
        tool.print_results(result)
        
        if result.get('status') == 'success':
            if export_excel:
                from excel_renderer import ExcelRenderer
                renderer = ExcelRenderer()
                filename = f"valuation_{address.replace('/', '_')}.xlsx"
                renderer.render_to_excel(
                    cases=result.get('cases', []),
                    output_path=filename,
                    title=f"不良资产估值 - {address} - {asset_type}",
                    statistics=result.get('statistics', {})
                )
            
            save_input = input('\n是否保存JSON结果? (y/n): ').strip().lower()
            if save_input == 'y':
                filename = f"valuation_{address.replace('/', '_')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                print(f"✓ 结果已保存到: {filename}")
        
        return 0
        
    except KeyboardInterrupt:
        print('\n用户中断')
        return 130
    except Exception as e:
        print(f'\n错误: {e}')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tool.cleanup()


def cmd_info(args):
    """显示配置信息"""
    from asset_valuation_tool import AssetValuationTool
    
    tool = AssetValuationTool()
    
    print('\n' + '=' * 60)
    print('📊 资产类型配置')
    print('=' * 60)
    
    for type_name in tool.get_all_types():
        sub_types = tool.get_sub_types(type_name)
        print(f'\n【{type_name}】')
        if sub_types:
            print(f'  子类型: {", ".join(sub_types)}')
        else:
            print(f'  子类型: 无')
    
    print('\n' + '=' * 60)
    print('支持平台:')
    print('  - 京东拍卖 (api.m.jd.com)')
    print('  - 淘宝司法拍卖 (sf.taobao.com)')
    print('\n输出格式:')
    print('  8列标准格式: 参照物位置、土地面积、建筑面积、')
    print('  市场价值、建筑单价、数据来源、备注、价格类型')
    print('\nExcel导出:')
    print('  支持 --excel 参数导出Excel文件')
    print('=' * 60)
    
    return 0


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == 'valuation':
        return cmd_valuation(args)
    elif args.command == 'search':
        return cmd_search(args)
    elif args.command == 'interactive':
        return cmd_interactive(args)
    elif args.command == 'info':
        return cmd_info(args)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())