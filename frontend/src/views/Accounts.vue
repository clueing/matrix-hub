<template>
  <div class="accounts-container">
    <!-- 顶部操作栏 -->
    <el-card shadow="never" class="mb-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-4">
          <span class="font-bold text-lg">自媒体矩阵账号</span>
          <el-radio-group v-model="platformFilter" size="small" @change="loadAccounts">
            <el-radio-button label="">全部平台</el-radio-button>
            <el-radio-button label="xiaohongshu">小红书</el-radio-button>
            <el-radio-button label="douyin">抖音</el-radio-button>
            <el-radio-button label="kuaishou">快手</el-radio-button>
            <el-radio-button label="channels">微信视频号</el-radio-button>
          </el-radio-group>
        </div>
        <div class="flex gap-2">
          <el-button type="primary" @click="openLoginDialog">
            <el-icon class="mr-1"><Plus /></el-icon> 扫码添加账号
          </el-button>
          <el-button type="success" @click="openImportDialog">
            <el-icon class="mr-1"><Upload /></el-icon> 导入账号凭证 (.zip)
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 账号卡片矩阵网格 -->
    <el-row :gutter="16" v-loading="loading">
      <el-col :span="8" v-for="acc in accounts" :key="acc.id" class="mb-4">
        <el-card shadow="hover" class="account-card">
          <div class="flex justify-between items-start mb-3">
            <div class="flex items-center gap-3">
              <el-avatar :size="48" :src="acc.avatar_url">
                {{ acc.account_name ? acc.account_name.slice(0, 2) : "平台" }}
              </el-avatar>
              <div>
                <div class="font-bold text-base flex items-center gap-2">
                  {{ acc.account_name }}
                  <el-tag size="small" :type="getPlatformTagType(acc.platform)">
                    {{ getPlatformLabel(acc.platform) }}
                  </el-tag>
                </div>
                <div class="text-xs text-gray-400 mt-1">分组: {{ acc.group_name }}</div>
              </div>
            </div>
            <div>
              <el-tag v-if="acc.status === 'active'" type="success" effect="dark" size="small">在线有效</el-tag>
              <el-tag v-else-if="acc.status === 'expired'" type="danger" effect="dark" size="small">登录失效</el-tag>
              <el-tag v-else type="info" size="small">未授权</el-tag>
            </div>
          </div>

          <div class="account-meta text-xs text-gray-500 mb-4">
            <div>UID: {{ acc.uid || "暂未捕获" }}</div>
            <div>最近健康检测: {{ acc.last_check_at ? acc.last_check_at.slice(0, 19).replace('T', ' ') : "未检测" }}</div>
          </div>

          <!-- 操作按钮组 -->
          <div class="flex justify-between items-center border-t pt-3">
            <div class="flex gap-1">
              <el-button size="small" type="primary" link @click="handleCheckHealth(acc)">
                <el-icon><Refresh /></el-icon> 检测
              </el-button>
              <el-button size="small" type="warning" link @click="handleLaunchAssist(acc)">
                <el-icon><Monitor /></el-icon> 呼出窗口
              </el-button>
              <el-button size="small" type="success" link @click="handleExport(acc)">
                <el-icon><Download /></el-icon> 导出
              </el-button>
            </div>
            <div>
              <el-popconfirm title="确定要删除此账号及其独立缓存吗？" @confirm="handleDelete(acc.id)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 空状态 -->
    <el-empty v-if="!loading && accounts.length === 0" description="暂无矩阵账号，点击右上角【扫码添加账号】或【导入账号凭证】开始使用" />

    <!-- 扫码添加账号模态框 -->
    <el-dialog v-model="loginDialogVisible" title="添加/登录自媒体账号" width="480px" :close-on-click-modal="false" @close="closeLoginDialog">
      <el-form :model="loginForm" label-width="90px">
        <el-form-item label="目标平台">
          <el-select v-model="loginForm.platform" placeholder="请选择平台" style="width: 100%" :disabled="isLoggingIn">
            <el-option label="小红书 (creator.xiaohongshu.com)" value="xiaohongshu" />
            <el-option label="抖音 (creator.douyin.com)" value="douyin" />
            <el-option label="快手 (敬请期待)" value="kuaishou" disabled />
            <el-option label="微信视频号 (敬请期待)" value="channels" disabled />
          </el-select>
        </el-form-item>
        <el-form-item label="账号分组">
          <el-input v-model="loginForm.group_name" placeholder="如：美妆一号群、个人生活号" :disabled="isLoggingIn" />
        </el-form-item>
        <el-form-item label="独立代理IP">
          <el-input v-model="loginForm.proxy_url" placeholder="可选: http://user:pass@ip:port" :disabled="isLoggingIn" />
        </el-form-item>
      </el-form>

      <!-- 二维码呈现区 -->
      <div v-if="isLoggingIn" class="qrcode-wrapper text-center my-4">
        <div v-if="qrcodeBase64" class="inline-block p-2 border rounded bg-white shadow-sm">
          <img :src="qrcodeBase64" alt="登录二维码" style="width: 220px; height: 220px; object-fit: contain;" />
          <div class="text-sm text-gray-600 mt-2 font-medium">请打开对应手机 App 扫码登录</div>
        </div>
        <div v-else class="py-10 flex flex-col items-center justify-center">
          <el-icon class="is-loading text-3xl text-primary mb-2"><Loading /></el-icon>
          <span class="text-sm text-gray-500">正在拉起隔离浏览器并提取二维码...</span>
        </div>
        <div class="mt-4 pt-3 border-t flex flex-col items-center gap-2">
          <span class="text-xs text-gray-400">
            若遇到拼图滑块验证或二维码提取缓慢，可一键呼出桌面窗口直接操作
          </span>
          <el-button 
            type="warning" 
            plain 
            size="small" 
            :disabled="!currentLoginAccountId" 
            @click="handleAssistFromDialog"
          >
            <el-icon class="mr-1"><Monitor /></el-icon>
            呼出桌面 Chrome 辅助窗口 (过滑块/扫码)
          </el-button>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeLoginDialog">取消</el-button>
          <el-button v-if="!isLoggingIn" type="primary" @click="handleStartLogin">
            获取登录二维码
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入账号模态框 -->
    <el-dialog v-model="importDialogVisible" title="导入账号凭证 (.zip)" width="450px">
      <el-upload
        class="upload-demo"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".zip"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将账号备份包拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip text-xs text-gray-400">
            支持由本平台导出的 .zip 凭证包，系统将自动还原会话并执行连通性校验
          </div>
        </template>
      </el-upload>
      <div class="mt-3">
        <el-checkbox v-model="overwriteOnImport">若账号已存在则覆盖已有会话</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="submitImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue"
import { ElMessage } from "element-plus"
import { Plus, Upload, Refresh, Monitor, Download, Loading, UploadFilled } from "@element-plus/icons-vue"
import { 
  getAccounts, startLogin, checkAccountHealth, launchAssist, 
  deleteAccount, getExportAccountUrl, importAccount 
} from "../api"

const loading = ref(false)
const accounts = ref<any[]>([])
const platformFilter = ref("")

// 登录模态框控制
const loginDialogVisible = ref(false)
const isLoggingIn = ref(false)
const qrcodeBase64 = ref("")
const currentLoginAccountId = ref("")
const loginForm = ref({
  platform: "xiaohongshu",
  group_name: "默认分组",
  proxy_url: ""
})

// 导入模态框控制
const importDialogVisible = ref(false)
const importing = ref(false)
const selectedFile = ref<File | null>(null)
const overwriteOnImport = ref(true)

// 辅助登录与状态自动同步轮询器
let assistPollTimer: any = null

const startAssistPolling = (accountId: string) => {
  if (assistPollTimer) clearInterval(assistPollTimer)
  let attempts = 0
  assistPollTimer = setInterval(async () => {
    attempts++
    if (attempts > 90) { // 最多持续轮询 3 分钟
      clearInterval(assistPollTimer)
      assistPollTimer = null
      return
    }
    try {
      const res: any = await getAccounts({ platform: platformFilter.value || undefined })
      if (res && res.data) {
        accounts.value = res.data
        const target = res.data.find((a: any) => a.id === accountId)
        if (target && target.status === "active") {
          ElMessage.success(`【${target.account_name}】授权状态已自动同步为有效！`)
          clearInterval(assistPollTimer)
          assistPollTimer = null
          if (loginDialogVisible.value) {
            closeLoginDialog()
          }
        }
      }
    } catch (e) {}
  }, 2000)
}

// WebSocket 连接
let ws: WebSocket | null = null

const initWebSocket = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.event === "qrcode_updated") {
        if (msg.data.account_id === currentLoginAccountId.value) {
          qrcodeBase64.value = msg.data.qrcode_base64
        }
      } else if (msg.event === "account_status_changed") {
        loadAccounts()
        if (msg.data.status === "active") {
          if (loginDialogVisible.value && msg.data.id === currentLoginAccountId.value) {
            ElMessage.success(`【${msg.data.account_name}】扫码授权成功！`)
            closeLoginDialog()
          }
        }
      }
    } catch (e) {}
  }
}

const loadAccounts = async () => {
  loading.value = true
  try {
    const res: any = await getAccounts({ platform: platformFilter.value || undefined })
    accounts.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message)
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
  loadAccounts()
}

const handleStartLogin = async () => {
  isLoggingIn.value = true
  qrcodeBase64.value = ""
  try {
    const res: any = await startLogin(loginForm.value)
    currentLoginAccountId.value = res.data.account_id
    // 立即刷新列表保证新增的待授权账号即时可见
    loadAccounts()
    // 启动状态同步轮询
    startAssistPolling(res.data.account_id)
  } catch (e: any) {
    isLoggingIn.value = false
    ElMessage.error(e.message)
  }
}

const handleAssistFromDialog = async () => {
  if (!currentLoginAccountId.value) return
  try {
    await launchAssist(currentLoginAccountId.value)
    ElMessage.success("已在桌面呼出 Chrome 窗口，请在弹出的窗口中操作，完成后将自动同步！")
    startAssistPolling(currentLoginAccountId.value)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleCheckHealth = async (acc: any) => {
  const loadingMsg = ElMessage.info({ message: `正在检测【${acc.account_name}】登录态...`, duration: 0 })
  try {
    const res: any = await checkAccountHealth(acc.id)
    loadingMsg.close()
    if (res.data.status === "active") {
      ElMessage.success(`【${acc.account_name}】登录态有效！`)
    } else {
      ElMessage.warning(`【${acc.account_name}】登录态已过期，请重新登录`)
    }
    loadAccounts()
  } catch (e: any) {
    loadingMsg.close()
    ElMessage.error(e.message)
  }
}

const handleLaunchAssist = async (acc: any) => {
  try {
    await launchAssist(acc.id)
    ElMessage.success("已在桌面弹出受控 Chrome 窗口，请在弹窗中滑动滑块或输入验证码！")
    startAssistPolling(acc.id)
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleExport = (acc: any) => {
  window.open(getExportAccountUrl(acc.id), "_blank")
}

const handleDelete = async (accountId: string) => {
  try {
    await deleteAccount(accountId)
    ElMessage.success("账号已删除")
    loadAccounts()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const openImportDialog = () => {
  importDialogVisible.value = true
  selectedFile.value = null
}

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
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
    channels: "视频号"
  }
  return map[platform] || platform
}

const getPlatformTagType = (platform: string) => {
  const map: Record<string, any> = {
    xiaohongshu: "danger",
    douyin: "primary",
    kuaishou: "warning",
    channels: "success"
  }
  return map[platform] || "info"
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

<style scoped>
.accounts-container { padding: 10px 0; }
.account-card { border-radius: 8px; }
.mb-4 { margin-bottom: 16px; }
.mb-3 { margin-bottom: 12px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }
.mr-1 { margin-right: 4px; }
.pt-3 { padding-top: 12px; }
.border-t { border-top: 1px solid #f1f5f9; }
.flex { display: flex; }
.flex-col { flex-direction: column; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.gap-4 { gap: 16px; }
.font-bold { font-weight: 600; }
.text-lg { font-size: 18px; }
.text-base { font-size: 15px; }
.text-sm { font-size: 14px; }
.text-xs { font-size: 12px; }
.text-gray-400 { color: #94a3b8; }
.text-gray-500 { color: #64748b; }
.text-gray-600 { color: #475569; }
.text-center { text-align: center; }
.qrcode-wrapper { min-height: 240px; }
</style>
