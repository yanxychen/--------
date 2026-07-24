"""
交互式淘宝登录脚本 - 通过文件通信
步骤：
1. 打开登录页
2. 输入手机号
3. 点击获取验证码
4. 等待用户提供验证码（通过 code.txt 文件）
5. 输入验证码登录
6. 保存登录状态
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def write_status(msg):
    """写入状态到文件"""
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_status.txt')
    with open(status_file, 'w', encoding='utf-8') as f:
        f.write(msg)
    print(f"[状态] {msg}")


def read_code():
    """读取验证码文件"""
    code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_code.txt')
    if os.path.exists(code_file):
        with open(code_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def main():
    phone = sys.argv[1] if len(sys.argv) > 1 else ''
    
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_code.txt')
    
    # 清理旧的验证码文件
    if os.path.exists(code_file):
        os.remove(code_file)
    
    write_status("正在启动浏览器...")
    
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
        
        write_status("正在打开淘宝登录页面...")
        page.goto('https://login.taobao.com/', timeout=60000)
        time.sleep(3)
        
        # 切换到密码登录（如果默认是扫码的话）
        try:
            # 尝试点击"密码登录"
            page.click('text=密码登录', timeout=3000)
            time.sleep(1)
        except:
            pass
        
        # 尝试切换到手机号验证码登录
        try:
            # 点击"短信登录"或类似选项
            sms_login = page.get_by_text('短信登录', exact=False)
            if sms_login.count() > 0:
                sms_login.first.click()
                time.sleep(1)
                write_status("已切换到短信登录")
        except:
            pass
        
        write_status(f"正在输入手机号: {phone}...")
        
        # 输入手机号 - 尝试多种选择器
        phone_input = None
        selectors = [
            'input[name="fm-login-id"]',
            'input[placeholder*="手机号"]',
            'input[type="tel"]',
            '#fm-login-id',
        ]
        
        for selector in selectors:
            try:
                el = page.locator(selector)
                if el.count() > 0:
                    phone_input = el.first
                    break
            except:
                continue
        
        if not phone_input:
            # 尝试通过label找
            try:
                phone_input = page.get_by_role('textbox', name='手机号/会员名/邮箱')
                if phone_input.count() == 0:
                    phone_input = page.get_by_role('textbox').first
            except:
                phone_input = page.locator('input').first
        
        if phone_input:
            phone_input.click()
            time.sleep(0.5)
            phone_input.fill(phone)
            time.sleep(1)
            write_status("手机号已输入，正在点击获取验证码...")
        
        # 点击获取验证码按钮
        code_button = None
        code_selectors = [
            'text=获取验证码',
            'text=发送验证码',
            'button:has-text("获取验证码")',
            '#J_GetCode',
            '.get-code-btn',
        ]
        
        for selector in code_selectors:
            try:
                btn = page.locator(selector)
                if btn.count() > 0 and btn.first.is_visible():
                    code_button = btn.first
                    break
            except:
                continue
        
        if code_button:
            try:
                code_button.click()
                write_status("✅ 验证码已发送！请查看手机短信")
            except Exception as e:
                write_status(f"点击获取验证码失败: {e}")
        else:
            write_status("⚠️  未找到获取验证码按钮，请手动点击")
        
        # 等待验证码文件
        write_status("等待用户提供验证码...（请把验证码发给我）")
        
        max_wait = 300  # 最多等5分钟
        for i in range(max_wait):
            time.sleep(1)
            
            code = read_code()
            if code and len(code) >= 4:
                write_status(f"收到验证码: {code}，正在输入...")
                
                # 输入验证码
                code_input_selectors = [
                    'input[name="fm-login-checkcode"]',
                    'input[placeholder*="验证码"]',
                    '#fm-login-checkcode',
                    'input[type="text"]',
                ]
                
                code_input = None
                for selector in code_input_selectors:
                    try:
                        el = page.locator(selector)
                        if el.count() > 0 and el.first.is_visible():
                            # 确认是验证码输入框（不是密码框）
                            placeholder = el.first.get_attribute('placeholder') or ''
                            if '验证码' in placeholder or 'checkcode' in selector.lower():
                                code_input = el.first
                                break
                    except:
                        continue
                
                if not code_input:
                    # 找第二个输入框（通常是验证码）
                    try:
                        inputs = page.locator('input[type="text"]')
                        if inputs.count() >= 2:
                            code_input = inputs.nth(1)
                        else:
                            code_input = inputs.first
                    except:
                        code_input = page.locator('input').nth(1)
                
                if code_input:
                    code_input.click()
                    time.sleep(0.5)
                    code_input.fill(code)
                    time.sleep(1)
                    write_status("验证码已输入，正在登录...")
                
                # 点击登录按钮
                login_btn_selectors = [
                    'text=登录',
                    'button:has-text("登录")',
                    '#J_SubmitStatic',
                    '.fm-button',
                    'button[type="submit"]',
                ]
                
                login_btn = None
                for selector in login_btn_selectors:
                    try:
                        btn = page.locator(selector)
                        if btn.count() > 0 and btn.first.is_visible():
                            text = btn.first.inner_text() or ''
                            if '登录' in text and '注册' not in text:
                                login_btn = btn.first
                                break
                    except:
                        continue
                
                if login_btn:
                    try:
                        login_btn.click()
                        write_status("已点击登录按钮，等待登录结果...")
                    except Exception as e:
                        write_status(f"点击登录失败: {e}")
                
                # 等待登录结果
                for j in range(30):
                    time.sleep(2)
                    current_url = page.url
                    
                    if 'login' not in current_url and 'taobao.com' in current_url:
                        write_status("🎉 登录成功！正在保存状态...")
                        time.sleep(3)
                        
                        # 验证一下
                        try:
                            page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
                            time.sleep(5)
                            content = page.content()
                            if len(content) > 10000:
                                write_status("✅ 详情页访问正常，正在保存登录状态...")
                                context.storage_state(path=storage_path)
                                write_status(f"✅ 登录状态已保存到: {storage_path}")
                                write_status("登录完成！浏览器将在30秒后关闭")
                                time.sleep(30)
                                browser.close()
                                return
                        except:
                            pass
                        
                        # 即使验证失败也保存
                        context.storage_state(path=storage_path)
                        write_status(f"✅ 登录状态已保存到: {storage_path}")
                        write_status("登录完成！浏览器将在30秒后关闭")
                        time.sleep(30)
                        browser.close()
                        return
                
                write_status("⚠️  登录可能失败，请检查")
                break
            
            # 每10秒打印一次等待状态
            if i % 10 == 0:
                write_status(f"等待验证码中... ({i}s)")
        
        write_status("⏰ 等待超时")
        time.sleep(10)
        browser.close()


if __name__ == '__main__':
    main()
