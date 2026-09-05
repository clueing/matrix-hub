<template>
  <div class="space-y-6">
    <!-- 顶部核心指标看板 (官方 shadcn 规范卡片) -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <!-- 矩阵账号总数 -->
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-foreground">矩阵账号资产</CardTitle>
          <Users2 class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono">{{ stats.totalAccounts }}</div>
          <p class="text-xs text-muted-foreground mt-1">
            有效在线 <span class="text-foreground font-medium">{{ stats.activeAccounts }}</span> 个，待重登 {{ stats.expiredAccounts }} 个
          </p>
        </CardContent>
      </Card>

      <!-- 累计分发任务 -->
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-foreground">分发调度批次</CardTitle>
          <Layers class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono">{{ stats.totalTasks }}</div>
          <p class="text-xs text-muted-foreground mt-1">
            已成功完成 <span class="text-foreground font-medium">{{ stats.completedTasks }}</span> 批次
          </p>
        </CardContent>
      </Card>

      <!-- 作品落地总量 -->
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-foreground">作品发布总数</CardTitle>
          <Send class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="text-2xl font-bold font-mono">{{ stats.totalSubtasks }}</div>
          <div class="mt-1 flex items-center justify-between text-xs text-muted-foreground">
            <span>成功率 {{ stats.successRate }}%</span>
            <Progress :model-value="stats.successRate" class="w-16 h-1.5" />
          </div>
        </CardContent>
      </Card>

      <!-- 自动化底座模式 -->
      <Card>
        <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle class="text-sm font-medium text-foreground">自动化执行引擎</CardTitle>
          <Cpu class="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div class="flex items-center gap-2">
            <span class="text-2xl font-bold font-mono">Playwright</span>
            <Badge variant="outline" class="text-[10px]">Stealth</Badge>
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            无痕沙箱隔离与多账号错峰调度
          </p>
        </CardContent>
      </Card>
    </div>

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
              <div class="text-xs text-muted-foreground">一键推送多账号</div>
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
              <div class="text-sm font-medium text-foreground">扫码接入账号</div>
              <div class="text-xs text-muted-foreground">添加小红书或抖音</div>
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
              <div class="text-xs text-muted-foreground">查看任务进度与日志</div>
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
              <div class="text-sm font-medium text-foreground">防风控与设置</div>
              <div class="text-xs text-muted-foreground">并发数与错峰时间</div>
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
import { ref, onMounted } from "vue"
import {
  Users2, Layers, Send, Cpu, ArrowRight, QrCode, ListChecks, Sliders
} from "lucide-vue-next"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"

import { getAccounts, getTasks } from "../api"

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

const loadData = async () => {
  try {
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

onMounted(() => {
  loadData()
})
</script>
