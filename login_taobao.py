"""
淘宝拍卖登录脚本
第一次使用时运行此脚本，扫码登录淘宝账号
登录成功后会自动保存登录状态，后续搜索可自动使用
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from taobao_playwright_crawler import TaobaoDetailCrawler


def main():
    print("=" * 60)
    print("  淘宝拍卖登录工具")
    print("=" * 60)
    print()
    print("📋 使用说明：")
    print("  1. 即将打开浏览器，进入淘宝登录页面")
    print("  2. 请使用手机淘宝扫码登录")
    print("  3. 登录成功后，回到此窗口按回车键")
    print("  4. 登录状态会自动保存，后续搜索可全自动获取详情页数据")
    print()
    print("⚠️  注意事项：")
    print("  - 登录状态大约可保存 7-15 天")
    print("  - 如果后续搜索提示未登录，重新运行此脚本即可")
    print()
    
    input("按回车键开始登录...")
    
    crawler = TaobaoDetailCrawler(headless=False)
    
    try:
        crawler.start()
        print("\n🌐 浏览器已打开，请在浏览器中登录淘宝...")
        crawler.interactive_login()
        
        print("\n🔍 验证登录状态...")
        if crawler.is_logged_in():
            print("✅ 登录成功！以后搜索将自动获取完整详情页数据")
        else:
            print("❌ 登录验证失败，请重试")
            
    except Exception as e:
        print(f"❌ 登录出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.close()
    
    print()
    input("按回车键退出...")


if __name__ == '__main__':
    main()
