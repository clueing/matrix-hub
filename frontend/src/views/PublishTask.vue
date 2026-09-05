<template>
  <div class="space-y-6 max-w-6xl mx-auto pb-16">
    <!-- 顶栏：任务模式与指引 -->
    <Card class="border-border/60 bg-gradient-to-r from-card via-card to-primary/[0.03] shadow-sm">
      <CardContent class="p-6">
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2.5">
              <div class="p-2 rounded-lg bg-primary/10 text-primary">
                <Send class="w-5 h-5" />
              </div>
              <div>
                <h1 class="text-xl font-bold tracking-tight text-foreground">创建矩阵分发任务</h1>
                <p class="text-xs text-muted-foreground">
                  支持原画零损直传、平台原生定时与本地多账号错峰队列防风控
                </p>
              </div>
            </div>
          </div>

          <!-- 分发模式切换 -->
          <div class="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/80 self-start md:self-auto">
            <button
              type="button"
              :class="[
                'flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all',
                taskType === 'one_to_many'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              ]"
              @click="taskType = 'one_to_many'; handleTypeChange()"
            >
              <Radio class="w-3.5 h-3.5" />
              <span>1对多广播模式 (单视频多账号)</span>
            </button>
            <button
              type="button"
              :class="[
                'flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all',
                taskType === 'many_to_many'
                  ? 'bg-background text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              ]"
              @click="taskType = 'many_to_many'; handleTypeChange()"
            >
              <Layers class="w-3.5 h-3.5" />
              <span>多对多匹配模式 (不同视频不同账号)</span>
            </button>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤一：素材选择 -->
    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-4 border-b border-border/40">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Badge variant="matrix" class="h-6 w-6 rounded-full p-0 flex items-center justify-center font-bold">1</Badge>
            <CardTitle class="text-base font-semibold">视频素材准备</CardTitle>
            <CardDescription class="text-xs">选择本地原始视频文件或素材文件夹</CardDescription>
          </div>
          <div v-if="taskType === 'one_to_many' && singleVideoPath" class="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <CheckCircle2 class="w-4 h-4" />
            <span>素材已就绪并校验通过</span>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-6">
        <!-- 1对多模式下的视频选择 -->
        <div v-if="taskType === 'one_to_many'">
          <!-- 状态 A：尚未选择视频素材时的 Dropzone 选择区 -->
          <div
            v-if="!singleVideoPath"
            class="group relative border-2 border-dashed border-border/80 hover:border-primary/60 rounded-2xl p-8 bg-muted/20 hover:bg-primary/[0.02] transition-all text-center max-w-2xl mx-auto cursor-pointer"
            @dragover.prevent
            @drop.prevent="handleDrop"
          >
            <div class="flex justify-center mb-3">
              <div class="w-16 h-16 rounded-2xl bg-primary/10 group-hover:bg-primary/15 group-hover:scale-105 flex items-center justify-center text-primary shadow-sm transition-all">
                <Film class="w-8 h-8" />
              </div>
            </div>
            <h3 class="text-base font-semibold text-foreground mb-1">选择或拖入本地原始视频</h3>
            <p class="text-xs text-muted-foreground mb-5 max-w-md mx-auto leading-relaxed">
              支持 MP4, MOV, FLV, MKV 等常见视频格式，MatrixHub 将向矩阵平台直接原画分发，免二次压缩
            </p>

            <div class="flex flex-wrap items-center justify-center gap-3 mb-4">
              <Button type="button" variant="default" :disabled="pickingFile" @click.stop="handlePickFile">
                <FolderOpen class="w-4 h-4 mr-1.5" />
                <span>{{ pickingFile ? "调起系统选择器中..." : "调起系统窗口选择" }}</span>
              </Button>

              <label class="cursor-pointer">
                <Button type="button" variant="outline" as="span">
                  <UploadCloud class="w-4 h-4 mr-1.5" />
                  <span>浏览器上传/选择</span>
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
              <span>支持直接拖拽文件到此窗口</span>
              <span class="text-border">•</span>
              <button
                type="button"
                class="text-primary hover:underline font-medium"
                @click.stop="showManualPath = !showManualPath"
              >
                {{ showManualPath ? "收起手动输入" : "手动输入/粘贴绝对路径" }}
              </button>
            </div>

            <div v-if="showManualPath" class="mt-4 pt-4 border-t border-border/60 text-left" @click.stop>
              <div class="flex gap-2">
                <Input
                  v-model="singleVideoPath"
                  placeholder="输入本地视频绝对路径 (例如: D:\videos\my_vlog.mp4)"
                  @keyup.enter="handleVerifySingleVideo"
                />
                <Button type="button" variant="secondary" @click="handleVerifySingleVideo">
                  校验并载入
                </Button>
              </div>
            </div>
          </div>

          <!-- 状态 B：已选择视频素材后的就绪卡片 -->
          <div
            v-else
            class="max-w-2xl mx-auto p-5 bg-card border border-border rounded-xl shadow-sm hover:shadow transition"
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex items-start gap-3.5 min-w-0">
                <!-- 文件格式图徽 -->
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex flex-col items-center justify-center text-white shadow-sm flex-shrink-0">
                  <Film class="w-5 h-5" />
                  <span class="text-[9px] font-bold mt-0.5 tracking-wider uppercase">
                    {{ getVideoExt(singleVideoPath) }}
                  </span>
                </div>

                <!-- 视频详细元信息 -->
                <div class="flex flex-col min-w-0 space-y-1.5">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-bold text-foreground text-sm leading-snug truncate max-w-md">
                      {{ singleVideoInfo?.name || getFileName(singleVideoPath) }}
                    </span>
                    <Badge variant="success" class="text-[10px] px-1.5 py-0 h-5">
                      <CheckCircle2 class="w-3 h-3 mr-1" /> 已验证
                    </Badge>
                    <Badge v-if="singleVideoInfo?.size_mb" variant="secondary" class="text-[10px] px-1.5 py-0 h-5">
                      {{ singleVideoInfo.size_mb }} MB
                    </Badge>
                  </div>

                  <!-- 路径预览条 -->
                  <div
                    class="text-xs text-muted-foreground bg-muted/50 px-2.5 py-1 rounded-md border border-border/50 font-mono truncate max-w-lg select-all"
                    :title="singleVideoPath"
                  >
                    {{ singleVideoPath }}
                  </div>
                </div>
              </div>

              <!-- 操作按钮组 -->
              <div class="flex items-center gap-1.5 flex-shrink-0">
                <Button variant="outline" size="sm" :disabled="pickingFile" @click="handlePickFile">
                  <FolderOpen class="w-3.5 h-3.5 mr-1" /> 更换
                </Button>
                <label class="cursor-pointer">
                  <Button variant="ghost" size="sm" as="span">
                    <UploadCloud class="w-3.5 h-3.5 mr-1" /> 上传
                  </Button>
                  <input
                    type="file"
                    class="hidden"
                    accept="video/*,.mp4,.mov,.flv,.mkv,.webm"
                    @change="handleBrowserFileChange"
                  />
                </label>
                <Button variant="destructive" size="sm" class="h-8 px-2" @click="clearSelectedVideo">
                  <Trash2 class="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>

            <!-- 底部辅助说明 -->
            <div class="mt-3 pt-2.5 border-t border-border/60 flex items-center justify-between text-xs text-muted-foreground">
              <span class="flex items-center gap-1">
                <Sparkles class="w-3.5 h-3.5 text-primary" />
                零转码原片直发通道已激活
              </span>
              <button
                type="button"
                class="text-primary hover:underline text-xs"
                @click="showManualPath = !showManualPath"
              >
                {{ showManualPath ? "收起编辑" : "修改路径" }}
              </button>
            </div>
            <div v-if="showManualPath" class="mt-2.5 flex gap-2">
              <Input v-model="singleVideoPath" placeholder="修改视频文件绝对路径" class="h-8 text-xs" />
              <Button size="sm" variant="secondary" class="h-8 text-xs" @click="handleVerifySingleVideo">
                重新校验
              </Button>
            </div>
          </div>
        </div>

        <!-- 多对多模式下的文件夹扫描批量导入 -->
        <div v-else class="space-y-4 max-w-3xl mx-auto">
          <div class="p-5 bg-card border border-border rounded-xl shadow-sm">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                <div class="w-11 h-11 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-600 flex-shrink-0">
                  <FolderOpen class="w-6 h-6" />
                </div>
                <div>
                  <div class="font-bold text-foreground text-sm">选择素材存放文件夹</div>
                  <div class="text-xs text-muted-foreground mt-0.5">系统将自动检索目录下的所有有效视频文件</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Button variant="default" size="sm" :disabled="pickingFolder" @click="handlePickFolder">
                  <FolderOpen class="w-3.5 h-3.5 mr-1" /> 调起系统选择
                </Button>
                <Button v-if="folderPath" variant="outline" size="sm" :disabled="scanning" @click="handleScanFolder">
                  <RefreshCw :class="['w-3.5 h-3.5 mr-1', scanning ? 'animate-spin' : '']" /> 重新扫描
                </Button>
              </div>
            </div>

            <div class="mt-3">
              <Input
                v-model="folderPath"
                placeholder="通过上方按钮选择，或手动粘贴文件夹路径 (如 D:\videos\september)"
                @change="handleScanFolder"
              />
            </div>
          </div>

          <div v-if="scannedVideos.length > 0" class="bg-card border border-border rounded-xl p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <div class="text-sm font-bold text-foreground flex items-center gap-2">
                <span>检索到的视频素材清单</span>
                <Badge variant="success" class="text-xs">{{ scannedVideos.length }} 个视频</Badge>
              </div>
              <span class="text-xs text-muted-foreground">将按账号勾选顺序自动一对一配对</span>
            </div>
            <div class="max-h-60 overflow-y-auto border border-border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="text-xs font-semibold">文件名</TableHead>
                    <TableHead class="text-xs font-semibold w-24 text-center">大小</TableHead>
                    <TableHead class="text-xs font-semibold">绝对路径</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="video in scannedVideos" :key="video.path" class="text-xs">
                    <TableCell class="font-medium truncate max-w-xs">{{ video.name }}</TableCell>
                    <TableCell class="text-center text-muted-foreground">{{ video.size_mb }} MB</TableCell>
                    <TableCell class="text-muted-foreground font-mono text-[11px] truncate max-w-sm">{{ video.path }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤二：目标账号勾选 -->
    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-4 border-b border-border/40">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <Badge variant="matrix" class="h-6 w-6 rounded-full p-0 flex items-center justify-center font-bold">2</Badge>
            <CardTitle class="text-base font-semibold">选择发布目标账号</CardTitle>
            <CardDescription class="text-xs">
              已勾选 <span class="font-bold text-primary">{{ selectedAccountIds.length }}</span> / {{ availableAccounts.length }} 个账号
            </CardDescription>
          </div>

          <!-- 快速选择操作 -->
          <div v-if="availableAccounts.length > 0" class="flex items-center gap-2">
            <Button variant="ghost" size="sm" class="h-7 text-xs" @click="selectAllAccounts">
              全选
            </Button>
            <Button variant="ghost" size="sm" class="h-7 text-xs" @click="clearAccountSelection">
              清空
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent class="p-6">
        <div v-if="availableAccounts.length === 0" class="py-8 text-center text-muted-foreground">
          <AlertCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p class="text-sm">暂无有效在线账号</p>
          <p class="text-xs mt-1 text-muted-foreground/70">请先在【账号矩阵管理】中扫码登录或导入账号 Cookie</p>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div
            v-for="acc in availableAccounts"
            :key="acc.id"
            :class="[
              'group relative flex items-center gap-3 p-3.5 rounded-xl border transition-all cursor-pointer select-none',
              isAccountSelected(acc.id)
                ? 'border-primary bg-primary/[0.04] shadow-sm ring-1 ring-primary/30'
                : 'border-border/80 bg-card hover:border-border hover:bg-muted/30'
            ]"
            @click="toggleAccount(acc.id)"
          >
            <!-- Checkbox 视觉呈现 -->
            <div
              :class="[
                'w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors',
                isAccountSelected(acc.id)
                  ? 'bg-primary border-primary text-primary-foreground'
                  : 'border-muted-foreground/40 bg-background group-hover:border-primary'
              ]"
            >
              <Check v-if="isAccountSelected(acc.id)" class="w-3 h-3 stroke-[3]" />
            </div>

            <!-- 头像 -->
            <Avatar class="w-8 h-8 rounded-full border border-border/50">
              <AvatarImage :src="acc.avatar_url" :alt="acc.account_name" />
              <AvatarFallback class="text-xs font-bold">{{ acc.account_name.slice(0, 1) }}</AvatarFallback>
            </Avatar>

            <!-- 账号名称与平台徽章 -->
            <div class="flex-1 min-w-0">
              <div class="font-medium text-xs text-foreground truncate" :title="acc.account_name">
                {{ acc.account_name }}
              </div>
              <div class="flex items-center gap-1.5 mt-0.5">
                <Badge
                  :variant="acc.platform === 'xiaohongshu' ? 'xiaohongshu' : 'douyin'"
                  class="text-[9px] px-1 py-0 h-4 uppercase font-semibold"
                >
                  {{ acc.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                </Badge>
                <span class="text-[10px] text-muted-foreground truncate">
                  {{ acc.fans_count ? formatNumber(acc.fans_count) + ' 粉' : '正常' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤三：母版文案与发布配置 -->
    <Card class="border-border/60 shadow-sm">
      <CardHeader class="pb-4 border-b border-border/40">
        <div class="flex items-center gap-2">
          <Badge variant="matrix" class="h-6 w-6 rounded-full p-0 flex items-center justify-center font-bold">3</Badge>
          <CardTitle class="text-base font-semibold">统一母版内容与调度策略</CardTitle>
          <CardDescription class="text-xs">为各子账号设定基准文案与防风控错峰排期</CardDescription>
        </div>
      </CardHeader>

      <CardContent class="p-6 space-y-5">
        <!-- 任务名称 -->
        <div class="space-y-1.5 max-w-xl">
          <label class="text-xs font-semibold text-foreground flex items-center gap-1">
            任务名称 <span class="text-destructive">*</span>
          </label>
          <Input v-model="form.name" placeholder="为本次矩阵发布任务命名，如：0905日常更新" />
        </div>

        <!-- 统一主标题 -->
        <div class="space-y-1.5 max-w-2xl">
          <div class="flex items-center justify-between">
            <label class="text-xs font-semibold text-foreground flex items-center gap-1">
              统一主标题 <span class="text-destructive">*</span>
            </label>
            <span class="text-[11px] text-muted-foreground">
              {{ form.master_title.length }} / 30 字 (小红书限20字)
            </span>
          </div>
          <Input
            v-model="form.master_title"
            placeholder="通用主标题 (各账号可在下方步骤4中独立个性化微调)"
            @input="syncMasterToItems"
          />
        </div>

        <!-- 统一正文描述 -->
        <div class="space-y-1.5 max-w-2xl">
          <label class="text-xs font-semibold text-foreground">统一正文描述</label>
          <Textarea
            v-model="form.master_description"
            rows="3"
            placeholder="通用视频介绍正文，介绍视频核心亮点与互动引导..."
            @input="syncMasterToItems"
          />
        </div>

        <!-- 统一话题标签 -->
        <div class="space-y-2 max-w-2xl">
          <label class="text-xs font-semibold text-foreground">统一话题标签</label>
          <div class="flex items-center gap-2">
            <Input
              v-model="tagInput"
              placeholder="输入标签名称后按回车或点添加，如: 自媒体运营"
              class="h-9 text-xs"
              @keyup.enter="addTag"
            />
            <Button type="button" variant="secondary" size="sm" class="h-9 text-xs" @click="addTag">
              添加标签
            </Button>
          </div>

          <!-- 已添加标签徽章列表 -->
          <div v-if="form.master_tags.length > 0" class="flex flex-wrap gap-1.5 pt-1">
            <Badge
              v-for="(tag, idx) in form.master_tags"
              :key="idx"
              variant="secondary"
              class="text-xs py-1 px-2.5 flex items-center gap-1 group bg-secondary/80 hover:bg-secondary"
            >
              <Hash class="w-3 h-3 text-muted-foreground" />
              <span>{{ tag }}</span>
              <button
                type="button"
                class="ml-1 opacity-60 group-hover:opacity-100 hover:text-destructive transition"
                @click="removeTag(idx)"
              >
                <X class="w-3 h-3" />
              </button>
            </Badge>
          </div>

          <!-- 热门常用推荐标签 -->
          <div class="flex items-center gap-1.5 flex-wrap text-xs text-muted-foreground pt-1">
            <span class="text-[11px]">快捷添加:</span>
            <button
              v-for="preset in ['自媒体运营', '创业日常', '日常vlog', '干货分享', '生活记录', '好物推荐']"
              :key="preset"
              type="button"
              class="text-[11px] bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground px-2 py-0.5 rounded-full border border-border/50 transition"
              @click="addPresetTag(preset)"
            >
              + #{{ preset }}
            </button>
          </div>
        </div>

        <div class="pt-4 border-t border-border/50"></div>

        <!-- 发布方式与调度策略 -->
        <div class="space-y-4">
          <div class="space-y-1">
            <h3 class="text-sm font-semibold text-foreground">时间控制与防风控错峰调度</h3>
            <p class="text-xs text-muted-foreground">控制任务发布节奏，模拟自然分发规律</p>
          </div>

          <!-- 调度模式选择 -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl">
            <div
              :class="[
                'p-3.5 rounded-xl border transition-all cursor-pointer select-none',
                form.schedule_mode === 'immediate'
                  ? 'border-primary bg-primary/[0.04] ring-1 ring-primary/30'
                  : 'border-border/80 bg-card hover:bg-muted/30'
              ]"
              @click="form.schedule_mode = 'immediate'"
            >
              <div class="flex items-center gap-2">
                <Zap :class="['w-4 h-4', form.schedule_mode === 'immediate' ? 'text-primary' : 'text-muted-foreground']" />
                <span class="text-xs font-bold text-foreground">立即发布</span>
              </div>
              <p class="text-[11px] text-muted-foreground mt-1">即刻启动分发流程</p>
            </div>

            <div
              :class="[
                'p-3.5 rounded-xl border transition-all cursor-pointer select-none',
                form.schedule_mode === 'platform_native'
                  ? 'border-primary bg-primary/[0.04] ring-1 ring-primary/30'
                  : 'border-border/80 bg-card hover:bg-muted/30'
              ]"
              @click="form.schedule_mode = 'platform_native'"
            >
              <div class="flex items-center gap-2">
                <CloudRain :class="['w-4 h-4', form.schedule_mode === 'platform_native' ? 'text-primary' : 'text-muted-foreground']" />
                <span class="text-xs font-bold text-foreground">平台官方原生定时</span>
              </div>
              <p class="text-[11px] text-muted-foreground mt-1">关机也能按时全网公开</p>
            </div>

            <div
              :class="[
                'p-3.5 rounded-xl border transition-all cursor-pointer select-none',
                form.schedule_mode === 'local_staggered'
                  ? 'border-primary bg-primary/[0.04] ring-1 ring-primary/30'
                  : 'border-border/80 bg-card hover:bg-muted/30'
              ]"
              @click="form.schedule_mode = 'local_staggered'"
            >
              <div class="flex items-center gap-2">
                <Clock :class="['w-4 h-4', form.schedule_mode === 'local_staggered' ? 'text-primary' : 'text-muted-foreground']" />
                <span class="text-xs font-bold text-foreground">本地预约定时</span>
              </div>
              <p class="text-[11px] text-muted-foreground mt-1">到点准时由本地唤醒执行</p>
            </div>
          </div>

          <!-- 预约公开时间选择器 -->
          <div v-if="form.schedule_mode !== 'immediate'" class="space-y-1.5 max-w-sm">
            <label class="text-xs font-semibold text-foreground flex items-center gap-1">
              预约公开时间 <span class="text-destructive">*</span>
            </label>
            <Input
              type="datetime-local"
              v-model="form.scheduled_at"
              class="h-9 text-xs"
            />
            <p class="text-[11px] text-muted-foreground">支持预约未来 14 天内的公开时间</p>
          </div>

          <!-- 错峰防风控开关与参数 -->
          <div class="p-4 rounded-xl bg-muted/40 border border-border/70 max-w-2xl space-y-3">
            <div class="flex items-center justify-between">
              <div class="space-y-0.5">
                <div class="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <ShieldCheck class="w-4 h-4 text-emerald-600" />
                  <span>启用账号阶梯错峰延迟</span>
                </div>
                <div class="text-[11px] text-muted-foreground">
                  适合多账号大批量分发防关联，避免同一时刻同局域网高并发操作触发风控
                </div>
              </div>
              <Switch v-model:checked="enableStagger" />
            </div>

            <div v-if="enableStagger" class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-border/60">
              <div class="space-y-1">
                <label class="text-[11px] font-medium text-foreground">账号基础间隔 (秒)</label>
                <div class="flex items-center gap-2">
                  <Input type="number" v-model.number="form.stagger_interval" min="10" max="1800" step="30" class="h-8 text-xs" />
                  <span class="text-xs text-muted-foreground">秒</span>
                </div>
              </div>
              <div class="space-y-1">
                <label class="text-[11px] font-medium text-foreground">随机扰动浮动 (±秒)</label>
                <div class="flex items-center gap-2">
                  <Input type="number" v-model.number="form.stagger_jitter" min="0" max="120" step="5" class="h-8 text-xs" />
                  <span class="text-xs text-muted-foreground">秒</span>
                </div>
              </div>
            </div>
            <div v-else class="text-xs text-emerald-600 flex items-center gap-1.5 font-medium pt-1">
              <CheckCircle2 class="w-3.5 h-3.5" />
              <span>已开启极速准点模式：任务创建后子账号立即启动发布，零额外等待。</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- 步骤四：各账号差异化微调预览表格 -->
    <Card v-if="subtaskItems.length > 0" class="border-border/60 shadow-sm">
      <CardHeader class="pb-4 border-b border-border/40">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Badge variant="matrix" class="h-6 w-6 rounded-full p-0 flex items-center justify-center font-bold">4</Badge>
            <CardTitle class="text-base font-semibold">矩阵作品差异化微调</CardTitle>
            <Badge variant="secondary" class="text-xs">{{ subtaskItems.length }} 个分发目标</Badge>
          </div>
          <span class="text-xs text-muted-foreground">
            小红书标题严格限20字内；抖音可容纳更多文字
          </span>
        </div>
      </CardHeader>

      <CardContent class="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="text-xs font-semibold w-48">目标账号</TableHead>
              <TableHead class="text-xs font-semibold min-w-[200px]">视频素材文件</TableHead>
              <TableHead class="text-xs font-semibold min-w-[220px]">独立标题 (覆盖母版)</TableHead>
              <TableHead class="text-xs font-semibold w-48">独立封面图 (可选)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="item in subtaskItems" :key="item.account_id" class="hover:bg-muted/30">
              <!-- 目标账号 -->
              <TableCell>
                <div class="flex items-center gap-2">
                  <Badge
                    :variant="item.platform === 'xiaohongshu' ? 'xiaohongshu' : 'douyin'"
                    class="text-[9px] px-1 py-0 h-4 uppercase font-semibold"
                  >
                    {{ item.platform === 'xiaohongshu' ? '小红书' : '抖音' }}
                  </Badge>
                  <span class="font-semibold text-xs text-foreground truncate max-w-[120px]" :title="item.account_name">
                    {{ item.account_name }}
                  </span>
                </div>
              </TableCell>

              <!-- 视频素材文件 -->
              <TableCell>
                <Input
                  v-model="item.video_path"
                  placeholder="视频文件绝对路径"
                  class="h-8 text-xs font-mono"
                />
              </TableCell>

              <!-- 独立标题 -->
              <TableCell>
                <div class="relative">
                  <Input
                    v-model="item.title_override"
                    :maxlength="item.platform === 'xiaohongshu' ? 20 : 100"
                    placeholder="独立个性化标题"
                    class="h-8 text-xs pr-12"
                  />
                  <span class="absolute right-2 top-1.5 text-[10px] text-muted-foreground font-mono">
                    {{ (item.title_override || '').length }}/{{ item.platform === 'xiaohongshu' ? 20 : 100 }}
                  </span>
                </div>
              </TableCell>

              <!-- 独立封面图 -->
              <TableCell>
                <Input
                  v-model="item.cover_path"
                  placeholder="可选封面路径 (留空平台截取)"
                  class="h-8 text-xs"
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <!-- 底部固定/悬浮提交栏 -->
    <div class="sticky bottom-4 z-20">
      <Card class="border-border/80 bg-background/95 backdrop-blur-md shadow-lg">
        <CardContent class="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-3 text-xs text-muted-foreground">
            <span class="flex items-center gap-1.5">
              <CheckCircle2 class="w-4 h-4 text-emerald-600" />
              <span>已就绪: <strong class="text-foreground">{{ subtaskItems.length }}</strong> 个作品分发</span>
            </span>
            <span class="text-border">•</span>
            <span>
              模式: <strong class="text-foreground">{{ taskType === 'one_to_many' ? '1对多广播' : '多对多匹配' }}</strong>
            </span>
          </div>

          <div class="flex items-center gap-2">
            <Button
              type="button"
              variant="default"
              size="lg"
              :disabled="submitting || subtaskItems.length === 0"
              class="w-full sm:w-auto shadow-md"
              @click="handleSubmit"
            >
              <Send class="w-4 h-4 mr-2" />
              <span>{{ submitting ? "任务提交中..." : "确认并提交矩阵分发任务" }}</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import {
  Send, Radio, Layers, Film, FolderOpen, UploadCloud, CheckCircle2,
  Trash2, Sparkles, RefreshCw, AlertCircle, Check, Hash, X,
  Zap, CloudRain, Clock, ShieldCheck
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
  const now = new Date()
  form.value.name = `矩阵发布_${now.getMonth() + 1}月${now.getDate()}日`
})
</script>
