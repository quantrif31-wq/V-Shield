<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Exceptions</span>
                <h1 class="page-title">Rà soát các lượt mở cổng thủ công, lỗi nhận diện và trạng thái bất thường.</h1>
                <p class="page-subtitle">
                    Đây là màn hình dành cho các trường hợp cần đối soát đặc biệt: <code>IsBypass = true</code>, có
                    <code>Exception_Reason</code> hoặc log ra vào có trạng thái không thành công.
                </p>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Top lý do</span>
                        <strong>{{ topReasonLabel }}</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        Kiểm soát ngoại lệ
                    </span>
                </div>

                <div class="aside-summary">
                    <article v-for="reason in summaryByReason.slice(0, 3)" :key="reason.reasonCode" class="reason-row">
                        <strong>{{ reason.reasonCode }}</strong>
                        <span>{{ reason.count }} lượt</span>
                    </article>
                </div>
            </div>
        </section>

        <section class="ops-panel">
            <div class="panel-head">
                <div>
                    <span class="panel-kicker">Exception filters</span>
                    <h2 class="panel-title">Bộ lọc ngoại lệ</h2>
                    <p class="panel-copy">
                        Áp dụng khi cần đối soát theo lý do, khoảng ngày và từ khóa mà không bị refresh giữa chừng.
                    </p>
                </div>
                <div class="filter-summary">
                    <span class="soft-chip warn">{{ total }} ngoại lệ</span>
                    <span v-for="tag in appliedFilterTags" :key="tag" class="soft-chip">{{ tag }}</span>
                </div>
            </div>

            <div class="filter-card">
                <div class="filter-grid">
                    <label class="filter-field filter-field-search">
                        <span class="field-label">Từ khóa</span>
                        <div class="search-bar">
                            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8" />
                                <path d="M21 21l-4.35-4.35" />
                            </svg>
                            <input
                                v-model="draftFilters.query"
                                type="text"
                                placeholder="Tìm theo người, biển số, ghi chú..."
                                @keyup.enter="applyFilters"
                            />
                        </div>
                    </label>

                    <label class="filter-field">
                        <span class="field-label">Lý do ngoại lệ</span>
                        <select v-model="draftFilters.reasonId" class="filter-select">
                            <option value="">Tất cả lý do</option>
                            <option v-for="reason in reasons" :key="reason.reasonId" :value="String(reason.reasonId)">
                                {{ reason.reasonCode }} - {{ reason.description }}
                            </option>
                        </select>
                    </label>

                    <label class="filter-field">
                        <span class="field-label">Từ ngày</span>
                        <input v-model="draftFilters.dateFrom" type="date" class="filter-select" />
                    </label>

                    <label class="filter-field">
                        <span class="field-label">Đến ngày</span>
                        <input v-model="draftFilters.dateTo" type="date" class="filter-select" />
                    </label>
                </div>

                <div class="filter-footer">
                    <div>
                        <p class="filter-hint">Nếu nhập ngày kết thúc sớm hơn ngày bắt đầu, hệ thống sẽ tự hoán đổi.</p>
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

            <div v-if="isLoading" class="empty-card">Đang tải danh sách ngoại lệ...</div>
            <div v-else-if="items.length === 0" class="empty-card">
                {{ hasActiveFilters ? 'Không có ngoại lệ nào khớp với bộ lọc đã áp dụng.' : 'Chưa có ngoại lệ nào để hiển thị.' }}
            </div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Thời gian</th>
                            <th>Đối tượng</th>
                            <th>Cổng</th>
                            <th>Biển số</th>
                            <th>Lý do</th>
                            <th>Trạng thái</th>
                            <th>Ghi chú</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="item in items" :key="item.logId">
                            <td>{{ formatDateTime(item.timestamp) }}</td>
                            <td>
                                <div class="table-main">{{ item.actorName }}</div>
                                <div class="table-sub">{{ item.cameraName || 'Không có camera' }}</div>
                            </td>
                            <td>{{ item.gateName || 'Chưa gán cổng' }}</td>
                            <td>
                                <span v-if="item.capturedLicensePlate" class="plate-pill">{{ item.capturedLicensePlate }}</span>
                                <span v-else class="table-sub">Không ghi nhận</span>
                            </td>
                            <td>
                                <div class="chip-row">
                                    <span v-if="item.exceptionReasonCode" class="soft-chip warn">{{ item.exceptionReasonCode }}</span>
                                    <span v-else class="soft-chip warn">UNCLASSIFIED</span>
                                </div>
                                <div class="table-sub">{{ item.exceptionReasonDescription || 'Chưa có mô tả' }}</div>
                            </td>
                            <td>
                                <div class="chip-row">
                                    <span v-if="item.isBypass" class="soft-chip danger">BYPASS</span>
                                    <span v-if="item.resultStatus" class="soft-chip">{{ item.resultStatus }}</span>
                                </div>
                            </td>
                            <td class="note-cell">{{ item.note || '—' }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="total > 0" class="pagination">
                <div class="pagination-info">Hiển thị {{ items.length }} / {{ total }} ngoại lệ</div>
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
import { getExceptions } from '../services/accessLogApi'
import { getExceptionReasons } from '../services/exceptionReasonApi'

const pageSize = 12

const createDefaultFilters = () => ({
    query: '',
    reasonId: '',
    dateFrom: '',
    dateTo: '',
})

const isLoading = ref(true)
const items = ref([])
const total = ref(0)
const page = ref(1)
const reasons = ref([])
const summaryByReason = ref([])
const filterNotice = ref('')
const draftFilters = reactive(createDefaultFilters())
const appliedFilters = ref(createDefaultFilters())

const normalizeFilters = (source) => {
    const normalized = {
        query: source.query?.trim() || '',
        reasonId: source.reasonId || '',
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

const topReasonLabel = computed(() => {
    const top = summaryByReason.value[0]
    return top ? `${top.reasonCode} - ${top.count} lượt` : 'Chưa có ngoại lệ'
})

const appliedFilterTags = computed(() => {
    const current = normalizeFilters(appliedFilters.value).normalized
    const tags = []

    if (current.query) tags.push(`Từ khóa: ${current.query}`)

    if (current.reasonId) {
        const reason = reasons.value.find((item) => String(item.reasonId) === current.reasonId)
        tags.push(`Lý do: ${reason ? reason.reasonCode : current.reasonId}`)
    }

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

async function fetchReasons() {
    try {
        const { data } = await getExceptionReasons()
        reasons.value = data || []
    } catch (error) {
        console.error('Exception reasons error:', error)
    }
}

async function fetchItems() {
    isLoading.value = true
    try {
        const current = normalizeFilters(appliedFilters.value).normalized
        const params = {
            page: page.value,
            pageSize,
            query: current.query || undefined,
            reasonId: current.reasonId || undefined,
            dateFrom: current.dateFrom || undefined,
            dateTo: current.dateTo || undefined,
        }

        const { data } = await getExceptions(params)
        items.value = data.items || []
        total.value = data.total || 0
        summaryByReason.value = data.summaryByReason || []
    } catch (error) {
        console.error('Exceptions load error:', error)
        items.value = []
        total.value = 0
        summaryByReason.value = []
    } finally {
        isLoading.value = false
    }
}

function commitFilters(nextFilters) {
    appliedFilters.value = { ...nextFilters }
    if (page.value === 1) {
        fetchItems()
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

watch(page, fetchItems)

onMounted(async () => {
    await fetchReasons()
    await fetchItems()
})
</script>

<style scoped>
.aside-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: start;
    gap: 14px;
}

.aside-label {
    color: rgba(215, 251, 255, 0.72);
    font-size: 0.76rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.aside-head strong {
    font-family: var(--font-heading);
    font-size: 1.15rem;
    line-height: 1.3;
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

.aside-summary {
    margin-top: 18px;
    display: grid;
    gap: 10px;
}

.reason-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 12px 14px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.reason-row strong {
    color: #fff;
    font-size: 0.88rem;
}

.reason-row span {
    color: rgba(215, 251, 255, 0.76);
    font-size: 0.8rem;
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
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
}

.filter-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.filter-field-search {
    grid-column: span 2;
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
    max-width: 240px;
    color: var(--text-secondary);
}

@media (max-width: 1180px) {
    .filter-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .filter-field-search {
        grid-column: span 2;
    }
}

@media (max-width: 768px) {
    .filter-grid {
        grid-template-columns: 1fr;
    }

    .filter-field-search {
        grid-column: span 1;
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
