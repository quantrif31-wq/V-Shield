<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Quản lý Phương tiện</h1>
                <p class="page-subtitle">Đăng ký và quản lý phương tiện ra/vào công ty</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Đăng ký phương tiện
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini" style="grid-template-columns: repeat(3, 1fr);">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13" rx="2" /><path d="M16 8h4l3 3v5h-7V8z" /><circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val">{{ vehicles.length }}</div>
                    <div class="stat-lbl">Tổng phương tiện</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val blue">{{ uniqueOwnerCount }}</div>
                    <div class="stat-lbl">Chủ sở hữu</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper cyan" style="background: rgba(6, 182, 212, 0.1); color: #06b6d4;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z" /><line x1="7" y1="7" x2="7.01" y2="7" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: #06b6d4;">{{ vehicleTypeCount }}</div>
                    <div class="stat-lbl">Loại xe</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm biển số, chủ xe..." @input="debouncedFilter" />
                </div>
                <div class="filter-box" style="display: flex; gap: 12px;">
                    <select v-model="filterType" class="minimal-select">
                        <option value="">Tất cả loại xe</option>
                        <option v-for="t in vehicleTypes" :key="t" :value="t">{{ t }}</option>
                    </select>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="empty-layout">
                <div class="spinner-lg"></div>
                <p>Đang tải danh sách phương tiện...</p>
            </div>

            <!-- Error State -->
            <div v-else-if="loadError" class="empty-layout error-layout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--accent-danger);">
                    <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
                </svg>
                <p>{{ loadError }}</p>
                <button class="btn btn-primary" @click="fetchVehicles">
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
                            <th>Biển số</th>
                            <th>Loại xe</th>
                            <th>Chủ sở hữu</th>
                            <th>Mô tả</th>
                            <th class="text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="v in filteredVehicles" :key="v.vehicleId" class="table-row">
                            <td>
                                <div class="plate-number"><span class="plate">{{ v.licensePlate }}</span></div>
                            </td>
                            <td>
                                <div class="vehicle-info-cell">
                                    <div class="v-type">
                                        <span class="v-icon" v-html="getTypeIcon(v.vehicleTypeName)"></span>
                                        {{ v.vehicleTypeName || 'Chưa phân loại' }}
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="user-cell">
                                    <template v-if="getEmployeeFace(v.employeeId)">
                                        <img :src="API_BASE + getEmployeeFace(v.employeeId)" class="avatar-img" @error="$event.target.style.display = 'none'" />
                                    </template>
                                    <template v-else>
                                        <div class="avatar" :style="{ background: getAvatarColor(v.employeeId || 0) }">{{ getInitials(v.employeeFullName) }}</div>
                                    </template>
                                    <div class="user-info">
                                        <span class="user-name">{{ v.employeeFullName || '—' }}</span>
                                        <span class="user-id">ID: {{ v.employeeId || '—' }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="desc-text">{{ v.description || '—' }}</span>
                            </td>
                            <td class="text-right">
                                <div class="action-menu">
                                    <button class="icon-btn" @click="openModal(v)" title="Sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                                    </button>
                                    <button class="icon-btn danger" @click="deleteVehicle(v)" title="Xóa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filteredVehicles.length === 0 && !loading">
                            <td colspan="5" class="empty-layout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--text-muted);"><rect x="1" y="3" width="15" height="13" rx="2" /><path d="M16 8h4l3 3v5h-7V8z" /><circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" /></svg>
                                <p>Không tìm thấy phương tiện nào</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="!loading && !loadError" class="pagination-footer">
                <span class="showing-txt">Hiển thị {{ filteredVehicles.length }} / {{ vehicles.length }}</span>
            </div>
        </div>

        <!-- Create/Edit Modal -->
        <transition name="modal">
            <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
                <div class="modern-modal">
                    <div class="modal-top">
                        <h3>{{ editingVehicle ? 'Cập nhật Phương tiện' : 'Đăng ký Phương tiện' }}</h3>
                        <button class="icon-close" @click="closeModal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>
                    
                    <form @submit.prevent="saveVehicle" class="modal-body">
                        <div class="grid-2" :class="{ 'grid-1': !editingVehicle }">
                            <div class="input-pane">
                                <label>Biển số xe <span class="req">*</span></label>
                                <input v-model="form.licensePlate" type="text" class="sleek-input" 
                                    :class="{ 'input-error': plateValidation.touched && !plateValidation.isValid, 'input-success': plateValidation.isValid }"
                                    placeholder="VD: 51A-123.45" required 
                                    @input="onPlateInput" />
                                <div v-if="plateValidation.touched" class="plate-feedback">
                                    <span v-if="plateValidation.isValid" class="feedback-success">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                                        Hợp lệ — {{ plateValidation.typeLabel }}
                                        <span v-if="plateValidation.corrected" class="feedback-corrected">(đã sửa: {{ plateValidation.cleanedPlate }})</span>
                                    </span>
                                    <span v-else-if="form.licensePlate.length >= 3" class="feedback-error">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6"/><path d="M9 9l6 6"/></svg>
                                        Biển số không hợp lệ
                                    </span>
                                </div>
                            </div>
                            <div v-if="editingVehicle" class="input-pane">
                                <label>Loại xe</label>
                                <select v-model="form.vehicleTypeId" class="sleek-select">
                                    <option :value="null">-- Chọn loại xe --</option>
                                    <option v-for="type in vehicleTypeOptions" :key="type.vehicleTypeId" :value="type.vehicleTypeId">
                                        {{ type.typeName }}
                                    </option>
                                </select>
                                <small class="field-note">Chỉ chỉnh tay loại xe khi cập nhật phương tiện.</small>
                            </div>
                            <div v-else class="input-pane">
                                <label>Loại xe</label>
                                <div class="auto-detected-type" :class="{ ready: !!inferredVehicleTypeId }">
                                    <strong>{{ inferredVehicleTypeLabel }}</strong>
                                    <span>Tự động nhận diện từ biển số khi đăng ký mới.</span>
                                </div>
                            </div>
                        </div>

                        <div class="input-pane">
                            <label>Chủ sở hữu (Nhân viên) <span class="req">*</span></label>
                            <div class="combobox-wrapper" v-click-outside="closeOwnerDropdown">
                                <div class="input-with-avatar">
                                    <div v-if="selectedOwnerEmployee && !showOwnerDropdown" class="selected-avatar-preview">
                                        <img
                                            v-if="canShowOwnerAvatar(selectedOwnerEmployee)"
                                            :src="getOwnerAvatarSrc(selectedOwnerEmployee)"
                                            class="avatar-img avatar-mini-inline"
                                            @error="markOwnerAvatarBroken(selectedOwnerEmployee.employeeId)"
                                        />
                                        <div
                                            v-else
                                            class="avatar mini avatar-mini-inline"
                                            :style="{ background: getAvatarColor(selectedOwnerEmployee.employeeId || 0) }"
                                        >
                                            {{ getInitials(selectedOwnerEmployee.fullName) }}
                                        </div>
                                    </div>

                                    <input
                                        v-model="ownerSearchQuery"
                                        type="text"
                                        class="sleek-input combobox-input"
                                        :class="{ 'has-avatar': selectedOwnerEmployee && !showOwnerDropdown }"
                                        placeholder="-- Chọn nhân viên --"
                                        required
                                        @focus="onOwnerInputFocus"
                                        @input="onOwnerInputChange"
                                    />
                                </div>

                                <svg class="dropdown-icon" :class="{ rotated: showOwnerDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M6 9l6 6 6-6" />
                                </svg>

                                <div v-if="showOwnerDropdown" class="combobox-dropdown">
                                    <div v-if="filteredOwnerEmployees.length === 0" class="no-results">
                                        Không tìm thấy nhân viên
                                    </div>

                                    <div
                                        v-for="emp in filteredOwnerEmployees"
                                        :key="emp.employeeId"
                                        class="combobox-item"
                                        :class="{ selected: form.employeeId === emp.employeeId }"
                                        @click="selectOwner(emp)"
                                    >
                                        <img
                                            v-if="canShowOwnerAvatar(emp)"
                                            :src="getOwnerAvatarSrc(emp)"
                                            class="avatar-img avatar-img-mini"
                                            @error="markOwnerAvatarBroken(emp.employeeId)"
                                        />
                                        <div
                                            v-else
                                            class="avatar mini"
                                            :style="{ background: getAvatarColor(emp.employeeId || 0) }"
                                        >
                                            {{ getInitials(emp.fullName) }}
                                        </div>

                                        <div class="emp-details">
                                            <span class="emp-name">{{ emp.fullName }}</span>
                                            <span class="emp-meta">
                                                ID: {{ emp.employeeId }}
                                                <span v-if="emp.departmentName">• {{ emp.departmentName }}</span>
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="input-pane">
                            <label>Mô tả</label>
                            <textarea v-model="form.description" rows="3" class="sleek-input" placeholder="Thông tin thêm về phương tiện..." maxlength="200"></textarea>
                            <small class="char-count" v-if="form.description">{{ form.description.length }}/200</small>
                        </div>

                        <div v-if="modalError" class="alert-box error">{{ modalError }}</div>

                        <div class="modal-actions mt-4">
                            <button type="button" class="btn btn-secondary" @click="closeModal">Hủy</button>
                            <button type="submit" class="btn btn-primary" :disabled="saving">
                                <span v-if="saving" class="spinner-sm"></span>
                                {{ editingVehicle ? 'Lưu Thông Tin' : 'Đăng Ký' }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </transition>

        <!-- Delete Confirm Dialog -->
        <transition name="modal">
            <div v-if="deleteConfirm" class="modal-backdrop" @click.self="deleteConfirm = null">
                <div class="modern-modal mini">
                    <div class="modal-body text-center" style="padding: 32px 24px;">
                        <div class="warning-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
                        <h3 style="margin: 0 0 10px 0;">Xóa phương tiện này?</h3>
                        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 24px;">
                            Biển số <strong style="color: var(--text-primary);">{{ deleteConfirm.licensePlate }}</strong> sẽ bị gỡ khỏi hệ thống. Hành động này không thể hoàn tác.
                        </p>
                        <div class="modal-actions" style="justify-content: center; gap: 12px; flex-wrap: wrap;">
                            <button class="btn btn-secondary" @click="deleteConfirm = null" style="flex: 1; min-width: 100px; max-width: 140px; justify-content: center;">Hủy</button>
                            <button class="btn btn-danger" @click="executeDelete" :disabled="saving" style="flex: 1; min-width: 100px; max-width: 140px; justify-content: center;">
                                <span v-if="saving" class="spinner-sm"></span> Xóa
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
import { ref, reactive as useReactive, computed, onMounted } from 'vue'
import * as vehicleApi from '../services/vehicleApi'
import { getAll as getAllEmployees } from '../services/employeeApi'
import { optimizeAndValidatePlate, getVehicleTypeLabel } from '../utils/licensePlateValidator'

// ─── State ──────────────────────────────────────────────────
const API_BASE = 'https://localhost:7107'
const vehicles = ref([])
const employeeList = ref([])
const loading = ref(true)
const loadError = ref('')
const searchQuery = ref('')
const filterType = ref('')

const showModal = ref(false)
const editingVehicle = ref(null)
const saving = ref(false)
const modalError = ref('')
const deleteConfirm = ref(null)
const showOwnerDropdown = ref(false)
const ownerSearchQuery = ref('')
const brokenOwnerAvatarIds = ref({})
const vehicleTypeOptions = ref([])

const form = ref({ licensePlate: '', vehicleTypeId: null, employeeId: null, description: '' })

// License plate validation state
const plateValidation = useReactive({
    touched: false,
    isValid: false,
    type: 'Unknown',
    typeLabel: '',
    cleanedPlate: '',
    corrected: false
})

function onPlateInput() {
    const val = form.value.licensePlate?.trim()
    if (!val) {
        plateValidation.touched = false
        plateValidation.isValid = false
        if (!editingVehicle.value) {
            form.value.vehicleTypeId = null
        }
        return
    }
    plateValidation.touched = true
    const result = optimizeAndValidatePlate(val)
    plateValidation.isValid = result.isValid
    plateValidation.type = result.type
    plateValidation.typeLabel = getVehicleTypeLabel(result.type)
    plateValidation.cleanedPlate = result.cleanedPlate
    plateValidation.corrected = result.cleanedPlate !== result.rawInput
    if (!editingVehicle.value) {
        form.value.vehicleTypeId = result.isValid ? (resolveVehicleTypeIdByPlateType(result.type) || null) : null
    }
}

const toast = ref(null)
let toastTimer = null

// ─── Toast ──────────────────────────────────────────────────
function showToast(message, type = 'success') {
    if (toastTimer) clearTimeout(toastTimer)
    toast.value = { message, type }
    toastTimer = setTimeout(() => { toast.value = null }, 3500)
}

// ─── Computed ───────────────────────────────────────────────
const uniqueOwnerCount = computed(() => {
    const ids = new Set(vehicles.value.filter(v => v.employeeId).map(v => v.employeeId))
    return ids.size
})

const vehicleTypes = computed(() => {
    const types = new Set(vehicles.value.filter(v => v.vehicleTypeName).map(v => v.vehicleTypeName))
    return [...types]
})

const vehicleTypeCount = computed(() => vehicleTypes.value.length)

const selectedOwnerEmployee = computed(() => {
    if (!form.value.employeeId) return null
    return employeeList.value.find(e => e.employeeId === form.value.employeeId) || null
})

const normalizeVehicleTypeName = (name) =>
    String(name || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()

const resolveVehicleTypeIdByPlateType = (plateType) => {
    const aliases = plateType === 'Car'
        ? ['o to', 'xe hoi', 'car']
        : plateType === 'Motorcycle'
            ? ['xe may', 'motorcycle', 'motorbike', 'moto']
            : []

    if (!aliases.length) return null

    const matchedType = vehicleTypeOptions.value.find((item) => {
        const normalizedName = normalizeVehicleTypeName(item.typeName)
        return aliases.some((alias) => normalizedName.includes(alias))
    })

    return matchedType?.vehicleTypeId || null
}

const inferredVehicleTypeId = computed(() => {
    if (!plateValidation.isValid) return null
    return resolveVehicleTypeIdByPlateType(plateValidation.type)
})

const inferredVehicleTypeLabel = computed(() => {
    if (!plateValidation.touched) return 'Sẽ tự nhận diện sau khi nhập biển số'
    if (!plateValidation.isValid || !inferredVehicleTypeId.value) return 'Chưa xác định được loại xe'
    return getVehicleTypeLabel(plateValidation.type)
})

const filteredOwnerEmployees = computed(() => {
    const list = employeeList.value || []
    if (!ownerSearchQuery.value) return list

    const selectedEmp = selectedOwnerEmployee.value
    if (selectedEmp && ownerSearchQuery.value === selectedEmp.fullName) {
        return list
    }

    const q = ownerSearchQuery.value.toLowerCase()
    return list.filter(emp =>
        emp?.fullName?.toLowerCase().includes(q) ||
        String(emp?.employeeId || '').includes(q) ||
        emp?.departmentName?.toLowerCase().includes(q)
    )
})

let filterTimer = null
function debouncedFilter() {
    if (filterTimer) clearTimeout(filterTimer)
    filterTimer = setTimeout(() => { /* filteredVehicles tự cập nhật qua computed */ }, 300)
}

const filteredVehicles = computed(() => {
    return vehicles.value.filter(v => {
        const q = searchQuery.value.toLowerCase()
        const matchSearch = !q ||
            v.licensePlate?.toLowerCase().includes(q) ||
            v.employeeFullName?.toLowerCase().includes(q) ||
            v.description?.toLowerCase().includes(q)
        const matchType = !filterType.value || v.vehicleTypeName === filterType.value
        return matchSearch && matchType
    })
})

// ─── Fetch data ─────────────────────────────────────────────
async function fetchVehicles() {
    loading.value = true
    loadError.value = ''
    try {
        const res = await vehicleApi.getAll()
        vehicles.value = res.data
    } catch (err) {
        loadError.value = 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra API.'
    } finally {
        loading.value = false
    }
}

async function fetchVehicleTypes() {
    try {
        const res = await vehicleApi.getTypes()
        vehicleTypeOptions.value = Array.isArray(res.data) ? res.data : []
    } catch {
        vehicleTypeOptions.value = []
    }
}

async function fetchEmployees() {
    try {
        const res = await getAllEmployees()
        employeeList.value = res.data
    } catch { /* im lặng */ }
}

// ─── Modal ──────────────────────────────────────────────────
function openModal(v = null) {
    editingVehicle.value = v
    modalError.value = ''
    // Reset plate validation
    plateValidation.touched = false
    plateValidation.isValid = false
    plateValidation.type = 'Unknown'
    plateValidation.typeLabel = ''
    plateValidation.cleanedPlate = ''
    plateValidation.corrected = false
    if (v) {
        form.value = {
            licensePlate: v.licensePlate || '',
            vehicleTypeId: v.vehicleTypeId || null,
            employeeId: v.employeeId || null,
            description: v.description || ''
        }
        ownerSearchQuery.value = v.employeeFullName || ''
        // Validate existing plate
        if (v.licensePlate) {
            plateValidation.touched = true
            const result = optimizeAndValidatePlate(v.licensePlate)
            plateValidation.isValid = result.isValid
            plateValidation.type = result.type
            plateValidation.typeLabel = getVehicleTypeLabel(result.type)
            plateValidation.cleanedPlate = result.cleanedPlate
            plateValidation.corrected = false
        }
    } else {
        form.value = { licensePlate: '', vehicleTypeId: null, employeeId: null, description: '' }
        ownerSearchQuery.value = ''
    }
    showOwnerDropdown.value = false
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    modalError.value = ''
    editingVehicle.value = null
    showOwnerDropdown.value = false
    ownerSearchQuery.value = ''
}

async function saveVehicle() {
    if (!form.value.licensePlate?.trim()) {
        modalError.value = 'Vui lòng nhập biển số xe.'
        return
    }
    // Validate license plate format
    const plateResult = optimizeAndValidatePlate(form.value.licensePlate)
    if (!plateResult.isValid) {
        modalError.value = 'Biển số xe không đúng định dạng. VD hợp lệ: 51A-12345 (Ô tô), 29-A1 12345 (Xe máy)'
        return
    }
    // Apply corrected plate if OCR fixed
    if (plateResult.cleanedPlate !== plateResult.rawInput) {
        form.value.licensePlate = plateResult.cleanedPlate
    }
    const inferredTypeId = resolveVehicleTypeIdByPlateType(plateResult.type)
    if (!editingVehicle.value && !inferredTypeId) {
        modalError.value = 'Không thể đối chiếu loại xe từ danh mục trong hệ thống. Vui lòng kiểm tra lại bảng VehicleType.'
        return
    }
    if (!form.value.employeeId) {
        modalError.value = 'Vui lòng chọn nhân viên sở hữu.'
        return
    }

    saving.value = true
    modalError.value = ''
    try {
        if (editingVehicle.value) {
            // Cập nhật
            await vehicleApi.update(editingVehicle.value.vehicleId, {
                licensePlate: form.value.licensePlate.trim(),
                vehicleTypeId: form.value.vehicleTypeId,
                employeeId: form.value.employeeId,
                description: form.value.description || null
            })
            showToast('Đã cập nhật phương tiện thành công!')
        } else {
            // Tạo mới
            await vehicleApi.create({
                licensePlate: form.value.licensePlate.trim(),
                vehicleTypeId: inferredTypeId,
                employeeId: form.value.employeeId,
                description: form.value.description || null
            })
            showToast('Đã đăng ký phương tiện thành công!')
        }
        closeModal()
        await fetchVehicles()
    } catch (err) {
        const msg = err.response?.data?.message || err.response?.data?.title || 'Có lỗi xảy ra khi lưu dữ liệu.'
        modalError.value = msg
    } finally {
        saving.value = false
    }
}

// ─── Delete ─────────────────────────────────────────────────
function deleteVehicle(v) {
    deleteConfirm.value = v
}

async function executeDelete() {
    if (!deleteConfirm.value) return
    saving.value = true
    try {
        await vehicleApi.deleteVehicle(deleteConfirm.value.vehicleId)
        showToast('Đã xóa phương tiện khỏi hệ thống.')
        deleteConfirm.value = null
        await fetchVehicles()
    } catch (err) {
        showToast('Không thể xóa phương tiện.', 'error')
    } finally {
        saving.value = false
    }
}

// ─── Helpers ────────────────────────────────────────────────
const vClickOutside = {
    mounted(el, binding) {
        el.clickOutsideEvent = function (event) {
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

function onOwnerInputFocus() {
    showOwnerDropdown.value = true
}

function onOwnerInputChange() {
    showOwnerDropdown.value = true

    if (!selectedOwnerEmployee.value) return
    if (ownerSearchQuery.value !== selectedOwnerEmployee.value.fullName) {
        form.value.employeeId = null
    }
}

function selectOwner(emp) {
    form.value.employeeId = emp.employeeId
    ownerSearchQuery.value = emp.fullName
    showOwnerDropdown.value = false
}

function closeOwnerDropdown() {
    showOwnerDropdown.value = false

    if (selectedOwnerEmployee.value) {
        ownerSearchQuery.value = selectedOwnerEmployee.value.fullName
    } else {
        ownerSearchQuery.value = ''
    }
}

function getEmployeeFace(empId) {
    if (!empId) return null;
    const emp = employeeList.value.find(e => e.employeeId === empId);
    return emp ? emp.faceImageUrl : null;
}

function canShowOwnerAvatar(employee) {
    return !!employee?.faceImageUrl && !brokenOwnerAvatarIds.value[employee.employeeId]
}

function getOwnerAvatarSrc(employee) {
    if (!employee?.faceImageUrl) return ''
    return employee.faceImageUrl.startsWith('http') ? employee.faceImageUrl : `${API_BASE}${employee.faceImageUrl}`
}

function markOwnerAvatarBroken(employeeId) {
    if (!employeeId || brokenOwnerAvatarIds.value[employeeId]) return
    brokenOwnerAvatarIds.value = { ...brokenOwnerAvatarIds.value, [employeeId]: true }
}

function getInitials(name) {
    if (!name) return '?'
    return name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
}

const avColors = ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e']
function getAvatarColor(id) { return avColors[Math.abs(id) % avColors.length] }

function getTypeIcon(typeName) {
    const name = (typeName || '').toLowerCase()
    if (name.includes('ô tô') || name.includes('car'))
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
    if (name.includes('xe máy') || name.includes('motorbike') || name.includes('moto'))
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-4 8h6"/><path d="M9 14l1-3h6"/></svg>'
    if (name.includes('xe đạp') || name.includes('bicycle'))
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-7 11"/><path d="M5.5 17.5L9 8h4l4 9.5"/></svg>'
    if (name.includes('xe tải') || name.includes('truck'))
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
    // default
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
}

// ─── Init ───────────────────────────────────────────────────
onMounted(async () => {
    await Promise.all([fetchVehicles(), fetchEmployees(), fetchVehicleTypes()])
})
</script>

<style scoped>
/* Common Page Layout - Mirrors Employees.vue */
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
.stat-val { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-val.blue { color: var(--accent-primary); }
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

.plate-number { display: inline-flex; }
.plate { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.95rem; padding: 6px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; letter-spacing: 0.5px; color: var(--text-primary); box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }

.vehicle-info-cell { display: flex; flex-direction: column; gap: 4px; }
.v-type { display: flex; align-items: center; gap: 8px; font-weight: 500; font-size: 0.95rem; color: var(--text-primary); }
.v-icon { color: var(--text-muted); display: flex; }

.desc-text { font-size: 0.9rem; color: var(--text-secondary); }

.user-cell { display: flex; align-items: center; gap: 14px; }
.avatar, .avatar-img { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; font-size: 0.8rem; object-fit: cover; }
.avatar.mini, .avatar-img-mini { width: 32px; height: 32px; font-size: 0.78rem; flex-shrink: 0; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.user-id { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }

.action-menu { display: flex; gap: 8px; justify-content: flex-end; }
.icon-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.icon-btn svg { width: 18px; }
.icon-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.icon-btn.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

/* Spinners & Empties */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }
.spinner-lg { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Pagination Area */
.pagination-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border-color); }
.showing-txt { font-size: 0.9rem; color: var(--text-secondary); }

/* Modern Modals */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 16px;}
.modern-modal { background: var(--bg-card); width: 100%; max-width: 520px; max-height: 90vh; border-radius: var(--border-radius-lg); border: 1px solid var(--border-color); box-shadow: var(--shadow-xl); overflow: hidden; display: flex; flex-direction: column;}
.modern-modal.mini { max-width: 400px; }
.modal-top { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border-color); }
.modal-top h3 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;}
.icon-close { background: none; border: none; color: var(--text-muted); cursor: pointer; width: 24px; transition: color 0.2s; }
.icon-close:hover { color: var(--accent-danger); }

.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; flex: 1; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.grid-1 { grid-template-columns: 1fr; }
.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }
.req { color: var(--accent-danger); }
.char-count { font-size: 0.8rem; color: var(--text-muted); text-align: right; }
.field-note { font-size: 0.8rem; color: var(--text-muted); }

.sleek-input, .sleek-select { width: 100%; padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.9rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }
.auto-detected-type {
    min-height: 92px;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1px dashed var(--border-color);
    background: linear-gradient(180deg, rgba(16, 121, 196, 0.04), rgba(16, 121, 196, 0.01));
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 6px;
}
.auto-detected-type strong {
    font-size: 1rem;
    color: var(--text-primary);
}
.auto-detected-type span {
    font-size: 0.82rem;
    color: var(--text-muted);
    line-height: 1.45;
}
.auto-detected-type.ready {
    border-color: rgba(16, 185, 129, 0.35);
    background: linear-gradient(180deg, rgba(16, 185, 129, 0.08), rgba(16, 185, 129, 0.02));
}

/* Owner Combobox */
.combobox-wrapper { position: relative; width: 100%; border-radius: 8px; }
.input-with-avatar { position: relative; width: 100%; display: flex; align-items: center; }
.selected-avatar-preview { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); pointer-events: none; z-index: 2; }
.avatar-mini-inline { width: 24px; height: 24px; font-size: 0.7rem; }
.combobox-input { padding-right: 40px; background: #fff !important; cursor: text; }
.combobox-input.has-avatar { padding-left: 52px; }
.dropdown-icon { position: absolute; right: 14px; top: 14px; width: 18px; height: 18px; color: var(--accent-primary); pointer-events: none; transition: transform 0.2s; }
.dropdown-icon.rotated { transform: rotate(180deg); }
.combobox-dropdown { position: absolute; top: calc(100% + 4px); left: 0; width: 100%; max-height: 240px; overflow-y: auto; background: #fff; border: 1px solid var(--border-color); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); z-index: 100; padding: 4px 0; }
.combobox-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; cursor: pointer; transition: background 0.2s; border-bottom: 1px solid var(--border-color); }
.combobox-item:last-child { border-bottom: none; }
.combobox-item:hover { background: rgba(16, 121, 196, 0.03); }
.combobox-item.selected { background: rgba(16, 121, 196, 0.06); }
.emp-details { display: flex; flex-direction: column; min-width: 0; }
.emp-name { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); }
.emp-meta { font-size: 0.83rem; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.no-results { padding: 14px; text-align: center; color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.modal-actions:not(.centered) .btn { width: auto; flex: 0 0 auto; }
.modal-actions.centered { justify-content: center; }

/* Notice & Alerts */
.alert-box { padding: 12px 16px; border-radius: 8px; font-size: 0.9rem; }
.alert-box.error { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); border: 1px solid rgba(239, 68, 68, 0.2); }

.warning-icon svg { width: 48px; height: 48px; color: var(--accent-danger); margin-bottom: 16px; }
.mt-4 { margin-top: 24px; }

/* Plate validation feedback */
.plate-feedback { margin-top: 4px; font-size: 0.82rem; display: flex; align-items: center; }
.feedback-success { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-success); font-weight: 500; }
.feedback-error { display: inline-flex; align-items: center; gap: 5px; color: var(--accent-danger); font-weight: 500; }
.feedback-corrected { font-size: 0.78rem; color: var(--accent-primary); margin-left: 4px; font-style: italic; }
.input-error { border-color: var(--accent-danger) !important; box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15) !important; }
.input-success { border-color: var(--accent-success) !important; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15) !important; }
.text-right { text-align: right; }
.text-center { text-align: center; }

/* Toast Modern */
.toast-card { position: fixed; bottom: 30px; right: 30px; padding: 16px 24px; border-radius: 12px; background: var(--bg-card); color: var(--text-primary); font-weight: 600; box-shadow: var(--shadow-xl); z-index: 9999; border: 1px solid var(--border-color); }
.toast-card.success { background: var(--accent-success); color: #fff; border: none;}
.toast-card.error { background: var(--accent-danger); color: #fff; border: none;}

.modal-enter-active, .modal-leave-active, .toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(20px); }

@media (max-width: 1200px) { .bento-grid-mini { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
    .bento-grid-mini { grid-template-columns: 1fr; }
    .grid-2 { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
    .modern-modal { max-width: 100%; max-height: 95vh; border-radius: 12px; }
    .modal-backdrop { padding: 8px; }
    .modal-body { padding: 16px; gap: 12px; }
    .modal-top { padding: 16px; }
}
</style>
