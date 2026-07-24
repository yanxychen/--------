"""
淘宝扫码登录 - 最简单可靠的方式
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def write_status(msg):
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_status.txt')
    with open(status_file, 'w', encoding='utf-8') as f:
        f.write(msg)
    print(f"[状态] {msg}")


def main():
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    
    write_status("正在启动浏览器...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900},
            locale='zh-CN',
        )
        
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)
        
        write_status("正在打开淘宝扫码登录页面...")
        
        # 直接打开登录页，默认应该就是扫码登录
        page.goto('https://login.taobao.com/', timeout=60000)
        time.sleep(3)
        
        # 确保是扫码登录（点击左边的二维码区域）
        try:
            qr_tab = page.get_by_text('手机扫码登录')
            if qr_tab.count() > 0:
                qr_tab.first.click()
                time.sleep(2)
        except:
            pass
        
        write_status("📱 请用手机淘宝扫描浏览器中的二维码登录")
        write_status("⏳ 登录成功后系统会自动检测并保存状态")
        
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        page.screenshot(path=os.path.join(screenshot_dir, 'qr_login.png'), full_page=True)
        
        # 等待登录成功
        max_wait = 600  # 最多等10分钟
        logged_in = False
        
        for i in range(max_wait):
            time.sleep(2)
            
            try:
                current_url = page.url
                title = page.title()
                
                if i % 10 == 0:
                    write_status(f"等待扫码登录中... ({i*2}s)")
                
                # 检测登录成功：URL不再包含login，页面标题不包含登录
                if 'login' not in current_url and ('taobao.com' in current_url or 'tmall.com' in current_url):
                    if '登录' not in title and 'login' not in title.lower():
                        write_status(f"🎉 检测到登录成功！")
                        write_status(f"当前URL: {current_url[:80]}")
                        write_status(f"页面标题: {title}")
                        logged_in = True
                        break
                        
                # 也可以检测是否跳转到了淘宝首页
                if 'www.taobao.com' in current_url and 'login' not in current_url:
                    write_status("🎉 跳转到淘宝首页，登录成功！")
                    logged_in = True
                    break
                    
            except Exception as e:
                if i % 20 == 0:
                    write_status(f"等待中... ({i*2}s)")
        
        if logged_in:
            time.sleep(3)
            
            # 保存截图
            page.screenshot(path=os.path.join(screenshot_dir, 'login_success.png'), full_page=True)
            
            write_status("🔍 正在访问拍卖详情页验证登录状态...")
            try:
                page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
                time.sleep(5)
                
                content = page.content()
                content_len = len(content)
                detail_title = page.title()
                
                page.screenshot(path=os.path.join(screenshot_dir, 'detail_verify.png'), full_page=True)
                
                write_status(f"详情页标题: {detail_title}")
                write_status(f"详情页内容长度: {content_len}")
                
                if content_len > 10000 and '登录' not in detail_title and 'login' not in page.url:
                    write_status("✅ 详情页访问正常，正在保存登录状态...")
                    context.storage_state(path=storage_path)
                    write_status(f"✅ 登录状态已保存到: {storage_path}")
                    write_status("🎉 登录完成！现在搜索会自动获取完整的详情页数据")
                    write_status("浏览器将在60秒后自动关闭")
                    time.sleep(60)
                    browser.close()
                    return
                else:
                    write_status("⚠️  详情页访问可能受限，仍保存登录状态...")
            except Exception as e:
                write_status(f"验证详情页出错: {e}")
            
            # 无论如何都保存状态
            context.storage_state(path=storage_path)
            write_status(f"✅ 登录状态已保存到: {storage_path}")
            write_status("浏览器将在60秒后自动关闭")
            time.sleep(60)
        else:
            write_status("⏰ 等待超时，请重新运行登录脚本")
            time.sleep(10)
        
        browser.close()


if __name__ == '__main__':
    main()
