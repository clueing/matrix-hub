import axios from "axios"

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000
})

// 统一响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || "网络请求失败"
    return Promise.reject(new Error(msg))
  }
)

// ==================== 账号管理接口 ====================
export const getAccounts = (params?: { platform?: string; group_name?: string; status?: string }) =>
  apiClient.get("/accounts", { params })

export const startLogin = (data: { platform: string; group_name?: string; proxy_url?: string }) =>
  apiClient.post("/accounts/login/start", data)

export const checkAccountHealth = (accountId: string) =>
  apiClient.get(`/accounts/${accountId}/check`)

export const launchAssist = (accountId: string) =>
  apiClient.post(`/accounts/${accountId}/assist`)

export const updateAccount = (accountId: string, data: { account_name?: string; group_name?: string; proxy_url?: string }) =>
  apiClient.patch(`/accounts/${accountId}`, data)

export const deleteAccount = (accountId: string) =>
  apiClient.delete(`/accounts/${accountId}`)

export const getExportAccountUrl = (accountId: string) =>
  `/api/accounts/${accountId}/export`

export const importAccount = (formData: FormData, overwrite: boolean = true) =>
  apiClient.post(`/accounts/import?overwrite=${overwrite}`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  })

// ==================== 发布任务接口 ====================
export const getTasks = (params?: { status?: string }) =>
  apiClient.get("/tasks", { params })

export const getTaskDetails = (taskId: string) =>
  apiClient.get(`/tasks/${taskId}`)

export const createTask = (data: any) =>
  apiClient.post("/tasks", data)

export const retryTask = (taskId: string) =>
  apiClient.post(`/tasks/${taskId}/retry`)

// ==================== 视频文件接口 ====================
export const scanFolder = (folderPath: string) =>
  apiClient.post("/videos/scan-folder", { folder_path: folderPath })

export const verifyVideo = (videoPath: string) =>
  apiClient.post("/videos/verify", { video_path: videoPath })

// ==================== 系统设置接口 ====================
export const getSettings = () =>
  apiClient.get("/settings")

export const updateSettings = (settings: Record<string, string>) =>
  apiClient.put("/settings", { settings })

export const testWebhook = (data: { webhook_url: string; channel: string }) =>
  apiClient.post("/settings/test-webhook", data)
