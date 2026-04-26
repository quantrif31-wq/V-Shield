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

        <div v-if="loadError" class="empty-card error-card">
            {{ loadError }}
        </div>

        <section class="ops-panel ai-engine-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">AI Security Engine</span>
                    <h2 class="panel-title">V-Shield AI – Giám sát an ninh</h2>
                </div>
                <div class="panel-actions">
                    <span class="soft-chip" :class="securityAiStatus.running ? 'success' : 'warn'">
                        {{ securityAiStatus.running ? 'Đang chạy' : 'Đã dừng' }}
                    </span>
                    <span v-if="securityAiStatus.pid" class="soft-chip">PID {{ securityAiStatus.pid }}</span>
                    <button class="btn btn-secondary btn-sm" :disabled="securityBusy" @click="loadSecurityAiStatus">
                        Làm mới
                    </button>
                </div>
            </div>

            <div class="ai-engine-body">
                <div class="ai-engine-controls">
                    <div class="ai-ctrl-section">
                        <h3 class="ai-ctrl-title">Nguồn camera</h3>

                        <div class="form-group">
                            <label>Camera đã cấu hình</label>
                            <select
                                v-model="securitySelectedCameraId"
                                class="filter-select"
                                :disabled="securityBusy || cameras.length === 0"
                            >
                                <option :value="null">Chọn camera</option>
                                <option v-for="camera in cameras" :key="camera.cameraId" :value="camera.cameraId">
                                    #{{ camera.cameraId }} – {{ camera.cameraName }}
                                </option>
                            </select>
                        </div>

                        <div class="ai-source-toggle">
                            <label class="ai-radio-pill" :class="{ active: securitySourceMode === 'camera' }">
                                <input
                                    type="radio"
                                    name="securitySourceMode"
                                    value="camera"
                                    :checked="securitySourceMode === 'camera'"
                                    :disabled="securityBusy"
                                    @change="setSecuritySourceMode('camera')"
                                />
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
                                Camera / RTSP
                            </label>
                            <label class="ai-radio-pill" :class="{ active: securitySourceMode === 'video' }">
                                <input
                                    type="radio"
                                    name="securitySourceMode"
                                    value="video"
                                    :checked="securitySourceMode === 'video'"
                                    :disabled="securityBusy"
                                    @change="setSecuritySourceMode('video')"
                                />
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="15" height="14" rx="2"/><path d="M18 10l3-2v8l-3-2"/></svg>
                                Tệp video
                            </label>
                        </div>

                        <div v-if="securitySourceMode === 'camera'" class="form-group">
                            <label>Chỉ số camera / RTSP URL</label>
                            <input
                                v-model="securityCameraSourceInput"
                                type="text"
                                :disabled="securityBusy"
                                placeholder="0 hoặc rtsp://..."
                                @input="markSecurityCameraSourceEdited"
                            />
                        </div>

                        <div v-else class="form-group">
                            <label>Đường dẫn video</label>
                            <div class="ai-video-input-row">
                                <input
                                    v-model="securityVideoSourceInput"
                                    type="text"
                                    :disabled="securityBusy"
                                    placeholder="C:\DoAnTotNghiep\V-Shield\AI_Project\AI_An_Ninh\test.mp4"
                                />
                                <button
                                    class="btn btn-secondary btn-sm"
                                    :disabled="securityBusy"
                                    @click="triggerVideoPicker"
                                >
                                    Chọn
                                </button>
                            </div>
                            <input
                                ref="securityVideoPicker"
                                type="file"
                                style="display:none"
                                accept="video/*"
                                @change="onVideoFilePicked"
                            />
                        </div>
                    </div>

                    <div class="ai-ctrl-section">
                        <h3 class="ai-ctrl-title">Điều khiển</h3>

                        <div class="ai-action-row">
                            <button class="btn btn-primary" :disabled="securityBusy" @click="handleSecurityStart">
                                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><polygon points="5,3 19,12 5,21"/></svg>
                                Bắt đầu
                            </button>
                            <button class="btn btn-danger" :disabled="securityBusy" @click="stopSecurityAiProcess">
                                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
                                Dừng
                            </button>
                        </div>

                        <label class="ai-checkbox-row">
                            <input v-model="securityLoopVideo" type="checkbox" :disabled="securityBusy || securitySourceMode !== 'video'" />
                            <span>Lặp lại khi hết video</span>
                        </label>

                        <p v-if="securityAiStatus.source" class="ai-source-note">
                            Nguồn: <code>{{ securityAiStatus.source }}</code>
                        </p>
                    </div>

                    <div v-if="securitySourceMode === 'video'" class="ai-ctrl-section">
                        <h3 class="ai-ctrl-title">Tiến trình video</h3>
                        <div class="ai-progress-bar">
                            <input
                                v-model.number="securitySeekFrameValue"
                                class="ai-progress-range"
                                type="range"
                                :min="0"
                                :max="securitySeekMaxFrame"
                                :step="1"
                                :disabled="!securityCanSeek || securitySeekBusy"
                                :style="{ '--ai-progress-percent': `${securityVideoProgressPercent}%` }"
                                @input="onSecuritySeekInput"
                                @change="onSecuritySeekCommit"
                                @mouseup="onSecuritySeekCommit"
                                @touchend="onSecuritySeekCommit"
                            />
                            <span class="ai-progress-text">{{ securityProgressText }}</span>
                        </div>
                    </div>

                    <div v-if="securityError || securityMessage" class="ai-ctrl-section">
                        <div v-if="securityError" class="ai-msg ai-msg-error">{{ securityError }}</div>
                        <div v-else-if="securityMessage" class="ai-msg ai-msg-success">{{ securityMessage }}</div>
                    </div>
                </div>

                <div class="ai-engine-preview">
                    <div class="ai-preview-header">
                        <strong>Khung hình AI An Ninh</strong>
                        <span class="soft-chip" :class="securityAiStatus.running ? 'success' : 'warn'">
                            {{ securityAiStatus.running ? 'Live' : 'Offline' }}
                        </span>
                    </div>
                    <div class="ai-preview-stage">
                        <div v-if="securityAiStatus.running" class="ai-preview-frame-wrap">
                            <img :src="securityFrameUrl" alt="Khung hình AI an ninh" class="ai-preview-frame" />
                            <div class="ai-preview-overlay">
                                <div class="ai-overlay-badge">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                                    {{ securityPersonCount }}
                                </div>
                                <div class="ai-overlay-status" :class="securityPersonCount > 0 ? 'has-person' : ''">
                                    {{ securityPersonCount > 0 ? 'CÓ NGƯỜI' : 'KHÔNG CÓ NGƯỜI' }}
                                </div>
                            </div>
                        </div>
                        <div v-else class="ai-preview-empty">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>
                            <p>AI An Ninh đang dừng</p>
                            <span>Chọn camera hoặc tệp video rồi bấm <strong>Bắt đầu</strong></span>
                        </div>
                    </div>
                    <p class="ai-preview-hint">Nhấn ESC hoặc Q để thoát cửa sổ video. Với tệp video, AI sẽ tự lặp nếu bật tùy chọn.</p>
                </div>
            </div>
        </section>

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
                                <th>Nguồn AI / Preview</th>
                                <th>Biển số gần nhất</th>
                                <th>AI An Ninh</th>
                                <th>Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="camera in paginatedCameras" :key="camera.cameraId">
                                <td>{{ camera.cameraName }}</td>
                                <td>{{ camera.cameraType || '—' }}</td>
                                <td>{{ camera.gateName || 'Chưa gắn cổng' }}</td>
                                <td>
                                    <div class="table-sub mono">{{ camera.streamUrl || 'Chưa có StreamUrl' }}</div>
                                    <div v-if="camera.urlView" class="table-sub mono">Preview: {{ camera.urlView }}</div>
                                </td>
                                <td>
                                    <span v-if="camera.latestPlate" class="plate-pill">{{ camera.latestPlate }}</span>
                                    <span v-else class="table-sub">Chưa có</span>
                                </td>
                                <td>
                                    <div class="ai-cell">
                                        <span v-if="isAiRunningOnCamera(camera.cameraId)" class="soft-chip success">Đang chạy</span>
                                        <button class="btn btn-secondary btn-sm" :disabled="securityBusy" @click="startSecurityAiForCamera(camera.cameraId)">
                                            {{ isAiRunningOnCamera(camera.cameraId) ? 'Chạy lại AI' : 'Bật AI' }}
                                        </button>
                                    </div>
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

                    <div class="form-group">
                        <label>StreamUrl (nguồn cho AI)</label>
                        <input
                            v-model="cameraForm.streamUrl"
                            type="text"
                            placeholder="rtsp://... hoặc http://..."
                        />
                    </div>

                    <div class="form-group">
                        <label>UrlView (preview web, tùy chọn)</label>
                        <input
                            v-model="cameraForm.urlView"
                            type="text"
                            placeholder="http://... hoặc /api/..."
                        />
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
import { onBeforeUnmount, onMounted, reactive, ref, computed, watch } from 'vue'
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
import {
    getSecurityAiFrameUrl,
    getSecurityAiResult,
    seekSecurityAi as seekSecurityAiApi,
    getSecurityAiStatus,
    startSecurityAi as startSecurityAiApi,
    stopSecurityAi as stopSecurityAiApi,
} from '../services/securityAiApi'

const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref('')
const summary = ref({
    camerasConfigured: 0,
    gatesConfigured: 0,
    camerasLinkedToGate: 0,
    unassignedCameras: 0,
})
const cameras = ref([])
const gates = ref([])
const createDefaultSecurityStatus = () => ({ running: false, cameraId: null, source: '', pid: null })
const securityAiStatus = ref(createDefaultSecurityStatus())
const securitySelectedCameraId = ref(null)
const securityBusy = ref(false)
const securityError = ref('')
const securityMessage = ref('')
const securityResult = ref({})
const securitySourceMode = ref('camera')
const securityCameraSourceInput = ref('')
const securityCameraSourceManuallyEdited = ref(false)
const securityVideoSourceInput = ref('C:\\DoAnTotNghiep\\V-Shield\\AI_Project\\AI_An_Ninh\\test.mp4')
const securityLoopVideo = ref(true)
const securityVideoPicker = ref(null)
const securityFrameTick = ref(Date.now())
const securitySeekFrameValue = ref(0)
const securitySeekBusy = ref(false)
const securitySeekDragging = ref(false)
const SECURITY_AI_STATUS_POLL_MS = 2500
const SECURITY_AI_FRAME_TICK_MS = 800
let securityStatusPollTimer = null
let securityFrameTimer = null
const securityResultFailureCount = ref(0)
const securityResultBackoffUntil = ref(0)

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
const selectedSecurityCamera = computed(() =>
    cameras.value.find((camera) => Number(camera.cameraId) === Number(securitySelectedCameraId.value)) || null
)
const securityFrameUrl = computed(() => getSecurityAiFrameUrl(securityFrameTick.value))
const securityPersonCount = computed(() =>
    toFiniteNumber(securityResult.value?.person_count ?? securityAiStatus.value?.person_count ?? 0, 0)
)
const securityCurrentFrameIdx = computed(() =>
    toFiniteNumber(securityAiStatus.value?.current_frame_idx ?? securityResult.value?.current_frame_idx ?? 0, 0)
)
const securityTotalFrames = computed(() =>
    toFiniteNumber(securityAiStatus.value?.total_frames ?? securityResult.value?.total_frames ?? 0, 0)
)
const securityElapsedSeconds = computed(() =>
    toFiniteNumber(securityAiStatus.value?.elapsed_seconds ?? securityResult.value?.elapsed_seconds ?? 0, 0)
)
const securityDurationSeconds = computed(() =>
    toFiniteNumber(securityAiStatus.value?.duration_seconds ?? securityResult.value?.duration_seconds ?? 0, 0)
)
const securitySeekMaxFrame = computed(() => {
    const totalFrames = toFiniteNumber(securityTotalFrames.value, 0)
    return Math.max(0, Math.floor(totalFrames) - 1)
})
const securityIsFileSource = computed(() =>
    String(securityAiStatus.value?.source_type ?? securityResult.value?.source_type ?? '').toLowerCase() === 'file'
)
const securityCanSeek = computed(() =>
    securitySourceMode.value === 'video' &&
    securityIsFileSource.value &&
    securitySeekMaxFrame.value > 0 &&
    Boolean(securityAiStatus.value?.running)
)
const securityVideoProgressPercent = computed(() => {
    if (securityTotalFrames.value <= 1) return 0
    const displayFrame = securitySeekDragging.value ? securitySeekFrameValue.value : securityCurrentFrameIdx.value
    const ratio = (Math.max(0, displayFrame) / Math.max(1, securityTotalFrames.value - 1)) * 100
    return Math.max(0, Math.min(100, ratio))
})
const securityProgressText = computed(() => {
    const displayFrame = securitySeekDragging.value ? securitySeekFrameValue.value : securityCurrentFrameIdx.value
    let elapsedSeconds = securityElapsedSeconds.value
    const durationSeconds = securityDurationSeconds.value

    if (securitySeekDragging.value && securitySeekMaxFrame.value > 0 && durationSeconds > 0) {
        elapsedSeconds = (Math.max(0, displayFrame) / securitySeekMaxFrame.value) * durationSeconds
    }

    if (securityTotalFrames.value > 0) {
        return `${Math.max(0, displayFrame)} / ${Math.max(0, securityTotalFrames.value - 1)} | ${formatDuration(elapsedSeconds)} / ${formatDuration(durationSeconds)}`
    }
    return securityAiStatus.value?.running ? 'Đang xử lý luồng camera...' : '0 / 0 | 00:00 / 00:00'
})

const showCameraModal = ref(false)
const showGateModal = ref(false)
const editingCameraId = ref(null)
const editingGateId = ref(null)
const formError = ref('')

const cameraForm = reactive({
    cameraName: '',
    cameraType: '',
    gateId: '',
    streamUrl: '',
    urlView: '',
})

const gateForm = reactive({
    gateName: '',
    location: '',
})

const getErrorMessage = (error, fallbackMessage) => {
    if (error?.response?.data?.message) return error.response.data.message
    if (typeof error?.response?.data === 'string' && error.response.data.trim()) return error.response.data
    if (error?.message) return error.message
    return fallbackMessage
}

const isTimeoutError = (error, fallbackMessage = '') => {
    const message = String(getErrorMessage(error, fallbackMessage) || '')
    return /timeout/i.test(message)
}

const toFiniteNumber = (value, fallback = 0) => {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
}

const formatDuration = (secondsValue) => {
    const totalSeconds = Number.isFinite(Number(secondsValue)) ? Math.max(0, Math.floor(Number(secondsValue))) : 0
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

const toNullableNumber = (value) => {
    if (value === null || value === undefined || value === '') return null
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
}

const clampSecuritySeekFrame = (value) => {
    const parsed = toFiniteNumber(value, 0)
    if (!Number.isFinite(parsed)) return 0
    const maxFrame = toFiniteNumber(securitySeekMaxFrame.value, 0)
    return Math.max(0, Math.min(maxFrame, Math.floor(parsed)))
}

const syncSecuritySeekFrameValue = ({ force = false } = {}) => {
    if (!force && (securitySeekBusy.value || securitySeekDragging.value)) return
    securitySeekFrameValue.value = clampSecuritySeekFrame(securityCurrentFrameIdx.value)
}

const normalizeSecurityStatus = (payload) => {
    const raw = payload?.status || payload || {}
    const hasCameraEnabled = Object.prototype.hasOwnProperty.call(raw, 'camera_enabled')
    const hasRunning = Object.prototype.hasOwnProperty.call(raw, 'running')
    const running = hasCameraEnabled
        ? Boolean(raw.camera_enabled)
        : hasRunning
            ? Boolean(raw.running)
            : false

    const source = typeof raw.source === 'string'
        ? raw.source
        : typeof raw.ip === 'string'
            ? raw.ip
            : ''

    const cameraId = toNullableNumber(raw.cameraId ?? raw.camera_id)
    const pid = running ? toNullableNumber(raw.pid) : null

    return {
        ...raw,
        running,
        source,
        cameraId,
        pid,
    }
}

const markSecurityCameraSourceEdited = () => {
    securityCameraSourceManuallyEdited.value = true
}

const syncSecuritySourceFromSelectedCamera = ({ force = false } = {}) => {
    if (securitySourceMode.value !== 'camera') return
    const source = selectedSecurityCamera.value?.streamUrl?.trim() || ''
    if (!force && securityCameraSourceManuallyEdited.value) return

    if (!force) {
        const current = securityCameraSourceInput.value?.trim() || ''
        if (current && current !== source) return
    }

    securityCameraSourceInput.value = source
    securityCameraSourceManuallyEdited.value = false
}

const setSecuritySourceMode = (mode) => {
    securitySourceMode.value = mode === 'video' ? 'video' : 'camera'
    if (securitySourceMode.value === 'camera') {
        syncSecuritySourceFromSelectedCamera()
    }
}

const triggerVideoPicker = () => {
    securityVideoPicker.value?.click()
}

const onVideoFilePicked = (event) => {
    const selectedFile = event?.target?.files?.[0]
    if (!selectedFile) return

    const browserPath = String(event?.target?.value || '').replace(/^C:\\fakepath\\/i, '')
    const pickedPath = selectedFile.path || browserPath || selectedFile.name || ''
    if (pickedPath) {
        securityVideoSourceInput.value = pickedPath
    }
}

const ensureSecurityCameraSelection = () => {
    if (!cameras.value.length) {
        securitySelectedCameraId.value = null
        securityCameraSourceInput.value = ''
        securityCameraSourceManuallyEdited.value = false
        return
    }
    const exists = cameras.value.some((camera) => Number(camera.cameraId) === Number(securitySelectedCameraId.value))
    if (!exists) {
        securitySelectedCameraId.value = cameras.value[0].cameraId
        syncSecuritySourceFromSelectedCamera({ force: true })
        return
    }
    syncSecuritySourceFromSelectedCamera()
}

const isAiRunningOnCamera = (cameraId) =>
    Boolean(securityAiStatus.value?.running) &&
    Number(securityAiStatus.value?.cameraId) === Number(cameraId)

const markSecurityResultFetchSuccess = () => {
    securityResultFailureCount.value = 0
    securityResultBackoffUntil.value = 0
}

const markSecurityResultFetchFailure = () => {
    const nextFailureCount = Math.min(6, Number(securityResultFailureCount.value || 0) + 1)
    securityResultFailureCount.value = nextFailureCount
    const delayMs = Math.min(30000, 2000 * (2 ** (nextFailureCount - 1)))
    securityResultBackoffUntil.value = Date.now() + delayMs
}

const loadSecurityAiStatus = async ({ silent = false, syncSourceMode = false } = {}) => {
    try {
        const statusPayload = await getSecurityAiStatus()
        const normalizedStatus = normalizeSecurityStatus(statusPayload)
        securityAiStatus.value = normalizedStatus

        const isRunning = Boolean(normalizedStatus?.running ?? normalizedStatus?.camera_enabled)
        const serviceReachable = normalizedStatus?.serviceReachable !== false
        const now = Date.now()
        const canRequestResult = isRunning &&
            serviceReachable &&
            now >= Number(securityResultBackoffUntil.value || 0)

        if (canRequestResult) {
            try {
                const resultPayload = await getSecurityAiResult()
                securityResult.value = resultPayload || {}
                markSecurityResultFetchSuccess()
            } catch {
                // Keep UI stable and avoid hammering /result when service is unstable.
                markSecurityResultFetchFailure()
            }
        } else if (!isRunning || !serviceReachable) {
            securityResult.value = {}
            if (!isRunning) {
                markSecurityResultFetchSuccess()
            }
        }
        // Chỉ tự đồng bộ source mode khi được yêu cầu rõ ràng (lần đầu load),
        // KHÔNG ghi đè khi user đang chủ động thao tác.
        if (syncSourceMode) {
            const sourceType = String(securityAiStatus.value?.source_type || securityResult.value?.source_type || '').toLowerCase()
            if (sourceType === 'file') {
                securitySourceMode.value = 'video'
            } else if (sourceType === 'rtsp' || sourceType === 'webcam') {
                securitySourceMode.value = 'camera'
            }
        }
        securityError.value = ''
    } catch (error) {
        securityAiStatus.value = createDefaultSecurityStatus()
        securityResult.value = {}
        if (!silent) {
            securityError.value = getErrorMessage(error, 'Không tải được trạng thái AI An Ninh.')
        }
    }
}

const handleStartTimeoutFallback = async (error, fallbackMessage) => {
    if (!isTimeoutError(error, fallbackMessage)) {
        securityError.value = getErrorMessage(error, fallbackMessage)
        return
    }

    await loadSecurityAiStatus({ silent: true })
    if (securityAiStatus.value?.running) {
        securityError.value = ''
        securityMessage.value = 'Lệnh bật bị chậm phản hồi, nhưng AI đã chạy. Trạng thái đã tự đồng bộ.'
        securityFrameTick.value = Date.now()
        return
    }

    securityError.value = 'Khởi động AI bị timeout. Kiểm tra lại link RTSP hoặc kết nối camera rồi bấm Bắt đầu lại.'
}

const startSecurityAiForCamera = async (cameraId) => {
    securitySourceMode.value = 'camera'

    const manualSource = securityCameraSourceInput.value?.trim()
    if (cameraId !== null && cameraId !== undefined && cameraId !== '') {
        securitySelectedCameraId.value = cameraId
    } else if (!manualSource) {
        securityError.value = 'Vui lòng chọn camera hoặc nhập RTSP URL trước khi bật AI An Ninh.'
        securityMessage.value = ''
        return
    }

    const selectedCamera = cameras.value.find((camera) => Number(camera.cameraId) === Number(securitySelectedCameraId.value))
    const selectedCameraSource = selectedCamera?.streamUrl?.trim() || ''
    const sourceToStart = manualSource || selectedCameraSource
    if (!sourceToStart) {
        securityError.value = 'Không có nguồn camera hợp lệ để bật AI. Nhập RTSP URL hoặc cấu hình StreamUrl cho camera.'
        securityMessage.value = ''
        return
    }

    securityBusy.value = true
    securityError.value = ''
    securityMessage.value = ''
    try {
        const response = await startSecurityAiApi({
            cameraId: toNullableNumber(securitySelectedCameraId.value),
            source: sourceToStart,
            restartIfRunning: true,
            loopVideo: securityLoopVideo.value,
        })
        securityAiStatus.value = normalizeSecurityStatus(response)
        securityFrameTick.value = Date.now()
        securityMessage.value = response?.message || 'Đã bật AI An Ninh.'
    } catch (error) {
        await handleStartTimeoutFallback(error, 'Không bật được AI An Ninh cho camera này.')
    } finally {
        securityBusy.value = false
        await loadSecurityAiStatus({ silent: true })
    }
}

const startSecurityAiForSelected = async () => {
    securitySourceMode.value = 'camera'
    await startSecurityAiForCamera(securitySelectedCameraId.value)
}

const startSecurityAiForVideo = async () => {
    const source = securityVideoSourceInput.value?.trim()
    if (!source) {
        securityError.value = 'Vui lòng nhập đường dẫn tệp video trước khi chạy AI.'
        securityMessage.value = ''
        return
    }

    securityBusy.value = true
    securityError.value = ''
    securityMessage.value = ''
    try {
        const response = await startSecurityAiApi({
            source,
            restartIfRunning: true,
            loopVideo: securityLoopVideo.value,
        })
        securityAiStatus.value = normalizeSecurityStatus(response)
        securityFrameTick.value = Date.now()
        securityMessage.value = response?.message || 'Đã bật AI An Ninh bằng tệp video.'
    } catch (error) {
        await handleStartTimeoutFallback(error, 'Không bật được AI An Ninh bằng tệp video.')
    } finally {
        securityBusy.value = false
        await loadSecurityAiStatus({ silent: true })
    }
}

const stopSecurityAiProcess = async () => {
    securityBusy.value = true
    securityError.value = ''
    securityMessage.value = ''
    try {
        const response = await stopSecurityAiApi()
        securityAiStatus.value = normalizeSecurityStatus(response)
        securityMessage.value = response?.message || 'Đã dừng AI An Ninh.'
    } catch (error) {
        securityError.value = getErrorMessage(error, 'Không dừng được AI An Ninh.')
    } finally {
        securityBusy.value = false
        await loadSecurityAiStatus({ silent: true })
    }
}

const handleSecurityStart = async () => {
    if (securitySourceMode.value === 'camera') {
        await startSecurityAiForSelected()
        return
    }
    await startSecurityAiForVideo()
}

const onSecuritySeekInput = () => {
    securitySeekDragging.value = true
}

const onSecuritySeekCommit = async () => {
    if (securitySeekBusy.value) return
    securitySeekDragging.value = false

    if (!securityCanSeek.value) {
        syncSecuritySeekFrameValue({ force: true })
        return
    }

    const targetFrame = clampSecuritySeekFrame(securitySeekFrameValue.value)
    securitySeekFrameValue.value = targetFrame

    const currentFrame = clampSecuritySeekFrame(securityCurrentFrameIdx.value)
    if (targetFrame === currentFrame) return

    securitySeekBusy.value = true
    securityError.value = ''
    try {
        const response = await seekSecurityAiApi(targetFrame)
        if (response?.status) {
            securityAiStatus.value = normalizeSecurityStatus(response.status)
        }
        securityFrameTick.value = Date.now()
        await loadSecurityAiStatus({ silent: true })
    } catch (error) {
        securityError.value = getErrorMessage(error, 'Không tua được video AI.')
    } finally {
        securitySeekBusy.value = false
        syncSecuritySeekFrameValue({ force: true })
    }
}

const fetchOverview = async () => {
    isLoading.value = true
    loadError.value = ''
    try {
        const { data } = await getDeviceOverview()
        summary.value = { ...summary.value, ...(data.summary || {}) }
        cameras.value = data.cameras || []
        gates.value = data.gates || []
        ensureSecurityCameraSelection()
        cameraCurrentPage.value = 1
        gateCurrentPage.value = 1
    } catch (error) {
        console.error('Device overview error:', error)
        cameras.value = []
        gates.value = []
        loadError.value = getErrorMessage(error, 'Không thể tải cấu hình camera/cổng. Hãy kiểm tra API backend.')
    } finally {
        isLoading.value = false
    }
}

const openCameraModal = (camera = null) => {
    editingCameraId.value = camera?.cameraId || null
    cameraForm.cameraName = camera?.cameraName || ''
    cameraForm.cameraType = camera?.cameraType || ''
    cameraForm.gateId = camera?.gateId || ''
    cameraForm.streamUrl = camera?.streamUrl || ''
    cameraForm.urlView = camera?.urlView || ''
    formError.value = ''
    showCameraModal.value = true
}

const closeCameraModal = () => {
    showCameraModal.value = false
    editingCameraId.value = null
    cameraForm.cameraName = ''
    cameraForm.cameraType = ''
    cameraForm.gateId = ''
    cameraForm.streamUrl = ''
    cameraForm.urlView = ''
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
            streamUrl: cameraForm.streamUrl?.trim() || null,
            urlView: cameraForm.urlView?.trim() || null,
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

onMounted(async () => {
    await fetchOverview()
    await loadSecurityAiStatus({ syncSourceMode: true })
    syncSecuritySeekFrameValue({ force: true })
    securityStatusPollTimer = window.setInterval(() => {
        if (!securityBusy.value) {
            loadSecurityAiStatus({ silent: true })
        }
    }, SECURITY_AI_STATUS_POLL_MS)
    securityFrameTimer = window.setInterval(() => {
        if (securityAiStatus.value?.running) {
            securityFrameTick.value = Date.now()
        }
    }, SECURITY_AI_FRAME_TICK_MS)
})

onBeforeUnmount(() => {
    if (securityStatusPollTimer) {
        window.clearInterval(securityStatusPollTimer)
        securityStatusPollTimer = null
    }
    if (securityFrameTimer) {
        window.clearInterval(securityFrameTimer)
        securityFrameTimer = null
    }
})

watch(securitySelectedCameraId, (nextCameraId, previousCameraId) => {
    if (Number(nextCameraId) === Number(previousCameraId)) return
    if (!securityCameraSourceManuallyEdited.value) {
        syncSecuritySourceFromSelectedCamera({ force: true })
    }
})

watch(cameras, () => {
    ensureSecurityCameraSelection()
})

watch([securityCurrentFrameIdx, securitySeekMaxFrame], () => {
    syncSecuritySeekFrameValue()
})

watch([securitySourceMode, securityCanSeek], () => {
    syncSecuritySeekFrameValue({ force: true })
})
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

/* ── AI Engine Panel ── */
.ai-engine-panel {
    display: grid;
    gap: 16px;
    margin-bottom: 20px;
}

.ai-engine-body {
    display: grid;
    grid-template-columns: minmax(300px, 1fr) minmax(0, 1.4fr);
    gap: 18px;
}

.ai-engine-controls {
    display: grid;
    gap: 16px;
    align-content: start;
}

.ai-ctrl-section {
    padding: 16px;
    border-radius: 18px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
    display: grid;
    gap: 12px;
}

.ai-ctrl-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.ai-source-toggle {
    display: flex;
    gap: 8px;
}

.ai-radio-pill {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 14px;
    border: 1px solid rgba(24, 49, 77, 0.10);
    background: rgba(255, 255, 255, 0.5);
    color: var(--text-secondary);
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}

.ai-radio-pill input {
    display: none;
}

.ai-radio-pill svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
}

.ai-radio-pill.active {
    background: var(--accent-primary);
    color: #fff;
    border-color: var(--accent-primary);
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22);
}

.ai-radio-pill:hover:not(.active) {
    background: rgba(236, 244, 246, 0.92);
    border-color: rgba(24, 49, 77, 0.16);
}

.ai-video-input-row {
    display: flex;
    gap: 8px;
}

.ai-video-input-row input {
    flex: 1;
    min-width: 0;
}

.ai-action-row {
    display: flex;
    gap: 10px;
}

.ai-action-row .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.ai-action-row .btn svg {
    width: 14px;
    height: 14px;
}

.ai-checkbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.86rem;
    color: var(--text-secondary);
    cursor: pointer;
}

.ai-checkbox-row input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: var(--accent-primary);
}

.ai-source-note {
    margin: 0;
    font-size: 0.82rem;
    color: var(--text-muted);
}

.ai-source-note code {
    padding: 2px 6px;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.06);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    word-break: break-all;
}

.ai-progress-bar {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: center;
}

.ai-progress-range {
    --ai-progress-percent: 0%;
    appearance: none;
    width: 100%;
    height: 10px;
    border-radius: 999px;
    border: 0;
    outline: none;
    cursor: pointer;
    background:
        linear-gradient(90deg, var(--accent-primary), #60a5fa) 0 0 / var(--ai-progress-percent) 100% no-repeat,
        rgba(24, 49, 77, 0.08);
}

.ai-progress-range:disabled {
    cursor: not-allowed;
    opacity: 0.65;
}

.ai-progress-range::-webkit-slider-runnable-track {
    height: 10px;
    border-radius: 999px;
    background: transparent;
}

.ai-progress-range::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid #fff;
    background: var(--accent-primary);
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.25);
    margin-top: -3px;
}

.ai-progress-range::-moz-range-track {
    height: 10px;
    border-radius: 999px;
    background: transparent;
}

.ai-progress-range::-moz-range-thumb {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid #fff;
    background: var(--accent-primary);
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.25);
}

.ai-progress-text {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}

.ai-msg {
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.86rem;
    font-weight: 600;
}

.ai-msg-error {
    background: rgba(255, 239, 236, 0.9);
    color: var(--accent-danger);
    border: 1px solid rgba(195, 81, 70, 0.18);
}

.ai-msg-success {
    background: rgba(236, 252, 243, 0.9);
    color: var(--accent-success);
    border: 1px solid rgba(22, 163, 74, 0.18);
}

/* ── AI Engine Preview ── */
.ai-engine-preview {
    display: grid;
    gap: 12px;
    align-content: start;
}

.ai-preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.ai-preview-header strong {
    font-size: 0.92rem;
    color: var(--text-primary);
}

.ai-preview-stage {
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: radial-gradient(circle at top left, rgba(31, 94, 143, 0.18), transparent 48%),
                linear-gradient(140deg, #0f172a, #12263f 60%, #17324d);
    min-height: 340px;
}

.ai-preview-frame-wrap {
    position: relative;
}

.ai-preview-frame {
    width: 100%;
    display: block;
    min-height: 340px;
    object-fit: contain;
    background: rgba(15, 23, 42, 0.92);
}

.ai-preview-overlay {
    position: absolute;
    top: 14px;
    left: 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.ai-overlay-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.78);
    backdrop-filter: blur(8px);
    color: #e2e8f0;
    font-size: 0.92rem;
    font-weight: 700;
    font-family: var(--font-heading);
    width: fit-content;
}

.ai-overlay-badge svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
}

.ai-overlay-status {
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.62);
    backdrop-filter: blur(8px);
    color: rgba(191, 209, 229, 0.88);
    font-size: 0.78rem;
    font-weight: 600;
    width: fit-content;
}

.ai-overlay-status.has-person {
    background: rgba(22, 163, 74, 0.28);
    color: #86efac;
}

.ai-preview-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    min-height: 340px;
    color: rgba(191, 209, 229, 0.72);
    text-align: center;
    padding: 30px;
}

.ai-preview-empty svg {
    opacity: 0.4;
}

.ai-preview-empty p {
    font-size: 1rem;
    font-weight: 600;
    color: rgba(226, 232, 240, 0.88);
    margin: 0;
}

.ai-preview-empty span {
    font-size: 0.84rem;
    color: rgba(191, 209, 229, 0.7);
}

.ai-preview-hint {
    margin: 0;
    font-size: 0.78rem;
    color: var(--text-muted);
    line-height: 1.5;
}

.ai-cell {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }

    .ai-engine-body {
        grid-template-columns: 1fr;
    }

    .ai-progress-bar {
        grid-template-columns: 1fr;
    }

    .ai-progress-text {
        text-align: left;
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
