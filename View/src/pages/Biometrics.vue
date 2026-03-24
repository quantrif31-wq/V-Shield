<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Biometrics</span>
                <h1 class="page-title">Theo dõi tình trạng huấn luyện dữ liệu khuôn mặt của từng nhân sự để AI nhận diện ổn định.</h1>
                <p class="page-subtitle">
                    Tại đây kỹ thuật viên có thể xem ai đã có video, ai đã có model, ai còn thiếu dữ liệu và những file
                    sinh gần nhất trong `EmployeeFaceVideos` và `EmployeeFaceModels`.
                </p>
                <div class="hero-actions">
                    <router-link to="/employees" class="btn btn-primary">Mở hồ sơ nhân sự</router-link>
                    <router-link to="/monitoring" class="btn btn-secondary">Quay lại giám sát</router-link>
                </div>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Độ phủ model</span>
                        <strong>{{ summary.trainedEmployees }}/{{ summary.totalEmployees }}</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        AI readiness
                    </span>
                </div>
                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Có model</span>
                        <strong>{{ summary.trainedEmployees }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Có video</span>
                        <strong>{{ summary.employeesWithVideos }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Thiếu model</span>
                        <strong>{{ summary.employeesMissingModels }}</strong>
                    </div>
                </div>
            </div>
        </section>

        <section class="metric-grid">
            <article class="metric-tile">
                <span class="metric-label">Tổng nhân sự</span>
                <strong class="metric-value">{{ summary.totalEmployees }}</strong>
                <span class="metric-note">Số nhân sự nội bộ hiện đang có trong hệ thống.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">File model</span>
                <strong class="metric-value">{{ summary.totalModelFiles }}</strong>
                <span class="metric-note">Tất cả model khuôn mặt đang lưu.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">File video</span>
                <strong class="metric-value">{{ summary.totalVideoFiles }}</strong>
                <span class="metric-note">Video huấn luyện đang có trong kho dữ liệu.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Thiếu video</span>
                <strong class="metric-value">{{ summary.employeesMissingVideos }}</strong>
                <span class="metric-note">Nhân sự chưa có video để huấn luyện thêm.</span>
            </article>
        </section>

        <section class="ops-panel">
            <div class="toolbar-shell">
                <div class="search-bar">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="query" type="text" placeholder="Tìm nhân sự, phòng ban, email..." />
                </div>
            </div>

            <div v-if="isLoading" class="empty-card">Đang tải dữ liệu biometrics...</div>
            <div v-else-if="employees.length === 0" class="empty-card">Không có nhân sự nào khớp với bộ lọc hiện tại.</div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Nhân sự</th>
                            <th>Phòng ban</th>
                            <th>Model</th>
                            <th>Video</th>
                            <th>Cập nhật gần nhất</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="employee in employees" :key="employee.employeeId">
                            <td>
                                <div class="table-main">{{ employee.fullName }}</div>
                                <div class="table-sub">{{ employee.positionName || 'Chưa có chức vụ' }}</div>
                            </td>
                            <td>{{ employee.departmentName || 'Chưa gán phòng ban' }}</td>
                            <td>
                                <div class="chip-row">
                                    <span class="soft-chip" :class="employee.modelCount > 0 ? 'success' : 'danger'">
                                        {{ employee.modelCount }} model
                                    </span>
                                </div>
                            </td>
                            <td>
                                <div class="chip-row">
                                    <span class="soft-chip" :class="employee.videoCount > 0 ? 'success' : 'warn'">
                                        {{ employee.videoCount }} video
                                    </span>
                                </div>
                            </td>
                            <td>{{ latestRecordLabel(employee) }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Recent models</span>
                        <h2 class="panel-title">Model mới nhất</h2>
                    </div>
                </div>

                <div v-if="recentModels.length" class="surface-list">
                    <article v-for="model in recentModels" :key="model.id" class="surface-item">
                        <div class="surface-item-title">{{ model.employeeName }}</div>
                        <div class="surface-item-sub">{{ model.modelFileName }}</div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ formatDateTime(model.createdAt) }}</span>
                            <span class="soft-chip success">{{ model.modelPath }}</span>
                        </div>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có model nào trong hệ thống.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Recent videos</span>
                        <h2 class="panel-title">Video mới nhất</h2>
                    </div>
                </div>

                <div v-if="recentVideos.length" class="surface-list">
                    <article v-for="video in recentVideos" :key="video.id" class="surface-item">
                        <div class="surface-item-title">{{ video.employeeName }}</div>
                        <div class="surface-item-sub">{{ video.fileName }} - {{ formatFileSize(video.fileSize) }}</div>
                        <div class="chip-row">
                            <span class="soft-chip">{{ formatDateTime(video.createdAt) }}</span>
                            <span class="soft-chip success">{{ video.filePath }}</span>
                        </div>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có video nào trong hệ thống.</div>
            </article>
        </section>
    </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { getBiometricOverview } from '../services/biometricApi'

const isLoading = ref(true)
const query = ref('')
const summary = ref({
    totalEmployees: 0,
    trainedEmployees: 0,
    employeesWithVideos: 0,
    employeesMissingModels: 0,
    employeesMissingVideos: 0,
    totalModelFiles: 0,
    totalVideoFiles: 0,
})
const employees = ref([])
const recentModels = ref([])
const recentVideos = ref([])

const formatDateTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

const formatFileSize = (value) => {
    if (!value) return '0 B'
    if (value < 1024) return `${value} B`
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
    return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const latestRecordLabel = (employee) => {
    const latest = employee.latestModelAt || employee.latestVideoAt
    if (!latest) return 'Chưa có dữ liệu'
    return formatDateTime(latest)
}

const fetchOverview = async () => {
    isLoading.value = true
    try {
        const { data } = await getBiometricOverview({ query: query.value || undefined })
        summary.value = { ...summary.value, ...(data.summary || {}) }
        employees.value = data.employees || []
        recentModels.value = data.recentModels || []
        recentVideos.value = data.recentVideos || []
    } catch (error) {
        console.error('Biometric overview error:', error)
        employees.value = []
        recentModels.value = []
        recentVideos.value = []
    } finally {
        isLoading.value = false
    }
}

let queryTimer = null
watch(query, () => {
    clearTimeout(queryTimer)
    queryTimer = setTimeout(fetchOverview, 260)
})

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
    font-size: 1.8rem;
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

.table-main {
    color: var(--text-primary);
    font-weight: 600;
}

.table-sub {
    margin-top: 4px;
    color: var(--text-muted);
    font-size: 0.8rem;
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }
}
</style>
