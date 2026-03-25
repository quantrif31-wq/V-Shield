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
                <span class="metric-note">Đọc từ bảng `Camera` trong hệ thống.</span>
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
                                <span>{{ camera.gateName || 'Chưa gán cổng' }}</span>
                            </div>
                            <span class="soft-chip" :class="camera.gateId ? 'success' : 'warn'">
                                {{ camera.cameraType || 'Không rõ loại' }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ camera.accessLogCount }} log</span>
                            <span v-if="camera.latestPlate" class="soft-chip success">{{ camera.latestPlate }}</span>
                            <span v-else class="soft-chip warn">Chưa có biển số</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ camera.gateLocation || 'Chưa có vị trí cổng' }}
                            <template v-if="camera.lastAccessAt">
                                - hoạt động gần nhất {{ formatDateTime(camera.lastAccessAt) }}
                            </template>
                        </p>
                    </article>
                    <div v-if="cameras.length > maxCameras" class="show-more-hint">
                        Hiển thị {{ maxCameras }}/{{ cameras.length }} camera. Vào <router-link to="/device-management">Quản lý thiết bị</router-link> để xem tất cả.
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
                                <span>{{ activity.gateName || 'Chưa gán cổng' }}</span>
                            </div>
                            <span class="soft-chip" :class="activity.direction === 'IN' ? 'success' : 'warn'">
                                {{ activity.direction === 'IN' ? 'Vào' : 'Ra' }}
                            </span>
                        </div>
                        <div class="chip-row">
                            <span v-if="activity.capturedLicensePlate" class="soft-chip">{{ activity.capturedLicensePlate }}</span>
                            <span v-if="activity.resultStatus" class="soft-chip">{{ activity.resultStatus }}</span>
                            <span v-if="activity.isBypass" class="soft-chip danger">BYPASS</span>
                        </div>
                        <p class="surface-item-sub">
                            {{ activity.cameraName || 'Không có camera' }} - {{ formatDateTime(activity.timestamp) }}
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
                                <span>{{ gate.location || 'Chưa có vị trí' }}</span>
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
import { computed, onMounted, ref } from 'vue'
import { getDeviceOverview } from '../services/deviceManagementApi'
import { getDetectedPlates } from '../services/plateRecognitionApi'
import { getAccessLogs } from '../services/accessLogApi'

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

const displayedCameras = computed(() => cameras.value.slice(0, maxCameras))
const displayedPlates = computed(() => recentPlates.value.slice(0, maxPlates))
const displayedActivities = computed(() => recentActivities.value.slice(0, maxActivities))
const displayedGates = computed(() => gates.value.slice(0, maxGates))

const formatDateTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
    })
}

const formatTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
    })
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
        console.error('Monitoring load error:', error)
    }
}

onMounted(loadMonitoring)
</script>

<style scoped>


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



</style>
