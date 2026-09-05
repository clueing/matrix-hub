<template>
  <div class="flex h-screen w-screen overflow-hidden bg-background font-sans text-foreground antialiased">
    <!-- 侧边栏导航 -->
    <aside class="flex w-60 flex-col border-r border-zinc-800/80 bg-zinc-950 text-zinc-300">
      <!-- 品牌区 (严格 60px 等高对齐) -->
      <div class="flex h-[60px] items-center gap-3 border-b border-zinc-800/80 px-4 bg-zinc-950">
        <img src="./assets/logo.png" alt="MatrixHub" class="h-8 w-auto max-w-[36px] object-contain rounded" />
        <div class="flex min-w-0 flex-1 flex-col justify-center">
          <span class="text-sm font-semibold tracking-tight text-zinc-100">MatrixHub</span>
          <span class="truncate text-[11px] text-zinc-400">多账号矩阵分发平台</span>
        </div>
      </div>

      <!-- 导航项列表 -->
      <nav class="flex-1 space-y-1 p-3 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors select-none"
          :class="[
            $route.path === item.path
              ? 'bg-zinc-800 text-zinc-100'
              : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100'
          ]"
        >
          <component
            :is="item.icon"
            class="h-4 w-4"
            :class="[ $route.path === item.path ? 'text-zinc-100' : 'text-zinc-400' ]"
          />
          <span class="truncate">{{ item.name }}</span>
          <span
            v-if="item.badge"
            class="ml-auto rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] font-semibold text-zinc-400"
          >
            {{ item.badge }}
          </span>
        </router-link>
      </nav>

      <!-- 底部系统状态 -->
      <div class="border-t border-zinc-800/80 p-3.5 bg-zinc-950">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="h-2 w-2 rounded-full bg-emerald-500"></span>
            <span class="text-xs text-zinc-400">自动化引擎就绪</span>
          </div>
          <span class="text-[10px] font-mono text-zinc-500">v0.1</span>
        </div>
      </div>
    </aside>

    <!-- 主工作区 -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- 顶部 Header (严格 60px 等高) -->
      <header class="flex h-[60px] items-center justify-between border-b border-border bg-background px-6">
        <div class="flex items-center gap-2">
          <h1 class="text-sm font-semibold text-foreground tracking-tight">
            {{ $route.meta.title || "控制台" }}
          </h1>
          <span class="text-xs text-muted-foreground">/</span>
          <span class="text-xs text-muted-foreground">自媒体矩阵分发平台</span>
        </div>

        <div class="flex items-center gap-3">
          <router-link to="/publish">
            <Button size="sm" class="gap-1.5 h-8">
              <Send class="h-3.5 w-3.5" />
              <span>创建分发任务</span>
            </Button>
          </router-link>
        </div>
      </header>

      <!-- 页面主要内容区 -->
      <main class="flex-1 overflow-y-auto bg-muted/20 p-6">
        <router-view />
      </main>
    </div>

    <!-- 全局受控浏览器视窗 -->
    <LiveBrowserPreview />

    <!-- 全局二次安全验证弹窗 -->
    <VerificationDialog />
  </div>
</template>

<script setup lang="ts">
import { LayoutDashboard, Users2, Send, Layers, Settings2 } from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import LiveBrowserPreview from "./components/LiveBrowserPreview.vue"
import VerificationDialog from "./components/VerificationDialog.vue"

interface NavItem {
  name: string
  path: string
  icon: any
  badge?: string
}

const navItems: NavItem[] = [
  { name: "概览仪表盘", path: "/", icon: LayoutDashboard },
  { name: "账号矩阵管理", path: "/accounts", icon: Users2 },
  { name: "创建矩阵分发", path: "/publish", icon: Send },
  { name: "任务调度看板", path: "/tasks", icon: Layers },
  { name: "系统全局设置", path: "/settings", icon: Settings2 },
]
</script>

<style>
/* 全局基础重置 */
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background-color: #f8fafc;
  color: #1e293b;
}
* {
  box-sizing: border-box;
}
</style>
