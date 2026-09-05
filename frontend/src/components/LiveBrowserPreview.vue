<template>
  <div>
    <!-- 右下角常驻悬浮控制按钮 (极简精致的浮动胶囊，告别花哨杂色) -->
    <button
      v-if="!visible"
      type="button"
      @click="visible = true"
      class="fixed right-6 bottom-6 z-40 flex items-center gap-2 rounded-full border border-border bg-background/95 px-3.5 py-2 shadow-lg backdrop-blur-sm hover:bg-muted transition-all select-none group text-foreground cursor-pointer"
      :class="{ 'border-emerald-500/50 ring-2 ring-emerald-500/20': isLive }"
      title="点击展开受控浏览器实时视窗"
    >
      <span class="relative flex h-2 w-2">
        <span v-if="isLive" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
        <span class="relative inline-flex h-2 w-2 rounded-full" :class="isLive ? 'bg-emerald-500' : 'bg-muted-foreground/40'"></span>
      </span>
      <Monitor class="h-4 w-4 text-foreground" />
      <span class="text-xs font-medium text-foreground">实时视窗</span>
      <Badge v-if="isLive" variant="success" class="text-[9px] px-1 py-0 h-4">
        LIVE
      </Badge>
    </button>

    <!-- 侧边推拉视窗抽屉 (采用官方 shadcn Sheet 架构) -->
    <Sheet v-model:open="visible">
      <SheetContent
        side="right"
        :class="[
          'p-0 flex flex-col gap-0 border-l border-border bg-background transition-all duration-300',
          isExpanded ? 'w-full sm:max-w-4xl' : 'w-full sm:max-w-2xl'
        ]"
      >
        <SheetTitle class="sr-only">受控浏览器实时视窗</SheetTitle>
        <SheetDescription class="sr-only">实时监控底层自动化浏览器的执行画面与流水日志</SheetDescription>

        <!-- 顶部导航栏 -->
        <div class="h-14 px-4 border-b border-border flex items-center justify-between bg-card flex-shrink-0">
          <div class="flex items-center gap-2.5 min-w-0 pr-2">
            <Monitor class="h-4 w-4 text-muted-foreground flex-shrink-0" />
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-foreground">受控浏览器视窗</span>
                <Badge v-if="isLive" variant="success" class="text-[10px] px-1.5 py-0 gap-1 font-mono">
                  <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  LIVE {{ fps > 0 ? `${fps} FPS` : '' }}
                </Badge>
                <Badge v-else-if="currentFrame" variant="secondary" class="text-[10px] px-1.5 py-0">
                  已暂停
                </Badge>
                <Badge v-else variant="outline" class="text-[10px] px-1.5 py-0 text-muted-foreground">
                  待命中
                </Badge>
              </div>
              <p class="text-[11px] text-muted-foreground truncate max-w-sm">
                {{ currentTitle || (isLive ? '正在执行自动化交互管线...' : '等待发布任务、扫码登录或巡检启动') }}
              </p>
            </div>
          </div>

          <!-- 工具控制按钮 (留出 pr-8 避开 SheetContent 自带的 DialogClose) -->
          <div class="flex items-center gap-1.5 pr-8">
            <Button
              variant="outline"
              size="sm"
              class="h-7 px-2 text-xs"
              :disabled="!currentFrame"
              @click="downloadSnapshot"
              title="保存当前画面快照"
            >
              <Camera class="h-3.5 w-3.5 mr-1" />
              <span>快照</span>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              class="h-7 w-7 p-0"
              @click="isExpanded = !isExpanded"
              :title="isExpanded ? '还原宽度' : '展开视窗'"
            >
              <component :is="isExpanded ? Minimize2 : Maximize2" class="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        <!-- 模拟浏览器地址栏 (Omnibox) -->
        <div class="p-2.5 px-4 bg-muted/40 border-b border-border flex items-center gap-3 flex-shrink-0 text-xs">
          <!-- 窗口三色圆点 (微精致修饰，克制不花哨) -->
          <div class="flex items-center gap-1.5 flex-shrink-0">
            <span class="h-2.5 w-2.5 rounded-full bg-border"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-border"></span>
            <span class="h-2.5 w-2.5 rounded-full bg-border"></span>
          </div>

          <!-- URL 地址展示栏 -->
          <div class="flex-1 min-w-0 flex items-center gap-1.5 bg-background border border-border rounded-md px-2.5 py-1 font-mono text-[11px] text-muted-foreground">
            <Lock class="h-3 w-3 text-muted-foreground flex-shrink-0" />
            <span class="truncate select-all text-foreground">{{ currentUrl || 'about:blank' }}</span>
          </div>

          <Button
            v-if="currentUrl"
            variant="ghost"
            size="sm"
            class="h-7 px-2 text-xs text-muted-foreground hover:text-foreground flex-shrink-0"
            @click="copyUrl"
            title="复制当前页面地址"
          >
            <Copy class="h-3.5 w-3.5 mr-1" />
            <span>复制</span>
          </Button>
        </div>

        <!-- 画面呈现核心视口区 -->
        <div class="flex-1 bg-zinc-950 relative flex items-center justify-center p-4 overflow-hidden min-h-[320px]">
          <!-- 正在串流时的图像画面 -->
          <div v-if="currentFrame" class="relative w-full h-full flex items-center justify-center">
            <img
              :src="'data:image/jpeg;base64,' + currentFrame"
              alt="Live Screen"
              class="max-w-full max-h-full object-contain rounded border border-zinc-800 shadow-md select-none"
            />

            <!-- 底部浮动动作提示 HUD -->
            <div
              v-if="lastAction"
              class="absolute bottom-3 left-1/2 -translate-x-1/2 bg-zinc-900/90 border border-zinc-700/80 rounded-full px-3.5 py-1 flex items-center gap-2 max-w-[90%] shadow-lg backdrop-blur-sm"
            >
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping flex-shrink-0"></span>
              <span class="text-[11px] text-zinc-200 font-medium truncate" :title="lastAction">
                {{ lastAction }}
              </span>
            </div>
          </div>

          <!-- 空闲待命时的官方极简占位 (无任何伪科幻雷达花里胡哨) -->
          <div v-else class="flex flex-col items-center justify-center text-center p-8 max-w-sm">
            <div class="h-12 w-12 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-500 mb-3">
              <Globe class="h-6 w-6" />
            </div>
            <h3 class="text-sm font-semibold text-zinc-300">自动化视窗待命中</h3>
            <p class="text-xs text-zinc-500 mt-1.5 leading-relaxed">
              当发起矩阵视频发布、账号扫码授权或平台数据巡检时，此处将低时延实时串流展示底层 Chrome 的操作画面。
            </p>
          </div>
        </div>

        <!-- 底部动作流水控制台 -->
        <div class="h-48 border-t border-border bg-zinc-950 flex flex-col flex-shrink-0">
          <div class="p-2 px-4 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between text-xs">
            <span class="font-mono text-[11px] text-zinc-400">
              ACTION STREAM ({{ logs.length }})
            </span>
            <div class="flex items-center gap-2">
              <button
                type="button"
                :class="[
                  'text-[10px] px-1.5 py-0.5 rounded transition-colors cursor-pointer',
                  autoScroll ? 'bg-zinc-800 text-zinc-200' : 'text-zinc-500 hover:text-zinc-300'
                ]"
                @click="autoScroll = !autoScroll"
              >
                自动滚屏: {{ autoScroll ? '开' : '关' }}
              </button>
              <button
                v-if="logs.length > 0"
                type="button"
                class="text-[10px] text-zinc-500 hover:text-zinc-300 cursor-pointer"
                @click="logs = []"
              >
                清空
              </button>
            </div>
          </div>

          <div ref="terminalRef" class="flex-1 p-2.5 px-4 overflow-y-auto font-mono text-[11px] space-y-1 select-text leading-relaxed">
            <div v-if="logs.length === 0" class="text-zinc-600 text-xs py-4 text-center">
              等待底层动作流水注入...
            </div>
            <div
              v-for="(log, idx) in logs"
              :key="idx"
              class="flex items-start gap-2 hover:bg-zinc-900/50 px-1 py-0.5 rounded"
            >
              <span class="text-zinc-500 flex-shrink-0">[{{ log.time }}]</span>
              <span :class="['font-bold flex-shrink-0', getLogLevelClass(log.level)]">[{{ log.level }}]</span>
              <span class="text-zinc-300 break-all">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue"
import { ElMessage } from "element-plus"
import {
  Monitor, Maximize2, Minimize2, Camera, Lock, Copy, Globe
} from "lucide-vue-next"

import { Sheet, SheetContent, SheetTitle, SheetDescription } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const visible = ref(false)
const isExpanded = ref(false)
const autoScroll = ref(true)

const currentFrame = ref<string | null>(null)
const currentTitle = ref<string>("")
const currentUrl = ref<string>("")
const lastAction = ref<string>("")
const logs = ref<any[]>([])

const frameCount = ref(0)
const fps = ref(0)
let fpsTimer: any = null

const lastFrameTime = ref(0)
const isLive = computed(() => {
  return Date.now() - lastFrameTime.value < 4000
})

const terminalRef = ref<HTMLElement | null>(null)

const downloadSnapshot = () => {
  if (!currentFrame.value) return
  const link = document.createElement("a")
  link.download = `matrixhub-browser-${Date.now()}.jpg`
  link.href = "data:image/jpeg;base64," + currentFrame.value
  link.click()
  ElMessage.success("画面快照已下载！")
}

const copyUrl = () => {
  if (!currentUrl.value) return
  navigator.clipboard.writeText(currentUrl.value).then(() => {
    ElMessage.success("页面地址已复制！")
  }).catch(() => {
    ElMessage.warning("复制失败")
  })
}

const getLogLevelClass = (level: string) => {
  switch (level) {
    case "SUCCESS": return "text-emerald-400"
    case "ERROR": return "text-rose-400"
    case "WARNING": return "text-amber-400"
    default: return "text-sky-400"
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
        setTimeout(() => {
          if (Date.now() - lastFrameTime.value >= 4000) {
            currentFrame.value = null
            currentTitle.value = ""
            currentUrl.value = ""
          }
        }, 4000)
      } else if (msg.event === "log_append") {
        lastAction.value = msg.data.message
        // 正常时间正序追加 (最新消息在底部)
        logs.value.push(msg.data)
        if (logs.value.length > 200) logs.value.shift()

        if (autoScroll.value) {
          nextTick(() => {
            if (terminalRef.value) {
              terminalRef.value.scrollTop = terminalRef.value.scrollHeight
            }
          })
        }
      }
    } catch (e) {}
  }

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000)
  }
}

const handleOpenLive = () => {
  visible.value = true
}

onMounted(() => {
  window.addEventListener("open-live-browser", handleOpenLive)
  initWebSocket()
  fpsTimer = setInterval(() => {
    fps.value = frameCount.value
    frameCount.value = 0
  }, 1000)
})

onUnmounted(() => {
  window.removeEventListener("open-live-browser", handleOpenLive)
  if (fpsTimer) clearInterval(fpsTimer)
  if (ws) ws.close()
})
</script>
