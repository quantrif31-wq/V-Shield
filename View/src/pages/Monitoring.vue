<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Live monitoring</span>
                <h1 class="page-title">Giam sat truc tiep</h1>
            </div>
            <div class="header-actions">
                <router-link to="/device-management" class="btn btn-primary">Quan ly camera & cong</router-link>
                <router-link to="/exceptions" class="btn btn-secondary">Xem ngoai le</router-link>
            </div>
        </div>

        <section class="metric-grid">
            <article class="metric-tile">
                <span class="metric-label">Camera da cau hinh</span>
                <strong class="metric-value">{{ summary.camerasConfigured }}</strong>
                <span class="metric-note">Doc tu bang <code>Camera</code> trong he thong.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Cong dang quan ly</span>
                <strong class="metric-value">{{ summary.gatesConfigured }}</strong>
                <span class="metric-note">So vi tri cong dang duoc khai bao.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera co gan cong</span>
                <strong class="metric-value">{{ summary.camerasLinkedToGate }}</strong>
                <span class="metric-note">Cac camera da lien ket dung diem truy cap.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Camera chua gan cong</span>
                <strong class="metric-value">{{ summary.unassignedCameras }}</strong>
                <span class="metric-note">Can kiem tra lai cau hinh thiet bi.</span>
            </article>
        </section>

        <section class="ops-panel local-preview-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Local camera previews</span>
                    <h2 class="panel-title">Preview tu cau hinh local</h2>
                    <p class="panel-copy">
                        Muc nay doc du lieu da nhap o trang Quan ly camera. RTSP chi dung cho AI; de xem tren web, hay
                        them <code>Preview URL</code> dang HLS, MJPEG, MP4 hoac WebRTC gateway.
                    </p>
                </div>
                <div class="panel-actions">
                    <button class="btn btn-secondary btn-sm" @click="loadLocalCameraSettings">Tai lai preview</button>
                    <router-link to="/device-management" class="btn btn-primary btn-sm">Sua cau hinh</router-link>
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
                            Chua co Preview URL cho browser. Neu slot nay chi co RTSP, web se hien thong bao thay vi video.
                        </p>
                    </div>
                </article>
            </div>
            <div v-else class="empty-card">
                Chua co camera local nao duoc bat trong trinh duyet nay. Hay vao Quan ly camera de them RTSP va Preview
                URL.
            </div>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Configured cameras</span>
                        <h2 class="panel-title">Camera & diem dat</h2>
                    </div>
                    <router-link to="/device-management" class="btn btn-secondary btn-sm">Mo cau hinh</router-link>
                </div>

                <div v-if="cameras.length" class="camera-grid scrollable-panel">
                    <article v-for="camera in displayedCameras" :key="camera.cameraId" class="camera-card">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ camera.cameraName }}</strong>
                                <span>{{ camera.gateName || "Chua gan cong" }}</span>
                            </div>
                            <span class="soft-chip" :class="camera.gateId ? 'success' : 'warn'">
                                {{ camera.cameraType || "Khong ro loai" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ camera.accessLogCount }} log</span>
                            <span v-if="camera.latestPlate" class="soft-chip success">{{ camera.latestPlate }}</span>
                            <span v-else class="soft-chip warn">Chua co bien so</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ camera.gateLocation || "Chua co vi tri cong" }}
                            <template v-if="camera.lastAccessAt">
                                - hoat dong gan nhat {{ formatDateTime(camera.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                    <div v-if="cameras.length > maxCameras" class="show-more-hint">
                        Hien thi {{ maxCameras }}/{{ cameras.length }} camera. Vao
                        <router-link to="/device-management">Quan ly thiet bi</router-link> de xem tat ca.
                    </div>
                </div>
                <div v-else class="empty-card">Chua co camera nao trong co so du lieu.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Plate recognition</span>
                        <h2 class="panel-title">Bien so nhan dien gan nhat</h2>
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
                            Ban ghi bien so moi nhat tu camera, dung de doi soat nhanh voi dong ra vao.
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chua co du lieu nhan dien bien so gan day.</div>
            </article>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Face & access</span>
                        <h2 class="panel-title">Dong xac minh khuon mat gan nhat</h2>
                    </div>
                    <router-link to="/access-logs" class="btn btn-secondary btn-sm">Mo nhat ky</router-link>
                </div>

                <div v-if="recentActivities.length" class="surface-list scrollable-panel">
                    <article v-for="activity in displayedActivities" :key="activity.logId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ activity.actorName }}</strong>
                                <span>{{ activity.gateName || "Chua gan cong" }}</span>
                            </div>
                            <span class="soft-chip" :class="activity.direction === 'IN' ? 'success' : 'warn'">
                                {{ activity.direction === "IN" ? "Vao" : "Ra" }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span v-if="activity.capturedLicensePlate" class="soft-chip">{{ activity.capturedLicensePlate }}</span>
                            <span v-if="activity.resultStatus" class="soft-chip">{{ activity.resultStatus }}</span>
                            <span v-if="activity.isBypass" class="soft-chip danger">BYPASS</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ activity.cameraName || "Khong co camera" }} - {{ formatDateTime(activity.timestamp) }}
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chua co log nhan dien nao gan day.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Gate posture</span>
                        <h2 class="panel-title">Tinh trang cong truy cap</h2>
                    </div>
                </div>

                <div v-if="gates.length" class="surface-list scrollable-panel">
                    <article v-for="gate in displayedGates" :key="gate.gateId" class="surface-item">
                        <div class="camera-card-head">
                            <div>
                                <strong>{{ gate.gateName }}</strong>
                                <span>{{ gate.location || "Chua co vi tri" }}</span>
                            </div>
                            <span class="soft-chip">{{ gate.cameraCount }} camera</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ gate.accessLogCount }} log lien quan
                            <template v-if="gate.lastAccessAt">
                                - gan nhat {{ formatDateTime(gate.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                </div>
                <div v-else class="empty-card">Chua khai bao cong nao trong he thong.</div>
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
    return camera.online ? "Preview online" : "Preview chua xac nhan"
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
