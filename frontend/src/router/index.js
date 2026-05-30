import { createRouter, createWebHistory } from 'vue-router'

import Login from '@/views/Login.vue'
import Market from '@/views/Market.vue'
import Upload from '@/views/Upload.vue'
import Verify from '@/views/Verify.vue'
import Wallet from '@/views/Wallet.vue'
import Audit from '@/views/Audit.vue'
import Status from '@/views/Status.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '登录系统'
    }
  },
  {
    path: '/market',
    name: 'Market',
    component: Market,
    meta: {
      title: '资料市场'
    }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    meta: {
      title: '上传资料'
    }
  },
  {
    path: '/verify',
    name: 'Verify',
    component: Verify,
    meta: {
      title: '文件验证'
    }
  },
  {
    path: '/wallet',
    name: 'Wallet',
    component: Wallet,
    meta: {
      title: '我的钱包'
    }
  },
  {
    path: '/audit',
    name: 'Audit',
    component: Audit,
    meta: {
      title: '审计追溯'
    }
  },
  {
    path: '/status',
    name: 'Status',
    component: Status,
    meta: {
      title: '系统状态'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
