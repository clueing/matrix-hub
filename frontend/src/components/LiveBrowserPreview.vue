<template>
  <div class="live-browser-wrapper">
    <!-- 右侧浮动召唤按钮 (类似 Manus 侧边挂件) -->
    <div 
      class="floating-preview-trigger"
      :class="{ 'is-active': isLive }"
      @click="visible = !visible"
      title="点击展开/折叠受控浏览器实时视窗"
    >
      <div class="trigger-indicator">
        <span class="status-pulse" :class="{ 'is-live': isLive }"></span>
      </div>
      <div class="trigger-content">
        <span class="trigger-icon">🤖</span>
        <span class="trigger-text">实时浏览器</span>
      </div>
      <div v-if="isLive" class="live-pill">LIVE</div>
    </div>

    <!-- 侧边推拉视窗抽屉 -->
    <el-drawer
      v-model="visible"
      :size="drawerSize"
      :with-header="false"
      class="manus-preview-drawer"
      direction="rtl"
      :modal="false"
      append-to-body
    >
      <div class="preview-container">
        <!-- 顶部导航栏与状态 -->
        <div class="preview-header">
          <div class="flex items-center gap-2">
            <span class="text-lg">🤖</span>
            <div>
              <div class="font-bold text-sm text-slate-100 flex items-center gap-2">
                <span>实时受控视窗</span>
                <el-tag v-if="isLive" size="small" type="success" effect="dark" class="live-tag">
                  <span class="live-dot"></span> LIVE 画面
                </el-tag>
                <el-tag v-else size="small" type="info" effect="dark">
                  待命中
                </el-tag>
              </div>
              <div class="text-[11px] text-slate-400 truncate max-w-[280px]">
                {{ currentTitle || (isLive ? '正在执行自动化管线...' : '等待分发或登录任务启动') }}
              </div>
            </div>
          </div>

          <!-- 顶部快捷工具组 -->
          <div class="flex items-center gap-1">
            <el-tooltip content="保存当前画面快照" placement="bottom">
              <el-button 
                size="small" 
                circle 
                type="info" 
                plain 
                :disabled="!currentFrame" 
                @click="downloadSnapshot"
              >
                <el-icon><Camera /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="切换窗口尺寸" placement="bottom">
              <el-button 
                size="small" 
                circle 
                type="info" 
                plain 
                @click="toggleSize"
              >
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="收起视窗" placement="bottom">
              <el-button 
                size="small" 
                circle 
                type="info" 
                plain 
                @click="visible = false"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>

        <!-- 模拟浏览器地址栏 (Omnibox) -->
        <div class="omnibox-bar">
          <div class="omnibox-controls">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
          </div>
          <div class="omnibox-input">
            <el-icon class="mr-1 text-slate-400"><Lock /></el-icon>
            <span class="url-text select-all truncate">{{ currentUrl || 'about:blank' }}</span>
          </div>
          <div class="omnibox-fps text-[10px] text-slate-400">
            {{ isLive ? `${fps} FPS` : 'OFFLINE' }}
          </div>
        </div>

        <!-- 核心画面渲染区 (Cinematic Viewport) -->
        <div class="viewport-area">
          <div v-if="currentFrame" class="frame-screen">
            <img 
              :src="'data:image/jpeg;base64,' + currentFrame" 
              alt="Live Screen" 
              class="screencast-img"
            />
            <div v-if="lastAction" class="action-hud-pill">
              <span class="hud-dot"></span>
              <span class="hud-text">{{ lastAction }}</span>
            </div>
          </div>

          <!-- 空闲待命时的科技感骨架占位 -->
          <div v-else class="idle-placeholder">
            <div class="radar-box">
              <div class="radar-wave"></div>
              <el-icon :size="48" class="text-slate-600"><Monitor /></el-icon>
            </div>
            <div class="text-sm font-medium text-slate-300 mt-4">暂无活跃的受控浏览器视窗</div>
            <div class="text-xs text-slate-500 mt-1 max-w-xs text-center leading-relaxed">
              当发起矩阵视频发布、账号扫码登录或平台健康检测时，此处将以低时延流式呈现底层无头浏览器的真实操作过程。
            </div>
          </div>
        </div>

        <!-- 底部实时动作流水 -->
        <div class="action-terminal">
          <div class="terminal-header">
            <span class="text-[11px] font-mono font-bold text-slate-400">SYNC LOG STREAM</span>
            <span class="text-[10px] text-slate-500">{{ recentLogs.length }} 动作记录</span>
          </div>
          <div class="terminal-body" ref="terminalBodyRef">
            <div v-if="recentLogs.length === 0" class="text-slate-600 text-xs py-3 text-center font-mono">
              等待动作流水注入...
            </div>
            <div 
              v-for="(log, idx) in recentLogs" 
              :key="idx" 
              class="terminal-line"
            >
              <span class="line-time">{{ log.time }}</span>
              <span class="line-tag" :class="getLogLevelClass(log.level)">[{{ log.level }}]</span>
              <span class="line-msg">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue"
import { Camera, FullScreen, Close, Lock, Monitor } from "@element-plus/icons-vue"

const visible = ref(false)
const drawerSize = ref("620px")

const currentFrame = ref<string | null>(null)
const currentTitle = ref<string>("")
const currentUrl = ref<string>("")
const lastAction = ref<string>("")
const recentLogs = ref<any[]>([])

const frameCount = ref(0)
const fps = ref(0)
let fpsTimer: any = null

const lastFrameTime = ref(0)
const isLive = computed(() => {
  return Date.now() - lastFrameTime.value < 4000
})

const terminalBodyRef = ref<HTMLElement | null>(null)

const toggleSize = () => {
  drawerSize.value = drawerSize.value === "620px" ? "880px" : "620px"
}

const downloadSnapshot = () => {
  if (!currentFrame.value) return
  const link = document.createElement("a")
  link.download = `matrix-browser-${Date.now()}.jpg`
  link.href = "data:image/jpeg;base64," + currentFrame.value
  link.click()
}

const getLogLevelClass = (level: string) => {
  switch (level) {
    case "SUCCESS": return "text-emerald-400 font-bold"
    case "ERROR": return "text-rose-400 font-bold"
    case "WARNING": return "text-amber-400 font-bold"
    default: return "text-sky-300"
  }
}

let ws: WebSocket | null = null

const initWebSocket = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.event === "screencast_frame") {
        currentFrame.value = msg.data.frame
        if (msg.data.title) currentTitle.value = msg.data.title
        if (msg.data.url) currentUrl.value = msg.data.url
        lastFrameTime.value = Date.now()
        frameCount.value++
      } else if (msg.event === "screencast_stopped") {
        // 会话结束
        setTimeout(() => {
          if (Date.now() - lastFrameTime.value >= 3000) {
            currentFrame.value = null
            currentTitle.value = ""
            currentUrl.value = ""
          }
        }, 3000)
      } else if (msg.event === "log_append") {
        lastAction.value = msg.data.message
        recentLogs.value.unshift(msg.data)
        if (recentLogs.value.length > 50) recentLogs.value.pop()
        nextTick(() => {
          if (terminalBodyRef.value) {
            terminalBodyRef.value.scrollTop = 0
          }
        })
      }
    } catch (e) {}
  }

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000)
  }
}

onMounted(() => {
  initWebSocket()
  fpsTimer = setInterval(() => {
    fps.value = frameCount.value
    frameCount.value = 0
  }, 1000)
})

onUnmounted(() => {
  if (fpsTimer) clearInterval(fpsTimer)
  if (ws) ws.close()
})
</script>

<style scoped>
/* 悬浮唤出气泡 */
.floating-preview-trigger {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2100;
  background: #0f172a;
  border: 1px solid #334155;
  border-right: none;
  border-radius: 12px 0 0 12px;
  padding: 10px 8px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.25);
  transition: all 0.25s ease;
  user-select: none;
}

.floating-preview-trigger:hover {
  background: #1e293b;
  padding-left: 12px;
  border-color: #38bdf8;
}

.floating-preview-trigger.is-active {
  border-color: #10b981;
  box-shadow: -4px 0 20px rgba(16, 185, 129, 0.35);
}

.trigger-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.3s ease;
}

.status-pulse.is-live {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: pulse-ring 1.8s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.9); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.7; }
  100% { transform: scale(0.9); opacity: 1; }
}

.trigger-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.trigger-icon {
  font-size: 16px;
}

.trigger-text {
  writing-mode: vertical-rl;
  font-size: 11px;
  letter-spacing: 2px;
  color: #94a3b8;
  font-weight: 500;
}

.floating-preview-trigger:hover .trigger-text,
.floating-preview-trigger.is-active .trigger-text {
  color: #f8fafc;
}

.live-pill {
  background: #10b981;
  color: #ffffff;
  font-size: 9px;
  font-weight: bold;
  padding: 1px 4px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

/* 抽屉内部结构 */
.preview-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #090d16;
  color: #f1f5f9;
}

.preview-header {
  padding: 14px 18px;
  background: #0f172a;
  border-bottom: 1px solid #1e293b;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.live-tag {
  background-color: #064e3b !important;
  border-color: #059669 !important;
  color: #34d399 !important;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34d399;
  display: inline-block;
  margin-right: 4px;
  animation: blink 1s infinite alternate;
}

@keyframes blink {
  from { opacity: 0.4; }
  to { opacity: 1; }
}

/* Omnibox */
.omnibox-bar {
  padding: 8px 16px;
  background: #131c31;
  border-bottom: 1px solid #1e293b;
  display: flex;
  align-items: center;
  gap: 12px;
}

.omnibox-controls {
  display: flex;
  gap: 5px;
}

.omnibox-controls .dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.dot.red { background: #ef4444; }
.dot.yellow { background: #eab308; }
.dot.green { background: #22c55e; }

.omnibox-input {
  flex: 1;
  background: #090d16;
  border: 1px solid #223049;
  border-radius: 6px;
  padding: 4px 10px;
  display: flex;
  align-items: center;
  font-size: 11px;
  color: #94a3b8;
  font-family: monospace;
}

.url-text {
  color: #e2e8f0;
}

/* 核心视口 */
.viewport-area {
  flex: 1;
  background: #030712;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 12px;
}

.frame-screen {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.screencast-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  border: 1px solid #1e293b;
}

.action-hud-pill {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(15, 23, 42, 0.88);
  backdrop-filter: blur(8px);
  border: 1px solid #334155;
  border-radius: 20px;
  padding: 6px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  max-width: 85%;
}

.hud-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 6px #38bdf8;
  flex-shrink: 0;
}

.hud-text {
  font-size: 11px;
  color: #f1f5f9;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 空闲待命状态 */
.idle-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.radar-box {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #0f172a;
  border: 1px solid #1e293b;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-wave {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 1px solid rgba(56, 189, 248, 0.2);
  animation: radar-expand 2.5s infinite;
}

@keyframes radar-expand {
  0% { transform: scale(0.9); opacity: 0.8; }
  100% { transform: scale(1.6); opacity: 0; }
}

/* 同步日志控制台 */
.action-terminal {
  height: 180px;
  background: #0b1120;
  border-top: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
}

.terminal-header {
  padding: 8px 16px;
  background: #0f172a;
  border-bottom: 1px solid #1e293b;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.terminal-body {
  flex: 1;
  padding: 8px 16px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 11px;
  line-height: 1.6;
}

.terminal-line {
  margin-bottom: 2px;
  display: flex;
  gap: 6px;
  align-items: flex-start;
  word-break: break-all;
}

.line-time {
  color: #64748b;
  flex-shrink: 0;
}

.line-tag {
  flex-shrink: 0;
}

.line-msg {
  color: #cbd5e1;
}
</style>
<style>
/* 抽屉无 padding 样式适配 */
.manus-preview-drawer .el-drawer__body {
  padding: 0 !important;
  overflow: hidden !important;
}
</style>
