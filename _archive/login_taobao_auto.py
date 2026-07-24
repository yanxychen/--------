"""
自动登录脚本 - 自动检测登录状态并保存
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def main():
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    
    print("=" * 60)
    print("  淘宝拍卖登录工具")
    print("=" * 60)
    print()
    print("📱 请用手机淘宝扫描浏览器中的二维码登录")
    print("⏳ 登录成功后会自动检测并保存状态")
    print("💡 请在浏览器中完成登录操作...")
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
        max_wait = 300  # 最多等5分钟
        
        for i in range(max_wait):
            time.sleep(2)
            
            title = page.title()
            url = page.url
            
            print(f"  等待登录... ({i*2}s) 当前页面: {title[:40]}", end='\r')
            
            if '我的淘宝' in title or '首页' in title or 'taobao.com' in url and 'login' not in url:
                if 'login' not in url:
                    print(f"\n✅ 检测到登录成功！当前页面: {title}")
                    logged_in = True
                    break
            
            if 'sf-item.taobao.com' in url:
                print(f"\n✅ 检测到登录成功！已跳转到拍卖页")
                logged_in = True
                break
        
        if logged_in:
            print("\n💾 正在保存登录状态...")
            context.storage_state(path=storage_path)
            print(f"✅ 登录状态已保存到: {storage_path}")
            print("\n🎉 登录完成！现在搜索会自动获取完整的详情页数据")
        else:
            print("\n⏰ 等待超时，请重新运行登录脚本")
        
        print()
        print("浏览器将在10秒后自动关闭...")
        time.sleep(10)
        browser.close()


if __name__ == '__main__':
    main()
