<template>
    <header class="app-header">
        <div class="header-left">
            <button class="menu-toggle" @click="$emit('toggle-sidebar')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <line x1="3" y1="12" x2="21" y2="12" />
                    <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
            </button>
            <div class="search-bar">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8" />
                    <path d="M21 21l-4.35-4.35" />
                </svg>
                <input type="text" placeholder="Tìm kiếm nhân viên, phương tiện..." />
            </div>
        </div>

        <div class="header-right">
            <!-- Live Clock -->
            <div class="header-clock">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    style="width: 16px; height: 16px;">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                </svg>
                <span>{{ currentTime }}</span>
            </div>

            <!-- Notifications -->
            <button class="header-action" @click="showNotifications = !showNotifications">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 01-3.46 0" />
                </svg>
                <span class="notification-dot"></span>
            </button>

            <!-- User Profile -->
        <div class="header-user" @click="showUserMenu = !showUserMenu">
            <div class="user-avatar">{{ userInitial }}</div>
            <div class="user-info">
                <span class="user-name">{{ authState.user?.fullName || authState.user?.username || 'User' }}</span>
                <span class="user-role">{{ roleLabel }}</span>
            </div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                style="width: 16px; height: 16px;">
                <path d="M6 9l6 6 6-6" />
            </svg>
        </div>

        <!-- User Dropdown -->
        <transition name="dropdown">
            <div v-if="showUserMenu" class="dropdown user-dropdown">
                <div class="dropdown-user-info">
                    <div class="user-avatar" style="width:40px;height:40px;font-size:1rem;">{{ userInitial }}</div>
                    <div>
                        <p style="font-weight:600;">{{ authState.user?.fullName || authState.user?.username }}</p>
                        <p style="font-size:0.8rem;color:var(--text-muted);">{{ roleLabel }}</p>
                    </div>
                </div>
                <div style="border-top:1px solid var(--border-color);padding:8px;">
                    <button class="dropdown-item" @click="handleLogout">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px;">
                            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                            <polyline points="16 17 21 12 16 7" />
                            <line x1="21" y1="12" x2="9" y2="12" />
                        </svg>
                        Đăng xuất
                    </button>
                </div>
            </div>
        </transition>

            <!-- Notification Dropdown -->
            <transition name="dropdown">
                <div v-if="showNotifications" class="dropdown notification-dropdown">
                    <div class="dropdown-header">
                        <span>Thông báo</span>
                        <button class="btn-link">Đánh dấu tất cả đã đọc</button>
                    </div>
                    <div class="notification-list">
                        <div v-for="n in notifications" :key="n.id" class="notification-item"
                            :class="{ unread: !n.read }">
                            <div class="notification-icon" :class="n.type">
                                <span v-html="n.icon"></span>
                            </div>
                            <div class="notification-content">
                                <p>{{ n.message }}</p>
                                <span class="notification-time">{{ n.time }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </transition>
        </div>
    </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authState, logout } from '../../stores/auth'

const router = useRouter()

defineEmits(['toggle-sidebar'])

const userInitial = computed(() => {
    const name = authState.user?.fullName || authState.user?.username || 'U'
    return name.charAt(0).toUpperCase()
})

const roleLabel = computed(() => {
    const map = { Admin: 'Quản trị viên', Staff: 'Nhân viên', BaoVe: 'Bảo vệ' }
    return map[authState.user?.role] || authState.user?.role || ''
})

function handleLogout() {
    logout()
    router.push('/login')
}

const showNotifications = ref(false)
const showUserMenu = ref(false)
const currentTime = ref('')

let timer = null

const updateTime = () => {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }) + ' - ' + now.toLocaleDateString('vi-VN', {
        weekday: 'long',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}

onMounted(() => {
    updateTime()
    timer = setInterval(updateTime, 1000)
})

onUnmounted(() => {
    clearInterval(timer)
})

const notifications = ref([
    {
        id: 1,
        message: 'Nhân viên Nguyễn Văn A đã check-in lúc 08:05',
        time: '5 phút trước',
        type: 'success',
        icon: '✓',
        read: false
    },
    {
        id: 2,
        message: 'Phương tiện 51A-123.45 không nhận dạng được',
        time: '12 phút trước',
        type: 'warning',
        icon: '⚠',
        read: false
    },
    {
        id: 3,
        message: 'Camera 02 mất kết nối',
        time: '1 giờ trước',
        type: 'danger',
        icon: '✕',
        read: true
    },
])
</script>

<style scoped>
.app-header {
    position: fixed;
    top: 0;
    right: 0;
    left: var(--sidebar-width);
    height: var(--header-height);
    background: var(--bg-header);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    z-index: 90;
    transition: left var(--transition-slow);
}

.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.menu-toggle {
    width: 36px;
    height: 36px;
    display: none;
    align-items: center;
    justify-content: center;
    background: transparent;
    color: var(--text-secondary);
    border-radius: var(--border-radius-sm);
}

.menu-toggle svg {
    width: 20px;
    height: 20px;
}

.menu-toggle:hover {
    background: var(--bg-card);
    color: var(--text-primary);
}

.search-bar {
    position: relative;
    width: 360px;
}

.search-bar .search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    color: var(--text-muted);
}

.search-bar input {
    width: 100%;
    padding: 9px 16px 9px 42px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--text-primary);
    font-size: 0.85rem;
    transition: all var(--transition-normal);
}

.search-bar input:focus {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-bar input::placeholder {
    color: var(--text-muted);
}

.header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    position: relative;
}

.header-clock {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 500;
    padding: 6px 14px;
    background: var(--bg-card);
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--border-color);
    white-space: nowrap;
}

.header-action {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--text-secondary);
    position: relative;
    transition: all var(--transition-fast);
}

.header-action svg {
    width: 20px;
    height: 20px;
}

.header-action:hover {
    background: var(--bg-card-hover);
    color: var(--text-primary);
    border-color: var(--accent-primary);
}

.notification-dot {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 8px;
    height: 8px;
    background: var(--accent-danger);
    border-radius: 50%;
    border: 2px solid var(--bg-card);
}

.header-user {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.header-user:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-color-hover);
}

.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--accent-gradient);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
    color: #fff;
}

.user-info {
    display: flex;
    flex-direction: column;
}

.user-name {
    font-weight: 600;
    font-size: 0.85rem;
}

.user-role {
    font-size: 0.7rem;
    color: var(--text-muted);
}

/* Dropdown */
.dropdown {
    position: absolute;
    top: 52px;
    right: 0;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-lg);
    min-width: 360px;
    z-index: 200;
}

.dropdown-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    font-weight: 600;
    font-size: 0.95rem;
}

.btn-link {
    background: none;
    color: var(--accent-primary);
    font-size: 0.8rem;
    font-weight: 500;
}

.btn-link:hover {
    text-decoration: underline;
}

.notification-list {
    max-height: 320px;
    overflow-y: auto;
}

.notification-item {
    display: flex;
    gap: 12px;
    padding: 14px 20px;
    border-bottom: 1px solid var(--border-color);
    transition: background var(--transition-fast);
}

.notification-item:hover {
    background: var(--bg-card-hover);
}

.notification-item:last-child {
    border-bottom: none;
}

.notification-item.unread {
    background: rgba(59, 130, 246, 0.04);
}

.notification-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 0.85rem;
}

.notification-icon.success {
    background: rgba(16, 185, 129, 0.15);
    color: var(--accent-success);
}

.notification-icon.warning {
    background: rgba(245, 158, 11, 0.15);
    color: var(--accent-warning);
}

.notification-icon.danger {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
}

.notification-content p {
    font-size: 0.85rem;
    line-height: 1.4;
    color: var(--text-primary);
}

.notification-time {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
    display: block;
}

/* User Dropdown */
.user-dropdown {
    min-width: 240px;
}

.dropdown-user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
}

.dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 14px;
    background: none;
    color: var(--text-secondary);
    font-size: 0.9rem;
    border-radius: var(--border-radius-sm);
    transition: all var(--transition-fast);
}

.dropdown-item:hover {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-danger);
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

@media (max-width: 768px) {
    .app-header {
        left: 0;
    }

    .menu-toggle {
        display: flex;
    }

    .search-bar {
        width: 180px;
    }

    .header-clock {
        display: none;
    }

    .user-info {
        display: none;
    }
}
</style>
