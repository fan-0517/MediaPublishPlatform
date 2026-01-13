import asyncio
import configparser
import os

from playwright.async_api import async_playwright
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import tencent_logger, kuaishou_logger, douyin_logger, xiaohongshu_logger, tiktok_logger, instagram_logger
from pathlib import Path


async def cookie_auth_douyin(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
            # 2024.06.17 抖音创作者中心改版
            # 判断
            # 等待“扫码登录”元素出现，超时 5 秒（如果 5 秒没出现，说明 cookie 有效）
            try:
                await page.get_by_text("扫码登录").wait_for(timeout=5000)
                douyin_logger.error("[douyin] cookie 失效，需要扫码登录")
                return False
            except:
                douyin_logger.success("[douyin]  cookie 有效")
                return True
        except:
            douyin_logger.error("[douyin] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False


async def cookie_auth_tencent(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[tencent] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[tencent] cookie 有效")
            return True


async def cookie_auth_ks(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒

            kuaishou_logger.info("[ks] 等待5秒 cookie 失效")
            return False
        except:
            kuaishou_logger.success("[ks] cookie 有效")
            return True


async def cookie_auth_xhs(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            xiaohongshu_logger.error("[xhs] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            xiaohongshu_logger.error("[xhs] 等待5秒 cookie 失效")
            return False
        else:
            xiaohongshu_logger.success("[xhs] cookie 有效")
            return True


async def cookie_auth_tiktok(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问TikTok创作者中心上传页面
        await page.goto("https://www.tiktok.com/creator-center/upload")
        try:
            # 等待页面加载完成
            await page.wait_for_url("https://www.tiktok.com/creator-center/upload", timeout=60000)
            # 检查是否需要登录
            try:
                await page.get_by_text("Log in", timeout=30000)
                tiktok_logger.error("[tiktok] TikTok cookie 失效，需要登录")
                return False
            except:
                tiktok_logger.success("[tiktok] cookie 有效")
                return True
        except:
            tiktok_logger.error("[tiktok] 等待 TikTok 页面超时，cookie 可能失效")
            await context.close()
            await browser.close()
            return False


async def cookie_auth_instagram(account_file):
    """
    验证Instagram账号Cookie是否有效
    
    Args:
        account_file: Cookie文件路径
    
    Returns:
        bool: Cookie是否有效
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Instagram创作者中心上传页面
        await page.goto("https://www.instagram.com/create/upload/")
        try:
            # 等待页面加载完成
            await page.wait_for_url("https://www.instagram.com/create/upload/", timeout=30000)
            # 检查是否需要登录
            try:
                await page.get_by_text("Log in", timeout=15000)
                instagram_logger.error("[instagram] cookie 失效，需要登录")
                return False
            except:
                instagram_logger.success("[instagram] cookie 有效")
                return True
        except:
            instagram_logger.error("[instagram] 等待页面超时，cookie 可能失效")
            await context.close()
            await browser.close()
            return False

async def cookie_auth_facebook(account_file):
    """
    验证Facebook账号Cookie是否有效
    
    Args:
        account_file: Cookie文件路径
    
    Returns:
        bool: Cookie是否有效
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Facebook主页
        await page.goto("https://www.facebook.com/")
        try:
            # 等待页面加载完成
            await page.wait_for_url("https://www.facebook.com/", timeout=30000)
            # 检查是否需要登录
            try:
                await page.get_by_text("Log in", timeout=15000)
                tiktok_logger.error("[facebook] cookie 失效，需要登录")
                return False
            except:
                tiktok_logger.success("[facebook] cookie 有效")
                return True
        except:
            tiktok_logger.error("[facebook] 等待页面超时，cookie 可能失效")
            await context.close()
            await browser.close()
            return False

async def cookie_auth_bilibili(account_file):
    """
    验证Bilibili账号Cookie是否有效
    
    Args:
        account_file: Cookie文件路径
    
    Returns:
        bool: Cookie是否有效
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Bilibili创作中心
        await page.goto("https://member.bilibili.com/platform/home")
        try:
            # 等待页面加载完成
            await page.wait_for_url("https://member.bilibili.com/platform/home", timeout=30000)
            # 检查是否需要登录
            try:
                await page.get_by_text("登录", timeout=15000)
                tiktok_logger.error("[bilibili] cookie 失效，需要登录")
                return False
            except:
                tiktok_logger.success("[bilibili] cookie 有效")
                return True
        except:
            tiktok_logger.error("[bilibili] 等待页面超时，cookie 可能失效")
            await context.close()
            await browser.close()
            return False

async def cookie_auth_baijiahao(account_file):
    """
    验证Baijiahao账号Cookie是否有效
    
    Args:
        account_file: Cookie文件路径
    
    Returns:
        bool: Cookie是否有效
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问Baijiahao创作中心
        await page.goto("https://baijiahao.baidu.com/builder/rc/home")
        try:
            # 等待页面加载完成
            await page.wait_for_url("https://baijiahao.baidu.com/builder/rc/home", timeout=30000)
            # 检查是否需要登录
            try:
                await page.get_by_text("登录", timeout=15000)
                tiktok_logger.error("[baijiahao] cookie 失效，需要登录")
                return False
            except:
                tiktok_logger.success("[baijiahao] cookie 有效")
                return True
        except:
            tiktok_logger.error("[baijiahao] 等待页面超时，cookie 可能失效")
            await context.close()
            await browser.close()
            return False

async def check_cookie(type, file_path):
    """
    根据平台类型验证Cookie有效性
    
    Args:
        type: 平台类型 (1:小红书, 2:腾讯视频号, 3:抖音, 4:快手, 5:TikTok, 6:Instagram, 7:Facebook)
        file_path: Cookie文件路径
    
    Returns:
        bool: Cookie是否有效
    """
    match type:
        # 小红书
        case 1:
            return await cookie_auth_xhs(Path(BASE_DIR / "cookiesFile" / file_path))
        # 视频号
        case 2:
            return await cookie_auth_tencent(Path(BASE_DIR / "cookiesFile" / file_path))
        # 抖音
        case 3:
            return await cookie_auth_douyin(Path(BASE_DIR / "cookiesFile" / file_path))
        # 快手
        case 4:
            return await cookie_auth_ks(Path(BASE_DIR / "cookiesFile" / file_path))
        # TikTok
        case 5:
            return await cookie_auth_tiktok(Path(BASE_DIR / "cookiesFile" / file_path))
        # Instagram
        case 6:
            return await cookie_auth_instagram(Path(BASE_DIR / "cookiesFile" / file_path))
        # Facebook
        case 7:
            return await cookie_auth_facebook(Path(BASE_DIR / "cookiesFile" / file_path))
        # Bilibili
        case 8:
            return await cookie_auth_bilibili(Path(BASE_DIR / "cookiesFile" / file_path))
        # Baijiahao
        case 9:
            return await cookie_auth_baijiahao(Path(BASE_DIR / "cookiesFile" / file_path))
        case _:
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)
