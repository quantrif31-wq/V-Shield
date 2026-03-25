<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">AI devices</span>
                <h1 class="page-title">Quản lý camera & cổng</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openCameraModal()">Thêm camera</button>
                <button class="btn btn-secondary" @click="openGateModal()">Thêm cổng</button>
            </div>
        </div>

        <CameraNetworkPanel />

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Cameras</span>
                        <h2 class="panel-title">Danh sách camera</h2>
                    </div>
                    <button class="btn btn-secondary btn-sm" @click="openCameraModal()">Thêm camera</button>
                </div>

                <div v-if="isLoading" class="empty-card">Đang tải cấu hình camera...</div>
                <div v-else-if="cameras.length === 0" class="empty-card">Chưa có camera nào trong hệ thống.</div>
                <div v-else class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Tên camera</th>
                                <th>Loại</th>
                                <th>Cổng</th>
                                <th>Biển số gần nhất</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="camera in paginatedCameras" :key="camera.cameraId">
                                <td>{{ camera.cameraName }}</td>
                                <td>{{ camera.cameraType || '—' }}</td>
                                <td>{{ camera.gateName || 'Chưa gắn cổng' }}</td>
                                <td>
                                    <span v-if="camera.latestPlate" class="plate-pill">{{ camera.latestPlate }}</span>
                                    <span v-else class="table-sub">Chưa có</span>
                                </td>
                                <td>
                                    <div class="panel-actions">
                                        <button class="btn btn-secondary btn-sm" @click="openCameraModal(camera)">Sửa</button>
                                        <button class="btn btn-danger btn-sm" @click="handleDeleteCamera(camera)">Xóa</button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <!-- Camera Pagination -->
                <div v-if="!isLoading && cameras.length > 0" class="pagination-bar">
                    <span>Hiển thị {{ camPagStart }}–{{ camPagEnd }} / {{ cameras.length }}</span>
                    <div class="page-buttons">
                        <button class="page-btn" :disabled="cameraCurrentPage <= 1" @click="cameraCurrentPage--">‹</button>
                        <button class="page-btn" disabled>{{ cameraCurrentPage }} / {{ cameraTotalPages }}</button>
                        <button class="page-btn" :disabled="cameraCurrentPage >= cameraTotalPages" @click="cameraCurrentPage++">›</button>
                    </div>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Gates</span>
                        <h2 class="panel-title">Danh sách cổng</h2>
                    </div>
                    <button class="btn btn-secondary btn-sm" @click="openGateModal()">Thêm cổng</button>
                </div>

                <div v-if="isLoading" class="empty-card">Đang tải cấu hình cổng...</div>
                <div v-else-if="gates.length === 0" class="empty-card">Chưa có cổng nào trong hệ thống.</div>
                <div v-else class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Cổng</th>
                                <th>Vị trí</th>
                                <th>Camera</th>
                                <th>Log liên quan</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="gate in paginatedGates" :key="gate.gateId">
                                <td>{{ gate.gateName }}</td>
                                <td>{{ gate.location || '—' }}</td>
                                <td>{{ gate.cameraCount }}</td>
                                <td>{{ gate.accessLogCount }}</td>
                                <td>
                                    <div class="panel-actions">
                                        <button class="btn btn-secondary btn-sm" @click="openGateModal(gate)">Sửa</button>
                                        <button class="btn btn-danger btn-sm" @click="handleDeleteGate(gate)">Xóa</button>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <!-- Gate Pagination -->
                <div v-if="!isLoading && gates.length > 0" class="pagination-bar">
                    <span>Hiển thị {{ gatePagStart }}–{{ gatePagEnd }} / {{ gates.length }}</span>
                    <div class="page-buttons">
                        <button class="page-btn" :disabled="gateCurrentPage <= 1" @click="gateCurrentPage--">‹</button>
                        <button class="page-btn" disabled>{{ gateCurrentPage }} / {{ gateTotalPages }}</button>
                        <button class="page-btn" :disabled="gateCurrentPage >= gateTotalPages" @click="gateCurrentPage++">›</button>
                    </div>
                </div>
            </article>
        </section>

        <transition name="modal">
            <div v-if="showCameraModal" class="modal-overlay" @click.self="closeCameraModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingCameraId ? 'Cập nhật camera' : 'Thêm camera' }}</h3>
                        <button class="modal-close" @click="closeCameraModal">×</button>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Tên camera</label>
                            <input v-model="cameraForm.cameraName" type="text" placeholder="Camera cổng A" />
                        </div>
                        <div class="form-group">
                            <label>Loại camera</label>
                            <input v-model="cameraForm.cameraType" type="text" placeholder="ANPR / Face / Overview" />
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Gắn vào cổng</label>
                        <select v-model="cameraForm.gateId" class="filter-select">
                            <option value="">Chưa gắn cổng</option>
                            <option v-for="gate in gates" :key="gate.gateId" :value="gate.gateId">{{ gate.gateName }}</option>
                        </select>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeCameraModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isSaving" @click="handleSaveCamera">
                            {{ isSaving ? 'Đang lưu...' : editingCameraId ? 'Lưu thay đổi' : 'Tạo camera' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>

        <transition name="modal">
            <div v-if="showGateModal" class="modal-overlay" @click.self="closeGateModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingGateId ? 'Cập nhật cổng' : 'Thêm cổng' }}</h3>
                        <button class="modal-close" @click="closeGateModal">×</button>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Tên cổng</label>
                            <input v-model="gateForm.gateName" type="text" placeholder="Cổng A" />
                        </div>
                        <div class="form-group">
                            <label>Vị trí</label>
                            <input v-model="gateForm.location" type="text" placeholder="Khối văn phòng / bãi xe..." />
                        </div>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeGateModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isSaving" @click="handleSaveGate">
                            {{ isSaving ? 'Đang lưu...' : editingGateId ? 'Lưu thay đổi' : 'Tạo cổng' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import CameraNetworkPanel from '../components/CameraNetworkPanel.vue'
import {
    createCamera,
    createGate,
    deleteCamera,
    deleteGate,
    getDeviceOverview,
    updateCamera,
    updateGate,
} from '../services/deviceManagementApi'

const isLoading = ref(true)
const isSaving = ref(false)
const summary = ref({
    camerasConfigured: 0,
    gatesConfigured: 0,
    camerasLinkedToGate: 0,
    unassignedCameras: 0,
})
const cameras = ref([])
const gates = ref([])

// Pagination
const itemsPerPage = 4

const cameraCurrentPage = ref(1)
const cameraTotalPages = computed(() => Math.max(1, Math.ceil(cameras.value.length / itemsPerPage)))
const paginatedCameras = computed(() => {
    const start = (cameraCurrentPage.value - 1) * itemsPerPage
    return cameras.value.slice(start, start + itemsPerPage)
})
const camPagStart = computed(() => cameras.value.length === 0 ? 0 : (cameraCurrentPage.value - 1) * itemsPerPage + 1)
const camPagEnd = computed(() => Math.min(cameraCurrentPage.value * itemsPerPage, cameras.value.length))

const gateCurrentPage = ref(1)
const gateTotalPages = computed(() => Math.max(1, Math.ceil(gates.value.length / itemsPerPage)))
const paginatedGates = computed(() => {
    const start = (gateCurrentPage.value - 1) * itemsPerPage
    return gates.value.slice(start, start + itemsPerPage)
})
const gatePagStart = computed(() => gates.value.length === 0 ? 0 : (gateCurrentPage.value - 1) * itemsPerPage + 1)
const gatePagEnd = computed(() => Math.min(gateCurrentPage.value * itemsPerPage, gates.value.length))

const showCameraModal = ref(false)
const showGateModal = ref(false)
const editingCameraId = ref(null)
const editingGateId = ref(null)
const formError = ref('')

const cameraForm = reactive({
    cameraName: '',
    cameraType: '',
    gateId: '',
})

const gateForm = reactive({
    gateName: '',
    location: '',
})

const fetchOverview = async () => {
    isLoading.value = true
    try {
        const { data } = await getDeviceOverview()
        summary.value = { ...summary.value, ...(data.summary || {}) }
        cameras.value = data.cameras || []
        gates.value = data.gates || []
        cameraCurrentPage.value = 1
        gateCurrentPage.value = 1
    } catch (error) {
        console.error('Device overview error:', error)
        cameras.value = []
        gates.value = []
    } finally {
        isLoading.value = false
    }
}

const openCameraModal = (camera = null) => {
    editingCameraId.value = camera?.cameraId || null
    cameraForm.cameraName = camera?.cameraName || ''
    cameraForm.cameraType = camera?.cameraType || ''
    cameraForm.gateId = camera?.gateId || ''
    formError.value = ''
    showCameraModal.value = true
}

const closeCameraModal = () => {
    showCameraModal.value = false
    editingCameraId.value = null
    cameraForm.cameraName = ''
    cameraForm.cameraType = ''
    cameraForm.gateId = ''
    formError.value = ''
}

const openGateModal = (gate = null) => {
    editingGateId.value = gate?.gateId || null
    gateForm.gateName = gate?.gateName || ''
    gateForm.location = gate?.location || ''
    formError.value = ''
    showGateModal.value = true
}

const closeGateModal = () => {
    showGateModal.value = false
    editingGateId.value = null
    gateForm.gateName = ''
    gateForm.location = ''
    formError.value = ''
}

const handleSaveCamera = async () => {
    if (!cameraForm.cameraName.trim()) {
        formError.value = 'Tên camera là bắt buộc.'
        return
    }

    isSaving.value = true
    formError.value = ''
    try {
        const payload = {
            cameraName: cameraForm.cameraName.trim(),
            cameraType: cameraForm.cameraType || null,
            gateId: cameraForm.gateId || null,
        }

        if (editingCameraId.value) {
            await updateCamera(editingCameraId.value, payload)
        } else {
            await createCamera(payload)
        }

        await fetchOverview()
        closeCameraModal()
    } catch (error) {
        console.error('Save camera error:', error)
        formError.value = error.response?.data?.message || 'Không thể lưu camera.'
    } finally {
        isSaving.value = false
    }
}

const handleSaveGate = async () => {
    if (!gateForm.gateName.trim()) {
        formError.value = 'Tên cổng là bắt buộc.'
        return
    }

    isSaving.value = true
    formError.value = ''
    try {
        const payload = {
            gateName: gateForm.gateName.trim(),
            location: gateForm.location || null,
        }

        if (editingGateId.value) {
            await updateGate(editingGateId.value, payload)
        } else {
            await createGate(payload)
        }

        await fetchOverview()
        closeGateModal()
    } catch (error) {
        console.error('Save gate error:', error)
        formError.value = error.response?.data?.message || 'Không thể lưu cổng.'
    } finally {
        isSaving.value = false
    }
}

const handleDeleteCamera = async (camera) => {
    const confirmed = window.confirm(`Xóa camera "${camera.cameraName}"?`)
    if (!confirmed) return

    try {
        await deleteCamera(camera.cameraId)
        await fetchOverview()
    } catch (error) {
        console.error('Delete camera error:', error)
        window.alert(error.response?.data?.message || 'Không thể xóa camera này.')
    }
}

const handleDeleteGate = async (gate) => {
    const confirmed = window.confirm(`Xóa cổng "${gate.gateName}"?`)
    if (!confirmed) return

    try {
        await deleteGate(gate.gateId)
        await fetchOverview()
    } catch (error) {
        console.error('Delete gate error:', error)
        window.alert(error.response?.data?.message || 'Không thể xóa cổng này.')
    }
}

onMounted(fetchOverview)
</script>

<style scoped>


.plate-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(236, 244, 246, 0.92);
    border: 1px solid rgba(24, 49, 77, 0.12);
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 0.84rem;
    font-weight: 700;
}

.table-sub {
    color: var(--text-muted);
    font-size: 0.82rem;
}

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }
}

/* Pagination */
.pagination-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    border-top: 1px solid var(--border-color);
    font-size: 0.85rem;
    color: var(--text-secondary);
    background: transparent;
}
.page-buttons {
    display: flex;
    gap: 4px;
}
.page-btn {
    width: auto;
    min-width: 28px;
    height: 28px;
    padding: 0 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background: var(--bg-card);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.85rem;
}
.page-btn:hover:not(:disabled) {
    background: var(--bg-input);
    color: var(--text-primary);
}
.page-btn:disabled {
    opacity: 0.5;
    cursor: default;
    background: transparent;
    border-color: transparent;
}
</style>
