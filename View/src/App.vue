<template>
  <div class="app-layout">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
    <div class="main-content" :class="{ collapsed: sidebarCollapsed }">
      <Header @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
      <main class="content-area">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './components/Layout/Sidebar.vue'
import Header from './components/Layout/Header.vue'

const sidebarCollapsed = ref(false)
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-slow);
}

.main-content.collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

.content-area {
  margin-top: var(--header-height);
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 0;
  }
}
</style>
