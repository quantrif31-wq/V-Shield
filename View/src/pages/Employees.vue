<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Quản lý Nhân viên</h1>
                <p class="page-subtitle">Quản lý thông tin nhân viên và quyền ra/vào</p>
            </div>
            <button class="btn btn-primary" @click="openModal()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    style="width: 18px; height: 18px;">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Thêm nhân viên
            </button>
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
                    <input v-model="searchQuery" type="text" placeholder="Tìm nhân viên..." />
                </div>
                <select v-model="filterDepartment" class="filter-select">
                    <option value="">Tất cả phòng ban</option>
                    <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
                </select>
                <select v-model="filterStatus" class="filter-select">
                    <option value="">Tất cả trạng thái</option>
                    <option value="active">Đang hoạt động</option>
                    <option value="inactive">Ngừng hoạt động</option>
                </select>
                <div style="margin-left: auto; color: var(--text-secondary); font-size: 0.85rem;">
                    {{ filteredEmployees.length }} nhân viên
                </div>
            </div>
        </div>

        <!-- Table -->
        <div class="card" style="padding: 0;">
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Nhân viên</th>
                            <th>Mã NV</th>
                            <th>Phòng ban</th>
                            <th>Chức vụ</th>
                            <th>Trạng thái</th>
                            <th>Lần check-in cuối</th>
                            <th style="width: 120px">Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="emp in filteredEmployees" :key="emp.id">
                            <td>
                                <div class="avatar-group">
                                    <div class="avatar" :style="{ background: emp.avatarColor }">{{ emp.initials }}
                                    </div>
                                    <div class="avatar-info">
                                        <span class="avatar-name">{{ emp.name }}</span>
                                        <span class="avatar-sub">{{ emp.email }}</span>
                                    </div>
                                </div>
                            </td>
                            <td><span style="font-family: monospace; font-weight: 500;">{{ emp.code }}</span></td>
                            <td>{{ emp.department }}</td>
                            <td>{{ emp.position }}</td>
                            <td>
                                <span class="badge" :class="emp.status">
                                    <span class="badge-dot"></span>
                                    {{ emp.status === 'active' ? 'Hoạt động' : 'Ngừng' }}
                                </span>
                            </td>
                            <td>
                                <span style="color: var(--text-secondary);">{{ emp.lastCheckIn }}</span>
                            </td>
                            <td>
                                <div style="display: flex; gap: 6px;">
                                    <button class="btn-icon" @click="openModal(emp)" title="Chỉnh sửa">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 16px; height: 16px;">
                                            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                                            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                                        </svg>
                                    </button>
                                    <button class="btn-icon" @click="deleteEmployee(emp)" title="Xóa"
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

            <!-- Pagination -->
            <div class="pagination" style="padding: 16px 20px;">
                <span class="pagination-info">Hiển thị 1-{{ filteredEmployees.length }} / {{ employees.length }} nhân
                    viên</span>
                <div class="pagination-buttons">
                    <button class="pagination-btn">‹</button>
                    <button class="pagination-btn active">1</button>
                    <button class="pagination-btn">2</button>
                    <button class="pagination-btn">3</button>
                    <button class="pagination-btn">›</button>
                </div>
            </div>
        </div>

        <!-- Modal -->
        <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">{{ editingEmployee ? 'Chỉnh sửa nhân viên' : 'Thêm nhân viên mới' }}</h3>
                    <button class="modal-close" @click="showModal = false">✕</button>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Họ và tên *</label>
                        <input v-model="form.name" type="text" placeholder="Nhập họ tên" />
                    </div>
                    <div class="form-group">
                        <label>Mã nhân viên *</label>
                        <input v-model="form.code" type="text" placeholder="VD: NV001" />
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Email</label>
                        <input v-model="form.email" type="email" placeholder="email@company.com" />
                    </div>
                    <div class="form-group">
                        <label>Số điện thoại</label>
                        <input v-model="form.phone" type="text" placeholder="0912 345 678" />
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Phòng ban</label>
                        <select v-model="form.department">
                            <option value="">Chọn phòng ban</option>
                            <option v-for="dept in departments" :key="dept" :value="dept">{{ dept }}</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Chức vụ</label>
                        <input v-model="form.position" type="text" placeholder="Nhập chức vụ" />
                    </div>
                </div>

                <div class="form-group">
                    <label>Trạng thái</label>
                    <select v-model="form.status">
                        <option value="active">Đang hoạt động</option>
                        <option value="inactive">Ngừng hoạt động</option>
                    </select>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary" @click="showModal = false">Hủy</button>
                    <button class="btn btn-primary" @click="saveEmployee">
                        {{ editingEmployee ? 'Lưu thay đổi' : 'Thêm nhân viên' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const searchQuery = ref('')
const filterDepartment = ref('')
const filterStatus = ref('')
const showModal = ref(false)
const editingEmployee = ref(null)

const departments = ['Kỹ thuật', 'Kinh doanh', 'Nhân sự', 'Tài chính', 'Marketing', 'IT', 'Hành chính']

const form = ref({
    name: '',
    code: '',
    email: '',
    phone: '',
    department: '',
    position: '',
    status: 'active',
})

const employees = ref([
    { id: 1, name: 'Nguyễn Văn An', initials: 'NA', code: 'NV001', email: 'an.nv@company.com', department: 'Kỹ thuật', position: 'Kỹ sư', status: 'active', lastCheckIn: '08:05 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' },
    { id: 2, name: 'Trần Thị Bình', initials: 'TB', code: 'NV002', email: 'binh.tt@company.com', department: 'Nhân sự', position: 'Trưởng phòng', status: 'active', lastCheckIn: '08:12 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #ec4899, #f43f5e)' },
    { id: 3, name: 'Lê Hoàng Cường', initials: 'LC', code: 'NV003', email: 'cuong.lh@company.com', department: 'Kinh doanh', position: 'Nhân viên', status: 'active', lastCheckIn: '08:20 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #10b981, #06b6d4)' },
    { id: 4, name: 'Phạm Minh Đức', initials: 'PD', code: 'NV004', email: 'duc.pm@company.com', department: 'IT', position: 'Lập trình viên', status: 'active', lastCheckIn: '08:25 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #f59e0b, #ef4444)' },
    { id: 5, name: 'Võ Thị Em', initials: 'VE', code: 'NV005', email: 'em.vt@company.com', department: 'Tài chính', position: 'Kế toán', status: 'inactive', lastCheckIn: '17:30 - 01/03/2026', avatarColor: 'linear-gradient(135deg, #8b5cf6, #3b82f6)' },
    { id: 6, name: 'Hoàng Văn Phong', initials: 'HP', code: 'NV006', email: 'phong.hv@company.com', department: 'Marketing', position: 'Chuyên viên', status: 'active', lastCheckIn: '08:35 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #06b6d4, #3b82f6)' },
    { id: 7, name: 'Đỗ Thị Giang', initials: 'DG', code: 'NV007', email: 'giang.dt@company.com', department: 'Hành chính', position: 'Nhân viên', status: 'active', lastCheckIn: '07:55 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #f43f5e, #f59e0b)' },
    { id: 8, name: 'Bùi Quốc Huy', initials: 'BH', code: 'NV008', email: 'huy.bq@company.com', department: 'Kỹ thuật', position: 'Trưởng nhóm', status: 'active', lastCheckIn: '08:10 - 05/03/2026', avatarColor: 'linear-gradient(135deg, #10b981, #8b5cf6)' },
])

const filteredEmployees = computed(() => {
    return employees.value.filter(emp => {
        const matchSearch = !searchQuery.value || emp.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || emp.code.toLowerCase().includes(searchQuery.value.toLowerCase())
        const matchDept = !filterDepartment.value || emp.department === filterDepartment.value
        const matchStatus = !filterStatus.value || emp.status === filterStatus.value
        return matchSearch && matchDept && matchStatus
    })
})

const openModal = (emp = null) => {
    editingEmployee.value = emp
    if (emp) {
        form.value = { ...emp }
    } else {
        form.value = { name: '', code: '', email: '', phone: '', department: '', position: '', status: 'active' }
    }
    showModal.value = true
}

const saveEmployee = () => {
    if (editingEmployee.value) {
        const idx = employees.value.findIndex(e => e.id === editingEmployee.value.id)
        if (idx !== -1) {
            employees.value[idx] = { ...employees.value[idx], ...form.value }
        }
    } else {
        employees.value.push({
            ...form.value,
            id: Date.now(),
            initials: form.value.name.split(' ').map(w => w[0]).join('').slice(-2).toUpperCase(),
            lastCheckIn: '—',
            avatarColor: 'linear-gradient(135deg, #3b82f6, #8b5cf6)'
        })
    }
    showModal.value = false
}

const deleteEmployee = (emp) => {
    if (confirm(`Bạn có chắc muốn xóa nhân viên ${emp.name}?`)) {
        employees.value = employees.value.filter(e => e.id !== emp.id)
    }
}
</script>
