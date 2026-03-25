<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Registration links</span>
                <h1 class="page-title">Link đăng ký</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="showModal = true">Tạo link mới</button>
                <router-link to="/pre-registrations" class="btn btn-secondary">Xem danh sách hẹn trước</router-link>
            </div>
        </div>

        <section class="ops-panel">
            <div class="toolbar-shell">
                <div class="search-bar">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="query" type="text" placeholder="Tìm theo host hoặc token..." />
                </div>
            </div>

            <div v-if="isLoading" class="empty-card">Đang tải danh sách link đăng ký...</div>
            <div v-else-if="filteredLinks.length === 0" class="empty-card">Chưa có link đăng ký nào phù hợp.</div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Host</th>
                            <th>Token</th>
                            <th>Trạng thái</th>
                            <th>Tạo lúc</th>
                            <th>Hết hạn</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="link in filteredLinks" :key="link.linkId">
                            <td>{{ link.hostEmployeeName }}</td>
                            <td><span class="token-pill">{{ link.token }}</span></td>
                            <td>
                                <div class="chip-row">
                                    <span v-if="link.isUsed" class="soft-chip warn">Đã dùng</span>
                                    <span v-else-if="link.isExpired" class="soft-chip danger">Hết hạn</span>
                                    <span v-else class="soft-chip success">Còn hiệu lực</span>
                                </div>
                            </td>
                            <td>{{ formatDateTime(link.createdAt) }}</td>
                            <td>{{ formatDateTime(link.expiredAt) }}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" @click="copyLink(link.registrationUrl)">
                                    {{ copiedUrl === link.registrationUrl ? 'Đã copy' : 'Copy link' }}
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <transition name="modal">
            <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">Tạo link đăng ký tự động</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>

                    <div class="form-group">
                        <label>Nhân sự Host đại diện <span class="req">*</span></label>
                        <div class="combobox-wrapper" v-click-outside="closeHostDropdown">
                            <div class="input-with-avatar">
                                <div v-if="selectedHostEmployee && !showHostDropdown" class="selected-avatar-preview">
                                    <img
                                        v-if="canShowAvatar(selectedHostEmployee)"
                                        :src="getAvatarSrc(selectedHostEmployee)"
                                        class="avatar-img avatar-mini-inline"
                                        @error="markAvatarBroken(selectedHostEmployee.employeeId)"
                                    />
                                    <div
                                        v-else
                                        class="avatar mini avatar-mini-inline"
                                        :style="{ background: getAvatarColor(selectedHostEmployee.employeeId) }"
                                    >
                                        {{ getInitials(selectedHostEmployee.fullName) }}
                                    </div>
                                </div>
                                <input
                                    type="text"
                                    v-model="hostSearchQuery"
                                    @focus="showHostDropdown = true"
                                    @input="showHostDropdown = true"
                                    placeholder="-- Nhập tên để tìm nhân sự --"
                                    class="sleek-input combobox-input"
                                    :class="{ 'has-avatar': selectedHostEmployee && !showHostDropdown }"
                                />
                            </div>
                            <svg class="dropdown-icon" :class="{ rotated: showHostDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>

                            <div v-if="showHostDropdown" class="combobox-dropdown">
                                <div v-if="filteredEmployees.length === 0" class="no-results">Không tìm thấy nhân sự</div>
                                <div
                                    v-for="emp in filteredEmployees"
                                    :key="emp.employeeId"
                                    class="combobox-item"
                                    :class="{ selected: form.hostEmployeeId === emp.employeeId }"
                                    @click="selectHost(emp)"
                                >
                                    <img
                                        v-if="canShowAvatar(emp)"
                                        :src="getAvatarSrc(emp)"
                                        class="avatar-img avatar-img-mini"
                                        @error="markAvatarBroken(emp.employeeId)"
                                    />
                                    <div v-else class="avatar mini" :style="{ background: getAvatarColor(emp.employeeId) }">
                                        {{ getInitials(emp.fullName) }}
                                    </div>
                                    <div class="emp-details">
                                        <span class="emp-name">{{ emp.fullName }}</span>
                                        <span class="emp-dept">{{ emp.departmentName || 'Chưa gán phòng ban' }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Thời hạn link (giờ)</label>
                        <select v-model="form.expiryHours" class="filter-select">
                            <option :value="12">12 giờ</option>
                            <option :value="24">24 giờ</option>
                            <option :value="48">48 giờ</option>
                            <option :value="72">72 giờ</option>
                        </select>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isCreating" @click="handleCreate">
                            {{ isCreating ? 'Đang tạo...' : 'Tạo link' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { getLinks, createLink } from '../services/preRegistrationApi'
import { getAll as getAllEmployees } from '../services/employeeApi'
import { API_ORIGIN } from '../config/api'

const API_BASE = API_ORIGIN
const isLoading = ref(true)
const isCreating = ref(false)
const links = ref([])
const employees = ref([])
const query = ref('')
const showModal = ref(false)
const copiedUrl = ref('')
const formError = ref('')

// Combobox state
const showHostDropdown = ref(false)
const hostSearchQuery = ref('')
const brokenAvatarIds = ref({})

const form = reactive({
    hostEmployeeId: null,
    expiryHours: 24,
})

// Click outside directive
const vClickOutside = {
    mounted(el, binding) {
        el.clickOutsideEvent = (event) => {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event, el)
            }
        }
        document.addEventListener('click', el.clickOutsideEvent)
    },
    unmounted(el) {
        document.removeEventListener('click', el.clickOutsideEvent)
    }
}

const selectedHostEmployee = computed(() => {
    if (!form.hostEmployeeId) return null
    return employees.value.find(e => e.employeeId === form.hostEmployeeId) || null
})

const filteredEmployees = computed(() => {
    const list = employees.value || []
    if (!hostSearchQuery.value) return list
    const selected = selectedHostEmployee.value
    if (selected && hostSearchQuery.value === selected.fullName) return list
    const q = hostSearchQuery.value.toLowerCase()
    return list.filter(e => e?.fullName?.toLowerCase().includes(q) || e?.departmentName?.toLowerCase().includes(q))
})

const selectHost = (emp) => {
    form.hostEmployeeId = emp.employeeId
    hostSearchQuery.value = emp.fullName
    showHostDropdown.value = false
}

const closeHostDropdown = () => {
    showHostDropdown.value = false
    if (selectedHostEmployee.value) {
        hostSearchQuery.value = selectedHostEmployee.value.fullName
    } else {
        hostSearchQuery.value = ''
    }
}

const getInitials = (name) => {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

const avColors = ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e']
const getAvatarColor = (id) => avColors[Math.abs(id || 0) % avColors.length]

const canShowAvatar = (emp) => !!emp?.faceImageUrl && !brokenAvatarIds.value[emp.employeeId]
const getAvatarSrc = (emp) => {
    if (!emp?.faceImageUrl) return ''
    return emp.faceImageUrl.startsWith('http') ? emp.faceImageUrl : `${API_BASE}${emp.faceImageUrl}`
}
const markAvatarBroken = (id) => {
    if (!id || brokenAvatarIds.value[id]) return
    brokenAvatarIds.value = { ...brokenAvatarIds.value, [id]: true }
}

const filteredLinks = computed(() => {
    const keyword = query.value.trim().toLowerCase()
    if (!keyword) return links.value
    return links.value.filter((item) =>
        item.hostEmployeeName?.toLowerCase().includes(keyword) ||
        item.token?.toLowerCase().includes(keyword)
    )
})

const activeLinks = computed(() => links.value.filter((item) => !item.isExpired && !item.isUsed).length)
const usedLinks = computed(() => links.value.filter((item) => item.isUsed).length)
const expiredLinks = computed(() => links.value.filter((item) => item.isExpired).length)

const formatDateTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

const fetchData = async () => {
    isLoading.value = true
    try {
        const [linksRes, employeesRes] = await Promise.all([
            getLinks(),
            getAllEmployees(),
        ])
        links.value = linksRes.data || []
        employees.value = employeesRes.data || []
    } catch (error) {
        console.error('Registration links load error:', error)
        links.value = []
    } finally {
        isLoading.value = false
    }
}

const copyLink = async (url) => {
    try {
        await navigator.clipboard.writeText(url)
        copiedUrl.value = url
        setTimeout(() => {
            if (copiedUrl.value === url) copiedUrl.value = ''
        }, 1800)
    } catch (error) {
        console.error('Copy error:', error)
    }
}

const handleCreate = async () => {
    formError.value = ''
    if (!form.hostEmployeeId) {
        formError.value = 'Bạn cần chọn nhân sự host trước khi tạo link.'
        return
    }

    isCreating.value = true
    try {
        const { data } = await createLink({
            hostEmployeeId: Number(form.hostEmployeeId),
            expiryHours: Number(form.expiryHours),
        })
        await fetchData()
        await copyLink(data.registrationUrl)
        closeModal()
    } catch (error) {
        console.error('Create link error:', error)
        formError.value = error.response?.data?.message || 'Không thể tạo link đăng ký.'
    } finally {
        isCreating.value = false
    }
}

const closeModal = () => {
    showModal.value = false
    form.hostEmployeeId = null
    form.expiryHours = 24
    formError.value = ''
    hostSearchQuery.value = ''
    showHostDropdown.value = false
}

onMounted(fetchData)
</script>

<style scoped>
.token-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(236, 244, 246, 0.92);
    border: 1px solid rgba(24, 49, 77, 0.12);
    color: var(--text-primary);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
}

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

.req { color: var(--accent-danger); }

/* Combobox */
.combobox-wrapper { position: relative; width: 100%; }
.input-with-avatar { position: relative; width: 100%; display: flex; align-items: center; }
.selected-avatar-preview { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); pointer-events: none; z-index: 2; }
.avatar-mini-inline { width: 24px; height: 24px; font-size: 0.7rem; }
.combobox-input { width: 100%; padding-right: 40px; cursor: text; }
.combobox-input.has-avatar { padding-left: 52px; }
.sleek-input { width: 100%; padding: 12px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.95rem; }
.sleek-input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }

.dropdown-icon { position: absolute; right: 14px; top: 14px; width: 18px; height: 18px; color: var(--accent-primary); pointer-events: none; transition: transform 0.2s; }
.dropdown-icon.rotated { transform: rotate(180deg); }

.combobox-dropdown { position: absolute; top: calc(100% + 4px); left: 0; width: 100%; max-height: 240px; overflow-y: auto; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); z-index: 100; padding: 4px 0; }
.combobox-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; cursor: pointer; transition: background 0.2s; border-bottom: 1px solid var(--border-color); }
.combobox-item:last-child { border-bottom: none; }
.combobox-item:hover { background: rgba(16, 121, 196, 0.03); }
.combobox-item.selected { background: rgba(16, 121, 196, 0.06); }

.avatar, .avatar-img { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; object-fit: cover; flex-shrink: 0; }
.avatar.mini, .avatar-img-mini { width: 32px; height: 32px; font-size: 0.78rem; }

.emp-details { display: flex; flex-direction: column; }
.emp-name { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); }
.emp-dept { font-size: 0.85rem; color: var(--accent-primary); }
.no-results { padding: 14px; text-align: center; color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

@media (max-width: 1180px) {
    }
</style>
