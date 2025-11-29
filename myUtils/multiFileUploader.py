# -*- coding: utf-8 -*-
"""
通用多平台批量视频上传实现
"""
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union
from utils.log import get_logger

# 假设这些配置在项目中可用
BASE_DIR = Path(__file__).parent.parent
logger = get_logger("multi_uploader")

# 从单个视频上传器导入基础类
try:
    from uploader.baseVideoUploader import FacebookVideo, YouTubeVideo, TikTokVideo
except ImportError:
    # 如果导入失败，使用回退方案
    logger.warning("无法导入单个视频上传器，使用简化版本")


def generate_schedule_time_next_day(
    total_videos: int, 
    videos_per_day: int, 
    daily_times: Optional[List[str]] = None,
    start_days: int = 0
) -> List[int]:
    """
    生成定时发布时间表
    
    参数:
        total_videos: 总视频数量
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表（格式: "HH:MM"）
        start_days: 开始发布的天数偏移
    
    返回:
        发布时间戳列表
    """
    if not daily_times:
        # 默认发布时间：9:00, 12:00, 15:00, 18:00, 21:00
        daily_times = ["09:00", "12:00", "15:00", "18:00", "21:00"]
    
    # 计算需要多少天
    days_needed = (total_videos + videos_per_day - 1) // videos_per_day
    
    publish_times = []
    current_date = datetime.now() + timedelta(days=start_days)
    
    for day in range(days_needed):
        day_date = current_date + timedelta(days=day)
        
        # 当天的发布时间
        day_times = daily_times[:min(videos_per_day, total_videos - len(publish_times))]
        
        for time_str in day_times:
            try:
                # 解析时间
                hour, minute = map(int, time_str.split(':'))
                publish_datetime = day_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                publish_times.append(int(publish_datetime.timestamp()))
            except ValueError:
                logger.warning(f"时间格式错误: {time_str}，使用默认时间")
                publish_datetime = day_date.replace(hour=12, minute=0, second=0, microsecond=0)
                publish_times.append(int(publish_datetime.timestamp()))
    
    return publish_times


class MultiVideoUploader:
    """
    多视频上传管理器
    """
    
    def __init__(self, platform: str):
        """
        初始化多视频上传器
        
        参数:
            platform: 平台名称 (facebook, youtube, tiktok)
        """
        self.platform = platform.lower()
        self.logger = get_logger(f"multi_uploader_{platform}")
        
        # 平台上传器类映射
        self.uploader_classes = {
            "facebook": FacebookVideo,
            "youtube": YouTubeVideo,
            "tiktok": TikTokVideo
        }
        
        if self.platform not in self.uploader_classes:
            raise ValueError(f"不支持的平台: {platform}")
    
    async def upload_single_video(
        self,
        title: str,
        file_path: str,
        tags: str,
        publish_date: int,
        account_file: str,
        thumbnail_path: Optional[str] = None
    ) -> bool:
        """
        上传单个视频
        
        参数:
            title: 视频标题
            file_path: 视频文件路径
            tags: 视频标签
            publish_date: 发布时间戳
            account_file: 账号cookie文件
            thumbnail_path: 封面图片路径（可选）
            
        返回:
            上传是否成功
        """
        try:
            uploader_class = self.uploader_classes[self.platform]
            
            if thumbnail_path and os.path.exists(thumbnail_path):
                uploader = uploader_class(title, file_path, tags, publish_date, account_file, thumbnail_path)
            else:
                uploader = uploader_class(title, file_path, tags, publish_date, account_file)
            
            result = await uploader.main()
            return result
            
        except Exception as e:
            self.logger.error(f"视频上传失败: {str(e)}")
            return False
    
    def find_thumbnail(self, video_path: str) -> Optional[str]:
        """
        自动查找封面图片
        
        参数:
            video_path: 视频文件路径
            
        返回:
            封面图片路径，如果找不到返回None
        """
        video_file = Path(video_path)
        
        # 尝试查找与视频同名的png文件
        thumbnail_candidates = [
            video_file.with_suffix('.png'),
            video_file.with_suffix('.jpg'),
            video_file.with_suffix('.jpeg'),
            video_file.parent / (video_file.stem + '.png'),
            video_file.parent / (video_file.stem + '.jpg'),
            video_file.parent / (video_file.stem + '.jpeg'),
        ]
        
        for candidate in thumbnail_candidates:
            if candidate.exists():
                self.logger.info(f"找到自动封面图片: {candidate}")
                return str(candidate)
        
        return None
    
    async def upload_multiple_videos(
        self,
        title: str,
        video_files: List[str],
        tags: str,
        account_files: List[str],
        enable_timer: bool = False,
        videos_per_day: int = 1,
        daily_times: Optional[List[str]] = None,
        start_days: int = 0,
        thumbnail_path: Optional[str] = None
    ) -> dict:
        """
        批量上传多个视频
        
        参数:
            title: 视频标题（可为模板，使用{index}作为占位符）
            video_files: 视频文件路径列表
            tags: 视频标签
            account_files: 账号cookie文件列表
            enable_timer: 是否启用定时发布
            videos_per_day: 每天发布视频数量
            daily_times: 每天发布时间点列表
            start_days: 开始发布的天数偏移
            thumbnail_path: 封面图片路径（可选）
            
        返回:
            上传结果统计
        """
        results = {
            "total": len(video_files),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        # 生成发布时间
        if enable_timer:
            publish_times = generate_schedule_time_next_day(
                len(video_files), videos_per_day, daily_times, start_days
            )
        else:
            publish_times = [0] * len(video_files)
        
        # 处理文件路径
        processed_video_files = []
        for file in video_files:
            if not os.path.isabs(file):
                processed_file = BASE_DIR / "videoFile" / file
                processed_video_files.append(str(processed_file))
            else:
                processed_video_files.append(file)
        
        # 处理账号文件路径
        processed_account_files = []
        for account_file in account_files:
            if not os.path.isabs(account_file):
                processed_account = BASE_DIR / "cookiesFile" / account_file
                processed_account_files.append(str(processed_account))
            else:
                processed_account_files.append(account_file)
        
        # 处理封面图片路径
        processed_thumbnail_path = None
        if thumbnail_path:
            if not os.path.isabs(thumbnail_path):
                processed_thumbnail = BASE_DIR / "videoFile" / thumbnail_path
                if processed_thumbnail.exists():
                    processed_thumbnail_path = str(processed_thumbnail)
                else:
                    self.logger.warning(f"指定的封面文件不存在: {processed_thumbnail}")
            else:
                if os.path.exists(thumbnail_path):
                    processed_thumbnail_path = thumbnail_path
                else:
                    self.logger.warning(f"指定的封面文件不存在: {thumbnail_path}")
        
        # 遍历所有视频文件和账号
        for video_index, video_file in enumerate(processed_video_files):
            video_success = False
            
            for account_index, account_file in enumerate(processed_account_files):
                if not os.path.exists(video_file):
                    self.logger.error(f"视频文件不存在: {video_file}")
                    results["details"].append({
                        "video": video_file,
                        "account": account_file,
                        "status": "failed",
                        "reason": "视频文件不存在"
                    })
                    break
                
                if not os.path.exists(account_file):
                    self.logger.error(f"账号文件不存在: {account_file}")
                    results["details"].append({
                        "video": video_file,
                        "account": account_file,
                        "status": "failed", 
                        "reason": "账号文件不存在"
                    })
                    continue
                
                try:
                    # 处理标题模板
                    if "{index}" in title:
                        formatted_title = title.replace("{index}", str(video_index + 1))
                    else:
                        formatted_title = f"{title} {video_index + 1}"
                    
                    # 查找封面图片
                    final_thumbnail_path = processed_thumbnail_path
                    if not final_thumbnail_path:
                        final_thumbnail_path = self.find_thumbnail(video_file)
                    
                    # 打印发布信息
                    self.logger.info(f"开始上传视频 {video_index + 1}/{len(processed_video_files)}")
                    self.logger.info(f"视频文件: {video_file}")
                    self.logger.info(f"视频标题: {formatted_title}")
                    self.logger.info(f"视频标签: {tags}")
                    self.logger.info(f"使用账号: {account_file}")
                    if final_thumbnail_path:
                        self.logger.info(f"封面图片: {final_thumbnail_path}")
                    
                    if enable_timer:
                        publish_time_str = datetime.fromtimestamp(publish_times[video_index]).strftime("%Y-%m-%d %H:%M")
                        self.logger.info(f"定时发布时间: {publish_time_str}")
                    
                    # 执行上传
                    success = await self.upload_single_video(
                        title=formatted_title,
                        file_path=video_file,
                        tags=tags,
                        publish_date=publish_times[video_index],
                        account_file=account_file,
                        thumbnail_path=final_thumbnail_path
                    )
                    
                    if success:
                        self.logger.info(f"✅ 视频上传成功: {Path(video_file).name}")
                        results["success"] += 1
                        results["details"].append({
                            "video": video_file,
                            "account": account_file,
                            "status": "success"
                        })
                        video_success = True
                        break  # 这个视频上传成功，跳出账号循环
                    else:
                        self.logger.error(f"❌ 视频上传失败: {Path(video_file).name}")
                        results["details"].append({
                            "video": video_file,
                            "account": account_file,
                            "status": "failed",
                            "reason": "上传过程失败"
                        })
                        
                except Exception as e:
                    self.logger.error(f"❌ 视频上传异常: {str(e)}")
                    results["details"].append({
                        "video": video_file,
                        "account": account_file,
                        "status": "failed",
                        "reason": f"异常: {str(e)}"
                    })
            
            if not video_success:
                results["failed"] += 1
        
        # 输出总结
        self.logger.info(f"批量上传完成: 成功 {results['success']}/{results['total']}, 失败 {results['failed']}")
        return results


# 特定平台的便捷函数
async def post_videos_to_platform(
    platform: str,
    title: str,
    video_files: List[str],
    tags: str,
    account_files: List[str],
    enable_timer: bool = False,
    videos_per_day: int = 1,
    daily_times: Optional[List[str]] = None,
    start_days: int = 0,
    thumbnail_path: Optional[str] = None
) -> dict:
    """
    发布视频到指定平台（异步版本）
    
    参数:
        platform: 平台名称 (facebook, youtube, tiktok)
        title: 视频标题
        video_files: 视频文件列表
        tags: 视频标签
        account_files: 账号cookie文件列表
        enable_timer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表
        start_days: 开始发布的天数偏移
        thumbnail_path: 封面图片路径（可选）
        
    返回:
        上传结果统计
    """
    uploader = MultiVideoUploader(platform)
    return await uploader.upload_multiple_videos(
        title=title,
        video_files=video_files,
        tags=tags,
        account_files=account_files,
        enable_timer=enable_timer,
        videos_per_day=videos_per_day,
        daily_times=daily_times,
        start_days=start_days,
        thumbnail_path=thumbnail_path
    )


def post_videos_to_platform_sync(
    platform: str,
    title: str,
    video_files: List[str],
    tags: str,
    account_files: List[str],
    enable_timer: bool = False,
    videos_per_day: int = 1,
    daily_times: Optional[List[str]] = None,
    start_days: int = 0,
    thumbnail_path: Optional[str] = None
) -> dict:
    """
    发布视频到指定平台（同步版本）
    
    参数:
        platform: 平台名称 (facebook, youtube, tiktok)
        title: 视频标题
        video_files: 视频文件列表
        tags: 视频标签
        account_files: 账号cookie文件列表
        enable_timer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间点列表
        start_days: 开始发布的天数偏移
        thumbnail_path: 封面图片路径（可选）
        
    返回:
        上传结果统计
    """
    return asyncio.run(
        post_videos_to_platform(
            platform=platform,
            title=title,
            video_files=video_files,
            tags=tags,
            account_files=account_files,
            enable_timer=enable_timer,
            videos_per_day=videos_per_day,
            daily_times=daily_times,
            start_days=start_days,
            thumbnail_path=thumbnail_path
        )
    )


# 特定平台的便捷函数（保持与原有接口兼容）
async def post_videos_to_facebook(
    title: str,
    video_files: List[str],
    tags: str,
    account_files: List[str],
    enable_timer: bool = False,
    videos_per_day: int = 1,
    daily_times: Optional[List[str]] = None,
    start_days: int = 0,
    thumbnail_path: Optional[str] = None
) -> dict:
    """发布视频到Facebook平台（异步版本）"""
    return await post_videos_to_platform(
        platform="facebook",
        title=title,
        video_files=video_files,
        tags=tags,
        account_files=account_files,
        enable_timer=enable_timer,
        videos_per_day=videos_per_day,
        daily_times=daily_times,
        start_days=start_days,
        thumbnail_path=thumbnail_path
    )


def post_videos_to_facebook_sync(
    title: str,
    video_files: List[str],
    tags: str,
    account_files: List[str],
    enable_timer: bool = False,
    videos_per_day: int = 1,
    daily_times: Optional[List[str]] = None,
    start_days: int = 0,
    thumbnail_path: Optional[str] = None
) -> dict:
    """发布视频到Facebook平台（同步版本）"""
    return post_videos_to_platform_sync(
        platform="facebook",
        title=title,
        video_files=video_files,
        tags=tags,
        account_files=account_files,
        enable_timer=enable_timer,
        videos_per_day=videos_per_day,
        daily_times=daily_times,
        start_days=start_days,
        thumbnail_path=thumbnail_path
    )


# 其他平台的类似函数可以根据需要添加...

if __name__ == "__main__":
    # 示例用法
    result = post_videos_to_facebook_sync(
        title="测试视频 {index}",
        video_files=["video1.mp4", "video2.mp4"],
        tags="测试 标签",
        account_files=["fb_cookie1.json", "fb_cookie2.json"],
        enable_timer=True,
        videos_per_day=2,
        daily_times=["09:00", "15:00"],
        start_days=1,
        thumbnail_path="thumbnail.png"
    )
    
    print(f"上传结果: {result}")