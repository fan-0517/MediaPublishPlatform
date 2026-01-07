# 自媒体智能运营系统

## 项目地址

[GitHub 仓库](https://github.com/fan-0517/SAU.git)

## 项目介绍

SAU 是一个功能强大的自媒体智能运营系统，支持图文和视频内容的批量上传与定时发布。

### 后端架构

后端采用模块化设计，基于 Flask 框架构建 RESTful API 服务，结合 Playwright 实现浏览器自动化上传，核心组件包括：

1. **核心上传引擎** (`myUtils/baseFileUploader.py`)
   - 通用多平台上传器基类，定义了统一的上传接口和流程
   - 支持多平台配置（小红书、腾讯、抖音、快手、TikTok、Instagram 等）
   - 使用 Playwright 实现浏览器自动化操作
   - 支持图文和视频两种内容类型
   - 提供定时发布、标签管理等核心功能

2. **多文件上传处理** (`myUtils/multiFileUploader.py`)
   - 批量文件处理，支持多账号轮换
   - 自动生成发布计划时间
   - 异步执行上传任务
   - 提供完整的发布结果反馈

3. **Flask 后端服务** (`sau_backend.py`)
   - RESTful API 接口设计
   - 文件上传、保存和查询功能
   - 支持跨域请求
   - 数据库集成，记录文件上传历史
   - 提供用户认证和权限管理

4. **平台特定实现** (`uploader/xiaohongshu_uploader/xhsVideoUploader.py`)
   - 针对小红书平台的特定上传逻辑
   - 继承自通用上传器，实现平台特有功能
   - 支持小红书创作者平台的各种发布选项

### 技术栈

- **Web 框架**: Flask
- **浏览器自动化**: Playwright
- **数据库**: SQLite
- **异步处理**: asyncio
- **文件管理**: pathlib
- **日志管理**: 自定义日志模块

### 核心功能

1. **多平台支持**
   - 小红书、腾讯视频号、抖音、快手、TikTok、Instagram 等主流平台
   - 统一的上传接口，便于扩展新平台

2. **内容类型支持**
   - 支持视频文件上传
   - 支持图文内容发布
   - 支持封面设置（部分平台）

3. **发布功能**
   - 即时发布
   - 定时发布，支持自定义发布时间
   - 批量发布，支持多账号轮换

4. **管理功能**
   - 文件上传和管理
   - 发布历史记录
   - 账号管理

### 工作流程

1. 前端上传文件到后端服务器
2. 后端保存文件并记录到数据库
3. 调用上传引擎执行发布任务
4. Playwright 启动浏览器，加载平台发布页面
5. 自动填充标题、正文、标签等信息
6. 执行发布操作，等待发布完成
7. 返回发布结果，更新数据库记录

## 安装指南

## 安装指南

1.  **克隆项目**:
    ```bash
    git clone https://github.com/fan-0517/SAU.git
    cd social-auto-upload
    ```

2.  **安装依赖**:
    建议在虚拟环境中安装依赖。
    ```bash
    conda create -n social-auto-upload python=3.10
    conda activate social-auto-upload
    # 挂载清华镜像 or 命令行代理
    pip install -r requirements.txt
    ```

3.  **安装 Playwright 浏览器驱动**:
    ```bash
    playwright install chromium firefox
    ```
    根据您的需求，至少需要安装 `chromium`。`firefox` 主要用于 TikTok 上传（旧版）。

4.  **修改配置文件**:
    复制 `conf.example.py` 并重命名为 `conf.py`。
    在 `conf.py` 中，您需要配置以下内容：
    -   `LOCAL_CHROME_PATH`: 本地 Chrome 浏览器的路径，比如 `C:\Program Files\Google\Chrome\Application\chrome.exe` 保存。
    
    **临时解决方案**

    需要在根目录创建 `cookiesFile` 和 `videoFile` 两个文件夹，分别是 存储cookie文件 和 存储上传文件 的文件夹

5.  **配置数据库**:
    如果 db/database.db 文件不存在，您可以运行以下命令来初始化数据库：
    ```bash
    cd db
    python createTable.py
    ```
    此命令将初始化 SQLite 数据库。

6.  **启动后端项目**:
    ```bash
    python sau_backend.py
    ```
    后端项目将在 `http://localhost:5409` 启动。

7.  **启动前端项目**:
    ```bash
    cd sau_frontend ; npm install ;npm run dev
    ```
    前端项目将在 `http://localhost:5173` 启动，在浏览器中打开此链接即可访问。

## 快速开始

1. 上传要发布的文件
2. 选择发布平台和账号
3. 填写标题、正文和标签
4. 设置发布时间（可选）
5. 点击发布按钮，系统将自动执行发布任务

## Docker 部署

```bash
docker build -t social-auto-upload .
docker run -p 5000:5000 social-auto-upload
```

## 支持的平台

- ✅ 小红书
- ✅ 腾讯视频号
- ✅ 抖音
- ✅ 快手
- ✅ TikTok
- ✅ Instagram

## 许可证

MIT License
