import asyncio
from pathlib import Path
from conf import BASE_DIR
from myUtils.baseFileUploader import BaseFileUploader
from utils.files_times import generate_schedule_time_next_day

def post_file(platform, account_file, file_type, files, title, text,tags,enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """
    发布文件到各种平台
    参数:
        platform: 平台名称
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
                    app = BaseFileUploader(platform, cookie, file_type, file, title, text, tags, publish_datetimes)
                    asyncio.run(app.main(), debug=False)
                    #是否成功发布
                    if app.publish_success:
                        app.logger.info(f"{platform}文件{file.name}发布成功")
                    else:
                        app.logger.error(f"{platform}文件{file.name}发布失败")
                    #任务进度
                    app.logger.info(f"{platform}已发布{index+1}/{file_num}个文件")
                    #全部发布完毕后
                    if index+1 == file_num:
                        app.logger.info(f"{platform}所有文件发布完成")
                except Exception as e:
                    app.logger.error(f"{platform}文件{file.name}发布失败: {str(e)}")
                    # 继续尝试其他账号或文件，不中断整个流程
    except Exception as e:
        app.logger.error(f"{platform}文件{file.name}发布过程中发生异常: {str(e)}")
        raise