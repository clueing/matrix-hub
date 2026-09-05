<template>
  <div class="space-y-6 max-w-7xl mx-auto pb-16">
    <!-- 顶部操作与筛选栏 -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <!-- 左侧：搜索与平台分段过滤 -->
      <div class="flex flex-wrap items-center gap-2.5">
        <div class="relative w-64">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            placeholder="搜索账号名称或 UID..."
            class="pl-9 h-9 text-xs"
          />
        </div>

        <div class="flex items-center rounded-lg border border-border bg-background p-1 text-xs">
          <button
            v-for="tab in platformTabs"
            :key="tab.value"
            type="button"
            @click="platformFilter = tab.value"
            class="rounded-md px-2.5 py-1 font-medium transition-colors"
            :class="[
              platformFilter === tab.value
                ? 'bg-secondary text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            ]"
          >
            {{ tab.label }}
            <span class="ml-1 text-[10px] opacity-70">
              ({{ getPlatformCount(tab.value) }})
            </span>
          </button>
        </div>
      </div>

      <!-- 右侧：操作按钮组 (官方纯净 Button) -->
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" class="h-9 gap-1.5" :disabled="isBatchChecking" @click="handleBatchCheck">
          <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': isBatchChecking }" />
          <span>全量巡检</span>
        </Button>

        <Button variant="outline" size="sm" class="h-9 gap-1.5" @click="importDialogVisible = true">
          <Upload class="h-3.5 w-3.5" />
          <span>导入凭证</span>
        </Button>

        <Button variant="default" size="sm" class="h-9 gap-1.5" @click="openLoginDialog">
          <Plus class="h-4 w-4" />
          <span>扫码添加账号</span>
        </Button>
      </div>
    </div>

    <!-- 账号列表：空状态 -->
    <div v-if="filteredAccounts.length === 0" class="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card p-16 text-center">
      <div class="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground mb-3">
        <Users2 class="h-6 w-6" />
      </div>
      <h3 class="text-sm font-semibold text-foreground">暂无匹配账号</h3>
      <p class="mt-1 max-w-sm text-xs text-muted-foreground">
        {{ accounts.length === 0 ? "尚未授权任何自媒体账号，点击上方【扫码添加账号】快速接入小红书或抖音。" : "未找到符合筛选条件的账号。" }}
      </p>
      <Button v-if="accounts.length === 0" variant="default" size="sm" class="mt-4" @click="openLoginDialog">
        立即扫码接入
      </Button>
    </div>

    <!-- 账号卡片网格 -->
    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Card
        v-for="acc in filteredAccounts"
        :key="acc.id"
        class="border-border shadow-sm transition-colors hover:border-border/80"
      >
        <CardContent class="p-4 space-y-3.5">
          <!-- 头部：清爽头像、账号名、平台徽标与在线状态 -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <!-- 头像：移除突兀的右下角角标，还原清爽纯净的官方 Avatar 设计 -->
              <Avatar class="h-11 w-11 rounded-lg border border-border flex-shrink-0">
                <AvatarImage :src="acc.avatar_url" />
                <AvatarFallback class="rounded-lg bg-muted text-foreground text-xs font-semibold">
                  {{ acc.account_name ? acc.account_name.slice(0, 2) : "账号" }}
                </AvatarFallback>
              </Avatar>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <h4 class="font-semibold text-sm text-foreground truncate max-w-[140px]" :title="acc.account_name">
                    {{ acc.account_name }}
                  </h4>
                  <!-- 平台标签放置在账号名旁边，简洁明了 -->
                  <Badge variant="outline" class="text-[10px] px-1.5 py-0">
                    {{ getPlatformLabel(acc.platform) }}
                  </Badge>
                </div>
                <div class="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                  <span class="text-[11px]">{{ acc.group_name || "默认分组" }}</span>
                </div>
              </div>
            </div>

            <!-- 在线状态微标 -->
            <div class="flex-shrink-0">
              <Badge v-if="acc.status === 'active'" variant="success" class="text-[10px] px-1.5 py-0">
                在线
              </Badge>
              <Badge v-else-if="acc.status === 'expired'" variant="destructive" class="text-[10px] px-1.5 py-0">
                待重登
              </Badge>
              <Badge v-else variant="secondary" class="text-[10px] px-1.5 py-0">
                未授权
              </Badge>
            </div>
          </div>

          <!-- UID 识别条 -->
          <div class="flex items-center justify-between rounded-md border border-border bg-muted/40 px-2.5 py-1.5 text-xs">
            <div class="flex items-center gap-1.5 min-w-0 flex-1">
              <span class="font-mono text-[11px] text-muted-foreground">UID:</span>
              <span class="truncate font-mono text-foreground select-all" :title="acc.uid || '未获取'">
                {{ acc.uid || "未获取 (点击巡检同步)" }}
              </span>
            </div>
            <button
              v-if="acc.uid"
              type="button"
              @click="copyText(acc.uid)"
              class="flex items-center gap-1 text-[11px] text-primary hover:underline ml-2 flex-shrink-0"
            >
              <Copy class="h-3 w-3" />
              <span>复制</span>
            </button>
          </div>

          <!-- 3列数据指标 (粉丝数/获赞与收藏/关注数) - 官方极简设计，无多余渐变 -->
          <div class="grid grid-cols-3 divide-x divide-border rounded-md border border-border bg-muted/20 py-2 text-center">
            <div class="px-2">
              <div class="font-mono text-sm font-semibold text-foreground leading-tight">
                {{ formatCount(acc.followers_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-muted-foreground">粉丝总数</div>
            </div>
            <div class="px-2">
              <div class="font-mono text-sm font-semibold text-foreground leading-tight">
                {{ formatCount(acc.likes_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-muted-foreground">获赞与收藏</div>
            </div>
            <div class="px-2">
              <div class="font-mono text-sm font-semibold text-foreground leading-tight">
                {{ formatCount(acc.following_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-muted-foreground">关注账号</div>
            </div>
          </div>

          <!-- 底部操作按钮 -->
          <div class="flex items-center justify-between border-t border-border pt-3">
            <div class="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                :disabled="checkingAccountId === acc.id"
                @click="handleCheckHealth(acc)"
              >
                <RefreshCw class="h-3 w-3 mr-1" :class="{ 'animate-spin': checkingAccountId === acc.id }" />
                <span>{{ checkingAccountId === acc.id ? "检测中" : "巡检" }}</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                @click="handleLaunchAssist(acc)"
              >
                <Monitor class="h-3 w-3 mr-1" />
                <span>辅助浏览器</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                @click="handleExport(acc)"
              >
                <Download class="h-3 w-3 mr-1" />
                <span>导出</span>
              </Button>
            </div>

            <Button
              variant="ghost"
              size="sm"
              class="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
              @click="confirmDelete(acc)"
            >
              <Trash2 class="h-3 w-3 mr-1" />
              <span>删除</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- 扫码添加账号模态框 (Dialog) -->
    <Dialog :open="loginDialogVisible" @update:open="val => { if (!val) closeLoginDialog() }">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="text-base font-semibold">扫码添加矩阵账号</DialogTitle>
          <DialogDescription class="text-xs">
            选择目标平台并启动官方自动化登录会话，在弹出的窗口或二维码中完成授权
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <!-- 平台选择 -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">目标平台</label>
            <div class="flex gap-2">
              <button
                v-for="p in [
                  { label: '小红书', value: 'xiaohongshu' },
                  { label: '抖音', value: 'douyin' }
                ]"
                :key="p.value"
                type="button"
                class="flex-1 rounded-md border p-2.5 text-center transition-colors text-xs font-medium"
                :class="[
                  loginForm.platform === p.value
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-card text-foreground hover:bg-muted/40'
                ]"
                @click="loginForm.platform = p.value"
              >
                {{ p.label }}
              </button>
            </div>
          </div>

          <!-- 分组名称 -->
          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">账号分组</label>
            <Input v-model="loginForm.group_name" placeholder="如：默认分组 / 运营一部" class="h-8 text-xs" />
          </div>

          <!-- 二维码与状态呈现 -->
          <div class="flex flex-col items-center justify-center rounded-lg border border-border bg-muted/20 p-6 min-h-[200px]">
            <div v-if="qrcodeBase64" class="flex flex-col items-center gap-3">
              <div class="bg-white p-2 rounded-lg border border-border shadow-sm">
                <img :src="qrcodeBase64" alt="登录二维码" class="h-44 w-44 object-contain" />
              </div>
              <p class="text-xs text-muted-foreground">
                请打开对应平台 App 扫一扫授权登录
              </p>
            </div>

            <div v-else-if="isLoggingIn" class="flex flex-col items-center gap-2 text-muted-foreground text-xs">
              <RefreshCw class="h-6 w-6 animate-spin text-primary" />
              <span>正在调起浏览器会话并捕获登录二维码...</span>
            </div>

            <div v-else class="flex flex-col items-center gap-2 text-muted-foreground text-xs">
              <QrCode class="h-8 w-8 opacity-40" />
              <span>点击下方按钮调起无痕浏览器并获取二维码</span>
              <Button size="sm" variant="default" class="mt-2" @click="handleStartLogin">
                启动登录流程
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="closeLoginDialog">关闭</Button>
          <Button v-if="currentLoginAccountId" variant="secondary" size="sm" @click="handleAssistFromDialog">
            调出桌面窗口辅助
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 批量导入凭证包模态框 (Dialog) -->
    <Dialog :open="importDialogVisible" @update:open="val => importDialogVisible = val">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="text-base font-semibold">批量导入账号凭证</DialogTitle>
          <DialogDescription class="text-xs">
            选择包含平台 Cookie 导出凭证的 ZIP 文件进行一键恢复
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <label class="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-border hover:border-primary/50 bg-muted/20 p-8 text-center cursor-pointer transition-colors">
            <Upload class="h-8 w-8 text-muted-foreground mb-2" />
            <span class="text-xs font-medium text-foreground">选择本地 ZIP 凭证包</span>
            <span class="text-[11px] text-muted-foreground mt-1">支持标准化账号备份包</span>
            <input
              type="file"
              accept=".zip"
              class="hidden"
              @change="handleFileSelected"
            />
          </label>

          <div v-if="selectedFile" class="flex items-center justify-between rounded-md border border-border p-2 text-xs">
            <span class="truncate font-medium">{{ selectedFile.name }}</span>
            <Button size="sm" variant="default" :disabled="importing" @click="submitImport">
              {{ importing ? "导入中..." : "确认导入" }}
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="importDialogVisible = false">取消</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Search,
  Plus,
  Upload,
  RefreshCw,
  Monitor,
  Download,
  Trash2,
  Copy,
  Users2,
  QrCode,
} from "lucide-vue-next"
import {
  getAccounts,
  startLogin,
  checkAccountHealth,
  launchAssist,
  deleteAccount,
  getExportAccountUrl,
  importAccount,
} from "../api"

const loading = ref(false)
const accounts = ref<any[]>([])
const platformFilter = ref("all")
const searchQuery = ref("")
const checkingAccountId = ref("")
const isBatchChecking = ref(false)

const platformTabs = [
  { label: "全部平台", value: "all" },
  { label: "小红书", value: "xiaohongshu" },
  { label: "抖音", value: "douyin" },
]

const getPlatformCount = (val: string) => {
  if (val === "all") return accounts.value.length
  return accounts.value.filter(a => a.platform === val).length
}

const getPlatformLabel = (platform: string) => {
  if (platform === "xiaohongshu") return "小红书"
  if (platform === "douyin") return "抖音"
  return platform
}

const filteredAccounts = computed(() => {
  return accounts.value.filter(acc => {
    const matchPlatform = platformFilter.value === "all" || acc.platform === platformFilter.value
    const query = searchQuery.value.trim().toLowerCase()
    const matchSearch =
      !query ||
      (acc.account_name && acc.account_name.toLowerCase().includes(query)) ||
      (acc.uid && String(acc.uid).toLowerCase().includes(query)) ||
      (acc.group_name && acc.group_name.toLowerCase().includes(query))
    return matchPlatform && matchSearch
  })
})

const formatCount = (val: number | null | undefined) => {
  if (!val || val === 0) return "0"
  if (val >= 10000) {
    return (val / 10000).toFixed(1).replace(/\.0$/, "") + "w"
  }
  return String(val)
}

const copyText = (text: string) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success("UID 已成功复制到剪贴板！")
  }).catch(() => {
    ElMessage.warning("复制失败")
  })
}

// 登录控制
const loginDialogVisible = ref(false)
const isLoggingIn = ref(false)
const qrcodeBase64 = ref("")
const currentLoginAccountId = ref("")
const loginForm = ref({
  platform: "xiaohongshu",
  group_name: "默认分组",
  proxy_url: "",
})

// 导入控制
const importDialogVisible = ref(false)
const importing = ref(false)
const overwriteOnImport = ref(true)
const selectedFile = ref<any>(null)

let ws: WebSocket | null = null

const loadAccounts = async () => {
  loading.value = true
  try {
    const res: any = await getAccounts()
    accounts.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message || "加载账号列表失败")
  } finally {
    loading.value = false
  }
}

const openLoginDialog = () => {
  loginDialogVisible.value = true
  isLoggingIn.value = false
  qrcodeBase64.value = ""
  currentLoginAccountId.value = ""
}

const closeLoginDialog = () => {
  loginDialogVisible.value = false
  isLoggingIn.value = false
  qrcodeBase64.value = ""
  currentLoginAccountId.value = ""
}

const handleStartLogin = async () => {
  isLoggingIn.value = true
  qrcodeBase64.value = ""
  currentLoginAccountId.value = ""
  try {
    const res: any = await startLogin(loginForm.value)
    currentLoginAccountId.value = res.data.account_id
  } catch (e: any) {
    ElMessage.error(e.message || "初始化登录环境失败")
    isLoggingIn.value = false
  }
}

const handleAssistFromDialog = async () => {
  if (!currentLoginAccountId.value) return
  try {
    await launchAssist(currentLoginAccountId.value)
    ElMessage.success("已在后台拉起桌面 Chrome 窗口，请在弹出的浏览器中操作！")
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleCheckHealth = async (acc: any) => {
  checkingAccountId.value = acc.id
  try {
    const res: any = await checkAccountHealth(acc.id)
    if (res.data?.status === "active") {
      ElMessage.success(`【${acc.account_name}】登录有效，最新数据已同步！`)
    } else {
      ElMessage.warning(`【${acc.account_name}】登录态已过期，请重新登录`)
    }
    loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message || "巡检失败")
  } finally {
    checkingAccountId.value = ""
  }
}

const handleBatchCheck = async () => {
  if (accounts.value.length === 0) return
  isBatchChecking.value = true
  ElMessage.info("开始并发巡检全部账号会话与数据...")
  try {
    await Promise.all(accounts.value.map(a => checkAccountHealth(a.id)))
    ElMessage.success("全部账号巡检完成！")
    loadAccounts()
  } catch (e) {
    ElMessage.error("巡检过程中部分账号出现异常")
  } finally {
    isBatchChecking.value = false
  }
}

const handleLaunchAssist = async (acc: any) => {
  try {
    await launchAssist(acc.id)
    ElMessage.success(`已呼出【${acc.account_name}】的辅助 Chrome 窗口！`)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleExport = (acc: any) => {
  const url = getExportAccountUrl(acc.id)
  window.open(url, "_blank")
}

const confirmDelete = (acc: any) => {
  ElMessageBox.confirm(`确定要删除账号【${acc.account_name}】及其本地独立缓存吗？`, "删除确认", {
    confirmButtonText: "确定删除",
    cancelButtonText: "取消",
    type: "warning",
  }).then(async () => {
    try {
      await deleteAccount(acc.id)
      ElMessage.success("账号已成功删除")
      loadAccounts()
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  }).catch(() => {})
}

const handleFileSelected = (e: any) => {
  const file = e.target.files?.[0]
  if (file) {
    selectedFile.value = file
  }
}

const submitImport = async () => {
  if (!selectedFile.value) {
    ElMessage.warning("请先选择要导入的 .zip 凭证包")
    return
  }
  importing.value = true
  const formData = new FormData()
  formData.append("file", selectedFile.value)
  try {
    const res: any = await importAccount(formData, overwriteOnImport.value)
    ElMessage.success(`成功导入 ${res.data?.imported_count || 0} 个账号！`)
    importDialogVisible.value = false
    selectedFile.value = null
    loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message || "导入失败")
  } finally {
    importing.value = false
  }
}

const initWebSocket = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.event === "login_qrcode") {
        qrcodeBase64.value = msg.data.qrcode
      } else if (msg.event === "login_success") {
        ElMessage.success(`账号【${msg.data.account_name}】登录授权成功！`)
        loginDialogVisible.value = false
        isLoggingIn.value = false
        loadAccounts()
      } else if (msg.event === "login_failed") {
        ElMessage.error(`登录失败: ${msg.data.error || "未知异常"}`)
        isLoggingIn.value = false
      }
    } catch (e) {}
  }

  ws.onclose = () => {
    setTimeout(initWebSocket, 3000)
  }
}

onMounted(() => {
  loadAccounts()
  initWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>
