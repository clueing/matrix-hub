# 自媒体多账号矩阵分发平台 (matrix-hub) 数据库设计文档

数据库采用轻量级关系型数据库 **SQLite**，开启 WAL (Write-Ahead Logging) 模式以支持异步高并发读写。

---

## 1. 数据表汇总

| 表名 | 实体说明 | 核心职责 |
| :--- | :--- | :--- |
| `accounts` | 平台账号表 | 存储各社交平台的账号信息、登录态路径、健康状态及所属分组 |
| `publish_tasks` | 发布任务主表 | 一次批量分发的大任务记录（统计总数、进度、状态等） |
| `publish_subtasks` | 发布子任务表 | 针对具体每个账号的独立发布执行记录，包含独立标题、标签、定时参数及执行结果 |
| `system_settings` | 系统设置表 | 保存全局参数（错峰间隔、Webhook 机器人地址、并发上限等） |

---

## 2. 表结构详细设计

### 2.1 平台账号表 (`accounts`)

```sql
CREATE TABLE accounts (
    id VARCHAR(36) PRIMARY KEY,              -- 账号唯一ID (UUID)
    platform VARCHAR(32) NOT NULL,            -- 平台标识: 'xiaohongshu', 'douyin', 'kuaishou', 'channels'
    account_name VARCHAR(128),                -- 创作者昵称
    uid VARCHAR(128),                         -- 平台唯一用户ID
    avatar_url TEXT,                          -- 创作者头像链接
    group_name VARCHAR(64) DEFAULT '默认分组', -- 账号分组/矩阵标签
    status VARCHAR(32) DEFAULT 'unauthorized',-- 状态: 'unauthorized', 'active', 'expired', 'banned'
    storage_path TEXT NOT NULL,               -- 独立会话/Cookies存储路径 (相对或绝对路径)
    proxy_url VARCHAR(255),                   -- 可选的独立代理IP (http://user:pass@host:port)
    last_login_at DATETIME,                   -- 最后成功登录时间
    last_check_at DATETIME,                   -- 最后一次健康检查时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_platform ON accounts(platform);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_group ON accounts(group_name);
```

---

### 2.2 发布任务主表 (`publish_tasks`)

```sql
CREATE TABLE publish_tasks (
    id VARCHAR(36) PRIMARY KEY,              -- 任务ID (UUID)
    name VARCHAR(255) NOT NULL,               -- 任务名称/描述
    task_type VARCHAR(32) NOT NULL,           -- 分发模式: 'one_to_many' (1对多), 'many_to_many' (多对多匹配)
    status VARCHAR(32) DEFAULT 'pending',     -- 状态: 'pending', 'processing', 'completed', 'partial_failed', 'failed', 'cancelled'
    total_count INTEGER DEFAULT 0,            -- 子任务总数
    success_count INTEGER DEFAULT 0,          -- 成功发布的数量
    fail_count INTEGER DEFAULT 0,             -- 失败数量
    remark TEXT,                              -- 备注信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_status ON publish_tasks(status);
CREATE INDEX idx_tasks_created_at ON publish_tasks(created_at);
```

---

### 2.3 发布子任务表 (`publish_subtasks`)

```sql
CREATE TABLE publish_subtasks (
    id VARCHAR(36) PRIMARY KEY,              -- 子任务ID (UUID)
    task_id VARCHAR(36) NOT NULL,             -- 关联的主任务ID
    account_id VARCHAR(36) NOT NULL,          -- 关联的发布账号ID
    platform VARCHAR(32) NOT NULL,            -- 平台标识
    
    -- 素材与元数据
    video_path TEXT NOT NULL,                 -- 原始视频文件本地绝对路径
    cover_path TEXT,                          -- 自定义封面图本地路径 (为空则由平台自动截取)
    title VARCHAR(255) NOT NULL,              -- 发布标题 (小红书<=20字，抖音将合并到描述)
    description TEXT,                         -- 正文描述
    tags JSON,                                -- 话题标签列表 (例如: ["#自媒体", "#干货"])
    
    -- 调度与时间控制
    schedule_mode VARCHAR(32) DEFAULT 'immediate', -- 'immediate'(立即发布), 'platform_native'(平台原生定时), 'local_staggered'(本地错峰定时)
    scheduled_at DATETIME,                    -- 期望发布的日期时间
    stagger_delay_seconds INTEGER DEFAULT 0,  -- 错峰执行延迟秒数
    
    -- 执行与结果
    status VARCHAR(32) DEFAULT 'pending',     -- 'pending', 'waiting_manual', 'uploading', 'published', 'failed', 'cancelled'
    retry_count INTEGER DEFAULT 0,            -- 已重试次数
    max_retries INTEGER DEFAULT 2,            -- 最大允许重试次数
    error_message TEXT,                       -- 失败原因或错误堆栈
    platform_work_id VARCHAR(128),            -- 平台返回的作品ID (如能捕获)
    platform_work_url TEXT,                   -- 平台作品公开链接
    executed_at DATETIME,                     -- 实际执行开始时间
    finished_at DATETIME,                     -- 最终完成时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id) REFERENCES publish_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX idx_subtasks_task_id ON publish_subtasks(task_id);
CREATE INDEX idx_subtasks_account_id ON publish_subtasks(account_id);
CREATE INDEX idx_subtasks_status ON publish_subtasks(status);
CREATE INDEX idx_subtasks_scheduled_at ON publish_subtasks(scheduled_at);
```

---

### 2.4 系统设置表 (`system_settings`)

```sql
CREATE TABLE system_settings (
    key VARCHAR(64) PRIMARY KEY,              -- 配置键
    value TEXT NOT NULL,                      -- 配置值 (JSON 字符串或普通标量)
    description VARCHAR(255),                 -- 配置说明
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 预置配置项示例：
- `stagger_interval_seconds`: 错峰基础间隔（秒），默认 `300`（5分钟）。
- `stagger_jitter_seconds`: 随机扰动上限（秒），默认 `120`（±2分钟）。
- `max_browser_concurrency`: 本地最大并发浏览器数，默认 `1`。
- `webhook_url`: 钉钉/飞书/企业微信机器人 Webhook 链接。
- `webhook_channel`: 机器人平台类型 (`feishu` / `dingtalk` / `wecom`)。
- `headless_default`: 默认是否以无头模式运行（`true` / `false`）。
