<template>
    <aside
        class="sidebar"
        :class="{
            collapsed,
            'is-mobile': isMobile,
            'mobile-open': mobileOpen,
        }"
    >
        <div class="sidebar-panel">
            <div class="sidebar-top">
                <div class="sidebar-logo">
                    <div class="logo-icon">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M12 2L3 7V17L12 22L21 17V7L12 2Z"
                                stroke="currentColor"
                                stroke-width="1.8"
                                stroke-linejoin="round"
                            />
                            <path
                                d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z"
                                fill="currentColor"
                                opacity="0.28"
                            />
                            <path
                                d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z"
                                stroke="currentColor"
                                stroke-width="1.4"
                                stroke-linejoin="round"
                            />
                        </svg>
                    </div>

                    <transition name="fade">
                        <div v-if="!collapsed" class="logo-copy">
                            <span class="logo-title">V-Shield</span>
                            <span class="logo-subtitle">Security Operations</span>
                        </div>
                    </transition>
                </div>

                <button
                    v-if="isMobile"
                    type="button"
                    class="sidebar-mobile-close"
                    aria-label="Đóng điều hướng"
                    @click="$emit('close-mobile')"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                </button>
            </div>

            <div class="sidebar-status" :class="{ compact: collapsed }">
                <span class="status-dot"></span>
                <transition name="fade">
                    <span v-if="!collapsed">Dữ liệu nghiệp vụ đã sẵn sàng cho ca trực</span>
                </transition>
            </div>

            <nav class="sidebar-nav">
                <transition name="fade">
                    <div v-if="!collapsed" class="sidebar-search" ref="searchContainerRef">
                        <label class="search-label" for="sidebar-search">Tra cứu nhanh</label>
                        <div class="search-shell">
                            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                            <input
                                id="sidebar-search"
                                v-model="searchQuery"
                                type="text"
                                placeholder="Nhân sự, khách thăm..."
                                @input="debouncedSearch"
                                @focus="showDropdown = true"
                            />

                            <transition name="dropdown">
                                <div
                                    v-show="showDropdown && (isSearching || searchResults.length > 0 || noResultsFound)"
                                    class="search-dropdown"
                                >
                                    <div v-if="isSearching" class="dropdown-msg">Đang tra cứu dữ liệu...</div>
                                    <div v-else-if="noResultsFound" class="dropdown-msg">Không có kết quả phù hợp</div>
                                    <div v-else class="dropdown-list">
                                        <button
                                            v-for="res in searchResults"
                                            :key="res.id"
                                            type="button"
                                            class="dropdown-item"
                                            @click="handleResultClick(res)"
                                        >
                                            <div class="result-icon">
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                                                    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                                                    <circle cx="12" cy="7" r="4" />
                                                </svg>
                                            </div>
                                            <div class="result-info">
                                                <div class="result-name">{{ res.name }}</div>
                                                <div class="result-sub">{{ res.sub }}</div>
                                            </div>
                                            <span class="result-badge">{{ res.badge }}</span>
                                        </button>
                                    </div>
                                </div>
                            </transition>
                        </div>
                    </div>
                </transition>

                <div v-for="group in visibleGroups" :key="group.label" class="nav-group">
                    <button
                        v-if="!collapsed"
                        type="button"
                        class="nav-label-toggle"
                        @click="toggleGroup(group.label)"
                    >
                        <span class="nav-label-text">{{ group.label }}</span>
                        <svg
                            class="nav-label-chevron"
                            :class="{ 'chevron-collapsed': collapsedGroups[group.label] }"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                        >
                            <path d="M6 9l6 6 6-6" />
                        </svg>
                    </button>
                    <span v-else class="nav-label sr-only">{{ group.label }}</span>

                    <div
                        class="nav-group-items"
                        :class="{ 'group-collapsed': collapsedGroups[group.label] && !collapsed }"
                    >
                        <router-link
                            v-for="item in group.items"
                            :key="item.path"
                            :to="item.path"
                            class="nav-item"
                            :class="{ active: route.path === item.path }"
                            @click="handleNavClick"
                        >
                            <span class="nav-icon" v-html="item.icon"></span>
                            <transition name="fade">
                                <span v-if="!collapsed" class="nav-copy">
                                    <span class="nav-text">{{ item.label }}</span>
                                    <span class="nav-hint">{{ item.hint }}</span>
                                </span>
                            </transition>
                            <transition name="fade">
                                <span v-if="!collapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
                            </transition>
                        </router-link>
                    </div>
                </div>

                <div v-if="passageItems.length" class="nav-group">
                    <button
                        v-if="!collapsed"
                        type="button"
                        class="nav-label-toggle"
                        @click="toggleGroup('Thông hành')"
                    >
                        <span class="nav-label-text">Thông hành</span>
                        <svg
                            class="nav-label-chevron"
                            :class="{ 'chevron-collapsed': collapsedGroups['Thông hành'] }"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                        >
                            <path d="M6 9l6 6 6-6" />
                        </svg>
                    </button>
                    <span v-else class="nav-label sr-only">Thông hành</span>

                    <div
                        class="nav-group-items"
                        :class="{ 'group-collapsed': collapsedGroups['Thông hành'] && !collapsed }"
                    >
                        <router-link
                            v-for="item in passageItems"
                            :key="item.path"
                            :to="item.path"
                            class="nav-item"
                            :class="{ active: route.path === item.path }"
                            @click="handleNavClick"
                        >
                            <span class="nav-icon" v-html="item.icon"></span>
                            <transition name="fade">
                                <span v-if="!collapsed" class="nav-copy">
                                    <span class="nav-text">{{ item.label }}</span>
                                    <span class="nav-hint">{{ item.hint }}</span>
                                </span>
                            </transition>
                            <transition name="fade">
                                <span v-if="!collapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
                            </transition>
                        </router-link>
                    </div>
                </div>
            </nav>

            <div class="sidebar-footer">
                <transition name="fade">
                    <div v-if="!collapsed" class="footer-card">
                        <div class="footer-chip">
                            <span class="chip-ping"></span>
                            Business data mapped
                        </div>
                        <div class="footer-metrics">
                            <div>
                                <strong>{{ authState.user?.role || 'Staff' }}</strong>
                                <span>Vai trò hiện tại</span>
                            </div>
                            <div>
                                <strong>{{ navigationGroupCount }} nhóm</strong>
                                <span>Điều hướng nghiệp vụ</span>
                            </div>
                        </div>
                    </div>
                </transition>

                <button
                    v-if="!isMobile"
                    type="button"
                    class="sidebar-toggle"
                    :aria-label="collapsed ? 'Mở rộng điều hướng' : 'Thu gọn điều hướng'"
                    @click="$emit('toggle')"
                >
                    <svg :class="{ rotated: collapsed }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M15 18l-6-6 6-6" />
                    </svg>
                </button>
            </div>
        </div>
    </aside>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authState } from '../../stores/auth'
import { getAll as getAllEmployees } from '../../services/employeeApi'
import { getGuestProfiles } from '../../services/guestProfileApi'

const props = defineProps({
    collapsed: Boolean,
    isMobile: Boolean,
    mobileOpen: Boolean,
})

const emit = defineEmits(['toggle', 'close-mobile'])

const router = useRouter()
const route = useRoute()

const collapsedGroups = ref({})

const toggleGroup = (label) => {
    collapsedGroups.value[label] = !collapsedGroups.value[label]
}

const navGroups = ref([
    {
        label: 'Tổng quan',
        items: [
            {
                path: '/dashboard',
                label: 'Dashboard',
                hint: 'Toàn cảnh khi đăng nhập',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>',
            },
        ],
    },
    {
        label: 'Giám sát & Lịch sử',
        items: [
            {
                path: '/monitoring',
                label: 'Giám sát trực tiếp',
                hint: 'Camera, biển số, access log',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>',
                badge: 'Live',
            },
            {
                path: '/access-logs',
                label: 'Tra cứu vào/ra',
                hint: 'Lịch sử theo thời gian',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="9"/></svg>',
            },
            {
                path: '/exceptions',
                label: 'Xử lý ngoại lệ',
                hint: 'Bypass và lỗi nhận diện',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
            },
        ],
    },
    {
        label: 'Quản lý Khách thăm',
        items: [
            {
                path: '/pre-registrations',
                label: 'Danh sách hẹn trước',
                hint: 'Duyệt và theo dõi đăng ký',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1.5"/><path d="M9 14l2 2 4-4"/></svg>',
            },
            {
                path: '/registration-links',
                label: 'Link đăng ký tự động',
                hint: 'Token và URL gửi khách',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>',
            },
            {
                path: '/guest-profiles',
                label: 'Hồ sơ khách',
                hint: 'Danh bạ khách quen',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M16 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="10" cy="7" r="4"/><path d="M20 8v6"/><path d="M17 11h6"/></svg>',
            },
        ],
    },
    {
        label: 'Quản trị Nội bộ',
        items: [
            {
                path: '/employees',
                label: 'Hồ sơ nhân viên',
                hint: 'Nhân sự, phòng ban, chức vụ',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
                badge: '0',
            },
            {
                path: '/vehicles',
                label: 'Phương tiện nội bộ',
                hint: 'Xe đăng ký cố định',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="1" y="5" width="16" height="11" rx="2"/><path d="M17 8h4l2 3v5h-6V8z"/><circle cx="5.5" cy="18" r="2.5"/><circle cx="18.5" cy="18" r="2.5"/></svg>',
            },
        ],
    },
    {
        label: 'AI & Thiết bị',
        items: [
            {
                path: '/device-management',
                label: 'Camera & cổng',
                hint: 'Cấu hình thiết bị truy cập',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16v10H4z"/><path d="M9 7V4h6v3"/><path d="M8 17h8"/><path d="M7 21h10"/></svg>',
            },
            {
                path: '/biometrics',
                label: 'Dữ liệu nhận diện',
                hint: 'Model và video khuôn mặt',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3H6a3 3 0 00-3 3v2"/><path d="M16 3h2a3 3 0 013 3v2"/><path d="M8 21H6a3 3 0 01-3-3v-2"/><path d="M16 21h2a3 3 0 003-3v-2"/><path d="M9 10a3 3 0 016 0v4a3 3 0 01-6 0z"/></svg>',
            },
        ],
    },
    {
        label: 'Cài đặt Hệ thống',
        items: [
            {
                path: '/users',
                label: 'Tài khoản & phân quyền',
                hint: 'Người dùng phần mềm',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
                adminOnly: true,
            },
            {
                path: '/system-catalog',
                label: 'Danh mục hệ thống',
                hint: 'Phòng ban, chức vụ, ngoại lệ',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></svg>',
                adminOnly: true,
            },
        ],
    },
])

const registryItems = ref([
    {
        path: '/employees',
        label: 'Nhân sự',
        hint: 'Danh sách và hồ sơ',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
        badge: '0',
    },
    {
        path: '/vehicles',
        label: 'Phương tiện',
        hint: 'Biển số và trạng thái',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="1" y="5" width="16" height="11" rx="2"/><path d="M17 8h4l2 3v5h-6V8z"/><circle cx="5.5" cy="18" r="2.5"/><circle cx="18.5" cy="18" r="2.5"/></svg>',
    },
    {
        path: '/FaceID',
        label: 'Face ID',
        hint: 'Nhận diện trực diện',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M8 3H6a3 3 0 00-3 3v2"/><path d="M16 3h2a3 3 0 013 3v2"/><path d="M8 21H6a3 3 0 01-3-3v-2"/><path d="M16 21h2a3 3 0 003-3v-2"/><path d="M9 10a3 3 0 016 0v4a3 3 0 01-6 0z"/></svg>',
    },
    {
        path: '/bienso',
        label: 'Nhận diện biển số',
        hint: 'Camera giao thông nội bộ',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h10"/><path d="M7 14h4"/></svg>',
    },
    {
        path: '/facevideo',
        label: 'Video khuôn mặt',
        hint: 'Đối soát theo video',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="15" height="14" rx="2"/><path d="M18 10l3-2v8l-3-2"/><path d="M8 10a2 2 0 114 0v4a2 2 0 11-4 0z"/></svg>',
    },
    {
        path: '/thonghanh',
        label: 'thonghanh',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
    {
        path: '/tao_qr_d',
        label: 'tao_qr_d',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
    {
        path: '/scan_qr_d',
        label: 'scan_qr_d',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>'
    },
])

const systemItems = [
    {
        path: '/about-project',
        label: 'Giới thiệu dự án',
        hint: 'Thông tin nền tảng',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    },
    {
        path: '/users',
        label: 'Tài khoản hệ thống',
        hint: 'Quyền truy cập',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
        adminOnly: true,
    },
    {
        path: '/departments-positions',
        label: 'Phòng ban & chức vụ',
        hint: 'Danh mục tổ chức',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 9l9-6 9 6"/><path d="M5 10v9h14v-9"/><path d="M9 19v-5h6v5"/></svg>',
        adminOnly: true,
    },
    {
        path: '/settings',
        label: 'Cài đặt',
        hint: 'Tùy chỉnh hệ thống',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
    },
]
const visibleGroups = computed(() =>
    navGroups.value
        .map((group) => ({
            ...group,
            items: group.items.filter((item) => !item.adminOnly || authState.user?.role === 'Admin'),
        }))
        .filter((group) => group.items.length > 0)
)

const passageItems = computed(() => [
    {
        path: '/thonghanh',
        label: 'Điều phối thông hành',
        hint: 'Face + biển số theo từng làn',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7h18"/><path d="M6 7v10"/><path d="M18 7v10"/><path d="M9 11h6"/><path d="M9 15h6"/><path d="M12 7v10"/></svg>',
        badge: '2 làn',
    },
    {
        path: '/scan_qr_d',
        label: 'Quét QR động',
        hint: 'Giải mã và xác thực tại cổng',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4h5v5H4z"/><path d="M15 4h5v5h-5z"/><path d="M4 15h5v5H4z"/><path d="M16 16h1"/><path d="M19 16h1"/><path d="M16 19h4"/><path d="M12 7h1"/><path d="M12 12h1"/><path d="M7 12h5"/></svg>',
    },
    {
        path: '/tao_qr_d',
        label: 'Tạo QR động',
        hint: 'Sinh mã QR realtime cho nhân viên',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/><path d="M4 14h6v6H4z"/><path d="M15 15h2"/><path d="M19 15v5"/><path d="M14 19h5"/></svg>',
    },
])

const navigationGroupCount = computed(() => visibleGroups.value.length + (passageItems.value.length ? 1 : 0))

onMounted(async () => {
    document.addEventListener('click', handleClickOutside)

    try {
        const employeesRes = await getAllEmployees()
        const employeesItem = navGroups.value
            .flatMap((group) => group.items)
            .find((item) => item.path === '/employees')
        if (employeesItem) {
            employeesItem.badge = String(employeesRes.data.length)
        }
    } catch (error) {
        console.error('Lỗi khi tải badge điều hướng:', error)
    }
})

onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
})

watch(
    () => route.fullPath,
    () => {
        showDropdown.value = false
        if (props.isMobile) {
            emit('close-mobile')
        }
    }
)

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
            const keyword = searchQuery.value.trim()
            const [employeesRes, guestsRes] = await Promise.all([
                getAllEmployees({ search: keyword }),
                getGuestProfiles({ query: keyword, page: 1, pageSize: 6 }),
            ])

            const results = []

            if (employeesRes.data?.length) {
                employeesRes.data.forEach((employee) => {
                    results.push({
                        id: `emp_${employee.employeeId}`,
                        type: 'employee',
                        name: employee.fullName,
                        sub: employee.departmentName || 'Chưa gán phòng ban',
                        badge: 'Nhân sự',
                    })
                })
            }

            if (guestsRes.data?.items?.length) {
                guestsRes.data.items.forEach((guest) => {
                    results.push({
                        id: `guest_${guest.guestId}`,
                        type: 'guest',
                        name: guest.fullName,
                        sub: guest.phone || guest.defaultLicensePlate || 'Hồ sơ khách',
                        badge: 'Khách',
                    })
                })
            }

            searchResults.value = results
            noResultsFound.value = results.length === 0
        } catch (error) {
            console.error('Search error:', error)
            searchResults.value = []
            noResultsFound.value = true
        } finally {
            isSearching.value = false
        }
    }, 320)
}

const handleResultClick = (result) => {
    if (result.type === 'employee') {
        router.push({ path: '/employees', query: { search: result.name } })
    } else if (result.type === 'guest') {
        router.push({ path: '/guest-profiles', query: { search: result.name } })
    }

    showDropdown.value = false
    searchQuery.value = ''
    searchResults.value = []

    if (props.isMobile) {
        emit('close-mobile')
    }
}

const handleClickOutside = (event) => {
    if (searchContainerRef.value && !searchContainerRef.value.contains(event.target)) {
        showDropdown.value = false
    }
}

const handleNavClick = () => {
    if (props.isMobile) {
        emit('close-mobile')
    }
}
</script>

<style scoped>
.sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    z-index: 90;
    padding: 18px 0 18px 18px;
    transition: transform var(--transition-slow), width var(--transition-slow);
}

.sidebar-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, var(--bg-sidebar) 0%, var(--bg-sidebar-raised) 100%);
    border: 1px solid var(--sidebar-border);
    border-radius: 28px;
    box-shadow: 0 30px 60px rgba(7, 16, 27, 0.34);
    overflow: hidden;
}

.sidebar.collapsed {
    width: var(--sidebar-collapsed-width);
}

.sidebar-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 22px 18px 16px;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
}

.logo-icon {
    width: 42px;
    height: 42px;
    flex-shrink: 0;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(84, 196, 211, 0.18), rgba(43, 109, 138, 0.28));
    color: #d7fbff;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 12px 28px rgba(84, 196, 211, 0.18);
}

.logo-icon svg {
    width: 26px;
    height: 26px;
}

.logo-copy {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.logo-title {
    font-family: var(--font-heading);
    font-size: 1.18rem;
    font-weight: 700;
    color: var(--sidebar-text);
    line-height: 1.1;
}

.logo-subtitle {
    color: var(--sidebar-text-muted);
    font-size: 0.78rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.sidebar-mobile-close {
    width: 40px;
    height: 40px;
    flex-shrink: 0;
    display: none;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    color: var(--sidebar-text);
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-mobile-close svg {
    width: 18px;
    height: 18px;
}

.sidebar-status {
    margin: 0 18px 18px;
    padding: 11px 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-radius: 16px;
    background: rgba(84, 196, 211, 0.08);
    border: 1px solid rgba(84, 196, 211, 0.12);
    color: var(--sidebar-text);
    font-size: 0.85rem;
}

.sidebar-status.compact {
    justify-content: center;
    padding-inline: 0;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #5de3c7;
    box-shadow: 0 0 0 6px rgba(93, 227, 199, 0.14);
    flex-shrink: 0;
}

.sidebar-nav {
    flex: 1;
    padding: 0 12px 16px;
    overflow-y: auto;
}

.sidebar-search {
    margin-bottom: 18px;
}

.search-label {
    display: block;
    margin-bottom: 10px;
    color: var(--sidebar-text-muted);
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.search-shell {
    position: relative;
}

.search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: var(--sidebar-text-muted);
}

.search-shell input {
    width: 100%;
    min-height: 46px;
    padding: 0 16px 0 40px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.05);
    color: var(--sidebar-text);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.search-shell input::placeholder {
    color: rgba(188, 209, 218, 0.64);
}

.search-shell input:focus {
    border-color: rgba(84, 196, 211, 0.38);
    background: rgba(255, 255, 255, 0.07);
    box-shadow: 0 0 0 4px rgba(84, 196, 211, 0.12);
}

.nav-group + .nav-group {
    margin-top: 18px;
}

.nav-label {
    display: block;
    padding: 0 12px 10px;
    color: var(--sidebar-text-muted);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.nav-label-toggle {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 12px 10px;
    color: var(--sidebar-text-muted);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: none;
    border: none;
    cursor: pointer;
    transition: color var(--transition-fast);
}

.nav-label-toggle:hover {
    color: var(--sidebar-text);
}

.nav-label-text {
    pointer-events: none;
}

.nav-label-chevron {
    width: 14px;
    height: 14px;
    flex-shrink: 0;
    transition: transform 0.25s ease;
}

.nav-label-chevron.chevron-collapsed {
    transform: rotate(-90deg);
}

.nav-group-items {
    max-height: 600px;
    overflow: hidden;
    transition: max-height 0.3s ease, opacity 0.25s ease;
    opacity: 1;
}

.nav-group-items.group-collapsed {
    max-height: 0;
    opacity: 0;
}

.nav-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 54px;
    margin: 4px 0;
    padding: 10px 12px;
    border-radius: 18px;
    color: var(--sidebar-text-muted);
    transition: background var(--transition-fast), border-color var(--transition-fast), transform var(--transition-fast), color var(--transition-fast);
    border: 1px solid transparent;
}

.nav-item:hover {
    transform: translateY(-1px);
    background: var(--sidebar-hover);
    color: var(--sidebar-text);
}

.nav-item.active {
    background: var(--sidebar-active);
    border-color: var(--sidebar-active-border);
    color: var(--sidebar-text);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.nav-item.active::before {
    content: '';
    position: absolute;
    left: 7px;
    top: 10px;
    bottom: 10px;
    width: 3px;
    border-radius: 999px;
    background: #8ceaf4;
}

.nav-icon {
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.nav-icon :deep(svg) {
    width: 100%;
    height: 100%;
}

.nav-copy {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.nav-text {
    color: currentColor;
    font-size: 0.92rem;
    font-weight: 600;
}

.nav-hint {
    color: rgba(188, 209, 218, 0.68);
    font-size: 0.74rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.nav-badge {
    margin-left: auto;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(84, 196, 211, 0.15);
    color: #b6f6ff;
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
}

.sidebar-footer {
    padding: 16px 12px 12px;
    border-top: 1px solid var(--sidebar-border);
}

.footer-card {
    padding: 14px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.06);
    color: var(--sidebar-text);
    margin-bottom: 12px;
}

.footer-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(84, 196, 211, 0.1);
    color: #c2f8ff;
    font-size: 0.78rem;
    font-weight: 600;
}

.chip-ping {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #5de3c7;
}

.footer-metrics {
    margin-top: 14px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.footer-metrics strong {
    display: block;
    color: var(--sidebar-text);
    font-family: var(--font-heading);
    font-size: 1rem;
    font-weight: 700;
}

.footer-metrics span {
    display: block;
    margin-top: 4px;
    color: var(--sidebar-text-muted);
    font-size: 0.74rem;
}

.sidebar-toggle {
    width: 100%;
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.05);
    color: var(--sidebar-text);
    transition: background var(--transition-fast), transform var(--transition-fast);
}

.sidebar-toggle:hover {
    background: rgba(255, 255, 255, 0.09);
    transform: translateY(-1px);
}

.sidebar-toggle svg {
    width: 18px;
    height: 18px;
    transition: transform var(--transition-slow);
}

.sidebar-toggle svg.rotated {
    transform: rotate(180deg);
}

.search-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    z-index: 10;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(11, 25, 39, 0.98);
    box-shadow: 0 18px 40px rgba(3, 8, 14, 0.45);
}

.dropdown-msg {
    padding: 14px 16px;
    color: var(--sidebar-text-muted);
    font-size: 0.84rem;
    text-align: center;
}

.dropdown-list {
    display: flex;
    flex-direction: column;
}

.dropdown-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    text-align: left;
    color: var(--sidebar-text);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: background var(--transition-fast);
}

.dropdown-item:last-child {
    border-bottom: none;
}

.dropdown-item:hover {
    background: rgba(84, 196, 211, 0.08);
}

.result-icon {
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    color: #c2f8ff;
    background: rgba(84, 196, 211, 0.12);
}

.result-icon svg {
    width: 18px;
    height: 18px;
}

.result-info {
    min-width: 0;
    flex: 1;
}

.result-name {
    color: var(--sidebar-text);
    font-size: 0.88rem;
    font-weight: 600;
}

.result-sub {
    color: var(--sidebar-text-muted);
    font-size: 0.76rem;
    margin-top: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.result-badge {
    padding: 4px 9px;
    border-radius: 999px;
    background: rgba(93, 227, 199, 0.12);
    color: #9ff4e2;
    font-size: 0.7rem;
    font-weight: 700;
}

.fade-enter-active,
.fade-leave-active,
.dropdown-enter-active,
.dropdown-leave-active {
    transition: all 0.18s ease;
}

.fade-enter-from,
.fade-leave-to,
.dropdown-enter-from,
.dropdown-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}

.sr-only {
    opacity: 0;
    pointer-events: none;
}

@media (max-width: 1023px) {
    .sidebar {
        width: min(320px, calc(100vw - 24px));
        padding: 12px;
        transform: translateX(calc(-100% - 16px));
    }

    .sidebar.mobile-open {
        transform: translateX(0);
    }

    .sidebar-mobile-close {
        display: inline-flex;
    }
}
</style>
