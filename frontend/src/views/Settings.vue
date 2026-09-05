<template>
  <div class="space-y-6 max-w-4xl mx-auto pb-16">
    <!-- 顶栏：标题 -->
    <div>
      <h1 class="text-xl font-bold tracking-tight text-foreground">系统全局设置</h1>
      <p class="text-xs text-muted-foreground mt-0.5">
        配置 Playwright 自动化浏览器引擎并发、阶梯错峰防风控与外部协同 Webhook
      </p>
    </div>

    <div v-if="loading" class="py-20 text-center text-muted-foreground">
      <RefreshCw class="w-7 h-7 mx-auto mb-2 animate-spin text-primary opacity-60" />
      <p class="text-xs">正在加载系统配置参数...</p>
    </div>

    <div v-else class="space-y-5">
      <!-- 卡片 1：防风控与自动化调度策略 -->
      <Card>
        <CardHeader class="pb-3 border-b border-border">
          <CardTitle class="text-sm font-semibold">自动化引擎与防风控策略</CardTitle>
          <CardDescription class="text-xs">
            控制浏览器多开并发与账号阶梯错峰排期，规避多账号同局域网关联风险
          </CardDescription>
        </CardHeader>

        <CardContent class="p-6 space-y-6">
          <!-- 浏览器最大并发数 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <label class="text-xs font-medium text-foreground">浏览器最大并发数</label>
                <p class="text-[11px] text-muted-foreground">同一时刻允许启动的最大独立无痕浏览器实例数</p>
              </div>
              <span class="text-xs font-mono text-muted-foreground">当前: {{ settings.max_concurrency }} 进程</span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 max-w-md">
              <button
                v-for="num in [1, 2, 3, 4, 5]"
                :key="num"
                type="button"
                :class="[
                  'p-2.5 rounded-md border text-center transition-colors text-xs font-medium',
                  settings.max_concurrency === num
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-card hover:bg-muted/40 text-foreground'
                ]"
                @click="settings.max_concurrency = num"
              >
                <div>{{ num }} 个实例</div>
                <div v-if="num <= 2" class="text-[10px] text-muted-foreground mt-0.5">推荐</div>
                <div v-else class="text-[10px] text-muted-foreground mt-0.5">需高配置</div>
              </button>
            </div>
            <p class="text-[11px] text-muted-foreground">
              建议单机保持 1~2 个并发，既能保证任务稳定，又能降低平台风控感知。
            </p>
          </div>

          <div class="pt-2 border-t border-border"></div>

          <!-- 默认错峰基础间隔 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <label class="text-xs font-medium text-foreground">默认错峰基础间隔</label>
                <p class="text-[11px] text-muted-foreground">多账号依次发布时的等待基准时间</p>
              </div>
              <span class="text-xs font-mono text-muted-foreground">
                {{ settings.stagger_interval }} 秒 ({{ Math.round(settings.stagger_interval / 60) }} 分钟)
              </span>
            </div>

            <div class="flex items-center gap-2 max-w-xs">
              <Input
                type="number"
                v-model.number="settings.stagger_interval"
                min="30"
                max="3600"
                step="30"
                class="h-8 text-xs font-mono"
              />
              <span class="text-xs text-muted-foreground">秒</span>
            </div>

            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-[11px] text-muted-foreground">预设:</span>
              <button
                v-for="preset in [
                  { label: '1分钟', sec: 60 },
                  { label: '3分钟', sec: 180 },
                  { label: '5分钟 (标准)', sec: 300 },
                  { label: '10分钟', sec: 600 }
                ]"
                :key="preset.sec"
                type="button"
                :class="[
                  'text-[11px] px-2 py-0.5 rounded border transition-colors',
                  settings.stagger_interval === preset.sec
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-muted/30 text-muted-foreground hover:text-foreground'
                ]"
                @click="settings.stagger_interval = preset.sec"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>

          <div class="pt-2 border-t border-border"></div>

          <!-- 错峰随机扰动时间 -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <label class="text-xs font-medium text-foreground">错峰随机扰动浮动时间</label>
                <p class="text-[11px] text-muted-foreground">在基础间隔上增加 ±N 秒的随机波动，模拟人工行为</p>
              </div>
              <span class="text-xs font-mono text-muted-foreground">±{{ settings.stagger_jitter }} 秒</span>
            </div>

            <div class="flex items-center gap-2 max-w-xs">
              <Input
                type="number"
                v-model.number="settings.stagger_jitter"
                min="0"
                max="300"
                step="10"
                class="h-8 text-xs font-mono"
              />
              <span class="text-xs text-muted-foreground">秒</span>
            </div>

            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="text-[11px] text-muted-foreground">扰动:</span>
              <button
                v-for="sec in [0, 30, 60, 120]"
                :key="sec"
                type="button"
                :class="[
                  'text-[11px] px-2 py-0.5 rounded border transition-colors',
                  settings.stagger_jitter === sec
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-muted/30 text-muted-foreground hover:text-foreground'
                ]"
                @click="settings.stagger_jitter = sec"
              >
                ±{{ sec }}秒 {{ sec === 0 ? '(固定)' : '' }}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 卡片 2：Webhook 通知机器人 -->
      <Card>
        <CardHeader class="pb-3 border-b border-border">
          <CardTitle class="text-sm font-semibold">Webhook 通知机器人</CardTitle>
          <CardDescription class="text-xs">
            任务完成、异常或登录态过期时，自动向群聊推送通知
          </CardDescription>
        </CardHeader>

        <CardContent class="p-6 space-y-4">
          <!-- 平台选择 -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">机器人平台</label>
            <div class="flex gap-2.5 max-w-md">
              <button
                v-for="ch in [
                  { label: '飞书群机器人', value: 'feishu' },
                  { label: '钉钉群机器人', value: 'dingtalk' },
                  { label: '企业微信', value: 'wecom' }
                ]"
                :key="ch.value"
                type="button"
                :class="[
                  'flex-1 p-2.5 rounded-md border text-center transition-colors text-xs font-medium',
                  settings.webhook_channel === ch.value
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-card hover:bg-muted/30 text-foreground'
                ]"
                @click="settings.webhook_channel = ch.value"
              >
                {{ ch.label }}
              </button>
            </div>
          </div>

          <!-- Webhook URL -->
          <div class="space-y-1.5 max-w-xl">
            <label class="text-xs font-medium text-foreground">Webhook 完整 URL</label>
            <div class="flex gap-2">
              <Input
                v-model="settings.webhook_url"
                :placeholder="getPlaceholder(settings.webhook_channel)"
                class="font-mono text-xs h-9"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                :disabled="testing || !settings.webhook_url"
                class="h-9 flex-shrink-0"
                @click="handleTestWebhook"
              >
                <Send :class="['w-3.5 h-3.5 mr-1', testing ? 'animate-pulse' : '']" />
                <span>{{ testing ? "测试中" : "测试连通性" }}</span>
              </Button>
            </div>
            <p class="text-[11px] text-muted-foreground">
              在群聊中添加自定义机器人后，将 Webhook 完整地址粘贴至此处。
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- 底部操作按钮 -->
      <div class="flex justify-end pt-2">
        <Button
          type="button"
          variant="default"
          size="default"
          :disabled="saving"
          @click="handleSave"
        >
          <Save class="w-4 h-4 mr-1.5" />
          <span>{{ saving ? "正在保存..." : "保存配置" }}</span>
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import {
  RefreshCw, Send, Save
} from "lucide-vue-next"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

import { getSettings, updateSettings, testWebhook } from "../api"

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

const settings = ref({
  max_concurrency: 1,
  stagger_interval: 300,
  stagger_jitter: 60,
  webhook_channel: "feishu",
  webhook_url: ""
})

const getPlaceholder = (channel: string) => {
  switch (channel) {
    case "feishu": return "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    case "dingtalk": return "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    case "wecom": return "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    default: return "输入 Webhook URL"
  }
}

const loadSettings = async () => {
  loading.value = true
  try {
    const res: any = await getSettings()
    const data = res.data || {}
    settings.value = {
      max_concurrency: Number(data.max_concurrency) || 1,
      stagger_interval: Number(data.stagger_interval) || 300,
      stagger_jitter: Number(data.stagger_jitter) || 60,
      webhook_channel: data.webhook_channel || "feishu",
      webhook_url: data.webhook_url || ""
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

const handleTestWebhook = async () => {
  if (!settings.value.webhook_url) {
    ElMessage.warning("请先填写 Webhook URL")
    return
  }
  testing.value = true
  try {
    const res: any = await testWebhook({
      webhook_url: settings.value.webhook_url,
      channel: settings.value.webhook_channel
    })
    ElMessage.success(res.message || "Webhook 测试消息发送成功！")
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    testing.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const payload: Record<string, string> = {
      max_concurrency: String(settings.value.max_concurrency),
      stagger_interval: String(settings.value.stagger_interval),
      stagger_jitter: String(settings.value.stagger_jitter),
      webhook_channel: settings.value.webhook_channel,
      webhook_url: settings.value.webhook_url
    }
    await updateSettings(payload)
    ElMessage.success("系统全局配置保存成功！")
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
