<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Lịch sử Ra/Vào</h1>
                <p class="page-subtitle">Theo dõi lịch sử check-in, check-out nhân viên và phương tiện</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-secondary btn-sm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 16px; height: 16px;">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Xuất Excel
                </button>
            </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-icon blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" />
                        <polyline points="10 17 15 12 10 7" />
                        <line x1="15" y1="12" x2="3" y2="12" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>187</h3>
                    <p>Lượt vào hôm nay</p>
                </div>
            </div>
            <div class="stat-card purple">
                <div class="stat-icon purple">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                        <polyline points="16 17 21 12 16 7" />
                        <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>142</h3>
                    <p>Lượt ra hôm nay</p>
                </div>
            </div>
            <div class="stat-card green">
                <div class="stat-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                        <circle cx="9" cy="7" r="4" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>45</h3>
                    <p>Đang trong KV</p>
                </div>
            </div>
            <div class="stat-card orange">
                <div class="stat-icon orange">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>3</h3>
                    <p>Cảnh báo</p>
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="card" style="margin-bottom: 20px; padding: 16px 20px;">
            <div class="filter-group">
                <div class="search-bar" style="max-width: 280px;">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 18px; height: 18px;">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm theo tên, biển số..." />
                </div>
                <select v-model="filterType" class="filter-select">
                    <option value="">Tất cả loại</option>
                    <option value="check-in">Check-in</option>
                    <option value="check-out">Check-out</option>
                </select>
                <select v-model="filterGate" class="filter-select">
                    <option value="">Tất cả cổng</option>
                    <option value="Cổng A">Cổng A</option>
                    <option value="Cổng B">Cổng B</option>
                    <option value="Cổng C">Cổng C</option>
                </select>
                <input v-model="filterDate" type="date" class="filter-select" />
            </div>
        </div>

        <!-- Timeline View -->
        <div class="card" style="padding: 0;">
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Nhân viên</th>
                            <th>Loại</th>
                            <th>Cổng</th>
                            <th>Phương tiện</th>
                            <th>Phương thức</th>
                            <th>Ghi chú</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="log in filteredLogs" :key="log.id">
                            <td>
                                <div class="time-cell">
                                    <span class="time-main">{{ log.time }}</span>
                                    <span class="time-date">{{ log.date }}</span>
                                </div>
                            </td>
                            <td>
                                <div class="avatar-group">
                                    <div class="avatar" style="width: 32px; height: 32px; font-size: 0.75rem;">{{
                                        log.initials }}</div>
                                    <div class="avatar-info">
                                        <span class="avatar-name">{{ log.employee }}</span>
                                        <span class="avatar-sub">{{ log.empCode }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="badge" :class="log.type">
                                    <span class="badge-dot"></span>
                                    {{ log.type === 'check-in' ? 'Vào' : 'Ra' }}
                                </span>
                            </td>
                            <td>{{ log.gate }}</td>
                            <td>
                                <span v-if="log.plate" class="plate-tag">{{ log.plate }}</span>
                                <span v-else style="color: var(--text-muted);">Đi bộ</span>
                            </td>
                            <td>
                                <span class="method-badge" :class="log.method">
                                    {{ getMethodLabel(log.method) }}
                                </span>
                            </td>
                            <td style="color: var(--text-secondary); font-size: 0.8rem;">{{ log.note || '—' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="pagination" style="padding: 16px 20px;">
                <span class="pagination-info">Hiển thị 1-{{ filteredLogs.length }} / {{ logs.length }} bản ghi</span>
                <div class="pagination-buttons">
                    <button class="pagination-btn">‹</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">3</button>
                    <button class="pagination-btn">4</button>
                    <button class="pagination-btn">›</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const filterType = ref('')
const filterGate = ref('')
const filterDate = ref('')

const getMethodLabel = (method) => {
    const labels = { face: 'Khuôn mặt', plate: 'Biển số', card: 'Thẻ từ', manual: 'Thủ công' }
    return labels[method] || method
}

const logs = ref([
    { id: 1, time: '08:05', date: '05/03/2026', employee: 'Nguyễn Văn An', initials: 'NA', empCode: 'NV001', type: 'check-in', gate: 'Cổng A', plate: '51A-123.45', method: 'face', note: '' },
    { id: 2, time: '08:12', date: '05/03/2026', employee: 'Trần Thị Bình', initials: 'TB', empCode: 'NV002', type: 'check-in', gate: 'Cổng B', plate: null, method: 'card', note: '' },
    { id: 3, time: '08:20', date: '05/03/2026', employee: 'Lê Hoàng Cường', initials: 'LC', empCode: 'NV003', type: 'check-out', gate: 'Cổng A', plate: '30H-567.89', method: 'plate', note: 'Ra sớm - có phép' },
    { id: 4, time: '08:25', date: '05/03/2026', employee: 'Phạm Minh Đức', initials: 'PD', empCode: 'NV004', type: 'check-in', gate: 'Cổng A', plate: '51B-234.56', method: 'face', note: '' },
    { id: 5, time: '08:30', date: '05/03/2026', employee: 'Võ Thị Em', initials: 'VE', empCode: 'NV005', type: 'check-out', gate: 'Cổng C', plate: null, method: 'card', note: '' },
    { id: 6, time: '08:35', date: '05/03/2026', employee: 'Hoàng Văn Phong', initials: 'HP', empCode: 'NV006', type: 'check-in', gate: 'Cổng A', plate: '51F-789.01', method: 'plate', note: '' },
    { id: 7, time: '07:55', date: '05/03/2026', employee: 'Đỗ Thị Giang', initials: 'DG', empCode: 'NV007', type: 'check-in', gate: 'Cổng B', plate: null, method: 'face', note: '' },
    { id: 8, time: '08:10', date: '05/03/2026', employee: 'Bùi Quốc Huy', initials: 'BH', empCode: 'NV008', type: 'check-in', gate: 'Cổng A', plate: '51G-333.44', method: 'face', note: '' },
    { id: 9, time: '17:05', date: '04/03/2026', employee: 'Nguyễn Văn An', initials: 'NA', empCode: 'NV001', type: 'check-out', gate: 'Cổng A', plate: '51A-123.45', method: 'plate', note: '' },
    { id: 10, time: '17:30', date: '04/03/2026', employee: 'Trần Thị Bình', initials: 'TB', empCode: 'NV002', type: 'check-out', gate: 'Cổng B', plate: null, method: 'card', note: '' },
    { id: 11, time: '09:15', date: '05/03/2026', employee: 'Lý Thanh Hải', initials: 'LH', empCode: 'NV010', type: 'check-in', gate: 'Cổng A', plate: '51D-456.78', method: 'manual', note: 'Khách - đăng ký tạm' },
    { id: 12, time: '11:00', date: '05/03/2026', employee: 'Nguyễn Minh Tuấn', initials: 'NT', empCode: 'NV012', type: 'check-out', gate: 'Cổng C', plate: null, method: 'face', note: 'Nghỉ trưa' },
])

const filteredLogs = computed(() => {
    return logs.value.filter(log => {
        const matchSearch = !searchQuery.value || log.employee.toLowerCase().includes(searchQuery.value.toLowerCase()) || (log.plate && log.plate.toLowerCase().includes(searchQuery.value.toLowerCase()))
        const matchType = !filterType.value || log.type === filterType.value
        const matchGate = !filterGate.value || log.gate === filterGate.value
        return matchSearch && matchType && matchGate
    })
})
</script>

<style scoped>
.header-actions {
    display: flex;
    gap: 10px;
}

.time-cell {
    display: flex;
    flex-direction: column;
}

.time-main {
    font-weight: 600;
    font-size: 0.95rem;
    font-family: monospace;
}

.time-date {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.plate-tag {
    font-family: monospace;
    font-weight: 600;
    font-size: 0.8rem;
    padding: 3px 10px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 6px;
}

.method-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.method-badge.face {
    background: rgba(59, 130, 246, 0.12);
    color: var(--accent-primary);
}

.method-badge.plate {
    background: rgba(139, 92, 246, 0.12);
    color: var(--accent-secondary);
}

.method-badge.card {
    background: rgba(16, 185, 129, 0.12);
    color: var(--accent-success);
}

.method-badge.manual {
    background: rgba(245, 158, 11, 0.12);
    color: var(--accent-warning);
}
</style>
