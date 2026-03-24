<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Live monitoring</span>
                <h1 class="page-title">Giám sát trực tiếp camera, cổng và kết quả nhận diện từ cùng một màn hình.</h1>
                <p class="page-subtitle">
                    Trang này gom dữ liệu camera đã cấu hình, cổng truy cập, biển số mới nhận diện và các bản ghi
                    khuôn mặt gần nhất trong `Access_Log` để bảo vệ có thể theo dõi nhanh tại chỗ.
                </p>
                <div class="hero-actions">
                    <router-link to="/device-management" class="btn btn-primary">Quản lý camera & cổng</router-link>
                    <router-link to="/exceptions" class="btn btn-secondary">Xem ngoại lệ</router-link>
                </div>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Thiết bị giám sát</span>
                        <strong>{{ summary.camerasConfigured }} camera / {{ summary.gatesConfigured }} cổng</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        Dữ liệu đang cập nhật
                    </span>
                </div>
                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Gắn cổng</span>
                        <strong>{{ summary.camerasLinkedToGate }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Chưa gắn cổng</span>
                        <strong>{{ summary.unassignedCameras }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Biển số mới</span>
                        <strong>{{ recentPlates.length }}</strong>
                    </div>
                </div>
            </div>
        </section>

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

                <div v-if="cameras.length" class="camera-grid">
                    <article v-for="camera in cameras" :key="camera.cameraId" class="camera-card">
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

                <div v-if="recentPlates.length" class="surface-list">
                    <article v-for="plate in recentPlates" :key="`${plate.cameraIP}-${plate.plateNumber}-${plate.lastUpdate}`" class="surface-item">
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

                <div v-if="recentActivities.length" class="surface-list">
                    <article v-for="activity in recentActivities" :key="activity.logId" class="surface-item">
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

                <div v-if="gates.length" class="surface-list">
                    <article v-for="gate in gates" :key="gate.gateId" class="surface-item">
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
import { onMounted, ref } from 'vue'
import { getDeviceOverview } from '../services/deviceManagementApi'
import { getDetectedPlates } from '../services/plateRecognitionApi'
import { getAccessLogs } from '../services/accessLogApi'

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
    font-size: 1.16rem;
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

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }
}
</style>
