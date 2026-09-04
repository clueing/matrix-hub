<template>
  <div class="publish-container">
    <el-card shadow="never" class="mb-4">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-xl font-bold">创建矩阵分发任务</h2>
          <div class="text-sm text-gray-500 mt-1">支持原视频直接分发、平台原生定时与本地错峰队列</div>
        </div>
        <el-radio-group v-model="taskType" size="large" @change="handleTypeChange">
          <el-radio-button label="one_to_many">1对多广播模式 (单视频多账号)</el-radio-button>
          <el-radio-button label="many_to_many">多对多匹配模式 (不同视频不同账号)</el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <!-- 步骤一：素材选择 -->
    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="font-bold flex items-center gap-2">
          <el-tag effect="dark">步骤 1</el-tag> 视频素材准备
        </div>
      </template>

      <!-- 1对多模式下的视频选择 -->
      <div v-if="taskType === 'one_to_many'">
        <el-form label-width="120px">
          <el-form-item label="原始视频路径" required>
            <el-input v-model="singleVideoPath" placeholder="例如: D:\videos\my_vlog.mp4" style="max-width: 600px;">
              <template #append>
                <el-button @click="handleVerifySingleVideo">校验文件</el-button>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="singleVideoInfo" label="视频信息">
            <el-tag type="success">
              {{ singleVideoInfo.name }} ({{ singleVideoInfo.size_mb }} MB) - 文件可读正常
            </el-tag>
          </el-form-item>
        </el-form>
      </div>

      <!-- 多对多模式下的文件夹扫描批量导入 -->
      <div v-else>
        <el-form label-width="120px">
          <el-form-item label="本地素材文件夹" required>
            <el-input v-model="folderPath" placeholder="例如: D:\my_channel_videos" style="max-width: 600px;">
              <template #append>
                <el-button type="primary" :loading="scanning" @click="handleScanFolder">扫描文件夹</el-button>
              </template>
            </el-input>
          </el-form-item>
        </el-form>

        <div v-if="scannedVideos.length > 0" class="mt-3">
          <div class="text-sm font-medium mb-2 text-gray-700">检索到 {{ scannedVideos.length }} 个视频素材：</div>
          <el-table :data="scannedVideos" max-height="240" size="small" border>
            <el-table-column prop="name" label="文件名" min-width="200" />
            <el-table-column prop="size_mb" label="大小" width="100" align="center">
              <template #default="{ row }">{{ row.size_mb }} MB</template>
            </el-table-column>
            <el-table-column prop="path" label="完整绝对路径" min-width="300" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
    </el-card>

    <!-- 步骤二：目标账号勾选 -->
    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="font-bold flex items-center gap-2">
          <el-tag effect="dark">步骤 2</el-tag> 选择发布目标账号
        </div>
      </template>

      <div v-if="availableAccounts.length === 0" class="text-gray-400 py-4">
        暂无有效在线账号，请先在【账号矩阵管理】中扫码登录或导入账号
      </div>
      <div v-else>
        <el-checkbox-group v-model="selectedAccountIds" @change="buildSubtaskItems">
          <el-row :gutter="12">
            <el-col :span="6" v-for="acc in availableAccounts" :key="acc.id" class="mb-2">
              <el-checkbox :label="acc.id" border class="w-full">
                <span class="font-medium mr-2">{{ acc.account_name }}</span>
                <el-tag size="small" :type="acc.platform === 'xiaohongshu' ? 'danger' : 'primary'">
                  {{ acc.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                </el-tag>
              </el-checkbox>
            </el-col>
          </el-row>
        </el-checkbox-group>
      </div>
    </el-card>

    <!-- 步骤三：母版文案与发布配置 -->
    <el-card shadow="never" class="mb-4">
      <template #header>
        <div class="font-bold flex items-center gap-2">
          <el-tag effect="dark">步骤 3</el-tag> 统一母版内容与调度策略
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="form.name" placeholder="为本次矩阵发布任务命名，如：0904日常更新" style="max-width: 450px;" />
        </el-form-item>

        <el-form-item label="统一主标题" required>
          <el-input v-model="form.master_title" placeholder="通用主标题 (各账号可在下方独立覆盖修改)" style="max-width: 600px;" @input="syncMasterToItems" />
        </el-form-item>

        <el-form-item label="统一正文描述">
          <el-input v-model="form.master_description" type="textarea" :rows="3" placeholder="通用视频介绍正文..." style="max-width: 600px;" @input="syncMasterToItems" />
        </el-form-item>

        <el-form-item label="统一话题标签">
          <el-select 
            v-model="form.master_tags" 
            multiple 
            filterable 
            allow-create 
            default-first-option 
            placeholder="输入话题标签后回车，如：自媒体运营"
            style="max-width: 600px;"
            @change="syncMasterToItems"
          />
        </el-form-item>

        <el-divider content-position="left">时间控制与防风控错峰调度</el-divider>

        <el-form-item label="发布方式" required>
          <el-radio-group v-model="form.schedule_mode">
            <el-radio label="immediate">立即错峰排队发布</el-radio>
            <el-radio label="platform_native">平台官方原生定时 (关机也能按时公开)</el-radio>
            <el-radio label="local_staggered">本地阶梯定时 (电脑到点唤醒)</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.schedule_mode !== 'immediate'" label="预约公开时间" required>
          <el-date-picker
            v-model="form.scheduled_at"
            type="datetime"
            placeholder="选择预约发布的日期与时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>

        <el-form-item label="账号错峰间隔">
          <div class="flex items-center gap-4">
            <span>基础间隔: </span>
            <el-input-number v-model="form.stagger_interval" :min="30" :max="1800" :step="60" /> 秒
            <span class="ml-4">随机扰动: ±</span>
            <el-input-number v-model="form.stagger_jitter" :min="0" :max="300" :step="10" /> 秒
            <span class="text-xs text-gray-400 ml-2">在同一局域网下依次延迟上传，防止触发平台瞬时并发风控</span>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 步骤四：各账号差异化微调预览表格 -->
    <el-card shadow="never" class="mb-4" v-if="subtaskItems.length > 0">
      <template #header>
        <div class="font-bold flex items-center justify-between">
          <div class="flex items-center gap-2">
            <el-tag effect="dark">步骤 4</el-tag> 矩阵作品差异化微调 ({{ subtaskItems.length }} 个目标)
          </div>
          <span class="text-xs text-gray-400">小红书标题严格限制20字以内；抖音可容纳更长标题</span>
        </div>
      </template>

      <el-table :data="subtaskItems" border size="small">
        <el-table-column label="目标账号" width="160">
          <template #default="{ row }">
            <div class="font-medium">{{ row.account_name }}</div>
            <el-tag size="small" :type="row.platform === 'xiaohongshu' ? 'danger' : 'primary'">
              {{ row.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="视频素材文件" min-width="220">
          <template #default="{ row }">
            <el-input v-model="row.video_path" size="small" placeholder="文件绝对路径" />
          </template>
        </el-table-column>

        <el-table-column label="独立标题 (覆盖母版)" min-width="220">
          <template #default="{ row }">
            <el-input 
              v-model="row.title_override" 
              size="small" 
              :maxlength="row.platform === 'xiaohongshu' ? 20 : 100" 
              show-word-limit
              placeholder="独立个性化标题" 
            />
          </template>
        </el-table-column>

        <el-table-column label="独立封面图 (可选)" min-width="180">
          <template #default="{ row }">
            <el-input v-model="row.cover_path" size="small" placeholder="图片路径 (留空平台截取)" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 底部提交栏 -->
    <div class="flex justify-end pb-8">
      <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
        <el-icon class="mr-1"><Check /></el-icon> 确认并提交分发任务
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { Check } from "@element-plus/icons-vue"
import { getAccounts, scanFolder, verifyVideo, createTask } from "../api"

const router = useRouter()

const taskType = ref("one_to_many")
const singleVideoPath = ref("")
const singleVideoInfo = ref<any>(null)

const folderPath = ref("")
const scanning = ref(false)
const scannedVideos = ref<any[]>([])

const availableAccounts = ref<any[]>([])
const selectedAccountIds = ref<string[]>([])
const subtaskItems = ref<any[]>([])

const submitting = ref(false)

const form = ref({
  name: "",
  master_title: "",
  master_description: "",
  master_tags: [] as string[],
  schedule_mode: "immediate",
  scheduled_at: null as string | null,
  stagger_interval: 300,
  stagger_jitter: 60
})

const loadAccounts = async () => {
  try {
    const res: any = await getAccounts({ status: "active" })
    availableAccounts.value = res.data || []
  } catch (e: any) {
    ElMessage.error(e.message)
  }
}

const handleTypeChange = () => {
  buildSubtaskItems()
}

const handleVerifySingleVideo = async () => {
  if (!singleVideoPath.value) {
    ElMessage.warning("请先输入视频文件绝对路径")
    return
  }
  try {
    const res: any = await verifyVideo(singleVideoPath.value)
    singleVideoInfo.value = res.data
    if (!form.value.master_title) {
      form.value.master_title = res.data.stem
    }
    ElMessage.success("视频文件校验通过！")
    buildSubtaskItems()
  } catch (e: any) {
    singleVideoInfo.value = null
    ElMessage.error(e.message)
  }
}

const handleScanFolder = async () => {
  if (!folderPath.value) {
    ElMessage.warning("请输入本地文件夹路径")
    return
  }
  scanning.value = true
  try {
    const res: any = await scanFolder(folderPath.value)
    scannedVideos.value = res.data || []
    ElMessage.success(`成功扫描到 ${scannedVideos.value.length} 个视频素材`)
    buildSubtaskItems()
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    scanning.value = false
  }
}

const buildSubtaskItems = () => {
  const items: any[] = []
  const accMap = new Map(availableAccounts.value.map((a: any) => [a.id, a]))

  selectedAccountIds.value.forEach((accId, idx) => {
    const acc = accMap.get(accId)
    if (!acc) return

    let videoFile = ""
    let initialTitle = form.value.master_title

    if (taskType.value === "one_to_many") {
      videoFile = singleVideoPath.value
    } else {
      // 多对多模式：若有扫描结果，顺序匹配不同视频
      if (scannedVideos.value.length > idx) {
        videoFile = scannedVideos.value[idx].path
        if (!initialTitle) initialTitle = scannedVideos.value[idx].stem
      }
    }

    items.push({
      account_id: acc.id,
      account_name: acc.account_name,
      platform: acc.platform,
      video_path: videoFile,
      cover_path: "",
      title_override: initialTitle ? (acc.platform === "xiaohongshu" ? initialTitle.slice(0, 20) : initialTitle) : "",
      description_override: "",
      tags_override: null
    })
  })
  subtaskItems.value = items
}

const syncMasterToItems = () => {
  subtaskItems.value.forEach(item => {
    if (!item.title_override || item.title_override === form.value.master_title) {
      item.title_override = item.platform === "xiaohongshu" ? form.value.master_title.slice(0, 20) : form.value.master_title
    }
  })
}

const handleSubmit = async () => {
  if (!form.value.name) {
    ElMessage.warning("请填写任务名称")
    return
  }
  if (!form.value.master_title) {
    ElMessage.warning("请填写统一主标题")
    return
  }
  if (subtaskItems.value.length === 0) {
    ElMessage.warning("请至少选择一个目标发布账号")
    return
  }
  for (const item of subtaskItems.value) {
    if (!item.video_path) {
      ElMessage.error(`账号【${item.account_name}】未绑定视频文件`)
      return
    }
  }

  submitting.value = true
  try {
    const payload = {
      name: form.value.name,
      task_type: taskType.value,
      master_title: form.value.master_title,
      master_description: form.value.master_description,
      master_tags: form.value.master_tags,
      schedule_mode: form.value.schedule_mode,
      scheduled_at: form.value.scheduled_at,
      stagger_interval: form.value.stagger_interval,
      stagger_jitter: form.value.stagger_jitter,
      items: subtaskItems.value.map(it => ({
        account_id: it.account_id,
        video_path: it.video_path,
        cover_path: it.cover_path || null,
        title_override: it.title_override || null
      }))
    }
    await createTask(payload)
    ElMessage.success("矩阵分发任务已成功创建！")
    router.push("/tasks")
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadAccounts()
  // 默认填充任务名称
  const now = new Date()
  form.value.name = `矩阵发布_${now.getMonth() + 1}月${now.getDate()}日`
})
</script>

<style scoped>
.publish-container { padding: 10px 0; }
.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.mt-1 { margin-top: 4px; }
.mt-3 { margin-top: 12px; }
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.ml-2 { margin-left: 8px; }
.ml-4 { margin-left: 16px; }
.pb-8 { padding-bottom: 32px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.w-full { width: 100%; }
.font-bold { font-weight: 600; }
.font-medium { font-weight: 500; }
.text-xl { font-size: 20px; }
.text-sm { font-size: 14px; }
.text-xs { font-size: 12px; }
.text-gray-400 { color: #94a3b8; }
.text-gray-500 { color: #64748b; }
.text-gray-700 { color: #334155; }
</style>
