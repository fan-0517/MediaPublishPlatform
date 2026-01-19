import asyncio
import sqlite3
from playwright.async_api import async_playwright
from utils.base_social_media import set_init_script
from pathlib import Path
from conf import BASE_DIR


# 统一登录异步处理函数
def run_unified_login(type, id, status_queue):
    """
    统一登录异步处理函数
    参数：
        type: 平台类型编号
        id: 账号名
        status_queue: 状态队列，用于返回登录状态
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(unified_login_cookie_gen(type, id, status_queue))
        loop.close()
    except Exception as e:
        print(f"统一登录失败: {str(e)}")
        status_queue.put(f'{{"code": 500, "msg": "登录失败: {str(e)}", "data": null}}')

# 统一登录cookie生成函数
async def unified_login_cookie_gen(type, id, status_queue):
    """
    统一登录cookie生成函数
    参数：
        type: 平台类型编号
        id: 账号名
        status_queue: 状态队列，用于返回登录状态
    """
    try:
        # 获取平台key
        platform_key = get_platform_key_by_type(int(type))
        if not platform_key:
            status_queue.put(f'{{"code": 400, "msg": "不支持的平台类型", "data": null}}')
            return

        # 获取平台配置
        platform_config = PLATFORM_CONFIGS.get(platform_key)
        if not platform_config:
            status_queue.put(f'{{"code": 400, "msg": "平台配置不存在", "data": null}}')
            return

        # 生成cookie文件路径
        cookie_file = f"{platform_key}_cookie_{id}.json"
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / cookie_file)

        # 创建cookiesFile目录（如果不存在）
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 使用Playwright进行登录
        async with async_playwright() as playwright:
            options = {
                'args': [
                    f'--lang en-US',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--ignore-certificate-errors',
                    '--start-maximized',
                    '--disable-blink-features=AutomationControlled'
                ],
                'headless': False,  # 登录时需要可视化
                'executable_path': LOCAL_CHROME_PATH,
            }

            # 启动浏览器
            browser = await playwright.chromium.launch(**options)
            # 创建上下文
            context = await browser.new_context()
            context = await set_init_script(context)

            # 创建页面
            page = await context.new_page()
            await page.goto(platform_config["login_url"], wait_until='domcontentloaded', timeout=60000)

            # 等待用户登录完成
            status_queue.put(f'{{"code": 200, "msg": "请在浏览器中登录{platform_config["platform_name"]}账号", "data": null}}')

            # 等待登录完成（检测cookie是否包含登录信息或URL是否变化）
            login_wait_timeout = 300000  # 5分钟登录超时
            start_time = time.time()

            while time.time() - start_time < login_wait_timeout:
                # 检查是否已登录（通过检查URL是否包含登录后的特征或cookie是否包含登录信息）
                current_url = page.url
                cookies = await context.cookies()

                # 简单判断：如果URL不再是登录页，或者cookie中包含认证信息，认为登录成功
                if "login" not in current_url.lower() or any(cookie.get("name") in ["session", "token", "cookie", "auth"] for cookie in cookies):
                    break

                await asyncio.sleep(5)  # 每5秒检查一次

            # 保存cookie
            await context.storage_state(path=str(cookie_file_path))
            status_queue.put(f'{{"code": 200, "msg": "Cookie已保存", "data": null}}')

            # 关闭浏览器
            await context.close()
            await browser.close()

        # 将账号信息插入数据库
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_info (type, userName, filePath, status)
                VALUES (?, ?, ?, ?)
            ''', (type, id, cookie_file, 1))
            conn.commit()

        status_queue.put(f'{{"code": 200, "msg": "登录成功", "data": null}}')

    except Exception as e:
        print(f"统一登录失败: {str(e)}")
        status_queue.put(f'{{"code": 500, "msg": "登录失败: {str(e)}", "data": null}}')


# 删除账号
def delete_account(account_id):
    """
    删除账号
    :param account_id: 账号ID
    :return: 字典，包含删除结果
    """
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return {
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }

            record = dict(record)
            file_path = record['filePath']

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        # 删除对应的cookies文件
        cookies_file = Path(BASE_DIR / "cookiesFile" / file_path)
        if cookies_file.exists():
            cookies_file.unlink()
            print(f"✅ 成功删除cookies文件: {cookies_file}")

        return {
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }

    except Exception as e:
        return {
            "code": 500,
            "msg": "delete failed!",
            "data": None
        }

# # 抖音登录
# async def douyin_cookie_gen(id,status_queue):
#     url_changed_event = asyncio.Event()
#     async def on_url_change():
#         # 检查是否是主框架的变化
#         if page.url != original_url:
#             url_changed_event.set()
#     async with async_playwright() as playwright:
#         options = {
#             'headless': LOCAL_CHROME_HEADLESS
#         }
#         # Make sure to run headed.
#         browser = await playwright.chromium.launch(**options)
#         # Setup context however you like.
#         context = await browser.new_context()  # Pass any options
#         context = await set_init_script(context)
#         # Pause the page, and start recording manually.
#         page = await context.new_page()
#         await page.goto("https://creator.douyin.com/")
#         original_url = page.url
#         img_locator = page.get_by_role("img", name="二维码")
#         # 获取 src 属性值
#         src = await img_locator.get_attribute("src")
#         print("✅ 图片地址:", src)
#         status_queue.put(src)
#         # 监听页面的 'framenavigated' 事件，只关注主框架的变化
#         page.on('framenavigated',
#                 lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
#         try:
#             # 等待 URL 变化或超时
#             await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
#             print("监听页面跳转成功")
#         except asyncio.TimeoutError:
#             print("监听页面跳转超时")
#             await page.close()
#             await context.close()
#             await browser.close()
#             status_queue.put("500")
#             return None
#         uuid_v1 = uuid.uuid1()
#         print(f"UUID v1: {uuid_v1}")
#         # 确保cookiesFile目录存在
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
#         result = await check_cookie(3, f"{uuid_v1}.json")
#         if not result:
#             status_queue.put("500")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         await page.close()
#         await context.close()
#         await browser.close()
#         with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                                 INSERT INTO user_info (type, filePath, userName, status)
#                                 VALUES (?, ?, ?, ?)
#                                 ''', (3, f"{uuid_v1}.json", id, 1))
#             conn.commit()
#             print("✅ 用户状态已记录")
#         status_queue.put("200")
#
#
# # 视频号登录
# async def get_tencent_cookie(id,status_queue):
#     url_changed_event = asyncio.Event()
#     async def on_url_change():
#         # 检查是否是主框架的变化
#         if page.url != original_url:
#             url_changed_event.set()
#
#     async with async_playwright() as playwright:
#         options = {
#             'args': [
#                 '--lang en-GB'
#             ],
#             'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
#         }
#         # Make sure to run headed.
#         browser = await playwright.chromium.launch(**options)
#         # Setup context however you like.
#         context = await browser.new_context()  # Pass any options
#         # Pause the page, and start recording manually.
#         context = await set_init_script(context)
#         page = await context.new_page()
#         await page.goto("https://channels.weixin.qq.com")
#         original_url = page.url
#
#         # 监听页面的 'framenavigated' 事件，只关注主框架的变化
#         page.on('framenavigated',
#                 lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
#
#         # 等待 iframe 出现（最多等 60 秒）
#         iframe_locator = page.frame_locator("iframe").first
#
#         # 获取 iframe 中的第一个 img 元素
#         img_locator = iframe_locator.get_by_role("img").first
#
#         # 获取 src 属性值
#         src = await img_locator.get_attribute("src")
#         print("✅ 图片地址:", src)
#         status_queue.put(src)
#
#         try:
#             # 等待 URL 变化或超时
#             await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
#             print("监听页面跳转成功")
#         except asyncio.TimeoutError:
#             status_queue.put("500")
#             print("监听页面跳转超时")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         uuid_v1 = uuid.uuid1()
#         print(f"UUID v1: {uuid_v1}")
#         # 确保cookiesFile目录存在
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
#         result = await check_cookie(2,f"{uuid_v1}.json")
#         if not result:
#             status_queue.put("500")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         await page.close()
#         await context.close()
#         await browser.close()
#
#         with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                                 INSERT INTO user_info (type, filePath, userName, status)
#                                 VALUES (?, ?, ?, ?)
#                                 ''', (2, f"{uuid_v1}.json", id, 1))
#             conn.commit()
#             print("✅ 用户状态已记录")
#         status_queue.put("200")
#
# # 快手登录
# async def get_ks_cookie(id,status_queue):
#     url_changed_event = asyncio.Event()
#     async def on_url_change():
#         # 检查是否是主框架的变化
#         if page.url != original_url:
#             url_changed_event.set()
#     async with async_playwright() as playwright:
#         options = {
#             'args': [
#                 '--lang en-GB'
#             ],
#             'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
#         }
#         # Make sure to run headed.
#         browser = await playwright.chromium.launch(**options)
#         # Setup context however you like.
#         context = await browser.new_context()  # Pass any options
#         context = await set_init_script(context)
#         # Pause the page, and start recording manually.
#         page = await context.new_page()
#         await page.goto("https://cp.kuaishou.com")
#
#         # 定位并点击“立即登录”按钮（类型为 link）
#         await page.get_by_role("link", name="立即登录").click()
#         await page.get_by_text("扫码登录").click()
#         img_locator = page.get_by_role("img", name="qrcode")
#         # 获取 src 属性值
#         src = await img_locator.get_attribute("src")
#         original_url = page.url
#         print("✅ 图片地址:", src)
#         status_queue.put(src)
#         # 监听页面的 'framenavigated' 事件，只关注主框架的变化
#         page.on('framenavigated',
#                 lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
#
#         try:
#             # 等待 URL 变化或超时
#             await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
#             print("监听页面跳转成功")
#         except asyncio.TimeoutError:
#             status_queue.put("500")
#             print("监听页面跳转超时")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         uuid_v1 = uuid.uuid1()
#         print(f"UUID v1: {uuid_v1}")
#         # 确保cookiesFile目录存在
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
#         result = await check_cookie(4, f"{uuid_v1}.json")
#         if not result:
#             status_queue.put("500")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         await page.close()
#         await context.close()
#         await browser.close()
#
#         with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                                         INSERT INTO user_info (type, filePath, userName, status)
#                                         VALUES (?, ?, ?, ?)
#                                         ''', (4, f"{uuid_v1}.json", id, 1))
#             conn.commit()
#             print("✅ 用户状态已记录")
#         status_queue.put("200")
#
# # 小红书登录
# async def xiaohongshu_cookie_gen(id,status_queue):
#     url_changed_event = asyncio.Event()
#
#     async def on_url_change():
#         # 检查是否是主框架的变化
#         if page.url != original_url:
#             url_changed_event.set()
#
#     async with async_playwright() as playwright:
#         options = {
#             'args': [
#                 '--lang en-GB'
#             ],
#             'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
#         }
#         # Make sure to run headed.
#         browser = await playwright.chromium.launch(**options)
#         # Setup context however you like.
#         context = await browser.new_context()  # Pass any options
#         context = await set_init_script(context)
#         # Pause the page, and start recording manually.
#         page = await context.new_page()
#         await page.goto("https://creator.xiaohongshu.com/")
#         await page.locator('img.css-wemwzq').click()
#
#         img_locator = page.get_by_role("img").nth(2)
#         # 获取 src 属性值
#         src = await img_locator.get_attribute("src")
#         original_url = page.url
#         print("✅ 图片地址:", src)
#         status_queue.put(src)
#         # 监听页面的 'framenavigated' 事件，只关注主框架的变化
#         page.on('framenavigated',
#                 lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
#
#         try:
#             # 等待 URL 变化或超时
#             await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
#             print("监听页面跳转成功")
#         except asyncio.TimeoutError:
#             status_queue.put("500")
#             print("监听页面跳转超时")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         uuid_v1 = uuid.uuid1()
#         print(f"UUID v1: {uuid_v1}")
#         # 确保cookiesFile目录存在
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
#         result = await check_cookie(1, f"{uuid_v1}.json")
#         if not result:
#             status_queue.put("500")
#             await page.close()
#             await context.close()
#             await browser.close()
#             return None
#         await page.close()
#         await context.close()
#         await browser.close()
#
#         with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                            INSERT INTO user_info (type, filePath, userName, status)
#                            VALUES (?, ?, ?, ?)
#                            ''', (1, f"{uuid_v1}.json", id, 1))
#             conn.commit()
#             print("✅ 用户状态已记录")
#         status_queue.put("200")
#
# # 导入必要的模块
# from oldFileUpload.uploader.tk_uploader.main import cookie_auth
# from playwright.async_api import async_playwright
# import uuid
# from pathlib import Path
# import sqlite3
# import asyncio
# from conf import LOCAL_CHROME_HEADLESS
# from utils.log import tiktok_logger
# from utils.base_social_media import set_init_script
# from conf import BASE_DIR
#
# # TikTok登录
# async def get_tiktok_cookie(id, status_queue):
#     try:
#         # 生成UUID并准备cookie文件路径
#         uuid_v1 = uuid.uuid1()
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         account_file = cookies_dir / f"{uuid_v1}.json"
#
#         async with async_playwright() as playwright:
#             options = {
#                 'args': [
#                     '--lang en-GB',
#                 ],
#                 'headless': LOCAL_CHROME_HEADLESS,  # 设置为非无头模式以允许用户登录
#             }
#             # 使用firefox浏览器，与main.py保持一致
#             browser = await playwright.firefox.launch(**options)
#             context = await browser.new_context()
#             context = await set_init_script(context)
#             page = await context.new_page()
#
#             # 访问TikTok登录页面
#             await page.goto("https://www.tiktok.com/login?lang=en")
#
#             # 暂停页面，让用户手动登录
#             # 这里使用较长的超时时间，让用户有足够时间完成登录
#             tiktok_logger.info("请在浏览器中完成TikTok登录...")
#             status_queue.put("请在浏览器中完成TikTok登录...")
#
#             # 等待用户完成登录，检查是否成功跳转到主页
#             try:
#                 # 等待URL变化，表明登录成功
#                 await page.wait_for_url("https://www.tiktok.com/foryou?lang=en", timeout=300000)  # 5分钟超时
#                 tiktok_logger.success("✅ TikTok 登录成功")
#             except Exception as e:
#                 tiktok_logger.error(f"[+] TikTok 登录超时或失败: {str(e)}")
#                 status_queue.put("500")
#                 return None
#
#             # 保存cookie
#             await context.storage_state(path=account_file)
#             tiktok_logger.success("✅ TikTok cookie 已保存")
#
#             # 验证cookie是否有效
#             # 使用main.py中的cookie_auth逻辑进行验证
#             result = await cookie_auth(account_file)
#             if not result:
#                 tiktok_logger.error("[+] TikTok cookie 验证失败")
#                 status_queue.put("500")
#                 return None
#
#             # 保存账号信息到数据库
#             with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute('''
#                                     INSERT INTO user_info (type, filePath, userName, status)
#                                     VALUES (?, ?, ?, ?)
#                                     ''', (5, f"{uuid_v1}.json", id, 1))
#                 conn.commit()
#                 tiktok_logger.success("✅ TikTok 用户状态已记录")
#
#             status_queue.put("200")
#
#     except Exception as e:
#         tiktok_logger.error(f"[+] TikTok 登录过程出错: {str(e)}")
#         status_queue.put("500")
#     finally:
#         # 确保资源被释放
#         if 'browser' in locals():
#             await browser.close()
#
# # Instagram登录
# async def get_instagram_cookie(id, status_queue):
#     try:
#         # 生成UUID并准备cookie文件路径
#         uuid_v1 = uuid.uuid1()
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         account_file = cookies_dir / f"{uuid_v1}.json"
#
#         async with async_playwright() as playwright:
#             options = {
#                 'args': [
#                     '--lang en-GB',
#                 ],
#                 'headless': LOCAL_CHROME_HEADLESS,  # 设置为非无头模式以允许用户登录
#             }
#             browser = await playwright.chromium.launch(**options)
#             context = await browser.new_context()
#             context = await set_init_script(context)
#             page = await context.new_page()
#
#             # 访问Instagram登录页面
#             await page.goto("https://www.instagram.com/accounts/login/")
#
#             # 提示用户登录
#             instagram_logger.info("请在浏览器中完成Instagram登录...")
#             status_queue.put("请在浏览器中完成Instagram登录...")
#
#             # 等待用户完成登录，检查是否成功跳转到主页
#             try:
#                 # 等待URL变化，表明登录成功
#                 await page.wait_for_url("https://www.instagram.com/", timeout=300000)  # 5分钟超时
#                 instagram_logger.success("✅ Instagram 登录成功")
#             except Exception as e:
#                 instagram_logger.error(f"[+] Instagram 登录超时或失败: {str(e)}")
#                 status_queue.put("500")
#                 return None
#
#             # 保存cookie
#             await context.storage_state(path=account_file)
#             instagram_logger.success("✅ Instagram cookie 已保存")
#
#             # 保存账号信息到数据库，Instagram平台ID设置为6
#             with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute('''
#                                     INSERT INTO user_info (type, filePath, userName, status)
#                                     VALUES (?, ?, ?, ?)
#                                     ''', (6, f"{uuid_v1}.json", id, 1))
#                 conn.commit()
#                 instagram_logger.success("✅ Instagram 用户状态已记录")
#
#             status_queue.put("200")
#
#     except Exception as e:
#         instagram_logger.error(f"[+] Instagram 登录过程出错: {str(e)}")
#         status_queue.put("500")
#     finally:
#         # 确保资源被释放
#         if 'browser' in locals():
#             await browser.close()
#
# # Facebook登录
# async def get_facebook_cookie(id, status_queue):
#     try:
#         # 生成UUID并准备cookie文件路径
#         uuid_v1 = uuid.uuid1()
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         account_file = cookies_dir / f"{uuid_v1}.json"
#
#         async with async_playwright() as playwright:
#             options = {
#                 'args': [
#                     '--lang en-GB',
#                 ],
#                 'headless': LOCAL_CHROME_HEADLESS,  # 设置为非无头模式以允许用户登录
#             }
#             browser = await playwright.chromium.launch(**options)
#             context = await browser.new_context()
#             context = await set_init_script(context)
#             page = await context.new_page()
#
#             # 访问Facebook登录页面
#             await page.goto("https://www.facebook.com/login")
#
#             # 提示用户登录
#             tiktok_logger.info("请在浏览器中完成Facebook登录...")
#             status_queue.put("请在浏览器中完成Facebook登录...")
#
#             # 等待用户完成登录，检查是否成功跳转到主页
#             try:
#                 # 等待URL变化，表明登录成功
#                 await page.wait_for_url("https://www.facebook.com/", timeout=300000)  # 5分钟超时
#                 tiktok_logger.success("✅ Facebook 登录成功")
#             except Exception as e:
#                 tiktok_logger.error(f"[+] Facebook 登录超时或失败: {str(e)}")
#                 status_queue.put("500")
#                 return None
#
#             # 保存cookie
#             await context.storage_state(path=account_file)
#             tiktok_logger.success("✅ Facebook cookie 已保存")
#
#             # 保存账号信息到数据库，Facebook平台ID设置为7
#             with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute('''
#                                     INSERT INTO user_info (type, filePath, userName, status)
#                                     VALUES (?, ?, ?, ?)
#                                     ''', (7, f"{uuid_v1}.json", id, 1))
#                 conn.commit()
#                 tiktok_logger.success("✅ Facebook 用户状态已记录")
#
#             status_queue.put("200")
#
#     except Exception as e:
#         tiktok_logger.error(f"[+] Facebook 登录过程出错: {str(e)}")
#         status_queue.put("500")
#     finally:
#         # 确保资源被释放
#         if 'browser' in locals():
#             await browser.close()
#
# # Bilibili登录
# async def get_bilibili_cookie(id, status_queue):
#     try:
#         # 生成UUID并准备cookie文件路径
#         uuid_v1 = uuid.uuid1()
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         account_file = cookies_dir / f"{uuid_v1}.json"
#
#         async with async_playwright() as playwright:
#             options = {
#                 'args': [
#                     '--lang zh-CN',
#                 ],
#                 'headless': LOCAL_CHROME_HEADLESS,  # 设置为非无头模式以允许用户登录
#             }
#             browser = await playwright.chromium.launch(**options)
#             context = await browser.new_context()
#             context = await set_init_script(context)
#             page = await context.new_page()
#
#             # 访问Bilibili登录页面
#             await page.goto("https://passport.bilibili.com/login")
#
#             # 提示用户登录
#             tiktok_logger.info("请在浏览器中完成Bilibili登录...")
#             status_queue.put("请在浏览器中完成Bilibili登录...")
#
#             # 等待用户完成登录，检查是否成功跳转到主页
#             try:
#                 # 等待URL变化，表明登录成功
#                 await page.wait_for_url("https://www.bilibili.com/", timeout=300000)  # 5分钟超时
#                 tiktok_logger.success("✅ Bilibili 登录成功")
#             except Exception as e:
#                 tiktok_logger.error(f"[+] Bilibili 登录超时或失败: {str(e)}")
#                 status_queue.put("500")
#                 return None
#
#             # 保存cookie
#             await context.storage_state(path=account_file)
#             tiktok_logger.success("✅ Bilibili cookie 已保存")
#
#             # 保存账号信息到数据库，Bilibili平台ID设置为8
#             with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute('''
#                                     INSERT INTO user_info (type, filePath, userName, status)
#                                     VALUES (?, ?, ?, ?)
#                                     ''', (8, f"{uuid_v1}.json", id, 1))
#                 conn.commit()
#                 tiktok_logger.success("✅ Bilibili 用户状态已记录")
#
#             status_queue.put("200")
#
#     except Exception as e:
#         tiktok_logger.error(f"[+] Bilibili 登录过程出错: {str(e)}")
#         status_queue.put("500")
#     finally:
#         # 确保资源被释放
#         if 'browser' in locals():
#             await browser.close()
#
# # Baijiahao登录
# async def get_baijiahao_cookie(id, status_queue):
#     try:
#         # 生成UUID并准备cookie文件路径
#         uuid_v1 = uuid.uuid1()
#         cookies_dir = Path(BASE_DIR / "cookiesFile")
#         cookies_dir.mkdir(exist_ok=True)
#         account_file = cookies_dir / f"{uuid_v1}.json"
#
#         async with async_playwright() as playwright:
#             options = {
#                 'args': [
#                     '--lang zh-CN',
#                 ],
#                 'headless': LOCAL_CHROME_HEADLESS,  # 设置为非无头模式以允许用户登录
#             }
#             browser = await playwright.chromium.launch(**options)
#             context = await browser.new_context()
#             context = await set_init_script(context)
#             page = await context.new_page()
#
#             # 访问Baijiahao登录页面
#             await page.goto("https://baijiahao.baidu.com/builder/rc/login")
#
#             # 提示用户登录
#             tiktok_logger.info("请在浏览器中完成Baijiahao登录...")
#             status_queue.put("请在浏览器中完成Baijiahao登录...")
#
#             # 等待用户完成登录，检查是否成功跳转到主页
#             try:
#                 # 等待URL变化，表明登录成功
#                 await page.wait_for_url("https://baijiahao.baidu.com/builder/rc/home", timeout=300000)  # 5分钟超时
#                 tiktok_logger.success("✅ Baijiahao 登录成功")
#             except Exception as e:
#                 tiktok_logger.error(f"[+] Baijiahao 登录超时或失败: {str(e)}")
#                 status_queue.put("500")
#                 return None
#
#             # 保存cookie
#             await context.storage_state(path=account_file)
#             tiktok_logger.success("✅ Baijiahao cookie 已保存")
#
#             # 保存账号信息到数据库，Baijiahao平台ID设置为9
#             with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute('''
#                                     INSERT INTO user_info (type, filePath, userName, status)
#                                     VALUES (?, ?, ?, ?)
#                                     ''', (9, f"{uuid_v1}.json", id, 1))
#                 conn.commit()
#                 tiktok_logger.success("✅ Baijiahao 用户状态已记录")
#
#             status_queue.put("200")
#
#     except Exception as e:
#         tiktok_logger.error(f"[+] Baijiahao 登录过程出错: {str(e)}")
#         status_queue.put("500")
#     finally:
#         # 确保资源被释放
#         if 'browser' in locals():
#             await browser.close()
#
# # a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# # print(a)