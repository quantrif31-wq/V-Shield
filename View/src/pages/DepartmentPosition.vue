<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Phòng ban & Chức vụ</h1>
                <p class="page-subtitle">Cấu trúc tổ chức và danh mục hệ thống</p>
            </div>
        </header>

        <!-- Two Column Layout using Bento Grid -->
        <div class="bento-grid-2col">
            <!-- Departments Card -->
            <div class="bento-card table-section">
                <div class="card-header-mini">
                    <h3 class="bento-title flex-center gap-2">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="title-icon">
                            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                            <polyline points="9 22 9 12 15 12 15 22" />
                        </svg>
                        Phòng ban
                    </h3>
                    <button class="btn btn-primary btn-sm rounded-btn" @click="openDeptModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19" />
                            <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        Thêm
                    </button>
                </div>

                <div v-if="deptLoading" class="empty-layout">
                    <div class="spinner-lg"></div>
                </div>
                <div v-else class="sleek-table-container">
                    <table class="sleek-table">
                        <thead>
                            <tr>
                                <th style="width: 60px;">ID</th>
                                <th>Tên phòng ban</th>
                                <th style="width: 90px; text-align: center;">Số NV</th>
                                <th style="width: 90px; text-align: right;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="dept in departments" :key="dept.departmentId" class="table-row">
                                <td class="text-muted font-mono">#{{ dept.departmentId }}</td>
                                <td class="font-medium text-primary">{{ dept.name }}</td>
                                <td class="text-center">
                                    <span class="badge minimal">{{ dept.employeeCount }}</span>
                                </td>
                                <td>
                                    <div class="action-menu">
                                        <button class="icon-btn" @click="openDeptModal(dept)" title="Sửa"><svg
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                            </svg></button>
                                        <button class="icon-btn action-reject" @click="confirmDeleteDept(dept)"
                                            title="Xóa"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="2">
                                                <polyline points="3 6 5 6 21 6" />
                                                <path
                                                    d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                            </svg></button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="departments.length === 0">
                                <td colspan="4" class="py-8">
                                    <div class="empty-layout">
                                        <span class="text-muted">Chưa có phòng ban nào</span>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Positions Card -->
            <div class="bento-card table-section">
                <div class="card-header-mini">
                    <h3 class="bento-title flex-center gap-2">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="title-icon">
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                        </svg>
                        Chức vụ
                    </h3>
                    <button class="btn btn-primary btn-sm rounded-btn" @click="openPosModal()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19" />
                            <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        Thêm
                    </button>
                </div>

                <div v-if="posLoading" class="empty-layout">
                    <div class="spinner-lg"></div>
                </div>
                <div v-else class="sleek-table-container">
                    <table class="sleek-table">
                        <thead>
                            <tr>
                                <th style="width: 60px;">ID</th>
                                <th>Tên chức vụ</th>
                                <th style="width: 90px; text-align: center;">Số NV</th>
                                <th style="width: 90px; text-align: right;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="pos in positions" :key="pos.positionId" class="table-row">
                                <td class="text-muted font-mono">#{{ pos.positionId }}</td>
                                <td class="font-medium text-primary">{{ pos.name }}</td>
                                <td class="text-center">
                                    <span class="badge minimal">{{ pos.employeeCount }}</span>
                                </td>
                                <td>
                                    <div class="action-menu">
                                        <button class="icon-btn" @click="openPosModal(pos)" title="Sửa"><svg
                                                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                            </svg></button>
                                        <button class="icon-btn action-reject" @click="confirmDeletePos(pos)"
                                            title="Xóa"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                                stroke-width="2">
                                                <polyline points="3 6 5 6 21 6" />
                                                <path
                                                    d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                            </svg></button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="positions.length === 0">
                                <td colspan="4" class="py-8">
                                    <div class="empty-layout">
                                        <span class="text-muted">Chưa có chức vụ nào</span>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Modern Toast Notification -->
        <transition name="toast-slide">
            <div v-if="toast" class="modern-toast" :class="toast.type">
                <div class="toast-icon">
                    <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                    </svg>
                </div>
                <span>{{ toast.message }}</span>
            </div>
        </transition>

        <!-- Department Modal -->
        <transition name="modal">
            <div v-if="showDeptModal" class="modal-backdrop" @click.self="showDeptModal = false">
                <div class="modern-modal mini">
                    <div class="modal-top">
                        <h3>{{ editingDept ? 'Cập nhật Phòng ban' : 'Thêm Phòng ban' }}</h3>
                        <button class="icon-close" @click="showDeptModal = false"><svg viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg></button>
                    </div>
                    <form @submit.prevent="handleDeptSubmit" class="modal-body">
                        <div class="input-pane mb-4">
                            <label>Tên phòng ban <span class="req">*</span></label>
                            <input v-model="deptForm.name" type="text" class="sleek-input"
                                placeholder="Ví dụ: Phòng Nhân sự" required maxlength="100" />
                        </div>
                        <div v-if="modalError" class="error-box mb-4"><svg viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="8" x2="12" y2="12" />
                                <line x1="12" y1="16" x2="12.01" y2="16" />
                            </svg><span>{{ modalError }}</span></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" @click="showDeptModal = false">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ editingDept ? 'Lưu' : 'Tạo mới' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Position Modal -->
        <transition name="modal">
            <div v-if="showPosModal" class="modal-backdrop" @click.self="showPosModal = false">
                <div class="modern-modal mini">
                    <div class="modal-top">
                        <h3>{{ editingPos ? 'Cập nhật Chức vụ' : 'Thêm Chức vụ' }}</h3>
                        <button class="icon-close" @click="showPosModal = false"><svg viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18" />
                                <line x1="6" y1="6" x2="18" y2="18" />
                            </svg></button>
                    </div>
                    <form @submit.prevent="handlePosSubmit" class="modal-body">
                        <div class="input-pane mb-4">
                            <label>Tên chức vụ <span class="req">*</span></label>
                            <input v-model="posForm.name" type="text" class="sleek-input"
                                placeholder="Ví dụ: Trưởng phòng" required maxlength="100" />
                        </div>
                        <div v-if="modalError" class="error-box mb-4"><svg viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="8" x2="12" y2="12" />
                                <line x1="12" y1="16" x2="12.01" y2="16" />
                            </svg><span>{{ modalError }}</span></div>
                        <div class="modal-actions">
                            <button type="button" class="btn btn-secondary" @click="showPosModal = false">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ editingPos ? 'Lưu' : 'Tạo mới' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Delete Confirm -->
        <transition name="modal">
            <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
                <div class="modern-modal mini">
                    <div class="modal-body text-center" style="padding: 32px 24px;">
                        <div class="warning-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                stroke-width="2">
                                <path
                                    d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                <line x1="12" y1="9" x2="12" y2="13" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg></div>
                        <h3 style="margin: 0 0 10px 0;">Xác nhận Xóa?</h3>
                        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 24px;">
                            Hạng mục <strong style="color: var(--text-primary);">{{ deleteTarget?.name }}</strong> sẽ bị
                            xóa vĩnh viễn khỏi hệ thống.
                        </p>
                        <div v-if="modalError" class="error-box text-left mb-4"><span>{{ modalError }}</span></div>
                        <div class="modal-actions centered">
                            <button class="btn btn-secondary" @click="showDeleteModal = false">Hủy</button>
                            <button class="btn btn-danger" @click="handleDelete" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span> Xóa hạng mục
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
    getDepartments, createDepartment, updateDepartment, deleteDepartment,
    getPositions, createPosition, updatePosition, deletePosition
} from '../services/lookupApi'

const departments = ref([])
const positions = ref([])
const deptLoading = ref(true)
const posLoading = ref(true)

// Modal state
const showDeptModal = ref(false)
const showPosModal = ref(false)
const showDeleteModal = ref(false)
const editingDept = ref(null)
const editingPos = ref(null)
const deleteTarget = ref(null)
const deleteType = ref('') // 'dept' or 'pos'
const saving = ref(false)
const modalError = ref('')

const deptForm = reactive({ name: '' })
const posForm = reactive({ name: '' })

// Toast
const toast = ref(null)
let toastTimer = null
function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { message, type }
    toastTimer = setTimeout(() => { toast.value = null }, 3500)
}

// Fetch
async function fetchDepartments() {
    deptLoading.value = true
    try {
        const res = await getDepartments()
        departments.value = res.data
    } catch (e) { console.error(e) }
    finally { deptLoading.value = false }
}

async function fetchPositions() {
    posLoading.value = true
    try {
        const res = await getPositions()
        positions.value = res.data
    } catch (e) { console.error(e) }
    finally { posLoading.value = false }
}

// Department CRUD
function openDeptModal(dept = null) {
    editingDept.value = dept
    modalError.value = ''
    deptForm.name = dept ? dept.name : ''
    showDeptModal.value = true
}

async function handleDeptSubmit() {
    saving.value = true
    modalError.value = ''
    try {
        if (editingDept.value) {
            await updateDepartment(editingDept.value.departmentId, { name: deptForm.name })
            showToast('Cập nhật phòng ban thành công')
        } else {
            await createDepartment({ name: deptForm.name })
            showToast('Thêm phòng ban thành công')
        }
        showDeptModal.value = false
        await fetchDepartments()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Đã xảy ra lỗi'
    } finally { saving.value = false }
}

function confirmDeleteDept(dept) {
    deleteTarget.value = dept
    deleteType.value = 'dept'
    modalError.value = ''
    showDeleteModal.value = true
}

// Position CRUD
function openPosModal(pos = null) {
    editingPos.value = pos
    modalError.value = ''
    posForm.name = pos ? pos.name : ''
    showPosModal.value = true
}

async function handlePosSubmit() {
    saving.value = true
    modalError.value = ''
    try {
        if (editingPos.value) {
            await updatePosition(editingPos.value.positionId, { name: posForm.name })
            showToast('Cập nhật chức vụ thành công')
        } else {
            await createPosition({ name: posForm.name })
            showToast('Thêm chức vụ thành công')
        }
        showPosModal.value = false
        await fetchPositions()
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Đã xảy ra lỗi'
    } finally { saving.value = false }
}

function confirmDeletePos(pos) {
    deleteTarget.value = pos
    deleteType.value = 'pos'
    modalError.value = ''
    showDeleteModal.value = true
}

// Delete handler
async function handleDelete() {
    saving.value = true
    modalError.value = ''
    try {
        if (deleteType.value === 'dept') {
            await deleteDepartment(deleteTarget.value.departmentId)
            showToast('Đã xóa phòng ban khỏi hệ thống')
            await fetchDepartments()
        } else {
            await deletePosition(deleteTarget.value.positionId)
            showToast('Đã xóa chức vụ khỏi hệ thống')
            await fetchPositions()
        }
        showDeleteModal.value = false
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Không thể xóa hạng mục này'
    } finally { saving.value = false }
}

onMounted(() => {
    fetchDepartments()
    fetchPositions()
})
</script>

<style scoped>
/* Page Layout */
.bento-header {
    margin-bottom: 24px;
    padding: 0 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.bento-header .greeting h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
}

.bento-header .greeting p {
    color: var(--text-secondary);
    font-size: 0.95rem;
}

.bento-grid-2col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

/* Dashboard Cards */
.bento-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-height: 400px;
}

.card-header-mini {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-color);
}

.bento-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    white-space: nowrap;
}

.title-icon {
    width: 20px;
    height: 20px;
    color: var(--accent-primary);
}

.rounded-btn {
    border-radius: 8px;
    padding: 6px 16px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-weight: 600;
    font-size: 0.85rem;
    white-space: nowrap;
    width: fit-content;
    flex-shrink: 0;
}

.rounded-btn svg {
    width: 14px;
    height: 14px;
}

/* Table Elements */
.sleek-table-container {
    flex: 1;
    overflow-x: auto;
}

.sleek-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
}

.sleek-table th {
    padding: 14px 24px;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
    background: rgba(0, 0, 0, 0.1);
}

.sleek-table td {
    padding: 14px 24px;
    border-bottom: 1px solid var(--border-color);
    vertical-align: middle;
    font-size: 0.9rem;
}

.table-row {
    transition: background var(--transition-fast);
}

.table-row:hover {
    background: var(--bg-card-hover);
    cursor: default;
}

.badge.minimal {
    background: rgba(16, 121, 196, 0.1);
    border: 1px solid rgba(16, 121, 196, 0.2);
    color: var(--accent-primary);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Actions */
.action-menu {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
}

.icon-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s;
}

.icon-btn svg {
    width: 16px;
}

.icon-btn:hover {
    background: var(--bg-input);
    color: var(--text-primary);
}

.icon-btn.action-reject:hover {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-danger);
}

/* Typography/Utils */
.text-primary {
    color: var(--text-primary);
}

.text-muted {
    color: var(--text-muted);
}

.font-medium {
    font-weight: 500;
}

.font-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}

.text-center {
    text-align: center;
}

.flex-center {
    display: flex;
    align-items: center;
}

.gap-2 {
    gap: 8px;
}

.mb-4 {
    margin-bottom: 16px;
}

.py-8 {
    padding-top: 32px;
    padding-bottom: 32px;
}

/* State Placeholders */
.empty-layout {
    text-align: center;
    color: var(--text-muted);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 120px;
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
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    display: inline-block;
    margin-right: 6px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Modern Modals */
.modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px;
}

.modern-modal {
    background: var(--bg-card);
    width: 100%;
    max-width: 500px;
    border-radius: var(--border-radius-lg);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-xl);
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.modern-modal.mini {
    max-width: 420px;
}

.modal-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px;
    border-bottom: 1px solid var(--border-color);
}

.modal-top h3 {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}

.icon-close {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    width: 24px;
    transition: color 0.2s;
}

.icon-close:hover {
    color: var(--accent-danger);
}

.modal-body {
    padding: 24px;
    display: flex;
    flex-direction: column;
}

.input-pane {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.input-pane label {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.req {
    color: var(--accent-danger);
}

.sleek-input {
    width: 100%;
    padding: 12px 16px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    color: var(--text-primary);
    outline: none;
    transition: border 0.2s;
    font-size: 0.95rem;
}

.sleek-input:focus {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15);
}

.error-box {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 8px;
    color: var(--accent-danger);
    font-size: 0.85rem;
}

.error-box svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 8px;
}

.modal-actions.centered {
    justify-content: center;
    margin-top: 0;
}

.warning-icon svg {
    width: 48px;
    height: 48px;
    color: var(--accent-danger);
    margin-bottom: 16px;
}

/* Toast */
.modern-toast {
    position: fixed;
    bottom: 32px;
    right: 32px;
    padding: 14px 20px;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 500;
    z-index: 9999;
    box-shadow: var(--shadow-xl);
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: var(--bg-card);
    color: var(--text-primary);
}

.toast-icon svg {
    width: 20px;
    height: 20px;
}

.modern-toast.success .toast-icon {
    color: var(--accent-success);
}

.modern-toast.error .toast-icon {
    color: var(--accent-danger);
}

.toast-slide-enter-active,
.toast-slide-leave-active {
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.toast-slide-enter-from,
.toast-slide-leave-to {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
}

.modal-enter-active,
.modal-leave-active {
    transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
    transform: scale(0.95);
}

@media (max-width: 1024px) {
    .bento-grid-2col {
        grid-template-columns: 1fr;
    }

    .bento-card {
        min-height: auto;
    }
}
</style>
