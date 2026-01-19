import asyncio
import sqlite3
import time
from playwright.async_api import async_playwright
from utils.base_social_media import set_init_script
from pathlib import Path
from conf import BASE_DIR, LOCAL_CHROME_PATH
from newFileUpload.platform_configs import get_platform_key_by_type, PLATFORM_CONFIGS



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
                print(f"当前URL: {current_url}")
                cookies = await context.cookies()

                # 简单判断：如果URL不再是登录页，或者cookie中包含认证信息，认为登录成功
                if "login" not in current_url.lower() or any(cookie.get("name") in ["session", "token", "cookie", "auth"] for cookie in cookies):
                    break

                await asyncio.sleep(5)  # 每5秒检查一次

            # 保存cookie
            await context.storage_state(path=str(cookie_file_path))
            status_queue.put(f'{{"code": 200, "msg": "Cookie已保存", "data": null}}')
            print(f"✅ 成功保存cookies文件: {cookie_file_path}")

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