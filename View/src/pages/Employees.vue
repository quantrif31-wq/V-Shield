<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Quản lý Nhân sự</h1>
                <p class="page-subtitle">Danh sách nhân viên, thông tin và quyền hạn</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openCreateModal">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Thêm nhân viên
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val">{{ employees.length }}</div>
                    <div class="stat-lbl">Tổng số</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val green">{{ activeCount }}</div>
                    <div class="stat-lbl">Hoạt động</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val red">{{ inactiveCount }}</div>
                    <div class="stat-lbl">Ngừng HĐ</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm kiếm tên, SĐT, Email..." @input="debouncedFetch" />
                </div>
                <div class="filter-box">
                    <select v-model="filterStatus" class="minimal-select" @change="fetchEmployees">
                        <option value="">Tất cả trạng thái</option>
                        <option value="true">Đang hoạt động</option>
                        <option value="false">Ngừng hoạt động</option>
                    </select>
                </div>
            </div>

            <!-- States -->
            <div v-if="loading" class="empty-layout">
                <div class="spinner-lg"></div>
                <p>Đang tải hệ thống...</p>
            </div>
            <div v-else-if="loadError" class="empty-layout error-layout">
                <p>{{ loadError }}</p>
                <button class="btn btn-primary" @click="fetchEmployees">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                        <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                    </svg>
                    Thử lại
                </button>
            </div>
            
            <!-- Sleek Table -->
            <div v-else class="sleek-table-container">
                <table class="sleek-table">
                    <thead>
                        <tr>
                            <th>Nhân viên</th>
                            <th>Liên hệ</th>
                            <th>Phòng ban / Chức vụ</th>
                            <th>Trạng thái</th>
                            <th class="text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="emp in employees" :key="emp.employeeId" class="table-row">
                            <td>
                                <div class="user-cell">
                                    <div class="avatar" v-if="!emp.faceImageUrl" :style="{ background: getAvatarColor(emp.employeeId) }">
                                        {{ getInitials(emp.fullName) }}
                                    </div>
                                    <img v-else :src="emp.faceImageUrl?.startsWith('http') ? emp.faceImageUrl : API_BASE + emp.faceImageUrl" class="avatar-img" @error="$event.target.style.display = 'none'" />
                                    <div class="user-info">
                                        <span class="user-name">{{ emp.fullName }}</span>
                                        <span class="user-id">ID: {{ emp.employeeId }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="contact-cell">
                                    <span class="contact-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>{{ emp.phone || '—' }}</span>
                                    <span class="contact-item"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>{{ emp.email || '—' }}</span>
                                </div>
                            </td>
                            <td>
                                <div class="role-cell">
                                    <span class="dept">{{ emp.departmentName || 'Chưa xếp phòng' }}</span>
                                    <span class="pos">{{ emp.positionName || '—' }}</span>
                                </div>
                            </td>
                            <td>
                                <span class="status-pill" :class="emp.status ? 'active' : 'inactive'">
                                    <span class="pill-dot"></span>
                                    {{ emp.status ? 'Hoạt động' : 'Đã khóa' }}
                                </span>
                            </td>
                            <td class="text-right">
                                <div class="action-menu">
                                    <button class="icon-btn" @click="openEditModal(emp)" title="Sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                                    </button>
                                    <label class="icon-btn" title="Cập nhật FaceID" style="cursor: pointer;">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>
                                        <input type="file" accept="image/*" hidden @change="handleFaceUpload(emp.employeeId, $event)" />
                                    </label>
                                    <button class="icon-btn danger" @click="confirmDelete(emp)" title="Xóa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="employees.length === 0">
                            <td colspan="5" class="empty-state">Không có nhân viên nào phù hợp</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Create/Edit Modal Override -->
        <transition name="modal">
            <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
                <div class="modern-modal">
                    <div class="modal-top">
                        <h3>{{ isEditing ? 'Cập nhật Thông tin' : 'Thêm Nhân sự' }}</h3>
                        <button class="icon-close" @click="closeModal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>
                    
                    <form @submit.prevent="handleSubmit" class="modal-body">
                        <div class="input-pane">
                            <label>Họ và tên <span class="req">*</span></label>
                            <input v-model="modalForm.fullName" type="text" class="sleek-input" required placeholder="VD: Nguyễn Văn An"
                                @input="runNameValidation"
                                @blur="empNameValidation.touched = true; runNameValidation()"
                                :class="{ 'input-error': empNameValidation.touched && !empNameValidation.isValid && modalForm.fullName.length >= 2, 'input-success': empNameValidation.isValid }" />
                            <div v-if="empNameValidation.touched && modalForm.fullName.length >= 2" class="name-feedback">
                                <span v-if="empNameValidation.isValid" class="feedback-success">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                                    Hợp lệ
                                </span>
                                <span v-else class="feedback-error">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                                    {{ empNameValidation.error }}
                                </span>
                            </div>
                        </div>
                        <div class="grid-2">
                            <div class="input-pane">
                                <label>Điện thoại</label>
                                <input v-model="modalForm.phone" type="tel" class="sleek-input" placeholder="09xx xxx xxx" />
                            </div>
                            <div class="input-pane">
                                <label>Email</label>
                                <input v-model="modalForm.email" type="email" class="sleek-input" placeholder="mail@example.com" />
                            </div>
                        </div>
                        <div class="grid-2">
                            <div class="input-pane">
                                <label>Phòng ban</label>
                                <select v-model="modalForm.departmentId" class="sleek-select">
                                    <option :value="null">-- Chọn phòng ban --</option>
                                    <option v-for="d in departments" :key="d.departmentId" :value="d.departmentId">{{d.name}}</option>
                                </select>
                            </div>
                            <div class="input-pane">
                                <label>Chức vụ</label>
                                <select v-model="modalForm.positionId" class="sleek-select">
                                    <option :value="null">-- Chọn chức vụ --</option>
                                    <option v-for="p in positions" :key="p.positionId" :value="p.positionId">{{p.name}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="input-pane" v-if="isEditing">
                            <label>Trạng thái truy cập</label>
                            <select v-model="modalForm.status" class="sleek-select">
                                <option :value="true">Hoạt động bình thường</option>
                                <option :value="false">Khóa truy cập</option>
                            </select>
                        </div>
                        
                        <!-- Face Upload -->
<div class="input-pane">
    <label>Dữ liệu nhận diện (Face ID)</label>
    
    <!-- Tab switcher -->
    <div class="face-tab-switcher">
        <button type="button" 
            class="face-tab" :class="{ active: faceInputMode === 'upload' }"
            @click="switchFaceMode('upload')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4-4 4 4"/></svg>
            Tải ảnh lên
        </button>
        <button type="button" 
            class="face-tab" :class="{ active: faceInputMode === 'url' }"
            @click="switchFaceMode('url')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            Dùng URL
        </button>
    </div>

    <!-- Upload mode -->
    <template v-if="faceInputMode === 'upload'">
        <div class="face-dropzone" @click="$refs.faceInput.click()" @dragover.prevent @drop.prevent="handleDrop">
            <img v-if="facePreview && !faceUrlInput" :src="facePreview" class="face-preview-img" />
            <div v-else class="dropzone-text">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m8 17 4-4 4 4"/></svg>
                <span>Tải ảnh khuôn mặt lên</span>
                <small>Định dạng JPG/PNG/WebP, Max 5MB</small>
            </div>
        </div>
        <input ref="faceInput" type="file" accept="image/*" hidden @change="handleFaceSelect" />
        <div class="text-right" v-if="facePreview && !faceUrlInput" style="margin-top: 8px;">
            <button type="button" class="btn-text danger" @click.stop="removeFace">Xóa ảnh này</button>
        </div>
    </template>

    <!-- URL mode -->
    <template v-else>
        <div class="url-input-wrapper">
            <input 
                v-model="faceUrlInput"
                type="url"
                class="sleek-input"
                placeholder="https://example.com/avatar.jpg"
                @input="handleUrlInput"
                @paste="handleUrlPaste"
            />
            <button v-if="faceUrlInput" type="button" class="url-clear-btn" @click="clearFaceUrl" title="Xóa URL">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
        </div>

        <!-- URL Preview -->
        <div v-if="faceUrlInput" class="url-preview-box">
            <div v-if="urlPreviewStatus === 'loading'" class="url-preview-loading">
                <div class="spinner-sm" style="border-color: var(--border-color); border-top-color: var(--accent-primary);"></div>
                <span>Đang tải ảnh xem trước...</span>
            </div>
            <div v-else-if="urlPreviewStatus === 'success'" class="url-preview-success">
                <img :src="faceUrlInput" class="url-preview-img" @error="urlPreviewStatus = 'error'" />
                <div class="url-preview-info">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;color:var(--accent-success)"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                    <span style="color: var(--accent-success); font-size: 0.82rem;">Ảnh hợp lệ</span>
                </div>
            </div>
            <div v-else-if="urlPreviewStatus === 'error'" class="url-preview-error">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:20px;height:20px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                <span>Không thể tải ảnh từ URL này</span>
            </div>
        </div>
    </template>
</div>

                        <div v-if="modalError" class="alert-box error">{{ modalError }}</div>

                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" @click="closeModal">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving || (empNameValidation.touched && !empNameValidation.isValid)">
                                <span v-if="saving" class="spinner-sm"></span> {{ isEditing ? 'Lưu Thông Tin' : 'Tạo Nhân Sự' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Delete Confirm Override -->
        <transition name="modal">
            <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
                <div class="modern-modal mini">
                    <div class="modal-top borderless">
                        <h3>Cảnh báo Xóa</h3>
                    </div>
                    <div class="modal-body text-center">
                        <div class="warning-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
                        <p>Bạn sắp xóa dữ liệu của nhân viên <strong>{{ deleteTarget?.fullName }}</strong>.</p>
                        <p class="text-danger mt-1">Hành động này sẽ xóa toàn bộ lịch sử và FaceID liên quan. Vẫn tiếp tục?</p>

                        <div class="modal-actions mt-4" style="justify-content: center; gap: 12px; flex-wrap: wrap;">
                            <button class="btn btn-secondary" @click="showDeleteModal = false" style="flex: 1; min-width: 100px; max-width: 140px; justify-content: center;">Hủy bỏ</button>
                            <button class="btn btn-danger" @click="handleDelete" :disabled="saving" style="flex: 1; min-width: 100px; max-width: 140px; justify-content: center;">
                                <span v-if="saving" class="spinner-sm"></span> Xác nhận Xóa
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <!-- Toast -->
        <transition name="toast">
            <div v-if="toast" class="toast-card" :class="toast.type">{{ toast.message }}</div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getAll, create, update, deleteEmployee, uploadFace } from '../services/employeeApi'
import { getDepartments, getPositions } from '../services/lookupApi'
import { API_ORIGIN } from '../config/api'
import { validateVietnameseName, normalizeVietnameseName } from '../utils/nameValidator'

const route = useRoute()
const API_BASE = API_ORIGIN

const employees = ref([])
const departments = ref([])
const positions = ref([])
const loading = ref(true)
const loadError = ref('')
const searchQuery = ref('')
const filterStatus = ref('')

const showModal = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const saving = ref(false)
const modalError = ref('')

const modalForm = reactive({ fullName: '', phone: '', email: '', departmentId: null, positionId: null, status: true })
const faceFile = ref(null)
const facePreview = ref(null)

const showDeleteModal = ref(false)
const deleteTarget = ref(null)

const toast = ref(null)
let toastTimer = null

// Name validation state
const empNameValidation = reactive({
    touched: false,
    isValid: false,
    error: ''
})
// Thêm sau các ref hiện tại
const faceInputMode = ref('upload') // 'upload' | 'url'
const faceUrlInput = ref('')
const urlPreviewStatus = ref('') // 'loading' | 'success' | 'error'
let urlDebounceTimer = null

function switchFaceMode(mode) {
    faceInputMode.value = mode
    // Reset cái còn lại khi đổi tab
    if (mode === 'upload') {
        faceUrlInput.value = ''
        urlPreviewStatus.value = ''
    } else {
        faceFile.value = null
        facePreview.value = null
    }
}

function handleUrlInput() {
    urlPreviewStatus.value = 'loading'
    if (urlDebounceTimer) clearTimeout(urlDebounceTimer)
    urlDebounceTimer = setTimeout(() => {
        checkUrlPreview(faceUrlInput.value)
    }, 600)
}

function handleUrlPaste(e) {
    // Paste xử lý ngay không cần debounce
    if (urlDebounceTimer) clearTimeout(urlDebounceTimer)
    const pasted = e.clipboardData?.getData('text') || ''
    urlDebounceTimer = setTimeout(() => {
        checkUrlPreview(pasted || faceUrlInput.value)
    }, 200)
}

function checkUrlPreview(url) {
    if (!url?.trim()) { urlPreviewStatus.value = ''; return }
    urlPreviewStatus.value = 'loading'
    const img = new Image()
    img.onload = () => { urlPreviewStatus.value = 'success' }
    img.onerror = () => { urlPreviewStatus.value = 'error' }
    img.src = url
}

function clearFaceUrl() {
    faceUrlInput.value = ''
    urlPreviewStatus.value = ''
}

function runNameValidation() {
    const val = modalForm.fullName?.trim()
    if (!val) {
        empNameValidation.touched = false
        empNameValidation.isValid = false
        empNameValidation.error = ''
        return
    }
    empNameValidation.touched = true
    const result = validateVietnameseName(val)
    empNameValidation.isValid = result.isValid
    empNameValidation.error = result.error
}

function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { message, type }
    toastTimer = setTimeout(() => { toast.value = null }, 3000)
}

const activeCount = computed(() => employees.value.filter(e => e.status).length)
const inactiveCount = computed(() => employees.value.filter(e => !e.status).length)

let searchTimer = null
function debouncedFetch() {
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => fetchEmployees(), 400)
}

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
        loadError.value = 'Không thể kết nối đến máy chủ.'
    } finally { loading.value = false }
}

function openCreateModal() {
    isEditing.value = false; editingId.value = null; modalError.value = ''
    faceFile.value = null; facePreview.value = null
    faceInputMode.value = 'upload'; faceUrlInput.value = ''; urlPreviewStatus.value = ''
    empNameValidation.touched = false; empNameValidation.isValid = false; empNameValidation.error = ''
    Object.assign(modalForm, { fullName: '', phone: '', email: '', departmentId: null, positionId: null, status: true })
    showModal.value = true
}

function openEditModal(emp) {
    isEditing.value = true; editingId.value = emp.employeeId; modalError.value = ''
    faceFile.value = null
    facePreview.value = emp.faceImageUrl ? (API_BASE + emp.faceImageUrl) : null
    faceInputMode.value = 'upload'; faceUrlInput.value = ''; urlPreviewStatus.value = ''
    Object.assign(modalForm, { fullName: emp.fullName, phone: emp.phone || '', email: emp.email || '', departmentId: emp.departmentId || null, positionId: emp.positionId || null, status: emp.status ?? true })
    showModal.value = true
}

function closeModal() {
    showModal.value = false; modalError.value = ''
    faceFile.value = null; facePreview.value = null
    faceUrlInput.value = ''; urlPreviewStatus.value = ''
}

async function handleSubmit() {
    runNameValidation()
    if (!empNameValidation.isValid) {
        modalError.value = empNameValidation.error || 'Họ và tên không hợp lệ'
        return
    }

    if (faceInputMode.value === 'url' && faceUrlInput.value && urlPreviewStatus.value === 'error') {
        modalError.value = 'URL ảnh không hợp lệ, vui lòng kiểm tra lại'
        return
    }

    modalForm.fullName = normalizeVietnameseName(modalForm.fullName)
    saving.value = true; modalError.value = ''
    try {
        const data = {
            fullName: modalForm.fullName,
            phone: modalForm.phone || null,
            email: modalForm.email || null,
            departmentId: modalForm.departmentId || null,
            positionId: modalForm.positionId || null,
        }

        // ✅ Nếu dùng URL thì truyền thẳng vào body — backend đã hỗ trợ sẵn
        if (faceInputMode.value === 'url' && faceUrlInput.value && urlPreviewStatus.value === 'success') {
            data.faceImageUrl = faceUrlInput.value
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

        // ✅ Nếu dùng file upload thì gọi endpoint /face như cũ
        if (faceInputMode.value === 'upload' && faceFile.value && employeeId) {
            await uploadFace(employeeId, faceFile.value)
        }

        showToast(isEditing.value ? 'Đã lưu thay đổi' : 'Đã tạo hồ sơ nhân sự')
        closeModal(); await fetchEmployees()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Có lỗi khi lưu dữ liệu'
    } finally {
        saving.value = false
    }
}

function handleFaceSelect(e) {
    const f = e.target.files[0]; if (!f) return; e.target.value = ''; faceFile.value = f; facePreview.value = URL.createObjectURL(f);
}
function handleDrop(e) {
    const f = e.dataTransfer.files[0]; if (f && f.type.startsWith('image/')) { faceFile.value = f; facePreview.value = URL.createObjectURL(f) }
}
function removeFace() { faceFile.value = null; facePreview.value = null }

async function handleFaceUpload(id, e) {
    const f = e.target.files[0]; if (!f) return; e.target.value = ''
    try { await uploadFace(id, f); showToast('Cập nhật FaceID thành công!'); await fetchEmployees() } 
    catch (err) { showToast('Upload FaceID thất bại', 'error') }
}

function confirmDelete(emp) { deleteTarget.value = emp; modalError.value = ''; showDeleteModal.value = true }
async function handleDelete() {
    saving.value = true; modalError.value = ''
    try { await deleteEmployee(deleteTarget.value.employeeId); showDeleteModal.value = false; showToast('Đã xóa dữ liệu nhân sự'); await fetchEmployees() } 
    catch (err) { modalError.value = 'Mất kết nối nội bộ' } finally { saving.value = false }
}

function getInitials(name) { return name ? name.split(' ').map(w=>w[0]).slice(0,2).join('').toUpperCase() : '?' }
const avColors = [ '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e' ]
function getAvatarColor(id) { return avColors[id % avColors.length] }

onMounted(async () => {
    if (route.query.search) { searchQuery.value = route.query.search }
    try { const [dRes, pRes] = await Promise.all([getDepartments(), getPositions()]); departments.value = dRes.data; positions.value = pRes.data } catch {}
    fetchEmployees()
})

watch(() => route.query.search, (val) => { if (val !== undefined) { searchQuery.value = val; fetchEmployees() } })
</script>

<style scoped>
/* Page Layout */
.bento-header { margin-bottom: 24px; padding: 0 4px; display: flex; justify-content: space-between; align-items: center; }
.bento-header .greeting h1 { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
.bento-header .greeting p { color: var(--text-secondary); font-size: 0.95rem; }

/* Grid Mini */
.bento-grid-mini { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
.bento-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--border-radius-lg); padding: 24px; }
.stat-card { display: flex; align-items: center; gap: 16px; transition: transform var(--transition-normal); }
.stat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.stat-icon-wrapper { width: 56px; height: 56px; border-radius: 14px; display: flex; justify-content: center; align-items: center; }
.stat-icon-wrapper svg { width: 28px; height: 28px; }
.stat-icon-wrapper.blue { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.stat-icon-wrapper.green { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.stat-icon-wrapper.red { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }
.stat-val { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
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
.avatar, .avatar-img { width: 44px; height: 44px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; object-fit: cover; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); }
.user-id { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }

.contact-cell { display: flex; flex-direction: column; gap: 4px; }
.contact-item { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--text-secondary); }
.contact-item svg { width: 14px; color: var(--text-muted); }

.role-cell { display: flex; flex-direction: column; gap: 2px; }
.dept { font-weight: 500; font-size: 0.9rem; color: var(--text-primary); }
.pos { font-size: 0.8rem; color: var(--accent-primary); }

.status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;}
.status-pill.active { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.status-pill.inactive { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-menu { display: flex; gap: 8px; justify-content: flex-end; }
.icon-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.icon-btn svg { width: 18px; }
.icon-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.icon-btn.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

/* Spinners & Empties */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }
.spinner-lg { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Modern Modals */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 16px;}
.modern-modal { background: var(--bg-card); width: 100%; max-width: 520px; max-height: 90vh; border-radius: var(--border-radius-lg); border: 1px solid var(--border-color); box-shadow: var(--shadow-xl); overflow: hidden; display: flex; flex-direction: column;}
.modern-modal.mini { max-width: 420px; }
.modal-top { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border-color); }
.modal-top.borderless { border: none; padding-bottom: 0; }
.modal-top h3 { font-size: 1.3rem; font-weight: 700; color: var(--text-primary); margin: 0;}
.icon-close { background: none; border: none; color: var(--text-muted); cursor: pointer; width: 24px; transition: color 0.2s; }
.icon-close:hover { color: var(--accent-danger); }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; flex: 1; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }
.req { color: var(--accent-danger); }

.sleek-input, .sleek-select { width: 100%; padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.9rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }

.face-dropzone { border: 2px dashed var(--border-color); border-radius: 12px; height: 120px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; transition: all 0.2s; background: rgba(0,0,0,0.1); }
.face-dropzone:hover { border-color: var(--accent-primary); background: rgba(16, 121, 196, 0.05); }
.dropzone-text { display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); }
.dropzone-text svg { width: 36px; height: 36px; color: var(--text-secondary); }
.face-preview-img { width: 100%; height: 100%; object-fit: contain; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.modal-actions:not(.centered) .btn { width: auto; flex: 0 0 auto; }
.modal-actions.centered { justify-content: center; }

/* Notice elements */
.alert-box { padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; }
.alert-box.error { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); border: 1px solid rgba(239, 68, 68, 0.2); }

/* Name validation feedback */
.name-feedback { margin-top: 4px; font-size: 0.82rem; display: flex; align-items: center; }
.feedback-success { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-success); font-weight: 500; }
.feedback-error { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-danger); font-weight: 500; }
.input-error { border-color: var(--accent-danger) !important; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15) !important; }
.input-success { border-color: var(--accent-success) !important; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important; }

.btn-text.danger { background: none; color: var(--accent-danger); border: none; font-size: 0.85rem; cursor: pointer;}
.warning-icon svg { width: 48px; height: 48px; color: var(--accent-danger); margin-bottom: 16px; }
.text-danger { color: var(--accent-danger); }
.mt-4 { margin-top: 24px; }
.mt-1 { margin-top: 4px; }
.text-right { text-align: right; }
.text-center { text-align: center; }

/* Toast Modern */
.toast-card { position: fixed; bottom: 30px; right: 30px; padding: 16px 24px; border-radius: 12px; background: var(--bg-card); color: var(--text-primary); font-weight: 600; box-shadow: var(--shadow-xl); z-index: 9999; border: 1px solid var(--border-color); }
.toast-card.success { background: var(--accent-success); color: #fff; border: none;}
.toast-card.error { background: var(--accent-danger); color: #fff; border: none;}

.modal-enter-active, .modal-leave-active, .toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(20px); }

@media (max-width: 992px) { .bento-grid-mini { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
    .grid-2 { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
    .modern-modal { max-width: 100%; max-height: 95vh; border-radius: 12px; }
    .modal-backdrop { padding: 8px; }
    .modal-body { padding: 16px; gap: 12px; }
    .modal-top { padding: 16px; }
    .face-dropzone { height: 100px; }
}
</style>
