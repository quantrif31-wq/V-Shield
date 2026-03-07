<template>
    <aside class="sidebar" :class="{ collapsed }">
        <!-- Logo -->
        <div class="sidebar-logo">
            <div class="logo-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" stroke-width="2"
                        stroke-linejoin="round" />
                    <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" fill="currentColor" opacity="0.3" />
                    <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" stroke="currentColor" stroke-width="1.5"
                        stroke-linejoin="round" />
                </svg>
            </div>
            <transition name="fade">
                <span v-if="!collapsed" class="logo-text">V-Shield</span>
            </transition>
        </div>

        <!-- Navigation -->
        <nav class="sidebar-nav">
            <div class="nav-section">
                <span v-if="!collapsed" class="nav-label">MENU CHÍNH</span>
            </div>
            <router-link v-for="item in menuItems" :key="item.path" :to="item.path" class="nav-item"
                :class="{ active: $route.path === item.path }">
                <span class="nav-icon" v-html="item.icon"></span>
                <transition name="fade">
                    <span v-if="!collapsed" class="nav-text">{{ item.label }}</span>
                </transition>
                <transition name="fade">
                    <span v-if="!collapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
                </transition>
            </router-link>

            <div class="nav-section" style="margin-top: 20px;">
                <span v-if="!collapsed" class="nav-label">HỆ THỐNG</span>
            </div>
            <router-link v-for="item in systemItems.filter(i => !i.adminOnly || authState.user?.role === 'Admin')" :key="item.path" :to="item.path" class="nav-item"
                :class="{ active: $route.path === item.path }">
                <span class="nav-icon" v-html="item.icon"></span>
                <transition name="fade">
                    <span v-if="!collapsed" class="nav-text">{{ item.label }}</span>
                </transition>
            </router-link>
        </nav>

        <!-- Toggle Button -->
        <button class="sidebar-toggle" @click="$emit('toggle')">
            <svg :class="{ rotated: collapsed }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6" />
            </svg>
        </button>
    </aside>
</template>

<script setup>
import { authState } from '../../stores/auth'

defineProps({
    collapsed: Boolean
})

defineEmits(['toggle'])

const menuItems = [
    {
        path: '/',
        label: 'Dashboard',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'
    },
    {
        path: '/employees',
        label: 'Nhân viên',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
        badge: '24'
    },
    {
        path: '/vehicles',
        label: 'Phương tiện',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
    },
    {
        path: '/access-logs',
        label: 'Lịch sử ra/vào',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>',
        badge: '156'
    },
    {
        path: '/monitoring',
        label: 'Giám sát',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
    {
        path: '/FaceID',
        label: 'FaceID',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
]

const systemItems = [
    {
        path: '/users',
        label: 'Quản lý tài khoản',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
        adminOnly: true,
    },
    {
        path: '/departments-positions',
        label: 'Phòng ban & Chức vụ',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        adminOnly: true,
    },
    {
        path: '/settings',
        label: 'Cài đặt',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>'
    },
]
</script>

<style scoped>
.sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: var(--sidebar-width);
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    z-index: 100;
    transition: width var(--transition-slow);
    overflow: hidden;
}

.sidebar.collapsed {
    width: var(--sidebar-collapsed-width);
}

/* Logo */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    min-height: var(--header-height);
}

.logo-icon {
    width: 36px;
    height: 36px;
    color: var(--accent-primary);
    flex-shrink: 0;
}

.logo-icon svg {
    width: 100%;
    height: 100%;
}

.logo-text {
    font-size: 1.3rem;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    white-space: nowrap;
}

/* Navigation */
.sidebar-nav {
    flex: 1;
    padding: 16px 12px;
    overflow-y: auto;
    overflow-x: hidden;
}

.nav-section {
    padding: 8px 12px 8px;
}

.nav-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    white-space: nowrap;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    margin: 3px 0;
    border-radius: var(--border-radius-sm);
    color: var(--text-secondary);
    transition: all var(--transition-normal);
    white-space: nowrap;
    position: relative;
}

.nav-item:hover {
    background: rgba(59, 130, 246, 0.08);
    color: var(--text-primary);
}

.nav-item.active {
    background: rgba(59, 130, 246, 0.12);
    color: var(--accent-primary);
}

.nav-item.active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 8px;
    bottom: 8px;
    width: 3px;
    background: var(--accent-primary);
    border-radius: 0 3px 3px 0;
}

.nav-icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.nav-icon :deep(svg) {
    width: 100%;
    height: 100%;
}

.nav-text {
    font-size: 0.9rem;
    font-weight: 500;
}

.nav-badge {
    margin-left: auto;
    padding: 2px 8px;
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent-primary);
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* Toggle Button */
.sidebar-toggle {
    padding: 16px;
    border-top: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: color var(--transition-fast);
}

.sidebar-toggle:hover {
    color: var(--text-primary);
}

.sidebar-toggle svg {
    width: 20px;
    height: 20px;
    transition: transform var(--transition-slow);
}

.sidebar-toggle svg.rotated {
    transform: rotate(180deg);
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
    }

    .sidebar:not(.collapsed) {
        transform: translateX(0);
        box-shadow: var(--shadow-lg);
    }
}
</style>
