<template>
  <div class="space-y-6 max-w-7xl mx-auto pb-16">
    <!-- 顶栏：标题与操作看板 (官方纯净风格) -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-foreground">任务调度看板</h1>
        <p class="text-xs text-muted-foreground mt-0.5">
          全流程监控多平台矩阵分发进度、调度排期队列与原生/本地定时执行
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- 状态快速筛选 -->
        <div class="flex items-center rounded-lg border border-border bg-background p-1 text-xs">
          <button
            v-for="st in [
              { label: '全部', value: '' },
              { label: '执行中', value: 'processing' },
              { label: '已完成', value: 'completed' },
              { label: '失败', value: 'failed' }
            ]"
            :key="st.value"
            type="button"
            :class="[
              'px-2.5 py-1 font-medium rounded-md transition-colors',
              statusFilter === st.value
                ? 'bg-secondary text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            ]"
            @click="statusFilter = st.value; loadTasks()"
          >
            {{ st.label }}
          </button>
        </div>

        <!-- 操作按钮组 -->
        <Button
          v-if="hasFailedTasks"
          variant="destructive"
          size="sm"
          class="h-8 text-xs gap-1"
          @click="confirmClearFailedTasks"
        >
          <Trash2 class="w-3.5 h-3.5" /> 清理失败
        </Button>

        <Button
          variant="outline"
          size="sm"
          class="h-8 text-xs gap-1"
          :disabled="loading"
          @click="loadTasks"
        >
          <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" /> 刷新
        </Button>

        <Button
          variant="outline"
          size="sm"
          class="h-8 text-xs gap-1"
          @click="openGlobalLogDrawer"
        >
          <Terminal class="w-3.5 h-3.5" /> 运行日志
        </Button>
      </div>
    </div>

    <!-- 任务列表容器 -->
    <div v-if="loading && tasks.length === 0" class="py-20 text-center text-muted-foreground">
      <RefreshCw class="w-7 h-7 mx-auto mb-2 animate-spin text-primary opacity-60" />
      <p class="text-xs">正在加载任务调度看板...</p>
    </div>

    <div v-else-if="tasks.length === 0" class="py-20 text-center bg-card border border-border rounded-xl shadow-sm">
      <ListChecks class="w-10 h-10 mx-auto mb-3 text-muted-foreground/40" />
      <h3 class="text-sm font-semibold text-foreground">暂无矩阵分发任务</h3>
      <p class="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
        当前还没有创建任何分发任务，可以点击下方按钮创建第一批任务。
      </p>
      <div class="mt-4">
        <router-link to="/publish">
          <Button size="sm">
            <Plus class="w-4 h-4 mr-1.5" /> 立即创建新任务
          </Button>
        </router-link>
      </div>
    </div>

    <!-- 任务卡片列表 -->
    <div v-else class="space-y-3">
      <Card
        v-for="task in tasks"
        :key="task.id"
        class="border-border shadow-sm overflow-hidden"
      >
        <!-- 主任务行：左信息、中进度条（固定宽度）、右操作区（严格固定宽度 w-56），保证进度条在所有行像素级绝对对齐 -->
        <div class="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-card">
          <!-- 左侧：折叠按钮与任务主体信息 -->
          <div class="flex items-center gap-3 min-w-0 flex-1">
            <button
              type="button"
              class="p-1 rounded-md border border-border hover:bg-accent text-muted-foreground hover:text-foreground transition-colors flex-shrink-0"
              @click="toggleExpand(task.id)"
              :title="isExpanded(task.id) ? '折叠子作品明细' : '展开子作品明细'"
            >
              <ChevronDown :class="['w-4 h-4 transition-transform duration-200', isExpanded(task.id) ? 'rotate-180' : '']" />
            </button>

            <div class="space-y-1 min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-semibold text-sm text-foreground tracking-tight truncate max-w-md" :title="task.name">
                  {{ task.name }}
                </span>
                <Badge variant="outline" class="text-[10px] px-1.5 py-0">
                  {{ task.task_type === 'one_to_many' ? '1对多' : '多对多' }}
                </Badge>
                <Badge :variant="getStatusBadgeVariant(task.status)" class="text-[10px] px-1.5 py-0 font-medium">
                  {{ getStatusText(task.status) }}
                </Badge>
              </div>

              <div class="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                <span>共 {{ task.total_count }} 个作品</span>
                <span class="text-border">•</span>
                <span class="text-emerald-600">成功 {{ task.success_count }}</span>
                <span class="text-border">•</span>
                <span :class="task.fail_count > 0 ? 'text-destructive font-medium' : 'text-muted-foreground'">
                  失败 {{ task.fail_count }}
                </span>
                <span class="text-border">•</span>
                <span class="font-mono text-[11px]">
                  {{ formatTime(task.created_at) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 右侧区域：进度条（固定宽 w-36）+ 操作栏（严格固定宽 w-56） -->
          <div class="flex items-center gap-6 flex-shrink-0 justify-between md:justify-end pt-2 md:pt-0 border-t md:border-t-0 border-border">
            <!-- 进度条：严格固定宽度 144px (w-36)，确保所有卡片对齐 -->
            <div class="w-36 flex-shrink-0 space-y-1">
              <div class="flex items-center justify-between text-xs">
                <span class="text-muted-foreground">进度</span>
                <span class="font-mono font-medium text-foreground">{{ calcProgress(task) }}%</span>
              </div>
              <Progress :model-value="calcProgress(task)" class="h-1.5" />
            </div>

            <!-- 操作按钮区域：严格固定宽度 224px (w-56)，右对齐，不同数量按钮绝不导致左侧进度条偏移 -->
            <div class="w-56 flex-shrink-0 flex items-center justify-end gap-1">
              <Button
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
                @click="openTaskLogDrawer(task)"
              >
                <Terminal class="w-3 h-3 mr-1" /> 日志
              </Button>

              <Button
                v-if="task.fail_count > 0"
                variant="outline"
                size="sm"
                class="h-7 px-2 text-xs text-amber-600 hover:text-amber-700"
                @click="handleRetry(task.id)"
              >
                重试
              </Button>

              <Button
                v-if="task.status === 'processing' || task.status === 'pending' || task.status === 'partial_failed'"
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-destructive hover:bg-destructive/10"
                @click="confirmCancelTask(task.id)"
              >
                取消
              </Button>

              <Button
                variant="ghost"
                size="sm"
                class="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"
                @click="confirmDeleteTask(task.id)"
                title="删除任务记录"
              >
                <Trash2 class="w-3 h-3" />
              </Button>
            </div>
          </div>
        </div>

        <!-- 展开后：子任务明细表格 -->
        <div v-if="isExpanded(task.id)" class="border-t border-border bg-muted/20 p-3">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold text-foreground">
              子作品明细 ({{ task.subtasks?.length || 0 }} 个目标账号)
            </span>
          </div>

          <div class="border border-border rounded-lg overflow-hidden bg-card">
            <Table>
              <TableHeader>
                <TableRow class="bg-muted/40">
                  <TableHead class="text-xs font-semibold w-36">目标账号</TableHead>
                  <TableHead class="text-xs font-semibold min-w-[180px]">作品标题</TableHead>
                  <TableHead class="text-xs font-semibold w-24 text-center">调度方式</TableHead>
                  <TableHead class="text-xs font-semibold w-36 text-center">预约时间</TableHead>
                  <TableHead class="text-xs font-semibold w-20 text-center">状态</TableHead>
                  <TableHead class="text-xs font-semibold min-w-[140px]">执行反馈</TableHead>
                  <TableHead class="text-xs font-semibold w-40 text-center">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="sub in task.subtasks || []"
                  :key="sub.id"
                  class="text-xs hover:bg-muted/30"
                >
                  <!-- 目标账号 -->
                  <TableCell>
                    <div class="flex items-center gap-1.5">
                      <Badge variant="outline" class="text-[9px] px-1 py-0 uppercase">
                        {{ sub.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                      </Badge>
                      <span class="font-medium text-foreground truncate max-w-[90px]" :title="sub.account_name">
                        {{ sub.account_name }}
                      </span>
                    </div>
                  </TableCell>

                  <!-- 标题与数据资产胶囊 -->
                  <TableCell class="font-medium max-w-xs">
                    <div class="space-y-1 py-0.5">
                      <div class="truncate text-foreground text-xs" :title="sub.title">{{ sub.title }}</div>
                      <!-- 已发布作品的实时数据胶囊 -->
                      <div v-if="sub.status === 'published'" class="flex items-center gap-2 text-[10px] text-muted-foreground font-mono">
                        <span class="flex items-center gap-0.5" title="播放/阅读量">
                          <Eye class="w-3 h-3 text-sky-500" />
                          <span>{{ formatNumber(sub.view_count) }}</span>
                        </span>
                        <span class="flex items-center gap-0.5" title="获赞数">
                          <Heart class="w-3 h-3 text-rose-500" />
                          <span>{{ formatNumber(sub.like_count) }}</span>
                        </span>
                        <span class="flex items-center gap-0.5" title="评论数">
                          <MessageSquare class="w-3 h-3 text-amber-500" />
                          <span>{{ formatNumber(sub.comment_count) }}</span>
                        </span>
                        <a
                          v-if="sub.platform_work_url"
                          :href="sub.platform_work_url"
                          target="_blank"
                          class="hover:text-primary transition-colors ml-0.5"
                          title="在平台原站打开作品"
                        >
                          <ExternalLink class="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </div>
                  </TableCell>

                  <!-- 调度方式 -->
                  <TableCell class="text-center">
                    <span v-if="sub.schedule_mode === 'immediate'" class="text-muted-foreground text-[11px]">
                      立即错峰
                    </span>
                    <span v-else-if="sub.schedule_mode === 'platform_native'" class="text-primary text-[11px]">
                      平台原生
                    </span>
                    <span v-else class="text-muted-foreground text-[11px]">
                      本地定时
                    </span>
                  </TableCell>

                  <!-- 预约公开时间 -->
                  <TableCell class="text-center font-mono text-[11px] text-muted-foreground">
                    {{ sub.scheduled_at ? formatTime(sub.scheduled_at) : '-' }}
                  </TableCell>

                  <!-- 状态 -->
                  <TableCell class="text-center">
                    <Badge :variant="getSubtaskStatusBadgeVariant(sub.status)" class="text-[10px] px-1.5 py-0">
                      {{ getSubtaskStatusText(sub.status) }}
                    </Badge>
                  </TableCell>

                  <!-- 执行反馈 -->
                  <TableCell>
                    <span v-if="sub.error_message" class="text-[11px] text-destructive line-clamp-1" :title="sub.error_message">
                      {{ sub.error_message }}
                    </span>
                    <span v-else class="text-muted-foreground/60 text-xs">-</span>
                  </TableCell>

                  <!-- 操作 -->
                  <TableCell class="text-center">
                    <div class="flex items-center justify-center gap-1">
                      <!-- 等待二次验证时显示醒目的输入验证码按钮 -->
                      <Button
                        v-if="sub.status === 'waiting_manual'"
                        variant="default"
                        size="sm"
                        class="h-6 px-2 text-[11px] bg-amber-600 hover:bg-amber-700 text-white font-medium shadow-sm"
                        @click="openManualVerification(sub)"
                      >
                        <ShieldCheck class="w-3 h-3 mr-1" /> 输入验证码
                      </Button>

                      <Button
                        variant="ghost"
                        size="sm"
                        class="h-6 px-1.5 text-[11px] text-muted-foreground hover:text-foreground"
                        @click="openTaskLogDrawer(task, sub)"
                      >
                        日志
                      </Button>

                      <Button
                        v-if="sub.status !== 'published'"
                        variant="ghost"
                        size="sm"
                        class="h-6 px-1.5 text-[11px] text-primary"
                        @click="openEditSubtaskDialog(sub)"
                      >
                        编辑
                      </Button>

                      <Button
                        v-if="sub.status !== 'published' && sub.status !== 'cancelled'"
                        variant="ghost"
                        size="sm"
                        class="h-6 px-1.5 text-[11px] text-destructive hover:bg-destructive/10"
                        @click="handleCancelSubtask(sub.id)"
                      >
                        取消
                      </Button>

                      <Button
                        v-if="sub.status === 'failed'"
                        variant="ghost"
                        size="sm"
                        class="h-6 px-1.5 text-[11px] text-amber-600"
                        @click="handleRetrySubtask(sub.id)"
                      >
                        重试
                      </Button>

                      <Button
                        v-if="sub.status === 'failed' || sub.status === 'cancelled'"
                        variant="ghost"
                        size="sm"
                        class="h-6 px-1 text-[11px] text-muted-foreground hover:text-destructive"
                        @click="handleDeleteSubtask(sub.id)"
                      >
                        <Trash2 class="w-3 h-3" />
                      </Button>

                      <span v-if="sub.status === 'published'" class="text-[11px] text-emerald-600 font-medium px-1">
                        已完成
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>
      </Card>
    </div>

    <!-- 编辑子任务模态框 (Dialog) -->
    <Dialog :open="editDialogVisible" @update:open="val => editDialogVisible = val">
      <DialogContent class="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle class="text-base font-semibold">编辑子作品发布配置</DialogTitle>
          <DialogDescription class="text-xs">
            修改分发到该账号的独立标题、描述或预约时间
          </DialogDescription>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div class="flex items-center gap-2 p-2 rounded-md bg-muted/40 border border-border">
            <Badge variant="outline" class="text-[9px]">
              {{ editingSubtask?.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
            </Badge>
            <span class="text-xs font-medium text-foreground">{{ editingSubtask?.account_name }}</span>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between">
              <label class="text-xs font-medium text-foreground">作品标题</label>
              <span class="text-[11px] text-muted-foreground font-mono">
                {{ editForm.title.length }}/{{ editingSubtask?.platform === 'xiaohongshu' ? 20 : 100 }}
              </span>
            </div>
            <Input
              v-model="editForm.title"
              :maxlength="editingSubtask?.platform === 'xiaohongshu' ? 20 : 100"
              placeholder="作品标题"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">正文描述</label>
            <Textarea v-model="editForm.description" rows="3" placeholder="作品正文描述..." />
          </div>

          <div v-if="editingSubtask?.schedule_mode !== 'immediate'" class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">预约发布时间</label>
            <Input type="datetime-local" v-model="editForm.scheduled_at" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-medium text-foreground">独立封面图</label>
            <Input v-model="editForm.cover_path" placeholder="可选图片绝对路径" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" @click="editDialogVisible = false">取消</Button>
          <Button variant="default" size="sm" :disabled="savingEdit" @click="submitEditSubtask">
            {{ savingEdit ? "保存中..." : "保存修改" }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 运行与持久化日志抽屉 (Sheet) -->
    <Sheet :open="showLogDrawer" @update:open="val => showLogDrawer = val">
      <SheetContent class="w-full sm:max-w-2xl flex flex-col p-0 gap-0">
        <div class="p-4 border-b border-border flex items-center justify-between bg-card">
          <div>
            <h2 class="text-sm font-semibold text-foreground leading-none">{{ drawerTitle }}</h2>
            <p class="text-[11px] text-muted-foreground mt-1">
              记录 Playwright 自动化驱动与矩阵平台接口日志
            </p>
          </div>

          <div class="flex items-center gap-2 pr-6">
            <select
              v-model="logLevelFilter"
              class="h-7 text-xs bg-background border border-border rounded-md px-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">全部等级</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="ERROR">ERROR</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
            </select>

            <Button variant="outline" size="sm" class="h-7 px-2 text-xs" :disabled="loadingTaskLogs" @click="handleRefreshLogs">
              <RefreshCw :class="['w-3 h-3', loadingTaskLogs ? 'animate-spin' : '']" />
            </Button>
            <Button variant="secondary" size="sm" class="h-7 px-2 text-xs" @click="copyAllLogs">
              <Copy class="w-3 h-3 mr-1" /> 复制
            </Button>
          </div>
        </div>

        <!-- 子任务过滤标签 -->
        <div
          v-if="selectedTask && selectedTask.subtasks && selectedTask.subtasks.length > 1"
          class="px-4 py-2 bg-muted/30 border-b border-border flex items-center gap-1.5 flex-wrap text-xs"
        >
          <span class="text-[11px] text-muted-foreground mr-1">过滤账号:</span>
          <button
            type="button"
            :class="[
              'px-2 py-0.5 rounded text-[11px] transition-colors',
              !selectedSubtask
                ? 'bg-foreground text-background font-medium'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            ]"
            @click="selectSubtaskFilter(null)"
          >
            全部 ({{ selectedTask.subtasks.length }})
          </button>
          <button
            v-for="sub in selectedTask.subtasks"
            :key="sub.id"
            type="button"
            :class="[
              'px-2 py-0.5 rounded text-[11px] transition-colors',
              selectedSubtask?.id === sub.id
                ? 'bg-foreground text-background font-medium'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            ]"
            @click="selectSubtaskFilter(sub)"
          >
            {{ sub.account_name }}
          </button>
        </div>

        <!-- 终端日志区域 -->
        <div class="flex-1 bg-slate-950 text-slate-100 p-4 font-mono text-xs overflow-y-auto select-text leading-relaxed">
          <div v-if="displayedLogs.length === 0" class="text-slate-500 py-16 text-center">
            <Terminal class="w-7 h-7 mx-auto mb-2 opacity-40" />
            <div>{{ loadingTaskLogs ? '正在读取持久化执行日志...' : '暂无日志记录' }}</div>
          </div>
          <div
            v-for="(log, idx) in displayedLogs"
            :key="idx"
            class="py-0.5 font-mono text-[11px] flex items-start gap-2 hover:bg-slate-900/60 px-1 rounded"
          >
            <span class="text-slate-500 flex-shrink-0 select-none">[{{ log.time }}]</span>
            <span :class="['flex-shrink-0 font-bold', getLogLevelClass(log.level)]">[{{ log.level }}]</span>
            <span class="break-all text-slate-300">{{ log.message }}</span>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import {
  ListChecks, Plus, Trash2, RefreshCw, Terminal, ChevronDown, Copy, ShieldCheck,
  Eye, Heart, MessageSquare, ExternalLink
} from "lucide-vue-next"

import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Sheet, SheetContent } from "@/components/ui/sheet"

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

const expandedTaskIds = ref<string[]>([])

const toggleExpand = (taskId: string) => {
  const idx = expandedTaskIds.value.indexOf(taskId)
  if (idx > -1) {
    expandedTaskIds.value.splice(idx, 1)
  } else {
    expandedTaskIds.value.push(taskId)
  }
}

const isExpanded = (taskId: string) => expandedTaskIds.value.includes(taskId)

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

const calcProgress = (task: any) => {
  if (!task.total_count) return 0
  return Math.round(((task.success_count + task.fail_count) / task.total_count) * 100)
}

const formatTime = (timeStr?: string) => {
  if (!timeStr) return "-"
  return timeStr.slice(0, 19).replace("T", " ")
}

const formatNumber = (num?: number) => {
  if (!num) return "0"
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + "w"
  }
  return num.toLocaleString()
}

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "completed": return "success"
    case "processing": return "info"
    case "partial_failed": return "warning"
    case "failed": return "destructive"
    case "cancelled": return "secondary"
    default: return "secondary"
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case "completed": return "已完成"
    case "processing": return "执行中"
    case "partial_failed": return "部分失败"
    case "failed": return "失败"
    case "cancelled": return "已取消"
    default: return "排队待执行"
  }
}

const getSubtaskStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "published": return "success"
    case "uploading": return "info"
    case "waiting_manual": return "warning"
    case "failed": return "destructive"
    case "cancelled": return "secondary"
    default: return "secondary"
  }
}

const getSubtaskStatusText = (status: string) => {
  switch (status) {
    case "published": return "已发布"
    case "uploading": return "上传中"
    case "waiting_manual": return "等待验证码"
    case "failed": return "失败"
    case "cancelled": return "已取消"
    default: return "排队中"
  }
}

const openManualVerification = (sub: any) => {
  window.dispatchEvent(new CustomEvent("open-verification-dialog", {
    detail: {
      subtask_id: sub.id,
      task_id: sub.task_id,
      account_id: sub.account_id,
      account_name: sub.account_name,
      platform: sub.platform,
      title: sub.title
    }
  }))
}

// 编辑子任务模态框状态
const editDialogVisible = ref(false)
const editingSubtask = ref<any>(null)
const savingEdit = ref(false)
const editForm = ref({
  title: "",
  description: "",
  tags: [] as string[],
  scheduled_at: "" as string,
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

    for (const t of mainTasks) {
      try {
        const detailRes: any = await getTaskDetails(t.id)
        t.subtasks = detailRes.data?.subtasks || []
      } catch (err) {}
    }
    tasks.value = mainTasks

    mainTasks.forEach((t: any) => {
      if (t.status === "processing" && !expandedTaskIds.value.includes(t.id)) {
        expandedTaskIds.value.push(t.id)
      }
    })
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

const confirmCancelTask = (taskId: string) => {
  ElMessageBox.confirm("确定要取消该任务所有未发布的子作品吗？", "提示", {
    type: "warning"
  }).then(async () => {
    try {
      const res: any = await cancelTask(taskId)
      ElMessage.success(res.message)
      loadTasks()
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  }).catch(() => {})
}

const confirmDeleteTask = (taskId: string) => {
  ElMessageBox.confirm("确定要删除此任务及其所有子作品记录吗？", "提示", {
    type: "warning"
  }).then(async () => {
    try {
      const res: any = await deleteTask(taskId)
      ElMessage.success(res.message)
      loadTasks()
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  }).catch(() => {})
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

const confirmClearFailedTasks = () => {
  ElMessageBox.confirm("确定要清理所有失败的任务与失败子作品吗？", "提示", {
    type: "warning"
  }).then(async () => {
    try {
      const res: any = await clearFailedTasks()
      ElMessage.success(res.message)
      loadTasks()
    } catch (e: any) {
      ElMessage.error(e.message)
    }
  }).catch(() => {})
}

const openEditSubtaskDialog = (sub: any) => {
  editingSubtask.value = sub
  editForm.value = {
    title: sub.title,
    description: sub.description || "",
    tags: [...(sub.tags || [])],
    scheduled_at: sub.scheduled_at ? sub.scheduled_at.slice(0, 16) : "",
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
    await updateSubtask(editingSubtask.value.id, {
      title: editForm.value.title,
      description: editForm.value.description,
      tags: editForm.value.tags,
      scheduled_at: editForm.value.scheduled_at || null,
      cover_path: editForm.value.cover_path || null
    })
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
    case "SUCCESS": return "text-emerald-400"
    case "ERROR": return "text-rose-400"
    case "WARNING": return "text-amber-400"
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
