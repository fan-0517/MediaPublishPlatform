import asyncio
import configparser
import os

from playwright.async_api import async_playwright
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import create_logger
from pathlib import Path
import sys
import os

async def check_cookie_generic(type, file_path):
    """
    通用的Cookie有效性验证方法
    Args:
        type: 平台类型 (1:小红书, 2:腾讯视频号, 3:抖音, 4:快手, 5:TikTok, 6:Instagram, 7:Facebook, 8:Bilibili, 9:Baijiahao)
        file_path: Cookie文件路径
    Returns:
        bool: Cookie是否有效
    """
    # 添加项目根目录到Python路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    # 从正确的路径导入platform_configs
    from newFileUpload.platform_configs import PLATFORM_CONFIGS

    # 根据类型获取平台配置
    platform_config = None
    for config in PLATFORM_CONFIGS.values():
        if config.get("type") == type:
            platform_config = config
            break

    if not platform_config:
        return False

    platform_name = platform_config.get("platform_name", "unknown")
    personal_url = platform_config.get("personal_url", "")
    logger = create_logger (platform_name, f'logs/{platform_name}.log')
    logger.info(f"开始检测平台 {platform_name} 的账号有效性")
    if not personal_url:
        logger.error(f"平台 {platform_name} 未配置 personal_url")
        return False

    # 使用Playwright检测账号有效性
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context(storage_state=Path(BASE_DIR / "cookiesFile" / file_path))
            context = await set_init_script(context)

            # 创建一个新的页面
            page = await context.new_page()

            # 访问个人中心页面
            await page.goto(personal_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(2)

            # 检查是否跳转到登录页面
            current_url = page.url
            logger.info(f"[+]Current URL: {current_url}")

            # 1.检查url是否包含登录相关的关键词
            login_keywords = ["login", "signin", "auth", "登录", "登录页", "登录页面"]
            is_login_page = any(keyword in current_url.lower() for keyword in login_keywords)

            if is_login_page:
                logger.error(f"[{platform_name}] 账号未登录，URL跳转到了登录页面")
                await context.close()
                await browser.close()
                return False

            # 根据不同平台的特征元素进行检查
            # 2.检查页面内容是否包含登录相关的文本（douyin和tiktok特征，就算没登录也可以到个人中心url）
            if platform_name in ["douyin", "tiktok"]:
                try:
                    content = await page.content()
                    # 检查是否包含登录按钮或登录提示
                    login_texts = ["登录", "Sign in", "Log in", "登录/注册", "扫码登录"]
                    for text in login_texts:
                        if text in content:
                            logger.error(f"[{platform_name}] 页面包含登录文本: {text}")
                            await context.close()
                            await browser.close()
                            return False
                except Exception as e:
                    logger.warning(f"[{platform_name}] 读取页面内容失败: {str(e)}")

            # 检查是否成功加载个人中心页面的特征元素

            # 暂时使用通用的检查方法
            logger.success(f"[{platform_name}] 账号有效")
            await context.close()
            await browser.close()
            return True
    except Exception as e:
        logger.error(f"[{platform_name}] 检测账号有效性时出错: {str(e)}")
        return False

async def check_cookie(type, file_path):
    """
    根据平台类型验证Cookie有效性
    Args:
        type: 平台类型 (1:小红书, 2:腾讯视频号, 3:抖音, 4:快手, 5:TikTok, 6:Instagram, 7:Facebook, 8:Bilibili, 9:Baijiahao)
        file_path: Cookie文件路径
    Returns:
        bool: Cookie是否有效
    """
    # 使用通用检测方法
    return await check_cookie_generic(type, file_path)


# async def cookie_auth_douyin(account_file):
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问指定的 URL
#         await page.goto("https://creator.douyin.com/creator-micro/content/upload")
#         try:
#             await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
#             # 2024.06.17 抖音创作者中心改版
#             # 判断
#             # 等待“扫码登录”元素出现，超时 5 秒（如果 5 秒没出现，说明 cookie 有效）
#             try:
#                 await page.get_by_text("扫码登录").wait_for(timeout=5000)
#                 douyin_logger.error("[douyin] cookie 失效，需要扫码登录")
#                 return False
#             except:
#                 douyin_logger.success("[douyin]  cookie 有效")
#                 return True
#         except:
#             douyin_logger.error("[douyin] 等待5秒 cookie 失效")
#             await context.close()
#             await browser.close()
#             return False
#
#
# async def cookie_auth_tencent(account_file):
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问指定的 URL
#         await page.goto("https://channels.weixin.qq.com/platform/post/create")
#         try:
#             await page.wait_for_url("https://channels.weixin.qq.com/platform/post/create", timeout=5000)
#             try:
#                 await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
#                 tencent_logger.error("[tencent] 等待5秒 cookie 失效")
#                 return False
#             except:
#                 tencent_logger.success("[tencent] cookie 有效")
#                 return True
#         except:
#             tencent_logger.error("[tencent] 等待5秒 cookie 失效")
#             await context.close()
#             await browser.close()
#             return False
#
# async def cookie_auth_ks(account_file):
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问指定的 URL
#         await page.goto("https://cp.kuaishou.com/article/publish/video")
#         try:
#             await page.wait_for_url("https://cp.kuaishou.com/article/publish/video", timeout=5000)
#             try:
#                 await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒
#                 kuaishou_logger.info("[ks] 等待5秒 cookie 失效")
#                 return False
#             except:
#                 kuaishou_logger.success("[ks] cookie 有效")
#                 return True
#         except:
#             kuaishou_logger.error("[ks] 等待5秒 cookie 失效")
#             await context.close()
#             await browser.close()
#             return False
#
#
# async def cookie_auth_xhs(account_file):
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问指定的 URL
#         await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
#         try:
#             await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
#             # 2024.06.17 抖音创作者中心改版
#             if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
#                 xiaohongshu_logger.error("[xhs] 等待5秒 cookie 失效")
#                 return False
#             else:
#                 xiaohongshu_logger.success("[xhs] cookie 有效")
#                 return True
#         except:
#             xiaohongshu_logger.error("[xhs] 等待5秒 cookie 失效")
#             await context.close()
#             await browser.close()
#             return False
#
#
#
# async def cookie_auth_tiktok(account_file):
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问TikTok创作者中心上传页面
#         await page.goto("https://www.tiktok.com/creator-center/upload")
#         try:
#             # 等待页面加载完成
#             await page.wait_for_url("https://www.tiktok.com/creator-center/upload", timeout=60000)
#             # 检查是否需要登录
#             try:
#                 await page.get_by_text("Log in", timeout=30000)
#                 tiktok_logger.error("[tiktok] TikTok cookie 失效，需要登录")
#                 return False
#             except:
#                 tiktok_logger.success("[tiktok] cookie 有效")
#                 return True
#         except:
#             tiktok_logger.error("[tiktok] 等待 TikTok 页面超时，cookie 可能失效")
#             await context.close()
#             await browser.close()
#             return False
#
#
# async def cookie_auth_instagram(account_file):
#     """
#     验证Instagram账号Cookie是否有效
#
#     Args:
#         account_file: Cookie文件路径
#
#     Returns:
#         bool: Cookie是否有效
#     """
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问Instagram创作者中心上传页面
#         await page.goto("https://www.instagram.com/create/upload/")
#         try:
#             # 等待页面加载完成
#             await page.wait_for_url("https://www.instagram.com/create/upload/", timeout=30000)
#             # 检查是否需要登录
#             try:
#                 await page.get_by_text("Log in", timeout=15000)
#                 instagram_logger.error("[instagram] cookie 失效，需要登录")
#                 return False
#             except:
#                 instagram_logger.success("[instagram] cookie 有效")
#                 return True
#         except:
#             instagram_logger.error("[instagram] 等待页面超时，cookie 可能失效")
#             await context.close()
#             await browser.close()
#             return False
#
# async def cookie_auth_facebook(account_file):
#     """
#     验证Facebook账号Cookie是否有效
#
#     Args:
#         account_file: Cookie文件路径
#
#     Returns:
#         bool: Cookie是否有效
#     """
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问Facebook主页
#         await page.goto("https://www.facebook.com/")
#         try:
#             # 等待页面加载完成
#             await page.wait_for_url("https://www.facebook.com/", timeout=30000)
#             # 检查是否需要登录
#             try:
#                 await page.get_by_text("Log in", timeout=15000)
#                 tiktok_logger.error("[facebook] cookie 失效，需要登录")
#                 return False
#             except:
#                 tiktok_logger.success("[facebook] cookie 有效")
#                 return True
#         except:
#             tiktok_logger.error("[facebook] 等待页面超时，cookie 可能失效")
#             await context.close()
#             await browser.close()
#             return False
#
# async def cookie_auth_bilibili(account_file):
#     """
#     验证Bilibili账号Cookie是否有效
#
#     Args:
#         account_file: Cookie文件路径
#
#     Returns:
#         bool: Cookie是否有效
#     """
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问Bilibili创作中心
#         await page.goto("https://member.bilibili.com/platform/home")
#         try:
#             # 等待页面加载完成
#             await page.wait_for_url("https://member.bilibili.com/platform/home", timeout=30000)
#             # 检查是否需要登录
#             try:
#                 await page.get_by_text("登录", timeout=15000)
#                 tiktok_logger.error("[bilibili] cookie 失效，需要登录")
#                 return False
#             except:
#                 tiktok_logger.success("[bilibili] cookie 有效")
#                 return True
#         except:
#             tiktok_logger.error("[bilibili] 等待页面超时，cookie 可能失效")
#             await context.close()
#             await browser.close()
#             return False
#
# async def cookie_auth_baijiahao(account_file):
#     """
#     验证Baijiahao账号Cookie是否有效
#
#     Args:
#         account_file: Cookie文件路径
#
#     Returns:
#         bool: Cookie是否有效
#     """
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(headless=True)
#         context = await browser.new_context(storage_state=account_file)
#         context = await set_init_script(context)
#         # 创建一个新的页面
#         page = await context.new_page()
#         # 访问Baijiahao创作中心
#         await page.goto("https://baijiahao.baidu.com/builder/rc/home")
#         try:
#             # 等待页面加载完成
#             await page.wait_for_url("https://baijiahao.baidu.com/builder/rc/home", timeout=30000)
#             # 检查是否需要登录
#             try:
#                 await page.get_by_text("登录", timeout=15000)
#                 tiktok_logger.error("[baijiahao] cookie 失效，需要登录")
#                 return False
#             except:
#                 tiktok_logger.success("[baijiahao] cookie 有效")
#                 return True
#         except:
#             tiktok_logger.error("[baijiahao] 等待页面超时，cookie 可能失效")
#             await context.close()
#             await browser.close()
#             return False