<template>
  <div class="space-y-6">
    <!-- 顶部操作与筛选栏 -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <!-- 左侧：搜索与平台筛选胶囊 -->
      <div class="flex flex-wrap items-center gap-2.5">
        <div class="relative w-64">
          <Search class="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
          <Input
            v-model="searchQuery"
            placeholder="搜索账号名称或 UID..."
            class="pl-9 h-9 bg-white text-xs"
          />
        </div>

        <div class="flex items-center rounded-lg border border-slate-200 bg-white p-1 text-xs shadow-sm">
          <button
            v-for="tab in platformTabs"
            :key="tab.value"
            @click="platformFilter = tab.value"
            class="rounded-md px-2.5 py-1 font-medium transition-all"
            :class="[
              platformFilter === tab.value
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            ]"
          >
            {{ tab.label }}
            <span class="ml-1 text-[10px] opacity-70">
              ({{ getPlatformCount(tab.value) }})
            </span>
          </button>
        </div>
      </div>

      <!-- 右侧：全局操作按钮 -->
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" class="h-9 gap-1.5" @click="handleBatchCheck">
          <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': isBatchChecking }" />
          <span>全量巡检</span>
        </Button>

        <Button variant="outline" size="sm" class="h-9 gap-1.5" @click="importDialogVisible = true">
          <Upload class="h-3.5 w-3.5" />
          <span>导入凭证</span>
        </Button>

        <Button variant="glow" size="sm" class="h-9 gap-1.5 font-semibold" @click="openLoginDialog">
          <Plus class="h-4 w-4" />
          <span>扫码添加账号</span>
        </Button>
      </div>
    </div>

    <!-- 账号卡片网格 -->
    <div v-if="filteredAccounts.length === 0" class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white p-16 text-center">
      <div class="flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-3">
        <Users2 class="h-7 w-7" />
      </div>
      <h3 class="text-sm font-bold text-slate-800">暂无匹配账号</h3>
      <p class="mt-1 max-w-sm text-xs text-slate-400">
        {{ accounts.length === 0 ? "尚未授权任何自媒体账号，点击上方【扫码添加账号】快速接入小红书或抖音。" : "未找到符合筛选条件的账号。" }}
      </p>
      <Button v-if="accounts.length === 0" variant="glow" size="sm" class="mt-4" @click="openLoginDialog">
        立即扫码接入
      </Button>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Card
        v-for="acc in filteredAccounts"
        :key="acc.id"
        class="group relative overflow-hidden border-slate-200/80 bg-white shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-0.5"
      >
        <CardContent class="p-4 space-y-3.5">
          <!-- 头部：头像、账号名、平台徽标与在线状态 -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <div class="relative flex-shrink-0">
                <Avatar class="h-12 w-12 border border-slate-200 shadow-sm">
                  <AvatarImage :src="acc.avatar_url" />
                  <AvatarFallback class="bg-gradient-to-br from-indigo-500 to-blue-600 text-white font-bold text-sm">
                    {{ acc.account_name ? acc.account_name.slice(0, 2) : "平台" }}
                  </AvatarFallback>
                </Avatar>
                <!-- 平台小角标 -->
                <span
                  class="absolute -bottom-1 -right-1 flex h-4.5 w-4.5 items-center justify-center rounded-full text-[9px] font-bold text-white shadow-sm ring-2 ring-white"
                  :class="getPlatformBadgeColor(acc.platform)"
                >
                  {{ getPlatformShort(acc.platform) }}
                </span>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h4 class="font-bold text-sm text-slate-900 truncate" :title="acc.account_name">
                    {{ acc.account_name }}
                  </h4>
                  <Badge variant="outline" class="text-[10px] px-1.5 py-0 flex-shrink-0">
                    {{ getPlatformLabel(acc.platform) }}
                  </Badge>
                </div>
                <div class="mt-1 flex items-center gap-2 text-xs text-slate-400">
                  <span class="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                    {{ acc.group_name }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 在线状态 -->
            <div class="flex-shrink-0">
              <Badge v-if="acc.status === 'active'" variant="success" class="gap-1 text-[11px]">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>有效</span>
              </Badge>
              <Badge v-else-if="acc.status === 'expired'" variant="destructive" class="gap-1 text-[11px]">
                <span class="h-1.5 w-1.5 rounded-full bg-rose-500"></span>
                <span>已失效</span>
              </Badge>
              <Badge v-else variant="secondary" class="text-[11px]">
                未授权
              </Badge>
            </div>
          </div>

          <!-- UID 识别条 -->
          <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/80 px-2.5 py-1.5 text-xs">
            <div class="flex items-center gap-1.5 min-w-0 flex-1">
              <span class="font-mono text-[11px] font-semibold text-slate-400">UID:</span>
              <span class="truncate font-mono font-medium text-slate-700 select-all" :title="acc.uid || '未获取'">
                {{ acc.uid || "未捕获 (点击检测同步)" }}
              </span>
            </div>
            <button
              v-if="acc.uid"
              @click="copyText(acc.uid)"
              class="flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-700 ml-2 flex-shrink-0 active:scale-95"
            >
              <Copy class="h-3 w-3" />
              <span>复制</span>
            </button>
          </div>

          <!-- 3列核心数据指标看板 (粉丝/点赞/关注) -->
          <div class="grid grid-cols-3 divide-x divide-slate-200/70 rounded-lg border border-slate-200/80 bg-gradient-to-b from-slate-50/70 to-slate-100/50 py-2.5 text-center">
            <div class="px-2">
              <div class="font-mono text-base font-bold text-slate-900 leading-tight">
                {{ formatCount(acc.followers_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-slate-500">粉丝总数</div>
            </div>
            <div class="px-2">
              <div class="font-mono text-base font-bold text-rose-600 leading-tight">
                {{ formatCount(acc.likes_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-slate-500">获赞与收藏</div>
            </div>
            <div class="px-2">
              <div class="font-mono text-base font-bold text-slate-700 leading-tight">
                {{ formatCount(acc.following_count) }}
              </div>
              <div class="mt-0.5 text-[11px] text-slate-500">关注账号</div>
            </div>
          </div>

          <!-- 检测时间与状态 -->
          <div class="flex items-center justify-between text-[11px] text-slate-400 pt-0.5">
            <span>最近检测: {{ acc.last_check_at ? acc.last_check_at.slice(0, 16).replace('T', ' ') : "未检测" }}</span>
            <span v-if="checkingAccountId === acc.id" class="text-blue-500 font-medium flex items-center gap-1">
              <RefreshCw class="h-3 w-3 animate-spin" />
              <span>同步数据中...</span>
            </span>
          </div>

          <!-- 底部操作按钮组 -->
          <div class="flex items-center justify-between border-t border-slate-100 pt-3">
            <div class="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="xs"
                class="h-7 text-xs text-slate-700 hover:text-blue-600 hover:bg-blue-50 gap-1 px-2"
                :disabled="checkingAccountId === acc.id"
                @click="handleCheckHealth(acc)"
              >
                <RefreshCw class="h-3 w-3" :class="{ 'animate-spin': checkingAccountId === acc.id }" />
                <span>检测更新</span>
              </Button>

              <Button
                variant="ghost"
                size="xs"
                class="h-7 text-xs text-amber-600 hover:text-amber-700 hover:bg-amber-50 gap-1 px-2"
                @click="handleLaunchAssist(acc)"
              >
                <Monitor class="h-3 w-3" />
                <span>呼出窗口</span>
              </Button>

              <Button
                variant="ghost"
                size="xs"
                class="h-7 text-xs text-slate-600 hover:text-slate-800 hover:bg-slate-100 gap-1 px-2"
                @click="handleExport(acc)"
              >
                <Download class="h-3 w-3" />
                <span>导出</span>
              </Button>
            </div>

            <Button
              variant="ghost"
              size="xs"
              class="h-7 text-xs text-rose-500 hover:text-rose-700 hover:bg-rose-50 px-2"
              @click="confirmDelete(acc)"
            >
              <Trash2 class="h-3 w-3" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- 扫码授权模态框 (Dialog) -->
    <Dialog :open="loginDialogVisible" @update:open="val => { if (!val) closeLoginDialog() }">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="text-base font-bold">自媒体账号免密扫码授权</DialogTitle>
          <DialogDescription>
            启动本地无头 Chromium 获取官方登录二维码，使用手机 App 扫码即可完成 Cookie 会话持久化。
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1.5">目标发布平台</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                type="button"
                @click="loginForm.platform = 'xiaohongshu'"
                :disabled="isLoggingIn"
                class="flex items-center gap-2.5 rounded-lg border p-2.5 text-left transition-all"
                :class="[
                  loginForm.platform === 'xiaohongshu'
                    ? 'border-red-500 bg-red-50/50 text-red-700 font-semibold shadow-sm'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                ]"
              >
                <span class="flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">红</span>
                <div>
                  <div class="text-xs">小红书</div>
                  <div class="text-[10px] text-slate-400 font-normal">creator.xiaohongshu.com</div>
                </div>
              </button>

              <button
                type="button"
                @click="loginForm.platform = 'douyin'"
                :disabled="isLoggingIn"
                class="flex items-center gap-2.5 rounded-lg border p-2.5 text-left transition-all"
                :class="[
                  loginForm.platform === 'douyin'
                    ? 'border-blue-500 bg-blue-50/50 text-blue-700 font-semibold shadow-sm'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                ]"
              >
                <span class="flex h-6 w-6 items-center justify-center rounded-full bg-slate-900 text-[10px] font-bold text-white">抖</span>
                <div>
                  <div class="text-xs">抖音</div>
                  <div class="text-[10px] text-slate-400 font-normal">creator.douyin.com</div>
                </div>
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">账号所属分组</label>
            <Input v-model="loginForm.group_name" placeholder="如：美食矩阵A组、生活博主" :disabled="isLoggingIn" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-700 mb-1">独立代理 IP (可选)</label>
            <Input v-model="loginForm.proxy_url" placeholder="格式: http://user:pass@ip:port" :disabled="isLoggingIn" />
          </div>

          <!-- 二维码显示区 -->
          <div v-if="isLoggingIn" class="rounded-xl border border-slate-200 bg-slate-50/60 p-4 text-center">
            <div v-if="qrcodeBase64" class="inline-block p-2 bg-white rounded-lg border border-slate-200 shadow-sm">
              <img :src="qrcodeBase64" alt="登录二维码" class="h-48 w-48 object-contain mx-auto" />
              <p class="text-xs font-medium text-slate-700 mt-2">请使用对应手机 App 扫码确认登录</p>
            </div>
            <div v-else class="py-10 flex flex-col items-center justify-center text-slate-400">
              <RefreshCw class="h-7 w-7 animate-spin text-blue-600 mb-2" />
              <p class="text-xs text-slate-600">正在拉起隔离浏览器提取官方登录二维码...</p>
            </div>

            <div class="mt-3 pt-3 border-t border-slate-200/80 flex flex-col items-center gap-1.5">
              <p class="text-[11px] text-slate-400">遇到滑块拼图验证或二维码提取缓慢？</p>
              <Button
                variant="outline"
                size="sm"
                class="text-xs gap-1.5 text-amber-600 border-amber-200 bg-amber-50/50 hover:bg-amber-100"
                :disabled="!currentLoginAccountId"
                @click="handleAssistFromDialog"
              >
                <Monitor class="h-3.5 w-3.5" />
                <span>呼出桌面窗口直接操作 (过滑块/手机验证)</span>
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="closeLoginDialog">取消</Button>
          <Button v-if="!isLoggingIn" variant="glow" size="sm" @click="handleStartLogin">
            启动浏览器获取二维码
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 导入凭证模态框 (Dialog) -->
    <Dialog :open="importDialogVisible" @update:open="val => importDialogVisible = val">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="text-base font-bold">导入账号会话包 (.zip)</DialogTitle>
          <DialogDescription>
            支持导入由本平台导出的加密会话凭证包，系统将自动还原并校验连通性。
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div
            class="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 p-6 text-center transition-colors hover:border-blue-400 bg-slate-50/50 cursor-pointer"
            @click="triggerFileSelect"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".zip"
              class="hidden"
              @change="handleFileSelected"
            />
            <Upload class="h-8 w-8 text-slate-400 mb-2" />
            <div v-if="selectedFile" class="font-medium text-xs text-blue-600">
              已选文件: {{ selectedFile.name }}
            </div>
            <div v-else class="text-xs text-slate-600">
              <span class="font-semibold text-blue-600">点击选择</span> 或拖拽 .zip 文件至此处
            </div>
            <p class="text-[11px] text-slate-400 mt-1">仅支持 MatrixHub 导出的 .zip 会话压缩包</p>
          </div>

          <div class="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 p-2.5 text-xs">
            <span class="text-slate-700">若账号已存在则覆盖已有会话</span>
            <Switch :checked="overwriteOnImport" @update:checked="val => overwriteOnImport = val" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="importDialogVisible = false">取消</Button>
          <Button variant="glow" size="sm" :disabled="!selectedFile || importing" @click="submitImport">
            {{ importing ? "正在还原..." : "开始导入" }}
          </Button>
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
import { Switch } from "@/components/ui/switch"
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
const fileInput = ref<HTMLInputElement | null>(null)
const triggerFileSelect = () => {
  fileInput.value?.click()
}

const platformTabs = [
  { label: "全部平台", value: "all" },
  { label: "小红书", value: "xiaohongshu" },
  { label: "抖音", value: "douyin" },
  { label: "快手", value: "kuaishou" },
  { label: "视频号", value: "channels" },
]

const getPlatformCount = (val: string) => {
  if (val === "all") return accounts.value.length
  return accounts.value.filter(a => a.platform === val).length
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
  if (val >= 1000) {
    return (val / 1000).toFixed(1).replace(/\.0$/, "") + "k"
  }
  return String(val)
}

const copyText = (text: string) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success("账号ID已成功复制到剪贴板！")
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
let assistPollTimer: any = null

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
    ElMessage.success("已在后台为您拉起桌面 Chrome 窗口，请在弹出的浏览器中操作！")
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleCheckHealth = async (acc: any) => {
  checkingAccountId.value = acc.id
  const loadingMsg = ElMessage.info({ message: `正在检测并同步【${acc.account_name}】最新数据...`, duration: 0 })
  try {
    const res: any = await checkAccountHealth(acc.id)
    loadingMsg.close()
    if (res.data.status === "active") {
      ElMessage.success(`【${acc.account_name}】登录有效，最新数据已同步！`)
    } else {
      ElMessage.warning(`【${acc.account_name}】登录态已过期，请重新登录`)
    }
    loadAccounts()
  } catch (e: any) {
    loadingMsg.close()
    ElMessage.error(e.message)
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
    ElMessage.success(`已为您呼出【${acc.account_name}】的辅助 Chrome 窗口！`)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleExport = (acc: any) => {
  const url = getExportAccountUrl(acc.id)
  window.open(url, "_blank")
}

const confirmDelete = (acc: any) => {
  ElMessageBox.confirm(`确定要删除账号【${acc.account_name}】及其本地独立隔离缓存吗？`, "删除确认", {
    confirmButtonText: "确定删除",
    cancelButtonText: "取消",
    type: "warning",
  }).then(() => {
    handleDelete(acc.id)
  }).catch(() => {})
}

const handleDelete = async (id: string) => {
  try {
    await deleteAccount(id)
    ElMessage.success("账号已成功删除")
    loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
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
    ElMessage.success(`成功导入 ${res.data.imported_count} 个账号！`)
    importDialogVisible.value = false
    selectedFile.value = null
    loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    importing.value = false
  }
}

const getPlatformLabel = (platform: string) => {
  const map: Record<string, string> = {
    xiaohongshu: "小红书",
    douyin: "抖音",
    kuaishou: "快手",
    channels: "视频号",
  }
  return map[platform] || platform
}

const getPlatformShort = (platform: string) => {
  const map: Record<string, string> = {
    xiaohongshu: "红",
    douyin: "抖",
    kuaishou: "快",
    channels: "视",
  }
  return map[platform] || "号"
}

const getPlatformBadgeColor = (platform: string) => {
  const map: Record<string, string> = {
    xiaohongshu: "bg-red-500",
    douyin: "bg-slate-900",
    kuaishou: "bg-amber-500",
    channels: "bg-emerald-600",
  }
  return map[platform] || "bg-blue-600"
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
  if (assistPollTimer) {
    clearInterval(assistPollTimer)
    assistPollTimer = null
  }
})
</script>
