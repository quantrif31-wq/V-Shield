<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Registration links</span>
                <h1 class="page-title">Tạo và quản lý link đăng ký tự động để khách tự khai báo trước khi đến.</h1>
                <p class="page-subtitle">
                    Đây là lớp vận hành nhanh cho lễ tân hoặc nhân sự mời khách. Link có token riêng, thời hạn hết hạn
                    rõ ràng và được liên kết trực tiếp tới nhân sự host trong hệ thống.
                </p>
                <div class="hero-actions">
                    <button class="btn btn-primary" @click="showModal = true">Tạo link mới</button>
                    <router-link to="/pre-registrations" class="btn btn-secondary">Xem danh sách hẹn trước</router-link>
                </div>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Link đang hoạt động</span>
                        <strong>{{ activeLinks }}</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        Visitor self-registration
                    </span>
                </div>
                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Tổng link</span>
                        <strong>{{ links.length }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Đã dùng</span>
                        <strong>{{ usedLinks }}</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Hết hạn</span>
                        <strong>{{ expiredLinks }}</strong>
                    </div>
                </div>
            </div>
        </section>

        <section class="ops-panel">
            <div class="toolbar-shell">
                <div class="search-bar">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="query" type="text" placeholder="Tìm theo host hoặc token..." />
                </div>
            </div>

            <div v-if="isLoading" class="empty-card">Đang tải danh sách link đăng ký...</div>
            <div v-else-if="filteredLinks.length === 0" class="empty-card">Chưa có link đăng ký nào phù hợp.</div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Host</th>
                            <th>Token</th>
                            <th>Trạng thái</th>
                            <th>Tạo lúc</th>
                            <th>Hết hạn</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="link in filteredLinks" :key="link.linkId">
                            <td>{{ link.hostEmployeeName }}</td>
                            <td><span class="token-pill">{{ link.token }}</span></td>
                            <td>
                                <div class="chip-row">
                                    <span v-if="link.isUsed" class="soft-chip warn">Đã dùng</span>
                                    <span v-else-if="link.isExpired" class="soft-chip danger">Hết hạn</span>
                                    <span v-else class="soft-chip success">Còn hiệu lực</span>
                                </div>
                            </td>
                            <td>{{ formatDateTime(link.createdAt) }}</td>
                            <td>{{ formatDateTime(link.expiredAt) }}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" @click="copyLink(link.registrationUrl)">
                                    {{ copiedUrl === link.registrationUrl ? 'Đã copy' : 'Copy link' }}
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <transition name="modal">
            <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">Tạo link đăng ký tự động</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>

                    <div class="form-group">
                        <label>Nhân sự host</label>
                        <select v-model="form.hostEmployeeId" class="filter-select">
                            <option value="">Chọn nhân sự</option>
                            <option v-for="employee in employees" :key="employee.employeeId" :value="employee.employeeId">
                                {{ employee.fullName }} - {{ employee.departmentName || 'Chưa gán phòng ban' }}
                            </option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Thời hạn link (giờ)</label>
                        <select v-model="form.expiryHours" class="filter-select">
                            <option :value="12">12 giờ</option>
                            <option :value="24">24 giờ</option>
                            <option :value="48">48 giờ</option>
                            <option :value="72">72 giờ</option>
                        </select>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isCreating" @click="handleCreate">
                            {{ isCreating ? 'Đang tạo...' : 'Tạo link' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getLinks, createLink } from '../services/preRegistrationApi'
import { getAll as getAllEmployees } from '../services/employeeApi'

const isLoading = ref(true)
const isCreating = ref(false)
const links = ref([])
const employees = ref([])
const query = ref('')
const showModal = ref(false)
const copiedUrl = ref('')
const formError = ref('')

const form = reactive({
    hostEmployeeId: '',
    expiryHours: 24,
})

const filteredLinks = computed(() => {
    const keyword = query.value.trim().toLowerCase()
    if (!keyword) return links.value
    return links.value.filter((item) =>
        item.hostEmployeeName?.toLowerCase().includes(keyword) ||
        item.token?.toLowerCase().includes(keyword)
    )
})

const activeLinks = computed(() => links.value.filter((item) => !item.isExpired && !item.isUsed).length)
const usedLinks = computed(() => links.value.filter((item) => item.isUsed).length)
const expiredLinks = computed(() => links.value.filter((item) => item.isExpired).length)

const formatDateTime = (value) => {
    if (!value) return '--'
    return new Date(value).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
    })
}

const fetchData = async () => {
    isLoading.value = true
    try {
        const [linksRes, employeesRes] = await Promise.all([
            getLinks(),
            getAllEmployees(),
        ])
        links.value = linksRes.data || []
        employees.value = employeesRes.data || []
    } catch (error) {
        console.error('Registration links load error:', error)
        links.value = []
    } finally {
        isLoading.value = false
    }
}

const copyLink = async (url) => {
    try {
        await navigator.clipboard.writeText(url)
        copiedUrl.value = url
        setTimeout(() => {
            if (copiedUrl.value === url) copiedUrl.value = ''
        }, 1800)
    } catch (error) {
        console.error('Copy error:', error)
    }
}

const handleCreate = async () => {
    formError.value = ''
    if (!form.hostEmployeeId) {
        formError.value = 'Bạn cần chọn nhân sự host trước khi tạo link.'
        return
    }

    isCreating.value = true
    try {
        const { data } = await createLink({
            hostEmployeeId: Number(form.hostEmployeeId),
            expiryHours: Number(form.expiryHours),
        })
        await fetchData()
        await copyLink(data.registrationUrl)
        closeModal()
    } catch (error) {
        console.error('Create link error:', error)
        formError.value = error.response?.data?.message || 'Không thể tạo link đăng ký.'
    } finally {
        isCreating.value = false
    }
}

const closeModal = () => {
    showModal.value = false
    form.hostEmployeeId = ''
    form.expiryHours = 24
    formError.value = ''
}

onMounted(fetchData)
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

.token-pill {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 10px;
    background: rgba(236, 244, 246, 0.92);
    border: 1px solid rgba(24, 49, 77, 0.12);
    color: var(--text-primary);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
}

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }
}
</style>
