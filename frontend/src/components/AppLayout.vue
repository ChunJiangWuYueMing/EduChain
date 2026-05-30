<template>
  <div class="app-layout">
    <AppSidebar />

    <div class="app-main">
      <AppHeader />

      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from './AppSidebar.vue'
import AppHeader from './AppHeader.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-page);
}

.app-main {
  flex: 1;
  min-width: 0;
  margin-left: var(--sidebar-width);
}

.app-content {
  min-height: calc(100vh - var(--header-height));
  padding: var(--content-padding);
  padding-top: calc(var(--header-height) + var(--content-padding));
}
</style>