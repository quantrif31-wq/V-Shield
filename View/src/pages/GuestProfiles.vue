<template>
    <div class="page-container ops-page animate-in">
        <div class="page-header-bar">
            <div>
                <span class="panel-kicker">Guest profiles</span>
                <h1 class="page-title">Hồ sơ khách</h1>
            </div>
            <div class="header-actions">
                <button class="btn btn-primary" @click="openModal()">Thêm hồ sơ khách</button>
                <router-link to="/registration-links" class="btn btn-secondary">Mở link đăng ký</router-link>
            </div>
        </div>

        <section class="ops-panel">
            <div class="toolbar-shell">
                <div class="search-bar">
                    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8" />
                        <path d="M21 21l-4.35-4.35" />
                    </svg>
                    <input v-model="query" type="text" placeholder="Tìm tên khách, SĐT hoặc biển số..." />
                </div>
            </div>

            <div v-if="isLoading" class="empty-card">Đang tải hồ sơ khách...</div>
            <div v-else-if="profiles.length === 0" class="empty-card">Chưa có hồ sơ khách nào trong cơ sở dữ liệu.</div>
            <div v-else class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Khách</th>
                            <th>Liên hệ</th>
                            <th>Biển số mặc định</th>
                            <th>Lịch sử hẹn trước</th>
                            <th>Lần tới</th>
                            <th>Thao tác</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="profile in paginatedProfiles" :key="profile.guestId">
                            <td>
                                <div class="table-main">{{ profile.fullName }}</div>
                                <div class="chip-row">
                                    <span v-if="profile.faceImageUrl" class="soft-chip success">Có ảnh mặt</span>
                                </div>
                            </td>
                            <td>{{ profile.phone || '—' }}</td>
                            <td>
                                <span v-if="profile.defaultLicensePlate" class="plate-pill">{{ profile.defaultLicensePlate }}</span>
                                <span v-else class="table-sub">Chưa lưu</span>
                            </td>
                            <td>{{ profile.preRegistrationCount }} lượt</td>
                            <td>{{ profile.nextExpectedVisit ? formatDateTime(profile.nextExpectedVisit) : 'Chưa có lịch' }}</td>
                            <td>
                                <div class="panel-actions">
                                    <button class="btn btn-secondary btn-sm" @click="openModal(profile)">Sửa</button>
                                    <button class="btn btn-danger btn-sm" @click="handleDelete(profile)">Xóa</button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div v-if="!isLoading && profiles.length > 0" class="pagination-bar">
                <span>Hiển thị {{ gPagStart }}–{{ gPagEnd }} / {{ profiles.length }}</span>
                <div class="page-buttons">
                    <button class="page-btn" :disabled="gCurrentPage <= 1" @click="gCurrentPage--">‹</button>
                    <button v-for="p in gTotalPages" :key="p" class="page-btn" :class="{ active: p === gCurrentPage }" @click="gCurrentPage = p">{{ p }}</button>
                    <button class="page-btn" :disabled="gCurrentPage >= gTotalPages" @click="gCurrentPage++">›</button>
                </div>
            </div>
        </section>

        <transition name="modal">
            <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3 class="modal-title">{{ editingId ? 'Cập nhật hồ sơ khách' : 'Thêm hồ sơ khách' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Họ tên</label>
                            <input v-model="form.fullName" type="text" placeholder="Ví dụ: Nguyễn Văn B" />
                        </div>
                        <div class="form-group">
                            <label>Số điện thoại</label>
                            <input v-model="form.phone" type="text" placeholder="09xxxxxxxx" />
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Biển số mặc định</label>
                            <input v-model="form.defaultLicensePlate" type="text" placeholder="51A-123.45" />
                        </div>
                        <div class="form-group">
                            <label>Ảnh khuôn mặt URL</label>
                            <input v-model="form.faceImageUrl" type="text" placeholder="/uploads/..." />
                        </div>
                    </div>

                    <div v-if="formError" class="empty-card error-card">{{ formError }}</div>

                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">Hủy</button>
                        <button class="btn btn-primary" :disabled="isSaving" @click="handleSubmit">
                            {{ isSaving ? 'Đang lưu...' : editingId ? 'Lưu thay đổi' : 'Tạo hồ sơ' }}
                        </button>
                    </div>
                </div>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
    createGuestProfile,
    deleteGuestProfile,
    getGuestProfiles,
    updateGuestProfile,
} from '../services/guestProfileApi'

const route = useRoute()
const isLoading = ref(true)
const isSaving = ref(false)
const profiles = ref([])
const total = ref(0)
const query = ref('')
const showModal = ref(false)
const editingId = ref(null)
const formError = ref('')

const form = reactive({
    fullName: '',
    phone: '',
    defaultLicensePlate: '',
    faceImageUrl: '',
})

const upcomingCount = computed(() => profiles.value.filter((item) => item.nextExpectedVisit).length)
const withPlateCount = computed(() => profiles.value.filter((item) => item.defaultLicensePlate).length)
const withFaceCount = computed(() => profiles.value.filter((item) => item.faceImageUrl).length)

const gCurrentPage = ref(1)
const gPageSize = 10
const gTotalPages = computed(() => Math.max(1, Math.ceil(profiles.value.length / gPageSize)))
const paginatedProfiles = computed(() => {
    const start = (gCurrentPage.value - 1) * gPageSize
    return profiles.value.slice(start, start + gPageSize)
})
const gPagStart = computed(() => profiles.value.length === 0 ? 0 : (gCurrentPage.value - 1) * gPageSize + 1)
const gPagEnd = computed(() => Math.min(gCurrentPage.value * gPageSize, profiles.value.length))

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

const fetchProfiles = async () => {
    isLoading.value = true
    gCurrentPage.value = 1
    try {
        const { data } = await getGuestProfiles({ query: query.value || undefined, page: 1, pageSize: 50 })
        profiles.value = data.items || []
        total.value = data.total || 0
    } catch (error) {
        console.error('Guest profiles error:', error)
        profiles.value = []
        total.value = 0
    } finally {
        isLoading.value = false
    }
}

const openModal = (profile = null) => {
    editingId.value = profile?.guestId || null
    form.fullName = profile?.fullName || ''
    form.phone = profile?.phone || ''
    form.defaultLicensePlate = profile?.defaultLicensePlate || ''
    form.faceImageUrl = profile?.faceImageUrl || ''
    formError.value = ''
    showModal.value = true
}

const closeModal = () => {
    showModal.value = false
    editingId.value = null
    form.fullName = ''
    form.phone = ''
    form.defaultLicensePlate = ''
    form.faceImageUrl = ''
    formError.value = ''
}

const handleSubmit = async () => {
    formError.value = ''
    if (!form.fullName.trim()) {
        formError.value = 'Họ tên khách là bắt buộc.'
        return
    }

    isSaving.value = true
    try {
        const payload = {
            fullName: form.fullName.trim(),
            phone: form.phone || null,
            defaultLicensePlate: form.defaultLicensePlate || null,
            faceImageUrl: form.faceImageUrl || null,
        }

        if (editingId.value) {
            await updateGuestProfile(editingId.value, payload)
        } else {
            await createGuestProfile(payload)
        }

        await fetchProfiles()
        closeModal()
    } catch (error) {
        console.error('Guest profile save error:', error)
        formError.value = error.response?.data?.message || 'Không thể lưu hồ sơ khách.'
    } finally {
        isSaving.value = false
    }
}

const handleDelete = async (profile) => {
    const confirmed = window.confirm(`Xóa hồ sơ khách "${profile.fullName}"?`)
    if (!confirmed) return

    try {
        await deleteGuestProfile(profile.guestId)
        await fetchProfiles()
    } catch (error) {
        console.error('Guest profile delete error:', error)
        window.alert(error.response?.data?.message || 'Không thể xóa hồ sơ khách này.')
    }
}

let queryTimer = null
watch(query, () => {
    clearTimeout(queryTimer)
    queryTimer = setTimeout(fetchProfiles, 260)
})

watch(
    () => route.query.search,
    (value) => {
        if (typeof value === 'string') {
            query.value = value
        }
    },
    { immediate: true }
)

onMounted(fetchProfiles)
</script>

<style scoped>
.table-main {
    color: var(--text-primary);
    font-weight: 600;
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

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

@media (max-width: 1180px) {
    }
</style>
