<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Phòng ban & Chức vụ</h1>
                <p class="page-subtitle">Quản lý danh mục phòng ban và chức vụ trong hệ thống</p>
            </div>
        </div>

        <!-- Two column layout -->
        <div class="two-col">
            <!-- Departments -->
            <div class="card">
                <div class="card-header" style="display:flex;align-items:center;justify-content:space-between;">
                    <h3 style="font-size:1rem;font-weight:600;color:var(--text-primary);">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width:18px;height:18px;display:inline;vertical-align:middle;margin-right:6px;">
                            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                            <polyline points="9 22 9 12 15 12 15 22" />
                        </svg>
                        Phòng ban
                    </h3>
                    <button class="btn btn-primary btn-sm" @click="openDeptModal()">+ Thêm</button>
                </div>

                <div v-if="deptLoading" class="loading-sm">Đang tải...</div>
                <div v-else>
                    <table class="data-table compact">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tên phòng ban</th>
                                <th>Số NV</th>
                                <th style="width:90px;text-align:center;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="dept in departments" :key="dept.departmentId">
                                <td>{{ dept.departmentId }}</td>
                                <td><strong>{{ dept.name }}</strong></td>
                                <td>
                                    <span class="badge info">{{ dept.employeeCount }}</span>
                                </td>
                                <td>
                                    <div class="action-buttons">
                                        <button class="btn-icon" @click="openDeptModal(dept)" title="Sửa">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width:14px;height:14px;">
                                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                            </svg>
                                        </button>
                                        <button class="btn-icon danger" @click="confirmDeleteDept(dept)" title="Xóa">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width:14px;height:14px;">
                                                <polyline points="3 6 5 6 21 6" />
                                                <path
                                                    d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                            </svg>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="departments.length === 0">
                                <td colspan="4" class="empty-state">Chưa có phòng ban</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Positions -->
            <div class="card">
                <div class="card-header" style="display:flex;align-items:center;justify-content:space-between;">
                    <h3 style="font-size:1rem;font-weight:600;color:var(--text-primary);">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width:18px;height:18px;display:inline;vertical-align:middle;margin-right:6px;">
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                        </svg>
                        Chức vụ
                    </h3>
                    <button class="btn btn-primary btn-sm" @click="openPosModal()">+ Thêm</button>
                </div>

                <div v-if="posLoading" class="loading-sm">Đang tải...</div>
                <div v-else>
                    <table class="data-table compact">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Tên chức vụ</th>
                                <th>Số NV</th>
                                <th style="width:90px;text-align:center;">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="pos in positions" :key="pos.positionId">
                                <td>{{ pos.positionId }}</td>
                                <td><strong>{{ pos.name }}</strong></td>
                                <td>
                                    <span class="badge info">{{ pos.employeeCount }}</span>
                                </td>
                                <td>
                                    <div class="action-buttons">
                                        <button class="btn-icon" @click="openPosModal(pos)" title="Sửa">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width:14px;height:14px;">
                                                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                            </svg>
                                        </button>
                                        <button class="btn-icon danger" @click="confirmDeletePos(pos)" title="Xóa">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width:14px;height:14px;">
                                                <polyline points="3 6 5 6 21 6" />
                                                <path
                                                    d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                            </svg>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                            <tr v-if="positions.length === 0">
                                <td colspan="4" class="empty-state">Chưa có chức vụ</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Toast -->
        <transition name="toast">
            <div v-if="toast" class="toast" :class="toast.type">{{ toast.message }}</div>
        </transition>

        <!-- Department Modal -->
        <transition name="modal">
            <div v-if="showDeptModal" class="modal-overlay" @click.self="showDeptModal = false">
                <div class="modal" style="max-width: 440px;">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingDept ? 'Sửa phòng ban' : 'Thêm phòng ban' }}</h3>
                        <button class="modal-close" @click="showDeptModal = false">✕</button>
                    </div>
                    <form @submit.prevent="handleDeptSubmit">
                        <div class="form-group">
                            <label>Tên phòng ban *</label>
                            <input v-model="deptForm.name" type="text" placeholder="Nhập tên phòng ban" required
                                maxlength="100" />
                        </div>
                        <div v-if="modalError" class="form-error">{{ modalError }}</div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" @click="showDeptModal = false">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ editingDept ? 'Cập nhật' : 'Thêm' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Position Modal -->
        <transition name="modal">
            <div v-if="showPosModal" class="modal-overlay" @click.self="showPosModal = false">
                <div class="modal" style="max-width: 440px;">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingPos ? 'Sửa chức vụ' : 'Thêm chức vụ' }}</h3>
                        <button class="modal-close" @click="showPosModal = false">✕</button>
                    </div>
                    <form @submit.prevent="handlePosSubmit">
                        <div class="form-group">
                            <label>Tên chức vụ *</label>
                            <input v-model="posForm.name" type="text" placeholder="Nhập tên chức vụ" required
                                maxlength="100" />
                        </div>
                        <div v-if="modalError" class="form-error">{{ modalError }}</div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" @click="showPosModal = false">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ editingPos ? 'Cập nhật' : 'Thêm' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Delete Confirm -->
        <transition name="modal">
            <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
                <div class="modal" style="max-width: 420px;">
                    <div class="modal-header">
                        <h3 class="modal-title">Xác nhận xóa</h3>
                        <button class="modal-close" @click="showDeleteModal = false">✕</button>
                    </div>
                    <p style="color: var(--text-secondary); line-height: 1.6; margin-bottom: 8px;">
                        Bạn có chắc chắn muốn xóa
                        <strong style="color: var(--text-primary);">{{ deleteTarget?.name }}</strong>?
                    </p>
                    <div v-if="modalError" class="form-error" style="margin-top: 12px;">{{ modalError }}</div>
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
    toastTimer = setTimeout(() => { toast.value = null }, 3000)
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
            showToast('Xóa phòng ban thành công')
            await fetchDepartments()
        } else {
            await deletePosition(deleteTarget.value.positionId)
            showToast('Xóa chức vụ thành công')
            await fetchPositions()
        }
        showDeleteModal.value = false
    } catch (err) {
        modalError.value = err.response?.data?.message || 'Không thể xóa'
    } finally { saving.value = false }
}

onMounted(() => {
    fetchDepartments()
    fetchPositions()
})
</script>

<style scoped>
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 900px) {
    .two-col {
        grid-template-columns: 1fr;
    }
}

.data-table.compact th,
.data-table.compact td {
    padding: 10px 14px;
    font-size: 0.85rem;
}

.action-buttons {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
}

.btn-icon.danger:hover {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
    border-color: var(--accent-danger);
}

.loading-sm {
    padding: 32px 20px;
    text-align: center;
    color: var(--text-muted);
}

.empty-state {
    text-align: center;
    color: var(--text-muted);
    padding: 28px !important;
}

.form-error {
    padding: 10px 14px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--border-radius-sm);
    color: var(--accent-danger);
    font-size: 0.85rem;
    margin-bottom: 16px;
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

.toast.success { background: var(--accent-success); color: #fff; }
.toast.error { background: var(--accent-danger); color: #fff; }

.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(16px); }

.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
