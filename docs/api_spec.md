# 自媒体多账号矩阵分发平台 (matrix-hub) 接口设计规范 (API Spec)

系统后端采用 **FastAPI** 构建，接口遵循 RESTful 设计规范，同时提供 **WebSocket** 实现多端实时日志、二维码流推送与人机协同交互。

---

## 1. 基础约定

- **接口前缀**：`/api`
- **数据交互格式**：JSON (`Content-Type: application/json; charset=utf-8`)
- **统一响应结构**：
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```
- 错误时 `code` != 0，`message` 携带人类友好的错误提示。

---

## 2. 账号管理接口 (`/api/accounts`)

### 2.1 获取账号列表
- **路径**：`GET /api/accounts`
- **参数**：
  - `platform` (可选，字符串): 平台过滤 (`xiaohongshu`, `douyin`, `kuaishou`, `channels`)
  - `group_name` (可选，字符串): 分组过滤
  - `status` (可选，字符串): 状态过滤 (`active`, `expired`, `unauthorized`)
- **返回**：`Account` 列表数据

### 2.2 发起扫码登录
- **路径**：`POST /api/accounts/login/start`
- **请求体**：
```json
{
  "platform": "xiaohongshu",
  "group_name": "默认分组",
  "proxy_url": ""
}
```
- **返回**：
```json
{
  "code": 0,
  "data": {
    "account_id": "uuid-xxx",
    "qrcode_base64": "data:image/png;base64,iVBORw0KG...",
    "timeout_seconds": 180
  }
}
```

### 2.3 检查账号登录态与健康度
- **路径**：`GET /api/accounts/{account_id}/check`
- **返回**：当前账号状态（`active` / `expired`）及最新的创作者昵称、头像。

### 2.4 唤起本地窗口人工辅助 (解决滑块/短信)
- **路径**：`POST /api/accounts/{account_id}/assist`
- **说明**：在宿主机桌面唤起当前账号的可见 Chrome 窗口，由人工完成验证后关闭并返回。
- **返回**：`{ "code": 0, "message": "桌面辅助窗口已唤起" }`

### 2.5 更新账号信息 / 删除账号
- **路径**：`PATCH /api/accounts/{account_id}` (修改分组名称、代理等)
- **路径**：`DELETE /api/accounts/{account_id}` (删除账号及其本地 session 文件)

---

## 3. 发布任务接口 (`/api/tasks`)

### 3.1 创建发布任务 (支持 1:N 与 M:N 模式)
- **路径**：`POST /api/tasks`
- **请求体**：
```json
{
  "name": "20260904 矩阵宣发任务",
  "task_type": "one_to_many", // "one_to_many" 或 "many_to_many"
  "master_config": {
    "title": "自媒体必备神器！多账号矩阵分发指南",
    "description": "今天给大家分享一款超实用的多账号一键分发工具，支持定时与多平台管理！#自媒体运营 #干货分享",
    "tags": ["自媒体运营", "干货分享", "工具推荐"],
    "schedule_mode": "platform_native", // "immediate" | "platform_native" | "local_staggered"
    "scheduled_at": "2026-09-05T10:00:00"
  },
  "items": [
    {
      "account_id": "uuid-account-1",
      "video_path": "D:/videos/ep01.mp4",
      "cover_path": "D:/videos/ep01_cover.jpg",
      // 差异化覆盖 (可选，若不传则沿用 master_config)
      "title_override": "小红书独家爆款！多账号管理技巧",
      "tags_override": ["小红书运营", "效率工具"]
    },
    {
      "account_id": "uuid-account-2",
      "video_path": "D:/videos/ep01.mp4",
      "cover_path": null
    }
  ]
}
```

### 3.2 获取任务列表与详情
- **路径**：`GET /api/tasks` (主任务分页列表)
- **路径**：`GET /api/tasks/{task_id}` (获取主任务详情及所有子任务进度)

### 3.3 任务控制
- **路径**：`POST /api/tasks/{task_id}/retry` (重试失败的子任务)
- **路径**：`POST /api/tasks/{task_id}/cancel` (取消尚未开始的排队任务)

---

## 4. 视频文件辅助接口 (`/api/videos`)

### 4.1 扫描本地目录
- **路径**：`POST /api/videos/scan-folder`
- **请求体**：`{ "folder_path": "D:/my_videos" }`
- **返回**：符合条件的视频文件列表（文件名、大小、格式、修改时间等），方便前端一键选择与自动配对。

### 4.2 校验视频文件有效性
- **路径**：`POST /api/videos/verify`
- **请求体**：`{ "video_path": "D:/my_videos/sample.mp4" }`
- **返回**：文件是否存在、可读性及基本文件元信息。

---

## 5. 系统设置与通知接口 (`/api/settings`)

### 5.1 查询 / 更新配置
- **路径**：`GET /api/settings`
- **路径**：`PUT /api/settings` (更新错峰参数、并发数、Webhook 地址等)

### 5.2 测试 Webhook 连通性
- **路径**：`POST /api/settings/test-webhook`
- **请求体**：`{ "webhook_url": "https://...", "channel": "feishu" }`
- **返回**：发送一条测试卡片，验证网络连通性与密钥正确性。

---

## 6. WebSocket 实时双向通道 (`/ws`)

前端建立单一长连接，支持按任务或账号订阅实时事件：

### 消息格式示例：
```json
{
  "event": "log_append",
  "data": {
    "task_id": "uuid-task-xxx",
    "account_name": "我的小红书大号",
    "level": "INFO",
    "message": "正在上传视频素材 (78%)...",
    "timestamp": "2026-09-04T16:30:00"
  }
}
```
```json
{
  "event": "qrcode_updated",
  "data": {
    "account_id": "uuid-account-xxx",
    "qrcode_base64": "data:image/png;base64,..."
  }
}
```
```json
{
  "event": "assist_required",
  "data": {
    "account_id": "uuid-account-xxx",
    "reason": "检测到滑块拼图验证码，请在界面点击呼出本地窗口完成验证"
  }
}
```
