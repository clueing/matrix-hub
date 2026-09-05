<template>
  <div class="space-y-6 max-w-5xl mx-auto pb-16">
    <!-- 顶栏：标题与分发模式切换 -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold tracking-tight text-foreground">创建矩阵分发任务</h1>
        <p class="text-xs text-muted-foreground mt-0.5">
          支持原画零损直传、平台原生定时与本地多账号错峰队列防风控
        </p>
      </div>

      <!-- 分发模式切换 -->
      <div class="flex items-center rounded-lg border border-border bg-background p-1 text-xs">
        <button
          type="button"
          :class="[
            'flex items-center gap-1.5 px-3 py-1 font-medium rounded-md transition-colors',
            taskType === 'one_to_many'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          ]"
          @click="taskType = 'one_to_many'; handleTypeChange()"
        >
          <Radio class="w-3.5 h-3.5" />
          <span>1对多广播 (单视频多账号)</span>
        </button>
        <button
          type="button"
          :class="[
            'flex items-center gap-1.5 px-3 py-1 font-medium rounded-md transition-colors',
            taskType === 'many_to_many'
              ? 'bg-secondary text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          ]"
          @click="taskType = 'many_to_many'; handleTypeChange()"
        >
          <Layers class="w-3.5 h-3.5" />
          <span>多对多匹配 (不同视频不同账号)</span>
        </button>
      </div>
    </div>

    <!-- 步骤一：素材选择 -->
    <Card>
      <CardHeader class="pb-3 border-b border-border">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="h-5 w-5 rounded-full p-0 flex items-center justify-center text-[10px]">1</Badge>
            <CardTitle class="text-sm font-semibold">视频素材准备</CardTitle>
            <CardDescription class="text-xs">选择本地原始视频文件或素材文件夹</CardDescription>
          </div>
          <div v-if="taskType === 'one_to_many' && singleVideoPath" class="flex items-center gap-1 text-xs text-emerald-600">
            <CheckCircle2 class="w-3.5 h-3.5" />
            <span>素材已就绪</span>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-6">
        <!-- 1对多模式下的视频选择 -->
        <div v-if="taskType === 'one_to_many'">
          <!-- 状态 A：尚未选择视频素材时的 Dropzone 选择区 -->
          <div
            v-if="!singleVideoPath"
            class="border-2 border-dashed border-border hover:border-primary/50 rounded-xl p-8 bg-muted/10 hover:bg-muted/30 transition-colors text-center max-w-xl mx-auto cursor-pointer"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <div class="flex justify-center mb-3">
              <div class="w-12 h-12 rounded-lg bg-muted flex items-center justify-center text-muted-foreground">
                <Film class="w-6 h-6" />
              </div>
            </div>
            <h3 class="text-sm font-semibold text-foreground mb-1">选择或拖入本地原始视频</h3>
            <p class="text-xs text-muted-foreground mb-4 max-w-md mx-auto">
              支持 MP4, MOV, FLV, MKV 等常见视频格式，原画直接分发
            </p>

            <div class="flex flex-wrap items-center justify-center gap-2.5 mb-3">
              <Button type="button" variant="default" size="sm" :disabled="pickingFile" @click.stop="handlePickFile">
                <FolderOpen class="w-3.5 h-3.5 mr-1" />
                <span>{{ pickingFile ? "调起中..." : "系统文件选择" }}</span>
              </Button>

              <label class="cursor-pointer">
                <Button type="button" variant="outline" size="sm" as="span">
                  <UploadCloud class="w-3.5 h-3.5 mr-1" />
                  <span>浏览器上传</span>
                </Button>
                <input
                  type="file"
                  class="hidden"
                  accept="video/*,.mp4,.mov,.flv,.mkv,.webm"
                  @change="handleBrowserFileChange"
                />
              </label>
            </div>

            <div class="text-xs text-muted-foreground flex items-center justify-center gap-2">
              <span>支持拖拽文件到此区域</span>
              <span>•</span>
              <button
                type="button"
                class="text-primary hover:underline"
                @click.stop="showManualPath = !showManualPath"
              >
                {{ showManualPath ? "收起路径输入" : "手动输入绝对路径" }}
              </button>
            </div>

            <div v-if="showManualPath" class="mt-3 pt-3 border-t border-border text-left" @click.stop>
              <div class="flex gap-2">
                <Input
                  v-model="singleVideoPath"
                  placeholder="输入本地视频绝对路径 (如 D:\videos\video.mp4)"
                  class="h-8 text-xs font-mono"
                  @keyup.enter="handleVerifySingleVideo"
                />
                <Button type="button" variant="secondary" size="sm" class="h-8 text-xs" @click="handleVerifySingleVideo">
                  校验
                </Button>
              </div>
            </div>
          </div>

          <!-- 状态 B：已选择视频素材后的就绪卡片 (纯净 shadcn 风格) -->
          <div
            v-else
            class="max-w-xl mx-auto p-4 bg-card border border-border rounded-lg shadow-sm"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-start gap-3 min-w-0">
                <div class="w-10 h-10 rounded-lg bg-muted border border-border flex flex-col items-center justify-center text-foreground flex-shrink-0">
                  <Film class="w-4 h-4 text-muted-foreground" />
                  <span class="text-[9px] font-mono font-semibold uppercase mt-0.5 text-muted-foreground">
                    {{ getVideoExt(singleVideoPath) }}
                  </span>
                </div>

                <div class="flex flex-col min-w-0 space-y-1">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-medium text-foreground text-xs truncate max-w-xs">
                      {{ singleVideoInfo?.name || getFileName(singleVideoPath) }}
                    </span>
                    <Badge variant="outline" class="text-[10px] px-1 py-0 text-emerald-600">
                      已校验
                    </Badge>
                    <span v-if="singleVideoInfo?.size_mb" class="text-[11px] text-muted-foreground font-mono">
                      {{ singleVideoInfo.size_mb }} MB
                    </span>
                  </div>

                  <div class="text-[11px] text-muted-foreground font-mono truncate max-w-sm select-all" :title="singleVideoPath">
                    {{ singleVideoPath }}
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="flex items-center gap-1 flex-shrink-0">
                <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" :disabled="pickingFile" @click="handlePickFile">
                  更换
                </Button>
                <Button variant="ghost" size="sm" class="h-7 px-2 text-xs text-muted-foreground hover:text-destructive" @click="clearSelectedVideo">
                  <Trash2 class="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- 多对多模式下的文件夹扫描批量导入 -->
        <div v-else class="space-y-4 max-w-2xl mx-auto">
          <div class="p-4 bg-card border border-border rounded-lg shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div class="font-medium text-foreground text-xs">选择素材存放文件夹</div>
                <div class="text-[11px] text-muted-foreground">系统将自动扫描目录下的所有有效视频</div>
              </div>
              <div class="flex items-center gap-2">
                <Button variant="outline" size="sm" class="h-8 text-xs" :disabled="pickingFolder" @click="handlePickFolder">
                  <FolderOpen class="w-3.5 h-3.5 mr-1" /> 选择文件夹
                </Button>
                <Button v-if="folderPath" variant="ghost" size="sm" class="h-8 text-xs" :disabled="scanning" @click="handleScanFolder">
                  <RefreshCw :class="['w-3.5 h-3.5 mr-1', scanning ? 'animate-spin' : '']" /> 重新扫描
                </Button>
              </div>
            </div>

            <div class="mt-2.5">
              <Input
                v-model="folderPath"
                placeholder="文件夹绝对路径 (如 D:\videos)"
                class="h-8 text-xs font-mono"
                @change="handleScanFolder"
              />
            </div>
          </div>

          <div v-if="scannedVideos.length > 0" class="border border-border rounded-lg overflow-hidden">
            <div class="p-2.5 bg-muted/30 border-b border-border flex items-center justify-between">
              <span class="text-xs font-medium text-foreground">
                已检索到 {{ scannedVideos.length }} 个素材
              </span>
              <span class="text-[11px] text-muted-foreground">按勾选顺序依次匹配</span>
            </div>
            <div class="max-h-48 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow class="bg-muted/40">
                    <TableHead class="text-xs font-semibold">文件名</TableHead>
                    <TableHead class="text-xs font-semibold w-24 text-center">大小</TableHead>
                    <TableHead class="text-xs font-semibold">路径</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="video in scannedVideos" :key="video.path" class="text-xs">
                    <TableCell class="font-medium truncate max-w-xs">{{ video.name }}</TableCell>
                    <TableCell class="text-center text-muted-foreground">{{ video.size_mb }} MB</TableCell>
                    <TableCell class="text-muted-foreground font-mono text-[11px] truncate max-w-xs">{{ video.path }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤二：目标账号勾选 -->
    <Card>
      <CardHeader class="pb-3 border-b border-border">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="h-5 w-5 rounded-full p-0 flex items-center justify-center text-[10px]">2</Badge>
            <CardTitle class="text-sm font-semibold">选择发布目标账号</CardTitle>
            <CardDescription class="text-xs">
              已选 <span class="font-semibold text-foreground">{{ selectedAccountIds.length }}</span> / {{ availableAccounts.length }} 个账号
            </CardDescription>
          </div>

          <div v-if="availableAccounts.length > 0" class="flex items-center gap-1.5">
            <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="selectAllAccounts">
              全选
            </Button>
            <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="clearAccountSelection">
              清空
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-6">
        <div v-if="availableAccounts.length === 0" class="py-8 text-center text-muted-foreground">
          <p class="text-xs">暂无有效在线账号，请先在【账号矩阵管理】中扫码授权</p>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
          <div
            v-for="acc in availableAccounts"
            :key="acc.id"
            :class="[
              'flex items-center gap-2.5 p-2.5 rounded-lg border transition-colors cursor-pointer select-none',
              isAccountSelected(acc.id)
                ? 'border-primary bg-primary/5'
                : 'border-border bg-card hover:bg-muted/40'
            ]"
            @click="toggleAccount(acc.id)"
          >
            <!-- Checkbox -->
            <div
              :class="[
                'w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors',
                isAccountSelected(acc.id)
                  ? 'bg-primary border-primary text-primary-foreground'
                  : 'border-muted-foreground/40 bg-background'
              ]"
            >
              <Check v-if="isAccountSelected(acc.id)" class="w-3 h-3 stroke-[3]" />
            </div>

            <!-- 头像与信息 -->
            <Avatar class="w-7 h-7 rounded-md border border-border">
              <AvatarImage :src="acc.avatar_url" referrerpolicy="no-referrer" />
              <AvatarFallback class="text-[10px]">{{ acc.account_name.slice(0, 1) }}</AvatarFallback>
            </Avatar>

            <div class="flex-1 min-w-0">
              <div class="font-medium text-xs text-foreground truncate" :title="acc.account_name">
                {{ acc.account_name }}
              </div>
              <div class="flex items-center gap-1 mt-0.5">
                <Badge variant="outline" class="text-[9px] px-1 py-0">
                  {{ acc.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                </Badge>
                <span class="text-[10px] text-muted-foreground">
                  {{ acc.followers_count ? formatNumber(acc.followers_count) + '粉' : '' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤三：母版文案与发布配置 -->
    <Card>
      <CardHeader class="pb-3 border-b border-border">
        <div class="flex items-center gap-2">
          <Badge variant="outline" class="h-5 w-5 rounded-full p-0 flex items-center justify-center text-[10px]">3</Badge>
          <CardTitle class="text-sm font-semibold">统一母版内容与调度策略</CardTitle>
          <CardDescription class="text-xs">为各子账号设定基准文案与防风控排期</CardDescription>
        </div>
      </CardHeader>

      <CardContent class="p-6 space-y-4">
        <!-- 任务名称 -->
        <div class="space-y-1 max-w-md">
          <label class="text-xs font-medium text-foreground">任务名称 <span class="text-destructive">*</span></label>
          <Input v-model="form.name" placeholder="如：0905日常更新" class="h-9" />
        </div>

        <!-- 统一主标题 -->
        <div class="space-y-1 max-w-xl">
          <div class="flex items-center justify-between">
            <label class="text-xs font-medium text-foreground">统一主标题 <span class="text-destructive">*</span></label>
            <span class="text-[11px] text-muted-foreground">
              {{ form.master_title.length }} / 30 字 (小红书限20字)
            </span>
          </div>
          <Input
            v-model="form.master_title"
            placeholder="通用主标题 (可在步骤4中独立修改)"
            class="h-9"
            @input="syncMasterToItems"
          />
        </div>

        <!-- 统一正文描述 -->
        <div class="space-y-1 max-w-xl">
          <label class="text-xs font-medium text-foreground">统一正文描述</label>
          <Textarea
            v-model="form.master_description"
            rows="3"
            placeholder="通用视频介绍正文..."
            @input="syncMasterToItems"
          />
        </div>

        <!-- 统一话题标签 -->
        <div class="space-y-1.5 max-w-xl">
          <label class="text-xs font-medium text-foreground">统一话题标签</label>
          <div class="flex items-center gap-2">
            <Input
              v-model="tagInput"
              placeholder="输入标签名称按回车添加"
              class="h-8 text-xs"
              @keyup.enter="addTag"
            />
            <Button type="button" variant="secondary" size="sm" class="h-8 text-xs" @click="addTag">
              添加
            </Button>
          </div>

          <div v-if="form.master_tags.length > 0" class="flex flex-wrap gap-1 pt-1">
            <Badge
              v-for="(tag, idx) in form.master_tags"
              :key="idx"
              variant="secondary"
              class="text-xs py-0.5 px-2 flex items-center gap-1"
            >
              <span>#{{ tag }}</span>
              <button
                type="button"
                class="hover:text-destructive"
                @click="removeTag(idx)"
              >
                <X class="w-3 h-3" />
              </button>
            </Badge>
          </div>

          <!-- 推荐常用标签 -->
          <div class="flex items-center gap-1.5 flex-wrap text-xs text-muted-foreground pt-0.5">
            <span class="text-[11px]">快捷:</span>
            <button
              v-for="preset in ['自媒体运营', '日常vlog', '干货分享', '生活记录', '好物推荐']"
              :key="preset"
              type="button"
              class="text-[11px] bg-muted hover:bg-muted/80 px-2 py-0.5 rounded text-muted-foreground hover:text-foreground transition-colors"
              @click="addPresetTag(preset)"
            >
              + #{{ preset }}
            </button>
          </div>
        </div>

        <div class="pt-3 border-t border-border"></div>

        <!-- 发布方式与调度策略 -->
        <div class="space-y-3 max-w-xl">
          <label class="text-xs font-medium text-foreground">发布方式与时间调度</label>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <div
              :class="[
                'p-3 rounded-lg border transition-colors cursor-pointer text-center',
                form.schedule_mode === 'immediate'
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border bg-card hover:bg-muted/30 text-foreground'
              ]"
              @click="form.schedule_mode = 'immediate'"
            >
              <div class="text-xs font-medium">立即发布</div>
              <div class="text-[10px] text-muted-foreground mt-0.5">即刻启动分发</div>
            </div>

            <div
              :class="[
                'p-3 rounded-lg border transition-colors cursor-pointer text-center',
                form.schedule_mode === 'platform_native'
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border bg-card hover:bg-muted/30 text-foreground'
              ]"
              @click="form.schedule_mode = 'platform_native'"
            >
              <div class="text-xs font-medium">平台原生定时</div>
              <div class="text-[10px] text-muted-foreground mt-0.5">云端准时公开</div>
            </div>

            <div
              :class="[
                'p-3 rounded-lg border transition-colors cursor-pointer text-center',
                form.schedule_mode === 'local_staggered'
                  ? 'border-primary bg-primary/5 text-primary'
                  : 'border-border bg-card hover:bg-muted/30 text-foreground'
              ]"
              @click="form.schedule_mode = 'local_staggered'"
            >
              <div class="text-xs font-medium">本地预约定时</div>
              <div class="text-[10px] text-muted-foreground mt-0.5">到点本地执行</div>
            </div>
          </div>

          <div v-if="form.schedule_mode !== 'immediate'" class="space-y-1">
            <label class="text-xs font-medium text-foreground">预约公开时间</label>
            <Input
              type="datetime-local"
              v-model="form.scheduled_at"
              class="h-8 text-xs font-mono"
            />
          </div>

          <!-- 错峰防风控 -->
          <div class="p-3 rounded-lg bg-muted/30 border border-border space-y-2">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-xs font-medium text-foreground">启用账号阶梯错峰延迟</div>
                <div class="text-[11px] text-muted-foreground">多账号分发时按间隔排队，降低风控关联风险</div>
              </div>
              <Switch v-model:checked="enableStagger" />
            </div>

            <div v-if="enableStagger" class="grid grid-cols-2 gap-3 pt-2 border-t border-border">
              <div class="space-y-1">
                <label class="text-[11px] text-muted-foreground">基础间隔 (秒)</label>
                <Input type="number" v-model.number="form.stagger_interval" min="10" max="1800" step="30" class="h-8 text-xs font-mono" />
              </div>
              <div class="space-y-1">
                <label class="text-[11px] text-muted-foreground">随机扰动 (±秒)</label>
                <Input type="number" v-model.number="form.stagger_jitter" min="0" max="120" step="5" class="h-8 text-xs font-mono" />
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤四：各账号差异化微调预览表格 -->
    <Card v-if="subtaskItems.length > 0">
      <CardHeader class="pb-3 border-b border-border">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Badge variant="outline" class="h-5 w-5 rounded-full p-0 flex items-center justify-center text-[10px]">4</Badge>
            <CardTitle class="text-sm font-semibold">矩阵作品差异化微调</CardTitle>
            <span class="text-xs text-muted-foreground">({{ subtaskItems.length }} 个目标)</span>
          </div>
          <span class="text-xs text-muted-foreground">小红书限20字</span>
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <Table>
          <TableHeader>
            <TableRow class="bg-muted/40">
              <TableHead class="text-xs font-semibold w-36">目标账号</TableHead>
              <TableHead class="text-xs font-semibold min-w-[180px]">视频文件</TableHead>
              <TableHead class="text-xs font-semibold min-w-[200px]">独立标题</TableHead>
              <TableHead class="text-xs font-semibold w-40">独立封面 (可选)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="item in subtaskItems" :key="item.account_id" class="text-xs hover:bg-muted/30">
              <TableCell>
                <div class="flex items-center gap-1.5">
                  <Badge variant="outline" class="text-[9px] px-1 py-0">
                    {{ item.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                  </Badge>
                  <span class="font-medium text-foreground truncate max-w-[90px]" :title="item.account_name">
                    {{ item.account_name }}
                  </span>
                </div>
              </TableCell>

              <TableCell>
                <Input
                  v-model="item.video_path"
                  placeholder="文件绝对路径"
                  class="h-7 text-xs font-mono"
                />
              </TableCell>

              <TableCell>
                <div class="relative">
                  <Input
                    v-model="item.title_override"
                    :maxlength="item.platform === 'xiaohongshu' ? 20 : 100"
                    placeholder="独立标题"
                    class="h-7 text-xs pr-10"
                  />
                  <span class="absolute right-2 top-1 text-[10px] text-muted-foreground font-mono">
                    {{ (item.title_override || '').length }}
                  </span>
                </div>
              </TableCell>

              <TableCell>
                <Input
                  v-model="item.cover_path"
                  placeholder="可选封面路径"
                  class="h-7 text-xs"
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <!-- 底部提交栏 -->
    <div class="flex items-center justify-between pt-2">
      <span class="text-xs text-muted-foreground">
        已准备分发 <strong class="text-foreground">{{ subtaskItems.length }}</strong> 个作品
      </span>

      <Button
        type="button"
        variant="default"
        size="default"
        :disabled="submitting || subtaskItems.length === 0"
        @click="handleSubmit"
      >
        <Send class="w-4 h-4 mr-1.5" />
        <span>{{ submitting ? "提交中..." : "确认并提交任务" }}</span>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import {
  Send, Radio, Layers, Film, FolderOpen, UploadCloud, CheckCircle2,
  Trash2, RefreshCw, Check, X
} from "lucide-vue-next"

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"

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
const tagInput = ref("")

const getVideoExt = (path: string) => {
  if (!path) return "MP4"
  const ext = path.split(".").pop()
  return ext ? ext.toUpperCase() : "MP4"
}

const getFileName = (path: string) => {
  if (!path) return ""
  return path.replace(/\\/g, "/").split("/").pop() || path
}

const formatNumber = (num: number) => {
  if (!num) return "0"
  if (num >= 10000) return (num / 10000).toFixed(1) + "w"
  return String(num)
}

const clearSelectedVideo = () => {
  singleVideoPath.value = ""
  singleVideoInfo.value = null
  buildSubtaskItems()
}

const handleDrop = (e: DragEvent) => {
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    handleBrowserFileSelect(e.dataTransfer.files[0])
  }
}

const handleBrowserFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleBrowserFileSelect(target.files[0])
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
  scheduled_at: "" as string,
  stagger_interval: 60,
  stagger_jitter: 10
})

const isAccountSelected = (id: string) => selectedAccountIds.value.includes(id)

const toggleAccount = (id: string) => {
  const idx = selectedAccountIds.value.indexOf(id)
  if (idx > -1) {
    selectedAccountIds.value.splice(idx, 1)
  } else {
    selectedAccountIds.value.push(id)
  }
  buildSubtaskItems()
}

const selectAllAccounts = () => {
  selectedAccountIds.value = availableAccounts.value.map(a => a.id)
  buildSubtaskItems()
}

const clearAccountSelection = () => {
  selectedAccountIds.value = []
  buildSubtaskItems()
}

const addTag = () => {
  const val = tagInput.value.trim().replace(/^#/, "")
  if (val && !form.value.master_tags.includes(val)) {
    form.value.master_tags.push(val)
    tagInput.value = ""
    syncMasterToItems()
  }
}

const addPresetTag = (tag: string) => {
  if (!form.value.master_tags.includes(tag)) {
    form.value.master_tags.push(tag)
    syncMasterToItems()
  }
}

const removeTag = (idx: number) => {
  form.value.master_tags.splice(idx, 1)
  syncMasterToItems()
}

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

const handleBrowserFileSelect = async (file: File) => {
  const formData = new FormData()
  formData.append("file", file)
  const loadingMsg = ElMessage.info({ message: "正在上传视频素材...", duration: 0 })
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
      ElMessage.success(`视频上传成功: ${res.data.file_name}`)
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
      ElMessage.success(`已扫描到 ${scannedVideos.value.length} 个素材`)
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
    ElMessage.warning("请先输入视频绝对路径")
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
    ElMessage.success(`扫描到 ${scannedVideos.value.length} 个视频素材`)
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
  if (!form.value.name.trim()) {
    ElMessage.warning("请填写任务名称")
    return
  }
  if (!form.value.master_title.trim()) {
    ElMessage.warning("请填写统一主标题")
    return
  }
  if (subtaskItems.value.length === 0) {
    ElMessage.warning("请至少选择一个目标账号")
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
      scheduled_at: form.value.scheduled_at || null,
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
    ElMessage.success("矩阵分发任务创建成功！")
    router.push("/tasks")
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadAccounts()
  const now = new Date()
  form.value.name = `矩阵发布_${now.getMonth() + 1}月${now.getDate()}日`
})
</script>
