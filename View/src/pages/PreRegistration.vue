<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Đăng ký trước</h1>
                <p class="page-subtitle">Quản lý đơn đăng ký khách thăm quan trước khi đến</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="showCreateLinkModal = true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 16px; height: 16px;">
                        <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                        <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
                    </svg>
                    Tạo link đăng ký
                </button>
            </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-icon blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
                        <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ stats.total }}</h3>
                    <p>Tổng đơn</p>
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
                    <h3>{{ stats.pending }}</h3>
                    <p>Chờ duyệt</p>
                </div>
            </div>
            <div class="stat-card green">
                <div class="stat-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M9 12l2 2 4-4" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ stats.approved }}</h3>
                    <p>Đã duyệt</p>
                </div>
            </div>
            <div class="stat-card red">
                <div class="stat-icon red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                        style="width: 24px; height: 24px;">
                        <circle cx="12" cy="12" r="10" />
                        <path d="M15 9l-6 6" />
                        <path d="M9 9l6 6" />
                    </svg>
                </div>
                <div class="stat-info">
                    <h3>{{ stats.rejected }}</h3>
                    <p>Từ chối</p>
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
                    <input v-model="searchQuery" type="text" placeholder="Tìm tên khách, SĐT..." />
                </div>
                <select v-model="filterStatus" class="filter-select">
                    <option value="">Tất cả trạng thái</option>
                    <option value="Pending">Chờ duyệt</option>
                    <option value="Approved">Đã duyệt</option>
                    <option value="Rejected">Từ chối</option>
                </select>
                <input v-model="filterDate" type="date" class="filter-select" style="padding-right: 12px;" />
            </div>
        </div>

        <!-- Table -->
        <div class="card" style="padding: 0;">
            <!-- Loading -->
            <div v-if="isLoading" class="loading-state">
                <div class="spinner"></div>
                <p>Đang tải dữ liệu...</p>
            </div>

            <div v-else-if="registrations.length === 0" class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                    style="width: 48px; height: 48px; color: var(--text-muted); margin-bottom: 12px;">
                    <path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" />
                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
                    <path d="M9 14l2 2 4-4" />
                </svg>
                <p>Chưa có đơn đăng ký nào</p>
                <p class="empty-sub">Tạo link đăng ký và gửi cho khách để bắt đầu</p>
            </div>

            <template v-else>
                <div class="table-container">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Khách</th>
                                <th>Nhân viên chủ trì</th>
                                <th>Biển số xe</th>
                                <th>Thời gian dự kiến</th>
                                <th>Số khách</th>
                                <th>Trạng thái</th>
                                <th style="width: 150px">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="reg in registrations" :key="reg.registrationId">
                                <td style="color: var(--text-muted);">{{ reg.registrationId }}</td>
                                <td>
                                    <div class="avatar-group">
                                        <div class="avatar" style="width: 32px; height: 32px; font-size: 0.75rem;">
                                            {{ getInitials(reg.guestFullName) }}
                                        </div>
                                        <div class="avatar-info">
                                            <span class="avatar-name">{{ reg.guestFullName }}</span>
                                            <span class="avatar-sub">{{ reg.guestPhone || '—' }}</span>
                                        </div>
                                    </div>
                                </td>
                                <td>{{ reg.hostEmployeeName }}</td>
                                <td>
                                    <span v-if="reg.expectedLicensePlate" class="plate">{{ reg.expectedLicensePlate
                                        }}</span>
                                    <span v-else style="color: var(--text-muted);">—</span>
                                </td>
                                <td>
                                    <div class="time-range">
                                        <span>{{ formatDateTime(reg.expectedTimeIn) }}</span>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                            style="width: 14px; height: 14px; color: var(--text-muted); flex-shrink: 0;">
                                            <path d="M5 12h14" />
                                            <path d="M12 5l7 7-7 7" />
                                        </svg>
                                        <span>{{ formatDateTime(reg.expectedTimeOut) }}</span>
                                    </div>
                                </td>
                                <td style="text-align: center;">{{ reg.numberOfVisitors }}</td>
                                <td>
                                    <span class="badge" :class="getStatusClass(reg.status)">
                                        <span class="badge-dot"></span>
                                        {{ getStatusLabel(reg.status) }}
                                    </span>
                                </td>
                                <td>
                                    <div style="display: flex; gap: 6px;">
                                        <button class="btn-icon" @click="viewDetail(reg.registrationId)"
                                            title="Xem chi tiết">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width: 16px; height: 16px;">
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                <circle cx="12" cy="12" r="3" />
                                            </svg>
                                        </button>
                                        <button v-if="reg.status === 'Pending'" class="btn-icon btn-approve"
                                            @click="handleUpdateStatus(reg.registrationId, 'Approved')" title="Duyệt">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width: 16px; height: 16px;">
                                                <path d="M20 6L9 17l-5-5" />
                                            </svg>
                                        </button>
                                        <button v-if="reg.status === 'Pending'" class="btn-icon btn-reject"
                                            @click="handleUpdateStatus(reg.registrationId, 'Rejected')" title="Từ chối">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                                                style="width: 16px; height: 16px;">
                                                <path d="M18 6L6 18" />
                                                <path d="M6 6l12 12" />
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
                    <span class="pagination-info">Hiển thị {{ registrations.length }} / {{ totalItems }} đơn</span>
                    <div class="pagination-buttons">
                        <button class="pagination-btn" :disabled="currentPage <= 1"
                            @click="currentPage--; fetchRegistrations()">‹</button>
                        <button v-for="p in totalPages" :key="p" class="pagination-btn" :class="{ active: p === currentPage }"
                            @click="currentPage = p; fetchRegistrations()">{{ p }}</button>
                        <button class="pagination-btn" :disabled="currentPage >= totalPages"
                            @click="currentPage++; fetchRegistrations()">›</button>
                    </div>
                </div>
            </template>
        </div>

        <!-- Detail Modal -->
        <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
            <div class="modal" style="max-width: 700px;">
                <div class="modal-header">
                    <h3 class="modal-title">Chi tiết đơn đăng ký #{{ detail?.registrationId }}</h3>
                    <button class="modal-close" @click="showDetailModal = false">✕</button>
                </div>

                <div v-if="isLoadingDetail" class="loading-state" style="padding: 40px 0;">
                    <div class="spinner"></div>
                    <p>Đang tải...</p>
                </div>

                <template v-else-if="detail">
                    <!-- Guest info -->
                    <div class="detail-section">
                        <h4 class="section-title">Thông tin khách</h4>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <span class="detail-label">Họ tên</span>
                                <span class="detail-value">{{ detail.guestFullName }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">SĐT</span>
                                <span class="detail-value">{{ detail.guestPhone || '—' }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Biển số xe</span>
                                <span class="detail-value">{{ detail.expectedLicensePlate || '—' }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Nhân viên chủ trì</span>
                                <span class="detail-value">{{ detail.hostEmployeeName }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Thời gian vào</span>
                                <span class="detail-value">{{ formatDateTime(detail.expectedTimeIn) }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Thời gian ra</span>
                                <span class="detail-value">{{ formatDateTime(detail.expectedTimeOut) }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Trạng thái</span>
                                <span class="badge" :class="getStatusClass(detail.status)">
                                    <span class="badge-dot"></span>
                                    {{ getStatusLabel(detail.status) }}
                                </span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Ngày tạo</span>
                                <span class="detail-value">{{ formatDateTime(detail.createdAt) }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Visitors -->
                    <div v-if="detail.visitors && detail.visitors.length > 0" class="detail-section">
                        <h4 class="section-title">Danh sách khách trong đoàn ({{ detail.visitors.length }})</h4>
                        <div class="visitors-list">
                            <div v-for="(v, i) in detail.visitors" :key="i" class="visitor-item">
                                <div class="avatar" style="width: 32px; height: 32px; font-size: 0.7rem;">
                                    {{ getInitials(v.fullName) }}
                                </div>
                                <div class="visitor-info">
                                    <span class="visitor-name">{{ v.fullName }}</span>
                                    <span class="visitor-id">{{ v.idCardNumber || 'Chưa có CCCD' }}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Access Logs -->
                    <div v-if="detail.accessLogs && detail.accessLogs.length > 0" class="detail-section">
                        <h4 class="section-title">Lịch sử ra / vào</h4>
                        <div class="access-log-list">
                            <div v-for="log in detail.accessLogs" :key="log.logId" class="log-item">
                                <span class="badge" :class="log.direction === 'IN' ? 'check-in' : 'check-out'"
                                    style="min-width: 50px; justify-content: center;">
                                    {{ log.direction === 'IN' ? 'VÀO' : 'RA' }}
                                </span>
                                <span class="log-time">{{ formatDateTime(log.timestamp) }}</span>
                                <span v-if="log.capturedLicensePlate" class="plate" style="font-size: 0.8rem;">{{
                                    log.capturedLicensePlate }}</span>
                                <span v-if="log.note" class="log-note">{{ log.note }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Actions -->
                    <div v-if="detail.status === 'Pending'" class="modal-footer">
                        <button class="btn btn-danger"
                            @click="handleUpdateStatus(detail.registrationId, 'Rejected'); showDetailModal = false">
                            Từ chối
                        </button>
                        <button class="btn btn-primary"
                            @click="handleUpdateStatus(detail.registrationId, 'Approved'); showDetailModal = false"
                            style="background: var(--accent-success); box-shadow: 0 2px 10px rgba(16,185,129,0.3);">
                            Duyệt đơn
                        </button>
                    </div>
                </template>
            </div>
        </div>

        <!-- Create Link Modal -->
        <div v-if="showCreateLinkModal" class="modal-overlay" @click.self="showCreateLinkModal = false">
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title">Tạo link đăng ký</h3>
                    <button class="modal-close" @click="closeCreateLinkModal">✕</button>
                </div>

                <!-- Before creating -->
                <template v-if="!createdLink">
                    <div class="form-group">
                        <label>Nhân viên chủ trì *</label>
                        <select v-model="linkForm.hostEmployeeId">
                            <option :value="null" disabled>Chọn nhân viên</option>
                            <option v-for="emp in employees" :key="emp.employeeId" :value="emp.employeeId">
                                {{ emp.fullName }}
                            </option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Thời hạn link (giờ)</label>
                        <input v-model.number="linkForm.expiryHours" type="number" min="1" max="168"
                            placeholder="VD: 24" />
                        <span class="form-hint">Tối đa 168 giờ (7 ngày)</span>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeCreateLinkModal">Hủy</button>
                        <button class="btn btn-primary" @click="handleCreateLink"
                            :disabled="!linkForm.hostEmployeeId || isCreatingLink">
                            {{ isCreatingLink ? 'Đang tạo...' : 'Tạo link' }}
                        </button>
                    </div>
                </template>

                <!-- After creating -->
                <template v-else>
                    <div class="link-success">
                        <div class="success-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M9 12l2 2 4-4" />
                            </svg>
                        </div>
                        <h4>Link đã được tạo thành công!</h4>
                        <p class="link-expiry">Hết hạn: {{ formatDateTime(createdLink.expiredAt) }}</p>

                        <div class="link-box">
                            <a :href="createdLink.registrationUrl" target="_blank" rel="noopener noreferrer" class="link-url">{{ createdLink.registrationUrl }}</a>
                            <div class="link-actions">
                                <button class="btn btn-primary btn-sm copy-btn" @click="copyLink">
                                    {{ copied ? '✓ Đã copy' : 'Copy' }}
                                </button>
                                <a :href="createdLink.registrationUrl" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm open-btn">
                                    Mở link ↗
                                </a>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary close-btn" @click="closeCreateLinkModal">Đóng</button>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { getAll, getDetail, updateStatus, createLink } from '../services/preRegistrationApi'
import { getAll as getAllEmployees } from '../services/employeeApi'

// ── State ────────────────────────────────────────
const registrations = ref([])
const totalItems = ref(0)
const currentPage = ref(1)
const pageSize = 20
const isLoading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const filterDate = ref('')

const stats = reactive({ total: 0, pending: 0, approved: 0, rejected: 0 })

// Detail modal
const showDetailModal = ref(false)
const detail = ref(null)
const isLoadingDetail = ref(false)

// Create link modal
const showCreateLinkModal = ref(false)
const linkForm = reactive({ hostEmployeeId: null, expiryHours: 24 })
const createdLink = ref(null)
const isCreatingLink = ref(false)
const copied = ref(false)
const linkInput = ref(null)
const employees = ref([])

const totalPages = ref(1)

// ── Helpers ──────────────────────────────────────
const getInitials = (name) => {
    if (!name) return '??'
    return name.split(' ').map(w => w[0]).join('').slice(-2).toUpperCase()
}

const formatDateTime = (dt) => {
    if (!dt) return '—'
    const d = new Date(dt)
    const pad = (n) => String(n).padStart(2, '0')
    return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`
}

const getStatusLabel = (s) => {
    const map = { Pending: 'Chờ duyệt', Approved: 'Đã duyệt', Rejected: 'Từ chối' }
    return map[s] || s
}

const getStatusClass = (s) => {
    const map = { Pending: 'pending', Approved: 'active', Rejected: 'inactive' }
    return map[s] || ''
}

// ── Fetch data ───────────────────────────────────
const fetchRegistrations = async () => {
    isLoading.value = true
    try {
        const params = { page: currentPage.value, pageSize }
        if (filterStatus.value) params.status = filterStatus.value
        if (filterDate.value) params.date = filterDate.value

        const res = await getAll(params)
        const data = res.data
        registrations.value = data.items || []
        totalItems.value = data.total || 0
        totalPages.value = Math.max(1, Math.ceil(totalItems.value / pageSize))

        // Filter by search query locally (API doesn't have search param)
        if (searchQuery.value.trim()) {
            const q = searchQuery.value.toLowerCase()
            registrations.value = registrations.value.filter(r =>
                (r.guestFullName && r.guestFullName.toLowerCase().includes(q)) ||
                (r.guestPhone && r.guestPhone.includes(q))
            )
        }
    } catch (err) {
        console.error('Lỗi khi tải danh sách đăng ký:', err)
    } finally {
        isLoading.value = false
    }
}

const fetchStats = async () => {
    try {
        const [all, pending, approved, rejected] = await Promise.all([
            getAll({ pageSize: 1 }),
            getAll({ status: 'Pending', pageSize: 1 }),
            getAll({ status: 'Approved', pageSize: 1 }),
            getAll({ status: 'Rejected', pageSize: 1 }),
        ])
        stats.total = all.data.total || 0
        stats.pending = pending.data.total || 0
        stats.approved = approved.data.total || 0
        stats.rejected = rejected.data.total || 0
    } catch (err) {
        console.error('Lỗi khi tải thống kê:', err)
    }
}

const fetchEmployees = async () => {
    try {
        const res = await getAllEmployees()
        employees.value = res.data || []
    } catch (err) {
        console.error('Lỗi khi tải nhân viên:', err)
    }
}

// ── Actions ──────────────────────────────────────
const viewDetail = async (id) => {
    showDetailModal.value = true
    isLoadingDetail.value = true
    detail.value = null
    try {
        const res = await getDetail(id)
        detail.value = res.data
    } catch (err) {
        console.error('Lỗi khi tải chi tiết:', err)
    } finally {
        isLoadingDetail.value = false
    }
}

const handleUpdateStatus = async (id, status) => {
    try {
        await updateStatus(id, status)
        await fetchRegistrations()
        await fetchStats()
    } catch (err) {
        console.error('Lỗi cập nhật trạng thái:', err)
        alert(err.response?.data?.message || 'Có lỗi xảy ra')
    }
}

const handleCreateLink = async () => {
    isCreatingLink.value = true
    try {
        const res = await createLink({
            hostEmployeeId: linkForm.hostEmployeeId,
            expiryHours: linkForm.expiryHours
        })
        createdLink.value = res.data
        // Tự động mở link trong tab mới
        if (res.data.registrationUrl) {
            window.open(res.data.registrationUrl, '_blank')
            closeCreateLinkModal()
        }
    } catch (err) {
        console.error('Lỗi tạo link:', err)
        alert(err.response?.data?.message || 'Có lỗi xảy ra khi tạo link')
    } finally {
        isCreatingLink.value = false
    }
}

const copyLink = () => {
    const url = createdLink.value.registrationUrl
    // Thử clipboard API trước
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            copied.value = true
            setTimeout(() => (copied.value = false), 2000)
        }).catch(() => {
            fallbackCopy(url)
        })
    } else {
        fallbackCopy(url)
    }
}

const fallbackCopy = (text) => {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-9999px'
    document.body.appendChild(textarea)
    textarea.select()
    try {
        document.execCommand('copy')
        copied.value = true
        setTimeout(() => (copied.value = false), 2000)
    } catch (e) {
        console.error('Copy failed:', e)
        alert('Không thể copy tự động. Vui lòng copy thủ công: ' + text)
    }
    document.body.removeChild(textarea)
}

const closeCreateLinkModal = () => {
    showCreateLinkModal.value = false
    createdLink.value = null
    copied.value = false
    linkForm.hostEmployeeId = null
    linkForm.expiryHours = 24
}

// ── Watchers ─────────────────────────────────────
let searchTimeout = null
watch(searchQuery, () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => {
        currentPage.value = 1
        fetchRegistrations()
    }, 400)
})

watch([filterStatus, filterDate], () => {
    currentPage.value = 1
    fetchRegistrations()
})

// ── Init ─────────────────────────────────────────
onMounted(() => {
    fetchRegistrations()
    fetchStats()
    fetchEmployees()
})
</script>

<style scoped>
/* Plate number */
.plate {
    font-family: monospace;
    font-weight: 700;
    font-size: 0.9rem;
    padding: 3px 10px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    letter-spacing: 0.5px;
}

/* Time range */
.time-range {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--text-secondary);
}

/* Action buttons */
.btn-approve {
    color: var(--accent-success) !important;
    border-color: rgba(16, 185, 129, 0.3) !important;
}

.btn-approve:hover {
    background: rgba(16, 185, 129, 0.15) !important;
    border-color: var(--accent-success) !important;
}

.btn-reject {
    color: var(--accent-danger) !important;
    border-color: rgba(239, 68, 68, 0.3) !important;
}

.btn-reject:hover {
    background: rgba(239, 68, 68, 0.15) !important;
    border-color: var(--accent-danger) !important;
}

/* Loading / Empty states */
.loading-state,
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: var(--text-muted);
}

.empty-state p {
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-secondary);
}

.empty-sub {
    font-size: 0.85rem !important;
    color: var(--text-muted) !important;
    font-weight: 400 !important;
    margin-top: 4px;
}

.spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 12px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Detail sections */
.detail-section {
    margin-bottom: 24px;
}

.section-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
}

.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}

.detail-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.detail-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.detail-value {
    font-size: 0.9rem;
    color: var(--text-primary);
    font-weight: 500;
}

/* Visitors list */
.visitors-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.visitor-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: var(--bg-input);
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--border-color);
}

.visitor-info {
    display: flex;
    flex-direction: column;
}

.visitor-name {
    font-weight: 600;
    font-size: 0.85rem;
}

.visitor-id {
    font-size: 0.78rem;
    color: var(--text-muted);
}

/* Access log list */
.access-log-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.log-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 14px;
    background: var(--bg-input);
    border-radius: var(--border-radius-sm);
    border: 1px solid var(--border-color);
    font-size: 0.85rem;
}

.log-time {
    color: var(--text-secondary);
}

.log-note {
    color: var(--text-muted);
    font-style: italic;
    margin-left: auto;
}

/* Link success */
.link-success {
    text-align: center;
    padding: 20px 0;
}

.success-icon {
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.15);
    color: var(--accent-success);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
}

.success-icon svg {
    width: 28px;
    height: 28px;
}

.link-success h4 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.link-expiry {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin-bottom: 20px;
}

.copy-btn {
    flex-shrink: 0;
    width: auto !important;
}

.close-btn {
    width: auto !important;
}

.link-box {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 480px;
    margin: 0 auto;
}

.link-url {
    display: block;
    padding: 10px 14px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--accent-primary);
    font-size: 0.85rem;
    text-decoration: none;
    word-break: break-all;
    transition: all 0.2s ease;
}

.link-url:hover {
    border-color: var(--accent-primary);
    background: rgba(59, 130, 246, 0.08);
}

.link-actions {
    display: flex;
    gap: 8px;
    justify-content: center;
}

.open-btn {
    width: auto !important;
    text-decoration: none !important;
    display: inline-flex;
    align-items: center;
}

/* Form hint */
.form-hint {
    display: block;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
}

@media (max-width: 768px) {
    .detail-grid {
        grid-template-columns: 1fr;
    }
}

/* Fix modal footer buttons */
.modal-footer .btn {
    flex: 0 0 auto;
    width: auto;
}

.modal {
    overflow: hidden;
}
</style>
