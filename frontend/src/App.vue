<template>
  <div class="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-800 antialiased">
    <!-- 侧边栏导航 -->
    <aside class="flex w-60 flex-col border-r border-slate-800 bg-[#0f172a] text-slate-300">
      <!-- 品牌区 (严格 60px 等高对齐) -->
      <div class="flex h-[60px] items-center gap-2.5 border-b border-slate-800 px-3.5 bg-gradient-to-r from-sky-500/10 via-transparent to-transparent">
        <img src="./assets/logo.png" alt="MatrixHub" class="h-9 w-auto max-w-[42px] object-contain drop-shadow-[0_2px_8px_rgba(56,189,248,0.35)] transition-transform duration-200 hover:scale-105" />
        <div class="flex min-w-0 flex-1 flex-col justify-center">
          <div class="flex items-center gap-1.5 leading-tight">
            <span class="text-[15px] font-bold tracking-wide text-white">MatrixHub</span>
            <span class="inline-flex items-center rounded border border-sky-500/30 bg-sky-500/15 px-1 py-0.2 text-[10px] font-semibold text-sky-400">矩阵</span>
          </div>
          <span class="truncate text-[11px] text-slate-400 mt-0.5">多账号矩阵分发平台</span>
        </div>
      </div>

      <!-- 导航项列表 -->
      <nav class="flex-1 space-y-1.5 p-3 overflow-y-auto">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 select-none"
          :class="[
            $route.path === item.path
              ? 'bg-sky-500/15 text-sky-400 shadow-sm shadow-sky-500/10 font-semibold'
              : 'text-slate-400 hover:bg-slate-800/80 hover:text-slate-200'
          ]"
        >
          <component
            :is="item.icon"
            class="h-4 w-4 transition-transform duration-150 group-hover:scale-110"
            :class="[ $route.path === item.path ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200' ]"
          />
          <span class="truncate">{{ item.name }}</span>
          <span
            v-if="item.badge"
            class="ml-auto rounded-full bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold text-slate-400"
          >
            {{ item.badge }}
          </span>
        </router-link>
      </nav>

      <!-- 底部系统状态徽章 -->
      <div class="border-t border-slate-800/90 p-3.5 bg-slate-950/40">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="relative flex h-2 w-2">
              <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span class="text-xs text-slate-400">本地自动化引擎就绪</span>
          </div>
          <span class="text-[10px] font-mono text-slate-400">v0.1</span>
        </div>
      </div>
    </aside>

    <!-- 主工作区 -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- 顶部 Header (严格 60px 等高) -->
      <header class="flex h-[60px] items-center justify-between border-b border-slate-200 bg-white px-6 shadow-sm">
        <div class="flex items-center gap-2.5">
          <h1 class="text-base font-bold text-slate-800 tracking-tight">
            {{ $route.meta.title || "控制台" }}
          </h1>
          <span class="text-xs text-slate-400 font-normal">/</span>
          <span class="text-xs text-slate-500 font-normal">自媒体矩阵分发平台</span>
        </div>

        <div class="flex items-center gap-3">
          <router-link
            to="/publish"
            class="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm shadow-blue-500/20 transition-all hover:brightness-110 active:scale-95"
          >
            <Send class="h-3.5 w-3.5" />
            <span>创建分发任务</span>
          </router-link>
        </div>
      </header>

      <!-- 页面主要内容区 -->
      <main class="flex-1 overflow-y-auto bg-slate-50/60 p-6">
        <router-view />
      </main>
    </div>

    <!-- 全局 Manus 风格实时受控浏览器视窗 -->
    <LiveBrowserPreview />
  </div>
</template>

<script setup lang="ts">
import { LayoutDashboard, Users2, Send, Layers, Settings2 } from "lucide-vue-next"
import LiveBrowserPreview from "./components/LiveBrowserPreview.vue"

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
