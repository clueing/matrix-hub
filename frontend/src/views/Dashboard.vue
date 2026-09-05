<template>
  <div class="space-y-6">
    <!-- 顶部标题与数据同步操作栏 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-4">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold tracking-tight text-foreground">全矩阵数据资产大盘</h2>
          <Badge variant="outline" class="text-[10px] uppercase font-mono">
            实时监控
          </Badge>
        </div>
        <p class="text-xs text-muted-foreground mt-1">
          汇聚抖音、小红书等自媒体矩阵全平台作品播放量、获赞量与粉丝增长表现
        </p>
      </div>

      <div class="flex items-center gap-3">
        <span v-if="overview.last_sync_at" class="text-xs text-muted-foreground font-mono">
          最近同步: {{ overview.last_sync_at.slice(0, 16).replace('T', ' ') }}
        </span>
        <Button
          size="sm"
          variant="outline"
          :disabled="syncing || overview.is_syncing"
          @click="handleSyncMetrics"
          class="gap-1.5 h-8 text-xs font-medium"
        >
          <RefreshCw :class="['h-3.5 w-3.5', (syncing || overview.is_syncing) ? 'animate-spin' : '']" />
          <span>{{ (syncing || overview.is_syncing) ? '正在同步数据...' : '一键同步最新数据' }}</span>
        </Button>
      </div>
    </div>

    <!-- 顶部核心资产看板 (4 列卡片) -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <!-- 全网粉丝总量 -->
      <Card class="relative overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium text-muted-foreground">全网矩阵粉丝总量</CardTitle>
          <div class="flex h-7 w-7 items-center justify-center rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400">
            <Users2 class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono text-foreground">{{ formatNumber(overview.total_followers) }}</div>
          <p class="text-xs text-muted-foreground mt-1.5 flex items-center justify-between">
            <span>活跃矩阵账号</span>
            <span class="font-medium text-foreground">{{ overview.active_accounts }} / {{ overview.total_accounts }} 个</span>
          </p>
        </CardContent>
      </Card>

      <!-- 全网累计播放量 -->
      <Card class="relative overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium text-muted-foreground">全网作品累计播放量</CardTitle>
          <div class="flex h-7 w-7 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Eye class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono text-foreground">{{ formatNumber(overview.total_views) }}</div>
          <p class="text-xs text-muted-foreground mt-1.5 flex items-center justify-between">
            <span>已落地分发作品</span>
            <span class="font-medium text-foreground">{{ overview.total_published_works }} 篇</span>
          </p>
        </CardContent>
      </Card>

      <!-- 全网累计获赞量 -->
      <Card class="relative overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium text-muted-foreground">全网矩阵累计获赞</CardTitle>
          <div class="flex h-7 w-7 items-center justify-center rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400">
            <Heart class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono text-foreground">{{ formatNumber(overview.total_likes) }}</div>
          <p class="text-xs text-muted-foreground mt-1.5 flex items-center justify-between">
            <span>评论互动总量</span>
            <span class="font-medium text-foreground">{{ formatNumber(overview.total_comments) }} 条</span>
          </p>
        </CardContent>
      </Card>

      <!-- 分发批次与成功率 -->
      <Card class="relative overflow-hidden">
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-xs font-medium text-muted-foreground">分发调度成功率</CardTitle>
          <div class="flex h-7 w-7 items-center justify-center rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Send class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono text-foreground">{{ stats.successRate }}%</div>
          <div class="mt-1.5 flex items-center justify-between text-xs text-muted-foreground">
            <span>完成 {{ stats.completedTasks }} / {{ stats.totalTasks }} 批次</span>
            <Progress :model-value="stats.successRate" class="w-16 h-1.5" />
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- 平台资产表现分布 (抖音 vs 小红书) -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <!-- 抖音矩阵卡片 -->
      <Card class="border-border">
        <CardHeader class="flex flex-row items-center justify-between pb-3 border-b border-border">
          <div class="flex items-center gap-2">
            <Badge variant="default" class="bg-black text-white hover:bg-black font-semibold text-[10px] px-1.5 py-0.5">
              抖音 DOUYIN
            </Badge>
            <span class="text-xs font-medium text-foreground">创作者服务矩阵</span>
          </div>
          <span class="text-xs text-muted-foreground font-mono">
            {{ platformStats.douyin?.accounts || 0 }} 个账号
          </span>
        </CardHeader>
        <CardContent class="pt-4 grid grid-cols-3 gap-2 text-center divide-x divide-border">
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.douyin?.followers || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">总粉丝数</div>
          </div>
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.douyin?.views || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">累计播放量</div>
          </div>
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.douyin?.works || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">矩阵发布作品</div>
          </div>
        </CardContent>
      </Card>

      <!-- 小红书矩阵卡片 -->
      <Card class="border-border">
        <CardHeader class="flex flex-row items-center justify-between pb-3 border-b border-border">
          <div class="flex items-center gap-2">
            <Badge variant="default" class="bg-red-500 text-white hover:bg-red-500 font-semibold text-[10px] px-1.5 py-0.5">
              小红书 RED
            </Badge>
            <span class="text-xs font-medium text-foreground">创作者服务矩阵</span>
          </div>
          <span class="text-xs text-muted-foreground font-mono">
            {{ platformStats.xiaohongshu?.accounts || 0 }} 个账号
          </span>
        </CardHeader>
        <CardContent class="pt-4 grid grid-cols-3 gap-2 text-center divide-x divide-border">
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.xiaohongshu?.followers || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">总粉丝数</div>
          </div>
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.xiaohongshu?.likes || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">累计获赞量</div>
          </div>
          <div>
            <div class="text-lg font-bold font-mono text-foreground">{{ formatNumber(platformStats.xiaohongshu?.works || 0) }}</div>
            <div class="text-[11px] text-muted-foreground mt-0.5">矩阵发布作品</div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- 爆款作品排行榜 Top 10 -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-3 border-b border-border">
        <div>
          <div class="flex items-center gap-2">
            <Sparkles class="h-4 w-4 text-amber-500" />
            <CardTitle class="text-base font-semibold">全矩阵爆款内容排行榜 (Top 10)</CardTitle>
          </div>
          <CardDescription class="text-xs mt-0.5">按全网累计播放量与点赞互动量排序，实时回流内容表现</CardDescription>
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <div v-if="topWorks.length === 0" class="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
          <Layers class="h-8 w-8 mb-2 opacity-40" />
          <p class="text-sm">暂无作品数据，分发后点击【一键同步最新数据】即可自动回流</p>
        </div>

        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead class="text-xs font-semibold w-12 text-center">排名</TableHead>
              <TableHead class="text-xs font-semibold">作品内容</TableHead>
              <TableHead class="text-xs font-semibold w-36">分发平台 / 账号</TableHead>
              <TableHead class="text-xs font-semibold w-28 text-right">播放量</TableHead>
              <TableHead class="text-xs font-semibold w-24 text-right">获赞数</TableHead>
              <TableHead class="text-xs font-semibold w-24 text-right">评论数</TableHead>
              <TableHead class="text-xs font-semibold w-32 text-right">发布时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="(work, index) in topWorks" :key="work.id" class="text-xs hover:bg-muted/40">
              <TableCell class="text-center font-mono font-bold">
                <span
                  v-if="index === 0"
                  class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-amber-500/20 text-amber-600 font-bold text-xs"
                >1</span>
                <span
                  v-else-if="index === 1"
                  class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-300/40 text-slate-700 font-bold text-xs"
                >2</span>
                <span
                  v-else-if="index === 2"
                  class="inline-flex h-5 w-5 items-center justify-center rounded-full bg-amber-700/20 text-amber-700 font-bold text-xs"
                >3</span>
                <span v-else class="text-muted-foreground">{{ index + 1 }}</span>
              </TableCell>

              <TableCell class="font-medium text-foreground">
                <div class="flex items-center gap-2 max-w-md">
                  <span class="truncate" :title="work.title">{{ work.title }}</span>
                  <a
                    v-if="work.platform_work_url"
                    :href="work.platform_work_url"
                    target="_blank"
                    class="text-muted-foreground hover:text-primary transition-colors flex-shrink-0"
                    title="在平台原站打开"
                  >
                    <ExternalLink class="h-3 w-3" />
                  </a>
                </div>
              </TableCell>

              <TableCell>
                <div class="flex items-center gap-1.5">
                  <Badge variant="outline" class="text-[9px] px-1 py-0 uppercase">
                    {{ work.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                  </Badge>
                  <span class="truncate max-w-[90px] text-muted-foreground" :title="work.account_name">
                    {{ work.account_name }}
                  </span>
                </div>
              </TableCell>

              <TableCell class="text-right font-mono font-medium text-sky-600 dark:text-sky-400">
                {{ formatNumber(work.view_count) }}
              </TableCell>

              <TableCell class="text-right font-mono font-medium text-rose-600 dark:text-rose-400">
                {{ formatNumber(work.like_count) }}
              </TableCell>

              <TableCell class="text-right font-mono text-muted-foreground">
                {{ formatNumber(work.comment_count) }}
              </TableCell>

              <TableCell class="text-right text-muted-foreground font-mono text-[11px]">
                {{ work.executed_at ? work.executed_at.slice(0, 16).replace('T', ' ') : '-' }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <!-- 快捷功能入口 -->
    <Card>
      <CardHeader class="pb-3 border-b border-border">
        <CardTitle class="text-sm font-medium">快捷操作</CardTitle>
      </CardHeader>
      <CardContent class="pt-4">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <button
            type="button"
            @click="$router.push('/publish')"
            class="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/50 group"
          >
            <div class="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <Send class="h-4 w-4" />
            </div>
            <div>
              <div class="text-sm font-medium text-foreground">创建矩阵分发</div>
              <div class="text-xs text-muted-foreground">一键批量推送多账号</div>
            </div>
          </button>

          <button
            type="button"
            @click="$router.push('/accounts')"
            class="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/50 group"
          >
            <div class="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <QrCode class="h-4 w-4" />
            </div>
            <div>
              <div class="text-sm font-medium text-foreground">账号资产管理</div>
              <div class="text-xs text-muted-foreground">扫码授权与健康巡检</div>
            </div>
          </button>

          <button
            type="button"
            @click="$router.push('/tasks')"
            class="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/50 group"
          >
            <div class="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <ListChecks class="h-4 w-4" />
            </div>
            <div>
              <div class="text-sm font-medium text-foreground">调度排期看板</div>
              <div class="text-xs text-muted-foreground">任务进度与独立数据胶囊</div>
            </div>
          </button>

          <button
            type="button"
            @click="$router.push('/settings')"
            class="flex items-center gap-3 rounded-lg border border-border p-3 text-left transition-colors hover:bg-muted/50 group"
          >
            <div class="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
              <Sliders class="h-4 w-4" />
            </div>
            <div>
              <div class="text-sm font-medium text-foreground">防风控与调度配置</div>
              <div class="text-xs text-muted-foreground">错峰时间与通道管理</div>
            </div>
          </button>
        </div>
      </CardContent>
    </Card>

    <!-- 近期任务执行总览 -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between pb-3 border-b border-border">
        <div>
          <CardTitle class="text-base font-semibold">近期任务动态</CardTitle>
          <CardDescription class="text-xs mt-0.5">最近提交的矩阵分发任务批次与实时进度</CardDescription>
        </div>
        <router-link to="/tasks">
          <Button variant="ghost" size="sm" class="text-xs gap-1">
            <span>查看完整看板</span>
            <ArrowRight class="h-3.5 w-3.5" />
          </Button>
        </router-link>
      </CardHeader>

      <CardContent class="p-0">
        <div v-if="recentTasks.length === 0" class="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
          <Layers class="h-8 w-8 mb-2 opacity-40" />
          <p class="text-sm">暂无任务记录</p>
          <router-link to="/publish" class="mt-3">
            <Button size="sm" variant="outline">立即创建第一个任务</Button>
          </router-link>
        </div>

        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead class="text-xs font-semibold">任务名称</TableHead>
              <TableHead class="text-xs font-semibold w-28">分发模式</TableHead>
              <TableHead class="text-xs font-semibold w-24 text-center">子作品数</TableHead>
              <TableHead class="text-xs font-semibold w-24 text-center">成功 / 失败</TableHead>
              <TableHead class="text-xs font-semibold w-36">执行进度</TableHead>
              <TableHead class="text-xs font-semibold w-24 text-center">状态</TableHead>
              <TableHead class="text-xs font-semibold w-40 text-right">创建时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="task in recentTasks" :key="task.id" class="text-xs hover:bg-muted/40">
              <TableCell class="font-medium text-foreground truncate max-w-xs" :title="task.name">
                {{ task.name }}
              </TableCell>

              <TableCell>
                <Badge variant="outline" class="text-[10px]">
                  {{ task.task_type === 'one_to_many' ? '1对多广播' : '多对多匹配' }}
                </Badge>
              </TableCell>

              <TableCell class="text-center font-mono">
                {{ task.total_count }}
              </TableCell>

              <TableCell class="text-center">
                <span class="text-emerald-600 font-mono font-medium">{{ task.success_count }}</span>
                <span class="text-muted-foreground mx-1">/</span>
                <span :class="task.fail_count > 0 ? 'text-destructive font-mono font-medium' : 'text-muted-foreground font-mono'">
                  {{ task.fail_count }}
                </span>
              </TableCell>

              <TableCell>
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-[11px]">
                    <span class="text-muted-foreground font-mono">{{ calcTaskProgress(task) }}%</span>
                  </div>
                  <Progress :model-value="calcTaskProgress(task)" class="h-1.5" />
                </div>
              </TableCell>

              <TableCell class="text-center">
                <Badge :variant="getStatusBadgeVariant(task.status)" class="text-[10px]">
                  {{ getStatusText(task.status) }}
                </Badge>
              </TableCell>

              <TableCell class="text-right text-muted-foreground font-mono text-[11px]">
                {{ task.created_at ? task.created_at.slice(0, 19).replace('T', ' ') : '-' }}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue"
import { ElMessage } from "element-plus"
import {
  Users2, Layers, Send, ArrowRight, QrCode, ListChecks, Sliders,
  RefreshCw, Eye, Heart, Sparkles, ExternalLink
} from "lucide-vue-next"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"

import { getAccounts, getTasks, getMetricsOverview, syncMetrics } from "../api"

const syncing = ref(false)

const overview = ref<any>({
  total_accounts: 0,
  active_accounts: 0,
  total_followers: 0,
  total_views: 0,
  total_likes: 0,
  total_comments: 0,
  total_shares: 0,
  total_collects: 0,
  total_published_works: 0,
  last_sync_at: null,
  is_syncing: false
})

const platformStats = ref<Record<string, any>>({})
const topWorks = ref<any[]>([])

const stats = ref({
  totalAccounts: 0,
  activeAccounts: 0,
  expiredAccounts: 0,
  totalTasks: 0,
  completedTasks: 0,
  totalSubtasks: 0,
  successRate: 100,
})

const recentTasks = ref<any[]>([])

const formatNumber = (num?: number) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}

const calcTaskProgress = (task: any) => {
  if (!task.total_count) return 0
  return Math.round(((task.success_count + task.fail_count) / task.total_count) * 100)
}

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "completed": return "success"
    case "processing": return "info"
    case "partial_failed": return "warning"
    case "failed": return "destructive"
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
    default: return "待执行"
  }
}

const handleSyncMetrics = async () => {
  if (syncing.value) return
  syncing.value = true
  try {
    const res: any = await syncMetrics()
    ElMessage.success(res.message || "指标同步任务已触发，请关注执行日志")
    await loadMetrics()
  } catch (e: any) {
    ElMessage.error(e.message || "同步失败")
  } finally {
    syncing.value = false
  }
}

const loadMetrics = async () => {
  try {
    const res: any = await getMetricsOverview()
    if (res.data) {
      overview.value = res.data.overview || overview.value
      platformStats.value = res.data.platform_stats || {}
      topWorks.value = res.data.top_works || []
    }
  } catch (err) {}
}

const loadData = async () => {
  try {
    await loadMetrics()

    const accRes: any = await getAccounts()
    const accounts = accRes.data || []
    stats.value.totalAccounts = accounts.length
    stats.value.activeAccounts = accounts.filter((a: any) => a.status === "active").length
    stats.value.expiredAccounts = accounts.filter((a: any) => a.status === "expired").length

    const taskRes: any = await getTasks()
    const tasks = taskRes.data || []
    stats.value.totalTasks = tasks.length
    stats.value.completedTasks = tasks.filter((t: any) => t.status === "completed").length

    let allSubtasks = 0
    let successSubtasks = 0
    tasks.forEach((t: any) => {
      allSubtasks += t.total_count || 0
      successSubtasks += t.success_count || 0
    })
    stats.value.totalSubtasks = allSubtasks
    stats.value.successRate = allSubtasks > 0 ? Math.round((successSubtasks / allSubtasks) * 100) : 100

    recentTasks.value = tasks.slice(0, 5)
  } catch (err) {}
}

// WebSocket 监听指标更新
let ws: WebSocket | null = null

const initWs = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  ws = new WebSocket(`${protocol}//${host}/ws`)
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.event === 'metrics_updated' || msg.event === 'account_status_changed') {
        loadMetrics()
      }
    } catch (e) {}
  }
}

onMounted(() => {
  loadData()
  initWs()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>
