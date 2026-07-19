"""
交互式淘宝登录脚本 v2 - 更可靠
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


def read_code():
    code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_code.txt')
    if os.path.exists(code_file):
        with open(code_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None


def save_screenshot(page, name):
    """保存截图用于调试"""
    screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    path = os.path.join(screenshot_dir, f'{name}.png')
    page.screenshot(path=path, full_page=True)
    print(f"   截图已保存: {path}")


def main():
    phone = sys.argv[1] if len(sys.argv) > 1 else '13672840333'
    
    storage_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'taobao_storage_state.json')
    code_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_code.txt')
    
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
        
        write_status("正在打开淘宝登录页面...")
        page.goto('https://login.taobao.com/', timeout=60000)
        time.sleep(5)
        
        save_screenshot(page, '01_login_page')
        write_status(f"页面已打开，标题: {page.title()}")
        
        # 尝试切换到短信登录
        try:
            # 找"短信登录"、"验证码登录"等按钮
            sms_texts = ['短信登录', '验证码登录', '手机登录', '扫码登录']
            for text in sms_texts:
                try:
                    btn = page.get_by_text(text, exact=False)
                    if btn.count() > 0 and btn.first.is_visible():
                        write_status(f"找到按钮: {text}，点击切换")
                        btn.first.click()
                        time.sleep(2)
                        save_screenshot(page, f'02_after_{text}')
                        break
                except:
                    continue
        except Exception as e:
            write_status(f"切换登录方式时出错: {e}")
        
        # 检查国家/地区选择
        try:
            # 找国家选择器，确保是 +86 中国大陆
            country_selectors = [
                'select[name="country"]',
                '.country-select',
                '.J_CountrySelect',
                '[class*="country"]',
            ]
            
            for sel in country_selectors:
                try:
                    el = page.locator(sel)
                    if el.count() > 0 and el.first.is_visible():
                        write_status(f"找到国家选择器: {sel}")
                        # 尝试选择 +86
                        try:
                            el.first.select_option(value='CN')
                        except:
                            try:
                                el.first.select_option(label='中国大陆')
                            except:
                                pass
                        time.sleep(1)
                        break
                except:
                    continue
            
            # 也可能是点击式的选择
            try:
                area_code = page.locator('text=+86')
                if area_code.count() > 0:
                    write_status("已确认是 +86 中国大陆")
                else:
                    # 找区号选择按钮
                    code_btn = page.locator('[class*="code"]').first
                    if code_btn.count() > 0 and code_btn.is_visible():
                        write_status("点击区号选择...")
                        code_btn.click()
                        time.sleep(1)
                        save_screenshot(page, '03_country_select')
                        # 选择中国大陆
                        cn = page.get_by_text('中国大陆', exact=False)
                        if cn.count() > 0:
                            cn.first.click()
                            time.sleep(1)
            except Exception as e:
                write_status(f"国家选择处理: {e}")
                
        except Exception as e:
            write_status(f"国家选择检查出错: {e}")
        
        save_screenshot(page, '04_before_phone')
        
        write_status(f"正在输入手机号: {phone}...")
        
        # 输入手机号
        phone_input = None
        phone_selectors = [
            'input[name="fm-login-id"]',
            'input[placeholder*="手机号"]',
            'input[type="tel"]',
            '#fm-login-id',
            '#J_Mobile',
            'input[maxlength="11"]',
        ]
        
        for sel in phone_selectors:
            try:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible():
                    phone_input = el.first
                    write_status(f"找到手机号输入框: {sel}")
                    break
            except:
                continue
        
        if not phone_input:
            # 找所有可见的 input
            try:
                inputs = page.locator('input:visible')
                for i in range(min(5, inputs.count())):
                    inp = inputs.nth(i)
                    placeholder = inp.get_attribute('placeholder') or ''
                    typ = inp.get_attribute('type') or ''
                    if '手机' in placeholder or typ == 'tel':
                        phone_input = inp
                        write_status(f"通过placeholder找到手机号输入框: {placeholder}")
                        break
            except:
                pass
        
        if phone_input:
            phone_input.click()
            time.sleep(0.5)
            phone_input.fill('')
            time.sleep(0.3)
            phone_input.type(phone, delay=100)
            time.sleep(2)
            save_screenshot(page, '05_after_phone')
            write_status("手机号已输入")
        else:
            write_status("❌ 未找到手机号输入框")
            save_screenshot(page, 'error_no_phone_input')
            time.sleep(60)
            browser.close()
            return
        
        # 点击获取验证码
        write_status("正在点击获取验证码...")
        
        code_btn = None
        code_btn_selectors = [
            'text=获取验证码',
            'text=发送验证码',
            'text=免费获取',
            'button:has-text("获取验证码")',
            '#J_GetCode',
            '.get-code-btn',
            '.J_GetCode',
            '[class*="getcode"]',
            '[class*="get-code"]',
        ]
        
        for sel in code_btn_selectors:
            try:
                btn = page.locator(sel)
                if btn.count() > 0 and btn.first.is_visible():
                    text = btn.first.inner_text() or ''
                    if '验证码' in text or '获取' in text or '发送' in text:
                        code_btn = btn.first
                        write_status(f"找到获取验证码按钮: {sel}, 文本: {text}")
                        break
            except:
                continue
        
        if code_btn:
            try:
                code_btn.click()
                time.sleep(2)
                save_screenshot(page, '06_after_click_code')
                write_status("✅ 已点击获取验证码按钮，请查收短信")
            except Exception as e:
                write_status(f"点击获取验证码失败: {e}")
                save_screenshot(page, 'error_click_code')
        else:
            write_status("⚠️  未找到获取验证码按钮，请在浏览器中手动点击")
            save_screenshot(page, 'error_no_code_btn')
        
        # 等待滑块验证（如果有的话）
        try:
            slider = page.locator('[class*="slider"], [class*="nc_"]')
            if slider.count() > 0 and slider.first.is_visible():
                write_status("⚠️  检测到滑块验证，请在浏览器中手动完成")
                # 等待用户手动完成滑块
                for i in range(60):
                    time.sleep(2)
                    if not slider.first.is_visible():
                        write_status("✅ 滑块验证已完成")
                        break
        except:
            pass
        
        write_status("等待用户提供验证码...（请把验证码发给我）")
        
        # 等待验证码
        max_wait = 600  # 最多等10分钟
        for i in range(max_wait):
            time.sleep(1)
            
            code = read_code()
            if code and len(code) >= 4:
                write_status(f"收到验证码: {code}，正在输入...")
                
                save_screenshot(page, '07_before_code_input')
                
                # 输入验证码
                code_input = None
                code_input_selectors = [
                    'input[name="fm-login-checkcode"]',
                    'input[name="checkcode"]',
                    'input[placeholder*="验证码"]',
                    '#fm-login-checkcode',
                    '#J_CheckCode',
                    'input[type="text"]:visible',
                ]
                
                for sel in code_input_selectors:
                    try:
                        el = page.locator(sel)
                        if el.count() > 0 and el.first.is_visible():
                            placeholder = el.first.get_attribute('placeholder') or ''
                            name = el.first.get_attribute('name') or ''
                            if '验证码' in placeholder or 'checkcode' in name.lower() or 'code' in name.lower():
                                code_input = el.first
                                write_status(f"找到验证码输入框: {sel}")
                                break
                    except:
                        continue
                
                if not code_input:
                    # 找第二个文本输入框
                    try:
                        text_inputs = page.locator('input[type="text"]:visible')
                        if text_inputs.count() >= 2:
                            code_input = text_inputs.nth(1)
                        else:
                            # 找所有输入框中的第二个可见的
                            all_inputs = page.locator('input:visible')
                            for j in range(min(5, all_inputs.count())):
                                inp = all_inputs.nth(j)
                                typ = inp.get_attribute('type') or 'text'
                                if typ in ['text', 'tel', ''] and j > 0:
                                    code_input = inp
                                    break
                    except:
                        pass
                
                if code_input:
                    code_input.click()
                    time.sleep(0.5)
                    code_input.fill('')
                    time.sleep(0.3)
                    code_input.type(code, delay=100)
                    time.sleep(2)
                    save_screenshot(page, '08_after_code_input')
                    write_status("验证码已输入")
                else:
                    write_status("❌ 未找到验证码输入框")
                    save_screenshot(page, 'error_no_code_input')
                
                # 点击登录按钮
                write_status("正在点击登录按钮...")
                
                login_btn = None
                login_btn_selectors = [
                    'button:has-text("登录")',
                    'text=登 录',
                    '#J_SubmitStatic',
                    '.fm-button',
                    'button[type="submit"]',
                    '[class*="submit"]',
                    '[class*="login-btn"]',
                ]
                
                for sel in login_btn_selectors:
                    try:
                        btn = page.locator(sel)
                        if btn.count() > 0 and btn.first.is_visible():
                            text = btn.first.inner_text() or ''
                            if '登录' in text and '注册' not in text:
                                login_btn = btn.first
                                write_status(f"找到登录按钮: {sel}, 文本: {text}")
                                break
                    except:
                        continue
                
                if login_btn:
                    try:
                        login_btn.click()
                        save_screenshot(page, '09_after_login_click')
                        write_status("已点击登录按钮，等待登录结果...")
                    except Exception as e:
                        write_status(f"点击登录失败: {e}")
                else:
                    write_status("⚠️  未找到登录按钮，请手动点击")
                
                # 等待登录结果
                for j in range(60):
                    time.sleep(2)
                    try:
                        current_url = page.url
                        title = page.title()
                        
                        if j % 5 == 0:
                            write_status(f"等待登录结果... ({j*2}s) URL: {current_url[:60]}")
                        
                        # 检查是否登录成功
                        if 'login' not in current_url and ('taobao.com' in current_url or 'tmall.com' in current_url):
                            if 'login' not in title and '登录' not in title:
                                write_status("🎉 登录成功！正在验证...")
                                time.sleep(3)
                                save_screenshot(page, '10_login_success')
                                
                                # 访问拍卖详情页验证
                                try:
                                    page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
                                    time.sleep(5)
                                    content = page.content()
                                    content_len = len(content)
                                    detail_title = page.title()
                                    save_screenshot(page, '11_detail_page')
                                    
                                    write_status(f"详情页标题: {detail_title}")
                                    write_status(f"详情页内容长度: {content_len}")
                                    
                                    if content_len > 10000 and '登录' not in detail_title:
                                        write_status("✅ 详情页访问正常，正在保存登录状态...")
                                        context.storage_state(path=storage_path)
                                        write_status(f"✅ 登录状态已保存到: {storage_path}")
                                        write_status("登录完成！浏览器将在30秒后关闭")
                                        time.sleep(30)
                                        browser.close()
                                        return
                                except Exception as e:
                                    write_status(f"验证详情页出错: {e}")
                                
                                # 即使验证失败也保存
                                context.storage_state(path=storage_path)
                                write_status(f"✅ 登录状态已保存到: {storage_path}")
                                write_status("登录完成！浏览器将在30秒后关闭")
                                time.sleep(30)
                                browser.close()
                                return
                    except:
                        pass
                
                write_status("⚠️  登录可能失败，请检查")
                save_screenshot(page, 'error_login_failed')
                time.sleep(60)
                browser.close()
                return
            
            if i % 10 == 0:
                write_status(f"等待验证码中... ({i}s)")
        
        write_status("⏰ 等待超时")
        time.sleep(10)
        browser.close()


if __name__ == '__main__':
    main()
