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

export const cancelTask = (taskId: string) =>
  apiClient.post(`/tasks/${taskId}/cancel`)

export const deleteTask = (taskId: string) =>
  apiClient.delete(`/tasks/${taskId}`)

export const cancelSubtask = (subtaskId: string) =>
  apiClient.post(`/tasks/subtasks/${subtaskId}/cancel`)

export const deleteSubtask = (subtaskId: string) =>
  apiClient.delete(`/tasks/subtasks/${subtaskId}`)

export const clearFailedTasks = () =>
  apiClient.delete("/tasks/failed/clear")

export const updateSubtask = (subtaskId: string, data: any) =>
  apiClient.patch(`/tasks/subtasks/${subtaskId}`, data)

export const retrySubtask = (subtaskId: string) =>
  apiClient.post(`/tasks/subtasks/${subtaskId}/retry`)

export const verifySubtask = (subtaskId: string, data: { code?: string; action: "submit" | "resend" | "cancel" }) =>
  apiClient.post(`/tasks/subtasks/${subtaskId}/verify`, data)

export const getTaskLogs = (taskId: string, subtaskId?: string) =>
  apiClient.get(`/tasks/${taskId}/logs`, { params: { subtask_id: subtaskId } })

// ==================== 视频文件接口 ====================
export const scanFolder = (folderPath: string) =>
  apiClient.post("/videos/scan-folder", { folder_path: folderPath })

export const verifyVideo = (videoPath: string) =>
  apiClient.post("/videos/verify", { video_path: videoPath })

export const pickLocalFile = () =>
  apiClient.post("/videos/pick-file")

export const pickLocalFolder = () =>
  apiClient.post("/videos/pick-folder")

export const uploadVideoFile = (formData: FormData) =>
  apiClient.post("/videos/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  })

// ==================== 系统设置接口 ====================
export const getSettings = () =>
  apiClient.get("/settings")

export const updateSettings = (settings: Record<string, string>) =>
  apiClient.put("/settings", { settings })

export const testWebhook = (data: { webhook_url: string; channel: string }) =>
  apiClient.post("/settings/test-webhook", data)

// ==================== 数据资产与监控接口 ====================
export const getMetricsOverview = () =>
  apiClient.get("/metrics/overview")

export const syncMetrics = (accountId?: string) =>
  apiClient.post("/metrics/sync", accountId ? { account_id: accountId } : {})

export const syncSingleAccountMetrics = (accountId: string) =>
  apiClient.post(`/metrics/sync/${accountId}`)

