# -*- coding: utf-8 -*-
import re
from datetime import datetime

from playwright.async_api import Playwright, async_playwright
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from uploader.ins_uploader.ins_config import Ins_Locator
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import instagram_logger


async def cookie_auth(account_file):
    """
    验证cookie是否有效
    
    Args:
        account_file: cookie文件路径
        
    Returns:
        bool: cookie是否有效
    """
    browser = None
    context = None
    try:
        async with async_playwright() as playwright:
            # 启动浏览器时设置超时
            browser = await playwright.chromium.launch(
                headless=LOCAL_CHROME_HEADLESS,
                timeout=30000  # 30秒启动超时
            )
            context = await browser.new_context(
                storage_state=account_file,
                timeout=30000  # 30秒上下文创建超时
            )
            context = await set_init_script(context)
            # 创建页面
            page = await context.new_page()
            
            # 访问Meta Business Suite创作中心
            await page.goto("https://business.facebook.com/latest/composer", timeout=45000)  # 45秒导航超时
            
            # 等待页面加载完成
            try:
                await page.wait_for_load_state('networkidle', timeout=30000)  # 30秒网络空闲超时
            except TimeoutError:
                instagram_logger.warning("[+] 网络空闲状态等待超时，但继续检查")
            
            # 尝试多种方式验证是否已登录
            try:
                # 检查是否跳转到登录页面
                current_url = page.url
                if "loginpage" in current_url or "login" in current_url:
                    instagram_logger.error("[+] cookie expired - 跳转到登录页面")
                    return False
                
                # 检查是否有登录表单（未登录状态）
                if await page.locator('input[name="email"]').count() > 0 or await page.locator('input[name="pass"]').count() > 0 or await page.locator('button:has-text("使用 Facebook 登录")').count() > 0:
                    instagram_logger.error("[+] cookie expired - 检测到登录表单或登录按钮")
                    return False
                
                # 检查是否有创作中心元素（已登录状态）
                try:
                    # 检查Meta Business Suite创作中心的关键元素
                    await page.locator('div[role="main"]').wait_for(timeout=10000)
                    instagram_logger.success("[+] cookie valid - 检测到Meta Business Suite创作中心元素")
                    return True
                except TimeoutError:
                    instagram_logger.warning("[+] 未检测到创作中心元素，尝试其他验证方式")
                
                # 检查URL是否显示已登录状态
                if current_url.startswith("https://business.facebook.com/") and "login" not in current_url:
                    instagram_logger.success("[+] cookie valid - URL检查通过")
                    return True
                else:
                    instagram_logger.error("[+] cookie expired - URL检查失败")
                    return False
            
            except Exception as e:
                instagram_logger.error(f"Cookie验证检查过程出错: {str(e)}")
                return False
                
    except TimeoutError as e:
        instagram_logger.error(f"Cookie验证超时: {str(e)}")
        return False
    except Exception as e:
        instagram_logger.error(f"Cookie验证初始化错误: {str(e)}")
        return False
    finally:
        # 确保资源被释放
        if context:
            await context.close()
        if browser:
            await browser.close()


async def instagram_setup(account_file, handle=False):
    """
    检查并设置Instagram登录状态
    
    Args:
        account_file: cookie文件路径
        handle: 如果cookie无效，是否自动处理登录
        
    Returns:
        bool: 设置是否成功
    """
    account_file = get_absolute_path(account_file, "ins_uploader")
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            return False
        instagram_logger.info('[+] cookie file is not existed or expired. Now open the browser auto. Please login with your way(gmail phone, whatever, the cookie file will generated after login')
        await get_instagram_cookie(account_file)
    return True


async def get_instagram_cookie(account_file):
    """
    获取Instagram登录cookie
    
    Args:
        account_file: 保存cookie的文件路径
    """
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB',
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # 打开Meta Business Suite创作中心
        page = await context.new_page()
        await page.goto("https://business.facebook.com/latest/composer")
        
        # 等待登录页面加载
        await page.wait_for_load_state('networkidle')
        
        try:
            # 查找并点击使用Instagram登录按钮
            instagram_login_button = page.locator('button:has-text("使用 Instagram 登录")')
            if await instagram_login_button.count() > 0:
                await instagram_login_button.click()
                instagram_logger.info("[+] 已点击使用Instagram登录按钮")
            else:
                # 尝试英文文本
                instagram_login_button = page.locator('button:has-text("Log in with Instagram")')
                if await instagram_login_button.count() > 0:
                    await instagram_login_button.click()
                    instagram_logger.info("[+] 已点击Log in with Instagram按钮")
        except Exception as e:
            instagram_logger.error(f"点击Instagram登录按钮失败: {str(e)}")
        
        await page.pause()
        # 等待用户手动登录后保存cookie
        await context.storage_state(path=account_file)


class InstagramVideo(object):
    """
    Instagram视频上传类
    
    Args:
        title: 视频标题
        file_path: 视频文件路径
        tags: 标签列表
        publish_date: 发布日期
        account_file: 账号cookie文件路径
        thumbnail_path: 缩略图路径
    """
    def __init__(self, title, file_path, tags, publish_date, account_file, thumbnail_path=None):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.thumbnail_path = thumbnail_path
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None

    async def set_schedule_time(self, page, publish_date):
        """
        设置视频发布时间
        
        Args:
            page: playwright页面对象
            publish_date: 发布日期时间对象
        """
        try:
            # 查找并点击更多选项按钮
            more_options_button = self.locator_base.locator('button:has-text("Advanced settings")')
            await more_options_button.wait_for(state='visible')
            await more_options_button.click()
            
            # 查找并点击发布时间选择按钮
            schedule_button = self.locator_base.locator('button:has-text("Schedule")')
            await schedule_button.wait_for(state='visible')
            await schedule_button.click()
            
            # 设置日期
            date_input = self.locator_base.locator('input[type="date"]')
            await date_input.fill(publish_date.strftime("%Y-%m-%d"))
            
            # 设置时间
            time_input = self.locator_base.locator('input[type="time"]')
            await time_input.fill(publish_date.strftime("%H:%M"))
            
            # 确认设置
            confirm_button = self.locator_base.locator('button:has-text("Confirm")')
            await confirm_button.click()
            
            instagram_logger.info(f"[+] 已设置发布时间: {publish_date}")
        except Exception as e:
            instagram_logger.error(f"设置发布时间失败: {str(e)}")

    async def handle_upload_error(self, page):
        """
        处理上传错误，重新上传
        
        Args:
            page: playwright页面对象
        """
        instagram_logger.info("video upload error retrying.")
        try:
            # 重新选择文件
            upload_button = self.locator_base.locator('input[type="file"]')
            await upload_button.set_input_files(self.file_path)
        except Exception as e:
            instagram_logger.error(f"重新上传失败: {str(e)}")

    async def upload(self, playwright: Playwright) -> None:
        """
        上传视频到Instagram
        
        Args:
            playwright: playwright实例
        """
        browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        context = await browser.new_context(storage_state=f"{self.account_file}")
        page = await context.new_page()

        # 访问Instagram创作中心页面（Meta Business Suite）
        await page.goto("https://business.facebook.com/latest/composer")
        instagram_logger.info(f'[+]Uploading-------{self.title}.mp4')

        await page.wait_for_load_state('networkidle')
        
        # 检查是否需要登录
        current_url = page.url
        instagram_logger.info(f"[+]Current URL: {current_url}")
        
        # 如果跳转到登录页面，尝试点击Instagram登录按钮
        if "loginpage" in current_url or "login" in current_url:
            instagram_logger.info("[+]检测到登录页面，尝试点击Instagram登录按钮")
            try:
                # 尝试查找并点击Instagram登录按钮
                # 支持中英文两种文本
                login_buttons = [
                    'div[role="button"]:has-text("使用 Instagram 登录")',
                    'div[role="button"]:has-text("Log in with Instagram")',
                    'button:has-text("使用 Instagram 登录")',
                    'button:has-text("Log in with Instagram")'
                ]
                
                login_button = None
                found_selector = ""
                for selector in login_buttons:
                    count = await page.locator(selector).count()
                    if count > 0:
                        login_button = page.locator(selector)
                        found_selector = selector
                        break
                
                if login_button:
                    instagram_logger.info(f"[+]找到Instagram登录按钮，选择器: {found_selector}")
                    await login_button.wait_for(state='visible', timeout=5000)
                    
                    # 监听新打开的页面
                    new_page = None
                    async with page.context.expect_page() as new_page_info:
                        await login_button.click()
                        instagram_logger.info("[+]已点击Instagram登录按钮，等待新页面打开")
                    
                    # 获取新打开的页面
                    new_page = await new_page_info.value
                    instagram_logger.info(f"[+]新页面已打开，URL: {new_page.url}")
                    
                    # 等待新页面加载完成
                    await new_page.wait_for_load_state('networkidle', timeout=30000)
                    
                    # 等待用户登录完成
                    # 根据截图，新页面是Instagram登录页面，URL包含"accounts/login/"
                    instagram_logger.info("[+]等待用户在新页面完成登录...")
                    
                    # 等待新页面关闭或URL变化
                    # 当用户在新页面完成登录后，新页面可能会自动关闭或跳转
                    try:
                        # 等待新页面关闭或URL不再包含登录相关关键词
                        async with asyncio.timeout(120):  # 2分钟超时
                            while True:
                                # 检查新页面是否已关闭
                                if new_page.is_closed():
                                    instagram_logger.info("[+]新页面已自动关闭，登录完成")
                                    break
                                
                                # 检查新页面URL是否变化
                                new_page_url = new_page.url
                                if "accounts/login/" not in new_page_url and "force_authentication" not in new_page_url:
                                    instagram_logger.info(f"[+]新页面URL已变化，登录完成: {new_page_url}")
                                    break
                                
                                # 等待1秒后再次检查
                                await asyncio.sleep(1)
                    except asyncio.TimeoutError:
                        instagram_logger.warning("[+]等待用户登录超时")
                    except Exception as wait_error:
                        instagram_logger.warning(f"[+]等待登录过程中出错: {str(wait_error)}")
                    
                    # 如果新页面仍未关闭，则手动关闭
                    if not new_page.is_closed():
                        await new_page.close()
                        instagram_logger.info("[+]已手动关闭新登录页面")
                    
                    # 等待原页面加载完成
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # 检查原页面当前URL
                    current_url = page.url
                    instagram_logger.info(f"[+]原页面当前URL: {current_url}")
                else:
                    instagram_logger.warning("[+]未找到Instagram登录按钮")
            except Exception as e:
                instagram_logger.error(f"[+]处理登录页面时出错: {str(e)}")
                # 出错后尝试直接导航回创作中心
                try:
                    await page.goto("https://business.facebook.com/latest/composer")
                    await page.wait_for_load_state('networkidle')
                except Exception as goto_error:
                    instagram_logger.error(f"[+]尝试导航回创作中心失败: {str(goto_error)}")
        
        # 确保最终在正确的创作中心页面
        await page.goto("https://business.facebook.com/latest/composer")
        await page.wait_for_load_state('networkidle')
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after goto composer page: {page.url}")

        # 选择基本定位器
        await self.choose_base_locator(page)
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after choose base locator: {page.url}")

        # 上传视频文件
        await self.upload_video_file(page)
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after upload video file: {page.url}")
        
        # 检测上传状态
        await self.detect_upload_status(page)
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after detect upload status: {page.url}")
        
        # 添加标题和标签
        await self.add_title_tags(page)
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after add title tags: {page.url}")

        if self.thumbnail_path:
            instagram_logger.info(f'[+] Uploading thumbnail file {self.title}.png')
            await self.upload_thumbnails(page)

        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)

        await self.click_publish(page)
        # 打印当前URL
        instagram_logger.info(f"[+]Current URL after click publish: {page.url}")

        await context.storage_state(path=f"{self.account_file}")  # save cookie
        instagram_logger.info('  [instagram] update cookie！')
        await asyncio.sleep(2)  # close delay for look the video status
        # close all
        await context.close()
        await browser.close()

    async def upload_video_file(self, page):
        """
        上传视频文件
        
        Args:
            page: playwright页面对象
        """
        try:
            # 根据日志中的精确选择器简化
            upload_selector = 'div[role="button"]:has-text("Add photo/video")'
            
            upload_element = self.locator_base.locator(upload_selector)
            await upload_element.wait_for(state='visible')
            
            instagram_logger.info(f"[+] 找到上传按钮，选择器: {upload_selector}")
            
            # 上传按钮，需要点击触发文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_element.click()
                instagram_logger.info("[+] 点击上传按钮，等待文件选择器")
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            instagram_logger.info("[+] 通过文件选择器设置文件")
            instagram_logger.info("[+] 视频文件已选择")
        except Exception as e:
            instagram_logger.error(f"选择视频文件失败: {str(e)}")
            raise

    async def add_title_tags(self, page):
        """
        添加视频标题和标签
        
        Args:
            page: playwright页面对象
        """
        try:
            # 根据日志中的精确选择器简化
            caption_selector = 'div[role="combobox"][contenteditable="true"][aria-label*="Write into the dialogue box"]'
            
            caption_field = self.locator_base.locator(caption_selector)
            await caption_field.wait_for(state='visible')
            
            instagram_logger.info(f"[+] 找到文本输入框，选择器: {caption_selector}")
            
            await caption_field.click()
            
            # 清空现有内容
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Delete")
            
            await page.wait_for_timeout(500)  # 等待500毫秒
            
            # 输入标题
            await page.keyboard.insert_text(self.title)
            await page.wait_for_timeout(500)  # 等待500毫秒
            
            # 输入标签
            if self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                
                for index, tag in enumerate(self.tags, start=1):
                    instagram_logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    await page.wait_for_timeout(300)  # 等待300毫秒
            
            instagram_logger.info("[+] 已添加标题和标签")
        except Exception as e:
            instagram_logger.error(f"添加标题和标签失败: {str(e)}")

    async def upload_thumbnails(self, page):
        """
        上传缩略图
        
        Args:
            page: playwright页面对象
        """
        try:
            # Meta Business Suite的缩略图上传可能有不同的选择器
            # 尝试查找多种可能的缩略图上传元素
            thumbnail_buttons = [
                'button:has-text("Add cover")',
                'button:has-text("Upload cover")',
                'button:has-text("Change cover")',
                'div[role="button"]:has-text("Add cover")',
                'div[role="button"]:has-text("Upload cover")',
                'div[role="button"]:has-text("Change cover")'
            ]
            
            thumbnail_button = None
            for selector in thumbnail_buttons:
                if await self.locator_base.locator(selector).count() > 0:
                    thumbnail_button = self.locator_base.locator(selector)
                    break
            
            if thumbnail_button:
                await thumbnail_button.wait_for(state='visible')
                await thumbnail_button.click()
                
                # 查找文件上传输入框
                thumbnail_input = self.locator_base.locator('input[type="file"]').nth(1) if await self.locator_base.locator('input[type="file"]').count() > 1 else self.locator_base.locator('input[type="file"]')
                await thumbnail_input.set_input_files(self.thumbnail_path)
                
                # 确认缩略图
                confirm_buttons = [
                    'button:has-text("Confirm")',
                    'button:has-text("Save")',
                    'button:has-text("Done")',
                    'div[role="button"]:has-text("Confirm")',
                    'div[role="button"]:has-text("Save")',
                    'div[role="button"]:has-text("Done")'
                ]
                
                confirm_button = None
                for selector in confirm_buttons:
                    if await self.locator_base.locator(selector).count() > 0:
                        confirm_button = self.locator_base.locator(selector)
                        break
                
                if confirm_button:
                    await confirm_button.wait_for(state='visible')
                    await confirm_button.click()
                    
            instagram_logger.info("[+] 缩略图已上传")
        except Exception as e:
            instagram_logger.error(f"上传缩略图失败: {str(e)}")

    async def click_publish(self, page):
        """
        点击发布按钮
        
        Args:
            page: playwright页面对象
        """
        max_wait_time = 70  # 最大等待时间（秒）
        wait_time = 0
        
        while wait_time < max_wait_time:
            try:
                # 根据日志中的精确选择器简化 - 只使用日志中出现的选择器
                publish_selector = '*[role="button"]:has(:text("Publish"))'
                
                publish_button = self.locator_base.locator(publish_selector)
                await publish_button.wait_for(state='visible')
                
                # 检查按钮是否可用
                if await publish_button.is_disabled():
                    instagram_logger.info("  [-] 发布按钮不可用，等待...")
                    await asyncio.sleep(1)
                    continue
                
                # 点击发布按钮
                await publish_button.click()
                instagram_logger.info("  [-] 已点击发布按钮")
                
                # 等待发布完成，发布成功后会跳转到内容日历页面
                if "content_calendar" in page.url.lower():
                    instagram_logger.success("  [-] video published success, detected content calendar in URL")
                    break
            except Exception as e:
                instagram_logger.exception(f"  [-] Exception: {e}")
                instagram_logger.info(f"  [-] video publishing, current URL: {page.url}")
                await asyncio.sleep(0.5)
                wait_time += 0.5
        
        # 超时后检查URL
        if wait_time >= max_wait_time:
            instagram_logger.error(f"  [-] 发布超时，当前URL: {page.url}")
            if "content_calendar" in page.url.lower():
                instagram_logger.success("  [-] 虽然超时，但检测到内容日历页面，认为发布成功")
            else:
                raise Exception(f"发布超时，当前URL: {page.url}")

    async def detect_upload_status(self, page):
        """
        检测上传状态
        
        Args:
            page: playwright页面对象
        """
        max_wait_time = 300  # 最大等待时间（秒）
        wait_time = 0
        
        while wait_time < max_wait_time:
            try:
                # 根据Meta Business Suite截图，使用正确的发布按钮选择器
                publish_buttons = [
                    'button:has-text("Publish")',
                    'button:has-text("Post")',
                    'button:has-text("Share")',
                    'button:has-text("Submit")',
                    'button[aria-label="Publish"]',
                    'button[aria-label="Post"]',
                    'button[aria-label="Share"]',
                    'button[aria-label="Submit"]',
                    'button[data-testid="publish-button"]',
                    'button[data-testid="post-button"]',
                    'button[data-testid="share-button"]'
                ]
                
                publish_button = None
                for selector in publish_buttons:
                    if await self.locator_base.locator(selector).count() > 0:
                        publish_button = self.locator_base.locator(selector)
                        break
                
                if publish_button:
                    # 检查发布按钮是否可用
                    is_disabled = await publish_button.is_disabled()
                    if not is_disabled:
                        instagram_logger.info("  [-]video uploaded.")
                        break
                    else:
                        instagram_logger.info("  [-] video uploading...")
                else:
                    # 检查是否有上传进度或完成指示器
                    upload_indicators = [
                        # 检查是否有上传完成的迹象
                        'div:has-text("Upload complete")',
                        'div:has-text("Uploaded")',
                        'div:has-text("Ready to publish")',
                        'div:has-text("Ready to post")',
                        # 检查是否有媒体预览（表示上传完成）
                        'div[class*="media-preview"]',
                        'img[class*="preview-image"]',
                        'video[class*="preview-video"]',
                        # 检查是否有文本输入框（表示可以填写内容，上传已完成）
                        'textarea[placeholder*="Write something"]',
                        'textarea[placeholder*="Add a caption"]',
                        'textarea[placeholder*="Text"]'
                    ]
                    
                    upload_complete = False
                    for selector in upload_indicators:
                        if await self.locator_base.locator(selector).count() > 0:
                            upload_complete = True
                            break
                    
                    if upload_complete:
                        instagram_logger.info("  [-]video uploaded.")
                        break
                    else:
                        instagram_logger.info("  [-] video uploading...")
                
                await asyncio.sleep(2)
                wait_time += 2
                
                # 检查是否有错误提示
                error_elements = self.locator_base.locator('div:has-text("error"):visible, div:has-text("Error"):visible, div[class*="error"]:visible')
                if await error_elements.count() > 0:
                    instagram_logger.info("  [-] found error while uploading now retry...")
                    await self.handle_upload_error(page)
            except Exception as e:
                instagram_logger.info(f"  [-] 上传中，错误: {str(e)}")
                await asyncio.sleep(2)
                wait_time += 2
        
        if wait_time >= max_wait_time:
            instagram_logger.error("  [-] 上传超时")

    async def choose_base_locator(self, page):
        """
        选择基本定位器，处理iframe情况
        
        Args:
            page: playwright页面对象
        """
        # 检查是否有iframe
        if await page.locator('iframe').count():
            # 查找包含上传功能的iframe
            frames = await page.locator('iframe').all()
            for i, frame in enumerate(frames):
                try:
                    frame_locator = page.frame_locator(f'iframe:nth-child({i+1})')
                    # 检查iframe内是否有上传相关元素
                    if await frame_locator.locator('input[type="file"]').count() > 0:
                        self.locator_base = frame_locator
                        instagram_logger.info("[+] 使用iframe定位器")
                        return
                except Exception as e:
                    continue
        # 默认使用body定位器
        self.locator_base = page.locator(Ins_Locator.default)
        instagram_logger.info("[+] 使用默认定位器")

    async def get_last_video_id(self, page):
        """
        获取最后上传的视频ID
        
        Args:
            page: playwright页面对象
            
        Returns:
            str: 视频ID
        """
        try:
            # 导航到个人资料页面
            await page.goto("https://www.instagram.com/me/")
            await page.wait_for_load_state('networkidle')
            
            # 查找第一个视频的链接
            video_link = self.locator_base.locator('a[href*="/reel/"]').first
            await video_link.wait_for(state='visible')
            
            # 获取视频链接
            video_url = await video_link.get_attribute('href')
            
            # 提取视频ID
            if video_url:
                video_id = re.search(r'reel/(\w+)', video_url).group(1) if re.search(r'reel/(\w+)', video_url) else None
                return video_id
        except Exception as e:
            instagram_logger.error(f"获取视频ID失败: {str(e)}")
            return None

    async def main(self):
        """
        主函数，执行上传过程
        """
        async with async_playwright() as playwright:
            await self.upload(playwright)
