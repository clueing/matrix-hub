<template>
  <div class="space-y-6 max-w-5xl mx-auto pb-16">
    <!-- 顶栏：标题 -->
    <Card class="border-border/60 bg-gradient-to-r from-card via-card to-primary/[0.03] shadow-sm">
      <CardContent class="p-6">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-xl bg-primary/10 text-primary">
            <SlidersHorizontal class="w-6 h-6" />
          </div>
          <div>
            <h1 class="text-xl font-bold tracking-tight text-foreground">系统全局设置</h1>
            <p class="text-xs text-muted-foreground">
              配置 Playwright 自动化浏览器引擎、阶梯错峰防风控算法与企业外部协同 Webhook
            </p>
          </div>
        </div>
      </CardContent>
    </Card>

    <div v-if="loading" class="py-20 text-center text-muted-foreground">
      <RefreshCw class="w-8 h-8 mx-auto mb-2 animate-spin text-primary opacity-60" />
      <p class="text-sm">正在加载系统配置参数...</p>
    </div>

    <div v-else class="space-y-6">
      <!-- 卡片 1：防风控与自动化调度策略 -->
      <Card class="border-border/60 shadow-sm">
        <CardHeader class="pb-4 border-b border-border/40">
          <div class="flex items-center gap-2">
            <ShieldCheck class="w-5 h-5 text-emerald-600" />
            <div>
              <CardTitle class="text-base font-semibold">自动化引擎与防风控策略</CardTitle>
              <CardDescription class="text-xs">
                精细控制浏览器多开并发与阶梯错峰排期，规避多账号同局域网关联风险
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent class="p-6 space-y-6">
          <!-- 浏览器最大并发数 -->
          <div class="space-y-2.5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <label class="text-sm font-semibold text-foreground">浏览器最大并发数</label>
                <p class="text-xs text-muted-foreground">同一时刻允许启动的最大独立无痕浏览器实例数</p>
              </div>
              <Badge variant="secondary" class="text-xs font-mono self-start sm:self-auto">
                当前: {{ settings.max_concurrency }} 进程
              </Badge>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5 max-w-xl">
              <button
                v-for="num in [1, 2, 3, 4, 5]"
                :key="num"
                type="button"
                :class="[
                  'p-3 rounded-xl border text-center transition-all flex flex-col items-center justify-center gap-1',
                  settings.max_concurrency === num
                    ? 'border-primary bg-primary/[0.06] text-primary font-bold shadow-sm ring-1 ring-primary/40'
                    : 'border-border/80 bg-card hover:bg-muted/40 text-foreground'
                ]"
                @click="settings.max_concurrency = num"
              >
                <span class="text-base">{{ num }} 个实例</span>
                <span v-if="num <= 2" class="text-[10px] text-emerald-600 font-medium">推荐 (安全)</span>
                <span v-else class="text-[10px] text-amber-600 font-medium">需高配置</span>
              </button>
            </div>
            <p class="text-[11px] text-muted-foreground/80 max-w-2xl">
              💡 <strong>运营建议</strong>：单机保持 1~2 个并发最佳，既能保证任务高效平稳进行，又能显著降低平台风控算法对短时间内多账号集中请求的关联感知。
            </p>
          </div>

          <div class="pt-2 border-t border-border/40"></div>

          <!-- 默认错峰基础间隔 -->
          <div class="space-y-2.5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <label class="text-sm font-semibold text-foreground">默认错峰基础间隔</label>
                <p class="text-xs text-muted-foreground">多账号发布时的递增排队等待基准时间</p>
              </div>
              <Badge variant="secondary" class="text-xs font-mono self-start sm:self-auto">
                {{ settings.stagger_interval }} 秒 ({{ Math.round(settings.stagger_interval / 60) }} 分钟)
              </Badge>
            </div>

            <div class="flex items-center gap-3 max-w-md">
              <Input
                type="number"
                v-model.number="settings.stagger_interval"
                min="30"
                max="3600"
                step="30"
                class="h-9 font-mono"
              />
              <span class="text-xs text-muted-foreground flex-shrink-0">秒</span>
            </div>

            <!-- 快捷预设按钮 -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[11px] text-muted-foreground">常用预设:</span>
              <button
                v-for="preset in [
                  { label: '1分钟 (测试)', sec: 60 },
                  { label: '3分钟 (轻量)', sec: 180 },
                  { label: '5分钟 (标准)', sec: 300 },
                  { label: '10分钟 (高防护)', sec: 600 }
                ]"
                :key="preset.sec"
                type="button"
                :class="[
                  'text-xs px-2.5 py-1 rounded-md border transition',
                  settings.stagger_interval === preset.sec
                    ? 'bg-primary/10 border-primary/40 text-primary font-medium'
                    : 'bg-muted/40 hover:bg-muted border-border/60 text-muted-foreground'
                ]"
                @click="settings.stagger_interval = preset.sec"
              >
                {{ preset.label }}
              </button>
            </div>
          </div>

          <div class="pt-2 border-t border-border/40"></div>

          <!-- 错峰随机扰动时间 -->
          <div class="space-y-2.5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
              <div>
                <label class="text-sm font-semibold text-foreground">错峰随机扰动浮动时间</label>
                <p class="text-xs text-muted-foreground">在基础间隔上增加 ±N 秒的随机波动，模拟自然人类不规律行为</p>
              </div>
              <Badge variant="secondary" class="text-xs font-mono self-start sm:self-auto">
                ±{{ settings.stagger_jitter }} 秒
              </Badge>
            </div>

            <div class="flex items-center gap-3 max-w-md">
              <Input
                type="number"
                v-model.number="settings.stagger_jitter"
                min="0"
                max="300"
                step="10"
                class="h-9 font-mono"
              />
              <span class="text-xs text-muted-foreground flex-shrink-0">秒</span>
            </div>

            <!-- 快捷预设按钮 -->
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-[11px] text-muted-foreground">常用扰动:</span>
              <button
                v-for="sec in [0, 30, 60, 120]"
                :key="sec"
                type="button"
                :class="[
                  'text-xs px-2.5 py-1 rounded-md border transition',
                  settings.stagger_jitter === sec
                    ? 'bg-primary/10 border-primary/40 text-primary font-medium'
                    : 'bg-muted/40 hover:bg-muted border-border/60 text-muted-foreground'
                ]"
                @click="settings.stagger_jitter = sec"
              >
                ±{{ sec }}秒 {{ sec === 0 ? '(固定)' : '' }}
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 卡片 2：Webhook 外部协作与报警机器人 -->
      <Card class="border-border/60 shadow-sm">
        <CardHeader class="pb-4 border-b border-border/40">
          <div class="flex items-center gap-2">
            <BellRing class="w-5 h-5 text-indigo-500" />
            <div>
              <CardTitle class="text-base font-semibold">Webhook 协同通知机器人</CardTitle>
              <CardDescription class="text-xs">
                任务全部发布完成、遇到严重异常或登录凭证过期时，自动向工作群推送卡片通知
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent class="p-6 space-y-6">
          <!-- 通知机器人平台 -->
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground">通知机器人通道</label>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-xl">
              <div
                :class="[
                  'p-3.5 rounded-xl border transition-all cursor-pointer select-none flex items-center gap-3',
                  settings.webhook_channel === 'feishu'
                    ? 'border-primary bg-primary/[0.06] text-primary ring-1 ring-primary/30'
                    : 'border-border/80 bg-card hover:bg-muted/30 text-foreground'
                ]"
                @click="settings.webhook_channel = 'feishu'"
              >
                <div class="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-600 flex items-center justify-center font-bold text-xs">
                  飞
                </div>
                <div>
                  <div class="text-xs font-bold">飞书群机器人</div>
                  <div class="text-[10px] text-muted-foreground">Lark / Feishu Bot</div>
                </div>
              </div>

              <div
                :class="[
                  'p-3.5 rounded-xl border transition-all cursor-pointer select-none flex items-center gap-3',
                  settings.webhook_channel === 'dingtalk'
                    ? 'border-primary bg-primary/[0.06] text-primary ring-1 ring-primary/30'
                    : 'border-border/80 bg-card hover:bg-muted/30 text-foreground'
                ]"
                @click="settings.webhook_channel = 'dingtalk'"
              >
                <div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 flex items-center justify-center font-bold text-xs">
                  钉
                </div>
                <div>
                  <div class="text-xs font-bold">钉钉群机器人</div>
                  <div class="text-[10px] text-muted-foreground">DingTalk Bot</div>
                </div>
              </div>

              <div
                :class="[
                  'p-3.5 rounded-xl border transition-all cursor-pointer select-none flex items-center gap-3',
                  settings.webhook_channel === 'wecom'
                    ? 'border-primary bg-primary/[0.06] text-primary ring-1 ring-primary/30'
                    : 'border-border/80 bg-card hover:bg-muted/30 text-foreground'
                ]"
                @click="settings.webhook_channel = 'wecom'"
              >
                <div class="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 flex items-center justify-center font-bold text-xs">
                  企
                </div>
                <div>
                  <div class="text-xs font-bold">企业微信群机器人</div>
                  <div class="text-[10px] text-muted-foreground">WeCom Bot</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Webhook URL -->
          <div class="space-y-2">
            <label class="text-sm font-semibold text-foreground">Webhook 完整请求 URL</label>
            <div class="flex flex-col sm:flex-row gap-2 max-w-2xl">
              <Input
                v-model="settings.webhook_url"
                :placeholder="getPlaceholder(settings.webhook_channel)"
                class="font-mono text-xs"
              />
              <Button
                type="button"
                variant="outline"
                size="default"
                :disabled="testing || !settings.webhook_url"
                class="flex-shrink-0"
                @click="handleTestWebhook"
              >
                <Send :class="['w-3.5 h-3.5 mr-1.5', testing ? 'animate-pulse' : '']" />
                <span>{{ testing ? "测试连通中..." : "测试连通性" }}</span>
              </Button>
            </div>
            <p class="text-[11px] text-muted-foreground">
              在群聊中添加自定义机器人后，将生成的 Webhook 完整地址粘贴至此处。
            </p>
          </div>
        </CardContent>
      </Card>

      <!-- 底部操作按钮 -->
      <div class="flex justify-end pt-2">
        <Button
          type="button"
          variant="default"
          size="lg"
          :disabled="saving"
          class="shadow-md"
          @click="handleSave"
        >
          <Save class="w-4 h-4 mr-2" />
          <span>{{ saving ? "正在保存配置..." : "保存全部系统配置" }}</span>
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
import {
  SlidersHorizontal, ShieldCheck, BellRing, RefreshCw, Send, Save
} from "lucide-vue-next"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
    case "feishu": return "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx"
    case "dingtalk": return "https://oapi.dingtalk.com/robot/send?access_token=xxxxxx"
    case "wecom": return "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx"
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
