"""
严格登录验证脚本 - 确保真正登录成功后才保存状态
关键：必须检测到unb cookie（用户唯一标识）才算真正登录成功
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
    print(f"[状态] {msg}", flush=True)


def is_truly_logged_in(context):
    """检查是否真正登录成功 - 必须有unb cookie"""
    cookies = context.cookies()
    cookie_names = [c['name'] for c in cookies]

    has_unb = 'unb' in cookie_names
    has_uc1 = 'uc1' in cookie_names
    has_login5 = 'login5' in cookie_names

    return has_unb and has_uc1


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

        write_status("正在打开淘宝登录页面...")

        try:
            page.goto('https://login.taobao.com/', timeout=60000)
            time.sleep(3)
        except Exception as e:
            write_status(f"打开页面出错: {e}")
            return

        write_status("📱 请在浏览器中完成完整登录流程")
        write_status("⚠️  重要：如果出现身份验证页面，请完成验证")
        write_status("⏳ 只有真正登录成功（跳转到淘宝首页）才会保存状态")

        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        os.makedirs(screenshot_dir, exist_ok=True)
        page.screenshot(path=os.path.join(screenshot_dir, 'login_page.png'), full_page=True)

        max_wait = 900  # 最多等15分钟
        login_confirmed = False

        for i in range(max_wait):
            time.sleep(2)

            try:
                current_url = page.url
                title = page.title()

                if i % 15 == 0:
                    write_status(f"等待登录中... ({i*2}s) URL: {current_url[:70]}")

                # 检查1：URL跳转到淘宝首页
                if 'www.taobao.com' in current_url and 'login' not in current_url:
                    write_status("🎉 跳转到淘宝首页！")
                    login_confirmed = True
                    break

                # 检查2：URL不是登录页且不是身份验证页
                if ('login' not in current_url and
                    'normal_validate' not in current_url and
                    'iv/' not in current_url and
                    'taobao.com' in current_url):

                    if '登录' not in title and 'login' not in title.lower() and '身份验证' not in title:
                        write_status(f"🎉 检测到可能登录成功！")
                        write_status(f"URL: {current_url[:80]}")
                        write_status(f"标题: {title}")

                        # 进一步检查cookie
                        if is_truly_logged_in(context):
                            write_status("✅ 检测到unb cookie，确认登录成功！")
                            login_confirmed = True
                            break
                        else:
                            write_status("⚠️  Cookie不完整，继续等待...")

                # 检查3：身份验证页面
                if 'normal_validate' in current_url or 'iv/' in current_url:
                    if i % 10 == 0:
                        write_status(f"⏳ 检测到身份验证页面，请完成验证 ({i*2}s)")

            except Exception as e:
                if i % 30 == 0:
                    write_status(f"等待中... ({i*2}s)")

        if not login_confirmed:
            # 最后再检查一次cookie
            write_status("🔍 最终检查cookie状态...")
            if is_truly_logged_in(context):
                write_status("✅ 检测到unb cookie，确认登录成功！")
                login_confirmed = True
            else:
                cookies = context.cookies()
                cookie_names = [c['name'] for c in cookies]
                write_status(f"❌ 未检测到unb cookie，登录可能未完全成功")
                write_status(f"当前cookies: {', '.join(sorted(cookie_names)[:20])}")
                write_status(f"URL: {page.url[:80]}")
                write_status(f"标题: {page.title()}")

        if login_confirmed:
            time.sleep(3)

            page.screenshot(path=os.path.join(screenshot_dir, 'login_success.png'), full_page=True)

            write_status("🔍 正在访问拍卖详情页验证登录状态...")
            try:
                page.goto('https://sf-item.taobao.com/sf_item/1057642038615.htm', timeout=30000)
                page.wait_for_load_state('domcontentloaded', timeout=15000)
                time.sleep(5)

                content = page.content()
                content_len = len(content)
                detail_title = page.title()

                page.screenshot(path=os.path.join(screenshot_dir, 'detail_verify.png'), full_page=True)

                write_status(f"详情页标题: {detail_title}")
                write_status(f"详情页内容长度: {content_len}")
                write_status(f"详情页URL: {page.url[:80]}")

                has_area = '建筑面积' in content or '面积' in content
                has_price = '起拍价' in content or '评估价' in content

                if content_len > 10000 and '登录' not in detail_title and 'login' not in page.url:
                    write_status("✅ 详情页访问正常！")
                    write_status(f"包含建筑面积: {has_area}")
                    write_status(f"包含价格信息: {has_price}")

                    context.storage_state(path=storage_path)
                    write_status(f"✅ 登录状态已保存到: {storage_path}")
                    write_status("🎉 登录完成！现在可以自动获取详情页数据")
                    write_status("浏览器将在30秒后自动关闭")
                    time.sleep(30)
                    browser.close()
                    return
                else:
                    write_status("⚠️  详情页访问可能受限")
                    write_status(f"URL: {page.url[:80]}")
            except Exception as e:
                write_status(f"验证详情页出错: {e}")

            # 即使详情页验证失败，如果有unb cookie也保存
            if is_truly_logged_in(context):
                context.storage_state(path=storage_path)
                write_status(f"✅ 检测到unb cookie，已保存登录状态")
                write_status("浏览器将在30秒后自动关闭")
                time.sleep(30)
        else:
            write_status("⏰ 等待超时或登录未完全成功")
            write_status("请重新运行脚本并完成完整登录流程")
            time.sleep(15)

        browser.close()


if __name__ == '__main__':
    main()
