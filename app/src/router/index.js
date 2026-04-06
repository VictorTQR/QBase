import { createRouter, createWebHistory } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'

const routes = [
  {
    path: '/workspace-selector',
    name: 'workspace-selector',
    component: () => import('@/views/WorkspaceSelector.vue'),
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/parse-management',
    name: 'parse-management',
    component: () => import('@/views/ParseManagement.vue'),
    meta: { requiresWorkspace: true },
  },
  {
    path: '/papers',
    name: 'Papers',
    component: () => import('@/views/PapersView.vue'),
    meta: { title: '论文管理', requiresWorkspace: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const workspaceStore = useWorkspaceStore()

  if (to.meta.requiresWorkspace && !workspaceStore.isWorkspaceSelected) {
    next('/workspace-selector')
  } else if (to.path === '/workspace-selector' && workspaceStore.isWorkspaceSelected) {
    next('/')
  } else {
    next()
  }
})

export default router
