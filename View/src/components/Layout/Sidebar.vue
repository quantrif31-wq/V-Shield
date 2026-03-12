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
                <span class="logo-text" :class="{ 'sr-only': collapsed }">V-Shield</span>
            </transition>
        </div>

        <!-- Navigation -->
        <nav class="sidebar-nav">
            <!-- Thêm search bar vào Sidebar, ẩn khi collapsed -->
            <transition name="fade">
                <div class="sidebar-search" v-if="!collapsed" ref="searchContainerRef">
                    <div class="search-bar">
                        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8" />
                            <path d="M21 21l-4.35-4.35" />
                        </svg>
                        <input v-model="searchQuery" type="text" placeholder="Tìm kiếm nhân viên, phương tiện..."
                            @input="debouncedSearch" @focus="showDropdown = true" />

                        <!-- Dropdown Results -->
                        <transition name="dropdown">
                            <div v-show="showDropdown && (isSearching || searchResults.length > 0 || noResultsFound)"
                                class="search-dropdown">
                                <div v-if="isSearching" class="dropdown-msg">Đang tìm kiếm...</div>
                                <div v-else-if="noResultsFound" class="dropdown-msg">Không tìm thấy kết quả</div>
                                <div v-else class="dropdown-list">
                                    <div v-for="res in searchResults" :key="res.id" class="dropdown-item"
                                        @click="handleResultClick(res)">
                                        <div class="result-icon">
                                            <svg v-if="res.type === 'employee'" viewBox="0 0 24 24" fill="none"
                                                stroke="currentColor" stroke-width="1.5">
                                                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                                                <circle cx="12" cy="7" r="4" />
                                            </svg>
                                        </div>
                                        <div class="result-info">
                                            <div class="result-name">{{ res.name }}</div>
                                            <div class="result-sub">{{ res.sub }}</div>
                                        </div>
                                        <div class="result-badge">{{ res.badge }}</div>
                                    </div>
                                </div>
                            </div>
                        </transition>
                    </div>
                </div>
            </transition>

            <div class="nav-section">
                <span class="nav-label" :class="{ 'sr-only': collapsed }">MENU CHÍNH</span>
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

            <div class="nav-section" :style="collapsed ? 'margin-top: 10px;' : 'margin-top: 20px;'">
                <span class="nav-label" :class="{ 'sr-only': collapsed }">HỆ THỐNG</span>
            </div>
            <router-link v-for="item in systemItems.filter(i => !i.adminOnly || authState.user?.role === 'Admin')"
                :key="item.path" :to="item.path" class="nav-item" :class="{ active: $route.path === item.path }">
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authState } from '../../stores/auth'
import { getAll as getAllEmployees } from '../../services/employeeApi'

const router = useRouter()

defineProps({
    collapsed: Boolean
})

defineEmits(['toggle'])

const menuItems = ref([
    {
        path: '/',
        label: 'Dashboard',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>'
    },
    {
        path: '/employees',
        label: 'Nhân viên',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
        badge: '0'
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
        path: '/pre-registrations',
        label: 'Đăng ký trước',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M9 14l2 2 4-4"/></svg>'
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
    {
        path: '/bienso',
        label: 'bienso',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
    {
        path: '/facevideo',
        label: 'facevideo',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    }
])

onMounted(async () => {
    document.addEventListener('click', handleClickOutside)

    try {
        const res = await getAllEmployees()
        const count = res.data.length
        const empItem = menuItems.value.find(item => item.path === '/employees')
        if (empItem) {
            empItem.badge = count.toString()
        }
    } catch (error) {
        console.error('Lỗi khi lấy số lượng nhân viên:', error)
    }
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})

// Search Logic
const searchQuery = ref('')
const showDropdown = ref(false)
const isSearching = ref(false)
const searchResults = ref([])
const noResultsFound = ref(false)
const searchContainerRef = ref(null)

let searchTimeout = null

const debouncedSearch = () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    if (!searchQuery.value.trim()) {
        searchResults.value = []
        isSearching.value = false
        noResultsFound.value = false
        showDropdown.value = false
        return
    }

    showDropdown.value = true
    isSearching.value = true
    noResultsFound.value = false

    searchTimeout = setTimeout(async () => {
        try {
            const query = searchQuery.value.trim()
            // Fetch employees
            const curEmployees = await getAllEmployees({ search: query })

            const results = []

            // Map employees
            if (curEmployees.data && curEmployees.data.length > 0) {
                curEmployees.data.forEach(emp => {
                    results.push({
                        id: 'emp_' + emp.employeeId,
                        type: 'employee',
                        name: emp.fullName,
                        sub: emp.departmentName || 'Không có phòng ban',
                        badge: 'Nhân viên',
                        originalId: emp.employeeId
                    })
                })
            }

            // Mocks vehicle logic here later if needed

            searchResults.value = results
            noResultsFound.value = results.length === 0
        } catch (error) {
            console.error('Search error:', error)
            searchResults.value = []
            noResultsFound.value = true
        } finally {
            isSearching.value = false
        }
    }, 400)
}

const handleResultClick = (res) => {
    if (res.type === 'employee') {
        router.push({ path: '/employees', query: { search: res.name } })
    }

    // reset search
    showDropdown.value = false
    searchQuery.value = ''
    searchResults.value = []
}

const handleClickOutside = (e) => {
    if (searchContainerRef.value && !searchContainerRef.value.contains(e.target)) {
        showDropdown.value = false
    }
}

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

.sidebar-search {
    padding: 0 4px 16px;
}

.search-bar {
    position: relative;
    width: 100%;
}

.search-bar .search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: var(--text-muted);
}

.search-bar input {
    width: 100%;
    padding: 9px 16px 9px 38px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--text-primary);
    font-size: 0.8rem;
    transition: all var(--transition-normal);
}

.search-bar input:focus {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.1);
}

.search-bar input::placeholder {
    color: var(--text-muted);
}

.nav-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    white-space: nowrap;
    display: block;
    transition: opacity 0.2s;
}

.sr-only {
    opacity: 0;
    pointer-events: none;
}

/* Dropdown */
.search-dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    box-shadow: var(--shadow-lg);
    z-index: 200;
    max-height: 280px;
    overflow-y: auto;
}

.dropdown-msg {
    padding: 12px 16px;
    font-size: 0.85rem;
    color: var(--text-muted);
    text-align: center;
}

.dropdown-list {
    display: flex;
    flex-direction: column;
}

.dropdown-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    cursor: pointer;
    border-bottom: 1px solid var(--border-color);
    transition: background var(--transition-fast);
}

.dropdown-item:last-child {
    border-bottom: none;
}

.dropdown-item:hover {
    background: var(--bg-card-hover);
}

.result-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: rgba(16, 121, 196, 0.1);
    color: var(--accent-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.result-icon svg {
    width: 18px;
    height: 18px;
}

.result-info {
    flex: 1;
    overflow: hidden;
}

.result-name {
    font-weight: 600;
    font-size: 0.85rem;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.result-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.result-badge {
    font-size: 0.65rem;
    padding: 2px 6px;
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent-success);
    border-radius: 4px;
    white-space: nowrap;
}

/* Transition for dropdown */
.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-5px);
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
    background: rgba(16, 121, 196, 0.08);
    color: var(--text-primary);
}

.nav-item.active {
    background: rgba(16, 121, 196, 0.12);
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
    background: rgba(16, 121, 196, 0.15);
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
