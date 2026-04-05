import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/Settings.vue'),
  },
  {
    path: '/parse-management',
    name: 'parse-management',
    component: () => import('@/views/ParseManagement.vue'),
  },
  {
    path: '/papers',
    name: 'Papers',
    component: () => import('@/views/PapersView.vue'),
    meta: { title: '论文管理' }
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
