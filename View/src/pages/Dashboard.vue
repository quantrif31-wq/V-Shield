<template>
    <div class="page-container animate-in">
        <!-- Page Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Dashboard</h1>
                <p class="page-subtitle">Tổng quan hệ thống quản lý ra/vào</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-secondary btn-sm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 16px; height: 16px;">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Xuất báo cáo
                </button>
            </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card blue" v-for="stat in stats" :key="stat.label" :class="stat.color">
                <div class="stat-icon" :class="stat.color">
                    <span v-html="stat.icon"></span>
                </div>
                <div class="stat-info">
                    <h3>{{ stat.value }}</h3>
                    <p>{{ stat.label }}</p>
                    <span class="stat-change" :class="stat.trend">{{ stat.change }}</span>
                </div>
            </div>
        </div>

        <!-- Main Grid -->
        <div class="dashboard-grid">
            <!-- Activity Chart -->
            <div class="card chart-card">
                <div class="card-header">
                    <h3 class="card-title">Hoạt động ra/vào trong tuần</h3>
                    <div class="chart-legend">
                        <span class="legend-item"><span class="legend-dot in"></span> Vào</span>
                        <span class="legend-item"><span class="legend-dot out"></span> Ra</span>
                    </div>
                </div>
                <div class="chart-container">
                    <div class="chart-bars">
                        <div v-for="day in weekData" :key="day.label" class="chart-bar-group">
                            <div class="bar-wrapper">
                                <div class="bar bar-in" :style="{ height: day.inPercent + '%' }">
                                    <span class="bar-tooltip">{{ day.checkIn }}</span>
                                </div>
                                <div class="bar bar-out" :style="{ height: day.outPercent + '%' }">
                                    <span class="bar-tooltip">{{ day.checkOut }}</span>
                                </div>
                            </div>
                            <span class="bar-label">{{ day.label }}</span>
                        </div>
                    </div>
                    <div class="chart-y-axis">
                        <span>200</span>
                        <span>150</span>
                        <span>100</span>
                        <span>50</span>
                        <span>0</span>
                    </div>
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="card activity-card">
                <div class="card-header">
                    <h3 class="card-title">Hoạt động gần đây</h3>
                    <router-link to="/access-logs" class="btn btn-sm btn-secondary">Xem tất cả</router-link>
                </div>
                <div class="activity-list">
                    <div v-for="log in recentLogs" :key="log.id" class="activity-item">
                        <div class="activity-avatar" :class="log.type">
                            {{ log.initials }}
                        </div>
                        <div class="activity-info">
                            <p class="activity-name">{{ log.name }}</p>
                            <span class="activity-detail">{{ log.detail }}</span>
                        </div>
                        <div class="activity-meta">
                            <span class="badge" :class="log.type">
                                <span class="badge-dot"></span>
                                {{ log.type === 'check-in' ? 'Vào' : 'Ra' }}
                            </span>
                            <span class="activity-time">{{ log.time }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
            <h3 class="section-title">Thao tác nhanh</h3>
            <div class="actions-grid">
                <router-link to="/employees" class="action-card">
                    <div class="action-icon blue">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                            <circle cx="8.5" cy="7" r="4" />
                            <line x1="20" y1="8" x2="20" y2="14" />
                            <line x1="23" y1="11" x2="17" y2="11" />
                        </svg>
                    </div>
                    <span>Thêm nhân viên</span>
                </router-link>
                <router-link to="/vehicles" class="action-card">
                    <div class="action-icon green">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="1" y="3" width="15" height="13" rx="2" />
                            <path d="M16 8h4l3 3v5h-7V8z" />
                            <circle cx="5.5" cy="18.5" r="2.5" />
                            <circle cx="18.5" cy="18.5" r="2.5" />
                        </svg>
                    </div>
                    <span>Đăng ký xe</span>
                </router-link>
                <router-link to="/monitoring" class="action-card">
                    <div class="action-icon purple">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                            <circle cx="12" cy="13" r="4" />
                        </svg>
                    </div>
                    <span>Xem camera</span>
                </router-link>
                <router-link to="/access-logs" class="action-card">
                    <div class="action-icon orange">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                            <polyline points="14 2 14 8 20 8" />
                            <line x1="16" y1="13" x2="8" y2="13" />
                            <line x1="16" y1="17" x2="8" y2="17" />
                        </svg>
                    </div>
                    <span>Xem báo cáo</span>
                </router-link>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getSummary } from '../services/statisticsApi'

const totalEmployees = ref('...')
const activeEmployees = ref('...')

const stats = ref([
    {
        label: 'Tổng nhân viên',
        value: totalEmployees,
        change: 'Cập nhật realtime',
        trend: 'up',
        color: 'blue',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>'
    },
    {
        label: 'Nhân viên đang HĐ',
        value: activeEmployees,
        change: 'Trạng thái hoạt động',
        trend: 'up',
        color: 'green',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
    },
    {
        label: 'Lượt vào hôm nay',
        value: '187',
        change: '↑ +15% so với hôm qua',
        trend: 'up',
        color: 'purple',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>'
    },
    {
        label: 'Lượt ra hôm nay',
        value: '142',
        change: '↓ -3% so với hôm qua',
        trend: 'down',
        color: 'orange',
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>'
    },
])

let eventSource = null;

onMounted(async () => {
    try {
        // Init fake data or current data
        const summary = await getSummary()
        totalEmployees.value = summary.totalEmployees.toString()
        activeEmployees.value = summary.activeEmployees.toString()

        // Connect to SSE stream
        eventSource = new EventSource('http://localhost:5107/api/Statistics/employees/stream')
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                totalEmployees.value = data.totalEmployees.toString()
                activeEmployees.value = data.activeEmployees.toString()
            } catch (err) {
                console.error("Lỗi parse SSE:", err)
            }
        }
        eventSource.onerror = (error) => {
            console.error("SSE Error:", error)
            eventSource.close()
        }
    } catch (error) {
        console.error("Lỗi fetch summary:", error)
        totalEmployees.value = 'Lỗi'
        activeEmployees.value = 'Lỗi'
    }
})

onUnmounted(() => {
    if (eventSource) {
        eventSource.close()
    }
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
    { id: 1, name: 'Nguyễn Văn An', initials: 'NA', detail: 'Cổng A - Xe 51A-123.45', type: 'check-in', time: '08:05' },
    { id: 2, name: 'Trần Thị Bình', initials: 'TB', detail: 'Cổng B - Đi bộ', type: 'check-in', time: '08:12' },
    { id: 3, name: 'Lê Hoàng Cường', initials: 'LC', detail: 'Cổng A - Xe 30H-567.89', type: 'check-out', time: '08:20' },
    { id: 4, name: 'Phạm Minh Đức', initials: 'PD', detail: 'Cổng A - Xe 51B-234.56', type: 'check-in', time: '08:25' },
    { id: 5, name: 'Võ Thị Em', initials: 'VE', detail: 'Cổng C - Đi bộ', type: 'check-out', time: '08:30' },
    { id: 6, name: 'Hoàng Văn Phong', initials: 'HP', detail: 'Cổng A - Xe 51F-789.01', type: 'check-in', time: '08:35' },
])
</script>

<style scoped>
/* Dashboard Grid */
.dashboard-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 20px;
    margin-bottom: 28px;
}

/* Chart */
.chart-card {
    min-height: 360px;
}

.chart-legend {
    display: flex;
    gap: 16px;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    color: var(--text-secondary);
}

.legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 3px;
}

.legend-dot.in {
    background: var(--accent-primary);
}

.legend-dot.out {
    background: var(--accent-secondary);
}

.chart-container {
    display: flex;
    gap: 12px;
    height: 260px;
    position: relative;
}

.chart-y-axis {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-size: 0.7rem;
    color: var(--text-muted);
    padding: 0 0 24px;
    min-width: 30px;
    order: -1;
}

.chart-bars {
    flex: 1;
    display: flex;
    align-items: flex-end;
    gap: 16px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border-color);
}

.chart-bar-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.bar-wrapper {
    display: flex;
    gap: 4px;
    align-items: flex-end;
    height: 220px;
    width: 100%;
    justify-content: center;
}

.bar {
    width: 18px;
    border-radius: 4px 4px 0 0;
    position: relative;
    transition: height 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    min-height: 4px;
}

.bar-in {
    background: var(--accent-primary);
    opacity: 0.85;
}

.bar-out {
    background: var(--accent-secondary);
    opacity: 0.85;
}

.bar:hover {
    opacity: 1;
    filter: brightness(1.2);
}

.bar-tooltip {
    display: none;
    position: absolute;
    top: -28px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--bg-secondary);
    color: var(--text-primary);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    white-space: nowrap;
    border: 1px solid var(--border-color);
}

.bar:hover .bar-tooltip {
    display: block;
}

.bar-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* Activity */
.activity-card {
    max-height: 420px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.activity-list {
    flex: 1;
    overflow-y: auto;
}

.activity-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border-color);
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.75rem;
    flex-shrink: 0;
}

.activity-avatar.check-in {
    background: rgba(16, 185, 129, 0.15);
    color: var(--accent-success);
}

.activity-avatar.check-out {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
}

.activity-info {
    flex: 1;
    min-width: 0;
}

.activity-name {
    font-weight: 600;
    font-size: 0.85rem;
}

.activity-detail {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.activity-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
}

.activity-time {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* Quick Actions */
.quick-actions {
    margin-top: 8px;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text-primary);
}

.actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
}

.action-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    transition: all var(--transition-normal);
    cursor: pointer;
}

.action-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-color-hover);
}

.action-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--border-radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
}

.action-icon svg {
    width: 24px;
    height: 24px;
}

.action-icon.blue {
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent-primary);
}

.action-icon.green {
    background: rgba(16, 185, 129, 0.15);
    color: var(--accent-success);
}

.action-icon.purple {
    background: rgba(139, 92, 246, 0.15);
    color: var(--accent-secondary);
}

.action-icon.orange {
    background: rgba(245, 158, 11, 0.15);
    color: var(--accent-warning);
}

.action-card span {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.action-card:hover span {
    color: var(--text-primary);
}

.header-actions {
    display: flex;
    gap: 10px;
}

@media (max-width: 1024px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}
</style>
