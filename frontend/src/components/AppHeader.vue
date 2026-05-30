<template>
  <header class="app-header">
    <div class="header-left">
      <div class="breadcrumb">
        EduChain / 区块链综合实验
      </div>
      <div class="header-title">
        {{ currentTitle }}
      </div>
    </div>

    <div class="header-right">
      <div class="search-box">
        <span class="search-icon">⌕</span>
        <input placeholder="搜索课程、证书、交易哈希" />
      </div>

      <button class="header-action">链上同步</button>

      <div class="user-profile">
        <div class="avatar">管</div>
        <div class="user-info">
          <div class="user-name">管理员</div>
          <div class="user-role">实验平台管理端</div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const currentTitle = computed(() => {
  return route.meta.title || '数据看板'
})
</script>

<style scoped>
.app-header {
  position: fixed;
  left: var(--sidebar-width);
  right: 0;
  top: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: blur(12px);
}

.header-left {
  min-width: 0;
}

.breadcrumb {
  font-size: 12px;
  color: var(--text-muted);
}

.header-title {
  margin-top: 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.search-box {
  display: flex;
  align-items: center;
  width: 280px;
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--border-color);
  border-radius: 999px;
  background: #f9fafb;
}

.search-icon {
  margin-right: 8px;
  color: var(--text-muted);
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 13px;
  color: var(--text-primary);
}

.header-action {
  height: 38px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  color: #ffffff;
  background: var(--primary-color);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s;
}

.header-action:hover {
  background: var(--primary-dark);
}

.user-profile {
  display: flex;
  align-items: center;
  height: 42px;
  padding-left: 8px;
}

.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: #ffffff;
  background: var(--primary-color);
  font-size: 14px;
  font-weight: 700;
}

.user-info {
  margin-left: 10px;
}

.user-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.user-role {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-muted);
}
</style>