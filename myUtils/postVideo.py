import asyncio
import os
import logging
from datetime import datetime
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinVideo
from uploader.ks_uploader.main import KSVideo
from uploader.tk_uploader.main_chrome import tiktok_setup, TiktokVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags

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

def post_video_xhs(title,files,tags,account_file,category=TencentZoneTypes.LIFESTYLE.value,enableTimer=False,videos_per_day = 1, daily_times=None,start_days = 0):
    # 生成文件的完整路径
    account_file = [Path(BASE_DIR / "cookiesFile" / file) for file in account_file]
    files = [Path(BASE_DIR / "videoFile" / file) for file in files]
    file_num = len(files)
    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(file_num, videos_per_day, daily_times,start_days)
    else:
        publish_datetimes = 0
    for index, file in enumerate(files):
        for cookie in account_file:
            # 打印视频文件名、标题和 hashtag
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = XiaoHongShuVideo(title, file, tags, publish_datetimes, cookie)
            asyncio.run(app.main(), debug=False)



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
                # 打印发布信息
                logger.info(f"文件路径: {str(file)}")
                logger.info(f"视频文件名: {file.name}")
                logger.info(f"标题: {title}")
                logger.info(f"标签: {tags}")
                
                # 检查cookie文件是否存在
                if not cookie.exists():
                    logger.error(f"TikTok账号cookie文件不存在: {str(cookie)}")
                    continue
                
                # 初始化cookie设置
                try:
                    cookie_setup = asyncio.run(tiktok_setup(cookie, handle=True))
                    
                    # 使用与参考示例相同的方式处理标题和标签
                    # 如果没有提供标题和标签，则从文件名获取
                    if not title or not tags:
                        try:
                            file_title, file_tags = get_title_and_hashtags(str(file))
                            if not title:
                                title = file_title
                            if not tags:
                                tags = file_tags
                        except Exception as e:
                            logger.warning(f"无法从文件获取标题和标签: {str(e)}")
                            # 如果获取失败，使用默认值
                            if not title:
                                title = file.name.replace('.mp4', '').replace('_', ' ')
                            if not tags:
                                tags = []
                    
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

# post_video("333",["demo.mp4"],"d","d")
# post_video_DouYin("333",["demo.mp4"],"d","d")