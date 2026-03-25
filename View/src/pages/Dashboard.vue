<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Dashboard overview</span>
                <h1 class="page-title">Bảng điều phối tổng quan</h1>
            </div>
            <div class="header-actions">
                <router-link to="/monitoring" class="btn btn-primary">Mở giám sát trực tiếp</router-link>
                <router-link to="/access-logs" class="btn btn-secondary">Tra cứu vào/ra</router-link>
                <router-link to="/pre-registrations" class="btn btn-secondary">Xem khách hẹn trước</router-link>
            </div>
        </div>

        <section class="metric-grid">
            <article class="metric-tile">
                <span class="metric-label">Xe đang trong bãi</span>
                <strong class="metric-value">{{ snapshot.vehiclesInside }}</strong>
                <span class="metric-note">Đọc trực tiếp từ `ParkingStatus = IN`.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Khách dự kiến hôm nay</span>
                <strong class="metric-value">{{ snapshot.expectedVisitorsToday }}</strong>
                <span class="metric-note">Theo `ExpectedTimeIn` trong lịch hẹn trước.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Lượt chờ duyệt</span>
                <strong class="metric-value">{{ snapshot.pendingRegistrations }}</strong>
                <span class="metric-note">Đơn khách vẫn đang ở trạng thái chờ xử lý.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Ngoại lệ trong ngày</span>
                <strong class="metric-value">{{ snapshot.dailyExceptions }}</strong>
                <span class="metric-note">Gồm bypass, lỗi nhận diện hoặc trạng thái bất thường.</span>
            </article>
        </section>

        <section class="ops-grid two">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Traffic</span>
                        <h2 class="panel-title">Lưu lượng ra vào trong tuần</h2>
                    </div>
                    <div class="chip-row">
                        <span class="soft-chip">Vào</span>
                        <span class="soft-chip warn">Ra</span>
                    </div>
                </div>

                <div v-if="trafficChart.length" class="traffic-chart">
                    <div v-for="day in trafficChart" :key="day.label" class="chart-day">
                        <div class="chart-stack">
                            <div class="chart-bar in" :style="{ height: `${day.inPercent}%` }">
                                <span>{{ day.checkIn }}</span>
                            </div>
                            <div class="chart-bar out" :style="{ height: `${day.outPercent}%` }">
                                <span>{{ day.checkOut }}</span>
                            </div>
                        </div>
                        <strong>{{ day.label }}</strong>
                    </div>
                </div>
                <div v-else class="empty-card">Chưa có dữ liệu lưu lượng trong tuần này.</div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Live feed</span>
                        <h2 class="panel-title">Hoạt động mới nhất</h2>
                    </div>
                    <router-link to="/access-logs" class="btn btn-secondary btn-sm">Xem toàn bộ</router-link>
                </div>

                <div v-if="recentActivities.length" class="surface-list scrollable-panel">
                    <article v-for="activity in displayedActivities" :key="activity.logId" class="activity-item">
                        <div class="activity-dot" :class="activity.direction === 'IN' ? 'success' : 'warn'"></div>
                        <div class="activity-meta">
                            <strong>{{ formatTime(activity.timestamp) }}</strong>
                            <span>{{ activity.direction === 'IN' ? 'Vào' : 'Ra' }}</span>
                        </div>
                        <div class="activity-copy">
                            <strong>{{ activity.actorName }}</strong>
                            <p>
                                {{ activity.gateName }}
                                <template v-if="activity.capturedLicensePlate">- {{ activity.capturedLicensePlate }}</template>
                                <template v-else-if="activity.cameraName">- {{ activity.cameraName }}</template>
                            </p>
                            <div class="chip-row">
                                <span v-if="activity.isBypass" class="soft-chip danger">Bypass</span>
                                <span v-if="activity.exceptionReason" class="soft-chip warn">{{ activity.exceptionReason }}</span>
                                <span v-if="activity.resultStatus" class="soft-chip">{{ activity.resultStatus }}</span>
                            </div>
                        </div>
                    </article>
                </div>
                <div v-else class="empty-card">Chưa có bản ghi hoạt động nào để hiển thị.</div>
            </article>
        </section>

        <section class="ops-grid three">
            <article class="ops-panel">
                <div class="panel-head compact">
                    <div>
                        <span class="panel-kicker">Visitors</span>
                        <h2 class="panel-title">Khách & hồ sơ</h2>
                    </div>
                </div>
                <div class="surface-list">
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.guestProfiles }}</strong>
                            <span>Hồ sơ khách đang được lưu trong hệ thống</span>
                        </div>
                    </div>
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.expectedVisitorsToday }}</strong>
                            <span>Khách dự kiến đến trong ngày hôm nay</span>
                        </div>
                    </div>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head compact">
                    <div>
                        <span class="panel-kicker">Devices</span>
                        <h2 class="panel-title">Camera & cổng</h2>
                    </div>
                </div>
                <div class="surface-list">
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.camerasConfigured }}</strong>
                            <span>Camera đã cấu hình trong cơ sở dữ liệu</span>
                        </div>
                    </div>
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.gatesConfigured }}</strong>
                            <span>Cổng truy cập đang được quản lý</span>
                        </div>
                    </div>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head compact">
                    <div>
                        <span class="panel-kicker">Biometrics</span>
                        <h2 class="panel-title">Độ phủ dữ liệu AI</h2>
                    </div>
                </div>
                <div class="surface-list">
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.trainedEmployeeCount }}/{{ snapshot.employeeCount }}</strong>
                            <span>Nhân sự đã có model khuôn mặt</span>
                        </div>
                    </div>
                    <div class="surface-item">
                        <div class="inline-stat">
                            <strong>{{ snapshot.recognitionCoverage }}%</strong>
                            <span>Tỷ lệ nhân sự đã có dữ liệu nhận diện</span>
                        </div>
                    </div>
                </div>
            </article>
        </section>
    </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getDashboardOverview } from '../services/dashboardApi'

const maxActivities = 4

const isLoading = ref(true)
const loadError = ref('')
const snapshot = ref({
    vehiclesInside: 0,
    expectedVisitorsToday: 0,
    pendingRegistrations: 0,
    dailyCheckIn: 0,
    dailyCheckOut: 0,
    dailyExceptions: 0,
    camerasConfigured: 0,
    gatesConfigured: 0,
    guestProfiles: 0,
    employeeCount: 0,
    trainedEmployeeCount: 0,
    recognitionCoverage: 0,
})
const weeklyTraffic = ref([])
const recentActivities = ref([])

const displayedActivities = computed(() => recentActivities.value.slice(0, maxActivities))

const nowLabel = computed(() =>
    new Date().toLocaleDateString('vi-VN', {
        weekday: 'long',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
)

const trafficChart = computed(() => {
    const maxValue = Math.max(
        ...weeklyTraffic.value.flatMap((day) => [day.checkIn || 0, day.checkOut || 0]),
        1
    )

    return weeklyTraffic.value.map((day) => ({
        ...day,
        inPercent: Math.max(12, Math.round(((day.checkIn || 0) / maxValue) * 100)),
        outPercent: Math.max(12, Math.round(((day.checkOut || 0) / maxValue) * 100)),
    }))
})

const spotlightMessage = computed(() => {
    if (snapshot.value.dailyExceptions > 0) {
        return `Có ${snapshot.value.dailyExceptions} ngoại lệ trong ngày, nên ưu tiên rà soát mục Xử lý ngoại lệ và nhật ký ra vào.`
    }

    if (snapshot.value.pendingRegistrations > 0) {
        return `Hiện còn ${snapshot.value.pendingRegistrations} lượt đăng ký khách chờ duyệt, phù hợp để lễ tân xử lý sớm trước giờ cao điểm.`
    }

    return 'Luồng ra vào hôm nay đang ổn định. Có thể ưu tiên theo dõi camera, biển số và độ phủ dữ liệu nhận diện.'
})

const formatTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
    })
}

const loadDashboard = async () => {
    isLoading.value = true
    loadError.value = ''
    try {
        const { data } = await getDashboardOverview()
        snapshot.value = { ...snapshot.value, ...(data.snapshot || {}) }
        weeklyTraffic.value = data.weeklyTraffic || []
        recentActivities.value = data.recentActivities || []
    } catch (error) {
        console.error('Dashboard load error:', error)
        loadError.value = 'Không thể tải dữ liệu tổng quan'
    } finally {
        isLoading.value = false
    }
}

onMounted(loadDashboard)
</script>



<style scoped>
.ops-panel {
    display: flex;
    flex-direction: column;
}

.traffic-chart {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px;
    min-height: 250px;
    margin-top: auto;
}

.chart-day {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
}

.chart-stack {
    width: 100%;
    height: 280px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 8px;
}

.chart-bar {
    position: relative;
    width: min(24px, 100%);
    border-radius: 12px 12px 4px 4px;
}

.chart-bar span {
    position: absolute;
    left: 50%;
    top: -26px;
    transform: translateX(-50%);
    color: var(--text-muted);
    font-size: 0.72rem;
    font-weight: 700;
}

.chart-bar.in {
    background: linear-gradient(180deg, rgba(84, 196, 211, 0.24), var(--accent-primary));
}

.chart-bar.out {
    background: linear-gradient(180deg, rgba(216, 155, 55, 0.24), var(--accent-warning));
}

.chart-day strong {
    color: var(--text-secondary);
    font-size: 0.82rem;
}

.activity-item {
    display: grid;
    grid-template-columns: 12px 72px 1fr;
    gap: 14px;
    padding: 14px;
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.activity-dot {
    width: 12px;
    height: 12px;
    margin-top: 4px;
    border-radius: 50%;
}

.activity-dot.success {
    background: var(--accent-success);
    box-shadow: 0 0 0 6px rgba(20, 134, 109, 0.1);
}

.activity-dot.warn {
    background: var(--accent-warning);
    box-shadow: 0 0 0 6px rgba(184, 111, 33, 0.1);
}

.activity-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.activity-meta strong {
    color: var(--text-primary);
    font-size: 0.88rem;
}

.activity-meta span {
    color: var(--text-muted);
    font-size: 0.74rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.activity-copy strong {
    color: var(--text-primary);
    font-size: 0.94rem;
}

.activity-copy p {
    margin-top: 6px;
    color: var(--text-secondary);
    font-size: 0.84rem;
}

.activity-copy .chip-row {
    margin-top: 10px;
}

.panel-head.compact {
    margin-bottom: 14px;
}

.scrollable-panel {
    max-height: 360px;
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




@media (max-width: 768px) {
    .activity-item {
        grid-template-columns: 12px 1fr;
    }

    .activity-meta {
        grid-column: 2;
        flex-direction: row;
        gap: 8px;
        align-items: center;
    }

    .activity-copy {
        grid-column: 2;
    }
}
</style>
