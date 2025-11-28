import asyncio
import logging
from pathlib import Path
from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tk_uploader.main_chrome import TiktokVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from uploader.xiaohongshu_uploader.xhsVideoUploader import xhsVideoUploader
from uploader.xiaohongshu_uploader.xhsImageUploader import xhsImageUploader
from uploader.ins_uploader.main_chrome import InstagramVideo
from uploader.fb_uploader.main_chrome import FacebookVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day

logger = logging.getLogger(__name__)


def post_video_tencent(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0, is_draft=False):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = TencentVideo(title, str(file), tags, publish_datetimes[index], cookie, category, is_draft)
            asyncio.run(app.main(), debug=False)


def post_video_DouYin(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0,
                      thumbnail_path = '',
                      productLink = '', productTitle = ''):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = DouYinVideo(title, str(file), tags, publish_datetimes[index], cookie, thumbnail_path, productLink, productTitle)
            asyncio.run(app.main(), debug=False)


def post_video_ks(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = [0 for i in range(len(files))]
    for index, file in enumerate(files):
        for cookie in account_file:
            print(f"文件路径{str(file)}")
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = KSVideo(title, str(file), tags, publish_datetimes[index], cookie)
            asyncio.run(app.main(), debug=False)

def post_video_xhs(account_file, file_type, files, title, text,tags,enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """
    发布图文/视频到小红书平台
    参数:
        account_file: 账号文件列表
        file_type: 文件类型，1-图文 2-视频
        files: 文件列表
        title: 视频标题
        text: 视频正文描述
        tags: 视频标签
        enableTimer: 是否开启定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间列表
        start_days: 开始发布时间偏移天数
    """

    try:
        #平台名称
        platform = "xhs"
        # 生成文件的完整路径
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        file_num = len(files)

        if enableTimer:
            publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day,daily_times, start_days)
        else:
            publish_datetimes = 0

        for index, file in enumerate(files):
            for cookie in account_file:
                try:
                    # 打印视频文件名、标题和 hashtag
                    print(f"{platform}文件名：{file}")
                    # 根据文件名后缀判断文件类型
                    # .jpg,.jpeg,.png,.webp 为图片文件
                    if file.suffix in ['.jpg', '.jpeg', '.png', '.webp']:
                        file_type = 1
                    # .mp4,.mov,.flv,.f4v,.mkv,.rm,.rmvb,.m4v,.mpg,.mpeg,.ts 为视频文件
                    elif file.suffix in ['.mp4', '.mov', '.flv', '.f4v', '.mkv',
                                         '.rm', '.rmvb', '.m4v', '.mpg', '.mpeg', '.ts']:
                        file_type = 2
                    else:
                        logger.error(f"该文件类型暂不支持：{file}")
                        continue

                    print(f"{platform}文件类型：{file_type}")
                    print(f"{platform}标题：{title}")
                    # print(f"正文描述：{text}")
                    print(f"{platform}标签：{tags}")

                    app = xhsVideoUploader(cookie, file_type, file, title, text, tags, publish_datetimes)
                    asyncio.run(app.main(), debug=False)
                    #是否成功发布
                    if app.publish_success:
                        logger.info(f"{platform}文件{file.name}发布成功")
                    else:
                        logger.error(f"{platform}文件{file.name}发布失败")
                    #任务进度
                    logger.info(f"{platform}已发布{index+1}/{file_num}个文件")
                    #全部发布完毕后
                    if index+1 == file_num:
                        logger.info(f"{platform}所有文件发布完成")
                except Exception as e:
                    logger.error(f"{platform}文件{file.name}发布失败: {str(e)}")
                    # 继续尝试其他账号或文件，不中断整个流程
    except Exception as e:
        logger.error(f"{platform}文件{file.name}发布过程中发生异常: {str(e)}")
        # 抛出异常，让调用方处理
        raise



def post_video_TikTok(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, thumbnail_path=''):
    """
    发布视频到TikTok平台
    
    参数:
        title: 视频标题
        files: 视频文件列表
        tags: 视频标签
        account_file: 账号cookie文件列表
        category: 视频分类（默认LIFESTYLE）
        enableTimer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表
        start_days: 开始发布的天数偏移
        thumbnail_path: 封面图片路径（可选）
    """
    try:
        # 生成文件的完整路径
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        # 生成发布时间
        if enableTimer:
            publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
        else:
            publish_datetimes = [0 for i in range(len(files))]
        
        # 遍历文件和账号进行发布
        for index, file in enumerate(files):
            for cookie in account_file:
                # print打印发布信息
                print(f"文件路径: {str(file)}")
                print(f"视频文件名: {file.name}")
                print(f"标题: {title}")
                print(f"标签: {tags}")
                
                # 检查cookie文件是否存在
                #if not cookie.exists():
                #    logger.error(f"TikTok账号cookie文件不存在: {str(cookie)}")
                #    continue
                
                # 初始化cookie设置
                try:
                #    cookie_setup = asyncio.run(tiktok_setup(cookie, handle=True))
                #    # 使用与参考示例相同的方式处理标题和标签
                #    if not title:
                #        title = file.name.replace('.mp4', '').replace('_', ' ')
                #    if not tags:
                #        tags = []
                    
                    # 处理封面图片（与参考示例保持一致）
                    final_thumbnail_path = None
                    # 如果提供了封面路径，使用该路径
                    if thumbnail_path:
                        final_thumbnail_path = Path(BASE_DIR / "videoFile" / thumbnail_path)
                        if not final_thumbnail_path.exists():
                            logger.warning(f"指定的封面文件不存在: {str(final_thumbnail_path)}")
                            final_thumbnail_path = None
                    
                    # 如果没有提供封面或封面不存在，尝试使用与视频同名的png文件
                    if not final_thumbnail_path:
                        auto_thumbnail = file.parent / (file.stem + '.png')
                        if auto_thumbnail.exists():
                            final_thumbnail_path = auto_thumbnail
                            logger.info(f"使用自动检测到的封面文件: {str(final_thumbnail_path)}")
                    
                    # 初始化TikTok视频上传类并执行上传
                    print(f"video_file_name：{file}")
                    print(f"video_title：{title}")
                    print(f"video_hashtag：{tags}")
                    if final_thumbnail_path and final_thumbnail_path.exists():
                        print(f"thumbnail_file_name：{final_thumbnail_path}")
                        app = TiktokVideo(title, file, tags, publish_datetimes[index], cookie, final_thumbnail_path)
                    else:
                        app = TiktokVideo(title, file, tags, publish_datetimes[index], cookie)
                    asyncio.run(app.main(), debug=False)
                    logger.info(f"TikTok视频发布成功: {file.name}")
                except Exception as e:
                    logger.error(f"TikTok视频发布失败: {str(e)}")
                    # 继续尝试其他账号或文件，不中断整个流程
    except Exception as e:
        logger.error(f"TikTok视频发布过程中发生异常: {str(e)}")
        # 抛出异常，让调用方处理
        raise

def post_video_Instagram(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, thumbnail_path=''):
    """
    发布视频到Instagram平台
    
    参数:
        title: 视频标题
        files: 视频文件列表
        tags: 视频标签
        account_file: 账号cookie文件列表
        category: 视频分类（默认LIFESTYLE）
        enableTimer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表
        start_days: 开始发布的天数偏移
        thumbnail_path: 封面图片路径（可选）
    """
    try:
        # 生成文件的完整路径
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        # 生成发布时间
        if enableTimer:
            publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
        else:
            publish_datetimes = [0 for i in range(len(files))]
        
        # 遍历文件和账号进行发布
        for index, file in enumerate(files):
            for cookie in account_file:
                # 打印发布信息
                print(f"文件路径: {str(file)}")
                print(f"视频文件名: {file.name}")
                print(f"标题: {title}")
                print(f"标签: {tags}")
                
                try:
                    # 处理封面图片
                    final_thumbnail_path = None
                    if thumbnail_path:
                        final_thumbnail_path = Path(BASE_DIR / "videoFile" / thumbnail_path)
                        if not final_thumbnail_path.exists():
                            logger.warning(f"指定的封面文件不存在: {str(final_thumbnail_path)}")
                            final_thumbnail_path = None
                    
                    # 如果没有提供封面或封面不存在，尝试使用与视频同名的png文件
                    if not final_thumbnail_path:
                        auto_thumbnail = file.parent / (file.stem + '.png')
                        if auto_thumbnail.exists():
                            final_thumbnail_path = auto_thumbnail
                            logger.info(f"使用自动检测到的封面文件: {str(final_thumbnail_path)}")
                    
                    # 初始化Instagram视频上传类并执行上传
                    print(f"video_file_name：{file}")
                    print(f"video_title：{title}")
                    print(f"video_hashtag：{tags}")
                    if final_thumbnail_path and final_thumbnail_path.exists():
                        print(f"thumbnail_file_name：{final_thumbnail_path}")
                        app = InstagramVideo(title, file, tags, publish_datetimes[index], cookie, final_thumbnail_path)
                    else:
                        app = InstagramVideo(title, file, tags, publish_datetimes[index], cookie)
                    asyncio.run(app.main(), debug=False)
                    logger.info(f"Instagram视频发布成功: {file.name}")
                except Exception as e:
                    logger.error(f"Instagram视频发布失败: {str(e)}")
                    # 继续尝试其他账号或文件，不中断整个流程
    except Exception as e:
        logger.error(f"Instagram视频发布过程中发生异常: {str(e)}")
        # 抛出异常，让调用方处理
        raise


def post_video_Facebook(title, files, tags, account_file, category=TencentZoneTypes.LIFESTYLE.value, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0, thumbnail_path=''):
    """
    发布视频到Facebook平台
    
    参数:
        title: 视频标题
        files: 视频文件列表
        tags: 视频标签
        account_file: 账号cookie文件列表
        category: 视频分类（默认LIFESTYLE）
        enableTimer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表
        start_days: 开始发布的天数偏移
        thumbnail_path: 封面图片路径（可选）
    """
    try:
        # 生成文件的完整路径
        account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
        files = [Path(BASE_DIR / "videoFile" / file) for file in files]
        
        # 生成发布时间
        if enableTimer:
            publish_datetimes = generate_schedule_time_next_day(len(files), videos_per_day, daily_times, start_days)
        else:
            publish_datetimes = [0 for i in range(len(files))]
        
        # 遍历文件和账号进行发布
        for index, file in enumerate(files):
            for cookie in account_file:
                # 打印发布信息
                print(f"文件路径: {str(file)}")
                print(f"视频文件名: {file.name}")
                print(f"标题: {title}")
                print(f"标签: {tags}")
                
                try:
                    # 处理封面图片
                    final_thumbnail_path = None
                    if thumbnail_path:
                        final_thumbnail_path = Path(BASE_DIR / "videoFile" / thumbnail_path)
                        if not final_thumbnail_path.exists():
                            logger.warning(f"指定的封面文件不存在: {str(final_thumbnail_path)}")
                            final_thumbnail_path = None
                    
                    # 如果没有提供封面或封面不存在，尝试使用与视频同名的png文件
                    if not final_thumbnail_path:
                        auto_thumbnail = file.parent / (file.stem + '.png')
                        if auto_thumbnail.exists():
                            final_thumbnail_path = auto_thumbnail
                            logger.info(f"使用自动检测到的封面文件: {str(final_thumbnail_path)}")
                    
                    # 初始化Facebook视频上传类并执行上传
                    print(f"video_file_name：{file}")
                    print(f"video_title：{title}")
                    print(f"video_hashtag：{tags}")
                    if final_thumbnail_path and final_thumbnail_path.exists():
                        print(f"thumbnail_file_name：{final_thumbnail_path}")
                        app = FacebookVideo(title, str(file), tags, publish_datetimes[index], str(cookie), thumbnail_path=final_thumbnail_path)
                    else:
                        app = FacebookVideo(title, str(file), tags, publish_datetimes[index], str(cookie))
                    asyncio.run(app.main(), debug=False)
                    logger.info(f"Facebook视频发布成功: {file.name}")
                except Exception as e:
                    logger.error(f"Facebook视频发布失败: {str(e)}")
                    # 继续尝试其他账号或文件，不中断整个流程
    except Exception as e:
        logger.error(f"Facebook视频发布过程中发生异常: {str(e)}")
        # 抛出异常，让调用方处理
        raise

# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")