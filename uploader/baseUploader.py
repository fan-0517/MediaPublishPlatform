# -*- coding: utf-8 -*-
"""
通用多平台视频上传核心实现
"""
import os
import asyncio
from datetime import datetime
from playwright.async_api import Playwright, async_playwright
from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.files_times import get_absolute_path
from utils.log import create_logger

# 平台配置字典
PLATFORM_CONFIGS = {
    "xiaohongshu": {
        "platform_name": "小红书",
        "personal_url": "https://creator.xiaohongshu.com/new/home",
        "login_url": "https://creator.xiaohongshu.com/login",
        "creator_video_url": "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video&openFilePicker=true",
        "creator_image_url": "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&openFilePicker=true",
        "selectors": {
            "upload_button": ['input.upload-input[type="file"]'],
            "publish_button": ['div.d-button-content span.d-text:has-text("发布")'],
            "title_editor": [
                '[contenteditable="true"][role="textbox"][data-lexical-editor="true"]',
                '[aria-placeholder*="分享你的新鲜事"][contenteditable="true"]',
                '[aria-label="Add a description"]',
                '[aria-label="Write something..."]'
            ],
            "thumbnail_button": ["//span[contains(text(), 'Add')]", "//span[contains(text(), '添加')]"],
            "schedule_button": ["//span[text()='Schedule']", "//span[text()='定时']"],
            "date_input": '[aria-label="Date"]',
            "time_input": '[aria-label="Time"]',
        },
        "features": {
            "thumbnail": False,
            "schedule": False,
            "tags": True,
            "skip_cookie_verify": False
        }
    }    

    
}


class BaseVideoUploader(object):
    """
    通用视频上传器基类参数说明：
    account_file: 账号cookie文件路径
    file_type: 文件类型，1为图文，2为视频
    file_path: 文件路径
    title: 文件标题
    text: 文件正文描述
    tags: 文件标签，多个标签用逗号隔开
    publish_date: 发布时间，格式为YYYY-MM-DD HH:MM:SS
    """
    
    def __init__(self, platform, account_file, file_type, file_path, title, text, tags, publish_date):
        self.platform = platform
        self.account_file = account_file
        self.file_type = file_type
        self.file_path = file_path
        self.title = title
        self.text = text
        self.tags = tags
        self.publish_date = publish_date
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.locator_base = None
        
        # 获取平台配置
        self.config = PLATFORM_CONFIGS.get(self.platform)
        if not self.config:
            raise ValueError(f"不支持的平台: {self.platform}")

        # URL constants
        # 平台名称
        self.platform_name = self.config["platform_name"]
        # 个人中心页面URL
        self.personal_url = self.config["personal_url"]
        # 登录页面URL
        self.login_url = self.config["login_url"]
        # 视频上传页面URL
        self.creator_video_url = self.config["creator_video_url"]
        # 图文上传页面URL
        self.creator_image_url = self.config["creator_image_url"]

        # Selector lists
        # 上传按钮选择器
        self.upload_button_selectors = self.config["selectors"]["upload_button"]
        # 发布按钮选择器
        self.publish_button_selectors = self.config["selectors"]["publish_button"]
        # 错误信息选择器
        self.error_selectors = self.config["selectors"]["error"]
        # 标题编辑器输入框选择器
        self.editor_button_locators = self.config["selectors"]["title_editor"]
        # 正文编辑器输入框选择器
        self.textbox_selectors = self.config["selectors"]["textbox"]
        # 发布时间选择器
        self.schedule_button_selectors = self.config["selectors"]["schedule_button"]
        
        
        # constants
        # 日志记录器
        self.logger = create_logger (self.platform_name, f'logs/{self.platform_name}.log')
        # 是否跳过验证cookie有效性
        self.skip_cookie_verify = self.config["features"]["skip_cookie_verify"]
        # 视频/图文发布状态
        self.publish_status = False
        #按钮等待可见超时时间
        self.button_visible_timeout = 30000
        #网页加载超时时间
        self.page_load_timeout = 60000
        # 检查间隔时间
        self.check_interval = 2
        # 500ms等待超时时间
        self.wait_timeout_500ms = 500
        # 登录等待超时时间
        self.login_wait_timeout = 10000
        # 最大发布尝试次数
        self.max_publish_attempts = 3
        # 最大重试延迟时间
        self.max_retry_delay = 10
        # 日期格式
        self.date_format = '%Y-%m-%d'
        # 时间格式
        self.time_format = '%H:%M'
        # 系统文件输入选择器
        self.file_input_selector = ['input[type="file"]']

        # Browser launch options
        # 浏览器语言
        self.browser_lang = 'en-US'
        # 慢速模式，模拟人类操作，增加稳定性
        self.slow_mo = 50
        self.browser_args = [
            # 禁用沙盒模式，允许在容器中运行
            '--no-sandbox',
            # 禁用/共享内存使用，解决资源冲突问题
            '--disable-dev-shm-usage',
            # 禁用GPU加速，防止渲染问题
            '--disable-gpu',
            # 忽略证书错误，允许加载不安全的页面
            '--ignore-certificate-errors',
            # 启动时最大化窗口，避免元素遮挡
            '--start-maximized',
            # 禁用自动化控制特征，防止被检测为自动化工具
            '--disable-blink-features=AutomationControlled'
        ]

    async def main(self):
        """
        主入口函数
        """
        # 验证平台cookie是否有效(可选：如果已登录，可跳过验证)
        if not self.skip_cookie_verify:
            if not await self.platform_setup(handle=True):
                raise Exception(f"{self.platform_name} Cookie验证失败")

        # 执行平台上传视频
        async with async_playwright() as playwright:
            await self.upload(playwright)

        self.logger.info(f"{self.platform_name}视频上传成功: {self.title}")
        return self.publish_status

    async def upload(self, playwright: Playwright) -> None:
        """
        作用：执行视频上传
        """
        self.logger.info(f'开始上传视频: {self.title}')
        # step1.创建浏览器实例
        browser = await playwright.chromium.launch(
            headless=self.headless, 
            executable_path=self.local_executable_path
        )
        self.logger.info(f"step1: {self.platform_name}浏览器实例创建成功")


        # step2.创建上下文并加载cookie
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)
        self.logger.info(f"step2: {self.platform_name}浏览器上下文创建成功")


        # step3.创建新页面，导航到上传页面，明确指定等待domcontentloaded状态
        page = await context.new_page()
        # 根据文件类型选择上传页面
        if self.file_type == 1:
            await page.goto(self.creator_image_url, wait_until='domcontentloaded', timeout=self.page_load_timeout)
        else:
            await page.goto(self.creator_video_url, wait_until='domcontentloaded', timeout=self.page_load_timeout)
        self.logger.info(f"step3: {self.platform_name}页面加载完成")
        
        # step4.选择基础定位器
        await self.choose_base_locator(page)
        self.logger.info(f"step4: {self.platform_name}基础定位器选择完成")

        # step5.上传视频文件
        await self.upload_video_file(page)
        self.logger.info(f"step5: {self.platform_name}视频文件上传完成")

        # step6.检测上传状态
        await self.detect_upload_status(page)
        self.logger.info(f"step6: {self.platform_name}上传状态检测完成")
        
        # step7.添加标题和标签
        await self.add_title_tags(page)
        self.logger.info(f"step7: {self.platform_name}标题和标签添加完成")

        self.logger.info(f"step8: {self.platform_name}跳过设置缩略图")

        # step9.设置定时发布（如果需要）
        if self.publish_date != 0:
            await self.set_schedule_time(page, self.publish_date)
            self.logger.info(f"step9: {self.platform_name}定时发布设置完成")
        self.logger.info(f"step9: {self.platform_name}跳过定时发布")
        
        # step10.点击发布
        await self.click_publish(page)
        self.logger.info(f"step10：{self.platform_name}视频已点击发布按钮")   

        # step11.重新保存最新cookie
        await context.storage_state(path=f"{self.account_file}")  
        self.logger.info(f"step11：{self.platform_name}cookie已更新")

        await asyncio.sleep(self.check_interval)  # close delay for look the video status
        
        # step12.关闭所有页面和浏览器上下文
        await context.close()
        await browser.close()
        self.logger.info(f"step12：{self.platform_name}浏览器窗口已关闭")

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
                await self.locator_base.locator(selector).wait_for(state="visible", timeout=self.button_visible_timeout)
                # self.logger.info(f"找到按钮定位器: {selector}, 是否可见: {await self.locator_base.locator(selector).is_visible()}")
                # 返回找到的按钮定位器
                return self.locator_base.locator(selector)

        # 如果所有选择器都没找到，返回None
        self.logger.info("未找到任何按钮定位器")
        return None

    async def upload_video_file(self, page):
        """
        作用：上传视频文件
        网页中相关按钮：上传视频文件的按钮元素为（）
        """
        try:
            # 使用find_button方法查找上传按钮，支持中文和英文界面
            await asyncio.sleep(self.check_interval)
            upload_button = await self.find_button(self.upload_button_selectors)
            if not upload_button:
                raise Exception("未找到上传视频按钮")
            self.logger.info("  [-] 将点击上传视频按钮")
            await upload_button.wait_for(state='visible', timeout=self.button_visible_timeout)
            
            # 上传按钮，需要点击触发系统文件选择器
            async with page.expect_file_chooser() as fc_info:
                await upload_button.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(self.file_path)
            self.logger.info(f"通过系统文件选择器上传文件: {self.file_path}")
        except Exception as e:
            self.logger.error(f"选择视频文件失败: {str(e)}")
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
                    self.logger.info("  [-]video uploaded.")
                    break
                else:
                    self.logger.info("  [-] video uploading...")
                    await asyncio.sleep(self.check_interval)
                    # 检查是否有错误需要重试，使用中文和英文选择器
                    error_element = await self.find_button(self.error_selectors)
                    if error_element:
                        self.logger.info("  [-] found error while uploading now retry...")
                        await self.handle_upload_error(page)
            except Exception as e:
                self.logger.info(f"  [-] video uploading... Error: {str(e)}")
                await asyncio.sleep(self.check_interval)

    async def handle_upload_error(self, page):
        """
        作用：处理上传错误，重新上传
        网页中相关按钮：系统文件管理器的上传按钮（input[type="file"]）
        """
        self.logger.info("video upload error retrying.")
        try:
            # 使用find_button方法查找文件上传按钮
            file_input_button = await self.find_button(self.file_input_selector)
            if file_input_button:
                await file_input_button.set_input_files(self.file_path)
        except Exception as e:
            self.logger.error(f"重新上传失败: {str(e)}")
    
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
                self.logger.info(f"  [-] 将点击标题输入框: {await editor_button.text_content()}")
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
                    self.logger.info(f"  [-] 将点击正文输入框: {await textbox_button.text_content()}")
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
                    self.logger.info("Setting the %s tag" % index)
                    await page.keyboard.insert_text(f"#{tag} ")
                    # 等待300毫秒
                    await page.wait_for_timeout(self.wait_timeout_500ms)
        except Exception as e:
            self.logger.error(f"Failed to add title, text and tags: {str(e)}")

    async def set_schedule_time(self, page, publish_date):
        """
        设置定时发布时间
        """
        # 使用find_button方法查找定时发布按钮
        schedule_button = await self.find_button(self.schedule_button_selectors)
        if not schedule_button:
            raise Exception("未找到定时发布按钮")
        self.logger.info(f"  [-] 将点击定时发布按钮: {await schedule_button.text_content()}")
        await schedule_button.wait_for(state='visible')
        await schedule_button.click()

        # 解析时间戳
        publish_datetime = publish_date
        if isinstance(publish_date, int):
            publish_datetime = datetime.fromtimestamp(publish_date)

        # 设置日期和时间
        await page.fill('[aria-label="Date"]', publish_datetime.strftime(self.date_format))
        await page.fill('[aria-label="Time"]', publish_datetime.strftime(self.time_format))
        
        self.logger.info(f"  [-] 定时发布时间设置为: {publish_datetime}")

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
        
        while attempt < max_attempts and not self.publish_status:
            attempt += 1
            try:
                # 步骤1: 查找并点击发布按钮
                publish_button = await self.find_button(self.publish_button_selectors)
                if publish_button:
                    await publish_button.click()

                # 步骤2: 等待视频处理完成（通过检查上传按钮重新出现）
                self.logger.info("等待发布完成...")
                # 尝试查找上传按钮
                upload_button = await self.find_button(self.upload_button_selectors)
                self.logger.info(f"发布尝试 {attempt}，上传按钮可见状态: {await upload_button.is_visible()}")

                if upload_button:
                    await upload_button.wait_for(state='visible', timeout=self.button_visible_timeout)
                    self.publish_status = True
                    break
            except Exception:
                # 等待后重试
                self.logger.warning(f"发布尝试 {attempt} 失败，等待重试...")
                await asyncio.sleep(min(attempt * 2, self.max_retry_delay))
        
        # 最终状态检查
        if self.publish_status:
            self.logger.info("视频发布完成")
        else:
            self.logger.error(f"视频发布失败，已尝试 {max_attempts} 次")
        return self.publish_status


    async def platform_setup(self, handle=False):
        """
        设置平台账户cookie
        """
        account_file = get_absolute_path(self.account_file, "cookiesFile")
        if not os.path.exists(account_file) or not await self.cookie_auth():
            if not handle:
                return False
            self.logger.info("Cookie文件不存在，需要获取新的Cookie")
            await self.get_platform_cookie(account_file, self.local_executable_path, self.page_load_timeout, self.login_url, self.login_wait_timeout, self.browser_lang)
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
            await page.goto(self.personal_url, wait_until='domcontentloaded', timeout=self.page_load_timeout)
            self.logger.info("平台个人中心页面DOM加载完成")
            
            try:
                # 检查是否登录成功（如果成功跳转到个人中心页面的url）
                current_url = page.url
                self.logger.info(f"当前页面URL: {current_url}")
                if self.personal_url in current_url:
                    self.logger.info("Cookie有效")
                    return True
                else:
                    self.logger.error("Cookie已过期")
                    return False

            except Exception as e:
                self.logger.error(f"Cookie验证失败: {str(e)}")
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
            self.logger.info("请在浏览器中登录小红书账号")
            await page.wait_for_timeout(login_wait_timeout)
            # 保存cookie
            await context.storage_state(path=account_file)
            self.logger.info(f"Cookie已保存到: {account_file}")
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




# 工厂函数和便捷函数
async def run_upload(platform, account_file, file_type, file_path, title, text, tags, publish_date, **kwargs):
    """
    运行上传任务
    """
    uploader = BaseVideoUploader(platform, account_file, file_type, file_path, title, text, tags, publish_date)
    return await uploader.main()


# 特定平台上传器类（用于向后兼容和特殊处理）
# 小红书视频上传器
class XiaohongshuVideo(BaseVideoUploader):
    """小红书视频上传器"""
    def __init__(self, account_file, file_type, file_path, title, text, tags, publish_date):
        super().__init__("xiaohongshu", account_file, file_type, file_path, title, text, tags, publish_date)


if __name__ == "__main__":
    # 示例运行代码
    asyncio.run(run_upload(
        "xiaohongshu",
        "cookies/xhs_cookie.json",
        2,  # 文件类型：2为视频
        "videos/demo.mp4",
        "测试视频标题",
        "测试视频正文",
        "测试 标签",
        0  # 立即发布
    ))