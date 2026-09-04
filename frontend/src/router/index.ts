import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    name: "Dashboard",
    component: () => import("../views/Dashboard.vue"),
    meta: { title: "概览仪表盘" }
  },
  {
    path: "/accounts",
    name: "Accounts",
    component: () => import("../views/Accounts.vue"),
    meta: { title: "账号矩阵管理" }
  },
  {
    path: "/publish",
    name: "PublishTask",
    component: () => import("../views/PublishTask.vue"),
    meta: { title: "创建矩阵分发" }
  },
  {
    path: "/tasks",
    name: "TaskList",
    component: () => import("../views/TaskList.vue"),
    meta: { title: "任务调度看板" }
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("../views/Settings.vue"),
    meta: { title: "系统全局设置" }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
