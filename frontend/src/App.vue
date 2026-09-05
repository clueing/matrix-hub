<template>
  <el-container class="app-layout">
    <!-- 侧边栏导航 -->
    <el-aside width="240px" class="aside-menu">
      <div class="brand-area">
        <img src="./assets/logo.png" alt="MatrixHub" class="brand-logo-img" />
      </div>

      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
        background-color="#0f172a"
        text-color="#94a3b8"
        active-text-color="#38bdf8"
      >
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>概览仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/accounts">
          <el-icon><User /></el-icon>
          <span>账号矩阵管理</span>
        </el-menu-item>
        <el-menu-item index="/publish">
          <el-icon><Promotion /></el-icon>
          <span>创建矩阵分发</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><Tickets /></el-icon>
          <span>任务调度看板</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统全局设置</span>
        </el-menu-item>
      </el-menu>

      <div class="system-badge">
        <div class="flex items-center gap-2">
          <span class="status-dot"></span>
          <span class="text-xs text-slate-400">本地服务已就绪</span>
        </div>
      </div>
    </el-aside>

    <!-- 主工作区 -->
    <el-container class="main-container">
      <el-header class="app-header">
        <div class="font-bold text-gray-700 text-base">
          {{ $route.meta.title || "自媒体多账号矩阵分发平台" }}
        </div>
        <div class="flex items-center gap-3">
          <el-tag size="small" type="success" effect="plain">v0.1.0 (本地私有化)</el-tag>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>

    <!-- 全局 Manus 风格实时受控浏览器视窗 -->
    <LiveBrowserPreview />
  </el-container>
</template>

<script setup lang="ts">
import { Odometer, User, Promotion, Tickets, Setting } from "@element-plus/icons-vue"
import LiveBrowserPreview from "./components/LiveBrowserPreview.vue"
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

<style scoped>
.app-layout {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
.aside-menu {
  background-color: #0f172a;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #1e293b;
}
.brand-area {
  padding: 16px 14px 12px 14px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-bottom: 1px solid #1e293b;
  background: radial-gradient(circle at center top, rgba(56, 189, 248, 0.08) 0%, transparent 70%);
}
.brand-logo-img {
  width: 100%;
  max-width: 185px;
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 4px 16px rgba(56, 189, 248, 0.25));
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), filter 0.25s ease;
  user-select: none;
}
.brand-logo-img:hover {
  transform: scale(1.03);
  filter: drop-shadow(0 6px 20px rgba(56, 189, 248, 0.45));
}
.el-menu-vertical {
  border-right: none;
  flex: 1;
}
.el-menu-item {
  height: 52px;
  line-height: 52px;
  font-size: 14px;
}
.el-menu-item.is-active {
  background-color: #1e293b !important;
  font-weight: 600;
  border-left: 4px solid #38bdf8;
}
.system-badge {
  padding: 16px 20px;
  border-top: 1px solid #1e293b;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 6px #10b981;
}
.main-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.app-header {
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.app-main {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
  background-color: #f8fafc;
}
.flex { display: flex; }
.items-center { align-items: center; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.text-xs { font-size: 12px; }
.text-base { font-size: 15px; }
.font-bold { font-weight: 600; }
.text-gray-700 { color: #334155; }
.text-slate-400 { color: #94a3b8; }
</style>
