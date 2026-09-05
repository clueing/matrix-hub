<template>
  <div class="space-y-6">
    <!-- 顶部核心指标看板 -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <!-- 矩阵账号总数 -->
      <Card class="relative overflow-hidden border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div class="absolute -right-3 -top-3 h-20 w-20 rounded-full bg-blue-500/5 blur-xl"></div>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-xs font-semibold uppercase tracking-wider text-slate-500">
            矩阵账号资产
          </CardTitle>
          <div class="rounded-lg bg-blue-500/10 p-2 text-blue-600">
            <Users2 class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-bold tracking-tight text-slate-900 font-mono">
              {{ stats.totalAccounts }}
            </span>
            <span class="text-xs text-slate-500">个已绑账号</span>
          </div>
          <div class="mt-3 flex items-center gap-3 text-xs">
            <div class="flex items-center gap-1.5 text-emerald-600 font-medium">
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              <span>有效: {{ stats.activeAccounts }}</span>
            </div>
            <span class="text-slate-300">|</span>
            <div class="flex items-center gap-1.5 text-rose-500 font-medium">
              <span class="h-1.5 w-1.5 rounded-full bg-rose-500"></span>
              <span>待重登: {{ stats.expiredAccounts }}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <!-- 累计分发任务 -->
      <Card class="relative overflow-hidden border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div class="absolute -right-3 -top-3 h-20 w-20 rounded-full bg-indigo-500/5 blur-xl"></div>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-xs font-semibold uppercase tracking-wider text-slate-500">
            分发调度任务
          </CardTitle>
          <div class="rounded-lg bg-indigo-500/10 p-2 text-indigo-600">
            <Layers class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-bold tracking-tight text-slate-900 font-mono">
              {{ stats.totalTasks }}
            </span>
            <span class="text-xs text-slate-500">个调度批次</span>
          </div>
          <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>成功完成: <strong class="font-semibold text-slate-700 font-mono">{{ stats.completedTasks }}</strong></span>
            <Badge variant="success" class="text-[10px] px-1.5 py-0">
              完成率 {{ stats.totalTasks > 0 ? Math.round((stats.completedTasks / stats.totalTasks) * 100) : 100 }}%
            </Badge>
          </div>
        </CardContent>
      </Card>

      <!-- 子作品发布总量 -->
      <Card class="relative overflow-hidden border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div class="absolute -right-3 -top-3 h-20 w-20 rounded-full bg-amber-500/5 blur-xl"></div>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-xs font-semibold uppercase tracking-wider text-slate-500">
            作品落地总量
          </CardTitle>
          <div class="rounded-lg bg-amber-500/10 p-2 text-amber-600">
            <Send class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="flex items-baseline gap-2">
            <span class="text-3xl font-bold tracking-tight text-slate-900 font-mono">
              {{ stats.totalSubtasks }}
            </span>
            <span class="text-xs text-slate-500">次作品推送</span>
          </div>
          <div class="mt-3 space-y-1.5">
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span>总体成功率</span>
              <span class="font-mono font-semibold text-slate-700">{{ stats.successRate }}%</span>
            </div>
            <Progress :model-value="stats.successRate" class="h-1.5" />
          </div>
        </CardContent>
      </Card>

      <!-- 自动化底座模式 -->
      <Card class="relative overflow-hidden border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
        <div class="absolute -right-3 -top-3 h-20 w-20 rounded-full bg-emerald-500/5 blur-xl"></div>
        <CardHeader class="flex flex-row items-center justify-between pb-2">
          <CardTitle class="text-xs font-semibold uppercase tracking-wider text-slate-500">
            内核运行引擎
          </CardTitle>
          <div class="rounded-lg bg-emerald-500/10 p-2 text-emerald-600">
            <Cpu class="h-4 w-4" />
          </div>
        </CardHeader>
        <CardContent>
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-bold tracking-tight text-slate-900">
              Playwright
            </span>
            <Badge variant="matrix" class="text-[10px]">Stealth</Badge>
          </div>
          <div class="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
            <ShieldCheck class="h-3.5 w-3.5 text-emerald-600" />
            <span>反爬沙箱隔离 & 错峰调度</span>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- 快捷功能矩阵入口 -->
    <Card class="border-slate-200/80 shadow-sm">
      <CardHeader class="pb-3 border-b border-slate-100">
        <CardTitle class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Zap class="h-4 w-4 text-amber-500" />
          <span>常用高频快捷操作</span>
        </CardTitle>
      </CardHeader>
      <CardContent class="pt-4">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <button
            @click="$router.push('/publish')"
            class="flex items-center gap-3.5 rounded-xl border border-blue-100 bg-blue-50/40 p-3.5 text-left transition-all hover:bg-blue-50 hover:border-blue-200 group active:scale-[0.99]"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white shadow-md shadow-blue-500/30 group-hover:scale-105 transition-transform">
              <Send class="h-5 w-5" />
            </div>
            <div>
              <div class="font-bold text-sm text-slate-800">创建矩阵分发</div>
              <div class="text-[11px] text-slate-500 mt-0.5">选择视频一键推送到多账号</div>
            </div>
          </button>

          <button
            @click="$router.push('/accounts')"
            class="flex items-center gap-3.5 rounded-xl border border-emerald-100 bg-emerald-50/40 p-3.5 text-left transition-all hover:bg-emerald-50 hover:border-emerald-200 group active:scale-[0.99]"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-md shadow-emerald-500/30 group-hover:scale-105 transition-transform">
              <Users2 class="h-5 w-5" />
            </div>
            <div>
              <div class="font-bold text-sm text-slate-800">账号管理与授权</div>
              <div class="text-[11px] text-slate-500 mt-0.5">免密扫码登录、凭证导入导出</div>
            </div>
          </button>

          <button
            @click="$router.push('/tasks')"
            class="flex items-center gap-3.5 rounded-xl border border-indigo-100 bg-indigo-50/40 p-3.5 text-left transition-all hover:bg-indigo-50 hover:border-indigo-200 group active:scale-[0.99]"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md shadow-indigo-500/30 group-hover:scale-105 transition-transform">
              <Clock class="h-5 w-5" />
            </div>
            <div>
              <div class="font-bold text-sm text-slate-800">任务调度看板</div>
              <div class="text-[11px] text-slate-500 mt-0.5">实时进度跟踪、错误重试与日志</div>
            </div>
          </button>

          <button
            @click="$router.push('/settings')"
            class="flex items-center gap-3.5 rounded-xl border border-slate-200 bg-slate-50/50 p-3.5 text-left transition-all hover:bg-slate-100/70 hover:border-slate-300 group active:scale-[0.99]"
          >
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-700 text-white shadow-md shadow-slate-600/30 group-hover:scale-105 transition-transform">
              <Sliders class="h-5 w-5" />
            </div>
            <div>
              <div class="font-bold text-sm text-slate-800">防封与错峰设置</div>
              <div class="text-[11px] text-slate-500 mt-0.5">并发数、随机扰动秒数配置</div>
            </div>
          </button>
        </div>
      </CardContent>
    </Card>

    <!-- 最近调度任务列表 -->
    <Card class="border-slate-200/80 shadow-sm">
      <CardHeader class="flex flex-row items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <CardTitle class="text-sm font-bold text-slate-800">近期分发任务</CardTitle>
          <CardDescription>最近创建并执行的矩阵分发批次</CardDescription>
        </div>
        <Button variant="ghost" size="sm" class="text-xs text-blue-600 hover:text-blue-700" @click="$router.push('/tasks')">
          <span>查看全部任务</span>
          <ArrowRight class="ml-1 h-3.5 w-3.5" />
        </Button>
      </CardHeader>
      <CardContent class="p-0">
        <div v-if="recentTasks.length === 0" class="flex flex-col items-center justify-center p-12 text-center text-slate-400">
          <Layers class="h-10 w-10 stroke-[1.5] text-slate-300 mb-2" />
          <p class="text-sm">暂无任务记录，点击上方按钮创建第一个分发任务</p>
        </div>
        <Table v-else>
          <TableHeader>
            <TableRow class="hover:bg-transparent">
              <TableHead class="w-[260px]">任务标题</TableHead>
              <TableHead class="w-[120px]">模式</TableHead>
              <TableHead class="w-[110px] text-center">分发账号</TableHead>
              <TableHead class="min-w-[180px]">整体进度</TableHead>
              <TableHead class="w-[110px] text-center">状态</TableHead>
              <TableHead class="w-[170px] text-right">创建时间</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="task in recentTasks" :key="task.id" class="cursor-pointer hover:bg-slate-50/80" @click="$router.push('/tasks')">
              <TableCell class="font-medium text-slate-900">
                <div class="flex items-center gap-2">
                  <span class="truncate max-w-[240px]">{{ task.name }}</span>
                </div>
              </TableCell>
              <TableCell>
                <Badge v-if="task.task_type === 'one_to_many'" variant="secondary" class="text-[11px]">
                  1对多广播
                </Badge>
                <Badge v-else variant="warning" class="text-[11px]">
                  多对多匹配
                </Badge>
              </TableCell>
              <TableCell class="text-center font-mono text-xs">
                {{ task.total_count }} 个
              </TableCell>
              <TableCell>
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-[11px] text-slate-500 font-mono">
                    <span>{{ task.success_count + task.fail_count }} / {{ task.total_count }}</span>
                    <span>{{ task.total_count ? Math.round(((task.success_count + task.fail_count) / task.total_count) * 100) : 0 }}%</span>
                  </div>
                  <Progress
                    :model-value="task.total_count ? Math.round(((task.success_count + task.fail_count) / task.total_count) * 100) : 0"
                    class="h-1.5"
                  />
                </div>
              </TableCell>
              <TableCell class="text-center">
                <Badge v-if="task.status === 'completed'" variant="success">已完成</Badge>
                <Badge v-else-if="task.status === 'processing'" variant="info">执行中</Badge>
                <Badge v-else-if="task.status === 'partial_failed'" variant="warning">部分失败</Badge>
                <Badge v-else-if="task.status === 'failed'" variant="danger">失败</Badge>
                <Badge v-else variant="secondary">待排期</Badge>
              </TableCell>
              <TableCell class="text-right text-xs text-slate-400 font-mono">
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
import { ref, onMounted } from "vue"
import { getAccounts, getTasks } from "../api"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Progress } from "@/components/ui/progress"
import {
  Users2,
  Layers,
  Send,
  Cpu,
  ShieldCheck,
  Zap,
  Clock,
  Sliders,
  ArrowRight,
} from "lucide-vue-next"

const loading = ref(false)
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

const loadData = async () => {
  loading.value = true
  try {
    const accRes: any = await getAccounts()
    const accounts = accRes.data || []
    stats.value.totalAccounts = accounts.length
    stats.value.activeAccounts = accounts.filter((a: any) => a.status === "active").length
    stats.value.expiredAccounts = accounts.filter((a: any) => a.status !== "active").length

    const taskRes: any = await getTasks()
    const tasks = taskRes.data || []
    stats.value.totalTasks = tasks.length
    stats.value.completedTasks = tasks.filter((t: any) => t.status === "completed").length
    recentTasks.value = tasks.slice(0, 5)

    let totalSub = 0
    let successSub = 0
    tasks.forEach((t: any) => {
      totalSub += t.total_count || 0
      successSub += t.success_count || 0
    })
    stats.value.totalSubtasks = totalSub
    stats.value.successRate = totalSub > 0 ? Math.round((successSub / totalSub) * 100) : 100
  } catch (e) {
    console.error("加载数据失败", e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
