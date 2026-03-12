<template>
    <div class="bento-dashboard animate-in">
        <!-- Bento Header -->
        <header class="bento-header">
            <div class="greeting">
                <h1 class="page-title">Tổng quan Hệ thống</h1>
                <p class="page-subtitle">Hôm nay là {{ currentDate }}. Hệ thống V-Shield đang hoạt động ổn định.</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-secondary btn-icon" title="Cài đặt">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 20px; height: 20px;">
                        <path d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
                        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
                    </svg>
                </button>
                <button class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Báo cáo
                </button>
            </div>
        </header>

        <!-- Bento Grid Layout -->
        <div class="bento-grid">
            <!-- Main Stats (Spans 2 columns) -->
            <div class="bento-card col-span-2 row-span-1 stats-overview">
                <div class="stats-header">
                    <h3>Tổng quan nhân sự</h3>
                    <span class="live-badge"><span class="pulse-dot"></span> Đang cập nhật</span>
                </div>
                <div class="stats-content">
                    <div class="stat-highlight">
                        <div class="stat-value">{{ totalEmployees }}</div>
                        <div class="stat-label">Tổng nhân viên</div>
                    </div>
                    <div class="stat-divider"></div>
                    <div class="stat-highlight">
                        <div class="stat-value green">{{ activeEmployees }}</div>
                        <div class="stat-label">Đang hoạt động</div>
                    </div>
                </div>
            </div>

            <!-- Focus Quick Action 1 -->
            <router-link to="/pre-registrations" class="bento-card interactive-card action-primary">
                <div class="action-icon-large">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/>
                        <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
                        <path d="M9 14l2 2 4-4"/>
                    </svg>
                </div>
                <h3>Đăng ký khách</h3>
                <p>Tạo link QR trước cho khách</p>
                <div class="arrow-indicator">→</div>
            </router-link>

            <!-- Focus Quick Action 2 -->
            <router-link to="/monitoring" class="bento-card interactive-card action-secondary">
                <div class="action-icon-large">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                        <circle cx="12" cy="13" r="4"/>
                    </svg>
                </div>
                <h3>Live Camera</h3>
                <p>Giám sát ra vào trực tiếp</p>
                <div class="arrow-indicator">→</div>
            </router-link>

            <!-- Chart Activity -->
            <div class="bento-card col-span-2 row-span-2 activity-chart">
                <div class="card-header">
                    <h3>Lưu lượng ra/vào tuần này</h3>
                    <div class="chart-legend">
                        <span class="legend-item"><span class="legend-dot in"></span> Vào (187)</span>
                        <span class="legend-item"><span class="legend-dot out"></span> Ra (142)</span>
                    </div>
                </div>
                <!-- Mini Minimalist Chart -->
                <div class="minimal-chart">
                    <div v-for="day in weekData" :key="day.label" class="chart-col">
                        <div class="bar-stack">
                            <div class="bar in" :style="{ height: day.inPercent + '%' }"><div class="tt">{{day.checkIn}}</div></div>
                            <div class="bar out" :style="{ height: day.outPercent + '%' }"><div class="tt">{{day.checkOut}}</div></div>
                        </div>
                        <div class="col-lbl">{{ day.label }}</div>
                    </div>
                </div>
            </div>

            <!-- Recent Logs list (Spans height) -->
            <div class="bento-card col-span-2 row-span-2 recent-logs-card">
                <div class="card-header">
                    <h3>Hoạt động mới nhất</h3>
                    <router-link to="/access-logs" class="link-muted">Xem tất cả</router-link>
                </div>
                <div class="logs-feed">
                    <div v-for="log in recentLogs" :key="log.id" class="feed-item">
                        <div class="feed-marker" :class="log.type"></div>
                        <div class="feed-time">{{ log.time }}</div>
                        <div class="feed-content">
                            <strong>{{ log.name }}</strong>
                            <span>{{ log.detail }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getSummary } from '../services/statisticsApi'

// Date
const currentDate = computed(() => {
    const d = new Date()
    return d.toLocaleDateString('vi-VN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
})

// Stats
const totalEmployees = ref('...')
const activeEmployees = ref('...')
let eventSource = null;

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
            } catch (err) {}
        }
    } catch (error) {
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
    { id: 4, name: 'Phạm Minh Đức', detail: 'Vào cổng A - Máy khách KH29', type: 'in', time: '08:25' },
    { id: 5, name: 'Võ Thị Em', detail: 'Ra cổng C', type: 'out', time: '08:30' },
    { id: 6, name: 'Khách VIP', detail: 'Đã check-in mã QR', type: 'in', time: '08:35' },
])
</script>

<style scoped>
.bento-dashboard {
    padding: 0;
    max-width: 1400px;
    margin: 0 auto;
}

.bento-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    gap: 16px;
    flex-wrap: wrap;
}

.bento-header .greeting h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 4px;
}

.bento-header .greeting p {
    color: var(--text-secondary);
    font-size: 0.95rem;
}

.bento-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-auto-rows: 180px;
    gap: 20px;
}

/* Card Base */
.bento-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    padding: 24px;
    display: flex;
    flex-direction: column;
    position: relative;
    overflow: hidden;
    transition: all var(--transition-normal);
}

.col-span-2 { grid-column: span 2; }
.row-span-1 { grid-row: span 1; }
.row-span-2 { grid-row: span 2; }

/* Interactive Cards */
.interactive-card {
    cursor: pointer;
    text-decoration: none;
    color: var(--text-primary);
}
.interactive-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-color-hover);
}
.interactive-card.action-primary {
    background: linear-gradient(145deg, var(--bg-card), var(--bg-card-hover));
}
.interactive-card.action-secondary {
    background: var(--bg-card);
}
.action-icon-large {
    width: 48px;
    height: 48px;
    background: rgba(16, 121, 196, 0.1); /* lochmara accent */
    color: var(--accent-primary);
    border-radius: var(--border-radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: auto;
}
.action-icon-large svg { width: 24px; height: 24px; }
.interactive-card h3 { font-size: 1.1rem; margin-bottom: 4px; font-weight: 600; }
.interactive-card p { font-size: 0.85rem; color: var(--text-secondary); }
.arrow-indicator {
    position: absolute;
    bottom: 24px;
    right: 24px;
    font-size: 1.2rem;
    color: var(--text-muted);
    transition: transform var(--transition-fast);
}
.interactive-card:hover .arrow-indicator {
    transform: translateX(4px);
    color: var(--accent-primary);
}

/* Stats Overview */
.stats-overview {
    justify-content: space-between;
}
.stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.stats-header h3 { font-size: 1rem; color: var(--text-secondary); font-weight: 500;}
.live-badge {
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent-success);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}
.pulse-dot {
    width: 6px; height: 6px; background: currentColor; border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

.stats-content {
    display: flex;
    align-items: flex-end;
    gap: 32px;
}
.stat-highlight { flex: 1; }
.stat-value { font-size: 3rem; font-weight: 700; line-height: 1; margin-bottom: 8px; color: var(--text-primary); }
.stat-value.green { color: var(--accent-success); }
.stat-label { font-size: 0.9rem; color: var(--text-muted); }
.stat-divider { width: 1px; height: 60px; background: var(--border-color); }

/* Chart Area */
.activity-chart .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: auto;
}
.activity-chart h3 { font-size: 1.1rem; font-weight: 600; }
.chart-legend { display: flex; gap: 12px; }
.legend-item { font-size: 0.8rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px;}
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.legend-dot.in { background: var(--accent-primary); }
.legend-dot.out { background: var(--accent-secondary); }

.minimal-chart {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    height: 100%;
    padding-top: 40px;
}
.chart-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    flex: 1;
}
.bar-stack {
    height: 180px;
    display: flex;
    align-items: flex-end;
    gap: 4px;
    width: 100%;
    justify-content: center;
}
.bar {
    width: 16px;
    border-radius: 4px 4px 0 0;
    position: relative;
    cursor: pointer;
    transition: height 0.6s ease;
}
.bar.in { background: var(--accent-primary); }
.bar.out { background: var(--accent-secondary); }
.bar .tt {
    position: absolute; top: -26px; left: 50%; transform: translateX(-50%);
    background: var(--bg-secondary); color: var(--text-primary);
    font-size: 0.7rem; padding: 2px 6px; border-radius: 4px;
    opacity: 0; transition: opacity 0.2s; pointer-events: none;
    border: 1px solid var(--border-color);
}
.bar:hover { filter: brightness(1.2); }
.bar:hover .tt { opacity: 1; }
.col-lbl { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }

/* Logs Feed */
.recent-logs-card {
    display: flex;
    flex-direction: column;
}
.recent-logs-card .card-header {
    display: flex; justify-content: space-between; margin-bottom: 24px;
}
.link-muted { color: var(--text-muted); font-size: 0.85rem; text-decoration: none; transition: color 0.2s;}
.link-muted:hover { color: var(--accent-primary); }
.logs-feed {
    display: flex;
    flex-direction: column;
    gap: 20px;
    overflow-y: auto;
    padding-right: 8px;
}
.feed-item {
    display: flex;
    gap: 16px;
    align-items: flex-start;
}
.feed-marker {
    width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; flex-shrink: 0;
    position: relative;
}
.feed-marker.in { background: var(--accent-primary); box-shadow: 0 0 10px rgba(16, 121, 196, 0.4); }
.feed-marker.out { background: var(--accent-secondary); box-shadow: 0 0 10px rgba(139, 92, 246, 0.4); }
/* connected line */
.feed-marker::after {
    content: ''; position: absolute; top: 14px; left: 4px; width: 2px; height: 40px;
    background: var(--border-color);
}
.feed-item:last-child .feed-marker::after { display: none; }
.feed-time {
    font-size: 0.8rem; color: var(--text-muted); font-weight: 600; width: 45px; flex-shrink: 0;
}
.feed-content {
    display: flex; flex-direction: column; gap: 2px;
}
.feed-content strong { font-size: 0.9rem; color: var(--text-primary); font-weight: 500;}
.feed-content span { font-size: 0.8rem; color: var(--text-secondary); }

@media (max-width: 1200px) {
    .bento-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
    .bento-grid { grid-template-columns: 1fr; grid-auto-rows: min-content; }
    .col-span-2, .row-span-1, .row-span-2 { grid-column: span 1; grid-row: auto; }
    .bar-stack { height: 120px; }
}
</style>
