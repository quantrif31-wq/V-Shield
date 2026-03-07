<template>
    <div class="page-container animate-in">
        <!-- Page Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Quản lý tài khoản</h1>
                <p class="page-subtitle">Thêm, sửa, xóa tài khoản người dùng hệ thống</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openCreateModal">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Thêm tài khoản
                </button>
            </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-icon blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 00-3-3.87" />
                        <path d="M16 3.13a4 4 0 010 7.75" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ users.length }}</h3>
                    <p>Tổng tài khoản</p>
                </div>
            </div>
            <div class="stat-card green">
                <div class="stat-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ activeCount }}</h3>
                    <p>Đang hoạt động</p>
                </div>
            </div>
            <div class="stat-card red">
                <div class="stat-icon red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="15" y1="9" x2="9" y2="15" />
                        <line x1="9" y1="9" x2="15" y2="15" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ inactiveCount }}</h3>
                    <p>Đã vô hiệu hóa</p>
                </div>
            </div>
        </div>

        <!-- Search & Filter -->
        <div class="card">
            <div class="card-header">
                <div class="filter-group">
                    <div class="search-bar">
                        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width: 16px; height: 16px;">
                            <circle cx="11" cy="11" r="8" />
                            <path d="M21 21l-4.35-4.35" />
                        </svg>
                        <input type="text" v-model="searchQuery" placeholder="Tìm kiếm tài khoản..." />
                    </div>
                    <select class="filter-select" v-model="filterRole">
                        <option value="">Tất cả vai trò</option>
                        <option value="Admin">Admin</option>
                        <option value="Staff">Staff</option>
                        <option value="BaoVe">Bảo vệ</option>
                    </select>
                    <select class="filter-select" v-model="filterStatus">
                        <option value="">Tất cả trạng thái</option>
                        <option value="active">Hoạt động</option>
                        <option value="inactive">Vô hiệu hóa</option>
                    </select>
                </div>
            </div>

            <!-- Loading -->
            <div v-if="loading" class="loading-state">
                <div class="spinner-lg"></div>
                <p>Đang tải dữ liệu...</p>
            </div>

            <!-- Error -->
            <div v-else-if="loadError" class="error-state">
                <p>{{ loadError }}</p>
                <button class="btn btn-primary btn-sm" @click="fetchUsers">Thử lại</button>
            </div>

            <!-- Table -->
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Tài khoản</th>
                            <th>Họ và tên</th>
                            <th>Vai trò</th>
                            <th>Trạng thái</th>
                            <th>Ngày tạo</th>
                            <th style="text-align: center;">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in filteredUsers" :key="user.userId">
                            <td>{{ user.userId }}</td>
                            <td>
                                <div class="avatar-group">
                                    <div class="avatar">{{ getInitials(user.fullName || user.username) }}</div>
                                    <div class="avatar-info">
                                        <span class="avatar-name">{{ user.username }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>{{ user.fullName || '—' }}</td>
                            <td>
                                <span class="badge" :class="getRoleBadgeClass(user.role)">
                                    {{ getRoleLabel(user.role) }}
                                </span>
                            </td>
                            <td>
                                <span class="badge" :class="user.isActive ? 'active' : 'inactive'">
                                    <span class="badge-dot"></span>
                                    {{ user.isActive ? 'Hoạt động' : 'Vô hiệu hóa' }}
                                </span>
                            </td>
                            <td>{{ formatDate(user.createdAt) }}</td>
                            <td>
                                <div class="action-buttons">
                                    <button class="btn-icon" title="Chỉnh sửa" @click="openEditModal(user)">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <button class="btn-icon danger" title="Xóa" @click="confirmDelete(user)">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path
                                                d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                            <line x1="10" y1="11" x2="10" y2="17" />
                                            <line x1="14" y1="11" x2="14" y2="17" />
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filteredUsers.length === 0">
                            <td colspan="7" class="empty-state">Không tìm thấy tài khoản nào</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Create/Edit Modal -->
        <transition name="modal">
            <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ isEditing ? 'Chỉnh sửa tài khoản' : 'Thêm tài khoản mới' }}</h3>
                        <button class="modal-close" @click="closeModal">✕</button>
                    </div>

                    <form @submit.prevent="handleSubmit">
                        <div class="form-group" v-if="!isEditing">
                            <label>Tên đăng nhập *</label>
                            <input v-model="modalForm.username" type="text" placeholder="Nhập tên đăng nhập"
                                required maxlength="50" />
                        </div>

                        <div class="form-group">
                            <label>{{ isEditing ? 'Mật khẩu mới (để trống nếu không đổi)' : 'Mật khẩu *' }}</label>
                            <input v-model="modalForm.password" type="password"
                                placeholder="Nhập mật khẩu (tối thiểu 6 ký tự)" :required="!isEditing"
                                minlength="6" />
                        </div>

                        <div class="form-group">
                            <label>Họ và tên</label>
                            <input v-model="modalForm.fullName" type="text" placeholder="Nhập họ và tên"
                                maxlength="100" />
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Vai trò *</label>
                                <select v-model="modalForm.role" required>
                                    <option value="Admin">Admin</option>
                                    <option value="Staff">Staff</option>
                                    <option value="BaoVe">Bảo vệ</option>
                                </select>
                            </div>
                            <div class="form-group" v-if="isEditing">
                                <label>Trạng thái</label>
                                <select v-model="modalForm.isActive">
                                    <option :value="true">Hoạt động</option>
                                    <option :value="false">Vô hiệu hóa</option>
                                </select>
                            </div>
                        </div>

                        <!-- Modal Error -->
                        <div v-if="modalError" class="login-error" style="margin-top: 0;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                style="width: 16px; height: 16px; flex-shrink: 0;">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="15" y1="9" x2="9" y2="15" />
                                <line x1="9" y1="9" x2="15" y2="15" />
                            </svg>
                            <span>{{ modalError }}</span>
                        </div>

                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" @click="closeModal">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ isEditing ? 'Cập nhật' : 'Tạo tài khoản' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Delete Confirm Modal -->
        <transition name="modal">
            <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
                <div class="modal" style="max-width: 420px;">
                    <div class="modal-header">
                        <h3 class="modal-title">Xác nhận xóa</h3>
                        <button class="modal-close" @click="showDeleteModal = false">✕</button>
                    </div>
                    <p style="color: var(--text-secondary); line-height: 1.6; margin-bottom: 8px;">
                        Bạn có chắc chắn muốn xóa tài khoản
                        <strong style="color: var(--text-primary);">{{ deleteTarget?.username }}</strong>?
                    </p>
                    <p style="color: var(--accent-danger); font-size: 0.85rem;">
                        Hành động này không thể hoàn tác.
                    </p>
                    <div v-if="modalError" class="login-error" style="margin-top: 16px;">
                        <span>{{ modalError }}</span>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="showDeleteModal = false">Hủy</button>
                        <button class="btn btn-danger" @click="handleDelete" :disabled="saving">
                            <span v-if="saving" class="spinner-sm"></span>
                            Xóa
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getAll, create, update, deleteUser } from '../services/userApi'

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
    Object.assign(modalForm, {
        username: '',
        password: '',
        fullName: '',
        role: 'Staff',
        isActive: true,
    })
    showModal.value = true
}

function openEditModal(user) {
    isEditing.value = true
    editingId.value = user.userId
    modalError.value = ''
    Object.assign(modalForm, {
        username: user.username,
        password: '',
        fullName: user.fullName || '',
        role: user.role,
        isActive: user.isActive,
    })
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
            const data = {
                fullName: modalForm.fullName || null,
                role: modalForm.role,
                isActive: modalForm.isActive,
            }
            if (modalForm.password) {
                data.password = modalForm.password
            }
            await update(editingId.value, data)
        } else {
            await create({
                username: modalForm.username,
                password: modalForm.password,
                fullName: modalForm.fullName || null,
                role: modalForm.role,
            })
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

function getRoleLabel(role) {
    const map = { Admin: 'Admin', Staff: 'Nhân viên', BaoVe: 'Bảo vệ' }
    return map[role] || role
}

function getRoleBadgeClass(role) {
    const map = { Admin: 'info', Staff: 'pending', BaoVe: 'active' }
    return map[role] || 'info'
}

function formatDate(dateStr) {
    if (!dateStr) return '—'
    return new Date(dateStr).toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

onMounted(fetchUsers)
</script>

<style scoped>
.action-buttons {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
}

.btn-icon.danger:hover {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
    border-color: var(--accent-danger);
}

.loading-state,
.error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    gap: 16px;
    color: var(--text-secondary);
}

.spinner-lg {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

.spinner-sm {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    margin-right: 6px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.empty-state {
    text-align: center;
    color: var(--text-muted);
    padding: 40px !important;
}

.login-error {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--border-radius-sm);
    color: var(--accent-danger);
    font-size: 0.85rem;
    margin-bottom: 16px;
}

/* Modal transitions */
.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}

.stat-icon svg {
    width: 24px;
    height: 24px;
}
</style>
