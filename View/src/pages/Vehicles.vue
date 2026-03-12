<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Quản lý Phương tiện</h1>
                <p class="page-subtitle">Đăng ký và quản lý phương tiện ra/vào công ty</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openModal()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Đăng ký phương tiện
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini" style="grid-template-columns: repeat(4, 1fr);">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="15" height="13" rx="2" /><path d="M16 8h4l3 3v5h-7V8z" /><circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val">156</div>
                    <div class="stat-lbl">Tổng PT</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M9 12l2 2 4-4" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val blue">142</div>
                    <div class="stat-lbl">Đã đăng ký</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper orange" style="background: rgba(249, 115, 22, 0.1); color: var(--accent-warning);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: var(--accent-warning);">14</div>
                    <div class="stat-lbl">Chờ duyệt</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper cyan" style="background: rgba(6, 182, 212, 0.1); color: #06b6d4;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" /><polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: #06b6d4;">67</div>
                    <div class="stat-lbl">Trong khuôn viên</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm biển số, chủ xe..." />
                </div>
                <div class="filter-box" style="display: flex; gap: 12px;">
                    <select v-model="filterType" class="minimal-select">
                        <option value="">Tất cả loại xe</option>
                        <option value="car">Ô tô</option>
                        <option value="motorbike">Xe máy</option>
                        <option value="bicycle">Xe đạp</option>
                        <option value="truck">Xe tải</option>
                    </select>
                    <select v-model="filterStatus" class="minimal-select">
                        <option value="">Tất cả trạng thái</option>
                        <option value="active">Đã đăng ký</option>
                        <option value="pending">Chờ duyệt</option>
                        <option value="inactive">Ngừng hoạt động</option>
                    </select>
                </div>
            </div>
            
            <!-- Sleek Table -->
            <div class="sleek-table-container">
                <table class="sleek-table">
                    <thead>
                        <tr>
                            <th>Biển số</th>
                            <th>Thông tin xe</th>
                            <th>Chủ sở hữu</th>
                            <th>Trạng thái & Lịch sử</th>
                            <th class="text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="v in filteredVehicles" :key="v.id" class="table-row">
                            <td>
                                <div class="plate-number"><span class="plate">{{ v.plate }}</span></div>
                            </td>
                            <td>
                                <div class="vehicle-info-cell">
                                    <div class="v-type">
                                        <span class="v-icon" v-html="getTypeIcon(v.type)"></span>
                                        {{ getTypeLabel(v.type) }}
                                    </div>
                                    <div class="v-color" v-if="v.colorHex">
                                        <span class="color-dot" :style="{ background: v.colorHex }"></span>
                                        {{ v.color }} &middot; {{ v.brand || 'Khác' }}
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="user-cell">
                                    <div class="avatar" :style="{ background: getAvatarColor(v.ownerInitials) }">{{ v.ownerInitials }}</div>
                                    <div class="user-info">
                                        <span class="user-name">{{ v.owner }}</span>
                                        <span class="user-id">{{ v.ownerCode }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="status-cell">
                                    <span class="status-pill" :class="v.status">
                                        <span class="pill-dot"></span>
                                        {{ getStatusLabel(v.status) }}
                                    </span>
                                    <span class="history-txt">Lần cuối: {{ v.lastEntry }}</span>
                                </div>
                            </td>
                            <td class="text-right">
                                <div class="action-menu">
                                    <button class="icon-btn" @click="openModal(v)" title="Sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
                                    </button>
                                    <button class="icon-btn danger" @click="deleteVehicle(v)" title="Xóa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" /><line x1="10" y1="11" x2="10" y2="17" /><line x1="14" y1="11" x2="14" y2="17" /></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        <tr v-if="filteredVehicles.length === 0">
                            <td colspan="5" class="empty-layout">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--text-muted);"><rect x="1" y="3" width="15" height="13" rx="2" /><path d="M16 8h4l3 3v5h-7V8z" /><circle cx="5.5" cy="18.5" r="2.5" /><circle cx="18.5" cy="18.5" r="2.5" /></svg>
                                <p>Không tìm thấy phương tiện nào</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="pagination-footer">
                <span class="showing-txt">Hiển thị {{ filteredVehicles.length }} / {{ vehicles.length }}</span>
                <div class="pg-controls">
                    <button class="pg-btn">‹</button>
                    <button class="pg-btn active">1</button>
                    <button class="pg-btn">2</button>
                    <button class="pg-btn">›</button>
                </div>
            </div>
        </div>

        <!-- Modern Modal Override -->
        <transition name="modal">
            <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
                <div class="modern-modal">
                    <div class="modal-top">
                        <h3>{{ editingVehicle ? 'Cập nhật Phương tiện' : 'Đăng ký Phương tiện' }}</h3>
                        <button class="icon-close" @click="showModal = false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>
                    
                    <div class="modal-body">
                        <div class="grid-2">
                            <div class="input-pane">
                                <label>Biển số xe <span class="req">*</span></label>
                                <input v-model="form.plate" type="text" class="sleek-input" placeholder="VD: 51A-123.45" />
                            </div>
                            <div class="input-pane">
                                <label>Loại xe</label>
                                <select v-model="form.type" class="sleek-select">
                                    <option value="car">Ô tô</option>
                                    <option value="motorbike">Xe máy</option>
                                    <option value="bicycle">Xe đạp</option>
                                    <option value="truck">Xe tải</option>
                                </select>
                            </div>
                        </div>

                        <div class="grid-2">
                            <div class="input-pane">
                                <label>Màu sắc</label>
                                <input v-model="form.color" type="text" class="sleek-input" placeholder="VD: Trắng" />
                            </div>
                            <div class="input-pane">
                                <label>Hãng xe</label>
                                <input v-model="form.brand" type="text" class="sleek-input" placeholder="VD: Toyota" />
                            </div>
                        </div>

                        <div class="input-pane">
                            <label>Chủ sở hữu (Nhân sự)</label>
                            <select v-model="form.owner" class="sleek-select">
                                <option value="">-- Chọn nhân sự quản lý --</option>
                                <option value="Nguyễn Văn An">Nguyễn Văn An - NV001</option>
                                <option value="Trần Thị Bình">Trần Thị Bình - NV002</option>
                                <option value="Lê Hoàng Cường">Lê Hoàng Cường - NV003</option>
                                <option value="Phạm Minh Đức">Phạm Minh Đức - NV004</option>
                            </select>
                        </div>

                        <div class="input-pane">
                            <label>Ghi chú thêm</label>
                            <textarea v-model="form.note" rows="3" class="sleek-input" placeholder="Thông tin thêm..."></textarea>
                        </div>

                        <div class="modal-actions mt-4">
                            <button class="btn btn-secondary" @click="showModal = false">Hủy</button>
                            <button class="btn btn-primary" @click="saveVehicle">
                                {{ editingVehicle ? 'Lưu Thông Tin' : 'Đăng Ký' }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <!-- Custom confirm Dialog -->
         <transition name="modal">
            <div v-if="deleteConfirm" class="modal-backdrop" @click.self="deleteConfirm = null">
                <div class="modern-modal mini">
                    <div class="modal-body text-center" style="padding: 32px 24px;">
                        <div class="warning-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
                        <h3 style="margin: 0 0 10px 0;">Xóa phương tiện này?</h3>
                        <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 24px;">
                            Biển số <strong style="color: var(--text-primary);">{{ deleteConfirm.plate }}</strong> sẽ bị gỡ khỏi hệ thống. Hành động này không thể hoàn tác.
                        </p>
                        <div class="modal-actions centered">
                            <button class="btn btn-secondary" @click="deleteConfirm = null">Hủy</button>
                            <button class="btn btn-danger" @click="executeDelete">Xóa</button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const showModal = ref(false)
const editingVehicle = ref(null)
const deleteConfirm = ref(null)

const form = ref({ plate: '', type: 'car', color: '', brand: '', owner: '', note: '' })

const vehicles = ref([
    { id: 1, plate: '51A-123.45', type: 'car', color: 'Trắng', colorHex: '#e2e8f0', brand: 'Toyota Camry', owner: 'Nguyễn Văn An', ownerInitials: 'NA', ownerCode: 'NV001', status: 'active', lastEntry: '08:05 - 05/03' },
    { id: 2, plate: '30H-567.89', type: 'car', color: 'Đen', colorHex: '#475569', brand: 'Honda Civic', owner: 'Lê Hoàng Cường', ownerInitials: 'LC', ownerCode: 'NV003', status: 'active', lastEntry: '08:20 - 05/03' },
    { id: 3, plate: '51B-234.56', type: 'motorbike', color: 'Đỏ', colorHex: '#ef4444', brand: 'Honda SH', owner: 'Phạm Minh Đức', ownerInitials: 'PD', ownerCode: 'NV004', status: 'active', lastEntry: '08:25 - 05/03' },
    { id: 4, plate: '51F-789.01', type: 'car', color: 'Xanh', colorHex: '#3b82f6', brand: 'Hyundai Tucson', owner: 'Hoàng Văn Phong', ownerInitials: 'HP', ownerCode: 'NV006', status: 'active', lastEntry: '08:35 - 05/03' },
    { id: 5, plate: '59C-111.22', type: 'motorbike', color: 'Bạc', colorHex: '#94a3b8', brand: 'Yamaha Exciter', owner: 'Đỗ Thị Giang', ownerInitials: 'ĐG', ownerCode: 'NV007', status: 'pending', lastEntry: '—' },
    { id: 6, plate: '51G-333.44', type: 'car', color: 'Xám', colorHex: '#6b7280', brand: 'Ford Ranger', owner: 'Bùi Quốc Huy', ownerInitials: 'BH', ownerCode: 'NV008', status: 'active', lastEntry: '08:10 - 05/03' },
    { id: 7, plate: '30K-555.66', type: 'truck', color: 'Trắng', colorHex: '#e2e8f0', brand: 'Isuzu', owner: 'Nguyễn Văn An', ownerInitials: 'NA', ownerCode: 'NV001', status: 'inactive', lastEntry: '10:00 - 28/02' },
])

const filteredVehicles = computed(() => {
    return vehicles.value.filter(v => {
        const matchSearch = !searchQuery.value || v.plate.toLowerCase().includes(searchQuery.value.toLowerCase()) || v.owner.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchType = !filterType.value || v.type === filterType.value
        const matchStatus = !filterStatus.value || v.status === filterStatus.value
        return matchSearch && matchType && matchStatus
    })
})

const getTypeIcon = (type) => {
    const icons = {
        car: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
        motorbike: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-4 8h6"/><path d="M9 14l1-3h6"/></svg>',
        bicycle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-7 11"/><path d="M5.5 17.5L9 8h4l4 9.5"/></svg>',
        truck: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px;height:16px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    }
    return icons[type] || icons.car
}

const getTypeLabel = (type) => {
    const labels = { car: 'Ô tô', motorbike: 'Xe máy', bicycle: 'Xe đạp', truck: 'Xe tải' }
    return labels[type] || type
}

const getStatusLabel = (status) => {
    const labels = { active: 'Đã duyệt', pending: 'Chờ xử lý', inactive: 'Bị khóa' }
    return labels[status] || status
}

const getAvatarColor = (str) => {
    let hash = 0; for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const avColors = [ '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e' ];
    return avColors[Math.abs(hash) % avColors.length];
}

const openModal = (v = null) => {
    editingVehicle.value = v
    form.value = v ? { ...v } : { plate: '', type: 'car', color: '', brand: '', owner: '', note: '' }
    showModal.value = true
}

const saveVehicle = () => {
    if (editingVehicle.value) {
        const idx = vehicles.value.findIndex(x => x.id === editingVehicle.value.id)
        if (idx !== -1) vehicles.value[idx] = { ...vehicles.value[idx], ...form.value }
    } else {
        vehicles.value.push({
            ...form.value,
            id: Date.now(),
            ownerInitials: form.value.owner ? form.value.owner.split(' ').map(w => w[0]).join('').slice(-2).toUpperCase() : '??',
            ownerCode: 'NV00X',
            status: 'pending',
            lastEntry: '—',
            colorHex: '#94a3b8'
        })
    }
    showModal.value = false
}

const deleteVehicle = (v) => { deleteConfirm.value = v }
const executeDelete = () => {
    vehicles.value = vehicles.value.filter(x => x.id !== deleteConfirm.value.id)
    deleteConfirm.value = null
}
</script>

<style scoped>
/* Common Page Layout - Mirrors Employees.vue */
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
.stat-lbl { font-size: 0.9rem; color: var(--text-muted); font-weight: 500;}

/* Table Box */
.table-section { padding: 0; overflow: hidden; display: flex; flex-direction: column; min-height: 500px; }
.table-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border-color); }
.search-box { position: relative; width: 320px; display: flex; align-items: center; }
.search-icon { position: absolute; left: 14px; color: var(--text-muted); width: 18px; }
.search-box input { width: 100%; padding: 10px 14px 10px 42px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; }
.search-box input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 2px rgba(16, 121, 196, 0.2); }
.minimal-select { padding: 10px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); cursor: pointer; outline: none; }

/* Table Elements */
.sleek-table-container { flex: 1; overflow-x: auto; }
.sleek-table { width: 100%; border-collapse: collapse; text-align: left; }
.sleek-table th { padding: 16px 24px; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-color); background: rgba(0,0,0,0.1); }
.sleek-table td { padding: 18px 24px; border-bottom: 1px solid var(--border-color); vertical-align: middle; }
.table-row { transition: background var(--transition-fast); }
.table-row:hover { background: var(--bg-card-hover); cursor: default; }

.plate-number { display: inline-flex; }
.plate { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.95rem; padding: 6px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; letter-spacing: 0.5px; color: var(--text-primary); box-shadow: inset 0 2px 4px rgba(0,0,0,0.2); }

.vehicle-info-cell { display: flex; flex-direction: column; gap: 4px; }
.v-type { display: flex; align-items: center; gap: 8px; font-weight: 500; font-size: 0.95rem; color: var(--text-primary); }
.v-icon { color: var(--text-muted); display: flex; }
.v-color { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; color: var(--text-secondary); }
.color-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; box-shadow: 0 1px 3px rgba(0,0,0,0.3); flex-shrink: 0; }

.user-cell { display: flex; align-items: center; gap: 14px; }
.avatar { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.user-id { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }

.status-cell { display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
.history-txt { font-size: 0.8rem; color: var(--text-secondary); }
.status-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;}
.status-pill.active { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.status-pill.pending { background: rgba(249, 115, 22, 0.1); color: var(--accent-warning); }
.status-pill.inactive { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.action-menu { display: flex; gap: 8px; justify-content: flex-end; }
.icon-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.icon-btn svg { width: 18px; }
.icon-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.icon-btn.danger:hover { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

/* Spinners & Empties */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }

/* Pagination Area */
.pagination-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border-color); }
.showing-txt { font-size: 0.9rem; color: var(--text-secondary); }
.pg-controls { display: flex; gap: 6px; }
.pg-btn { background: var(--bg-input); border: 1px solid var(--border-color); color: var(--text-primary); width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: 500; transition: border 0.2s; }
.pg-btn:hover { border-color: var(--text-muted); }
.pg-btn.active { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }

/* Modern Modals */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 20px;}
.modern-modal { background: var(--bg-card); width: 100%; max-width: 540px; border-radius: var(--border-radius-lg); border: 1px solid var(--border-color); box-shadow: var(--shadow-xl); overflow: hidden; display: flex; flex-direction: column;}
.modern-modal.mini { max-width: 400px; }
.modal-top { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border-color); }
.modal-top h3 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;}
.icon-close { background: none; border: none; color: var(--text-muted); cursor: pointer; width: 24px; transition: color 0.2s; }
.icon-close:hover { color: var(--accent-danger); }

.modal-body { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }
.req { color: var(--accent-danger); }

.sleek-input, .sleek-select { width: 100%; padding: 12px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.95rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px; }
.modal-actions.centered { justify-content: center; }

.warning-icon svg { width: 48px; height: 48px; color: var(--accent-danger); margin-bottom: 16px; }
.mt-4 { margin-top: 24px; }
.text-right { text-align: right; }
.text-center { text-align: center; }

.modal-enter-active, .modal-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }

@media (max-width: 1200px) { .bento-grid-mini { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
    .bento-grid-mini { grid-template-columns: 1fr; }
    .grid-2 { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
}
</style>
