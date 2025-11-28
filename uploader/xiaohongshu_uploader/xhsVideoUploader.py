# -*- coding: utf-8 -*-
"""
xhs平台视频上传核心实现
"""
import os
import asyncio
from datetime import datetime
from playwright.async_api import Playwright, async_playwright
from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import xhs_logger as logger


class xhsVideoUploader(object):
    """
    小红书视频上传器类
    """
    
    def __init__(self, account_file, file_path, title, text, tags, publish_date):
        self.title = title
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None
        self.text = text
        
        # URL constants
        self.platform_name = "xhs"
        self.creator_url = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video&openFilePicker=true"
        self.personal_url = "https://creator.xiaohongshu.com/new/home"
        self.login_url = "https://creator.xiaohongshu.com/login"
        
        # Selector lists
        self.upload_button_selectors = [
            'input.upload-input[type="file"]'
        ]
        self.publish_button_selectors = [
            'div.d-button-content span.d-text:has-text("发布")'
        ]
        self.error_selectors = [
            'div:has-text("error"):visible',
            'div:has-text("Error"):visible',
            'div[class*="error"]:visible'
        ]
        self.editor_button_locators = [
            # 标题输入框选择器
            'div.d-input.\--color-text-title.\--color-bg-fill input.d-text[type="text"]'
        ]
        self.textbox_selectors = [
            # 正文输入框选择器
            'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
        ]
        self.schedule_button_selectors = [
            "//span[text()='Schedule']",
            "//span[text()='定时']"
        ]
        self.file_input_selectors = ['input[type="file"]']
        
        # Timeout and retry constants
        self.timeout_30s = 30000
        self.timeout_60s = 60000
        self.max_publish_attempts = 3
        self.upload_check_interval = 2
        self.wait_timeout_500ms = 500
        self.wait_timeout_300ms = 300
        self.sleep_2s = 2
        self.login_wait_timeout = 10000
        self.max_retry_delay = 10
        self.date_format = '%Y-%m-%d'
        self.time_format = '%H:%M'
        self.file_input_selector = "//input[@type='file']"
        self.browser_lang = 'en-US'
        
        # Browser launch options
        self.browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--ignore-certificate-errors',
            '--start-maximized',
            '--disable-blink-features=AutomationControlled'
        ]
        self.slow_mo = 50

    async def main(self):
        """
        主入口函数
        """
        # 验证平台cookie是否有效(可选：如果已登录，可跳过验证)
        if not await self.platform_setup(handle=True):
            raise Exception(f"{self.platform_name} Cookie验证失败")

        # 执行平台上传视频
        async with async_playwright() as playwright:
            await self.upload(playwright)

        logger.info(f"{self.platform_name}视频上传成功: {self.title}")
        return True

    async def upload(self, playwright: Playwright) -> None:
        """
        作用：执行视频上传
        """
        logger.info(f'开始上传视频: {self.title}')
        # step1.创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless, 
            executable_path=self.local_executable_path
        )
        logger.info(f"step1: {self.platform_name}浏览器实例创建成功")


        # step2.创建上下文并加载cookie
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        logger.info(f"step2: {self.platform_name}浏览器上下文创建成功")


        # step3.创建新页面，导航到上传页面，明确指定等待domcontentloaded状态
        page = await context.new_page()
        await page.goto(self.creator_url, wait_until='domcontentloaded', timeout=self.timeout_60s)
        logger.info(f"step3: {self.platform_name}页面加载完成")
        
        # step4.选择基础定位器
        await self.choose_base_locator(page)
        logger.info(f"step4: {self.platform_name}基础定位器选择完成")

        # step5.上传视频文件
        await self.upload_video_file(page)
        logger.info(f"step5: {self.platform_name}视频文件上传完成")

        # step6.检测上传状态
        await self.detect_upload_status(page)
        logger.info(f"step6: {self.platform_name}上传状态检测完成")
        
        # step7.添加标题和标签
        await self.add_title_tags(page)
        logger.info(f"step7: {self.platform_name}标题和标签添加完成")

        logger.info(f"step8: {self.platform_name}跳过设置缩略图")

        # step9.设置定时发布（如果需要）
        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
            logger.info(f"step9: {self.platform_name}定时发布设置完成")
        logger.info(f"step9: {self.platform_name}跳过定时发布")
        
        # step10.点击发布
        await self.click_publish(page)
        logger.info(f"step10：{self.platform_name}视频已发布")   

        # step11.重新保存最新cookie
        await context.storage_state(path=f"{self.account_file}")  
        logger.info(f"step11：{self.platform_name}cookie已更新")

        await asyncio.sleep(self.sleep_2s)  # close delay for look the video status
        
        # step12.关闭所有页面和浏览器上下文
        await context.close()
        await browser.close()
        logger.info(f"step12：{self.platform_name}浏览器实例已关闭")

    async def choose_base_locator(self, page):
        """
        选择基础定位器
        """
        # 通用平台不需要处理iframe，直接使用page即可
        self.locator_base = page

    async def find_button(self, selector_list):
        """
        通用的按钮查找方法
        Args:
            selector_list: 所有可能的按钮选择器列表
        Returns:
            找到的按钮定位器对象，如果没找到则返回None
        """
        for selector in selector_list:
            # 检查当前选择器是否在页面上存在匹配的元素
            count = await self.locator_base.locator(selector).count()
            if count > 0:
                # 异步等待元素可交互（避免元素未加载完成）
                await self.locator_base.locator(selector).wait_for(state="visible", timeout=self.timeout_30s)
                # logger.info(f"找到按钮定位器: {selector}, 是否可见: {await self.locator_base.locator(selector).is_visible()}")
                # 返回找到的按钮定位器
                return self.locator_base.locator(selector)

        # 如果所有选择器都没找到，返回None
        logger.info("未找到任何按钮定位器")
        return None

    async def upload_video_file(self, page):
        """
        作用：上传视频文件
        网页中相关按钮：上传视频文件的按钮元素为（）
        """
        try:
            # 使用find_button方法查找上传按钮，支持中文和英文界面
            await asyncio.sleep(self.sleep_2s)
            upload_button = await self.find_button(self.upload_button_selectors)
            if not upload_button:
                raise Exception("未找到上传视频按钮")
            logger.info("  [-] 将点击上传视频按钮")
            await upload_button.wait_for(state='visible', timeout=self.timeout_30s)
            
            # 上传按钮，需要点击触发系统文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            logger.info(f"通过系统文件选择器上传文件: {self.file_path}")
        except Exception as e:
            logger.error(f"选择视频文件失败: {str(e)}")
            raise

    async def detect_upload_status(self, page):
        """
        作用：检测上传状态
        网页中相关按钮：发布按钮选择器（）
        """
        while True:
            try:
                # 使用find_button方法查找发布按钮
                publish_button = await self.find_button(self.publish_button_selectors)
                
                # 检查发布按钮是否可点击
                if publish_button and await publish_button.get_attribute("disabled") is None:
                    logger.info("  [-]video uploaded.")
                    break
                else:
                    logger.info("  [-] video uploading...")
                    await asyncio.sleep(self.upload_check_interval)
                    # 检查是否有错误需要重试，使用中文和英文选择器
                    error_element = await self.find_button(self.error_selectors)
                    if error_element:
                        logger.info("  [-] found error while uploading now retry...")
                        await self.handle_upload_error(page)
            except Exception as e:
                logger.info(f"  [-] video uploading... Error: {str(e)}")
                await asyncio.sleep(self.upload_check_interval)

    async def handle_upload_error(self, page):
        """
        作用：处理上传错误，重新上传
        网页中相关按钮：系统文件管理器的上传按钮（input[type="file"]）
        """
        logger.info("video upload error retrying.")
        try:
            # 使用find_button方法查找文件上传按钮
            file_input_button = await self.find_button(self.file_input_selectors)
            if file_input_button:
                await file_input_button.set_input_files(self.file_path)
        except Exception as e:
            logger.error(f"重新上传失败: {str(e)}")
    
    async def add_title_tags(self, page):
        """
        作用：添加标题和标签
        网页中相关按钮：添加标题和标签的按钮选择器（）
        """
        try:
            # 输入标题
            if self.title:
                # 使用find_button方法定位标题输入框，支持中文和英文界面
                editor_button = await self.find_button(self.editor_button_locators)
                if not editor_button:
                    raise Exception("未找到标题输入框")
                logger.info(f"  [-] 将点击标题输入框: {await editor_button.text_content()}")
                await editor_button.click()
                
                # 清空现有内容
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
                    
                # 输入标题
                await page.keyboard.insert_text(self.title)
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒


            # 输入正文
            if self.text:
                textbox_button = await self.find_button(self.textbox_selectors)
                if textbox_button:
                    logger.info(f"  [-] 将点击正文输入框: {await textbox_button.text_content()}")
                await textbox_button.click()
                # 清空现有内容（如果有）
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
                        
                # 输入正文
                await page.keyboard.insert_text(self.text)
                await page.wait_for_timeout(self.wait_timeout_500ms)  # 等待500毫秒
            
            # 输入标签（跟在正文后面）
            if self.tags:
                await page.keyboard.press("Enter")
                await page.keyboard.press("Enter")
                    
                for index, tag in enumerate(self.tags, start=1):
                    logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    # 等待300毫秒
                    await page.wait_for_timeout(self.wait_timeout_300ms)
        except Exception as e:
            logger.error(f"Failed to add title, text and tags: {str(e)}")

    async def set_schedule_time(self, page, publish_date):
        """
        设置定时发布时间
        """
        # 使用find_button方法查找定时发布按钮
        schedule_button = await self.find_button(self.schedule_button_selectors)
        if not schedule_button:
            raise Exception("未找到定时发布按钮")
        logger.info(f"  [-] 将点击定时发布按钮: {await schedule_button.text_content()}")
        await schedule_button.wait_for(state='visible')
        await schedule_button.click()

        # 解析时间戳
        publish_datetime = publish_date
        if isinstance(publish_date, int):
            publish_datetime = datetime.fromtimestamp(publish_date)

        # 设置日期和时间
        await page.fill('[aria-label="Date"]', publish_datetime.strftime(self.date_format))
        await page.fill('[aria-label="Time"]', publish_datetime.strftime(self.time_format))
        
        logger.info(f"  [-] 定时发布时间设置为: {publish_datetime}")

    async def click_publish(self, page):
        """
        作用：点击发布按钮并等待发布完成
        参数：
            page: Playwright页面对象
        返回值：
            bool: 发布是否成功
        """
        max_attempts = self.max_publish_attempts  # 最大尝试次数
        attempt = 0
        publish_success = False
        
        # 上传按钮选择器列表
        
        while attempt < max_attempts and not publish_success:
            attempt += 1
            try:
                # 步骤1: 查找并点击发布按钮
                publish_button = await self.find_button(self.publish_button_selectors)
                if publish_button:
                    await publish_button.click()

                # 步骤2: 等待视频处理完成（通过检查上传按钮重新出现）
                logger.info("等待发布完成...")
                # 尝试查找上传按钮
                upload_button = await self.find_button(self.upload_button_selectors)
                logger.info(f"发布尝试 {attempt}，上传按钮可见状态: {await upload_button.is_visible()}")

                if upload_button:
                    await upload_button.wait_for(state='visible', timeout=self.timeout_30s)
                    publish_success = True
                    break
            except Exception:
                # 等待后重试
                logger.warning(f"发布尝试 {attempt} 失败，等待重试...")
                await asyncio.sleep(min(attempt * 2, self.max_retry_delay))
        
        # 最终状态检查
        if publish_success:
            logger.info("视频发布完成")
        else:
            logger.error(f"视频发布失败，已尝试 {max_attempts} 次")
        return publish_success


    async def platform_setup(self, handle=False):
        """
        设置平台账户cookie
        """
        account_file = get_absolute_path(self.account_file, "cookiesFile")
        if not os.path.exists(account_file) or not await self.cookie_auth():
            if not handle:
                return False
            logger.info("Cookie文件不存在，需要获取新的Cookie")
            await self.get_platform_cookie(account_file, self.local_executable_path, self.timeout_60s, self.login_url, self.login_wait_timeout, self.browser_lang)
        return True


    async def cookie_auth(self):
        """
        验证平台的cookie是否有效
        """
        async with async_playwright() as playwright:
            # 设置本地Chrome浏览器路径
            browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
            context = await browser.new_context(storage_state=self.account_file)
            context = await set_init_script(context)
            # 创建一个新的页面
            page = await context.new_page()
            # 访问平台个人中心页面url验证cookie，明确指定等待domcontentloaded状态
            await page.goto(self.personal_url, wait_until='domcontentloaded', timeout=self.timeout_60s)
            logger.info("平台个人中心页面DOM加载完成")
            
            try:
                # 检查是否登录成功（如果成功跳转到个人中心页面的url）
                current_url = page.url
                logger.info(f"当前页面URL: {current_url}")
                if self.personal_url in current_url:
                    logger.info("Cookie有效")
                    return True
                else:
                    logger.error("Cookie已过期")
                    return False

            except Exception as e:
                logger.error(f"Cookie验证失败: {str(e)}")
                return False
            finally:
                await browser.close()


    async def get_platform_cookie(self, account_file, executable_path, timeout, login_url, login_wait_timeout, browser_lang):
        """
        获取平台登录cookie
        """
        async with async_playwright() as playwright:
            options = {
                'args': [
                    f'--lang {browser_lang}',
                ],
                'headless': False,  # 登录时需要可视化
                'executable_path': executable_path,
            }
            # Make sure to run headed.
            browser = await playwright.chromium.launch(**options)
            # Setup context however you like.
            context = await browser.new_context()  # Pass any options
            context = await set_init_script(context)
            # Pause the page, and start recording manually.
            page = await context.new_page()
            await page.goto(self.login_url, wait_until='domcontentloaded', timeout=timeout)
            await page.pause()
            # 等待用户登录完成
            logger.info("请在浏览器中登录小红书账号")
            await page.wait_for_timeout(login_wait_timeout)
            # 保存cookie
            await context.storage_state(path=account_file)
            logger.info(f"Cookie已保存到: {account_file}")
            await browser.close()


    async def setup_upload_browser(self, playwright):
        """
        设置上传浏览器
        """
        # 创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless,
            executable_path=self.local_executable_path,
            args=self.browser_args,
            slow_mo=self.slow_mo
        )
        
        # 创建上下文并加载cookie
        account_file = get_absolute_path(self.account_file, "cookiesFile")
        if os.path.exists(account_file):
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            return browser, context
        else:
            raise FileNotFoundError(f"Cookie文件不存在: {account_file}")
