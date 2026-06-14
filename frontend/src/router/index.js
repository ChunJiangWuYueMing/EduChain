import { createRouter, createWebHistory } from 'vue-router'

import Login from '@/views/Login.vue'
import Market from '@/views/Market.vue'
import Upload from '@/views/Upload.vue'
import Verify from '@/views/Verify.vue'
import Wallet from '@/views/Wallet.vue'
import Audit from '@/views/Audit.vue'
import Status from '@/views/Status.vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录系统'
    }
  },
  {
    path: '/',
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/market' },
      {
        path: '/market',
        name: 'Market',
        component: Market,
        meta: { title: '资料市场', requiresAuth: true },
      },
      {
        path: '/upload',
        name: 'Upload',
        component: Upload,
        meta: { title: '上传资料', requiresAuth: true },
      },
      {
        path: '/verify',
        name: 'Verify',
        component: Verify,
        meta: { title: '文件验证', requiresAuth: true },
      },
      {
        path: '/wallet',
        name: 'Wallet',
        component: Wallet,
        meta: { title: '我的钱包', requiresAuth: true },
      },
      {
        path: '/audit',
        name: 'Audit',
        component: Audit,
        meta: { title: '审计追溯', requiresAuth: true },
      },
      {
        path: '/status',
        name: 'Status',
        component: Status,
        meta: { title: '系统状态', requiresAuth: true },
      },
    ],
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

let sessionChecked = false

router.beforeEach(async (to) => {
  document.title = `${to.meta.title || 'EduChain'} - EduChain`
  const auth = useAuthStore()
  if (!sessionChecked) {
    await auth.check()
    sessionChecked = true
  }
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && auth.isLoggedIn) {
    return '/market'
  }
})

export default router
