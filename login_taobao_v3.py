"""
淘宝拍卖登录脚本 v3 - 更可靠的检测
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def main():
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    
    print("=" * 60)
    print("  淘宝拍卖登录工具 v3")
    print("=" * 60)
    print()
    print("📱 请用手机淘宝扫描浏览器中的二维码登录")
    print("⏳ 登录成功后系统会自动检测并保存状态")
    print("💡 最多等待10分钟")
    print()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800},
        )
        
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        print("🌐 正在打开淘宝登录页面...")
        page.goto('https://login.taobao.com/', timeout=60000)
        
        logged_in = False
        max_wait = 600  # 最多等10分钟
        
        for i in range(max_wait):
            time.sleep(1)
            
            try:
                current_url = page.url
                title = page.title()
                
                if i % 5 == 0:
                    print(f"  等待登录... ({i}s) URL: {current_url[:60]}", end='\r')
                
                if 'login' not in current_url and 'taobao.com' in current_url:
                    print(f"\n\n✅ 检测到页面跳转，可能已登录！")
                    print(f"   当前URL: {current_url}")
                    print(f"   页面标题: {title}")
                    
                    time.sleep(3)
                    
                    print("\n🔍 正在访问拍卖详情页验证登录状态...")
                    try:
                        page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
                        time.sleep(5)
                        
                        content = page.content()
                        content_len = len(content)
                        detail_title = page.title()
                        
                        print(f"   详情页标题: {detail_title}")
                        print(f"   详情页内容长度: {content_len}")
                        
                        if content_len > 10000 and '登录' not in detail_title and 'login' not in page.url:
                            print("\n🎉 登录验证成功！")
                            logged_in = True
                            break
                        else:
                            print("⚠️  详情页内容不足，可能未登录成功")
                            print("   继续等待...")
                            page.goto('https://www.taobao.com', timeout=30000)
                    except Exception as e:
                        print(f"   访问详情页出错: {e}")
                        print("   继续等待...")
                        
            except Exception as e:
                if i % 10 == 0:
                    print(f"  等待登录... ({i}s) - 检测中", end='\r')
        
        if logged_in:
            print("\n💾 正在保存登录状态...")
            context.storage_state(path=storage_path)
            print(f"✅ 登录状态已保存到: {storage_path}")
            print("\n🎉 登录完成！现在搜索会自动获取完整的详情页数据")
            print("\n⚠️  浏览器将在60秒后自动关闭，请确认登录成功")
            time.sleep(60)
        else:
            print("\n\n⏰ 等待超时，请重新运行登录脚本")
            print("浏览器将在10秒后关闭...")
            time.sleep(10)
        
        browser.close()


if __name__ == '__main__':
    main()
