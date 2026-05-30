<template>
  <aside class="app-sidebar">
    <div class="sidebar-brand">
      <img class="school-logo" :src="swjtuLogo" alt="西南交通大学校徽" />

      <div class="brand-text">
        <div class="brand-title">EduChain</div>
        <div class="brand-subtitle">区块链综合实验平台</div>
      </div>
    </div>

    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <div class="chain-card">
        <div class="chain-card-title">当前链状态</div>
        <div class="chain-card-value">
          <span class="dot"></span>
          运行正常
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import swjtuLogo from '@/assets/images/swjtu-logo.png'

const navItems = [
  {
    label: '数据看板',
    path: '/dashboard',
    icon: '▣'
  },
  {
    label: '课程管理',
    path: '/courses',
    icon: '▤'
  },
  {
    label: '证书存证',
    path: '/certificates',
    icon: '◇'
  },
  {
    label: '链上记录',
    path: '/records',
    icon: '◎'
  },
  {
    label: '节点管理',
    path: '/nodes',
    icon: '⬡'
  },
  {
    label: '系统设置',
    path: '/settings',
    icon: '⚙'
  }
]
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 20;
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  height: 82px;
  padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
}

.school-logo {
  width: 42px;
  height: 42px;
  object-fit: contain;
  flex-shrink: 0;
}

.brand-text {
  margin-left: 12px;
  min-width: 0;
}

.brand-title {
  font-size: 20px;
  font-weight: 800;
  color: var(--primary-color);
  line-height: 1.2;
}

.brand-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 18px 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  height: 44px;
  padding: 0 14px;
  margin-bottom: 6px;
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  transition: 0.2s;
}

.nav-item:hover {
  color: var(--primary-color);
  background: var(--primary-light);
}

.nav-item.active {
  color: #ffffff;
  background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
  box-shadow: 0 10px 22px rgba(0, 121, 186, 0.24);
}

.nav-icon {
  width: 24px;
  margin-right: 10px;
  text-align: center;
  font-size: 15px;
}

.nav-label {
  font-weight: 500;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}

.chain-card {
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, #e6f4fa, #ffffff);
  border: 1px solid rgba(0, 121, 186, 0.18);
}

.chain-card-title {
  font-size: 12px;
  color: var(--text-secondary);
}

.chain-card-value {
  display: flex;
  align-items: center;
  margin-top: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--primary-dark);
}

.dot {
  width: 8px;
  height: 8px;
  margin-right: 8px;
  border-radius: 50%;
  background: var(--success-color);
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}
</style>