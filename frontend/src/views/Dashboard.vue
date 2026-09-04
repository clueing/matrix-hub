<template>
  <div class="dashboard-container">
    <!-- 顶部概览指标卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-title">矩阵账号总数</div>
          <div class="metric-value text-primary">{{ stats.totalAccounts }}</div>
          <div class="metric-desc">有效: {{ stats.activeAccounts }} | 需重登: {{ stats.expiredAccounts }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-title">累计分发任务</div>
          <div class="metric-value text-success">{{ stats.totalTasks }}</div>
          <div class="metric-desc">成功完成: {{ stats.completedTasks }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-title">子作品发布量</div>
          <div class="metric-value text-warning">{{ stats.totalSubtasks }}</div>
          <div class="metric-desc">发布成功率: {{ stats.successRate }}%</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-title">系统运行模式</div>
          <div class="metric-value text-info">本地私有</div>
          <div class="metric-desc">浏览器驱动: Playwright Stealth</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作区 -->
    <el-card class="mb-4" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="font-bold">快捷入口</span>
        </div>
      </template>
      <div class="flex gap-4">
        <el-button type="primary" size="large" @click="$router.push('/publish')">
          <el-icon class="mr-1"><Plus /></el-icon> 创建矩阵分发任务
        </el-button>
        <el-button type="success" size="large" @click="$router.push('/accounts')">
          <el-icon class="mr-1"><User /></el-icon> 账号授权与导入
        </el-button>
        <el-button size="large" @click="$router.push('/tasks')">
          <el-icon class="mr-1"><List /></el-icon> 任务调度看板
        </el-button>
        <el-button size="large" @click="$router.push('/settings')">
          <el-icon class="mr-1"><Setting /></el-icon> 错峰与告警设置
        </el-button>
      </div>
    </el-card>

    <!-- 最近发布的任务 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header flex justify-between items-center">
          <span class="font-bold">最近分发任务</span>
          <el-button link type="primary" @click="$router.push('/tasks')">查看全部</el-button>
        </div>
      </template>

      <el-table :data="recentTasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="task_type" label="分发模式" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.task_type === 'one_to_many'" type="info">1对多广播</el-tag>
            <el-tag v-else type="warning">多对多匹配</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_count" label="目标账号数" width="110" align="center" />
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.total_count ? Math.round(((row.success_count + row.fail_count) / row.total_count) * 100) : 0" 
              :status="row.status === 'completed' ? 'success' : row.status === 'failed' ? 'exception' : ''"
            />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success">已完成</el-tag>
            <el-tag v-else-if="row.status === 'processing'" type="primary">执行中</el-tag>
            <el-tag v-else-if="row.status === 'partial_failed'" type="warning">部分失败</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">失败</el-tag>
            <el-tag v-else type="info">待排期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getAccounts, getTasks } from "../api"
import { Plus, User, List, Setting } from "@element-plus/icons-vue"

const loading = ref(false)
const stats = ref({
  totalAccounts: 0,
  activeAccounts: 0,
  expiredAccounts: 0,
  totalTasks: 0,
  completedTasks: 0,
  totalSubtasks: 0,
  successRate: 100
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

<style scoped>
.dashboard-container {
  padding: 10px 0;
}
.metric-card {
  border-radius: 8px;
}
.metric-title {
  color: #64748b;
  font-size: 14px;
}
.metric-value {
  font-size: 28px;
  font-weight: bold;
  margin: 8px 0;
}
.metric-desc {
  font-size: 12px;
  color: #94a3b8;
}
.text-primary { color: #3b82f6; }
.text-success { color: #10b981; }
.text-warning { color: #f59e0b; }
.text-info { color: #6366f1; }
.mb-4 { margin-bottom: 16px; }
.mr-1 { margin-right: 4px; }
.flex { display: flex; }
.gap-4 { gap: 16px; }
.font-bold { font-weight: 600; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
</style>
