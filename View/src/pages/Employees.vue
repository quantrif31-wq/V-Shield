<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Quản lý Nhân viên</h1>
                <p class="page-subtitle">Quản lý thông tin nhân viên và quyền ra/vào</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openCreateModal">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Thêm nhân viên
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
                    <h3>{{ employees.length }}</h3>
                    <p>Tổng nhân viên</p>
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
                    <p>Ngừng hoạt động</p>
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="card">
            <div class="card-header">
                <div class="filter-group">
                    <div class="search-bar" style="max-width: 300px;">
                        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width: 18px; height: 18px;">
                            <circle cx="11" cy="11" r="8" />
                            <path d="M21 21l-4.35-4.35" />
                        </svg>
                        <input v-model="searchQuery" type="text" placeholder="Tìm nhân viên..."
                            @input="debouncedFetch" />
                    </div>
                    <select v-model="filterStatus" class="filter-select" @change="fetchEmployees">
                        <option value="">Tất cả trạng thái</option>
                        <option value="true">Đang hoạt động</option>
                        <option value="false">Ngừng hoạt động</option>
                    </select>
                    <div style="margin-left: auto; color: var(--text-secondary); font-size: 0.85rem;">
                        {{ employees.length }} nhân viên
                    </div>
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
                <button class="btn btn-primary btn-sm" @click="fetchEmployees">Thử lại</button>
            </div>

            <!-- Table -->
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Nhân viên</th>
                            <th>SĐT</th>
                            <th>Email</th>
                            <th>Phòng ban</th>
                            <th>Chức vụ</th>
                            <th>Trạng thái</th>
                            <th style="width: 140px; text-align: center;">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="emp in employees" :key="emp.employeeId">
                            <td>
                                <div class="avatar-group">
                                    <div class="avatar" v-if="!emp.faceImageUrl"
                                        :style="{ background: getAvatarColor(emp.employeeId) }">
                                        {{ getInitials(emp.fullName) }}
                                    </div>
                                    <img v-else :src="API_BASE + emp.faceImageUrl" class="avatar-img"
                                        @error="$event.target.style.display = 'none'" />
                                    <div class="avatar-info">
                                        <span class="avatar-name">{{ emp.fullName }}</span>
                                        <span class="avatar-sub">ID: {{ emp.employeeId }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>{{ emp.phone || '—' }}</td>
                            <td>{{ emp.email || '—' }}</td>
                            <td>{{ emp.departmentName || '—' }}</td>
                            <td>{{ emp.positionName || '—' }}</td>
                            <td>
                                <span class="badge" :class="emp.status ? 'active' : 'inactive'">
                                    <span class="badge-dot"></span>
                                    {{ emp.status ? 'Hoạt động' : 'Ngừng' }}
                                </span>
                            </td>
                            <td>
                                <div class="action-buttons">
                                    <button class="btn-icon" @click="openEditModal(emp)" title="Chỉnh sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <label class="btn-icon" :title="'Upload ảnh'" style="cursor: pointer;">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                            <circle cx="8.5" cy="8.5" r="1.5" />
                                            <polyline points="21 15 16 10 5 21" />
                                        </svg>
                                        <input type="file" accept="image/*" hidden
                                            @change="handleFaceUpload(emp.employeeId, $event)" />
                                    </label>
                                    <button class="btn-icon danger" @click="confirmDelete(emp)" title="Xóa">
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
                        <tr v-if="employees.length === 0">
                            <td colspan="7" class="empty-state">Không tìm thấy nhân viên nào</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Toast notification -->
        <transition name="toast">
            <div v-if="toast" class="toast" :class="toast.type">
                {{ toast.message }}
            </div>
        </transition>

        <!-- Create/Edit Modal -->
        <transition name="modal">
            <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ isEditing ? 'Chỉnh sửa nhân viên' : 'Thêm nhân viên mới' }}</h3>
                        <button class="modal-close" @click="closeModal">✕</button>
                    </div>

                    <form @submit.prevent="handleSubmit">
                        <div class="form-group">
                            <label>Họ và tên *</label>
                            <input v-model="modalForm.fullName" type="text" placeholder="Nhập họ tên" required
                                maxlength="150" />
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Email</label>
                                <input v-model="modalForm.email" type="email" placeholder="email@company.com"
                                    maxlength="100" />
                            </div>
                            <div class="form-group">
                                <label>Số điện thoại</label>
                                <input v-model="modalForm.phone" type="text" placeholder="0912 345 678"
                                    maxlength="20" />
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Phòng ban</label>
                                <select v-model="modalForm.departmentId">
                                    <option :value="null">Chọn phòng ban</option>
                                    <option v-for="dept in departments" :key="dept.departmentId"
                                        :value="dept.departmentId">{{ dept.name }}</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Chức vụ</label>
                                <select v-model="modalForm.positionId">
                                    <option :value="null">Chọn chức vụ</option>
                                    <option v-for="pos in positions" :key="pos.positionId" :value="pos.positionId">{{
                                        pos.name }}</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-group" v-if="isEditing">
                            <label>Trạng thái</label>
                            <select v-model="modalForm.status">
                                <option :value="true">Đang hoạt động</option>
                                <option :value="false">Ngừng hoạt động</option>
                            </select>
                        </div>

                        <!-- Face Image Upload -->
                        <div class="form-group">
                            <label>Ảnh khuôn mặt</label>
                            <div class="face-upload-area" @click="$refs.faceInput.click()" @dragover.prevent
                                @drop.prevent="handleDrop">
                                <img v-if="facePreview" :src="facePreview" class="face-preview" />
                                <div v-else class="face-placeholder">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                                        style="width: 32px; height: 32px; color: var(--text-muted);">
                                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                                        <circle cx="8.5" cy="8.5" r="1.5" />
                                        <polyline points="21 15 16 10 5 21" />
                                    </svg>
                                    <span>Click hoặc kéo thả ảnh vào đây</span>
                                    <span style="font-size: 0.75rem; color: var(--text-muted);">JPG, PNG, WebP — tối đa
                                        5MB</span>
                                </div>
                            </div>
                            <input ref="faceInput" type="file" accept="image/jpeg,image/png,image/webp" hidden
                                @change="handleFaceSelect" />
                            <button v-if="facePreview" type="button" class="btn-remove-face" @click.stop="removeFace">
                                ✕ Xóa ảnh
                            </button>
                        </div>

                        <!-- Modal Error -->
                        <div v-if="modalError" class="form-error">
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
                                {{ isEditing ? 'Lưu thay đổi' : 'Thêm nhân viên' }}
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
                        Bạn có chắc chắn muốn xóa nhân viên
                        <strong style="color: var(--text-primary);">{{ deleteTarget?.fullName }}</strong>?
                    </p>
                    <p style="color: var(--accent-danger); font-size: 0.85rem;">
                        Hành động này không thể hoàn tác.
                    </p>
                    <div v-if="modalError" class="form-error" style="margin-top: 16px;">
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
import { getAll, create, update, deleteEmployee, uploadFace } from '../services/employeeApi'
import { getDepartments, getPositions } from '../services/lookupApi'

const API_BASE = 'http://localhost:5107'

const employees = ref([])
const departments = ref([])
const positions = ref([])
const loading = ref(true)
const loadError = ref('')
const searchQuery = ref('')
const filterStatus = ref('')

// Modal state
const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const saving = ref(false)
const modalError = ref('')

const modalForm = reactive({
    fullName: '',
    phone: '',
    email: '',
    departmentId: null,
    positionId: null,
    status: true,
})

// Face upload in modal
const faceFile = ref(null)
const facePreview = ref(null)

// Delete modal
const showDeleteModal = ref(false)
const deleteTarget = ref(null)

// Toast
const toast = ref(null)
let toastTimer = null

function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { message, type }
    toastTimer = setTimeout(() => { toast.value = null }, 3000)
}

// Computed
const activeCount = computed(() => employees.value.filter(e => e.status).length)
const inactiveCount = computed(() => employees.value.filter(e => !e.status).length)

// Debounce search
let searchTimer = null
function debouncedFetch() {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => fetchEmployees(), 400)
}

// Fetch employees
async function fetchEmployees() {
    loading.value = true
    loadError.value = ''
    try {
        const params = {}
        if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
        if (filterStatus.value !== '') params.status = filterStatus.value === 'true'
        const res = await getAll(params)
        employees.value = res.data
    } catch (err) {
        if (err.code === 'ERR_NETWORK') {
            loadError.value = 'Không thể kết nối đến server'
        } else {
            loadError.value = 'Không thể tải danh sách nhân viên'
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
    faceFile.value = null
    facePreview.value = null
    Object.assign(modalForm, {
        fullName: '',
        phone: '',
        email: '',
        departmentId: null,
        positionId: null,
        status: true,
    })
    showModal.value = true
}

function openEditModal(emp) {
    isEditing.value = true
    editingId.value = emp.employeeId
    modalError.value = ''
    faceFile.value = null
    facePreview.value = emp.faceImageUrl ? (API_BASE + emp.faceImageUrl) : null
    Object.assign(modalForm, {
        fullName: emp.fullName,
        phone: emp.phone || '',
        email: emp.email || '',
        departmentId: emp.departmentId || null,
        positionId: emp.positionId || null,
        status: emp.status ?? true,
    })
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    modalError.value = ''
    faceFile.value = null
    facePreview.value = null
}

async function handleSubmit() {
    saving.value = true
    modalError.value = ''
    try {
        const data = {
            fullName: modalForm.fullName,
            phone: modalForm.phone || null,
            email: modalForm.email || null,
            departmentId: modalForm.departmentId || null,
            positionId: modalForm.positionId || null,
        }

        let employeeId = editingId.value

        if (isEditing.value) {
            data.status = modalForm.status
            await update(editingId.value, data)
        } else {
            data.status = true
            const res = await create(data)
            employeeId = res.data.employeeId
        }

        // Upload ảnh khuôn mặt nếu có chọn file mới
        if (faceFile.value && employeeId) {
            await uploadFace(employeeId, faceFile.value)
        }

        showToast(isEditing.value ? 'Cập nhật nhân viên thành công' : 'Thêm nhân viên thành công')
        closeModal()
        await fetchEmployees()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Đã xảy ra lỗi, vui lòng thử lại'
    } finally {
        saving.value = false
    }
}

// Face select in modal
function handleFaceSelect(event) {
    const file = event.target.files[0]
    if (!file) return
    event.target.value = ''
    faceFile.value = file
    facePreview.value = URL.createObjectURL(file)
}

function handleDrop(event) {
    const file = event.dataTransfer.files[0]
    if (file && file.type.startsWith('image/')) {
        faceFile.value = file
        facePreview.value = URL.createObjectURL(file)
    }
}

function removeFace() {
    faceFile.value = null
    facePreview.value = null
}

// Face upload from table row
async function handleFaceUpload(employeeId, event) {
    const file = event.target.files[0]
    if (!file) return
    event.target.value = '' // reset input
    try {
        await uploadFace(employeeId, file)
        showToast('Upload ảnh khuôn mặt thành công')
        await fetchEmployees()
    } catch (err) {
        showToast(err.response?.data?.message || 'Upload ảnh thất bại', 'error')
    }
}

// Delete handlers
function confirmDelete(emp) {
    deleteTarget.value = emp
    modalError.value = ''
    showDeleteModal.value = true
}

async function handleDelete() {
    saving.value = true
    modalError.value = ''
    try {
        await deleteEmployee(deleteTarget.value.employeeId)
        showDeleteModal.value = false
        showToast('Xóa nhân viên thành công')
        await fetchEmployees()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Không thể xóa nhân viên'
    } finally {
        saving.value = false
    }
}

// Helpers
function getInitials(name) {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

const avatarColors = [
    'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    'linear-gradient(135deg, #ec4899, #f43f5e)',
    'linear-gradient(135deg, #10b981, #06b6d4)',
    'linear-gradient(135deg, #f59e0b, #ef4444)',
    'linear-gradient(135deg, #8b5cf6, #3b82f6)',
    'linear-gradient(135deg, #06b6d4, #3b82f6)',
    'linear-gradient(135deg, #f43f5e, #f59e0b)',
    'linear-gradient(135deg, #10b981, #8b5cf6)',
]

function getAvatarColor(id) {
    return avatarColors[id % avatarColors.length]
}

onMounted(async () => {
    // Load lookup data + employees in parallel
    try {
        const [deptRes, posRes] = await Promise.all([
            getDepartments(),
            getPositions(),
        ])
        departments.value = deptRes.data
        positions.value = posRes.data
    } catch (e) {
        console.warn('Could not load lookup data:', e)
    }
    fetchEmployees()
})
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

.avatar-img {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid var(--border-color);
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
    to {
        transform: rotate(360deg);
    }
}

.empty-state {
    text-align: center;
    color: var(--text-muted);
    padding: 40px !important;
}

/* Face upload in modal */
.face-upload-area {
    border: 2px dashed var(--border-color);
    border-radius: var(--border-radius-sm);
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-fast);
    background: var(--bg-input);
    min-height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.face-upload-area:hover {
    border-color: var(--accent-primary);
    background: rgba(59, 130, 246, 0.05);
}

.face-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.face-preview {
    max-width: 150px;
    max-height: 150px;
    border-radius: var(--border-radius-sm);
    object-fit: cover;
    border: 2px solid var(--border-color);
}

.btn-remove-face {
    display: block;
    margin-top: 8px;
    background: none;
    color: var(--accent-danger);
    font-size: 0.8rem;
    cursor: pointer;
    padding: 4px 0;
    transition: opacity var(--transition-fast);
}

.btn-remove-face:hover {
    opacity: 0.7;
}

.form-error {
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

/* Toast */
.toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 14px 24px;
    border-radius: var(--border-radius-sm);
    font-size: 0.9rem;
    font-weight: 500;
    z-index: 9999;
    box-shadow: var(--shadow-lg);
}

.toast.success {
    background: var(--accent-success);
    color: #fff;
}

.toast.error {
    background: var(--accent-danger);
    color: #fff;
}

.toast-enter-active,
.toast-leave-active {
    transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
    opacity: 0;
    transform: translateY(16px);
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
