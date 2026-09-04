<template>
  <div class="settings-container">
    <el-card shadow="never" class="mb-4">
      <div class="font-bold text-lg mb-1">系统全局设置</div>
      <div class="text-sm text-gray-500">配置调度错峰防风控策略与外部协作告警机器人</div>
    </el-card>

    <el-form :model="settings" label-width="180px" v-loading="loading" style="max-width: 800px;">
      <!-- 调度与并发参数 -->
      <el-card shadow="never" class="mb-4">
        <template #header>
          <span class="font-bold">防风控与调度策略</span>
        </template>

        <el-form-item label="浏览器最大并发数">
          <el-input-number v-model="settings.max_concurrency" :min="1" :max="5" />
          <div class="text-xs text-gray-400 mt-1">
            建议单机保持为 1~2 个并发实例，避免占用过多内存与 CPU，同时降低多账号同 IP 触发风控概率
          </div>
        </el-form-item>

        <el-form-item label="默认错峰基础间隔 (秒)">
          <el-input-number v-model="settings.stagger_interval" :min="30" :max="3600" :step="60" />
          <div class="text-xs text-gray-400 mt-1">每个账号发布之间的排队基础延迟（默认 300 秒，即 5 分钟）</div>
        </el-form-item>

        <el-form-item label="错峰随机扰动时间 (秒)">
          <el-input-number v-model="settings.stagger_jitter" :min="0" :max="300" :step="10" />
          <div class="text-xs text-gray-400 mt-1">为基础间隔增加 ±N 秒的随机波动，模拟人工不规律操作</div>
        </el-form-item>
      </el-card>

      <!-- Webhook 告警机器人 -->
      <el-card shadow="never" class="mb-4">
        <template #header>
          <span class="font-bold">Webhook 消息通知机器人</span>
        </template>

        <el-form-item label="通知机器人平台">
          <el-radio-group v-model="settings.webhook_channel">
            <el-radio label="feishu">飞书群机器人</el-radio>
            <el-radio label="dingtalk">钉钉群机器人</el-radio>
            <el-radio label="wecom">企业微信群机器人</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="Webhook 完整 URL">
          <el-input v-model="settings.webhook_url" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
          <div class="text-xs text-gray-400 mt-1">
            在任务全部发布完成、遇到严重异常或登录态过期时，系统将主动向群聊发送卡片提醒
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="info" :loading="testing" @click="handleTestWebhook">测试 Webhook 连通性</el-button>
        </el-form-item>
      </el-card>

      <!-- 保存操作 -->
      <div class="flex justify-end">
        <el-button type="primary" size="large" :loading="saving" @click="handleSave">
          保存全部系统配置
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { ElMessage } from "element-plus"
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
    ElMessage.success(res.message)
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
    ElMessage.success("系统配置保存成功！")
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

<style scoped>
.settings-container { padding: 10px 0; }
.mb-1 { margin-bottom: 4px; }
.mb-4 { margin-bottom: 16px; }
.mt-1 { margin-top: 4px; }
.flex { display: flex; }
.justify-end { justify-content: flex-end; }
.font-bold { font-weight: 600; }
.text-lg { font-size: 18px; }
.text-sm { font-size: 14px; }
.text-xs { font-size: 12px; }
.text-gray-400 { color: #94a3b8; }
.text-gray-500 { color: #64748b; }
</style>
