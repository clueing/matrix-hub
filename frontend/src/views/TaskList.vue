<template>
  <div class="tasklist-container">
    <el-card shadow="never" class="mb-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center gap-4">
          <span class="font-bold text-lg">任务调度看板</span>
          <el-radio-group v-model="statusFilter" size="small" @change="loadTasks">
            <el-radio-button label="">全部状态</el-radio-button>
            <el-radio-button label="processing">执行中</el-radio-button>
            <el-radio-button label="completed">已完成</el-radio-button>
            <el-radio-button label="failed">失败</el-radio-button>
          </el-radio-group>
        </div>
        <div class="flex gap-2">
          <el-popconfirm 
            title="确定要清理所有失败的任务与失败子作品吗？" 
            @confirm="handleClearFailedTasks"
          >
            <template #reference>
              <el-button type="danger" plain :disabled="!hasFailedTasks">
                <el-icon class="mr-1"><Delete /></el-icon> 清理失败任务
              </el-button>
            </template>
          </el-popconfirm>
          <el-button @click="loadTasks">
            <el-icon class="mr-1"><Refresh /></el-icon> 刷新
          </el-button>
          <el-button type="info" @click="openGlobalLogDrawer">
            <el-icon class="mr-1"><Document /></el-icon> 实时运行日志
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 任务主列表 -->
    <el-card shadow="never">
      <el-table :data="tasks" v-loading="loading" style="width: 100%" row-key="id">
        <!-- 展开列：展示具体的每个账号子任务 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="p-4 bg-slate-50 rounded">
              <div class="font-bold text-sm mb-2 text-gray-700">子作品执行明细：</div>
              <el-table :data="row.subtasks || []" size="small" border>
                <el-table-column prop="account_name" label="目标账号" width="160">
                  <template #default="{ row: sub }">
                    <div class="flex items-center gap-1">
                      <span>{{ sub.account_name }}</span>
                      <el-tag size="small" :type="sub.platform === 'xiaohongshu' ? 'danger' : 'primary'">
                        {{ sub.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                      </el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="title" label="作品标题" min-width="200" show-overflow-tooltip />
                <el-table-column prop="schedule_mode" label="调度方式" width="130" align="center">
                  <template #default="{ row: sub }">
                    <el-tag v-if="sub.schedule_mode === 'immediate'" size="small" type="info">立即错峰</el-tag>
                    <el-tag v-else-if="sub.schedule_mode === 'platform_native'" size="small" type="success">平台原生定时</el-tag>
                    <el-tag v-else size="small" type="warning">本地定时</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="预约时间" width="160" align="center">
                  <template #default="{ row: sub }">
                    {{ sub.scheduled_at ? sub.scheduled_at.slice(0, 16).replace('T', ' ') : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="110" align="center">
                  <template #default="{ row: sub }">
                    <el-tag v-if="sub.status === 'published'" type="success" size="small">已发布</el-tag>
                    <el-tag v-else-if="sub.status === 'uploading'" type="primary" size="small">上传中</el-tag>
                    <el-tag v-else-if="sub.status === 'failed'" type="danger" size="small">发布失败</el-tag>
                    <el-tag v-else-if="sub.status === 'cancelled'" type="info" size="small">已取消</el-tag>
                    <el-tag v-else type="info" size="small">排队中</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="error_message" label="执行提示" min-width="180">
                  <template #default="{ row: sub }">
                    <span v-if="sub.error_message" class="text-xs text-red-500">{{ sub.error_message }}</span>
                    <span v-else class="text-gray-400">-</span>
                  </template>
                </el-table-column>
                <!-- 子任务操作栏：发布成功前允许取消与编辑，失败或已取消时支持删除 -->
                <el-table-column label="操作" width="230" align="center">
                  <template #default="{ row: sub }">
                    <div class="flex items-center justify-center gap-1">
                      <el-button size="small" type="info" link @click="openTaskLogDrawer(row, sub)">
                        日志
                      </el-button>
                      <el-button 
                        v-if="sub.status !== 'published'" 
                        size="small" 
                        type="primary" 
                        link 
                        @click="openEditSubtaskDialog(sub)"
                      >
                        编辑
                      </el-button>
                      <el-popconfirm 
                        v-if="sub.status !== 'published' && sub.status !== 'cancelled'" 
                        title="确定要取消该子任务吗？" 
                        @confirm="handleCancelSubtask(sub.id)"
                      >
                        <template #reference>
                          <el-button size="small" type="danger" link>取消</el-button>
                        </template>
                      </el-popconfirm>
                      <el-button 
                        v-if="sub.status === 'failed'" 
                        size="small" 
                        type="warning" 
                        link 
                        @click="handleRetrySubtask(sub.id)"
                      >
                        重试
                      </el-button>
                      <el-popconfirm 
                        v-if="sub.status === 'failed' || sub.status === 'cancelled'" 
                        title="确定要删除该子作品记录吗？" 
                        @confirm="handleDeleteSubtask(sub.id)"
                      >
                        <template #reference>
                          <el-button size="small" type="danger" link>删除</el-button>
                        </template>
                      </el-popconfirm>
                      <span v-if="sub.status === 'published'" class="text-xs text-green-600 font-medium">已完成</span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="task_type" label="模式" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.task_type === 'one_to_many' ? 'info' : 'warning'">
              {{ row.task_type === 'one_to_many' ? '1对多' : '多对多' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="子任务总数" width="110" align="center" />
        <el-table-column prop="success_count" label="成功数" width="90" align="center">
          <template #default="{ row }">
            <span class="text-green-600 font-bold">{{ row.success_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="fail_count" label="失败数" width="90" align="center">
          <template #default="{ row }">
            <span :class="row.fail_count > 0 ? 'text-red-500 font-bold' : ''">{{ row.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="160">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.total_count ? Math.round(((row.success_count + row.fail_count) / row.total_count) * 100) : 0" 
              :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="主状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success">已完成</el-tag>
            <el-tag v-else-if="row.status === 'processing'" type="primary">执行中</el-tag>
            <el-tag v-else-if="row.status === 'partial_failed'" type="warning">部分失败</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else-if="row.status === 'cancelled'" type="info">已取消</el-tag>
            <el-tag v-else type="info">待排期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.slice(0, 19).replace('T', ' ') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <div class="flex items-center justify-center gap-1">
              <el-button size="small" type="primary" link @click="openTaskLogDrawer(row)">
                日志
              </el-button>
              <el-button v-if="row.fail_count > 0" size="small" type="warning" link @click="handleRetry(row.id)">
                重试失败
              </el-button>
              <el-popconfirm 
                v-if="row.status === 'processing' || row.status === 'pending' || row.status === 'partial_failed'" 
                title="确定要取消该任务所有未发布的子任务吗？" 
                @confirm="handleCancelTask(row.id)"
              >
                <template #reference>
                  <el-button size="small" type="danger" link>取消任务</el-button>
                </template>
              </el-popconfirm>
              <el-popconfirm title="确定要删除此任务记录吗？" @confirm="handleDeleteTask(row.id)">
                <template #reference>
                  <el-button size="small" type="info" link>删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑子任务模态框 -->
    <el-dialog v-model="editDialogVisible" title="编辑子作品发布配置" width="560px">
      <el-form :model="editForm" label-width="110px">
        <el-form-item label="目标账号">
          <el-tag :type="editingSubtask?.platform === 'xiaohongshu' ? 'danger' : 'primary'">
            {{ editingSubtask?.platform === 'xiaohongshu' ? '小红书' : '抖音' }} ({{ editingSubtask?.account_name }})
          </el-tag>
        </el-form-item>
        <el-form-item label="作品标题" required>
          <el-input v-model="editForm.title" placeholder="作品标题 (小红书限20字以内)" />
        </el-form-item>
        <el-form-item label="正文描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" placeholder="作品正文描述..." />
        </el-form-item>
        <el-form-item label="话题标签">
          <el-select 
            v-model="editForm.tags" 
            multiple 
            filterable 
            allow-create 
            default-first-option 
            placeholder="输入标签后回车" 
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item v-if="editingSubtask?.schedule_mode !== 'immediate'" label="预约发布时间">
          <el-date-picker
            v-model="editForm.scheduled_at"
            type="datetime"
            placeholder="选择预约公开时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="独立封面图">
          <el-input v-model="editForm.cover_path" placeholder="可选图片绝对路径" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="submitEditSubtask">保存修改</el-button>
      </template>
    </el-dialog>

    <!-- 任务执行与持久化日志抽屉 -->
    <el-drawer 
      v-model="showLogDrawer" 
      size="50%"
      destroy-on-close
    >
      <template #header>
        <div class="flex items-center justify-between w-full pr-4">
          <div class="flex items-center gap-2">
            <el-icon :size="18"><Document /></el-icon>
            <span class="font-bold text-base text-slate-800">{{ drawerTitle }}</span>
            <el-tag v-if="selectedTask" size="small" type="success" effect="light">
              SQLite 数据库持久化
            </el-tag>
          </div>
          <div class="flex items-center gap-2">
            <el-select 
              v-model="logLevelFilter" 
              size="small" 
              placeholder="日志等级" 
              style="width: 105px;"
            >
              <el-option label="全部等级" value="" />
              <el-option label="SUCCESS" value="SUCCESS" />
              <el-option label="ERROR" value="ERROR" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="INFO" value="INFO" />
            </el-select>
            <el-button size="small" @click="handleRefreshLogs" :loading="loadingTaskLogs">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <el-button size="small" @click="copyAllLogs">
              复制日志
            </el-button>
          </div>
        </div>
      </template>

      <!-- 子任务快速切换栏（仅当选择主任务且有子任务时） -->
      <div v-if="selectedTask && selectedTask.subtasks && selectedTask.subtasks.length > 1" class="mb-3 flex items-center gap-2 flex-wrap bg-slate-100 p-2 rounded">
        <span class="text-xs text-slate-500">过滤子账号:</span>
        <el-tag 
          size="small" 
          :effect="!selectedSubtask ? 'dark' : 'plain'"
          class="cursor-pointer"
          @click="selectSubtaskFilter(null)"
        >
          全部账号 ({{ selectedTask.subtasks.length }})
        </el-tag>
        <el-tag 
          v-for="sub in selectedTask.subtasks" 
          :key="sub.id"
          size="small"
          :effect="selectedSubtask?.id === sub.id ? 'dark' : 'plain'"
          :type="sub.platform === 'xiaohongshu' ? 'danger' : 'primary'"
          class="cursor-pointer"
          @click="selectSubtaskFilter(sub)"
        >
          {{ sub.account_name }}
        </el-tag>
      </div>

      <div class="log-terminal bg-slate-900 text-slate-100 p-4 rounded font-mono text-xs overflow-y-auto">
        <div v-if="displayedLogs.length === 0" class="text-slate-500 py-12 text-center">
          <el-icon :size="24" class="mb-2"><Document /></el-icon>
          <div>{{ loadingTaskLogs ? '正在读取数据库历史持久化日志...' : '暂无符合条件的日志记录' }}</div>
        </div>
        <div v-for="(log, idx) in displayedLogs" :key="idx" class="log-line mb-1">
          <span class="text-slate-400 mr-2">[{{ log.time }}]</span>
          <span :class="getLogLevelClass(log.level)">[{{ log.level }}]</span>
          <span class="ml-2">{{ log.message }}</span>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { ElMessage } from "element-plus"
import { Refresh, Document, Delete } from "@element-plus/icons-vue"
import { 
  getTasks, getTaskDetails, retryTask, cancelTask, 
  deleteTask, cancelSubtask, updateSubtask, retrySubtask,
  deleteSubtask, clearFailedTasks, getTaskLogs
} from "../api"

const loading = ref(false)
const tasks = ref<any[]>([])
const statusFilter = ref("")
const showLogDrawer = ref(false)
const logs = ref<any[]>([])

// 独立任务日志状态
const selectedTask = ref<any>(null)
const selectedSubtask = ref<any>(null)
const taskLogs = ref<any[]>([])
const loadingTaskLogs = ref(false)
const logLevelFilter = ref("")

const drawerTitle = computed(() => {
  if (selectedTask.value) {
    let title = `任务日志: ${selectedTask.value.name}`
    if (selectedSubtask.value) {
      title += ` - ${selectedSubtask.value.account_name}`
    }
    return title
  }
  return "系统实时运行日志"
})

const displayedLogs = computed(() => {
  const source = selectedTask.value ? taskLogs.value : logs.value
  if (!logLevelFilter.value) return source
  return source.filter((l: any) => l.level === logLevelFilter.value)
})

const openTaskLogDrawer = (task: any, subtask?: any) => {
  selectedTask.value = task
  selectedSubtask.value = subtask || null
  showLogDrawer.value = true
  loadTaskLogs()
}

const openGlobalLogDrawer = () => {
  selectedTask.value = null
  selectedSubtask.value = null
  showLogDrawer.value = true
}

const selectSubtaskFilter = (sub: any) => {
  selectedSubtask.value = sub
  loadTaskLogs()
}

const loadTaskLogs = async () => {
  if (!selectedTask.value) return
  loadingTaskLogs.value = true
  try {
    const res: any = await getTaskLogs(selectedTask.value.id, selectedSubtask.value?.id)
    taskLogs.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loadingTaskLogs.value = false
  }
}

const handleRefreshLogs = () => {
  if (selectedTask.value) {
    loadTaskLogs()
  }
}

const copyAllLogs = () => {
  const text = displayedLogs.value.map((l: any) => `[${l.time}] [${l.level}] ${l.message}`).join("\n")
  if (!text) {
    ElMessage.info("暂无日志可复制")
    return
  }
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success("日志已复制到剪贴板！")
  }).catch(() => {
    ElMessage.warning("复制失败，请手动选择复制")
  })
}

const hasFailedTasks = computed(() => {
  return tasks.value.some(t => t.fail_count > 0 || t.status === 'failed' || t.status === 'partial_failed')
})

// 编辑子任务模态框状态
const editDialogVisible = ref(false)
const editingSubtask = ref<any>(null)
const savingEdit = ref(false)
const editForm = ref({
  title: "",
  description: "",
  tags: [] as string[],
  scheduled_at: null as string | null,
  cover_path: ""
})

let ws: WebSocket | null = null

const initWebSocket = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.event === "log_append") {
        logs.value.unshift(msg.data)
        if (logs.value.length > 300) logs.value.pop()

        // 若当前打开了专属任务日志抽屉且 ID 匹配，追加到 taskLogs
        if (selectedTask.value && msg.data.task_id === selectedTask.value.id) {
          if (!selectedSubtask.value || msg.data.subtask_id === selectedSubtask.value.id) {
            taskLogs.value.push(msg.data)
          }
        }
      } else if (msg.event === "subtask_status_changed" || msg.event === "task_status_changed") {
        loadTasks()
      }
    } catch (e) {}
  }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const res: any = await getTasks({ status: statusFilter.value || undefined })
    const mainTasks = res.data || []
    
    // 加载每个任务的子任务详情
    for (const t of mainTasks) {
      try {
        const detailRes: any = await getTaskDetails(t.id)
        t.subtasks = detailRes.data?.subtasks || []
      } catch (err) {}
    }
    tasks.value = mainTasks
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

const handleRetry = async (taskId: string) => {
  try {
    const res: any = await retryTask(taskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleCancelTask = async (taskId: string) => {
  try {
    const res: any = await cancelTask(taskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleDeleteTask = async (taskId: string) => {
  try {
    const res: any = await deleteTask(taskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleCancelSubtask = async (subtaskId: string) => {
  try {
    const res: any = await cancelSubtask(subtaskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleRetrySubtask = async (subtaskId: string) => {
  try {
    const res: any = await retrySubtask(subtaskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleDeleteSubtask = async (subtaskId: string) => {
  try {
    const res: any = await deleteSubtask(subtaskId)
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleClearFailedTasks = async () => {
  try {
    const res: any = await clearFailedTasks()
    ElMessage.success(res.message)
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const openEditSubtaskDialog = (sub: any) => {
  editingSubtask.value = sub
  editForm.value = {
    title: sub.title,
    description: sub.description || "",
    tags: [...(sub.tags || [])],
    scheduled_at: sub.scheduled_at || null,
    cover_path: sub.cover_path || ""
  }
  editDialogVisible.value = true
}

const submitEditSubtask = async () => {
  if (!editingSubtask.value) return
  if (!editForm.value.title.trim()) {
    ElMessage.warning("作品标题不能为空")
    return
  }
  savingEdit.value = true
  try {
    await updateSubtask(editingSubtask.value.id, editForm.value)
    ElMessage.success("子作品配置修改成功！")
    editDialogVisible.value = false
    loadTasks()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    savingEdit.value = false
  }
}

const getLogLevelClass = (level: string) => {
  switch (level) {
    case "SUCCESS": return "text-emerald-400 font-bold"
    case "ERROR": return "text-rose-400 font-bold"
    case "WARNING": return "text-amber-400 font-bold"
    default: return "text-sky-300"
  }
}

onMounted(() => {
  loadTasks()
  initWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.tasklist-container { padding: 10px 0; }
.mb-1 { margin-bottom: 4px; }
.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.ml-2 { margin-left: 8px; }
.p-4 { padding: 16px; }
.bg-slate-50 { background-color: #f8fafc; }
.bg-slate-900 { background-color: #0f172a; }
.text-slate-100 { color: #f1f5f9; }
.text-slate-400 { color: #94a3b8; }
.text-slate-500 { color: #64748b; }
.text-emerald-400 { color: #34d399; }
.text-rose-400 { color: #fb7185; }
.text-amber-400 { color: #fbbf24; }
.text-sky-300 { color: #7dd3fc; }
.text-green-600 { color: #16a34a; }
.text-red-500 { color: #ef4444; }
.text-gray-400 { color: #94a3b8; }
.text-gray-700 { color: #334155; }
.text-xs { font-size: 12px; }
.text-sm { font-size: 14px; }
.text-lg { font-size: 18px; }
.font-bold { font-weight: 600; }
.font-mono { font-family: monospace; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.gap-1 { gap: 4px; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.log-terminal { height: 80vh; }
.log-line { line-height: 1.5; word-break: break-all; }
</style>
