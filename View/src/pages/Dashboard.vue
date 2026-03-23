<template>
    <div class="page-container dashboard-shell animate-in">
        <header class="dashboard-hero">
            <div class="hero-copy">
                <span class="hero-kicker">V-Shield overview</span>
                <h1 class="page-title">Bảng điều phối an ninh tập trung cho con người, phương tiện và camera.</h1>
                <p class="page-subtitle">
                    Từ đây đội vận hành có thể nhìn ngay những gì đang diễn ra, khu vực nào cần phản ứng
                    và luồng truy cập nào đang tăng tải trong ngày.
                </p>

                <div class="hero-actions">
                    <router-link to="/monitoring" class="btn btn-primary">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width: 16px; height: 16px;">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                            <circle cx="12" cy="13" r="4" />
                        </svg>
                        Mở giám sát trực tiếp
                    </router-link>
                    <router-link to="/access-logs" class="btn btn-secondary">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width: 16px; height: 16px;">
                            <path d="M12 8v4l3 3" />
                            <circle cx="12" cy="12" r="9" />
                        </svg>
                        Xem dòng sự kiện
                    </router-link>
                </div>
            </div>

            <div class="hero-board">
                <div class="board-top">
                    <div>
                        <span class="board-label">Ca trực hiện tại</span>
                        <strong>{{ currentDate }}</strong>
                    </div>
                    <span class="board-pill">
                        <span class="pill-dot"></span>
                        Đồng bộ dữ liệu
                    </span>
                </div>

                <div class="board-metrics">
                    <div class="board-metric">
                        <span>Tổng lượt tuần</span>
                        <strong>{{ weeklyTraffic }}</strong>
                    </div>
                    <div class="board-metric">
                        <span>Ngày cao điểm</span>
                        <strong>{{ peakDay }}</strong>
                    </div>
                    <div class="board-metric">
                        <span>Tỷ lệ hiện diện</span>
                        <strong>{{ occupancyRate }}%</strong>
                    </div>
                </div>

                <div class="board-alert">
                    <span class="alert-tag">Focus</span>
                    <p>Khung 08:00 - 09:00 đang là giờ cao điểm ra vào. Ưu tiên theo dõi Cổng A và luồng khách đăng ký trước.</p>
                </div>
            </div>
        </header>

        <div class="dashboard-grid">
            <section class="dashboard-card metrics-card">
                <div class="section-head">
                    <div>
                        <span class="section-kicker">Nhân sự nội bộ</span>
                        <h2>Tình trạng hiện diện</h2>
                    </div>
                    <span class="live-badge">
                        <span class="live-dot"></span>
                        Đang cập nhật
                    </span>
                </div>

                <div class="metrics-main">
                    <div class="metric-spotlight">
                        <span>Tổng nhân sự</span>
                        <strong>{{ totalEmployees }}</strong>
                    </div>
                    <div class="metric-spotlight success">
                        <span>Đang hoạt động</span>
                        <strong>{{ activeEmployees }}</strong>
                    </div>
                </div>

                <div class="occupancy-track">
                    <div class="occupancy-copy">
                        <span>Hiện diện trong hệ thống</span>
                        <strong>{{ occupancyRate }}%</strong>
                    </div>
                    <div class="track-shell">
                        <div class="track-fill" :style="{ width: `${occupancyRate}%` }"></div>
                    </div>
                </div>

                <div class="metrics-foot">
                    <div>
                        <span class="mini-label">Mức độ ổn định</span>
                        <strong>Ổn định</strong>
                    </div>
                    <div>
                        <span class="mini-label">Khuyến nghị</span>
                        <strong>Duy trì xác minh khuôn mặt tại các cổng chính</strong>
                    </div>
                </div>
            </section>

            <router-link to="/pre-registrations" class="dashboard-card action-card accent-teal action-guest">
                <div class="action-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
                        <rect x="8" y="2" width="8" height="4" rx="1.5" />
                        <path d="M9 14l2 2 4-4" />
                    </svg>
                </div>
                <span class="section-kicker">Quick action</span>
                <h2>Đăng ký khách trước</h2>
                <p>Tạo luồng tiếp đón nhanh với liên kết QR, giảm ma sát tại điểm vào.</p>
                <span class="action-link">Tạo lượt mới</span>
            </router-link>

            <router-link to="/employees" class="dashboard-card action-card accent-gold action-employees">
                <div class="action-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 00-3-3.87" />
                        <path d="M16 3.13a4 4 0 010 7.75" />
                    </svg>
                </div>
                <span class="section-kicker">Quick action</span>
                <h2>Hồ sơ nhân sự</h2>
                <p>Quản lý định danh, Face ID, phòng ban và tình trạng truy cập từ cùng một luồng.</p>
                <span class="action-link">Mở danh sách</span>
            </router-link>

            <section class="dashboard-card traffic-card">
                <div class="section-head">
                    <div>
                        <span class="section-kicker">Traffic</span>
                        <h2>Lưu lượng ra vào trong tuần</h2>
                    </div>
                    <div class="chart-legend">
                        <span><i class="legend-dot in"></i> Vào</span>
                        <span><i class="legend-dot out"></i> Ra</span>
                    </div>
                </div>

                <div class="traffic-chart">
                    <div v-for="day in weekData" :key="day.label" class="chart-column">
                        <div class="bar-wrap">
                            <div class="bar-stack in" :style="{ height: `${day.inPercent}%` }">
                                <span>{{ day.checkIn }}</span>
                            </div>
                            <div class="bar-stack out" :style="{ height: `${day.outPercent}%` }">
                                <span>{{ day.checkOut }}</span>
                            </div>
                        </div>
                        <strong>{{ day.label }}</strong>
                    </div>
                </div>
            </section>

            <section class="dashboard-card feed-card">
                <div class="section-head">
                    <div>
                        <span class="section-kicker">Live feed</span>
                        <h2>Hoạt động mới nhất</h2>
                    </div>
                    <router-link to="/access-logs" class="feed-link">Xem toàn bộ</router-link>
                </div>

                <div class="feed-list">
                    <article v-for="log in dashboardRecentLogs" :key="log.id" class="feed-item">
                        <div class="feed-marker" :class="log.type"></div>
                        <div class="feed-meta">
                            <strong>{{ log.time }}</strong>
                            <span>{{ log.type === 'in' ? 'Vào' : 'Ra' }}</span>
                        </div>
                        <div class="feed-copy">
                            <strong>{{ log.name }}</strong>
                            <p>{{ log.detail }}</p>
                        </div>
                    </article>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { getSummary } from '../services/statisticsApi'

const currentDate = computed(() => {
    const d = new Date()
    return d.toLocaleDateString('vi-VN', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    })
})

const totalEmployees = ref('...')
const activeEmployees = ref('...')
let eventSource = null

onMounted(async () => {
    try {
        const summary = await getSummary()
        totalEmployees.value = summary.totalEmployees.toString()
        activeEmployees.value = summary.activeEmployees.toString()

        eventSource = new EventSource('https://localhost:7107/api/Statistics/employees/stream')
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                totalEmployees.value = data.totalEmployees.toString()
                activeEmployees.value = data.activeEmployees.toString()
            } catch {
                // Ignore malformed stream messages.
            }
        }
    } catch {
        totalEmployees.value = '--'
        activeEmployees.value = '--'
    }
})

onUnmounted(() => {
    if (eventSource) eventSource.close()
})

const weekData = ref([
    { label: 'T2', checkIn: 180, checkOut: 165, inPercent: 90, outPercent: 82 },
    { label: 'T3', checkIn: 195, checkOut: 178, inPercent: 97, outPercent: 89 },
    { label: 'T4', checkIn: 172, checkOut: 160, inPercent: 86, outPercent: 80 },
    { label: 'T5', checkIn: 200, checkOut: 185, inPercent: 100, outPercent: 92 },
    { label: 'T6', checkIn: 187, checkOut: 170, inPercent: 93, outPercent: 85 },
    { label: 'T7', checkIn: 95, checkOut: 88, inPercent: 47, outPercent: 44 },
    { label: 'CN', checkIn: 30, checkOut: 25, inPercent: 15, outPercent: 12 },
])

const recentLogs = ref([
    { id: 1, name: 'Nguyễn Văn An', detail: 'Vào cổng A - Đi bộ', type: 'in', time: '08:05' },
    { id: 2, name: 'Trần Thị Bình', detail: 'Ra cổng B', type: 'out', time: '08:12' },
    { id: 3, name: 'Lê Hoàng Cường', detail: 'Vào cổng A - Xe 30H-567.89', type: 'in', time: '08:20' },
    { id: 4, name: 'Phạm Minh Đức', detail: 'Khách đăng ký trước đã check-in', type: 'in', time: '08:25' },
    { id: 5, name: 'Võ Thị Em', detail: 'Ra cổng C', type: 'out', time: '08:30' },
    { id: 6, name: 'Khách VIP', detail: 'Đã xác thực qua mã QR', type: 'in', time: '08:35' },
])

const dashboardRecentLogs = computed(() => recentLogs.value.slice(0, 4))

const totalEmployeesNumber = computed(() => Number.parseInt(totalEmployees.value, 10) || 0)
const activeEmployeesNumber = computed(() => Number.parseInt(activeEmployees.value, 10) || 0)

const occupancyRate = computed(() => {
    if (!totalEmployeesNumber.value) return 0
    return Math.round((activeEmployeesNumber.value / totalEmployeesNumber.value) * 100)
})

const weeklyTraffic = computed(() =>
    weekData.value.reduce((sum, day) => sum + day.checkIn + day.checkOut, 0)
)

const peakDay = computed(() => {
    const topDay = weekData.value.reduce((max, day) => {
        const traffic = day.checkIn + day.checkOut
        return traffic > max.traffic ? { label: day.label, traffic } : max
    }, { label: '--', traffic: 0 })

    return topDay.label
})
</script>

<style scoped>
.dashboard-shell {
    display: flex;
    flex-direction: column;
    gap: 24px;
}

.dashboard-hero {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(360px, 430px);
    gap: 20px;
}

.hero-copy,
.hero-board,
.dashboard-card {
    border: 1px solid rgba(255, 255, 255, 0.7);
    background: rgba(255, 255, 255, 0.84);
    backdrop-filter: var(--glass-blur);
    box-shadow: var(--shadow-sm);
}

.hero-copy {
    padding: 30px;
    border-radius: 30px;
}

.hero-kicker,
.section-kicker {
    display: inline-flex;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(15, 124, 130, 0.08);
    color: var(--accent-primary);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero-copy .page-title {
    max-width: 14ch;
    margin-top: 16px;
}

.hero-copy .page-subtitle {
    margin-top: 14px;
    max-width: 58ch;
}

.hero-actions {
    margin-top: 26px;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.hero-board {
    padding: 24px;
    border-radius: 30px;
    background:
        radial-gradient(circle at top right, rgba(84, 196, 211, 0.2), transparent 34%),
        linear-gradient(180deg, rgba(16, 32, 51, 0.98), rgba(24, 49, 77, 0.96));
    color: #eefbfc;
    border-color: rgba(84, 196, 211, 0.12);
}

.board-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
}

.board-label {
    display: block;
    color: rgba(215, 251, 255, 0.7);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.board-top strong {
    display: block;
    margin-top: 8px;
    font-family: var(--font-heading);
    font-size: 1.15rem;
    line-height: 1.3;
}

.board-pill {
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

.pill-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #5de3c7;
}

.board-metrics {
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.board-metric {
    padding: 16px 14px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.board-metric span {
    display: block;
    color: rgba(215, 251, 255, 0.72);
    font-size: 0.76rem;
}

.board-metric strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-family: var(--font-heading);
    font-size: 1.12rem;
}

.board-alert {
    margin-top: 18px;
    padding: 18px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.alert-tag {
    display: inline-flex;
    align-items: center;
    margin-bottom: 10px;
    padding: 5px 10px;
    border-radius: 999px;
    background: rgba(216, 155, 55, 0.16);
    color: #ffd89d;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.board-alert p {
    color: rgba(239, 251, 252, 0.86);
    font-size: 0.88rem;
    line-height: 1.6;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    grid-template-areas:
        "metrics metrics action-guest action-employees"
        "traffic traffic feed feed";
    gap: 20px;
}

.dashboard-card {
    padding: 24px;
    border-radius: 28px;
}

.metrics-card { grid-area: metrics; }
.action-guest { grid-area: action-guest; }
.action-employees { grid-area: action-employees; }
.traffic-card {
    grid-area: traffic;
    align-self: start;
}
.feed-card { grid-area: feed; }

.section-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
}

.section-head h2 {
    margin-top: 10px;
    font-family: var(--font-heading);
    font-size: 1.28rem;
    font-weight: 700;
    line-height: 1.08;
    color: var(--text-primary);
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(20, 134, 109, 0.1);
    color: var(--accent-success);
    font-size: 0.76rem;
    font-weight: 700;
}

.live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: currentColor;
}

.metrics-main {
    margin-top: 20px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.metric-spotlight {
    padding: 20px;
    border-radius: 22px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(236, 244, 246, 0.82));
    border: 1px solid rgba(24, 49, 77, 0.08);
}

.metric-spotlight span {
    display: block;
    color: var(--text-secondary);
    font-size: 0.84rem;
}

.metric-spotlight strong {
    display: block;
    margin-top: 10px;
    font-family: var(--font-heading);
    font-size: 2.4rem;
    font-weight: 700;
    line-height: 1;
    color: var(--text-primary);
}

.metric-spotlight.success strong {
    color: var(--accent-success);
}

.occupancy-track {
    margin-top: 20px;
    padding: 18px 20px;
    border-radius: 22px;
    background: rgba(236, 244, 246, 0.68);
    border: 1px solid rgba(24, 49, 77, 0.08);
}

.occupancy-copy {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}

.occupancy-copy span {
    color: var(--text-secondary);
    font-size: 0.84rem;
}

.occupancy-copy strong {
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 1.06rem;
}

.track-shell {
    width: 100%;
    height: 12px;
    border-radius: 999px;
    background: rgba(16, 32, 51, 0.08);
    overflow: hidden;
}

.track-fill {
    height: 100%;
    border-radius: inherit;
    background: var(--accent-gradient);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
}

.metrics-foot {
    margin-top: 18px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.mini-label {
    display: block;
    color: var(--text-muted);
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.metrics-foot strong {
    display: block;
    margin-top: 8px;
    color: var(--text-primary);
    font-size: 0.92rem;
    line-height: 1.45;
}

.action-card {
    display: flex;
    flex-direction: column;
    gap: 12px;
    color: var(--text-primary);
    transition: transform var(--transition-normal), box-shadow var(--transition-normal), border-color var(--transition-normal);
}

.action-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.accent-teal {
    background:
        radial-gradient(circle at top right, rgba(84, 196, 211, 0.2), transparent 34%),
        rgba(255, 255, 255, 0.88);
}

.accent-gold {
    background:
        radial-gradient(circle at top right, rgba(216, 155, 55, 0.2), transparent 30%),
        rgba(255, 255, 255, 0.88);
}

.action-icon {
    width: 54px;
    height: 54px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 18px;
    background: rgba(15, 124, 130, 0.1);
    color: var(--accent-primary);
}

.accent-gold .action-icon {
    background: rgba(216, 155, 55, 0.12);
    color: var(--accent-warning);
}

.action-icon svg {
    width: 24px;
    height: 24px;
}

.action-card h2 {
    font-family: var(--font-heading);
    font-size: 1.18rem;
    font-weight: 700;
}

.action-card p {
    color: var(--text-secondary);
    font-size: 0.9rem;
    line-height: 1.6;
}

.action-link {
    margin-top: auto;
    color: var(--accent-primary);
    font-weight: 700;
}

.chart-legend {
    display: flex;
    gap: 12px;
    color: var(--text-secondary);
    font-size: 0.76rem;
    font-weight: 600;
}

.chart-legend span {
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.legend-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.legend-dot.in {
    background: var(--accent-primary);
}

.legend-dot.out {
    background: var(--accent-secondary);
}

.traffic-chart {
    margin-top: 22px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px;
    min-height: 224px;
}

.chart-column {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 14px;
}

.bar-wrap {
    width: 100%;
    height: 184px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 6px;
}

.bar-stack {
    position: relative;
    width: min(22px, 100%);
    border-radius: 12px 12px 4px 4px;
    transition: transform var(--transition-fast), filter var(--transition-fast);
}

.bar-stack span {
    position: absolute;
    left: 50%;
    top: -28px;
    transform: translateX(-50%);
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--text-muted);
}

.bar-stack.in {
    background: linear-gradient(180deg, rgba(84, 196, 211, 0.26), var(--accent-primary));
}

.bar-stack.out {
    background: linear-gradient(180deg, rgba(43, 109, 138, 0.26), var(--accent-secondary));
}

.chart-column:hover .bar-stack {
    transform: translateY(-2px);
    filter: brightness(1.02);
}

.chart-column strong {
    color: var(--text-secondary);
    font-size: 0.82rem;
}

.feed-list {
    margin-top: 18px;
    display: grid;
    gap: 12px;
}

.feed-item {
    display: grid;
    grid-template-columns: 12px 70px 1fr;
    gap: 14px;
    padding: 14px;
    border-radius: 20px;
    background: rgba(236, 244, 246, 0.72);
    border: 1px solid rgba(24, 49, 77, 0.08);
}

.feed-link {
    color: var(--accent-primary);
    font-size: 0.82rem;
    font-weight: 700;
}

.feed-item {
    grid-template-columns: 12px 70px 1fr;
    align-items: start;
}

.feed-marker {
    width: 12px;
    height: 12px;
    margin-top: 5px;
    border-radius: 50%;
    box-shadow: 0 0 0 6px rgba(15, 124, 130, 0.08);
}

.feed-marker.in {
    background: var(--accent-success);
    box-shadow: 0 0 0 6px rgba(20, 134, 109, 0.1);
}

.feed-marker.out {
    background: var(--accent-warning);
    box-shadow: 0 0 0 6px rgba(184, 111, 33, 0.1);
}

.feed-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.feed-meta strong {
    color: var(--text-primary);
    font-size: 0.88rem;
}

.feed-meta span {
    color: var(--text-muted);
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

@media (max-width: 1280px) {
    .dashboard-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        grid-template-areas:
            "metrics metrics"
            "action-guest action-employees"
            "traffic traffic"
            "feed feed";
    }
}

@media (max-width: 1080px) {
    .dashboard-hero {
        grid-template-columns: 1fr;
    }

    .hero-copy .page-title {
        max-width: none;
    }
}

@media (max-width: 768px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
        grid-template-areas:
            "metrics"
            "action-guest"
            "action-employees"
            "traffic"
            "feed";
    }

    .hero-copy,
    .hero-board,
    .dashboard-card {
        padding: 20px;
        border-radius: 24px;
    }

    .metrics-main,
    .metrics-foot,
    .board-metrics {
        grid-template-columns: 1fr;
    }

    .feed-item {
        grid-template-columns: 12px 1fr;
    }

    .feed-meta {
        grid-column: 2;
        flex-direction: row;
        align-items: center;
        gap: 8px;
    }

    .feed-copy {
        grid-column: 2;
    }
}
</style>
