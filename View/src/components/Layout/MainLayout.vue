<template>
    <div
        class="ops-shell"
        :class="{
            'nav-collapsed': desktopCollapsed,
            'nav-open': mobileSidebarOpen,
            'is-mobile': isMobile,
        }"
    >
        <div class="shell-background" aria-hidden="true">
            <div class="shell-glow shell-glow-a"></div>
            <div class="shell-glow shell-glow-b"></div>
            <div class="shell-grid"></div>
        </div>

        <Sidebar
            :collapsed="desktopCollapsed"
            :is-mobile="isMobile"
            :mobile-open="mobileSidebarOpen"
            @toggle="handleSidebarToggle"
            @close-mobile="mobileSidebarOpen = false"
        />

        <button
            v-if="isMobile && mobileSidebarOpen"
            class="shell-scrim"
            type="button"
            aria-label="Đóng điều hướng"
            @click="mobileSidebarOpen = false"
        ></button>

        <div class="shell-main">
            <Header
                :collapsed="desktopCollapsed"
                :is-mobile="isMobile"
                @toggle-sidebar="handleSidebarToggle"
            />

            <main class="main-content">
                <div class="content-shell">
                    <router-view v-slot="{ Component, route }">
                        <keep-alive>
                            <component :is="Component" v-if="route.meta.keepAlive" />
                        </keep-alive>
                        <component :is="Component" v-if="!route.meta.keepAlive" />
                    </router-view>
                </div>
            </main>
        </div>
    </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const isMobile = ref(false)
const desktopCollapsed = ref(false)
const mobileSidebarOpen = ref(false)

function syncViewport() {
    const nextIsMobile = window.innerWidth < 1024
    isMobile.value = nextIsMobile

    if (!nextIsMobile) {
        mobileSidebarOpen.value = false
    }
}

function handleSidebarToggle() {
    if (isMobile.value) {
        mobileSidebarOpen.value = !mobileSidebarOpen.value
        return
    }

    desktopCollapsed.value = !desktopCollapsed.value
}

onMounted(() => {
    syncViewport()
    window.addEventListener('resize', syncViewport)
})

onUnmounted(() => {
    window.removeEventListener('resize', syncViewport)
})
</script>

<style scoped>
.ops-shell {
    min-height: 100vh;
    position: relative;
}

.shell-background {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
}

.shell-glow {
    position: absolute;
    border-radius: 999px;
    filter: blur(90px);
    opacity: 0.3;
}

.shell-glow-a {
    width: 420px;
    height: 420px;
    top: 72px;
    right: -120px;
    background: rgba(84, 196, 211, 0.38);
}

.shell-glow-b {
    width: 360px;
    height: 360px;
    bottom: -80px;
    left: 18%;
    background: rgba(216, 155, 55, 0.18);
}

.shell-grid {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(16, 32, 51, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(16, 32, 51, 0.025) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.32), transparent 88%);
}

.shell-main {
    position: relative;
    z-index: 1;
}

.main-content {
    margin-left: var(--sidebar-width);
    padding-top: calc(var(--header-height) + 18px);
    transition: margin-left var(--transition-slow);
}

.nav-collapsed .main-content {
    margin-left: var(--sidebar-collapsed-width);
}

.content-shell {
    min-height: calc(100vh - var(--header-height));
    padding-bottom: 28px;
}

.shell-scrim {
    position: fixed;
    inset: 0;
    z-index: 84;
    background: rgba(16, 32, 51, 0.42);
    backdrop-filter: blur(6px);
}

:global(body.monitoring-immersive) {
    overflow: hidden;
}

@media (max-width: 1023px) {
    .main-content {
        margin-left: 0;
        padding-top: calc(var(--header-height) + 10px);
    }

    .content-shell {
        padding-bottom: 18px;
    }
}
</style>
