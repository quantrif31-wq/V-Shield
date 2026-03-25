<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Access logs</span>
                <h1 class="page-title">Tra cứu toàn bộ lịch sử ra vào theo thời gian, cổng, hướng di chuyển và trạng thái xử lý.</h1>
                <p class="page-subtitle">
                    Màn hình này dành cho bảo vệ và kiểm soát viên tại cổng để rà soát các lượt vào/ra, đối chiếu bằng chứng
                    nhận diện và phát hiện các trường hợp cần xử lý tiếp.
                </p>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Hôm nay</span>
                        <strong>{{ summary.totalToday }}</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        Nhật ký thời gian thực
                    </span>
                </div>

                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Vào</span>
                        <strong>{{ summary.entriesToday }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Ra</span>
                        <strong>{{ summary.exitsToday }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Ngoại lệ</span>
                        <strong>{{ summary.exceptionsToday }}</strong>
                    </div>
                </div>
            </div>
        </section>

        <section class="metric-grid">
            <article class="metric-tile">
                <span class="metric-label">Tổng lượt hôm nay</span>
                <strong class="metric-value">{{ summary.totalToday }}</strong>
                <span class="metric-note">Tất cả bản ghi phát sinh trong ngày.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Bypass thủ công</span>
                <strong class="metric-value">{{ summary.bypassToday }}</strong>
                <span class="metric-note">Trường hợp mở thủ công cần được rà soát kỹ.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Xe đang trong khu vực</span>
                <strong class="metric-value">{{ summary.vehiclesInside }}</strong>
                <span class="metric-note">Đọc từ trạng thái đỗ xe hiện tại.</span>
            </article>
            <article class="metric-tile">
                <span class="metric-label">Tỷ lệ thành công</span>
                <strong class="metric-value">{{ summary.successRate }}%</strong>
                <span class="metric-note">So sánh giữa lượt thường và lượt ngoại lệ.</span>
            </article>
        </section>

        <section class="ops-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Filter controls</span>
                    <h2 class="panel-title">Bộ lọc lịch sử ra vào</h2>
                    <p class="panel-copy">
                        Chỉ áp dụng khi bấm nút lọc để tránh rỗng dữ liệu tạm thời lúc đang nhập.
                    </p>
                </div>
                <div class="filter-summary">
                    <span class="soft-chip success">{{ total }} bản ghi</span>
                    <span v-for="tag in appliedFilterTags" :key="tag" class="soft-chip">{{ tag }}</span>
                </div>
            </div>

            <div class="filter-card">
                <div class="filter-grid access-filter-grid">
                    <label class="filter-field filter-field-query">
                        <span class="field-label">Từ khóa</span>
                        <div class="search-bar">
                            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                            <input
                                v-model="draftFilters.query"
                                type="text"
                                placeholder="Tìm theo tên, biển số, ghi chú..."
                                @keyup.enter="applyFilters"
                            />
                        </div>
                    </label>

                    <label class="filter-field filter-field-direction">
                        <span class="field-label">Chiều di chuyển</span>
                        <select v-model="draftFilters.direction" class="filter-select">
                            <option value="">Tất cả chiều</option>
                            <option value="IN">Vào</option>
                            <option value="OUT">Ra</option>
                        </select>
                    </label>

                    <label class="filter-field filter-field-gate">
                        <span class="field-label">Cổng</span>
                        <select v-model="draftFilters.gateId" class="filter-select">
                            <option value="">Tất cả cổng</option>
                            <option v-for="gate in gates" :key="gate.gateId" :value="String(gate.gateId)">{{ gate.gateName }}</option>
                        </select>
                    </label>

                    <label class="filter-field filter-field-status">
                        <span class="field-label">Trạng thái</span>
                        <select v-model="draftFilters.status" class="filter-select">
                            <option value="">Tất cả trạng thái</option>
                            <option v-for="status in statusOptions" :key="status" :value="status">{{ status }}</option>
                        </select>
                    </label>

                    <label class="filter-field filter-field-date">
                        <span class="field-label">Từ ngày</span>
                        <input v-model="draftFilters.dateFrom" type="date" class="filter-select" />
                    </label>

                    <label class="filter-field filter-field-date">
                        <span class="field-label">Đến ngày</span>
                        <input v-model="draftFilters.dateTo" type="date" class="filter-select" />
                    </label>
                </div>

                <div class="filter-footer">
                    <div>
                        <p class="filter-hint">Khoảng ngày sẽ tự đổi lại nếu nhập ngược thứ tự.</p>
                        <p v-if="filterNotice" class="filter-notice">{{ filterNotice }}</p>
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-secondary btn-sm" :disabled="isLoading && !hasPendingChanges" @click="resetFilters">
                            Đặt lại
                        </button>
                        <button class="btn btn-primary btn-sm" :disabled="!hasPendingChanges && !filterNotice" @click="applyFilters">
                            Áp dụng lọc
                        </button>
                    </div>
                </div>
            </div>

            <div v-if="isLoading" class="empty-card">Đang tải lịch sử ra vào...</div>
            <div v-else-if="items.length === 0" class="empty-card">
                {{ hasActiveFilters ? 'Không có bản ghi nào khớp với bộ lọc đã áp dụng.' : 'Chưa có bản ghi ra vào nào để hiển thị.' }}
            </div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Đối tượng</th>
                            <th>Chiều</th>
                            <th>Cổng / Camera</th>
                            <th>Biển số</th>
                            <th>Phương thức</th>
                            <th>Trạng thái</th>
                            <th>Ghi chú</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in items" :key="item.logId">
                            <td>
                                <div class="table-main">{{ formatDateTime(item.timestamp) }}</div>
                            </td>
                            <td>
                                <div class="table-main">{{ item.actorName }}</div>
                                <div class="table-sub">{{ actorTypeLabel(item.actorType) }}</div>
                            </td>
                            <td>
                                <span class="badge" :class="item.direction === 'IN' ? 'active' : 'pending'">
                                    {{ item.direction === 'IN' ? 'VÀO' : 'RA' }}
                                </span>
                            </td>
                            <td>
                                <div class="table-main">{{ item.gateName || 'Chưa gán cổng' }}</div>
                                <div class="table-sub">{{ item.cameraName || 'Không có camera' }}</div>
                            </td>
                            <td>
                                <span v-if="item.capturedLicensePlate" class="plate-pill">{{ item.capturedLicensePlate }}</span>
                                <span v-else class="table-sub">Đi bộ / không ghi nhận</span>
                            </td>
                            <td>
                                <span class="soft-chip" :class="methodClass(item.method)">{{ methodLabel(item.method) }}</span>
                            </td>
                            <td>
                                <div class="chip-row">
                                    <span v-if="item.resultStatus" class="soft-chip">{{ item.resultStatus }}</span>
                                    <span v-if="item.isBypass" class="soft-chip danger">BYPASS</span>
                                    <span v-if="item.isException" class="soft-chip warn">NGOẠI LỆ</span>
                                </div>
                            </td>
                            <td>
                                <div class="table-sub note-cell">
                                    {{ item.note || item.exceptionReasonDescription || '—' }}
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="total > 0" class="pagination">
                <div class="pagination-info">Hiển thị {{ items.length }} / {{ total }} bản ghi</div>
                <div class="pagination-buttons">
                    <button class="pagination-btn" :disabled="page === 1" @click="setPage(page - 1)">‹</button>
                    <button
                        v-for="current in visiblePages"
                        :key="current"
                        class="pagination-btn"
                        :class="{ active: current === page }"
                        @click="setPage(current)"
                    >
                        {{ current }}
                    </button>
                    <button class="pagination-btn" :disabled="page === totalPages" @click="setPage(page + 1)">›</button>
                </div>
            </div>
        </section>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { getAccessLogs, getAccessLogSummary } from '../services/accessLogApi'
import { getGates } from '../services/deviceManagementApi'

const pageSize = 12

const createDefaultFilters = () => ({
    query: '',
    direction: '',
    gateId: '',
    status: '',
    dateFrom: '',
    dateTo: '',
})

const isLoading = ref(true)
const items = ref([])
const total = ref(0)
const page = ref(1)
const gates = ref([])
const filterNotice = ref('')
const draftFilters = reactive(createDefaultFilters())
const appliedFilters = ref(createDefaultFilters())
const summary = ref({
    totalToday: 0,
    entriesToday: 0,
    exitsToday: 0,
    exceptionsToday: 0,
    bypassToday: 0,
    vehiclesInside: 0,
    successRate: 0,
})

const defaultStatusOptions = ['APPROVED', 'SUCCESS', 'MATCHED', 'GRANTED', 'OK', 'DENIED', 'FAILED', 'REJECTED']

const normalizeFilters = (source) => {
    const normalized = {
        query: source.query?.trim() || '',
        direction: source.direction || '',
        gateId: source.gateId || '',
        status: source.status || '',
        dateFrom: source.dateFrom || '',
        dateTo: source.dateTo || '',
    }

    let swapped = false
    if (normalized.dateFrom && normalized.dateTo && normalized.dateFrom > normalized.dateTo) {
        ;[normalized.dateFrom, normalized.dateTo] = [normalized.dateTo, normalized.dateFrom]
        swapped = true
    }

    return { normalized, swapped }
}

const serializeFilters = (source) => JSON.stringify(normalizeFilters(source).normalized)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const visiblePages = computed(() => {
    const start = Math.max(1, page.value - 2)
    const end = Math.min(totalPages.value, start + 4)
    return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

const hasPendingChanges = computed(() => serializeFilters(draftFilters) !== serializeFilters(appliedFilters.value))
const hasActiveFilters = computed(() =>
    Object.values(normalizeFilters(appliedFilters.value).normalized).some((value) => Boolean(value))
)

const statusOptions = computed(() => {
    const uniqueStatuses = new Set(defaultStatusOptions)
    items.value.forEach((item) => {
        if (item.resultStatus) {
            uniqueStatuses.add(item.resultStatus)
        }
    })
    return Array.from(uniqueStatuses)
})

const appliedFilterTags = computed(() => {
    const current = normalizeFilters(appliedFilters.value).normalized
    const tags = []

    if (current.query) tags.push(`Từ khóa: ${current.query}`)
    if (current.direction) tags.push(current.direction === 'IN' ? 'Chiều: Vào' : 'Chiều: Ra')

    if (current.gateId) {
        const gate = gates.value.find((item) => String(item.gateId) === current.gateId)
        tags.push(`Cổng: ${gate?.gateName || current.gateId}`)
    }

    if (current.status) tags.push(`Trạng thái: ${current.status}`)
    if (current.dateFrom) tags.push(`Từ: ${formatDate(current.dateFrom)}`)
    if (current.dateTo) tags.push(`Đến: ${formatDate(current.dateTo)}`)

    return tags
})

function formatDate(value) {
    if (!value) return '--'
    return new Date(value).toLocaleDateString('vi-VN')
}

function formatDateTime(value) {
    if (!value) return '--'
    return new Date(value).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

function actorTypeLabel(value) {
    const map = {
        Employee: 'Nhân sự nội bộ',
        Guest: 'Khách / đăng ký trước',
        Unknown: 'Chưa xác định',
    }
    return map[value] || 'Chưa phân loại'
}

function methodLabel(value) {
    const map = {
        face: 'Khuôn mặt',
        plate: 'Biển số',
        manual: 'Thủ công',
        'face-and-plate': 'Khuôn mặt + biển số',
        system: 'Hệ thống',
    }
    return map[value] || value
}

function methodClass(value) {
    if (value === 'manual') return 'danger'
    if (value === 'plate') return 'warn'
    if (value === 'face') return 'success'
    return ''
}

async function fetchSummary() {
    try {
        const { data } = await getAccessLogSummary()
        summary.value = { ...summary.value, ...data }
    } catch (error) {
        console.error('Access log summary error:', error)
    }
}

async function fetchGates() {
    try {
        const { data } = await getGates()
        gates.value = data || []
    } catch (error) {
        console.error('Gate list error:', error)
    }
}

async function fetchLogs() {
    isLoading.value = true
    try {
        const current = normalizeFilters(appliedFilters.value).normalized
        const params = {
            page: page.value,
            pageSize,
            query: current.query || undefined,
            direction: current.direction || undefined,
            gateId: current.gateId || undefined,
            resultStatus: current.status || undefined,
            dateFrom: current.dateFrom || undefined,
            dateTo: current.dateTo || undefined,
        }

        const { data } = await getAccessLogs(params)
        items.value = data.items || []
        total.value = data.total || 0
    } catch (error) {
        console.error('Access logs error:', error)
        items.value = []
        total.value = 0
    } finally {
        isLoading.value = false
    }
}

function commitFilters(nextFilters) {
    appliedFilters.value = { ...nextFilters }
    if (page.value === 1) {
        fetchLogs()
        return
    }
    page.value = 1
}

function applyFilters() {
    const { normalized, swapped } = normalizeFilters(draftFilters)
    Object.assign(draftFilters, normalized)
    filterNotice.value = swapped ? 'Khoảng ngày đã được đổi lại để đúng thứ tự từ ngày đến ngày.' : ''
    commitFilters(normalized)
}

function resetFilters() {
    const defaults = createDefaultFilters()
    Object.assign(draftFilters, defaults)
    filterNotice.value = ''
    commitFilters(defaults)
}

function setPage(nextPage) {
    if (nextPage < 1 || nextPage > totalPages.value) return
    page.value = nextPage
}

watch(page, fetchLogs)

onMounted(async () => {
    await Promise.all([fetchSummary(), fetchGates()])
    await fetchLogs()
})
</script>

<style scoped>
.aside-head,
.aside-metrics {
    display: grid;
    gap: 14px;
}

.aside-head {
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
}

.aside-label {
    color: rgba(215, 251, 255, 0.72);
    font-size: 0.76rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.aside-head strong {
    font-family: var(--font-heading);
    font-size: 1.8rem;
}

.aside-chip {
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

.aside-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #5de3c7;
}

.aside-metrics {
    margin-top: 12px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.aside-metric {
    padding: 16px 14px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.aside-metric span {
    color: rgba(215, 251, 255, 0.76);
    font-size: 0.74rem;
}

.aside-metric strong {
    display: block;
    margin-top: 8px;
    color: #fff;
    font-family: var(--font-heading);
    font-size: 1.14rem;
}

.filter-summary {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px;
}

.filter-card {
    display: grid;
    gap: 18px;
    padding: 18px;
    border-radius: 22px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.56);
}

.filter-grid {
    display: grid;
    grid-template-columns: repeat(12, minmax(0, 1fr));
    gap: 14px;
}

.access-filter-grid .filter-field-query {
    grid-column: span 6;
}

.access-filter-grid .filter-field-direction,
.access-filter-grid .filter-field-gate {
    grid-column: span 3;
}

.access-filter-grid .filter-field-status,
.access-filter-grid .filter-field-date {
    grid-column: span 4;
}

.filter-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.field-label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 700;
}

.filter-footer {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
}

.filter-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.filter-hint,
.filter-notice {
    font-size: 0.84rem;
}

.filter-hint {
    color: var(--text-muted);
}

.filter-notice {
    margin-top: 4px;
    color: var(--accent-primary);
    font-weight: 600;
}

.table-main {
    color: var(--text-primary);
    font-weight: 600;
    font-size: 0.9rem;
}

.table-sub {
    margin-top: 4px;
    color: var(--text-muted);
    font-size: 0.8rem;
}

.plate-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(236, 244, 246, 0.92);
    border: 1px solid rgba(24, 49, 77, 0.12);
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 0.84rem;
    font-weight: 700;
}

.note-cell {
    max-width: 220px;
    white-space: normal;
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }

    .filter-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .filter-grid .filter-field {
        grid-column: span 1;
    }
}

@media (max-width: 768px) {
    .filter-grid {
        grid-template-columns: 1fr;
    }

    .filter-summary {
        justify-content: flex-start;
    }

    .filter-actions {
        width: 100%;
    }

    .filter-actions .btn {
        flex: 1;
    }
}
</style>
