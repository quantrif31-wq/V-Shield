<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Quản lý Tài khoản</h1>
                <p class="page-subtitle">Thêm, sửa, xóa phân quyền tài khoản người dùng hệ thống</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openCreateModal">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Thêm tài khoản
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini" style="grid-template-columns: repeat(3, 1fr);">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val blue">{{ users.length }}</div>
                    <div class="stat-lbl">Tổng tài khoản</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val green">{{ activeCount }}</div>
                    <div class="stat-lbl">Đang hoạt động</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val red">{{ inactiveCount }}</div>
                    <div class="stat-lbl">Đã vô hiệu hóa</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                    <input type="text" v-model="searchQuery" placeholder="Tìm kiếm tài khoản..." />
                </div>
                <div class="filter-box" style="display: flex; gap: 12px;">
                    <select class="minimal-select" v-model="filterRole">
                        <option value="">Tất cả vai trò</option>
                        <option value="Admin">Admin</option>
                        <option value="Staff">Staff</option>
                        <option value="BaoVe">Bảo vệ</option>
                    </select>
                    <select class="minimal-select" v-model="filterStatus">
                        <option value="">Tất cả trạng thái</option>
                        <option value="active">Hoạt động</option>
                        <option value="inactive">Vô hiệu hóa</option>
                    </select>
                </div>
            </div>

            <!-- States -->
            <div v-if="loading" class="empty-layout">
                <div class="spinner-lg"></div>
                <p>Đang tải dữ liệu...</p>
            </div>
            <div v-else-if="loadError" class="empty-layout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--accent-danger);"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <p style="color: var(--accent-danger);">{{ loadError }}</p>
                <button class="btn btn-primary" @click="fetchUsers">Thử lại</button>
            </div>
            
            <!-- Sleek Table -->
            <div v-else class="sleek-table-container">
                <table class="sleek-table">
                    <thead>
                        <tr>
                            <th style="width: 80px;">ID</th>
                            <th>Tài khoản</th>
                            <th>Họ và tên</th>
                            <th>Vai trò</th>
                            <th>Trạng thái</th>
                            <th>Ngày tạo</th>
                            <th class="text-right">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in filteredUsers" :key="user.userId" class="table-row">
                            <td class="text-muted" style="font-family: monospace;">#{{ user.userId }}</td>
                            <td>
                                <div class="user-cell">
                                    <div class="avatar" :style="{ background: getAvatarColor(getInitials(user.fullName || user.username)) }">{{ getInitials(user.fullName || user.username) }}</div>
                                    <div class="user-info">
                                        <span class="user-name">{{ user.username }}</span>
                                    </div>
                                </div>
                            </td>
                            <td><span class="text-primary" style="font-weight: 500;">{{ user.fullName || '—' }}</span></td>
                            <td>
                                <span class="badge-role" :class="getRoleBadgeClass(user.role)">
                                    {{ getRoleLabel(user.role) }}
                                </span>
                            </td>
                            <td>
                                <span class="status-pill minimal" :class="user.isActive ? 'active' : 'inactive'">
                                    <span class="pill-dot"></span>
                                    {{ user.isActive ? 'Hoạt động' : 'Vô hiệu hóa' }}
                                </span>
                            </td>
                            <td class="text-muted" style="font-size: 0.85rem;">{{ formatDate(user.createdAt) }}</td>
                            <td class="text-right">
                                <div class="action-menu">
                                    <button class="icon-btn" title="Chỉnh sửa" @click="openEditModal(user)">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                                    </button>
                                    <button class="icon-btn action-reject" title="Xóa" @click="confirmDelete(user)">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filteredUsers.length === 0">
                            <td colspan="7" class="empty-layout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--text-muted);"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
                                <p>Không tìm thấy tài khoản nào khớp với bộ lọc</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Modern Modal for Create/Edit -->
        <transition name="modal">
            <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
                <div class="modern-modal" style="max-width: 500px;">
                    <div class="modal-top">
                        <h3>{{ isEditing ? 'Cập nhật Tài khoản' : 'Thêm Tài khoản Mới' }}</h3>
                        <button class="icon-close" @click="closeModal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>

                    <div class="modal-body">
                        <form @submit.prevent="handleSubmit" class="modal-form-grid">
                            <div class="input-pane" v-if="!isEditing">
                                <label>Tên đăng nhập <span class="req">*</span></label>
                                <input v-model="modalForm.username" type="text" class="sleek-input" placeholder="Nhập tên đăng nhập" required maxlength="50" />
                            </div>

                            <div class="input-pane">
                                <label>{{ isEditing ? 'Mật khẩu mới' : 'Mật khẩu' }} <span v-if="!isEditing" class="req">*</span></label>
                                <input v-model="modalForm.password" type="password" class="sleek-input" :placeholder="isEditing ? 'Để trống nếu không đổi' : 'Tối thiểu 6 ký tự'" :required="!isEditing" minlength="6" />
                            </div>

                            <div class="input-pane">
                                <label>Họ và tên</label>
                                <input v-model="modalForm.fullName" list="employee-names" type="text" class="sleek-input" placeholder="Ví dụ: Nguyễn Văn A" maxlength="100" autocomplete="off" />
                                <datalist id="employee-names">
                                    <option v-for="emp in employees" :key="emp.employeeId" :value="emp.fullName">
                                        {{ emp.fullName }} - {{ emp.departmentName || 'Chưa có PB' }}
                                    </option>
                                </datalist>
                            </div>

                            <div class="grid-2">
                                <div class="input-pane">
                                    <label>Vai trò <span class="req">*</span></label>
                                    <select v-model="modalForm.role" class="sleek-select" required>
                                        <option value="Admin">Admin</option>
                                        <option value="Staff">Nhân viên (Staff)</option>
                                        <option value="BaoVe">Bảo vệ</option>
                                    </select>
                                </div>
                                <div class="input-pane" v-if="isEditing">
                                    <label>Trạng thái</label>
                                    <select v-model="modalForm.isActive" class="sleek-select">
                                        <option :value="true">Đang hoạt động</option>
                                        <option :value="false">Vô hiệu hóa</option>
                                    </select>
                                </div>
                            </div>

                            <!-- Form Error -->
                            <div v-if="modalError" class="error-box">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                                <span>{{ modalError }}</span>
                            </div>

                            <div class="modal-actions mt-4">
                                <button type="button" class="btn btn-secondary" @click="closeModal">Hủy</button>
                                <button type="submit" class="btn btn-primary" :disabled="saving">
                                    <span v-if="saving" class="spinner-sm"></span>
                                    {{ isEditing ? 'Lưu cập nhật' : 'Khởi tạo' }}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </transition>

        <!-- Modern Warning Modal for Delete -->
        <transition name="modal">
            <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
                <div class="modern-modal mini">
                    <div class="modal-body text-center" style="padding: 32px 24px;">
                        <div class="warning-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
                        <h3 style="margin: 0 0 10px 0;">Xóa tài khoản này?</h3>
                        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 24px;">
                            Tài khoản <strong style="color: var(--text-primary);">{{ deleteTarget?.username }}</strong> sẽ bị xóa vĩnh viễn khỏi hệ thống.
                        </p>
                        
                        <div v-if="modalError" class="error-box text-left" style="margin-bottom: 20px;">
                            <span>{{ modalError }}</span>
                        </div>

                        <div class="modal-actions centered">
                            <button class="btn btn-secondary" @click="showDeleteModal = false">Hủy</button>
                            <button class="btn btn-danger" @click="handleDelete" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span> Xóa
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getAll, create, update, deleteUser } from '../services/userApi'
import { getAll as getAllEmployees } from '../services/employeeApi'

const employees = ref([])

const users = ref([])
const loading = ref(true)
const loadError = ref('')
const searchQuery = ref('')
const filterRole = ref('')
const filterStatus = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const saving = ref(false)
const modalError = ref('')

const modalForm = reactive({
    username: '',
    password: '',
    fullName: '',
    role: 'Staff',
    isActive: true,
})

// Delete modal
const showDeleteModal = ref(false)
const deleteTarget = ref(null)

// Computed
const activeCount = computed(() => users.value.filter(u => u.isActive).length)
const inactiveCount = computed(() => users.value.filter(u => !u.isActive).length)

const filteredUsers = computed(() => {
    return users.value.filter(u => {
        const matchSearch = !searchQuery.value ||
            u.username.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
            (u.fullName && u.fullName.toLowerCase().includes(searchQuery.value.toLowerCase()))
        const matchRole = !filterRole.value || u.role === filterRole.value
        const matchStatus = !filterStatus.value ||
            (filterStatus.value === 'active' && u.isActive) ||
            (filterStatus.value === 'inactive' && !u.isActive)
        return matchSearch && matchRole && matchStatus
    })
})

// Fetch users
async function fetchUsers() {
    loading.value = true
    loadError.value = ''
    try {
        const res = await getAll()
        users.value = res.data
    } catch (err) {
        if (err.code === 'ERR_NETWORK') {
            loadError.value = 'Không thể kết nối đến server'
        } else {
            loadError.value = 'Không thể tải danh sách tài khoản'
        }
    } finally {
        loading.value = false
    }
}

// Modal handlers
function openCreateModal() {
    isEditing.value = false
    editingId.value = null
    modalError.value = ''
    Object.assign(modalForm, { username: '', password: '', fullName: '', role: 'Staff', isActive: true })
    showModal.value = true
}

function openEditModal(user) {
    isEditing.value = true
    editingId.value = user.userId
    modalError.value = ''
    Object.assign(modalForm, { username: user.username, password: '', fullName: user.fullName || '', role: user.role, isActive: user.isActive })
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    modalError.value = ''
}

async function handleSubmit() {
    saving.value = true
    modalError.value = ''
    try {
        if (isEditing.value) {
            const data = { fullName: modalForm.fullName || null, role: modalForm.role, isActive: modalForm.isActive }
            if (modalForm.password) data.password = modalForm.password
            await update(editingId.value, data)
        } else {
            await create({ username: modalForm.username, password: modalForm.password, fullName: modalForm.fullName || null, role: modalForm.role })
        }
        closeModal()
        await fetchUsers()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Đã xảy ra lỗi, vui lòng thử lại'
    } finally {
        saving.value = false
    }
}

// Delete handlers
function confirmDelete(user) {
    deleteTarget.value = user
    modalError.value = ''
    showDeleteModal.value = true
}

async function handleDelete() {
    saving.value = true
    modalError.value = ''
    try {
        await deleteUser(deleteTarget.value.userId)
        showDeleteModal.value = false
        await fetchUsers()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Không thể xóa tài khoản'
    } finally {
        saving.value = false
    }
}

// Helpers
function getInitials(name) {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

const getAvatarColor = (str) => {
    let hash = 0; for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const avColors = [ '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e' ];
    return avColors[Math.abs(hash) % avColors.length];
}

function getRoleLabel(role) {
    const map = { Admin: 'Admin', Staff: 'Nhân viên', BaoVe: 'Bảo vệ' }
    return map[role] || role
}

function getRoleBadgeClass(role) {
    const map = { Admin: 'admin', Staff: 'staff', BaoVe: 'guard' }
    return map[role] || 'staff'
}

function formatDate(dateStr) {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

async function fetchEmployees() {
    try {
        const res = await getAllEmployees()
        employees.value = res.data
    } catch (err) {
        console.error('Lỗi tải danh sách nhân viên:', err)
    }
}

onMounted(() => {
    fetchUsers()
    fetchEmployees()
})
</script>

<style scoped>
/* Common Page Layout */
.bento-header { margin-bottom: 24px; padding: 0 4px; display: flex; justify-content: space-between; align-items: center; }
.bento-header .greeting h1 { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
.bento-header .greeting p { color: var(--text-secondary); font-size: 0.95rem; }

/* Grid Mini */
.bento-grid-mini { display: grid; gap: 20px; margin-bottom: 24px; }
.bento-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--border-radius-lg); padding: 24px; }
.stat-card { display: flex; align-items: center; gap: 16px; transition: transform var(--transition-normal); }
.stat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.stat-icon-wrapper { width: 56px; height: 56px; border-radius: 14px; display: flex; justify-content: center; align-items: center; }
.stat-icon-wrapper svg { width: 28px; height: 28px; }
.stat-icon-wrapper.blue { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.stat-icon-wrapper.green { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.stat-icon-wrapper.red { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }
.stat-val { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-val.blue { color: var(--accent-primary); }
.stat-val.green { color: var(--accent-success); }
.stat-val.red { color: var(--accent-danger); }
.stat-lbl { font-size: 0.9rem; color: var(--text-muted); font-weight: 500;}

/* Table Box */
.table-section { padding: 0; overflow: hidden; display: flex; flex-direction: column; min-height: 500px; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border-color); }
.search-box { position: relative; width: 320px; display: flex; align-items: center; }
.search-icon { position: absolute; left: 14px; color: var(--text-muted); width: 18px; }
.search-box input { width: 100%; padding: 10px 14px 10px 42px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; }
.search-box input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 2px rgba(16, 121, 196, 0.2); }
.minimal-select { padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); cursor: pointer; outline: none; }

/* Table Elements */
.sleek-table-container { flex: 1; overflow-x: auto; }
.sleek-table { width: 100%; border-collapse: collapse; text-align: left; }
.sleek-table th { padding: 16px 24px; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); background: rgba(0,0,0,0.1); }
.sleek-table td { padding: 18px 24px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }
.table-row { transition: background var(--transition-fast); }
.table-row:hover { background: var(--bg-card-hover); cursor: default; }

.user-cell { display: flex; align-items: center; gap: 14px; }
.avatar, .avatar-img { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; font-size: 0.8rem; object-fit: cover; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); }
.text-primary { color: var(--text-primary); }
.text-muted { color: var(--text-muted); }

.badge-role { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px; border: 1px solid transparent; }
.badge-role.admin { background: rgba(168, 85, 247, 0.1); color: #a855f7; border-color: rgba(168, 85, 247, 0.2); }
.badge-role.staff { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); border-color: rgba(16, 121, 196, 0.2); }
.badge-role.guard { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }

.status-pill.minimal { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid transparent; letter-spacing: 0.5px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600;}
.status-pill.active { background: rgba(16, 185, 129, 0.05); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }
.status-pill.inactive { background: rgba(239, 68, 68, 0.05); color: var(--accent-danger); border-color: rgba(239, 68, 68, 0.2); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-menu { display: flex; gap: 8px; justify-content: flex-end; }
.icon-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.icon-btn svg { width: 18px; }
.icon-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.icon-btn.action-reject:hover { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

/* Spinners & Empties */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }
.spinner-lg { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Modern Modals */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 20px;}
.modern-modal { background: var(--bg-card); width: 100%; max-width: 500px; border-radius: var(--border-radius-lg); border: 1px solid var(--border-color); box-shadow: var(--shadow-xl); overflow: hidden; display: flex; flex-direction: column;}
.modern-modal.mini { max-width: 400px; }
.modal-top { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border-color); }
.modal-top h3 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;}
.icon-close { background: none; border: none; color: var(--text-muted); cursor: pointer; width: 24px; transition: color 0.2s; }
.icon-close:hover { color: var(--accent-danger); }

.modal-body { padding: 24px; display: flex; flex-direction: column; }
.modal-form-grid { display: flex; flex-direction: column; gap: 20px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }
.req { color: var(--accent-danger); }

.sleek-input, .sleek-select { width: 100%; padding: 12px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.95rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }

.error-box { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; color: var(--accent-danger); font-size: 0.85rem; margin-top: 10px; }
.error-box svg { width: 18px; height: 18px; flex-shrink: 0; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; }
.modal-actions.centered { justify-content: center; }
.warning-icon svg { width: 48px; height: 48px; color: var(--accent-danger); margin-bottom: 16px; }

.text-right { text-align: right; }
.text-center { text-align: center; }
.text-left { text-align: left; }
.mt-4 { margin-top: 24px; }

.modal-enter-active, .modal-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }

@media (max-width: 1200px) { .bento-grid-mini { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
    .bento-grid-mini { grid-template-columns: 1fr; }
    .grid-2 { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
}
</style>
