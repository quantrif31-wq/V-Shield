<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Quản lý Phương tiện</h1>
                <p class="page-subtitle">Đăng ký và quản lý phương tiện ra/vào công ty</p>
            </div>
            <button class="btn btn-primary" @click="openModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    style="width: 18px; height: 18px;">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Đăng ký phương tiện
            </button>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card green">
                <div class="stat-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <rect x="1" y="3" width="15" height="13" rx="2" />
                        <path d="M16 8h4l3 3v5h-7V8z" />
                        <circle cx="5.5" cy="18.5" r="2.5" />
                        <circle cx="18.5" cy="18.5" r="2.5" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>156</h3>
                    <p>Tổng phương tiện</p>
                </div>
            </div>
            <div class="stat-card blue">
                <div class="stat-icon blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9 12l2 2 4-4" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>142</h3>
                    <p>Đã đăng ký</p>
                </div>
            </div>
            <div class="stat-card orange">
                <div class="stat-icon orange">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 8v4" />
                        <path d="M12 16h.01" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>14</h3>
                    <p>Chờ duyệt</p>
                </div>
            </div>
            <div class="stat-card cyan">
                <div class="stat-icon cyan">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" />
                        <polyline points="10 17 15 12 10 7" />
                        <line x1="15" y1="12" x2="3" y2="12" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>67</h3>
                    <p>Trong khuôn viên</p>
                </div>
            </div>
        </div>

        <!-- Filters -->
        <div class="card" style="margin-bottom: 20px; padding: 16px 20px;">
            <div class="filter-group">
                <div class="search-bar" style="max-width: 300px;">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 18px; height: 18px;">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm biển số, chủ xe..." />
                </div>
                <select v-model="filterType" class="filter-select">
                    <option value="">Tất cả loại xe</option>
                    <option value="car">Ô tô</option>
                    <option value="motorbike">Xe máy</option>
                    <option value="bicycle">Xe đạp</option>
                    <option value="truck">Xe tải</option>
                </select>
                <select v-model="filterStatus" class="filter-select">
                    <option value="">Tất cả trạng thái</option>
                    <option value="active">Đã đăng ký</option>
                    <option value="pending">Chờ duyệt</option>
                    <option value="inactive">Ngừng</option>
                </select>
            </div>
        </div>

        <!-- Table -->
        <div class="card" style="padding: 0;">
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Biển số</th>
                            <th>Loại xe</th>
                            <th>Màu sắc</th>
                            <th>Chủ sở hữu</th>
                            <th>Trạng thái</th>
                            <th>Lần vào cuối</th>
                            <th style="width: 120px">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="v in filteredVehicles" :key="v.id">
                            <td>
                                <div class="plate-number">
                                    <span class="plate">{{ v.plate }}</span>
                                </div>
                            </td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span class="vehicle-type-icon" v-html="getTypeIcon(v.type)"></span>
                                    {{ getTypeLabel(v.type) }}
                                </div>
                            </td>
                            <td>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span class="color-dot" :style="{ background: v.colorHex }"></span>
                                    {{ v.color }}
                                </div>
                            </td>
                            <td>
                                <div class="avatar-group">
                                    <div class="avatar" style="width: 32px; height: 32px; font-size: 0.75rem;">{{
                                        v.ownerInitials }}</div>
                                    <div class="avatar-info">
                                        <span class="avatar-name">{{ v.owner }}</span>
                                        <span class="avatar-sub">{{ v.ownerCode }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <span class="badge" :class="v.status">
                                    <span class="badge-dot"></span>
                                    {{ getStatusLabel(v.status) }}
                                </span>
                            </td>
                            <td style="color: var(--text-secondary);">{{ v.lastEntry }}</td>
                            <td>
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn-icon" @click="openModal(v)" title="Chỉnh sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <button class="btn-icon" @click="deleteVehicle(v)" title="Xóa"
                                        style="color: var(--accent-danger);">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <polyline points="3 6 5 6 21 6" />
                                            <path
                                                d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="pagination" style="padding: 16px 20px;">
                <span class="pagination-info">Hiển thị 1-{{ filteredVehicles.length }} / {{ vehicles.length }} phương
                    tiện</span>
                <div class="pagination-buttons">
                    <button class="pagination-btn">‹</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">›</button>
                </div>
            </div>
        </div>

        <!-- Modal -->
        <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">{{ editingVehicle ? 'Chỉnh sửa phương tiện' : 'Đăng ký phương tiện mới' }}
                    </h3>
                    <button class="modal-close" @click="showModal = false">✕</button>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Biển số xe *</label>
                        <input v-model="form.plate" type="text" placeholder="VD: 51A-123.45" />
                    </div>
                    <div class="form-group">
                        <label>Loại xe</label>
                        <select v-model="form.type">
                            <option value="car">Ô tô</option>
                            <option value="motorbike">Xe máy</option>
                            <option value="bicycle">Xe đạp</option>
                            <option value="truck">Xe tải</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Màu sắc</label>
                        <input v-model="form.color" type="text" placeholder="VD: Trắng" />
                    </div>
                    <div class="form-group">
                        <label>Hãng xe</label>
                        <input v-model="form.brand" type="text" placeholder="VD: Toyota" />
                    </div>
                </div>

                <div class="form-group">
                    <label>Chủ sở hữu (Nhân viên)</label>
                    <select v-model="form.owner">
                        <option value="">Chọn nhân viên</option>
                        <option value="Nguyễn Văn An">Nguyễn Văn An - NV001</option>
                        <option value="Trần Thị Bình">Trần Thị Bình - NV002</option>
                        <option value="Lê Hoàng Cường">Lê Hoàng Cường - NV003</option>
                        <option value="Phạm Minh Đức">Phạm Minh Đức - NV004</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Ghi chú</label>
                    <textarea v-model="form.note" rows="3" placeholder="Thêm ghi chú..."></textarea>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary" @click="showModal = false">Hủy</button>
                    <button class="btn btn-primary" @click="saveVehicle">
                        {{ editingVehicle ? 'Lưu thay đổi' : 'Đăng ký' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const showModal = ref(false)
const editingVehicle = ref(null)

const form = ref({
    plate: '', type: 'car', color: '', brand: '', owner: '', note: ''
})

const vehicles = ref([
    { id: 1, plate: '51A-123.45', type: 'car', color: 'Trắng', colorHex: '#e2e8f0', brand: 'Toyota Camry', owner: 'Nguyễn Văn An', ownerInitials: 'NA', ownerCode: 'NV001', status: 'active', lastEntry: '08:05 - 05/03' },
    { id: 2, plate: '30H-567.89', type: 'car', color: 'Đen', colorHex: '#374151', brand: 'Honda Civic', owner: 'Lê Hoàng Cường', ownerInitials: 'LC', ownerCode: 'NV003', status: 'active', lastEntry: '08:20 - 05/03' },
    { id: 3, plate: '51B-234.56', type: 'motorbike', color: 'Đỏ', colorHex: '#ef4444', brand: 'Honda SH', owner: 'Phạm Minh Đức', ownerInitials: 'PD', ownerCode: 'NV004', status: 'active', lastEntry: '08:25 - 05/03' },
    { id: 4, plate: '51F-789.01', type: 'car', color: 'Xanh', colorHex: '#3b82f6', brand: 'Hyundai Tucson', owner: 'Hoàng Văn Phong', ownerInitials: 'HP', ownerCode: 'NV006', status: 'active', lastEntry: '08:35 - 05/03' },
    { id: 5, plate: '59C-111.22', type: 'motorbike', color: 'Bạc', colorHex: '#94a3b8', brand: 'Yamaha Exciter', owner: 'Đỗ Thị Giang', ownerInitials: 'DG', ownerCode: 'NV007', status: 'pending', lastEntry: '—' },
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
        car: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
        motorbike: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-4 8h6"/><path d="M9 14l1-3h6"/></svg>',
        bicycle: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><path d="M15 6l-7 11"/><path d="M5.5 17.5L9 8h4l4 9.5"/></svg>',
        truck: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    }
    return icons[type] || icons.car
}

const getTypeLabel = (type) => {
    const labels = { car: 'Ô tô', motorbike: 'Xe máy', bicycle: 'Xe đạp', truck: 'Xe tải' }
    return labels[type] || type
}

const getStatusLabel = (status) => {
    const labels = { active: 'Đã đăng ký', pending: 'Chờ duyệt', inactive: 'Ngừng' }
    return labels[status] || status
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
            ownerCode: '',
            status: 'pending',
            lastEntry: '—',
            colorHex: '#94a3b8'
        })
    }
    showModal.value = false
}

const deleteVehicle = (v) => {
    if (confirm(`Xóa phương tiện ${v.plate}?`)) {
        vehicles.value = vehicles.value.filter(x => x.id !== v.id)
    }
}
</script>

<style scoped>
.plate-number {
    display: inline-flex;
}

.plate {
    font-family: monospace;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 4px 12px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    letter-spacing: 0.5px;
}

.vehicle-type-icon {
    display: flex;
    align-items: center;
    color: var(--text-secondary);
}

.color-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2px solid var(--border-color);
    flex-shrink: 0;
}
</style>
