# 自媒体多账号矩阵分发平台 (matrix-hub) 架构设计方案

## 1. 项目概述

`matrix-hub` 是一款专为自媒体创作者打造的本地私有化多账号矩阵内容分发与调度系统。系统以本地私有化 Web 服务的形式运行，充分利用本地真实网络和独立会话环境，规避公网云端服务器引发的风控限制；支持对小红书、抖音（后续扩展快手、微信视频号等）的主流创作者后台进行多账号独立管理、视频素材差异化映射分发、平台原生与本地错峰定时发布。

### 核心特性
- **本地环境与防风控**：基于本地局域网真实家庭/办公宽带网络运行，每个账号独享独立的持久化浏览器会话（`user_data_dir`），杜绝 Cookie 与缓存串号。
- **可插拔双轨驱动**：内置 Playwright + Stealth 防检测引擎；同时支持无缝对接比特浏览器/AdsPower等专业指纹浏览器的 CDP 调试接口。
- **原画质直发**：完全不做二次转码和有损压缩，原样分发用户原始视频文件，保持视频最高画质。
- **灵活的矩阵映射**：支持 1:N（单视频多发）与 M:N（多视频多账号独立对应发布），支持从文件夹或 Excel 表格批量导入绑定。
- **双重定时机制**：
  - **平台原生定时**：在上传过程中直接唤起平台自带的“定时发布”功能，发布后本地电脑无需保持开机。
  - **本地错峰调度**：由本地 APScheduler 接管，按设定的基础间隔叠加随机扰动时间排队分发，避免同一 IP 短时间内高并发上传触发平台限流。
- **异常人工辅助**：扫码登录实时推流至前端；若遇到滑块拼图或短信二次验证，支持一键在本地呼出真实浏览器窗口由用户人工解决，完成后自动接管。
- **开箱即用**：FastAPI + SQLite + Vue 3 架构，零外部中间件（无需安装 Redis 或独立数据库），提供 Windows 一键双击启动。

---

## 2. 系统整体架构

```mermaid
graph TD
    Client([用户浏览器 Web UI]) <-->|HTTP REST / WebSocket| Gateway[FastAPI 核心服务 :8000]

    subgraph BusinessLayer [业务服务层]
        Gateway --> AccountService[账号服务 (生命周期/心跳/扫码)]
        Gateway --> VideoService[视频素材服务 (元数据校验/封面抽取)]
        Gateway --> TaskService[任务编排服务 (1:N & M:N 分发映射)]
        Gateway --> SchedulerService[调度服务 (APScheduler + 错峰队列)]
        Gateway --> NotifierService[告警服务 (飞书/钉钉/企微 Webhook)]
    end

    subgraph DriverLayer [驱动与防关联隔离层]
        TaskService --> DriverFactory{驱动工厂}
        DriverFactory -->|默认内置驱动| PlaywrightDriver[Playwright + Stealth 独立上下文]
        DriverFactory -->|外部扩展驱动| FingerprintDriver[指纹浏览器 CDP 客户端]
    end

    subgraph AdapterLayer [平台适配器抽象层]
        BaseAdapter[BasePublisherAdapter 统一抽象接口]
        PlaywrightDriver --> BaseAdapter
        FingerprintDriver --> BaseAdapter
        
        BaseAdapter --> XHSAdapter[小红书创作者服务平台适配器]
        BaseAdapter --> DYAdapter[抖音创作者服务平台适配器]
        BaseAdapter -.-> KSAdapter[快手适配器 (预留扩展)]
        BaseAdapter -.-> WXAdapter[微信视频号适配器 (预留扩展)]
    end

    subgraph Persistence [数据持久化]
        AccountService --> SQLite[(SQLite 数据库)]
        TaskService --> SQLite
        AccountService --> SessionStore[各账号独立的 StorageState 存储]
    end
```

---

## 3. 核心子系统详细设计

### 3.1 浏览器环境隔离与防关联机制
为避免多账号被平台判定为同人操控或机刷，系统实施多重隔离：
1. **持久化目录隔离**：
   系统为每个注册账号在 `data/sessions/{account_id}/` 下分配专用的 `user_data_dir`。所有的 Cookie、LocalStorage、SessionStorage、Cache 和 IndexedDB 均完全物理隔离。
2. **反指纹检测注入**：
   加载 `playwright-stealth` 补丁，伪装 `navigator.webdriver` 为 `undefined`，规避常规的 Headless 检测、Chrome 运行时参数检测及自动化特征探测。
3. **多浏览器并发控制**：
   由于本地电脑内存限制，系统内置并发信号量（`Concurrency Semaphore`，默认最多同时开启 1~2 个浏览器实例），任务按队列串行或低并发执行，防止占用过多系统资源。
4. **扩展指纹浏览器接口**：
   预留 `FingerprintCdpDriver`，若用户后续账号量激增（如 20 个以上），可通过配置比特浏览器（BitBrowser）或 AdsPower 的本地 REST API，自动开启指定的指纹浏览器环境并通过 CDP 端口连接执行。

### 3.2 账号授权与人机协同交互
1. **内嵌扫码登录**：
   - 用户在 Web UI 点击“添加账号”或“重新登录”，后台启动对应平台的登录流程，自动定位二维码元素并截图为 Base64。
   - 通过 WebSocket 实时推送到前端模态框，用户打开对应手机 App 扫码。
   - 后台轮询登录状态，检测到 URL 跳转或创作者中心主元素出现后，立即调用 `context.storage_state(path=...)` 持久化凭证，并抓取账号昵称、头像和 UID 保存至数据库。
2. **异常情况人机协同（一键唤起桌面窗口）**：
   - 当遇到滑块验证码或需要短信二次验证时，系统捕获阻断状态，向前端发送警告并展示“呼出本地窗口”按钮。
   - 用户点击后，后台将当前浏览器上下文切为有头桌面窗口（Visible Desktop Window），用户在本地屏幕上直接用鼠标拖动滑块完成验证。
   - 验证通过后，系统保存会话状态并关闭窗口，无缝恢复自动化流程。
3. **健康度心跳检测**：
   - 支持后台定时或一键触发账号有效性检查（通过快速请求创作者后台主接口判断 Cookie 是否过期）。

### 3.3 原始视频分发与内容编排
1. **分发映射模式**：
   - **1:N 模式**：选择 1 个原始视频，同时勾选多个账号进行分发。
   - **M:N 模式**：选择多个原始视频，与多个账号进行 1对1 对应或自定义规则匹配。
   - **批量导入**：支持扫描指定文件夹（按文件名匹配），或通过 Excel/CSV 模版批量导入分发任务列表。
2. **元数据多级覆盖机制**：
   - **统一母版**：填写一份通用的标题、正文描述、话题标签（#）和定时时间。
   - **差异化覆盖**：允许用户在表格/卡片中单独针对某个平台（如小红书专用标题限制 20 字以内，抖音支持 @好友）或某个特定账号进行独立微调覆盖。

### 3.4 双重定时发布与错峰调度
1. **平台原生定时发布**：
   - 适配器在操作创作者后台发布页面时，自动勾选各平台的官方“定时发布”选项（小红书与抖音均原生支持 2小时~14天 内的定时发布）。
   - 提交成功后，平台服务器会在指定时刻自动公开视频，用户本地电脑在任务发布完成后可安全关机。
2. **本地错峰排队引擎**：
   - 若用户未选择平台原生定时，或需要更细致的时间控制，本地基于 `APScheduler` 执行定时唤醒。
   - **阶梯错峰算法**：
     $$T_{\text{exec}} = T_{\text{base}} + i \times \Delta t_{\text{interval}} + \text{random}(-\delta, \delta)$$
     其中每个账号之间设置一定的间隔（例如 3~8 分钟随机波动），避免同一本地局域网公网 IP 瞬间发起数十次上传行为，有效保护账号权重。

### 3.5 告警通知机制
- 系统支持对接主流协作平台的 Webhook 机器人（飞书、钉钉、企业微信）。
- 在发生以下关键事件时主动推送富文本卡片通知：
  - 任务批量分发完成报告；
  - 账号登录态过期或遇到需要人工介入的验证码；
  - 发布任务遇到严重异常（上传超时、内容违规提示等）。

---

## 4. 技术栈选型

| 层次 | 选型 | 优势与原因 |
| :--- | :--- | :--- |
| **后端框架** | Python 3.10+ / FastAPI | 高性能异步框架，内置 OpenAPI 文档，原生支持 WebSocket 双向通信 |
| **任务调度** | APScheduler (AsyncIOScheduler) | 轻量纯 Python 调度器，支持 Cron/Date/Interval，无外部守护进程依赖 |
| **浏览器自动化**| Playwright Python + playwright-stealth | 现代异步驱动，执行稳定，隔离性优于 Selenium，支持 CDP 连接 |
| **数据库** | SQLite + SQLAlchemy 2.0 | 本地单文件数据库，开启 WAL 模式高并发读写，零安装与维护成本 |
| **前端框架** | Vue 3 + Vite + Element Plus + TailwindCSS | 组件生态完善，中文文档友好，适合构建管理后台与数据看板 |
| **部署与交付** | 静态单体化 + Windows 批处理 (`start.bat`) | 前端构建产物由 FastAPI 直接托管，用户双击一键即启 |
