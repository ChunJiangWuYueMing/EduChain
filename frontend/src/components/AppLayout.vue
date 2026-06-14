<template>
  <div class="app-shell">
    <AppSidebar />
    <div class="app-stage">
      <AppHeader />
      <main class="app-view">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'

const auth = useAuthStore()
const system = useSystemStore()

onMounted(() => {
  system.startPolling()
  auth.refreshBalance()
})

onBeforeUnmount(system.stopPolling)
</script>

<style scoped>
.app-shell {
  width: 100%;
  min-height: 100vh;
  color: var(--text-primary);
  background: #f4f7fa;
}

.app-stage {
  min-width: 0;
  min-height: 100vh;
  margin-left: var(--sidebar-width);
}

.app-view {
  min-height: 100vh;
  padding-top: var(--header-height);
}
</style>
