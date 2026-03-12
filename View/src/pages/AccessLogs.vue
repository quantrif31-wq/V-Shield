<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Lịch sử Ra/Vào</h1>
                <p class="page-subtitle">Theo dõi lịch sử check-in, check-out nhân sự và khách</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-secondary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Xuất Excel
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini" style="grid-template-columns: repeat(4, 1fr);">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val blue">187</div>
                    <div class="stat-lbl">Lượt vào hôm nay</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper purple" style="background: rgba(168, 85, 247, 0.1); color: #a855f7;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: #a855f7;">142</div>
                    <div class="stat-lbl">Lượt ra hôm nay</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val green">45</div>
                    <div class="stat-lbl">Đang trong KV</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper orange" style="background: rgba(249, 115, 22, 0.1); color: var(--accent-warning);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: var(--accent-warning);">3</div>
                    <div class="stat-lbl">Cảnh báo</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm theo tên hoặc biển số..." />
                </div>
                <div class="filter-box" style="display: flex; gap: 12px; flex-wrap: wrap;">
                    <select v-model="filterType" class="minimal-select">
                        <option value="">Tất cả chiều</option>
                        <option value="check-in">Vào (Check-in)</option>
                        <option value="check-out">Ra (Check-out)</option>
                    </select>
                    <select v-model="filterGate" class="minimal-select">
                        <option value="">Tất cả cổng</option>
                        <option value="Cổng A">Cổng A</option>
                        <option value="Cổng B">Cổng B</option>
                        <option value="Cổng C">Cổng C</option>
                    </select>
                    <input v-model="filterDate" type="date" class="minimal-select" />
                </div>
            </div>
            
            <!-- Sleek Table -->
            <div class="sleek-table-container">
                <table class="sleek-table">
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Người ra/vào</th>
                            <th>Phân loại</th>
                            <th>Cổng</th>
                            <th>Phương tiện</th>
                            <th>Bằng chứng</th>
                            <th style="max-width: 150px;">Ghi chú</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="log in filteredLogs" :key="log.id" class="table-row">
                            <td>
                                <div class="time-cell">
                                    <span class="time-main">{{ log.time }}</span>
                                    <span class="time-date">{{ log.date }}</span>
                                </div>
                            </td>
                            <td>
                                <div class="user-cell">
                                    <div class="avatar" :style="{ background: getAvatarColor(log.initials) }">{{ log.initials }}</div>
                                    <div class="user-info">
                                        <span class="user-name">{{ log.employee }}</span>
                                        <span class="user-id">{{ log.empCode }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="status-pill minimal" :class="log.type">
                                    <span class="pill-dot"></span>
                                    {{ log.type === 'check-in' ? 'VÀO' : 'RA' }}
                                </span>
                            </td>
                            <td><span class="gate-txt">{{ log.gate }}</span></td>
                            <td>
                                <span v-if="log.plate" class="plate">{{ log.plate }}</span>
                                <span v-else class="walk-txt">Đi bộ</span>
                            </td>
                            <td>
                                <span class="method-badge" :class="log.method">
                                    {{ getMethodLabel(log.method) }}
                                </span>
                            </td>
                            <td>
                                <div class="desc-cell" :title="log.note">{{ log.note || '—' }}</div>
                            </td>
                        </tr>
                        <tr v-if="filteredLogs.length === 0">
                            <td colspan="7" class="empty-layout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--text-muted);"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                                <p>Không tìm thấy bản ghi nào khớp với bộ lọc</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="pagination-footer">
                <span class="showing-txt">Hiển thị {{ filteredLogs.length }} / {{ logs.length }} bản ghi</span>
                <div class="pg-controls">
                    <button class="pg-btn">‹</button>
                    <button class="pg-btn active">1</button>
                    <button class="pg-btn">2</button>
                    <button class="pg-btn">3</button>
                    <button class="pg-btn">4</button>
                    <button class="pg-btn">›</button>
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

const getAvatarColor = (str) => {
    let hash = 0; for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const avColors = [ '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e' ];
    return avColors[Math.abs(hash) % avColors.length];
}

const logs = ref([
    { id: 1, time: '08:05', date: '05/03/2026', employee: 'Nguyễn Văn An', initials: 'NA', empCode: 'NV001', type: 'check-in', gate: 'Cổng A', plate: '51A-123.45', method: 'face', note: '' },
    { id: 2, time: '08:12', date: '05/03/2026', employee: 'Trần Thị Bình', initials: 'TB', empCode: 'NV002', type: 'check-in', gate: 'Cổng B', plate: null, method: 'card', note: '' },
    { id: 3, time: '08:20', date: '05/03/2026', employee: 'Lê Hoàng Cường', initials: 'LC', empCode: 'NV003', type: 'check-out', gate: 'Cổng A', plate: '30H-567.89', method: 'plate', note: 'Ra sớm - có phép' },
    { id: 4, time: '08:25', date: '05/03/2026', employee: 'Phạm Minh Đức', initials: 'PD', empCode: 'NV004', type: 'check-in', gate: 'Cổng A', plate: '51B-234.56', method: 'face', note: '' },
    { id: 5, time: '08:30', date: '05/03/2026', employee: 'Võ Thị Em', initials: 'VE', empCode: 'NV005', type: 'check-out', gate: 'Cổng C', plate: null, method: 'card', note: '' },
    { id: 6, time: '08:35', date: '05/03/2026', employee: 'Hoàng Văn Phong', initials: 'HP', empCode: 'NV006', type: 'check-in', gate: 'Cổng A', plate: '51F-789.01', method: 'plate', note: '' },
    { id: 7, time: '07:55', date: '05/03/2026', employee: 'Đỗ Thị Giang', initials: 'ĐG', empCode: 'NV007', type: 'check-in', gate: 'Cổng B', plate: null, method: 'face', note: '' },
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
/* Page Layout */
.bento-header { margin-bottom: 24px; padding: 0 4px; display: flex; justify-content: space-between; align-items: center; }
.bento-header .greeting h1 { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
.bento-header .greeting p { color: var(--text-secondary); font-size: 0.95rem; }

/* Grid Mini */
.bento-grid-mini { display: grid; gap: 20px; margin-bottom: 24px; }
.bento-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--border-radius-lg); padding: 24px; }
.stat-card { display: flex; align-items: center; gap: 16px; transition: transform var(--transition-normal); }
.stat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.stat-icon-wrapper { width: 56px; height: 56px; border-radius: 14px; display: flex; justify-content: center; align-items: center; }
.stat-icon-wrapper svg { width: 28px; height: 28px; }
.stat-icon-wrapper.blue { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.stat-icon-wrapper.green { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.stat-val { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-val.blue { color: var(--accent-primary); }
.stat-val.green { color: var(--accent-success); }
.stat-lbl { font-size: 0.9rem; color: var(--text-muted); font-weight: 500;}

/* Table Box */
.table-section { padding: 0; overflow: hidden; display: flex; flex-direction: column; min-height: 500px; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border-color); }
.search-box { position: relative; width: 320px; display: flex; align-items: center; }
.search-icon { position: absolute; left: 14px; color: var(--text-muted); width: 18px; }
.search-box input { width: 100%; padding: 10px 14px 10px 42px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; }
.search-box input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 2px rgba(16, 121, 196, 0.2); }
.minimal-select { padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); cursor: pointer; outline: none; }
input[type="date"].minimal-select { padding: 8px 14px; }

/* Table Elements */
.sleek-table-container { flex: 1; overflow-x: auto; }
.sleek-table { width: 100%; border-collapse: collapse; text-align: left; }
.sleek-table th { padding: 16px 24px; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); background: rgba(0,0,0,0.1); }
.sleek-table td { padding: 18px 24px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }
.table-row { transition: background var(--transition-fast); }
.table-row:hover { background: var(--bg-card-hover); cursor: default; }

.time-cell { display: flex; flex-direction: column; gap: 2px; }
.time-main { font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; font-weight: 600; color: var(--text-primary); }
.time-date { font-size: 0.8rem; color: var(--text-muted); }

.user-cell { display: flex; align-items: center; gap: 14px; }
.avatar { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.user-id { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }

.status-pill.minimal { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid transparent; letter-spacing: 0.5px; }
.status-pill.check-in { background: rgba(16, 185, 129, 0.05); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }
.status-pill.check-out { background: rgba(16, 121, 196, 0.05); color: var(--accent-primary); border-color: rgba(16, 121, 196, 0.2); }
.pill-dot { display: none; }

.gate-txt { font-weight: 500; color: var(--text-secondary); }

.plate { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.85rem; padding: 4px 10px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-primary); }
.walk-txt { color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

.method-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;}
.method-badge.face { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.method-badge.plate { background: rgba(168, 85, 247, 0.1); color: #a855f7; }
.method-badge.card { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.method-badge.manual { background: rgba(245, 158, 11, 0.1); color: var(--accent-warning); }

.desc-cell { font-size: 0.85rem; color: var(--text-secondary); max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: inline-block; }

/* Empty & Pagination */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }
.pagination-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border-color); }
.showing-txt { font-size: 0.9rem; color: var(--text-secondary); }
.pg-controls { display: flex; gap: 6px; }
.pg-btn { background: var(--bg-input); border: 1px solid var(--border-color); color: var(--text-primary); width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: 500; transition: border 0.2s; }
.pg-btn:hover { border-color: var(--text-muted); }
.pg-btn.active { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }

@media (max-width: 1200px) { .bento-grid-mini { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
    .bento-grid-mini { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
}
</style>
