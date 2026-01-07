# 平台配置字典
PLATFORM_CONFIGS = {
    "xiaohongshu": {
        #平台类型编号
        "type": 1,
        #平台名称
        "platform_name": "xhs",
        #平台个人中心URL
        "personal_url": "https://creator.xiaohongshu.com/new/home",
        #平台登录URL
        "login_url": "https://creator.xiaohongshu.com/login",
        #平台视频发布URL
        "creator_video_url": "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video&openFilePicker=true",
        #平台图片发布URL
        "creator_image_url": "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&openFilePicker=true",
        "selectors": {
            #上传按钮选择器
            "upload_button": ['input.upload-input[type="file"]'],
            #发布按钮选择器
            "publish_button": ['div.d-button-content span.d-text:has-text("发布")'],
            #标题编辑器选择器
            "title_editor": [
                '[contenteditable="true"][role="textbox"][data-lexical-editor="true"]',
                '[aria-placeholder*="分享你的新鲜事"][contenteditable="true"]',
                '[aria-label="Add a description"]',
                '[aria-label="Write something..."]'
            ],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
            ],
            #封面按钮选择器
            "thumbnail_button": ["//span[contains(text(), 'Add')]", "//span[contains(text(), '添加')]"],
            #定时按钮选择器
            "schedule_button": ["//span[text()='Schedule']", "//span[text()='定时']"],
            #日期输入选择器
            "date_input": '[aria-label="Date"]',
            #时间输入选择器
            "time_input": '[aria-label="Time"]',
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "tencent": {
        "type": 2,
        "platform_name": "tc",
        "personal_url": "https://channels.weixin.qq.com/platform/",
        "login_url": "https://channels.weixin.qq.com/login.html",
        "creator_video_url": "https://channels.weixin.qq.com/platform/post/create",
        "creator_image_url": "https://channels.weixin.qq.com/platform/post/finderNewLifeCreate",
        "selectors": {
            "upload_button": ['span.add-icon.weui-icon-outlined-add', 'div.upload-content'],
            "publish_button": ['button.weui-desktop-btn.weui-desktop-btn_primary:has-text("发表")', 'button.weui-desktop-btn:has-text("发表")'],
            "title_editor": ['input.weui-desktop-form__input[placeholder="概括视频主要内容，字数建议6-16个字符"]'],
            "textbox_selectors": [
                'div.input-editor[contenteditable=""][data-placeholder="添加描述"]'
            ],
            "thumbnail_button": ["//span[contains(text(), '添加封面')]"],
            "schedule_button": ['label:has-text("定时")'],
            "date_input": ['input[placeholder="请选择发表时间"]'],
            "time_input": ['input[placeholder="请选择时间"]'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "douyin": {
        "type": 3,
        "platform_name": "dy",
        "personal_url": "https://creator.douyin.com/creator-micro/home",
        "login_url": "https://creator.douyin.com/login",
        "creator_video_url": "https://creator.douyin.com/creator-micro/content/upload",
        "creator_image_url": "https://creator.douyin.com/creator-micro/content/upload?default-tab=3",
        "selectors": {
            "upload_button": ['span.semi-button-content-right:has-text("上传视频")', 'span.semi-button-content-right:has-text("上传图文")'],
            "publish_button": ['role=button[name="发布"]', 'button:has-text("发布"):not(:has-text("高清发布"))', 'text="发布"'],
            "title_editor": ['input[placeholder="填写作品标题，为作品获得更多流量"]', 'input.semi-input.semi-input-default'],
            "textbox_selectors": ['div[data-line-wrapper="true"]', 'div.zone-container.editor-kit-container.editor.editor-comp-publish[contenteditable="true"]'],
            "thumbnail_button": ["//span[contains(text(), '添加封面')]"],
            "schedule_button": ['button:has-text("定时发布")'],
            "date_input": ['.el-input__inner[placeholder="选择日期和时间"]'],
            "time_input": ['.el-input__inner[placeholder="选择日期和时间"]'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "kuaishou": {
        "type": 4,
        "platform_name": "ks",
        "personal_url": "https://cp.kuaishou.com/profile",
        "login_url": "https://passport.kuaishou.com/pc/account/login",
        "creator_video_url": "https://cp.kuaishou.com/article/publish/video?tabType=1",
        "creator_image_url": "https://cp.kuaishou.com/article/publish/video?tabType=2",
        "selectors": {
            "upload_button": ['button:has-text("上传图片")', 'button:has-text("上传视频")'],
            "publish_button": ['div._button_3a3lq_1._button-primary_3a3lq_60:has-text("发布")', 'div:has-text("发布")', 'text="发布"'],
            #标题编辑器选择器
            "title_editor": ['div:has-text("描述") + div'],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div:has-text("描述") + div',
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]',
                'div#work-description-edit[contenteditable="true"]',
                '[contenteditable="true"][placeholder*="添加合适的话题和描述"]',
                '[contenteditable="true"][id*="description"][class*="description"]'
            ],
            "thumbnail_button": ["//span[contains(text(), '封面编辑')]"],
            "schedule_button": ['label:text("发布时间") + div .ant-radio-input'],
            "date_input": ['div.ant-picker-input input[placeholder="选择日期时间"]'],
            "time_input": ['div.ant-picker-input input[placeholder="选择日期时间"]'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": False,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "tiktok": {
        "type": 5,
        "platform_name": "tk",
        "personal_url": "https://www.tiktok.com/",
        "login_url": "https://www.tiktok.com/login?lang=en",
        "creator_video_url": "https://www.tiktok.com/tiktokstudio/upload?lang=en",
        "creator_image_url": "https://www.tiktok.com/tiktokstudio/upload?lang=en",
        "selectors": {
            "upload_button": ['button:has-text("Select video"):visible'],
            "publish_button": ['button[data-e2e="post_video_button"]', 'button:has-text("Post")', 'role=button[name="Post"]'],
            "title_editor": ['div.public-DraftEditor-content'],
            "textbox_selectors": [
                'div.public-DraftEditor-content[contenteditable="true"]',
                'div.caption-editor'
            ],
            "thumbnail_button": [".cover-container"],
            "schedule_button": ["//span[text()='Schedule']", "//span[text()='定时']"],
            "date_input": '[aria-label="Date"]',
            "time_input": '[aria-label="Time"]',
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": False,
            #是否支持标题
            "title": False,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "instagram": {
        "type": 6,
        "platform_name": "ig",
        "personal_url": "https://www.instagram.com/me/",
        "login_url": "https://www.instagram.com/accounts/login/",
        "creator_video_url": "https://business.facebook.com/latest/composer",
        "creator_image_url": "https://business.facebook.com/latest/composer",
        "selectors": {
            "upload_button": ['div[role="button"]:has-text("Add photo/video")'],
            "publish_button": ['*[role="button"]:has(:text("Publish"))'],
            "title_editor": ['div[role="combobox"][contenteditable="true"][aria-label*="Write into the dialogue box"]'],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
            ],
            "thumbnail_button": ["//span[contains(text(), '选择封面')]"],
            "schedule_button": ['#video_upload > div > div:nth-child(2) > div > div.time > div > div > div:nth-child(2) > label'],
            "date_input": ['#video_upload > div > div:nth-child(2) > div > div.time > div > div > div:nth-child(2) > div > input'],
            "time_input": ['#video_upload > div > div:nth-child(2) > div > div.time > div > div > div:nth-child(2) > div > input'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    #facebook
    "facebook": {
        "type": 7,
        "platform_name": "fb",
        "personal_url": "https://www.facebook.com/profile.php",
        "login_url": "https://www.facebook.com/login",
        "creator_video_url": "https://www.facebook.com/",
        "creator_image_url": "https://www.facebook.com/",
        "selectors": {
            "upload_button": ['div[aria-label="照片/视频"]','div[aria-label="Photo/Video"]'],
            "publish_button": ['//span[text()="发帖"]','//span[text()="Post"]','//span[text()="Schedule"]','//span[text()="发布"]'],
            #标题编辑器选择器
            "title_editor": [          
                # 中文界面选择器
                '[contenteditable="true"][role="textbox"][data-lexical-editor="true"]',
                '[aria-placeholder*="分享你的新鲜事"][contenteditable="true"]',
                # 英文界面选择器
                '[aria-label="Add a description"]',
                '[aria-label="Write something..."]'],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
            ],
            "thumbnail_button": ["//span[contains(text(), 'Add')]","//span[contains(text(), '添加')]"],
            "schedule_button": ["//span[text()='Schedule']","//span[text()='定时']"],
            "date_input": ['.date-picker-input'],
            "time_input": ['.time-picker-input'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": False,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    "bilibili": {
        "type": 8,
        "platform_name": "bl",
        "personal_url": "https://member.bilibili.com/v2#/home",
        "login_url": "https://passport.bilibili.com/login",
        "creator_video_url": "https://member.bilibili.com/v2#/upload/manual",
        "creator_image_url": "https://member.bilibili.com/v2#/upload/manual",
        "selectors": {
            "upload_button": ['input[type="file"]'],
            "publish_button": ['button:has-text("发布")'],
            #标题编辑器选择器
            "title_editor": ['#title'],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
            ],
            "thumbnail_button": ["//span[contains(text(), '添加封面')]"],
            "schedule_button": ['button:has-text("定时发布")'],
            "date_input": ['.date-picker-input'],
            "time_input": ['.time-picker-input'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    },
    #baijiahao
    "baijiahao": {
        "type": 9,
        "platform_name": "bjh",
        "personal_url": "https://baijiahao.baidu.com/builder/rc/list",
        "login_url": "https://baijiahao.baidu.com/builder/rc/login",
        "creator_video_url": "https://baijiahao.baidu.com/builder/rc/edit",
        "creator_image_url": "https://baijiahao.baidu.com/builder/rc/edit",
        "selectors": {
            "upload_button": ['input[type="file"]'],
            "publish_button": ['button:has-text("发布")'],
            #标题编辑器选择器
            "title_editor": ['#user_message'],
            #正文编辑器输入框选择器
            "textbox_selectors": [
                'div.tiptap.ProseMirror[contenteditable="true"][role="textbox"]'
            ],
            "thumbnail_button": ["//span[contains(text(), '添加封面')]"],
            "schedule_button": ['button:has-text("定时发布")'],
            "date_input": ['.date-picker-input'],
            "time_input": ['.time-picker-input'],
        },
        "features": {
            # 平台功能支持
            #是否跳过Cookie验证
            "skip_cookie_verify": True,
            #是否支持图文发布
            "image_publish": True,
            #是否支持标题
            "title": True,
            #是否支持正文
            "textbox": True,
            #是否支持标签
            "tags": True,
            #是否支持封面
            "thumbnail": False,
            #是否支持地点
            "location": False,
            #是否支持定时发布
            "schedule": False
        }
    }
}

# 导出配置以便其他模块导入
__all__ = ['PLATFORM_CONFIGS']