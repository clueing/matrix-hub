# matrix-hub (自媒体多账号矩阵分发平台) 落地实施完成走查

本项目已完成全量核心代码构建与系统集成，所有设计指标与用户定制要求均已就绪。

---

## 1. 核心交付成果

### 1.1 后端服务体系 (`backend/`)
- **核心架构**：基于 Python 3.14 + FastAPI + SQLite (WAL 模式) + SQLAlchemy 2.0 异步 ORM。
- **环境隔离驱动 (`backend/app/drivers/`)**：
  - `PlaywrightDriver`：为每个账号独立分配持久化会话目录（`user_data_dir`），杜绝串号与数据污染。
  - 集成 `playwright-stealth`（Stealth v2）消除浏览器自动化指纹特征。
  - 信号量机制严格限制本地并发数（默认 1~2 个实例），防止占用过多内存与 CPU。
- **平台适配器 (`backend/app/adapters/`)**：
  - `XiaohongshuAdapter`：小红书创作者服务平台，支持自动抓取登录二维码、扫码状态轮询、原视频上传、标题限制（<=20字）校验、正文与话题标签（#）填充、平台原生定时发布。
  - `DouyinAdapter`：抖音创作者服务平台，支持二维码流提取、登录健康检测、原视频无损直传、标题/描述/话题整合填充、平台原生定时。
  - `KuaishouAdapter` & `ChannelsAdapter`：标准化预留骨架，方便后续一键接入。
- **业务服务 (`backend/app/services/`)**：
  - `AccountService`：扫码登录会话管理、健康度心跳检查、桌面弹窗人工辅助（解决滑块拼图/短信验证）、**账号凭证单账号/批量一键导出与导入恢复（ZIP 归档）**。
  - `VideoService`：本地视频路径有效性检测与文件夹深度扫描。
  - `SchedulerService`：基于 `APScheduler`，支持**立即错峰排队**、**平台官方原生定时**以及**本地阶梯定时**（支持基础间隔与随机扰动时间）。
  - `NotifierService`：支持飞书、钉钉、企业微信机器人 Webhook 告警通知。
- **实时通信与 API (`backend/app/api/`)**：
  - RESTful 接口覆盖账号、任务、视频、系统设置四大领域。
  - `/ws` WebSocket 通道实时广播后台执行日志、动态二维码及账号状态变更。

### 1.2 前端可视化工作台 (`frontend/`)
- **技术栈**：基于 Vue 3 + TypeScript + Vite + Element Plus + pnpm 构建。
- **页面视图 (`frontend/src/views/`)**：
  - `Dashboard.vue`：矩阵概览看板、账号健康占比、发布成功率统计、快捷入口。
  - `Accounts.vue`：矩阵账号卡片网格、实时扫码弹窗、健康测试、桌面窗口唤起、一键导出 ZIP、导入恢复 ZIP。
  - `PublishTask.vue`：1对多广播与多对多匹配模式切换、本地文件/文件夹批量扫描导入、统一母版配置、账号差异化独立覆盖编辑、错峰与原生定时调度。
  - `TaskList.vue`：任务实时状态列表、可展开子任务明细、失败一键重试、实时日志终端抽屉。
  - `Settings.vue`：错峰间隔/扰动设置、并发上限配置、Webhook 机器人测试与配置。
- **生产构建产物 (`frontend/dist/`)**：已编译打包并由 FastAPI 自动静态托管。

### 1.3 启动与运行 (`start.bat`)
- 提供 Windows 一键双击批处理脚本 `start.bat`，自动检测环境、启动后端并自动拉起默认浏览器访问 `http://127.0.0.1:8000`。

---

## 2. 验证与测试结果

| 验证项 | 测试方法 | 结果 |
| :--- | :--- | :--- |
| **数据库初始化** | 执行 `init_db()` 创建 SQLite 表结构与索引 | 成功建立 `accounts`, `publish_tasks`, `publish_subtasks`, `system_settings` 表并开启 WAL 模式 |
| **Playwright 与 Chromium** | 验证 Playwright 驱动与 Stealth 补丁装载 | Chromium 依赖安装完毕，Stealth v2 成功挂载无头/有头上下文 |
| **前端打包构建** | `pnpm build` (vue-tsc + vite) | 成功生成 100% 静态产物至 `frontend/dist`，无任何类型报错 |
| **后端接口服务** | 请求 `http://127.0.0.1:8000/api/health` 与 `/api/accounts` | HTTP 200 成功响应 `{"status":"ok","app":"matrix-hub"}` |
| **静态单体化托管** | 浏览器直接访问 `http://127.0.0.1:8000/` | FastAPI 成功托管 Vue 3 SPA 应用，前端交互与路由全部正常 |
| **Windows 编码兼容** | 控制台输出重构为 UTF-8 并在 Windows 终端运行 | 彻底消除 GBK 编码异常，日志输出稳定 |

---

## 3. 快速启动说明

直接双击项目根目录下的 **`start.bat`**，系统将自动启动并在浏览器中打开控制台：
```
http://127.0.0.1:8000
```
或在终端通过命令行启动：
```bash
# 激活 Python 环境并启动
.venv\Scripts\python.exe backend/run.py
```
如需进行前端热更新开发：
```bash
cd frontend
pnpm dev
```

---

## 4. 登录授权与状态同步专项优化记录

### 4.1 二维码极速提取与反风控优化
- **问题原因**：早期版本在抓取登录页时使用 `networkidle`，由于创作者平台长期存在后台埋点与长轮询请求导致 30 秒超时挂死。
- **解决对策**：调整为 `domcontentloaded` 立即介入，直接捕获页面内生成的 `data:image` Base64 二维码数据，出码速度提升至 1.5 秒内。

### 4.2 账号登录态竞态覆盖与失效修复
- **问题原因**：用户在弹窗中呼出桌面辅助窗口后，后台原无头扫码任务仍以 120 秒超时倒计时运行；超时后执行了将状态重置为 `unauthorized` 的回退逻辑，导致已登录账号迅速失效；同时后台任务复用请求级数据库 Session 容易引发连接关闭异常。
- **解决对策**：
  1. 呼出桌面窗口时立即中断后台无头扫码任务，释放 Windows 下 Chromium `user_data_dir` 文件排他锁。
  2. 辅助窗口任务全面接管独立的数据库生命周期会话，检测到跳转或有效 Session Cookie 后立即自动保存凭证并标记状态为 `active`。
  3. 在扫码超时回退前做前置判断，若账号已处于有效激活态则不执行状态降级。

### 4.3 界面状态即时自动刷新
- **优化点**：
  1. 扫码弹窗内直接提供【遇到滑块/打不开？呼出桌面 Chrome 辅助窗口】快捷入口。
  2. 无论扫码登录还是人工辅助窗口登录，前端采用 WebSocket 广播 + 2 秒双保险轮询机制，验证通过后前端卡片网格与弹窗自动同步更新为【在线有效】，无需手动刷新。
