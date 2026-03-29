<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Live monitoring</span>
                <h1 class="page-title">Giám sát trực tiếp</h1>
            </div>
            <div class="header-actions">
                <router-link to="/device-management" class="btn btn-primary">Quản lý camera & cổng</router-link>
                <router-link to="/exceptions" class="btn btn-secondary">Xem ngoại lệ</router-link>
            </div>
        </div>

        <section class="metric-grid">
            <article class="metric-tile">
                <span class="metric-label">Camera đã cấu hình</span>
                <strong class="metric-value">{{ summary.camerasConfigured }}</strong>
                <span class="metric-note">Đọc từ bảng <code>Camera</code> trong hệ thống.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Cổng đang quản lý</span>
                <strong class="metric-value">{{ summary.gatesConfigured }}</strong>
                <span class="metric-note">Số vị trí cổng đang được khai báo.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera có gắn cổng</span>
                <strong class="metric-value">{{ summary.camerasLinkedToGate }}</strong>
                <span class="metric-note">Các camera đã liên kết đúng điểm truy cập.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera chưa gắn cổng</span>
                <strong class="metric-value">{{ summary.unassignedCameras }}</strong>
                <span class="metric-note">Cần kiểm tra lại cấu hình thiết bị.</span>
            </article>
        </section>

        <section class="ops-panel local-preview-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Local camera previews</span>
                    <h2 class="panel-title">Preview từ cấu hình local</h2>
                </div>
                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" @click="loadLocalCameraSettings">Tải lại preview</button>
                    <router-link to="/device-management" class="btn btn-primary btn-sm">Sửa cấu hình</router-link>
                </div>
            </div>

            <div v-if="localPreviewCameras.length" class="local-preview-grid">
                <article v-for="camera in localPreviewCameras" :key="camera.id" class="local-preview-card">
                    <div class="camera-card-head">
                        <div>
                            <strong>{{ camera.label || camera.name }}</strong>
                            <span>{{ camera.location || camera.name }}</span>
                        </div>
                        <span class="soft-chip" :class="getLocalCameraChipClass(camera)">
                            {{ getLocalCameraChipText(camera) }}
                        </span>
                    </div>

                    <StreamPreview :url="resolveCameraPreviewUrl(camera)" :label="camera.label || camera.name" />

                    <div class="chip-row">
                        <span class="soft-chip">{{ camera.name }}</span>
                        <span v-if="camera.url" class="soft-chip" :class="isRtspCameraUrl(camera.url) ? 'warn' : 'success'">
                            {{ isRtspCameraUrl(camera.url) ? 'RTSP source' : 'HTTP source' }}
                        </span>
                        <span v-if="camera.previewUrl" class="soft-chip success">Preview web</span>
                    </div>

                    <div class="source-list">
                        <p v-if="camera.url" class="surface-item-sub mono">
                            AI/source: {{ camera.url }}
                        </p>
                        <p v-if="camera.previewUrl" class="surface-item-sub mono">
                            Preview: {{ camera.previewUrl }}
                        </p>
                        <p v-else class="surface-item-sub">
                            Chưa có Preview URL cho browser. Nếu slot này chỉ có RTSP, web sẽ hiện thông báo thay vì video.
                        </p>
                    </div>
                </article>
            </div>
            <div v-else class="empty-card">
                Chưa có camera local nào được bật trong trình duyệt này. Hãy vào Quản lý camera để thêm RTSP và Preview
                URL.
            </div>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Configured cameras</span>
                        <h2 class="panel-title">Camera & điểm đặt</h2>
                    </div>
                    <router-link to="/device-management" class="btn btn-secondary btn-sm">Mở cấu hình</router-link>
                </div>

                <div v-if="cameras.length" class="camera-grid scrollable-panel">
                    <article v-for="camera in displayedCameras" :key="camera.cameraId" class="camera-card">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ camera.cameraName }}</strong>
                                <span>{{ camera.gateName || "Chưa gắn cổng" }}</span>
                            </div>
                            <span class="soft-chip" :class="camera.gateId ? 'success' : 'warn'">
                                {{ camera.cameraType || "Không rõ loại" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ camera.accessLogCount }} log</span>
                            <span v-if="camera.latestPlate" class="soft-chip success">{{ camera.latestPlate }}</span>
                            <span v-else class="soft-chip warn">Chưa có biển số</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ camera.gateLocation || "Chưa có vị trí cổng" }}
                            <template v-if="camera.lastAccessAt">
                                - hoạt động gần nhất {{ formatDateTime(camera.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                    <div v-if="cameras.length > maxCameras" class="show-more-hint">
                        Hiển thị {{ maxCameras }}/{{ cameras.length }} camera. Vào
                        <router-link to="/device-management">Quản lý thiết bị</router-link> để xem tất cả.
                    </div>
                </div>
                <div v-else class="empty-card">Chưa có camera nào trong cơ sở dữ liệu.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Plate recognition</span>
                        <h2 class="panel-title">Biển số nhận diện gần nhất</h2>
                    </div>
                </div>

                <div v-if="recentPlates.length" class="surface-list scrollable-panel">
                    <article v-for="plate in displayedPlates" :key="`${plate.cameraIP}-${plate.plateNumber}-${plate.lastUpdate}`" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ plate.plateNumber }}</strong>
                                <span>{{ plate.cameraIP }}</span>
                            </div>
                            <span class="soft-chip success">{{ formatTime(plate.lastUpdate) }}</span>
                        </div>
                        <p class="surface-item-sub">
                            Bản ghi biển số mới nhất từ camera, dùng để đối soát nhanh với dòng ra vào.
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có dữ liệu nhận diện biển số gần đây.</div>
            </article>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Face & access</span>
                        <h2 class="panel-title">Dòng xác minh khuôn mặt gần nhất</h2>
                    </div>
                    <router-link to="/access-logs" class="btn btn-secondary btn-sm">Mở nhật ký</router-link>
                </div>

                <div v-if="recentActivities.length" class="surface-list scrollable-panel">
                    <article v-for="activity in displayedActivities" :key="activity.logId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ activity.actorName }}</strong>
                                <span>{{ activity.gateName || "Chưa gắn cổng" }}</span>
                            </div>
                            <span class="soft-chip" :class="activity.direction === 'IN' ? 'success' : 'warn'">
                                {{ activity.direction === "IN" ? "Vào" : "Ra" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span v-if="activity.capturedLicensePlate" class="soft-chip">{{ activity.capturedLicensePlate }}</span>
                            <span v-if="activity.resultStatus" class="soft-chip">{{ activity.resultStatus }}</span>
                            <span v-if="activity.isBypass" class="soft-chip danger">BYPASS</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ activity.cameraName || "Không có camera" }} - {{ formatDateTime(activity.timestamp) }}
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có log nhận diện nào gần đây.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Gate posture</span>
                        <h2 class="panel-title">Tình trạng cổng truy cập</h2>
                    </div>
                </div>

                <div v-if="gates.length" class="surface-list scrollable-panel">
                    <article v-for="gate in displayedGates" :key="gate.gateId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ gate.gateName }}</strong>
                                <span>{{ gate.location || "Chưa có vị trí" }}</span>
                            </div>
                            <span class="soft-chip">{{ gate.cameraCount }} camera</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ gate.accessLogCount }} log liên quan
                            <template v-if="gate.lastAccessAt">
                                - gần nhất {{ formatDateTime(gate.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa khai báo cổng nào trong hệ thống.</div>
            </article>
        </section>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import StreamPreview from "../components/StreamPreview.vue"
import { getAccessLogs } from "../services/accessLogApi"
import { getDeviceOverview } from "../services/deviceManagementApi"
import { getDetectedPlates } from "../services/plateRecognitionApi"
import {
    CAMERA_NETWORK_STORAGE_KEY,
    isRtspCameraUrl,
    loadCameraNetworkSettings,
    resolveCameraPreviewUrl,
} from "../utils/cameraNetwork"

const maxCameras = 6
const maxPlates = 6
const maxActivities = 8
const maxGates = 6

const summary = ref({
    camerasConfigured: 0,
    gatesConfigured: 0,
    camerasLinkedToGate: 0,
    unassignedCameras: 0,
})
const cameras = ref([])
const gates = ref([])
const recentPlates = ref([])
const recentActivities = ref([])
const localCameraSettings = ref([])

const displayedCameras = computed(() => cameras.value.slice(0, maxCameras))
const displayedPlates = computed(() => recentPlates.value.slice(0, maxPlates))
const displayedActivities = computed(() => recentActivities.value.slice(0, maxActivities))
const displayedGates = computed(() => gates.value.slice(0, maxGates))
const localPreviewCameras = computed(() =>
    localCameraSettings.value.filter((camera) => camera.enabled && (camera.url || camera.previewUrl))
)

const formatDateTime = (value) => {
    if (!value) return "--"
    return new Date(value).toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
    })
}

const formatTime = (value) => {
    if (!value) return "--"
    return new Date(value).toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
    })
}

const getLocalCameraChipText = (camera) => {
    if (camera.previewUrl && camera.url && isRtspCameraUrl(camera.url)) return "RTSP + preview"
    if (camera.url && isRtspCameraUrl(camera.url)) return "RTSP cho AI"
    return camera.online ? "Preview online" : "Preview chưa xác nhận"
}

const getLocalCameraChipClass = (camera) => {
    if (camera.previewUrl) return camera.online ? "success" : "warn"
    if (camera.url && isRtspCameraUrl(camera.url)) return "warn"
    return camera.online ? "success" : "warn"
}

const loadLocalCameraSettings = () => {
    localCameraSettings.value = loadCameraNetworkSettings()
}

const loadMonitoring = async () => {
    try {
        const [overviewRes, platesRes, activitiesRes] = await Promise.all([
            getDeviceOverview(),
            getDetectedPlates(),
            getAccessLogs({ page: 1, pageSize: 6 }),
        ])

        summary.value = { ...summary.value, ...(overviewRes.data.summary || {}) }
        cameras.value = overviewRes.data.cameras || []
        gates.value = overviewRes.data.gates || []
        recentPlates.value = (platesRes.data || []).slice(0, 6)
        recentActivities.value = activitiesRes.data.items || []
    } catch (error) {
        console.error("Monitoring load error:", error)
    }
}

const handleStorageChange = (event) => {
    if (!event.key || event.key === CAMERA_NETWORK_STORAGE_KEY) {
        loadLocalCameraSettings()
    }
}

onMounted(async () => {
    loadLocalCameraSettings()
    window.addEventListener("storage", handleStorageChange)
    await loadMonitoring()
})

onBeforeUnmount(() => {
    window.removeEventListener("storage", handleStorageChange)
})
</script>

<style scoped>
.local-preview-panel {
    display: grid;
    gap: 18px;
}

.local-preview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
}

.local-preview-card {
    display: grid;
    gap: 14px;
    padding: 18px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.camera-grid {
    display: grid;
    gap: 12px;
}

.camera-card,
.camera-card-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
}

.camera-card {
    padding: 16px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
    flex-direction: column;
}

.camera-card-head strong {
    display: block;
    color: var(--text-primary);
    font-size: 0.94rem;
}

.camera-card-head span {
    display: block;
    margin-top: 5px;
    color: var(--text-muted);
    font-size: 0.8rem;
}

.source-list {
    display: grid;
    gap: 6px;
}

.mono {
    overflow-wrap: anywhere;
    font-family: "JetBrains Mono", monospace;
    font-size: 0.78rem;
}

.scrollable-panel {
    max-height: 520px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(24, 49, 77, 0.15) transparent;
}

.scrollable-panel::-webkit-scrollbar {
    width: 5px;
}

.scrollable-panel::-webkit-scrollbar-track {
    background: transparent;
}

.scrollable-panel::-webkit-scrollbar-thumb {
    background: rgba(24, 49, 77, 0.15);
    border-radius: 10px;
}

.show-more-hint {
    text-align: center;
    padding: 12px;
    color: var(--text-muted);
    font-size: 0.84rem;
}

.show-more-hint a {
    color: var(--accent-primary);
    font-weight: 600;
    text-decoration: none;
}

.show-more-hint a:hover {
    text-decoration: underline;
}

@media (max-width: 1024px) {
    .local-preview-grid {
        grid-template-columns: 1fr;
    }
}
</style>
