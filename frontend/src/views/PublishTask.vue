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
        <div class="font-bold flex items-center justify-between">
          <div class="flex items-center gap-2">
            <el-tag effect="dark">步骤 1</el-tag> 视频素材准备
          </div>
          <div v-if="taskType === 'one_to_many' && singleVideoPath" class="text-xs text-green-600 flex items-center gap-1 font-normal">
            <el-icon><CircleCheck /></el-icon> 视频素材已就绪
          </div>
        </div>
      </template>

      <!-- 1对多模式下的视频选择 -->
      <div v-if="taskType === 'one_to_many'">
        <!-- 状态 A：尚未选择视频素材时的 Dropzone 选择区 -->
        <div 
          v-if="!singleVideoPath"
          class="video-picker-dropzone border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-8 bg-slate-50/70 hover:bg-blue-50/20 transition-all text-center max-w-3xl cursor-pointer"
          @dragover.prevent
          @drop.prevent="handleDrop"
        >
          <div class="flex justify-center mb-3">
            <div class="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-600 shadow-sm">
              <el-icon :size="32"><Film /></el-icon>
            </div>
          </div>
          <div class="text-base font-bold text-slate-800 mb-1">选择或拖入本地原始视频</div>
          <div class="text-xs text-slate-500 mb-5">
            支持 MP4, MOV, FLV, MKV 等常见视频格式，系统将直接向矩阵平台原画分发
          </div>
          <div class="flex items-center justify-center gap-3 mb-3">
            <el-button type="primary" size="default" :loading="pickingFile" @click.stop="handlePickFile">
              <el-icon class="mr-1"><FolderOpened /></el-icon> 调起系统窗口选择
            </el-button>
            <el-upload
              action=""
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleBrowserFileSelect"
              accept="video/*,.mp4,.mov,.flv,.mkv,.webm"
            >
              <el-button size="default" @click.stop>
                <el-icon class="mr-1"><Upload /></el-icon> 浏览器选择/上传
              </el-button>
            </el-upload>
          </div>
          
          <div class="text-xs text-slate-400 flex items-center justify-center gap-2">
            <span>支持拖入视频文件到此区域</span>
            <span class="text-slate-300">|</span>
            <el-button link type="primary" size="small" @click.stop="showManualPath = !showManualPath">
              {{ showManualPath ? '收起手动输入' : '手动输入/粘贴路径' }}
            </el-button>
          </div>

          <div v-if="showManualPath" class="mt-4 pt-4 border-t border-slate-200 text-left" @click.stop>
            <el-input 
              v-model="singleVideoPath" 
              placeholder="输入本地视频绝对路径 (例如: D:\videos\my_vlog.mp4)" 
              clearable
              @change="handleVerifySingleVideo"
            >
              <template #append>
                <el-button @click="handleVerifySingleVideo">校验并载入</el-button>
              </template>
            </el-input>
          </div>
        </div>

        <!-- 状态 B：已选择视频素材后的就绪卡片 -->
        <div 
          v-else 
          class="selected-video-card max-w-3xl p-5 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex items-start gap-3.5 min-w-0">
              <!-- 文件格式图徽 -->
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex flex-col items-center justify-center text-white shadow-sm flex-shrink-0">
                <el-icon :size="18"><Film /></el-icon>
                <span class="text-[9px] font-bold mt-0.5 tracking-wider uppercase">
                  {{ getVideoExt(singleVideoPath) }}
                </span>
              </div>
              
              <!-- 视频详细元信息 -->
              <div class="flex flex-col min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-bold text-slate-800 text-base leading-snug truncate max-w-md">
                    {{ singleVideoInfo?.name || getFileName(singleVideoPath) }}
                  </span>
                  <el-tag size="small" type="success" effect="light" class="font-medium">
                    <el-icon class="mr-0.5"><CircleCheck /></el-icon> 校验通过
                  </el-tag>
                  <el-tag v-if="singleVideoInfo?.size_mb" size="small" type="info">
                    {{ singleVideoInfo.size_mb }} MB
                  </el-tag>
                </div>
                
                <!-- 路径预览条 -->
                <div class="mt-2 text-xs text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-100 font-mono truncate max-w-lg select-all" :title="singleVideoPath">
                  {{ singleVideoPath }}
                </div>
              </div>
            </div>

            <!-- 操作按钮组 -->
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <el-button size="small" type="primary" plain :loading="pickingFile" @click="handlePickFile">
                <el-icon class="mr-1"><FolderOpened /></el-icon> 更换
              </el-button>
              <el-upload
                action=""
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleBrowserFileSelect"
                accept="video/*,.mp4,.mov,.flv,.mkv,.webm"
              >
                <el-button size="small" plain>
                  <el-icon class="mr-1"><Upload /></el-icon> 上传更换
                </el-button>
              </el-upload>
              <el-button size="small" type="danger" link @click="clearSelectedVideo">
                清除
              </el-button>
            </div>
          </div>

          <!-- 底部辅助说明与展开路径微调 -->
          <div class="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
            <span>零转码原片分发模式已就绪</span>
            <el-button link type="primary" size="small" @click="showManualPath = !showManualPath">
              {{ showManualPath ? '收起路径编辑' : '修改文件路径' }}
            </el-button>
          </div>
          <div v-if="showManualPath" class="mt-2">
            <el-input 
              v-model="singleVideoPath" 
              size="small"
              placeholder="修改视频文件绝对路径" 
              clearable
              @change="handleVerifySingleVideo"
            >
              <template #append>
                <el-button size="small" @click="handleVerifySingleVideo">重新校验</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </div>

      <!-- 多对多模式下的文件夹扫描批量导入 -->
      <div v-else class="folder-picker-section max-w-3xl">
        <div class="p-5 bg-white border border-slate-200 rounded-xl shadow-sm mb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-11 h-11 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600 flex-shrink-0">
                <el-icon :size="22"><FolderOpened /></el-icon>
              </div>
              <div>
                <div class="font-bold text-slate-800 text-sm">选择素材存放文件夹</div>
                <div class="text-xs text-slate-500 mt-0.5">系统将自动检索目录下的所有有效视频文件</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <el-button type="primary" size="default" :loading="pickingFolder" @click="handlePickFolder">
                <el-icon class="mr-1"><FolderOpened /></el-icon> 调起系统选择文件夹
              </el-button>
              <el-button v-if="folderPath" size="default" :loading="scanning" @click="handleScanFolder">
                重新扫描
              </el-button>
            </div>
          </div>

          <div class="mt-3">
            <el-input 
              v-model="folderPath" 
              placeholder="通过上方按钮选择，或手动粘贴文件夹路径 (如 D:\my_channel_videos)" 
              clearable
              @change="handleScanFolder"
            >
              <template #prefix>
                <el-icon class="text-gray-400"><FolderOpened /></el-icon>
              </template>
            </el-input>
          </div>
        </div>

        <div v-if="scannedVideos.length > 0" class="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <div class="flex items-center justify-between mb-3">
            <div class="text-sm font-bold text-slate-700 flex items-center gap-2">
              <span>检索到的视频素材清单</span>
              <el-tag type="success" size="small">{{ scannedVideos.length }} 个视频</el-tag>
            </div>
            <span class="text-xs text-slate-400">将按账号勾选顺序自动一对一配对</span>
          </div>
          <el-table :data="scannedVideos" max-height="240" size="small" stripe border>
            <el-table-column prop="name" label="文件名" min-width="180" show-overflow-tooltip />
            <el-table-column prop="size_mb" label="大小" width="90" align="center">
              <template #default="{ row }">{{ row.size_mb }} MB</template>
            </el-table-column>
            <el-table-column prop="path" label="完整绝对路径" min-width="260" show-overflow-tooltip />
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
            <el-radio label="immediate">立即发布 (即刻启动流程)</el-radio>
            <el-radio label="platform_native">平台官方原生定时 (关机也能按时公开)</el-radio>
            <el-radio label="local_staggered">本地预约定时 (到点准时唤醒执行)</el-radio>
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

        <el-form-item label="错峰防风控">
          <div class="flex flex-col gap-2">
            <div class="flex items-center gap-4">
              <el-switch 
                v-model="enableStagger" 
                active-text="启用账号阶梯错峰延迟 (适合多账号大批量分发防关联)" 
                inactive-text="关闭错峰 (零等待即刻/准点并发分发)" 
              />
            </div>
            <div v-if="enableStagger" class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <span>账号基础间隔: </span>
              <el-input-number v-model="form.stagger_interval" :min="10" :max="1800" :step="30" size="small" /> 秒
              <span class="ml-3">随机扰动: ±</span>
              <el-input-number v-model="form.stagger_jitter" :min="0" :max="120" :step="5" size="small" /> 秒
              <span class="text-xs text-gray-400 ml-2">多账号依次递增执行，降低同一局域网并发风控风险</span>
            </div>
            <div v-else class="text-xs text-emerald-600 flex items-center gap-1 font-medium">
              <el-icon><CircleCheck /></el-icon>
              已开启极速准点模式：任务创建后子账号立即启动发布，零额外等待。
            </div>
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
import { Check, FolderOpened, Upload, Film, CircleCheck } from "@element-plus/icons-vue"
import { 
  getAccounts, scanFolder, verifyVideo, createTask, 
  pickLocalFile, pickLocalFolder, uploadVideoFile 
} from "../api"

const router = useRouter()

const taskType = ref("one_to_many")
const singleVideoPath = ref("")
const singleVideoInfo = ref<any>(null)
const pickingFile = ref(false)
const showManualPath = ref(false)

const getVideoExt = (path: string) => {
  if (!path) return "MP4"
  const ext = path.split(".").pop()
  return ext ? ext.toUpperCase() : "MP4"
}

const getFileName = (path: string) => {
  if (!path) return ""
  return path.replace(/\\/g, "/").split("/").pop() || path
}

const clearSelectedVideo = () => {
  singleVideoPath.value = ""
  singleVideoInfo.value = null
  buildSubtaskItems()
}

const handleDrop = (e: DragEvent) => {
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleBrowserFileSelect({ raw: e.dataTransfer.files[0] })
  }
}

const folderPath = ref("")
const scanning = ref(false)
const pickingFolder = ref(false)
const scannedVideos = ref<any[]>([])

const availableAccounts = ref<any[]>([])
const selectedAccountIds = ref<string[]>([])
const subtaskItems = ref<any[]>([])

const submitting = ref(false)
const enableStagger = ref(false)

const form = ref({
  name: "",
  master_title: "",
  master_description: "",
  master_tags: [] as string[],
  schedule_mode: "immediate",
  scheduled_at: null as string | null,
  stagger_interval: 60,
  stagger_jitter: 10
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

const handlePickFile = async () => {
  pickingFile.value = true
  try {
    const res: any = await pickLocalFile()
    if (res && res.data && res.data.file_path) {
      singleVideoPath.value = res.data.file_path
      singleVideoInfo.value = {
        name: res.data.file_name,
        size_mb: res.data.size_mb,
        path: res.data.file_path
      }
      if (!form.value.master_title) {
        form.value.master_title = res.data.file_name.replace(/\.[^/.]+$/, "")
      }
      ElMessage.success(`已选择视频文件: ${res.data.file_name}`)
      buildSubtaskItems()
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    pickingFile.value = false
  }
}

const handleBrowserFileSelect = async (uploadFile: any) => {
  if (!uploadFile || !uploadFile.raw) return
  const formData = new FormData()
  formData.append("file", uploadFile.raw)
  const loadingMsg = ElMessage.info({ message: "正在上传并载入视频素材...", duration: 0 })
  try {
    const res: any = await uploadVideoFile(formData)
    loadingMsg.close()
    if (res && res.data && res.data.file_path) {
      singleVideoPath.value = res.data.file_path
      singleVideoInfo.value = {
        name: res.data.file_name,
        size_mb: res.data.size_mb,
        path: res.data.file_path
      }
      if (!form.value.master_title) {
        form.value.master_title = res.data.file_name.replace(/\.[^/.]+$/, "")
      }
      ElMessage.success(`视频上传并校验成功: ${res.data.file_name}`)
      buildSubtaskItems()
    }
  } catch (e: any) {
    loadingMsg.close()
    ElMessage.error(e.message)
  }
}

const handlePickFolder = async () => {
  pickingFolder.value = true
  try {
    const res: any = await pickLocalFolder()
    if (res && res.data && res.data.folder_path) {
      folderPath.value = res.data.folder_path
      scannedVideos.value = res.data.videos || []
      ElMessage.success(`已选择文件夹并扫描到 ${scannedVideos.value.length} 个视频素材`)
      buildSubtaskItems()
    }
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    pickingFolder.value = false
  }
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
      stagger_interval: enableStagger.value ? form.value.stagger_interval : 0,
      stagger_jitter: enableStagger.value ? form.value.stagger_jitter : 0,
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
