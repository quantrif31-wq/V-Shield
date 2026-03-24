<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">AI devices</span>
                <h1 class="page-title">Quản lý camera, cổng và nguồn stream để các luồng giám sát luôn nối đúng điểm.</h1>
                <p class="page-subtitle">
                    Trang này gồm hai lớp cấu hình: mạng lưới stream thực tế từ IP Webcam hoặc IP Camera Lite, và danh mục
                    camera/cổng đang lưu trong cơ sở dữ liệu để map đúng vào nghiệp vụ ra vào.
                </p>
                <div class="hero-actions">
                    <button class="btn btn-primary" @click="openCameraModal()">Thêm camera</button>
                    <button class="btn btn-secondary" @click="openGateModal()">Thêm cổng</button>
                </div>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Thiết bị đã cấu hình</span>
                        <strong>{{ summary.camerasConfigured }} camera</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        Device topology
                    </span>
                </div>
                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Cổng</span>
                        <strong>{{ summary.gatesConfigured }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Đã gắn cổng</span>
                        <strong>{{ summary.camerasLinkedToGate }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Chưa gắn</span>
                        <strong>{{ summary.unassignedCameras }}</strong>
                    </div>
                </div>
            </div>
        </section>

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
                            <tr v-for="camera in cameras" :key="camera.cameraId">
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
                            <tr v-for="gate in gates" :key="gate.gateId">
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
import { onMounted, reactive, ref } from 'vue'
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
.aside-head,
.aside-metrics {
    display: grid;
    gap: 14px;
}

.aside-head {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
}

.aside-label {
    color: rgba(215, 251, 255, 0.72);
    font-size: 0.76rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.aside-head strong {
    font-family: var(--font-heading);
    font-size: 1.4rem;
    line-height: 1.35;
}

.aside-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(84, 196, 211, 0.14);
    color: #c0fbff;
    font-size: 0.76rem;
    font-weight: 700;
}

.aside-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #5de3c7;
}

.aside-metrics {
    margin-top: 12px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.aside-metric {
    padding: 16px 14px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.aside-metric span {
    color: rgba(215, 251, 255, 0.76);
    font-size: 0.74rem;
}

.aside-metric strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-family: var(--font-heading);
    font-size: 1.14rem;
}

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
</style>
