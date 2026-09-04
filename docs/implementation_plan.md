# 自媒体多账号矩阵分发平台 (matrix-hub) 实施计划 (更新版)

本项目旨在构建一个运行在本地私有化环境的自媒体多账号矩阵分发与定时发布系统。支持小红书、抖音（后续扩展快手、微信视频号等）的多账号隔离管理、一对多与多对多差异化原始视频批量分发、平台原生定时与本地错峰调度，以及扫码登录与状态监控。**（根据需求，不集成 FFmpeg 去重，系统直接分发与上传用户原始视频文件）**。

---

## 架构蓝图与设计决策

```mermaid
graph TD
    User([用户 / 浏览器 Web UI]) <-->|HTTP REST & WebSocket| FastAPI[FastAPI 后端服务 :8000]
    
    subgraph CoreServices [核心调度与业务层]
        FastAPI --> AccountMgr[账号与授权服务]
        FastAPI --> TaskOrchestrator[发布任务编排器]
        FastAPI --> VideoService[视频素材管理与校验 (纯原始文件)]
        FastAPI --> Scheduler[APScheduler 定时与错峰引擎]
        FastAPI --> Notifier[Webhook 告警机器人 (飞书/钉钉/企微)]
        
        Scheduler --> TaskOrchestrator
        TaskOrchestrator --> VideoService
    end

    subgraph DriverLayer [浏览器驱动与防风控隔离层]
        TaskOrchestrator --> DriverFactory{驱动提供器}
        DriverFactory -->|内置独立会话| PlaywrightEngine[Playwright + Stealth 独立环境]
        DriverFactory -->|CDP 协议扩展| FingerprintBrowser[比特浏览器 / AdsPower API]
    end

    subgraph PlatformAdapters [平台适配器抽象层]
        PlaywrightEngine --> BaseAdapter[BasePublisherAdapter 统一接口]
        FingerprintBrowser --> BaseAdapter
        BaseAdapter --> XHSAdapter[小红书适配器 (creator.xiaohongshu.com)]
        BaseAdapter --> DYAdapter[抖音适配器 (creator.douyin.com)]
        BaseAdapter -.-> KSAdapter[快手适配器 (预留扩展)]
        BaseAdapter -.-> WXAdapter[微信视频号适配器 (预留扩展)]
    end

    subgraph Storage [持久化存储]
        AccountMgr --> SQLite[(SQLite 数据库)]
        TaskOrchestrator --> SQLite
        AccountMgr --> SessionStore[(各账号 StorageState / Cookies)]
    end
```

---

## 核心设计要点

1. **多账号防关联与环境隔离 (Anti-Detection)**
   - 每个账号分配唯一的 `user_data_dir` 与会话存储文件，完全隔离 Cookie、LocalStorage、IndexedDB。
   - 注入 `playwright-stealth` 去除 `navigator.webdriver` 等自动化标记。
   - 适配器驱动层抽象统一，未来通过 CDP 可直接挂载外部指纹浏览器（如比特浏览器/AdsPower）。

2. **登录与风控交互 (QR Code & Human Assist)**
   - 后台调用浏览器打开创作者后台，捕获二维码 Base64 流实时推送到前端页面供手机扫码。
   - 遇到拼图滑块、短信验证码等强风控拦截时，后端提供“一键呼出本地窗口”接口，将后台浏览器切为可见桌面窗口，供人工辅助完成后自动切回静默运行并持久化会话。

3. **原视频精准分发与内容编排 (Zero-transcode Direct Distribution)**
   - **零转码原生分发**：不改变、不压缩、不去重用户原始视频，保证视频画质与原片完整性。
   - **分发映射模式**：
     - 单视频 -> 多账号（同一原视频分发给多个矩阵号）
     - 多视频 -> 多账号（1对1绑定、按文件夹名称/文件列表配对、或通过 Excel/CSV 批量导入）
   - **元数据定制覆盖**：
     - 支持设置统一主标题、正文与话题，同时支持为各个账号或平台单独微调标题、封面或标签。

4. **双重定时发布与错峰排队**
   - **平台原生定时发布**：在上传阶段自动识别并勾选小红书、抖音创作者中心的官方“定时发布”组件。优点是任务提交后本地电脑无需保持开机。
   - **本地错峰调度引擎**：基于 APScheduler。针对同一局域网/IP，支持设置阶梯错峰间隔（例如：每账号发布间隔 3~8 分钟随机波动），防止瞬时并发被平台判定为机刷。

---

## 项目工程结构

```
matrix-hub/
├── backend/
│   ├── app/
│   │   ├── api/                  # REST API 路由与 WebSocket
│   │   │   ├── accounts.py       # 账号增删查改、扫码登录、健康检查
│   │   │   ├── tasks.py          # 发布任务创建、批处理、状态查询
│   │   │   ├── videos.py         # 本地视频文件扫描、元数据校验、封面获取
│   │   │   ├── settings.py       # 系统配置与 Webhook 设置
│   │   │   └── ws.py             # 实时日志与二维码长连接
│   │   ├── core/                 # 核心配置与基础组件
│   │   │   ├── config.py         # 应用配置 (Pydantic Settings)
│   │   │   ├── database.py       # SQLite 连接与 Session 管理
│   │   │   ├── event_bus.py      # 事件总线 (日志推送、状态变更)
│   │   │   └── exceptions.py     # 异常定义
│   │   ├── models/               # 数据库实体模型 (SQLAlchemy)
│   │   │   ├── account.py        # 账号表 (平台类型, 昵称, 头像, 状态, 代理等)
│   │   │   ├── task.py           # 任务主表与子任务表 (发布状态, 错误信息, 定时时间)
│   │   │   └── setting.py        # 全局配置键值表
│   │   ├── drivers/              # 浏览器驱动与环境隔离
│   │   │   ├── base.py           # 浏览器驱动抽象接口
│   │   │   ├── playwright_driver.py # Playwright 本地隔离持久化驱动
│   │   │   └── fingerprint_driver.py # 指纹浏览器 CDP 连接器 (预留)
│   │   ├── adapters/             # 平台自动化发布适配器
│   │   │   ├── base.py           # BasePublisherAdapter 统一抽象基类
│   │   │   ├── xiaohongshu.py    # 小红书创作者服务平台适配器
│   │   │   ├── douyin.py         # 抖音创作者服务平台适配器
│   │   │   ├── kuaishou.py       # 快手适配器 (预留骨架)
│   │   │   └── channels.py       # 微信视频号适配器 (预留骨架)
│   │   ├── services/             # 业务服务层
│   │   │   ├── account_service.py # 账号生命周期管理与登录流程
│   │   │   ├── publisher_service.py # 发布任务执行与状态机
│   │   │   ├── video_service.py  # 原始视频文件管理与基本属性校验
│   │   │   ├── scheduler_service.py # APScheduler 定时调度与错峰算法
│   │   │   └── notifier_service.py  # 钉钉/飞书/企业微信 Webhook 通知
│   │   └── main.py               # FastAPI 入口与静态文件托管
│   ├── requirements.txt          # Python 依赖清单
│   └── run.py                    # 后端快捷启动脚本
├── frontend/                     # Vue 3 + Vite 前端工程
│   ├── src/
│   │   ├── api/                  # Axios 后端接口封装
│   │   ├── views/                # 页面视图
│   │   │   ├── Dashboard.vue     # 仪表盘 (发布统计、快捷操作)
│   │   │   ├── Accounts.vue      # 账号矩阵管理 (扫码登录、状态监测)
│   │   │   ├── PublishTask.vue   # 矩阵分发任务创建 (1:N / M:N 映射、母版/独立文案)
│   │   │   ├── TaskList.vue      # 任务队列与日志实时看板
│   │   │   └── Settings.vue      # 错峰策略与 Webhook 告警设置
│   │   ├── components/           # 公共组件 (二维码弹窗, 视频卡片, 差异化编辑器)
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
├── data/                         # 用户数据目录 (.gitignore 忽略敏感内容)
│   ├── matrix.db                 # SQLite 数据库文件
│   └── sessions/                 # 各账号独立 browser storage 状态文件
├── start.bat                     # Windows 一键启动脚本
└── README.md                     # 使用与部署说明文档
```

---

## 详细开发阶段与任务规划

### 阶段一：基础架构搭建与数据存储 (Milestone 1)
- [ ] 创建项目目录结构与 Python 虚拟环境配置。
- [ ] 编写 `requirements.txt`（精简依赖：`fastapi`, `uvicorn`, `playwright`, `playwright-stealth`, `sqlalchemy`, `apscheduler`, `pydantic`, `httpx` 等，无需 FFmpeg 依赖）。
- [ ] 搭建 FastAPI 基础架构，配置 SQLite 数据库 ORM 模型与数据表自动建表。
- [ ] 实现 WebSocket 日志广播与状态推送机制。

### 阶段二：浏览器驱动层与账号授权系统 (Milestone 2)
- [ ] 实现 `BrowserDriverProvider`，支持独立 `user_data_dir` 隔离。
- [ ] 实现 `BasePublisherAdapter` 抽象基类标准接口。
- [ ] 实现**小红书适配器**：
  - 扫码登录流程：捕获登录二维码图像并转为 Base64，轮询扫码状态，持久化存储 `storage_state.json`。
  - 会话健康检测：判断登录态是否有效，更新账号昵称与头像。
  - 异常辅助切换：支持切为有头浏览器供用户手动过验证码。
- [ ] 实现**抖音适配器**：
  - 扫码登录流程：抖音创作者服务平台二维码提取与状态监听。
  - 会话状态持久化与有效性探测。
- [ ] 账号管理 API：支持账号列表、分组标签、状态刷新与一键登录。

### 阶段三：原始视频素材服务与分发编排 (Milestone 3)
- [ ] 实现原视频管理服务：本地视频路径有效性校验、基本格式校验（mp4/mov 等）、生成临时预览海报图。
- [ ] 矩阵发布编排器：
  - 1:N 映射（单视频广播到多账号）。
  - M:N 映射（多视频批量分配给各账号，支持从文件夹或表格导入配对）。
  - 统一母版与独立覆盖（各账号独立标题、正文、话题标签 #、自定义封面）。

### 阶段四：自动化发布适配器与任务调度编排 (Milestone 4)
- [ ] 完成**小红书自动化发布流程**：
  - 自动打开创作者后台，上传原视频文件。
  - 填写标题、正文、话题标签（#）、设置封面。
  - 支持设置平台原生定时发布或立即发布。
  - 捕获发布成功状态与作品反馈。
- [ ] 完成**抖音自动化发布流程**：
  - 创作者中心上传原视频，等待转码/上传完成。
  - 填写描述文本、提取并填充话题（#）、@朋友、封面设置。
  - 平台原生定时发布控件操作与最终提交。
- [ ] 任务调度器（APScheduler 集成）：
  - 多账号错峰排队算法（支持配置基础间隔与随机扰动时间）。
  - 任务失败自动重试机制与状态流转。
  - 告警服务：对接飞书/钉钉/企业微信机器人 Webhook 推送。

### 阶段五：前端可视化管理后台开发 (Milestone 5)
- [ ] 初始化 Vue 3 + Vite + Element Plus 前端工程。
- [ ] **账号管理界面**：账号卡片列表、分组筛选、扫码登录弹窗（实时展示二维码）、一键健康检查、唤起人工辅助。
- [ ] **矩阵分发工作台**：
  - 视频与账号映射配置（支持“1视频->多账号”、“多视频->对应账号”）。
  - 统一母版配置 + 账号级独立覆盖编辑（标题、标签、定时时间）。
  - 文件夹批量扫描与 Excel 任务导入导出支持。
- [ ] **任务看板与调度中心**：任务时间轴、实时日志流展示、手动重试/取消。
- [ ] **系统设置**：错峰时间参数、Webhook 机器人 URL、平台扩展配置。

### 阶段六：Windows 一键启动与多平台扩展验证 (Milestone 6)
- [ ] 编写前端构建与静态文件集成脚本（FastAPI 直接托管编译后的前端资源）。
- [ ] 编写 Windows 一键启动脚本 `start.bat`（自动检查依赖、启动后台、自动在默认浏览器打开控制台）。
- [ ] 验证小红书和抖音端到端发布全链路。
- [ ] 为快手与微信视频号提供规范化适配器接口骨架与开发指南。

---

## 验证与测试计划

### 1. 自动化接口与驱动测试
- 驱动测试：Playwright 在无头与有头模式下会话文件读写隔离性测试。
- 调度测试：APScheduler 错峰排队时间间隔计算测试。
- 视频映射测试：1:N 与 M:N 矩阵映射及覆盖文案生成逻辑测试。

### 2. 核心业务全链路人工验收
- **账号授权**：测试小红书和抖音扫码登录，验证 `storage_state` 正常落盘，页面正常获取创作者昵称。
- **差异化发布**：
  - 测试用例 A：单视频 -> 小红书账号A + 抖音账号B（差异化标题和话题，直接上传原视频，验证两端成功发布）。
  - 测试用例 B：双视频 -> 账号A与账号B独立匹配发布。
  - 测试用例 C：勾选平台原生定时（如设定后天上午10:00），验证平台后台成功识别定时状态。
- **风控辅助**：模拟触发滑块时，点击“呼出本地窗口”，人工滑动通过后系统自动继续发布。
- **消息通知**：测试任务失败或成功时，配置的钉钉/飞书群能够即时收到卡片提醒。
