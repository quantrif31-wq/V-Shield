<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">System catalog</span>
                <h1 class="page-title">Danh mục hệ thống</h1>
            </div>
        </div>

        <section class="ops-grid three">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Departments</span>
                        <h2 class="panel-title">Phòng ban</h2>
                    </div>
                    <router-link to="/departments-positions" class="btn btn-secondary btn-sm">Quản lý chi tiết</router-link>
                </div>

                <div v-if="isLoading" class="empty-card">Đang tải phòng ban...</div>
                <div v-else-if="departments.length === 0" class="empty-card">Chưa có phòng ban nào.</div>
                <div v-else class="surface-list">
                    <article v-for="department in departments" :key="department.departmentId" class="surface-item">
                        <div class="surface-item-title">{{ department.name }}</div>
                        <div class="surface-item-sub">{{ department.employeeCount }} nhân sự</div>
                    </article>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Positions</span>
                        <h2 class="panel-title">Chức vụ</h2>
                    </div>
                    <router-link to="/departments-positions" class="btn btn-secondary btn-sm">Quản lý chi tiết</router-link>
                </div>

                <div v-if="isLoading" class="empty-card">Đang tải chức vụ...</div>
                <div v-else-if="positions.length === 0" class="empty-card">Chưa có chức vụ nào.</div>
                <div v-else class="surface-list">
                    <article v-for="position in positions" :key="position.positionId" class="surface-item">
                        <div class="surface-item-title">{{ position.name }}</div>
                        <div class="surface-item-sub">{{ position.employeeCount }} nhân sự</div>
                    </article>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Exception reasons</span>
                        <h2 class="panel-title">Lý do ngoại lệ</h2>
                    </div>
                    <button class="btn btn-secondary btn-sm" @click="openReasonModal()">Thêm lý do</button>
                </div>

                <div v-if="isLoading" class="empty-card">Đang tải lý do ngoại lệ...</div>
                <div v-else-if="reasons.length === 0" class="empty-card">Chưa có lý do ngoại lệ nào.</div>
                <div v-else class="surface-list">
                    <article v-for="reason in reasons" :key="reason.reasonId" class="surface-item">
                        <div class="surface-item-title">{{ reason.reasonCode }}</div>
                        <div class="surface-item-sub">{{ reason.description }}</div>
                        <div class="panel-actions top-gap">
                            <span class="soft-chip">{{ reason.usageCount }} log</span>
                            <button class="btn btn-secondary btn-sm" @click="openReasonModal(reason)">Sửa</button>
                            <button class="btn btn-danger btn-sm" @click="handleDeleteReason(reason)">Xóa</button>
                        </div>
                    </article>
                </div>
            </article>
        </section>

        <transition name="modal">
            <div v-if="showReasonModal" class="modal-overlay" @click.self="closeReasonModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingReasonId ? 'Cập nhật lý do ngoại lệ' : 'Thêm lý do ngoại lệ' }}</h3>
                        <button class="modal-close" @click="closeReasonModal">×</button>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Mã lý do</label>
                            <input v-model="reasonForm.reasonCode" type="text" placeholder="BYPASS_MANUAL" />
                        </div>
                        <div class="form-group">
                            <label>Mô tả</label>
                            <input v-model="reasonForm.description" type="text" placeholder="Mở cổng thủ công..." />
                        </div>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeReasonModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isSaving" @click="handleSaveReason">
                            {{ isSaving ? 'Đang lưu...' : editingReasonId ? 'Lưu thay đổi' : 'Tạo lý do' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getDepartments, getPositions } from '../services/lookupApi'
import {
    createExceptionReason,
    deleteExceptionReason,
    getExceptionReasons,
    updateExceptionReason,
} from '../services/exceptionReasonApi'

const isLoading = ref(true)
const isSaving = ref(false)
const departments = ref([])
const positions = ref([])
const reasons = ref([])

const showReasonModal = ref(false)
const editingReasonId = ref(null)
const formError = ref('')

const reasonForm = reactive({
    reasonCode: '',
    description: '',
})

const usedReasonCount = computed(() => reasons.value.filter((reason) => reason.usageCount > 0).length)

const fetchData = async () => {
    isLoading.value = true
    try {
        const [deptRes, posRes, reasonRes] = await Promise.all([
            getDepartments(),
            getPositions(),
            getExceptionReasons(),
        ])
        departments.value = deptRes.data || []
        positions.value = posRes.data || []
        reasons.value = reasonRes.data || []
    } catch (error) {
        console.error('System catalog load error:', error)
        departments.value = []
        positions.value = []
        reasons.value = []
    } finally {
        isLoading.value = false
    }
}

const openReasonModal = (reason = null) => {
    editingReasonId.value = reason?.reasonId || null
    reasonForm.reasonCode = reason?.reasonCode || ''
    reasonForm.description = reason?.description || ''
    formError.value = ''
    showReasonModal.value = true
}

const closeReasonModal = () => {
    showReasonModal.value = false
    editingReasonId.value = null
    reasonForm.reasonCode = ''
    reasonForm.description = ''
    formError.value = ''
}

const handleSaveReason = async () => {
    if (!reasonForm.reasonCode.trim() || !reasonForm.description.trim()) {
        formError.value = 'Bạn cần nhập cả mã lý do và mô tả.'
        return
    }

    isSaving.value = true
    formError.value = ''
    try {
        const payload = {
            reasonCode: reasonForm.reasonCode.trim(),
            description: reasonForm.description.trim(),
        }

        if (editingReasonId.value) {
            await updateExceptionReason(editingReasonId.value, payload)
        } else {
            await createExceptionReason(payload)
        }

        await fetchData()
        closeReasonModal()
    } catch (error) {
        console.error('Save exception reason error:', error)
        formError.value = error.response?.data?.message || 'Không thể lưu lý do ngoại lệ.'
    } finally {
        isSaving.value = false
    }
}

const handleDeleteReason = async (reason) => {
    const confirmed = window.confirm(`Xóa lý do "${reason.reasonCode}"?`)
    if (!confirmed) return

    try {
        await deleteExceptionReason(reason.reasonId)
        await fetchData()
    } catch (error) {
        console.error('Delete exception reason error:', error)
        window.alert(error.response?.data?.message || 'Không thể xóa lý do ngoại lệ này.')
    }
}

onMounted(fetchData)
</script>

<style scoped>
.top-gap {
    margin-top: 10px;
}

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

.surface-list {
    max-height: 420px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(24, 49, 77, 0.15) transparent;
}

.surface-list::-webkit-scrollbar {
    width: 5px;
}

.surface-list::-webkit-scrollbar-track {
    background: transparent;
}

.surface-list::-webkit-scrollbar-thumb {
    background: rgba(24, 49, 77, 0.15);
    border-radius: 10px;
}

@media (max-width: 1180px) {
    }
</style>
