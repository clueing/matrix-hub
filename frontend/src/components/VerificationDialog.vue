<template>
  <Dialog :open="visible" @update:open="handleDialogOpenChange">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <div class="flex items-center gap-2 mb-1">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck class="h-4 w-4" />
          </div>
          <DialogTitle class="text-base font-semibold text-foreground">
            二次安全验证
          </DialogTitle>
        </div>
        <DialogDescription class="text-xs text-muted-foreground">
          发布平台触发了手机短信二次验证，请输入接收到的 6 位验证码以继续完成发布
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-4 py-2">
        <!-- 账号与发布作品信息条 -->
        <div class="rounded-lg border border-border bg-muted/40 p-3 space-y-2 text-xs">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Badge variant="outline" class="text-[10px] px-1.5 py-0 font-medium uppercase">
                {{ currentPlatform === 'xiaohongshu' ? '小红书' : '抖音' }}
              </Badge>
              <span class="font-medium text-foreground truncate max-w-[180px]">
                {{ accountName || '未知账号' }}
              </span>
            </div>
            <span v-if="phone" class="font-mono text-muted-foreground text-[11px]">
              {{ phone }}
            </span>
          </div>

          <div v-if="workTitle" class="text-muted-foreground truncate" :title="workTitle">
            作品：<span class="text-foreground font-medium">《{{ workTitle }}》</span>
          </div>

          <div class="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 text-[11px]">
            <Smartphone class="h-3.5 w-3.5 flex-shrink-0" />
            <span>已自动触发短信下发，请查收手机短信验证码</span>
          </div>
        </div>

        <!-- 错误提示提示条 -->
        <div
          v-if="errorMessage"
          class="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-2.5 text-xs text-destructive animate-in fade-in duration-200"
        >
          <AlertCircle class="h-4 w-4 flex-shrink-0" />
          <span class="leading-tight">{{ errorMessage }}</span>
        </div>

        <!-- 验证成功提示条 -->
        <div
          v-if="isSuccess"
          class="flex items-center gap-2 rounded-md bg-emerald-500/10 border border-emerald-500/20 p-2.5 text-xs text-emerald-600 dark:text-emerald-400 animate-in fade-in duration-200"
        >
          <CheckCircle2 class="h-4 w-4 flex-shrink-0" />
          <span class="font-medium">验证码校验通过，正在自动推进视频发布...</span>
        </div>

        <!-- 6 位验证码输入格子 -->
        <div class="space-y-2">
          <div class="flex justify-between items-center text-xs">
            <label class="font-medium text-foreground">短信验证码 (6 位数字)</label>
            <!-- 倒计时 / 重新获取 -->
            <button
              type="button"
              :disabled="countdown > 0 || resending || isSuccess"
              @click="handleResend"
              class="text-xs text-primary hover:underline disabled:text-muted-foreground disabled:no-underline font-medium cursor-pointer transition-colors"
            >
              <span v-if="resending" class="flex items-center gap-1">
                <RefreshCw class="h-3 w-3 animate-spin" />
                正在重发...
              </span>
              <span v-else-if="countdown > 0">
                {{ countdown }}s 后可重新获取
              </span>
              <span v-else>
                重新获取验证码
              </span>
            </button>
          </div>

          <!-- 6 个方格输入框 -->
          <div class="flex items-center justify-between gap-2">
            <input
              v-for="(_, index) in 6"
              :key="index"
              :ref="el => digitInputs[index] = el as HTMLInputElement"
              type="text"
              inputmode="numeric"
              maxlength="1"
              :disabled="submitting || isSuccess"
              :value="digits[index]"
              @input="onDigitInput(index, $event)"
              @keydown="onDigitKeyDown(index, $event)"
              @paste="onDigitPaste"
              class="h-12 w-11 rounded-md border border-input bg-background text-center font-mono text-lg font-semibold text-foreground shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>
      </div>

      <DialogFooter class="flex sm:justify-between items-center gap-2 pt-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="submitting || isSuccess"
          @click="handleCancel"
          class="text-xs text-muted-foreground hover:text-destructive"
        >
          取消此作品发布
        </Button>

        <Button
          variant="default"
          size="sm"
          :disabled="!isCodeComplete || submitting || isSuccess"
          @click="handleSubmit"
          class="text-xs px-4"
        >
          <RefreshCw v-if="submitting" class="mr-1.5 h-3.5 w-3.5 animate-spin" />
          <span>{{ submitting ? '验证提交中...' : '提交验证' }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { ShieldCheck, Smartphone, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { verifySubtask } from '@/api'

const visible = ref(false)
const submitting = ref(false)
const resending = ref(false)
const isSuccess = ref(false)
const errorMessage = ref('')

const subtaskId = ref('')
const taskId = ref('')
const accountId = ref('')
const accountName = ref('')
const currentPlatform = ref('douyin')
const phone = ref('')
const workTitle = ref('')

// 6 位验证码状态
const digits = ref<string[]>(['', '', '', '', '', ''])
const digitInputs = ref<HTMLInputElement[]>([])

// 倒计时状态 (默认 60s)
const countdown = ref(60)
let timer: any = null

const startCountdown = (sec: number = 60) => {
  if (timer) clearInterval(timer)
  countdown.value = sec
  timer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--
    } else {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

const fullCode = computed(() => digits.value.join('').trim())
const isCodeComplete = computed(() => fullCode.value.length === 6)

const resetForm = () => {
  digits.value = ['', '', '', '', '', '']
  errorMessage.value = ''
  submitting.value = false
  isSuccess.value = false
}

const openWithData = (data: any) => {
  subtaskId.value = data.subtask_id || data.id || ''
  taskId.value = data.task_id || ''
  accountId.value = data.account_id || ''
  accountName.value = data.account_name || ''
  currentPlatform.value = data.platform || 'douyin'
  phone.value = data.phone || ''
  workTitle.value = data.title || data.work_title || ''

  resetForm()
  startCountdown(60)
  visible.value = true

  nextTick(() => {
    if (digitInputs.value[0]) {
      digitInputs.value[0].focus()
    }
  })
}

const handleDialogOpenChange = (val: boolean) => {
  if (!val && !isSuccess.value) {
    visible.value = false
  } else {
    visible.value = val
  }
}

// 6 格输入逻辑：键入数字自动跳往下一格
const onDigitInput = (index: number, event: Event) => {
  const input = event.target as HTMLInputElement
  const val = input.value.replace(/\D/g, '')

  if (val) {
    digits.value[index] = val.slice(-1)
    errorMessage.value = ''
    if (index < 5 && digitInputs.value[index + 1]) {
      digitInputs.value[index + 1].focus()
    }
  } else {
    digits.value[index] = ''
  }
}

// 6 格输入逻辑：按 Backspace 回退到上一格
const onDigitKeyDown = (index: number, event: KeyboardEvent) => {
  if (event.key === 'Backspace') {
    if (!digits.value[index] && index > 0 && digitInputs.value[index - 1]) {
      digits.value[index - 1] = ''
      digitInputs.value[index - 1].focus()
    } else {
      digits.value[index] = ''
    }
  } else if (event.key === 'ArrowLeft' && index > 0) {
    digitInputs.value[index - 1]?.focus()
  } else if (event.key === 'ArrowRight' && index < 5) {
    digitInputs.value[index + 1]?.focus()
  } else if (event.key === 'Enter' && isCodeComplete.value) {
    handleSubmit()
  }
}

// 6 格输入逻辑：粘贴 6 位验证码
const onDigitPaste = (event: ClipboardEvent) => {
  event.preventDefault()
  const pasted = event.clipboardData?.getData('text') || ''
  const cleanNumbers = pasted.replace(/\D/g, '').slice(0, 6)
  if (!cleanNumbers) return

  for (let i = 0; i < 6; i++) {
    digits.value[i] = cleanNumbers[i] || ''
  }
  errorMessage.value = ''

  const focusIdx = Math.min(cleanNumbers.length, 5)
  nextTick(() => {
    digitInputs.value[focusIdx]?.focus()
    if (cleanNumbers.length === 6) {
      handleSubmit()
    }
  })
}

// 重新获取短信验证码
const handleResend = async () => {
  if (!subtaskId.value || countdown.value > 0 || resending.value) return
  resending.value = true
  errorMessage.value = ''
  try {
    const res: any = await verifySubtask(subtaskId.value, { action: 'resend' })
    ElMessage.success(res.message || '已向后台请求重新发送验证码')
    startCountdown(60)
  } catch (e: any) {
    errorMessage.value = e.message || '重新获取验证码失败'
  } finally {
    resending.value = false
  }
}

// 取消发布
const handleCancel = async () => {
  if (!subtaskId.value) {
    visible.value = false
    return
  }
  try {
    await verifySubtask(subtaskId.value, { action: 'cancel' })
    ElMessage.info('已取消本次验证与发布任务')
  } catch (e) {}
  visible.value = false
}

// 提交验证码
const handleSubmit = async () => {
  if (!subtaskId.value || !isCodeComplete.value || submitting.value) return
  submitting.value = true
  errorMessage.value = ''

  try {
    const res: any = await verifySubtask(subtaskId.value, {
      code: fullCode.value,
      action: 'submit'
    })
    ElMessage.info(res.message || '验证码已下发后台校验...')
  } catch (e: any) {
    errorMessage.value = e.message || '提交验证码失败'
    submitting.value = false
  }
}

// WebSocket 监听
let ws: WebSocket | null = null

const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)

      // 触发二次安全验证弹窗
      if (msg.event === 'verification_required') {
        console.log('[VerificationDialog] Received verification_required:', msg.data)
        openWithData(msg.data)
      }
      // 验证码错误
      else if (msg.event === 'verification_failed') {
        if (msg.data.subtask_id === subtaskId.value) {
          submitting.value = false
          errorMessage.value = msg.data.error || '验证码不正确或已失效，请重新输入'
          digits.value = ['', '', '', '', '', '']
          nextTick(() => {
            digitInputs.value[0]?.focus()
          })
        }
      }
      // 验证通过
      else if (msg.event === 'verification_success') {
        if (msg.data.subtask_id === subtaskId.value) {
          submitting.value = false
          isSuccess.value = true
          setTimeout(() => {
            visible.value = false
            isSuccess.value = false
          }, 1500)
        }
      }
      // 子任务状态变更
      else if (msg.event === 'subtask_status_changed') {
        if (msg.data.id === subtaskId.value && (msg.data.status === 'published' || msg.data.status === 'cancelled')) {
          visible.value = false
        }
      }
    } catch (e) {}
  }

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000)
  }
}

const handleOpenEvent = (e: any) => {
  if (e.detail) {
    openWithData(e.detail)
  }
}

onMounted(() => {
  window.addEventListener('open-verification-dialog', handleOpenEvent)
  initWebSocket()
})

onUnmounted(() => {
  window.removeEventListener('open-verification-dialog', handleOpenEvent)
  if (timer) clearInterval(timer)
  if (ws) ws.close()
})
</script>
