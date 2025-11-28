import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, send_from_directory
from conf import BASE_DIR
from myUtils.login import douyin_cookie_gen, get_tencent_cookie, get_ks_cookie, xiaohongshu_cookie_gen, get_tiktok_cookie, get_instagram_cookie, get_facebook_cookie
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs, post_video_TikTok, post_video_Instagram, post_video_Facebook

active_queues = {}
app = Flask(__name__)

#允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{file.filename}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code":200,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return {"error": "filename is required"}, 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400

    # 拼接完整路径
    file_path = str(Path(BASE_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{filename}")

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            print("\n📋 当前数据表内容（快速获取）：")
            for row in rows_list:
                print(row)

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    platform_type = request.args.get('type', type=int, default=0)
    
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        if platform_type == 0:
            cursor.execute("SELECT * FROM user_info")
        else:
            cursor.execute("SELECT * FROM user_info WHERE type = ?", (platform_type,))
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)
        # 定义并发限制数量
        CONCURRENCY_LIMIT = 10  # 可以根据系统资源调整
        
        # 使用并发方式验证cookie
        async def check_and_update_cookie(row):
            flag = await check_cookie(row[1], row[2])
            if not flag:
                row[4] = 0
                # 注意：这里不执行数据库更新，而是返回需要更新的行ID
                return row[0]
            return None
        
        # 分批处理以控制并发数量
        def chunked_list(lst, chunk_size):
            for i in range(0, len(lst), chunk_size):
                yield lst[i:i + chunk_size]
        
        print(f"\n🔄 开始并发验证账号状态（并发数: {CONCURRENCY_LIMIT}）...")
        
        # 记录需要更新的账号ID
        ids_to_update = []
        
        # 分批处理所有账号
        for batch in chunked_list(rows_list, CONCURRENCY_LIMIT):
            # 为当前批次中的每个账号创建验证任务
            tasks = [check_and_update_cookie(row) for row in batch]
            # 并发执行当前批次的所有任务
            results = await asyncio.gather(*tasks)
            # 收集需要更新的账号ID
            for account_id in results:
                if account_id is not None:
                    ids_to_update.append(account_id)
        
        # 批量更新数据库，减少数据库操作次数
        if ids_to_update:
            # 使用批量更新语句
            placeholders = ','.join(['?' for _ in ids_to_update])
            cursor.execute(f'''
            UPDATE user_info 
            SET status = 0 
            WHERE id IN ({placeholders})
            ''', ids_to_update)
            conn.commit()
            print(f"✅ 已批量更新 {len(ids_to_update)} 个失效账号的状态")
        else:
            print("✅ 所有账号状态均有效，无需更新")
        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(BASE_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = int(request.args.get('id'))

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

# 统计数据API：获取平台账号统计
@app.route('/getPlatformStats', methods=['GET'])
def get_platform_stats():
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取各平台账号数量统计
            cursor.execute('''
                SELECT type, COUNT(*) as count, SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as valid_count
                FROM user_info
                GROUP BY type
            ''')
            platform_stats = []
            for row in cursor.fetchall():
                platform_stats.append({
                    "platform": row['type'],
                    "total": row['count'],
                    "valid": row['valid_count']
                })
            
            # 获取总体统计
            cursor.execute('''
                SELECT COUNT(*) as total_accounts, 
                       SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as valid_accounts,
                       (SELECT COUNT(*) FROM file_records) as total_files
                FROM user_info
            ''')
            overall_stats = cursor.fetchone()
            
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": {
                    "platform_stats": platform_stats,
                    "overall": {
                        "total_accounts": overall_stats['total_accounts'],
                        "valid_accounts": overall_stats['valid_accounts'],
                        "total_files": overall_stats['total_files']
                    }
                }
            }), 200
    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取统计数据失败: {str(e)}",
            "data": None
        }), 500

# 统计数据API：获取文件统计
@app.route('/getFileStats', methods=['GET'])
def get_file_stats():
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取文件大小统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_files,
                    SUM(filesize) as total_size,
                    AVG(filesize) as avg_size,
                    MAX(filesize) as max_size
                FROM file_records
            ''')
            size_stats = cursor.fetchone()
            
            # 获取最近上传的文件
            cursor.execute('''
                SELECT * FROM file_records
                ORDER BY id DESC
                LIMIT 10
            ''')
            recent_files = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": {
                    "size_stats": {
                        "total_files": size_stats['total_files'],
                        "total_size_mb": round(float(size_stats['total_size']), 2),
                        "avg_size_mb": round(float(size_stats['avg_size']), 2),
                        "max_size_mb": round(float(size_stats['max_size']), 2)
                    },
                    "recent_files": recent_files
                }
            }), 200
    except Exception as e:
        print(f"获取文件统计数据失败: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取文件统计数据失败: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    """
    参数说明：
    type: 发布平台类型，1-小红书 2-视频号 3-抖音 4-快手
    accountList: 账号列表，每个元素为一个字典，包含账号信息
    fileType: 文件类型，默认值为2：1-图文 2-视频
    title: 文件标题
    text: 文件正文描述
    tags: 文件标签，逗号分隔
    category: 文件分类，0-无分类 1-美食 2-日常 3-旅行 4-娱乐 5-教育 6-其他
    enableTimer: 是否启用定时发布，0-否 1-是
    videosPerDay: 每天发布文件数量
    dailyTimes: 每天发布时间，逗号分隔，格式为HH:MM
    startDays: 开始发布时间，距离当前时间的天数，负数表示之前的时间

    """
    # 获取JSON数据的POST请求体
    data = request.get_json()
    type = data.get('type') #发布平台类型，1-小红书 2-视频号 3-抖音 4-快手 5-tiktok 6-instagram 7-facebook
    account_list = data.get('accountList', []) #账号列表，每个元素为一个字典，包含账号信息
    file_type = data.get('fileType')  #文件类型，默认值为2：1-图文 2-视频
    file_list = data.get('fileList', []) #文件列表，每个元素为一个字典，包含文件路径和文件名
    title = data.get('title') #文件标题
    text = data.get('text') #文件正文描述，默认值为demo
    tags = data.get('tags') #文件标签，逗号分隔
    category = data.get('category') #文件分类，0-无分类 1-美食 2-日常 3-旅行 4-娱乐 5-教育 6-其他
    if category == 0:
        category = None
    thumbnail_path = data.get('thumbnail', '') #视频缩略图封面路径
    productLink = data.get('productLink', '') #商品链接
    productTitle = data.get('productTitle', '') #商品标题
    is_draft = data.get('isDraft', False)  # 是否保存为草稿
    enableTimer = data.get('enableTimer') #是否启用定时发布，0-否 1-是
    videos_per_day = data.get('videosPerDay') #每天发布文件数量
    daily_times = data.get('dailyTimes') #每天发布时间，逗号分隔，格式为HH:MM
    start_days = data.get('startDays') #开始发布时间，距离当前时间的天数，负数表示之前的时间
    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)
    match type:
        case 1:
            post_video_xhs(account_list, file_type, file_list, title, text, tags, enableTimer, videos_per_day, daily_times,
                               start_days)
        case 2:
            post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days, is_draft)
        case 3:
            post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, thumbnail_path, productLink, productTitle)
        case 4:
            post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days)
        case 5:
            post_video_TikTok(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, thumbnail_path)
        case 6:
            post_video_Instagram(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, thumbnail_path)
        case 7:
            post_video_Facebook(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, thumbnail_path)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        match type:
            case 1:
                return
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, productLink, productTitle)
            case 4:
                print(f'[+] Batch publishing to KuaiShou')
                # KuaiShou
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case 5:
                print(f'[+] Batch publishing to TikTok')
                # TikTok
                post_video_TikTok(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 6:
                print(f'[+] Batch publishing to Instagram')
                # Instagram
                post_video_Instagram(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
            case 7:
                print(f'[+] Batch publishing to Facebook')
                # Facebook
                post_video_Facebook(title, file_list, tags, account_list, enableTimer, videos_per_day, daily_times, start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 500,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 500,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 500,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 500,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue):
    match type:
        case '1':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            loop.close()
        case '2':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tencent_cookie(id,status_queue))
            loop.close()
        case '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(douyin_cookie_gen(id,status_queue))
            loop.close()
        case '4':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_ks_cookie(id,status_queue))
            loop.close()
        case '5':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tiktok_cookie(id,status_queue))
            loop.close()
        case '6':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_instagram_cookie(id,status_queue))
            loop.close()
        case '7':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_facebook_cookie(id,status_queue))
            loop.close()

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=5409)
