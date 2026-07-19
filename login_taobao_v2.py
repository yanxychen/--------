"""
淘宝拍卖登录脚本 v2 - 更可靠的登录检测
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def main():
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    
    print("=" * 60)
    print("  淘宝拍卖登录工具 v2")
    print("=" * 60)
    print()
    print("📱 请用手机淘宝扫描浏览器中的二维码登录")
    print("✅ 登录成功后，请在浏览器中确认已登录")
    print("💬 然后回到这里输入 'ok' 并按回车键")
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
        
        print("\n📱 请在浏览器中扫码登录...")
        print("✅ 登录成功后，在浏览器中确认你已登录淘宝账号")
        print("💬 然后回到这里输入 ok 并按回车键\n")
        
        while True:
            user_input = input("登录完成后输入 ok: ").strip().lower()
            if user_input == 'ok':
                break
            print("请输入 'ok' 确认登录完成\n")
        
        print("\n🔍 正在验证登录状态...")
        try:
            page.goto('https://www.taobao.com', timeout=30000)
            time.sleep(3)
            title = page.title()
            print(f"   淘宝首页标题: {title}")
            
            page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
            time.sleep(5)
            
            content = page.content()
            content_len = len(content)
            print(f"   详情页内容长度: {content_len}")
            
            if content_len > 10000 and '登录' not in page.title():
                print("✅ 登录验证成功！")
                
                print("\n💾 正在保存登录状态...")
                context.storage_state(path=storage_path)
                print(f"✅ 登录状态已保存到: {storage_path}")
                print("\n🎉 登录完成！现在搜索会自动获取完整的详情页数据")
            else:
                print("❌ 登录验证失败，请重试")
        except Exception as e:
            print(f"❌ 验证出错: {e}")
        
        print()
        print("浏览器将在10秒后自动关闭...")
        time.sleep(10)
        browser.close()


if __name__ == '__main__':
    main()
