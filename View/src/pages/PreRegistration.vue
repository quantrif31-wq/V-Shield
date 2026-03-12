<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Đăng ký trước</h1>
                <p class="page-subtitle">Quản lý đơn đăng ký khách thăm quan trước khi đến</p>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="showCreateLinkModal = true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                        <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
                    </svg>
                    Tạo link đăng ký
                </button>
            </div>
        </header>

        <!-- Stats Overview Row -->
        <div class="bento-grid-mini" style="grid-template-columns: repeat(4, 1fr);">
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" /><rect x="8" y="2" width="8" height="4" rx="1" ry="1" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val blue">{{ stats.total }}</div>
                    <div class="stat-lbl">Tổng đơn</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper orange" style="background: rgba(249, 115, 22, 0.1); color: var(--accent-warning);">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M12 8v4" /><path d="M12 16h.01" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val" style="color: var(--accent-warning);">{{ stats.pending }}</div>
                    <div class="stat-lbl">Chờ duyệt</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M9 12l2 2 4-4" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val green">{{ stats.approved }}</div>
                    <div class="stat-lbl">Đã duyệt</div>
                </div>
            </div>
            <div class="bento-card stat-card">
                <div class="stat-icon-wrapper red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" /><path d="M15 9l-6 6" /><path d="M9 9l6 6" /></svg>
                </div>
                <div class="stat-details">
                    <div class="stat-val red">{{ stats.rejected }}</div>
                    <div class="stat-lbl">Từ chối</div>
                </div>
            </div>
        </div>

        <!-- Main Content Box -->
        <div class="bento-card table-section">
            <div class="table-toolbar">
                <div class="search-box">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" /></svg>
                    <input v-model="searchQuery" type="text" placeholder="Tìm tên khách, SĐT..." />
                </div>
                <div class="filter-box" style="display: flex; gap: 12px;">
                    <select v-model="filterStatus" class="minimal-select">
                        <option value="">Tất cả trạng thái</option>
                        <option value="Pending">Chờ duyệt</option>
                        <option value="Approved">Đã duyệt</option>
                        <option value="Rejected">Từ chối</option>
                    </select>
                    <input v-model="filterDate" type="date" class="minimal-select" />
                </div>
            </div>

            <!-- States -->
            <div v-if="isLoading" class="empty-layout">
                <div class="spinner-lg"></div>
                <p>Đang tải dữ liệu đăng ký...</p>
            </div>
            <div v-else-if="registrations.length === 0" class="empty-layout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; color: var(--text-muted); margin-bottom: 12px;"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2" /><rect x="8" y="2" width="8" height="4" rx="1" ry="1" /><path d="M9 14l2 2 4-4" /></svg>
                <p style="font-size: 1.05rem; font-weight: 500; color: var(--text-primary); margin-bottom: 4px;">Chưa có đơn đăng ký nào</p>
                <p style="font-size: 0.9rem;">Tạo link đăng ký và gửi cho khách để bắt đầu</p>
            </div>
            
            <!-- Sleek Table -->
            <div v-else class="sleek-table-container">
                <table class="sleek-table">
                    <thead>
                        <tr>
                            <th>Khách</th>
                            <th>Host / Thời gian</th>
                            <th>Biển số</th>
                            <th>Khách đi cùng</th>
                            <th>Trạng thái</th>
                            <th class="text-right">Hành động</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="reg in registrations" :key="reg.registrationId" class="table-row">
                            <td>
                                <div class="user-cell">
                                    <div class="avatar" :style="{ background: getAvatarColor(getInitials(reg.guestFullName)) }">
                                        {{ getInitials(reg.guestFullName) }}
                                    </div>
                                    <div class="user-info">
                                        <span class="user-name">{{ reg.guestFullName }}</span>
                                        <span class="user-id">SĐT: {{ reg.guestPhone || '—' }}</span>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="host-cell">
                                    <span class="host-name">Host: {{ reg.hostEmployeeName }}</span>
                                    <span class="time-range-txt">
                                        {{ formatDateTime(reg.expectedTimeIn) }} 
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 12px; height: 12px;"><polyline points="9 18 15 12 9 6"></polyline></svg>
                                        {{ formatDateTime(reg.expectedTimeOut) }}
                                    </span>
                                </div>
                            </td>
                            <td>
                                <span v-if="reg.expectedLicensePlate" class="plate">{{ reg.expectedLicensePlate }}</span>
                                <span v-else class="walk-txt">—</span>
                            </td>
                            <td>
                                <div class="visitors-count">
                                    {{ reg.numberOfVisitors }} khách
                                </div>
                            </td>
                            <td>
                                <span class="status-pill minimal" :class="getStatusClass(reg.status)">
                                    <span class="pill-dot"></span>
                                    {{ getStatusLabel(reg.status) }}
                                </span>
                            </td>
                            <td class="text-right">
                                <div class="action-menu">
                                    <button class="icon-btn" @click="viewDetail(reg.registrationId)" title="Xem chi tiết">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                                    </button>
                                    <button v-if="reg.status === 'Pending'" class="icon-btn action-approve" @click="handleUpdateStatus(reg.registrationId, 'Approved')" title="Duyệt">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5" /></svg>
                                    </button>
                                    <button v-if="reg.status === 'Pending'" class="icon-btn action-reject" @click="handleUpdateStatus(reg.registrationId, 'Rejected')" title="Từ chối">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18" /><path d="M6 6l12 12" /></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div class="pagination-footer" v-if="registrations.length > 0">
                <span class="showing-txt">Hiển thị {{ registrations.length }} / {{ totalItems }} đơn</span>
                <div class="pg-controls">
                    <button class="pg-btn" :disabled="currentPage <= 1" @click="currentPage--; fetchRegistrations()">‹</button>
                    <button v-for="p in totalPages" :key="p" class="pg-btn" :class="{ active: p === currentPage }" @click="currentPage = p; fetchRegistrations()">{{ p }}</button>
                    <button class="pg-btn" :disabled="currentPage >= totalPages" @click="currentPage++; fetchRegistrations()">›</button>
                </div>
            </div>
        </div>

        <!-- Detail Modal Modern -->
        <transition name="modal">
            <div v-if="showDetailModal" class="modal-backdrop" @click.self="showDetailModal = false">
                <div class="modern-modal" style="max-width: 720px;">
                    <div class="modal-top">
                        <h3>Chi tiết Đăng ký #{{ detail?.registrationId }}</h3>
                        <button class="icon-close" @click="showDetailModal = false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>

                    <div v-if="isLoadingDetail" class="empty-layout">
                        <div class="spinner-lg"></div>
                        <p>Đang tải dữ liệu...</p>
                    </div>
                    <div v-else-if="detail" class="modal-body scrollable-body">
                        <!-- Guest info -->
                        <div class="detail-section-bento">
                            <h4 class="bento-subtitle">Thông tin Đăng ký</h4>
                            <div class="mini-grid-info">
                                <div class="info-block">
                                    <span class="lbl">Họ tên Khách</span>
                                    <span class="val">{{ detail.guestFullName }}</span>
                                </div>
                                <div class="info-block">
                                    <span class="lbl">Liên hệ</span>
                                    <span class="val">{{ detail.guestPhone || '—' }}</span>
                                </div>
                                <div class="info-block">
                                    <span class="lbl">Biển số PT</span>
                                    <span class="val plate-val">{{ detail.expectedLicensePlate || '—' }}</span>
                                </div>
                                <div class="info-block">
                                    <span class="lbl">Nhân sự Host</span>
                                    <span class="val text-primary">{{ detail.hostEmployeeName }}</span>
                                </div>
                                <div class="info-block">
                                    <span class="lbl">Thời gian Dự kiến</span>
                                    <span class="val">{{ formatDateTime(detail.expectedTimeIn) }} <br/>đến {{ formatDateTime(detail.expectedTimeOut) }}</span>
                                </div>
                                <div class="info-block">
                                    <span class="lbl">Trạng thái</span>
                                    <span class="status-pill minimal" :class="getStatusClass(detail.status)" style="margin-top: 4px;">
                                        <span class="pill-dot"></span>
                                        {{ getStatusLabel(detail.status) }}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <!-- Visitors Array -->
                        <div v-if="detail.visitors && detail.visitors.length > 0" class="detail-section-bento mt-2">
                            <h4 class="bento-subtitle">Đoàn khách đi cùng ({{ detail.visitors.length }})</h4>
                            <div class="pill-list mt-1">
                                <div v-for="(v, i) in detail.visitors" :key="i" class="visitor-card">
                                    <div class="avatar mini" :style="{ background: getAvatarColor(getInitials(v.fullName)) }">{{ getInitials(v.fullName) }}</div>
                                    <div class="v-details">
                                        <span class="v-name">{{ v.fullName }}</span>
                                        <span class="v-id">CCCD: {{ v.idCardNumber || '—' }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Access Logs -->
                        <div v-if="detail.accessLogs && detail.accessLogs.length > 0" class="detail-section-bento mt-2">
                            <h4 class="bento-subtitle">Lịch sử check-in / check-out</h4>
                            <div class="timeline-box mt-1">
                                <div v-for="log in detail.accessLogs" :key="log.logId" class="timeline-row">
                                    <div class="tl-chip" :class="log.direction === 'IN' ? 'check-in' : 'check-out'">{{ log.direction === 'IN' ? 'VÀO' : 'RA' }}</div>
                                    <div class="tl-time">{{ formatDateTime(log.timestamp) }}</div>
                                    <div class="tl-plate" v-if="log.capturedLicensePlate">{{ log.capturedLicensePlate }}</div>
                                    <div class="tl-note" v-if="log.note">{{ log.note }}</div>
                                </div>
                            </div>
                        </div>

                        <div v-if="detail.status === 'Pending'" class="action-footer mt-4">
                            <button class="btn btn-danger" @click="handleUpdateStatus(detail.registrationId, 'Rejected'); showDetailModal = false">
                                Từ chối Đơn
                            </button>
                            <button class="btn btn-primary" @click="handleUpdateStatus(detail.registrationId, 'Approved'); showDetailModal = false" style="background: var(--accent-success); box-shadow: 0 4px 14px rgba(16,185,129,0.3);">
                                Duyệt Đăng ký
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </transition>

        <!-- Create Link Modal Modern -->
        <transition name="modal">
            <div v-if="showCreateLinkModal" class="modal-backdrop" @click.self="showCreateLinkModal = false">
                <div class="modern-modal" style="max-width: 480px;">
                    <div class="modal-top">
                        <h3>Tạo Link Đăng ký</h3>
                        <button class="icon-close" @click="closeCreateLinkModal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
                    </div>

                    <div class="modal-body">
                        <template v-if="!createdLink">
                            <div class="input-pane">
                                <label>Nhân sự Host đại diện <span class="req">*</span></label>
                                <select v-model="linkForm.hostEmployeeId" class="sleek-select">
                                    <option :value="null" disabled>-- Chọn nhân sự --</option>
                                    <option v-for="emp in employees" :key="emp.employeeId" :value="emp.employeeId">
                                        {{ emp.fullName }}
                                    </option>
                                </select>
                            </div>
                            <div class="input-pane mt-2">
                                <label>Thời gian hiệu lực (giờ)</label>
                                <input v-model.number="linkForm.expiryHours" type="number" min="1" max="168" class="sleek-input" placeholder="Mặc định: 24h" />
                                <small class="note-txt">Link đăng ký sẽ hết hạn sau số giờ thiết lập (Max: 168h).</small>
                            </div>
                            <div class="modal-actions mt-4">
                                <button class="btn btn-secondary" @click="closeCreateLinkModal">Hủy bỏ</button>
                                <button class="btn btn-primary" @click="handleCreateLink" :disabled="!linkForm.hostEmployeeId || isCreatingLink">
                                    <span v-if="isCreatingLink" class="spinner-sm"></span> {{ isCreatingLink ? 'Đang tạo...' : 'Khởi tạo Link' }}
                                </button>
                            </div>
                        </template>

                        <template v-else>
                            <div class="success-box">
                                <div class="success-icon lg">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9 12l2 2 4-4"/></svg>
                                </div>
                                <h4 class="mb-1">Khởi tạo Thành công</h4>
                                <p class="text-secondary text-sm">Hiệu lực đến: {{ formatDateTime(createdLink.expiredAt) }}</p>

                                <div class="copy-box mt-3">
                                    <input type="text" readonly :value="createdLink.registrationUrl" class="sleek-input" />
                                    <div class="flex gap-2 mt-2">
                                        <button class="btn btn-primary flex-1" @click="copyLink">
                                            {{ copied ? 'Đã Copy!' : 'Copy Link' }}
                                        </button>
                                        <a :href="createdLink.registrationUrl" target="_blank" rel="noopener noreferrer" class="btn btn-secondary flex-1 text-center" style="display: flex; align-items: center; justify-content: center; text-decoration: none;">
                                            Mở tab mới ↗
                                        </a>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-actions mt-4 centered">
                                <button class="btn btn-secondary" @click="closeCreateLinkModal" style="width: 100%;">Đóng Cửa sổ</button>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { getAll, getDetail, updateStatus, createLink } from '../services/preRegistrationApi'
import { getAll as getAllEmployees } from '../services/employeeApi'

const registrations = ref([])
const totalItems = ref(0)
const currentPage = ref(1)
const pageSize = 20
const isLoading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const filterDate = ref('')

const stats = reactive({ total: 0, pending: 0, approved: 0, rejected: 0 })

const showDetailModal = ref(false)
const detail = ref(null)
const isLoadingDetail = ref(false)

const showCreateLinkModal = ref(false)
const linkForm = reactive({ hostEmployeeId: null, expiryHours: 24 })
const createdLink = ref(null)
const isCreatingLink = ref(false)
const copied = ref(false)
const employees = ref([])
const totalPages = ref(1)

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
    const map = { Pending: 'Chờ duyệt', Approved: 'Đã duyệt', Rejected: 'Đã từ chối' }
    return map[s] || s
}

const getStatusClass = (s) => {
    const map = { Pending: 'pending', Approved: 'check-in', Rejected: 'inactive' }
    return map[s] || ''
}

const getAvatarColor = (str) => {
    let hash = 0; for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const avColors = [ '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#f43f5e' ];
    return avColors[Math.abs(hash) % avColors.length];
}

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
    } catch (err) {}
}

const fetchEmployees = async () => {
    try {
        const res = await getAllEmployees()
        employees.value = res.data || []
    } catch (err) {}
}

const viewDetail = async (id) => {
    showDetailModal.value = true
    isLoadingDetail.value = true
    detail.value = null
    try {
        const res = await getDetail(id)
        detail.value = res.data
    } catch (err) {} finally { isLoadingDetail.value = false }
}

const handleUpdateStatus = async (id, status) => {
    try {
        await updateStatus(id, status)
        await fetchRegistrations()
        await fetchStats()
    } catch (err) { alert(err.response?.data?.message || 'Có lỗi xảy ra') }
}

const handleCreateLink = async () => {
    isCreatingLink.value = true
    try {
        const res = await createLink({ hostEmployeeId: linkForm.hostEmployeeId, expiryHours: linkForm.expiryHours })
        createdLink.value = res.data
        if (res.data.registrationUrl) {
            window.open(res.data.registrationUrl, '_blank')
            closeCreateLinkModal()
        }
    } catch (err) { alert('Có lỗi xảy ra khi tạo link') } finally { isCreatingLink.value = false }
}

const copyLink = () => {
    const url = createdLink.value.registrationUrl
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => { copied.value = true; setTimeout(() => (copied.value = false), 2000) }).catch(() => fallbackCopy(url))
    } else { fallbackCopy(url) }
}

const fallbackCopy = (text) => {
    const textarea = document.createElement('textarea')
    textarea.value = text; textarea.style.position = 'fixed'; textarea.style.left = '-9999px';
    document.body.appendChild(textarea); textarea.select();
    try { document.execCommand('copy'); copied.value = true; setTimeout(() => (copied.value = false), 2000) } catch (e) { alert('Copy thủ công: ' + text) }
    document.body.removeChild(textarea)
}

const closeCreateLinkModal = () => {
    showCreateLinkModal.value = false
    createdLink.value = null
    copied.value = false
    linkForm.hostEmployeeId = null
    linkForm.expiryHours = 24
}

let searchTimeout = null
watch(searchQuery, () => {
    if (searchTimeout) clearTimeout(searchTimeout)
    searchTimeout = setTimeout(() => { currentPage.value = 1; fetchRegistrations() }, 400)
})

watch([filterStatus, filterDate], () => { currentPage.value = 1; fetchRegistrations() })

onMounted(() => { fetchRegistrations(); fetchStats(); fetchEmployees() })
</script>

<style scoped>
/* Common Page Layout */
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
.stat-icon-wrapper.red { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }
.stat-val { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.stat-val.blue { color: var(--accent-primary); }
.stat-val.green { color: var(--accent-success); }
.stat-val.red { color: var(--accent-danger); }
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

.user-cell { display: flex; align-items: center; gap: 14px; }
.avatar { width: 38px; height: 38px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 700; color: white; }
.avatar.mini { width: 32px; height: 32px; font-size: 0.8rem; }
.user-info { display: flex; flex-direction: column; }
.user-name { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.user-id { font-size: 0.8rem; color: var(--text-muted); font-family: monospace; }

.host-cell { display: flex; flex-direction: column; gap: 4px; }
.host-name { font-weight: 500; font-size: 0.9rem; color: var(--text-primary); }
.time-range-txt { font-size: 0.8rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px; }

.status-pill.minimal { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid transparent; letter-spacing: 0.5px; display: inline-flex; align-items: center; gap: 6px;}
.status-pill.check-in { background: rgba(16, 185, 129, 0.05); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }
.status-pill.pending { background: rgba(249, 115, 22, 0.05); color: var(--accent-warning); border-color: rgba(249, 115, 22, 0.2); }
.status-pill.inactive { background: rgba(239, 68, 68, 0.05); color: var(--accent-danger); border-color: rgba(239, 68, 68, 0.2); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.plate { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 0.85rem; padding: 4px 10px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-primary); }
.plate-val { font-family: 'JetBrains Mono', monospace; font-weight: 700; letter-spacing: 0.5px;}
.walk-txt { color: var(--text-muted); font-size: 0.9rem; font-style: italic; }

.visitors-count { display: inline-flex; padding: 4px 10px; background: var(--bg-input); border-radius: 6px; font-size: 0.85rem; color: var(--text-secondary); border: 1px solid var(--border-color); }

.action-menu { display: flex; gap: 8px; justify-content: flex-end; }
.icon-btn { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: none; background: transparent; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.icon-btn svg { width: 18px; }
.icon-btn:hover { background: var(--bg-input); color: var(--text-primary); }
.icon-btn.action-approve:hover { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.icon-btn.action-reject:hover { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

/* Spinners & Empties */
.empty-layout { padding: 60px; text-align: center; color: var(--text-muted); display: flex; flex-direction: column; align-items: center; gap: 16px; }
.spinner-lg { width: 36px; height: 36px; border: 3px solid var(--border-color); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
.spinner-sm { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; display: inline-block; margin-right: 6px; }

@keyframes spin { to { transform: rotate(360deg); } }

/* Pagination Area */
.pagination-footer { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border-color); }
.showing-txt { font-size: 0.9rem; color: var(--text-secondary); }
.pg-controls { display: flex; gap: 6px; }
.pg-btn { background: var(--bg-input); border: 1px solid var(--border-color); color: var(--text-primary); width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-weight: 500; transition: border 0.2s; }
.pg-btn:hover:not(:disabled) { border-color: var(--text-muted); }
.pg-btn.active { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }
.pg-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Modern Modals */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 1000; padding: 20px;}
.modern-modal { background: var(--bg-card); width: 100%; border-radius: var(--border-radius-lg); border: 1px solid var(--border-color); box-shadow: var(--shadow-xl); overflow: hidden; display: flex; flex-direction: column; max-height: 90vh; }
.scrollable-body { overflow-y: auto; padding: 24px; }
.modal-top { display: flex; justify-content: space-between; align-items: center; padding: 24px; border-bottom: 1px solid var(--border-color); }
.modal-top h3 { font-size: 1.25rem; font-weight: 700; color: var(--text-primary); margin: 0;}
.icon-close { background: none; border: none; color: var(--text-muted); cursor: pointer; width: 24px; transition: color 0.2s; }
.icon-close:hover { color: var(--accent-danger); }

.modal-body { padding: 24px; display: flex; flex-direction: column; }
.detail-section-bento { background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
.bento-subtitle { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 0 0 16px 0; border-bottom: 1px solid var(--border-color); padding-bottom: 12px;}

.mini-grid-info { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.info-block { display: flex; flex-direction: column; gap: 4px; }
.info-block .lbl { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
.info-block .val { font-size: 0.95rem; font-weight: 500; color: var(--text-primary); }
.text-primary { color: var(--accent-primary) !important; font-weight: 600 !important; }

.pill-list { display: flex; flex-direction: column; gap: 8px; }
.visitor-card { display: flex; align-items: center; gap: 12px; background: var(--bg-card); border: 1px solid var(--border-color); padding: 10px 14px; border-radius: 8px; }
.v-details { display: flex; flex-direction: column; }
.v-name { font-weight: 600; font-size: 0.9rem; }
.v-id { font-size: 0.8rem; color: var(--text-secondary); }

.timeline-box { display: flex; flex-direction: column; gap: 10px; }
.timeline-row { display: flex; align-items: center; gap: 12px; background: var(--bg-card); padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border-color); }
.tl-chip { font-size: 0.75rem; font-weight: 700; padding: 4px 8px; border-radius: 4px; }
.tl-chip.check-in { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.tl-chip.check-out { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.tl-time { font-family: monospace; font-size: 0.85rem; color: var(--text-secondary); width: 140px; }
.tl-plate { font-family: monospace; font-weight: 700; font-size: 0.85rem; padding: 2px 6px; background: var(--bg-input); border-radius: 4px; border: 1px solid var(--border-color); }
.tl-note { font-style: italic; color: var(--text-muted); font-size: 0.85rem; margin-left: auto; }

.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }
.req { color: var(--accent-danger); }
.note-txt { font-size: 0.8rem; color: var(--text-muted); }

.sleek-input, .sleek-select { width: 100%; padding: 12px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.95rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }

/* Success Box */
.success-box { text-align: center; padding: 20px 10px; }
.success-icon.lg { width: 64px; height: 64px; border-radius: 50%; background: rgba(16, 185, 129, 0.1); color: var(--accent-success); display: flex; justify-content: center; align-items: center; margin: 0 auto 16px; }
.success-icon.lg svg { width: 32px; height: 32px; }
.mb-1 { margin-bottom: 4px; }
.text-sm { font-size: 0.85rem; }
.copy-box { background: var(--bg-card); padding: 16px; border: 1px solid var(--border-color); border-radius: 8px; text-align: left; }
.flex { display: flex; }
.gap-2 { gap: 8px; }
.flex-1 { flex: 1; }
.mt-1 { margin-top: 8px; }
.mt-2 { margin-top: 16px; }
.mt-3 { margin-top: 24px; }
.mt-4 { margin-top: 32px; }

.modal-actions { display: flex; justify-content: flex-end; gap: 12px; }
.action-footer { display: flex; justify-content: flex-end; gap: 16px; padding-top: 20px; border-top: 1px solid var(--border-color); }

.modal-enter-active, .modal-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; transform: scale(0.95); }

@media (max-width: 1200px) { .bento-grid-mini { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) {
    .bento-grid-mini { grid-template-columns: 1fr; }
    .table-toolbar { flex-direction: column; gap: 16px; align-items: stretch;}
    .search-box { width: 100%; }
    .mini-grid-info { grid-template-columns: 1fr; }
    .timeline-row { flex-wrap: wrap; }
}
</style>
