<template>
  <header class="shell-header">
    <div class="shell-title">
      <h1>{{ route.meta.title || 'EduChain' }}</h1>
      <span>{{ route.meta.subtitle || '校园学习资料可信分发平台' }}</span>
    </div>

    <div class="shell-actions">
      <button class="global-search-trigger" type="button" @click="openSearch">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <span>资料搜索</span>
      </button>

      <button class="shell-chain-status" type="button" @click="system.refresh">
        <span>链状态</span>
        <i :class="{ offline: !system.connected }"></i>
        <strong>{{ system.connected ? '已连接' : '未连接' }}</strong>
      </button>

      <section class="shell-user-card" aria-label="当前用户">
        <div class="shell-avatar">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="8" r="4" />
            <path d="M4 21a8 8 0 0 1 16 0" />
          </svg>
        </div>
        <div class="shell-user-main">
          <strong>{{ auth.user?.name || '--' }}</strong>
          <span>学号：{{ auth.user?.student_id || '--' }}</span>
        </div>
        <div class="shell-user-balance">
          <span>EDU 余额</span>
          <strong>{{ auth.user?.edu_balance ?? '--' }}</strong>
        </div>
        <div class="shell-user-address">
          <span>地址</span>
          <strong :title="auth.user?.eth_address">{{ truncate(auth.user?.eth_address) }}</strong>
          <button type="button" aria-label="复制钱包地址" @click="copyAddress">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <rect x="9" y="9" width="11" height="11" rx="2" />
              <rect x="4" y="4" width="11" height="11" rx="2" />
            </svg>
          </button>
        </div>
        <button class="shell-logout" type="button" @click="handleLogout">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M10 17 15 12l-5-5" />
            <path d="M15 12H3" />
            <path d="M21 19V5a2 2 0 0 0-2-2h-6" />
          </svg>
          退出
        </button>
      </section>
    </div>
  </header>

  <Teleport to="body">
    <div v-if="searchOpen" class="search-overlay" @click.self="closeSearch">
      <section class="search-dialog" role="dialog" aria-modal="true" aria-label="全局资料搜索">
        <header>
          <div>
            <strong>全局搜索</strong>
            <p>输入资料名称或课程编号，回车后进入资料市场。</p>
          </div>
          <button type="button" aria-label="关闭搜索" @click="closeSearch">×</button>
        </header>
        <form @submit.prevent="submitSearch">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input ref="searchInput" v-model.trim="searchTerm" placeholder="例如：区块链、CS201" />
          <button type="submit">搜索资料</button>
        </form>
        <div class="search-shortcuts">
          <span>快捷前往</span>
          <button
            v-for="item in appNavigation"
            :key="item.path"
            type="button"
            @click="navigateTo(item.path)"
          >
            <i v-html="item.icon"></i>{{ item.label }}
          </button>
        </div>
      </section>
    </div>
  </Teleport>

  <div v-if="notice" class="shell-notice" role="status">{{ notice }}</div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { appNavigation } from '@/config/navigation'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'
import { copyText } from '@/utils/clipboard'
import { truncate } from '@/utils/api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const system = useSystemStore()
const searchOpen = ref(false)
const searchTerm = ref('')
const searchInput = ref(null)
const notice = ref('')

function showNotice(message) {
  notice.value = message
  window.clearTimeout(showNotice.timer)
  showNotice.timer = window.setTimeout(() => {
    notice.value = ''
  }, 1800)
}

async function openSearch() {
  searchTerm.value = String(route.query.search || '')
  searchOpen.value = true
  await nextTick()
  searchInput.value?.focus()
}

function closeSearch() {
  searchOpen.value = false
}

async function submitSearch() {
  closeSearch()
  await router.push({
    path: '/market',
    query: searchTerm.value ? { search: searchTerm.value } : {},
  })
}

async function navigateTo(path) {
  closeSearch()
  await router.push(path)
}

async function copyAddress() {
  if (!auth.user?.eth_address) return
  await copyText(auth.user.eth_address)
  showNotice('钱包地址已复制')
}

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.shell-header {
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 14px 0 28px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #dce4ef;
  backdrop-filter: blur(14px);
}

.shell-title {
  width: 128px;
  flex: 0 0 128px;
  min-width: 128px;
}

.shell-title h1 {
  margin: 0;
  color: #10233f;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.05;
  white-space: nowrap;
}

.shell-title span {
  display: none;
}

.shell-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 12px;
}

.global-search-trigger,
.shell-chain-status {
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #53647c;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  font: inherit;
  cursor: pointer;
}

.global-search-trigger {
  width: 112px;
  flex: 0 0 112px;
}

.global-search-trigger svg {
  width: 20px;
  height: 20px;
}

.global-search-trigger svg,
.shell-user-card svg,
.search-dialog svg,
.search-shortcuts :deep(svg) {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.shell-chain-status {
  width: 136px;
  flex: 0 0 136px;
  padding: 0;
  border-color: transparent;
  background: transparent;
  white-space: nowrap;
}

.shell-chain-status > span,
.shell-chain-status i {
  flex: 0 0 auto;
}

.shell-chain-status i {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}

.shell-chain-status i.offline {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.12);
}

.shell-chain-status strong {
  color: #10233f;
  white-space: nowrap;
}

.shell-user-card {
  display: grid;
  flex: 0 0 516px;
  grid-template-columns: 48px 126px 96px 168px 78px;
  width: 516px;
  min-height: 58px;
  align-items: center;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
}

.shell-avatar {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  margin-left: 10px;
  color: #2f6fbc;
  background: #e8f2ff;
  border-radius: 50%;
}

.shell-avatar svg {
  width: 25px;
  height: 25px;
  fill: currentColor;
  stroke: none;
}

.shell-user-main,
.shell-user-balance,
.shell-user-address {
  display: grid;
  gap: 4px;
  height: 58px;
  align-content: center;
  min-width: 0;
  padding: 0 12px;
  border-left: 1px solid #e5e7eb;
}

.shell-user-main {
  border-left: none;
}

.shell-user-main strong,
.shell-user-address strong {
  overflow: hidden;
  color: #10233f;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shell-user-main span,
.shell-user-balance span,
.shell-user-address span {
  color: #53647c;
  font-size: 12px;
}

.shell-user-balance strong {
  color: #0079ba;
  font-size: 17px;
}

.shell-user-address {
  position: relative;
  padding-right: 34px;
}

.shell-user-address button {
  position: absolute;
  right: 8px;
  top: 19px;
  width: 24px;
  height: 24px;
  padding: 3px;
  color: #53647c;
  background: transparent;
  border: none;
  cursor: pointer;
}

.shell-user-address svg {
  width: 17px;
  height: 17px;
}

.shell-logout {
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #10233f;
  background: #ffffff;
  border: none;
  border-left: 1px solid #e5e7eb;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.shell-logout svg {
  width: 18px;
  height: 18px;
}

.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: start center;
  padding-top: 112px;
  background: rgba(2, 19, 39, 0.48);
  backdrop-filter: blur(5px);
}

.search-dialog {
  width: min(680px, calc(100vw - 48px));
  padding: 24px;
  background: #ffffff;
  border: 1px solid #dce4ef;
  border-radius: 14px;
  box-shadow: 0 28px 80px rgba(0, 29, 64, 0.28);
}

.search-dialog header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-dialog header strong {
  color: #10233f;
  font-size: 22px;
}

.search-dialog header p {
  margin: 6px 0 0;
  color: #53647c;
  font-size: 14px;
}

.search-dialog header button {
  width: 36px;
  height: 36px;
  color: #53647c;
  background: #f4f7fa;
  border: 1px solid #dce4ef;
  border-radius: 8px;
  font-size: 22px;
  cursor: pointer;
}

.search-dialog form {
  display: grid;
  grid-template-columns: 24px 1fr 104px;
  align-items: center;
  gap: 10px;
  height: 54px;
  padding: 0 8px 0 16px;
  border: 1px solid #bfd1e5;
  border-radius: 9px;
}

.search-dialog form svg {
  width: 21px;
  height: 21px;
  color: #0079ba;
}

.search-dialog form input {
  min-width: 0;
  border: none;
  outline: none;
  font: inherit;
}

.search-dialog form button {
  height: 40px;
  color: #ffffff;
  background: #0079ba;
  border: none;
  border-radius: 7px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.search-shortcuts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
}

.search-shortcuts > span {
  margin-right: 4px;
  color: #53647c;
  font-size: 13px;
}

.search-shortcuts button {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 11px;
  color: #33506f;
  background: #f4f8fc;
  border: 1px solid #dce4ef;
  border-radius: 7px;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.search-shortcuts i,
.search-shortcuts :deep(svg) {
  width: 16px;
  height: 16px;
}

.shell-notice {
  position: fixed;
  left: calc(var(--sidebar-width) + (100vw - var(--sidebar-width)) / 2);
  bottom: 26px;
  z-index: 110;
  transform: translateX(-50%);
  padding: 10px 18px;
  color: #ffffff;
  background: rgba(16, 35, 63, 0.94);
  border-radius: 999px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
  font-size: 14px;
}

@media (max-width: 1320px) {
  .global-search-trigger {
    width: 44px;
    flex-basis: 44px;
  }

  .global-search-trigger span,
  .shell-chain-status > span {
    display: none;
  }

  .shell-chain-status {
    width: 92px;
    flex-basis: 92px;
  }
}
</style>
