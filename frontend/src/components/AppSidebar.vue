<template>
  <aside class="shell-sidebar">
    <div class="shell-brand">
      <img :src="logoUrl" alt="西南交通大学 EduChain" />
      <p>校园学习资料可信分发</p>
    </div>

    <nav class="shell-nav" aria-label="功能导航">
      <RouterLink
        v-for="item in appNavigation"
        :key="item.path"
        :to="item.path"
        class="shell-nav-item"
      >
        <span class="shell-nav-icon" v-html="item.icon"></span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <img class="shell-watermark" :src="sidebarArtUrl" alt="" aria-hidden="true" />
    <div class="shell-bridge" aria-hidden="true"></div>

    <button class="shell-chain" type="button" @click="system.refresh">
      <span class="shell-status-dot" :class="{ offline: !system.connected }"></span>
      <span>{{ system.connected ? '课程测试 · 链正常' : '课程测试 · 链异常' }}</span>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M21 12a9 9 0 1 1-2.64-6.36" />
        <path d="M21 4v6h-6" />
      </svg>
    </button>
  </aside>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { appNavigation } from '@/config/navigation'
import { useSystemStore } from '@/stores/system'
import logoUrl from '@/assets/images/swjtu-logo-white.png'
import sidebarArtUrl from '@/assets/images/educhain_white_logo.png'

const system = useSystemStore()
</script>

<style scoped>
.shell-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 20;
  width: var(--sidebar-width);
  overflow: hidden;
  color: #ffffff;
  background: linear-gradient(180deg, #003a70 0%, #002f60 48%, #00284f 100%);
  box-shadow: 8px 0 28px rgba(0, 39, 82, 0.2);
}

.shell-brand {
  height: 177px;
  padding: 30px 20px 22px;
}

.shell-brand img {
  width: 210px;
  height: 78px;
  object-fit: contain;
  object-position: left center;
}

.shell-brand p {
  margin: 13px 0 0;
  color: rgba(255, 255, 255, 0.86);
  font-size: 16px;
  font-weight: 600;
}

.shell-nav {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 10px;
  padding: 0 8px;
}

.shell-nav-item {
  display: flex;
  align-items: center;
  gap: 15px;
  height: 60px;
  padding: 0 22px;
  color: rgba(255, 255, 255, 0.88);
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  transition:
    color 0.18s ease,
    background 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease;
}

.shell-nav-item:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.shell-nav-item.router-link-active {
  color: #ffffff;
  background: linear-gradient(135deg, #0079ba 0%, #005f92 100%);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 24px rgba(0, 36, 90, 0.22);
}

.shell-nav-icon,
.shell-nav-icon :deep(svg) {
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
}

.shell-nav-icon :deep(svg),
.shell-chain svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.shell-watermark {
  position: absolute;
  z-index: 1;
  right: -118px;
  bottom: 148px;
  width: 340px;
  height: 340px;
  object-fit: contain;
  opacity: 0.1;
  pointer-events: none;
  transform: rotate(-10deg);
  filter: drop-shadow(0 22px 42px rgba(0, 0, 0, 0.16));
}

.shell-bridge {
  position: absolute;
  left: -52px;
  right: 0;
  bottom: 96px;
  height: 210px;
  opacity: 0.2;
  border-top: 1px solid rgba(209, 232, 255, 0.35);
  border-bottom: 1px solid rgba(209, 232, 255, 0.25);
  border-radius: 50%;
  transform: rotate(-8deg);
}

.shell-chain {
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 18px;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 11px;
  height: 48px;
  padding: 0 12px;
  color: #ffffff;
  background: rgba(0, 31, 66, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.shell-chain svg {
  width: 18px;
  height: 18px;
  margin-left: auto;
}

.shell-status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}

.shell-status-dot.offline {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.12);
}
</style>
