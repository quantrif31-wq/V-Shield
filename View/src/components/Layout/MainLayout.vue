<template>
    <div class="app-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
        <Sidebar :collapsed="sidebarCollapsed" @toggle="sidebarCollapsed = !sidebarCollapsed" />
        <Header @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
        <main class="main-content">
            <router-view />
        </main>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const sidebarCollapsed = ref(false)
</script>

<style scoped>
.app-layout {
    min-height: 100vh;
}

.main-content {
    margin-left: var(--sidebar-width);
    margin-top: var(--header-height);
    transition: margin-left var(--transition-slow);
}

.sidebar-collapsed .main-content {
    margin-left: var(--sidebar-collapsed-width);
}

@media (max-width: 768px) {
    .main-content {
        margin-left: 0;
    }
}
</style>
