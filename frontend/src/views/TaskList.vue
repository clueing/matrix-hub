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
          <el-button @click="loadTasks">
            <el-icon class="mr-1"><Refresh /></el-icon> 刷新
          </el-button>
          <el-button type="info" @click="showLogDrawer = true">
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
                    <el-tag v-else type="info" size="small">排队中</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="error_message" label="错误提示" min-width="180">
                  <template #default="{ row: sub }">
                    <span v-if="sub.error_message" class="text-xs text-red-500">{{ sub.error_message }}</span>
                    <span v-else class="text-gray-400">-</span>
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
            <el-tag v-else type="info">待排期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.slice(0, 19).replace('T', ' ') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button v-if="row.fail_count > 0" size="small" type="warning" link @click="handleRetry(row.id)">
              重试失败
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 实时运行日志抽屉 -->
    <el-drawer v-model="showLogDrawer" title="实时执行日志" size="45%">
      <div class="log-terminal bg-slate-900 text-slate-100 p-4 rounded font-mono text-xs overflow-y-auto">
        <div v-if="logs.length === 0" class="text-slate-500 py-8 text-center">暂无实时日志事件</div>
        <div v-for="(log, idx) in logs" :key="idx" class="log-line mb-1">
          <span class="text-slate-400 mr-2">[{{ log.time }}]</span>
          <span :class="getLogLevelClass(log.level)">[{{ log.level }}]</span>
          <span class="ml-2">{{ log.message }}</span>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue"
import { ElMessage } from "element-plus"
import { Refresh, Document } from "@element-plus/icons-vue"
import { getTasks, getTaskDetails, retryTask } from "../api"

const loading = ref(false)
const tasks = ref<any[]>([])
const statusFilter = ref("")
const showLogDrawer = ref(false)
const logs = ref<any[]>([])

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
