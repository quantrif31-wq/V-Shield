<template>
    <header class="app-header" :class="{ collapsed: collapsed && !isMobile }">
        <div class="header-left">
            <button
                type="button"
                class="menu-toggle"
                aria-label="Mở điều hướng"
                @click="$emit('toggle-sidebar')"
            >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="6" x2="21" y2="6" />
                    <line x1="3" y1="12" x2="21" y2="12" />
                    <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
            </button>

            <div class="header-intro">
                <span class="header-eyebrow">Security operations center</span>
                <div class="header-copy">
                    <h2>{{ pageTitle }}</h2>
                    <p>{{ pageDescription }}</p>
                </div>
            </div>
        </div>

        <div class="header-right" ref="dropdownRootRef">
            <div class="header-chip status-chip">
                <span class="chip-dot"></span>
                <span>Ổn định</span>
            </div>

            <div class="header-chip time-chip">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M12 7v5l3 2" />
                </svg>
                <div>
                    <strong>{{ currentTime }}</strong>
                    <span>{{ currentDate }}</span>
                </div>
            </div>

            <button
                type="button"
                class="header-action"
                aria-label="Thông báo"
                @click="toggleNotifications"
            >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 01-3.46 0" />
                </svg>
                <span v-if="unreadCount" class="notification-count">{{ unreadCount }}</span>
            </button>

            <div class="header-user-wrap">
                <button type="button" class="header-user" @click="toggleUserMenu">
                    <div class="user-avatar">{{ userInitial }}</div>
                    <div class="user-info">
                        <span class="user-name">{{ authState.user?.fullName || authState.user?.username || 'User' }}</span>
                        <span class="user-role">{{ roleLabel }}</span>
                    </div>
                    <svg class="user-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 9l6 6 6-6" />
                    </svg>
                </button>

                <transition name="dropdown">
                    <div v-if="showUserMenu" class="dropdown user-dropdown">
                        <div class="dropdown-user-info">
                            <div class="user-avatar large">{{ userInitial }}</div>
                            <div>
                                <p class="dropdown-user-name">{{ authState.user?.fullName || authState.user?.username }}</p>
                                <p class="dropdown-user-role">{{ roleLabel }}</p>
                            </div>
                        </div>

                        <div class="dropdown-list simple">
                            <div class="dropdown-summary">
                                <span>Truy cập hiện tại</span>
                                <strong>{{ pageTitle }}</strong>
                            </div>

                            <button type="button" class="dropdown-item" @click="handleLogout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                                    <polyline points="16 17 21 12 16 7" />
                                    <line x1="21" y1="12" x2="9" y2="12" />
                                </svg>
                                Đăng xuất an toàn
                            </button>
                        </div>
                    </div>
                </transition>
            </div>

            <transition name="dropdown">
                <div v-if="showNotifications" class="dropdown notification-dropdown">
                    <div class="dropdown-header">
                        <div>
                            <span>Thông báo điều phối</span>
                            <small>{{ unreadCount }} mục cần chú ý</small>
                        </div>
                        <button type="button" class="btn-link" @click="markAllRead">Đánh dấu đã đọc</button>
                    </div>

                    <div class="notification-list">
                        <div
                            v-for="n in notifications"
                            :key="n.id"
                            class="notification-item"
                            :class="{ unread: !n.read }"
                        >
                            <div class="notification-icon" :class="n.type">
                                <svg v-if="n.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path d="M20 6L9 17l-5-5" />
                                </svg>
                                <svg v-else-if="n.type === 'warning'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                                    <line x1="12" y1="9" x2="12" y2="13" />
                                    <line x1="12" y1="17" x2="12.01" y2="17" />
                                </svg>
                                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <circle cx="12" cy="12" r="9" />
                                    <path d="M12 8v5" />
                                    <path d="M12 16h.01" />
                                </svg>
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
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authState, logout } from '../../stores/auth'

defineProps({
    collapsed: Boolean,
    isMobile: Boolean,
})

defineEmits(['toggle-sidebar'])

const router = useRouter()
const route = useRoute()
const dropdownRootRef = ref(null)
const showNotifications = ref(false)
const showUserMenu = ref(false)
const currentTime = ref('')
const currentDate = ref('')

const routeMeta = {
    Dashboard: {
        title: 'Tổng quan hệ thống',
        description: 'Giám sát con người, phương tiện và camera trong một luồng điều phối thống nhất.',
    },
    Monitoring: {
        title: 'Giám sát thời gian thực',
        description: 'Theo dõi luồng camera, tình trạng kết nối và tín hiệu an ninh tại các điểm truy cập.',
    },
    AccessLogs: {
        title: 'Nhật ký ra vào',
        description: 'Đối soát lịch sử check-in, check-out và các tín hiệu cảnh báo theo thời gian.',
    },
    Employees: {
        title: 'Hồ sơ nhân sự',
        description: 'Quản lý lực lượng nội bộ, danh tính, vai trò và dữ liệu nhận diện.',
    },
    Vehicles: {
        title: 'Quản lý phương tiện',
        description: 'Kiểm soát biển số, luồng phương tiện và trạng thái cấp quyền.',
    },
    PreRegistration: {
        title: 'Đăng ký khách trước',
        description: 'Tạo luồng đón tiếp nhanh với mã truy cập rõ ràng và ít ma sát.',
    },
    Settings: {
        title: 'Điều chỉnh hệ thống',
        description: 'Tinh chỉnh cấu hình vận hành, quy tắc nhận diện và môi trường tích hợp.',
    },
    UserManagement: {
        title: 'Quản trị tài khoản',
        description: 'Kiểm soát người dùng, quyền truy cập và phạm vi vận hành.',
    },
    DepartmentPosition: {
        title: 'Cấu trúc tổ chức',
        description: 'Sắp xếp phòng ban, vị trí công việc và quan hệ điều phối nội bộ.',
    },
    AboutProject: {
        title: 'Thông tin nền tảng',
        description: 'Tóm tắt mục tiêu, kiến trúc và năng lực chính của giải pháp V-Shield.',
    },
    Login: {
        title: 'Xác thực truy cập',
        description: 'Đăng nhập bảo mật để tiếp cận trung tâm điều phối V-Shield.',
    },
}

const pageTitle = computed(() => routeMeta[route.name]?.title || 'V-Shield Control Room')
const pageDescription = computed(() => routeMeta[route.name]?.description || 'Điều phối và kiểm soát ra vào tập trung.')

const userInitial = computed(() => {
    const name = authState.user?.fullName || authState.user?.username || 'U'
    return name.charAt(0).toUpperCase()
})

const roleLabel = computed(() => {
    const map = {
        Admin: 'Quản trị viên',
        Staff: 'Nhân viên vận hành',
        BaoVe: 'Bảo vệ trực cổng',
    }
    return map[authState.user?.role] || authState.user?.role || 'Tài khoản hệ thống'
})

const notifications = ref([
    {
        id: 1,
        message: 'Nhân viên Nguyễn Văn A đã check-in tại Cổng A lúc 08:05.',
        time: '5 phút trước',
        type: 'success',
        read: false,
    },
    {
        id: 2,
        message: 'Biển số 51A-123.45 đang cần xác minh lại nhận diện.',
        time: '12 phút trước',
        type: 'warning',
        read: false,
    },
    {
        id: 3,
        message: 'Camera 02 vừa khôi phục kết nối sau 1 phút gián đoạn.',
        time: '1 giờ trước',
        type: 'info',
        read: true,
    },
])

const unreadCount = computed(() => notifications.value.filter(item => !item.read).length)

function updateTime() {
    const now = new Date()
    currentTime.value = now.toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
    })
    currentDate.value = now.toLocaleDateString('vi-VN', {
        weekday: 'long',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

function closeDropdowns() {
    showNotifications.value = false
    showUserMenu.value = false
}

function toggleNotifications() {
    showNotifications.value = !showNotifications.value
    showUserMenu.value = false
}

function toggleUserMenu() {
    showUserMenu.value = !showUserMenu.value
    showNotifications.value = false
}

function markAllRead() {
    notifications.value = notifications.value.map(item => ({ ...item, read: true }))
}

function handleLogout() {
    logout()
    router.push('/login')
}

function handleDocumentClick(event) {
    if (dropdownRootRef.value && !dropdownRootRef.value.contains(event.target)) {
        closeDropdowns()
    }
}

let timer = null

onMounted(() => {
    updateTime()
    timer = setInterval(updateTime, 1000)
    document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
    clearInterval(timer)
    document.removeEventListener('click', handleDocumentClick)
})

watch(
    () => route.fullPath,
    () => {
        closeDropdowns()
    }
)
</script>

<style scoped>
.app-header {
    position: fixed;
    top: 16px;
    right: 18px;
    left: calc(var(--sidebar-width) + 18px);
    height: var(--header-height);
    z-index: 85;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 16px 22px;
    border-radius: 26px;
    border: 1px solid rgba(255, 255, 255, 0.6);
    background: var(--bg-header);
    backdrop-filter: var(--glass-blur);
    box-shadow: var(--shadow-sm);
    transition: left var(--transition-slow);
}

.app-header.collapsed {
    left: calc(var(--sidebar-collapsed-width) + 18px);
}

.header-left {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 16px;
}

.menu-toggle {
    width: 44px;
    height: 44px;
    display: none;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    border: 1px solid var(--border-color);
    background: rgba(255, 255, 255, 0.76);
    color: var(--text-secondary);
    flex-shrink: 0;
}

.menu-toggle svg {
    width: 20px;
    height: 20px;
}

.header-intro {
    min-width: 0;
}

.header-eyebrow {
    display: inline-block;
    margin-bottom: 4px;
    color: var(--text-muted);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.header-copy h2 {
    font-family: var(--font-heading);
    font-size: 1.28rem;
    font-weight: 700;
    line-height: 1.05;
    color: var(--text-primary);
}

.header-copy p {
    margin-top: 4px;
    max-width: 52ch;
    color: var(--text-secondary);
    font-size: 0.9rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.header-right {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
}

.header-chip {
    min-height: 48px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 0 16px;
    border-radius: 999px;
    border: 1px solid var(--border-color);
    background: rgba(255, 255, 255, 0.74);
    color: var(--text-secondary);
}

.status-chip {
    color: var(--accent-success);
    border-color: rgba(20, 134, 109, 0.16);
    background: rgba(20, 134, 109, 0.08);
    font-weight: 700;
}

.chip-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 0 5px rgba(20, 134, 109, 0.12);
}

.time-chip svg {
    width: 18px;
    height: 18px;
    color: var(--text-muted);
    flex-shrink: 0;
}

.time-chip div {
    display: flex;
    flex-direction: column;
}

.time-chip strong {
    color: var(--text-primary);
    font-weight: 700;
    line-height: 1;
}

.time-chip span {
    margin-top: 3px;
    color: var(--text-muted);
    font-size: 0.74rem;
}

.header-action {
    position: relative;
    width: 46px;
    height: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    border: 1px solid var(--border-color);
    background: rgba(255, 255, 255, 0.78);
    color: var(--text-secondary);
    transition: border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast), background var(--transition-fast);
}

.header-action:hover {
    transform: translateY(-1px);
    border-color: var(--border-color-hover);
    color: var(--accent-primary);
    background: rgba(255, 255, 255, 0.96);
}

.header-action svg {
    width: 20px;
    height: 20px;
}

.notification-count {
    position: absolute;
    top: -4px;
    right: -3px;
    min-width: 20px;
    height: 20px;
    padding: 0 5px;
    border-radius: 999px;
    background: var(--accent-danger);
    color: #fff;
    font-size: 0.68rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 20px rgba(195, 81, 70, 0.24);
}

.header-user-wrap {
    position: relative;
}

.header-user {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    min-height: 50px;
    padding: 0 14px 0 8px;
    border-radius: 18px;
    border: 1px solid var(--border-color);
    background: rgba(255, 255, 255, 0.8);
    color: var(--text-primary);
    transition: border-color var(--transition-fast), transform var(--transition-fast), background var(--transition-fast);
}

.header-user:hover {
    transform: translateY(-1px);
    border-color: var(--border-color-hover);
    background: rgba(255, 255, 255, 0.96);
}

.user-avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-gradient);
    color: #fff;
    font-weight: 700;
    box-shadow: 0 14px 28px rgba(15, 124, 130, 0.18);
}

.user-avatar.large {
    width: 48px;
    height: 48px;
    font-size: 1rem;
}

.user-info {
    display: flex;
    flex-direction: column;
    text-align: left;
}

.user-name {
    font-size: 0.9rem;
    font-weight: 700;
}

.user-role {
    color: var(--text-muted);
    font-size: 0.74rem;
}

.user-chevron {
    width: 16px;
    height: 16px;
    color: var(--text-muted);
}

.dropdown {
    position: absolute;
    top: calc(100% + 12px);
    right: 0;
    width: min(380px, calc(100vw - 32px));
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.68);
    background: rgba(255, 255, 255, 0.92);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    backdrop-filter: var(--glass-blur);
}

.notification-dropdown {
    right: 72px;
}

.dropdown-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 18px 20px 16px;
    border-bottom: 1px solid rgba(24, 49, 77, 0.08);
}

.dropdown-header span {
    display: block;
    font-family: var(--font-heading);
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
}

.dropdown-header small {
    display: block;
    margin-top: 4px;
    color: var(--text-muted);
    font-size: 0.76rem;
}

.btn-link {
    color: var(--accent-primary);
    font-size: 0.78rem;
    font-weight: 700;
}

.dropdown-user-info {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 20px;
    border-bottom: 1px solid rgba(24, 49, 77, 0.08);
}

.dropdown-user-name {
    color: var(--text-primary);
    font-size: 0.96rem;
    font-weight: 700;
}

.dropdown-user-role {
    margin-top: 4px;
    color: var(--text-muted);
    font-size: 0.78rem;
}

.dropdown-list.simple {
    padding: 14px;
}

.dropdown-summary {
    padding: 4px 8px 14px;
    color: var(--text-muted);
    font-size: 0.76rem;
}

.dropdown-summary strong {
    display: block;
    margin-top: 6px;
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 1rem;
}

.dropdown-item {
    width: 100%;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    min-height: 44px;
    padding: 0 14px;
    border-radius: 14px;
    color: var(--text-secondary);
    transition: background var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.dropdown-item:hover {
    transform: translateY(-1px);
    background: rgba(195, 81, 70, 0.08);
    color: var(--accent-danger);
}

.dropdown-item svg {
    width: 18px;
    height: 18px;
}

.notification-list {
    max-height: 360px;
    overflow-y: auto;
    padding: 10px;
}

.notification-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px;
    border-radius: 16px;
    transition: background var(--transition-fast);
}

.notification-item + .notification-item {
    margin-top: 6px;
}

.notification-item:hover {
    background: rgba(236, 244, 246, 0.74);
}

.notification-item.unread {
    background: rgba(84, 196, 211, 0.08);
}

.notification-icon {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.notification-icon.success {
    background: rgba(20, 134, 109, 0.12);
    color: var(--accent-success);
}

.notification-icon.warning {
    background: rgba(184, 111, 33, 0.12);
    color: var(--accent-warning);
}

.notification-icon.info {
    background: rgba(15, 124, 130, 0.1);
    color: var(--accent-primary);
}

.notification-icon svg {
    width: 18px;
    height: 18px;
}

.notification-content p {
    color: var(--text-primary);
    font-size: 0.88rem;
    line-height: 1.45;
}

.notification-time {
    display: block;
    margin-top: 6px;
    color: var(--text-muted);
    font-size: 0.76rem;
}

.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.18s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-6px);
}

@media (max-width: 1280px) {
    .status-chip {
        display: none;
    }

    .header-copy p {
        max-width: 38ch;
    }
}

@media (max-width: 1023px) {
    .app-header {
        top: 12px;
        left: 12px;
        right: 12px;
        height: var(--header-height);
        padding: 14px 16px;
    }

    .menu-toggle {
        display: inline-flex;
    }

    .time-chip {
        display: none;
    }

    .header-copy p {
        display: none;
    }
}

@media (max-width: 768px) {
    .header-copy h2 {
        font-size: 1.08rem;
    }

    .header-eyebrow {
        display: none;
    }

    .header-user {
        padding-right: 10px;
    }

    .user-info,
    .user-chevron {
        display: none;
    }

    .notification-dropdown {
        right: 0;
    }
}
</style>
