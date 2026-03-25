<template>
    <div class="page-container ops-page animate-in">
        <section class="hero-banner">
            <div class="hero-panel">
                <span class="hero-kicker">Dynamic QR</span>
                <h1 class="page-title">Tạo QR động cho nhân viên để dùng tại luồng thông hành.</h1>
                <p class="page-subtitle">
                    Mã QR được sinh theo time-step từ backend, tự làm mới khi gần hết hạn và chỉ dùng payload thật do API trả
                    về để render.
                </p>
                <div class="hero-actions">
                    <button class="btn btn-primary" :disabled="loading" @click="startGenerate">
                        {{ loading ? 'Đang tạo...' : 'Tạo QR động' }}
                    </button>
                    <button class="btn btn-secondary" :disabled="!isRealtimeActive" @click="stopAutoRefresh">
                        Dừng realtime
                    </button>
                </div>
            </div>

            <div class="hero-aside">
                <div class="aside-head">
                    <div>
                        <span class="aside-label">Trạng thái QR</span>
                        <strong>{{ qrData ? 'Đang hoạt động' : 'Chưa sinh mã' }}</strong>
                    </div>
                    <span class="aside-chip">
                        <span class="aside-dot"></span>
                        {{ isRealtimeActive ? 'Realtime bật' : 'Realtime tắt' }}
                    </span>
                </div>

                <div class="aside-metrics">
                    <div class="aside-metric">
                        <span>Chu kỳ</span>
                        <strong>{{ qrData?.timeStepSeconds || 0 }}s</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Còn lại</span>
                        <strong>{{ remainingSeconds }}s</strong>
                    </div>
                    <div class="aside-metric">
                        <span>Nhân viên</span>
                        <strong>{{ qrData?.employeeId || '—' }}</strong>
                    </div>
                </div>
            </div>
        </section>

        <section class="ops-grid two qr-layout">
            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Generate form</span>
                        <h2 class="panel-title">Sinh QR theo Employee ID</h2>
                        <p class="panel-copy">
                            Controller mới chỉ cần <code>employeeId</code>. Backend sẽ tự sinh secret nếu nhân viên chưa có cấu
                            hình QR động.
                        </p>
                    </div>
                </div>

                <div class="form-stack">
                    <label class="form-field">
                        <span class="field-label">Employee ID</span>
                        <input
                            v-model="employeeId"
                            type="number"
                            min="1"
                            class="filter-select"
                            placeholder="Nhập Employee ID"
                            @keyup.enter="startGenerate"
                            :readonly="authState.user?.role === 'Staff' && !!employeeId"
                        />
                    </label>
                </div>

                <div v-if="errorMessage" class="empty-card error-card">{{ errorMessage }}</div>
                <div v-if="successMessage" class="empty-card success-card">{{ successMessage }}</div>

                <div class="surface-list helper-list">
                    <article class="surface-item">
                        <div class="inline-stat">
                            <strong>Payload chuẩn</strong>
                            <span>Mẫu trả về từ backend: <code>EMP:&lt;id&gt;|TS:&lt;counter&gt;|OTP:&lt;code&gt;</code></span>
                        </div>
                    </article>
                    <article class="surface-item">
                        <div class="inline-stat">
                            <strong>Thời gian hiển thị</strong>
                            <span>Frontend tự đếm ngược và gọi lại API khi QR sắp hết hạn.</span>
                        </div>
                    </article>
                </div>
            </article>

            <article class="ops-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Generated output</span>
                        <h2 class="panel-title">QR động hiện tại</h2>
                    </div>
                    <span class="soft-chip" :class="qrData ? 'success' : 'warn'">
                        {{ qrData ? 'Có dữ liệu' : 'Chưa tạo' }}
                    </span>
                </div>

                <div v-if="qrData" class="qr-content">
                    <div class="info-grid">
                        <div class="info-card">
                            <span>Nhân viên</span>
                            <strong>{{ qrData.employeeName }}</strong>
                            <small>ID {{ qrData.employeeId }}</small>
                        </div>
                        <div class="info-card countdown-card">
                            <span>Còn lại</span>
                            <strong>{{ remainingSeconds }}s</strong>
                            <div class="countdown-bar">
                                <span :style="{ width: `${countdownPercent}%` }"></span>
                            </div>
                        </div>
                        <div class="info-card">
                            <span>Generated</span>
                            <strong>{{ formatDate(qrData.generatedAtUtc) }}</strong>
                            <small>Local time</small>
                        </div>
                        <div class="info-card">
                            <span>Expires</span>
                            <strong>{{ formatDate(qrData.expiresAtUtc) }}</strong>
                            <small>Local time</small>
                        </div>
                    </div>

                    <div class="qr-box">
                        <img v-if="qrImage" :src="qrImage" alt="Dynamic QR" />
                    </div>

                    <label class="form-field">
                        <span class="field-label">QR Payload</span>
                        <textarea rows="4" class="payload-box" readonly :value="qrData.qrPayload"></textarea>
                    </label>
                </div>

                <div v-else class="empty-card">
                    Chưa có mã QR nào được tạo. Nhập <code>Employee ID</code> và bấm <strong>Tạo QR động</strong> để bắt đầu.
                </div>
            </article>
        </section>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, onMounted } from 'vue'
import QRCode from 'qrcode'
import { generateDynamicQr } from '../services/dynamicQrApi'
import { authState } from '../stores/auth'
import { getAll as getAllEmployees } from '../services/employeeApi'

const employeeId = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const qrData = ref(null)
const qrImage = ref('')
const remainingSeconds = ref(0)
const isRealtimeActive = ref(false)

let intervalId = null
let currentEmployeeId = null

const countdownPercent = computed(() => {
    if (!qrData.value?.timeStepSeconds) return 0
    return Math.max(0, Math.min(100, Math.round((remainingSeconds.value / qrData.value.timeStepSeconds) * 100)))
})

function clearMessages() {
    errorMessage.value = ''
    successMessage.value = ''
}

function stopAutoRefresh() {
    if (intervalId) {
        clearInterval(intervalId)
        intervalId = null
    }
    isRealtimeActive.value = false
}

async function renderQr(payload) {
    qrImage.value = await QRCode.toDataURL(payload, {
        width: 300,
        margin: 2,
    })
}

async function fetchQr(employeeIdValue) {
    loading.value = true
    clearMessages()

    try {
        const result = await generateDynamicQr(employeeIdValue)

        if (!result.success || !result.data?.qrPayload) {
            throw new Error(result.message || 'Tạo QR thất bại.')
        }

        qrData.value = result.data
        remainingSeconds.value = result.data.remainingSeconds ?? 0
        await renderQr(result.data.qrPayload)
        successMessage.value = result.message || 'Tạo QR động thành công.'
        return true
    } catch (error) {
        qrData.value = null
        qrImage.value = ''
        errorMessage.value = error?.response?.data?.message || error?.message || 'Không thể tạo QR động.'
        return false
    } finally {
        loading.value = false
    }
}

async function startGenerate() {
    if (!employeeId.value) {
        errorMessage.value = 'Vui lòng nhập Employee ID.'
        return
    }

    currentEmployeeId = Number(employeeId.value)

    stopAutoRefresh()
    const ok = await fetchQr(currentEmployeeId)
    if (!ok) return

    isRealtimeActive.value = true
    intervalId = setInterval(async () => {
        if (remainingSeconds.value > 1) {
            remainingSeconds.value -= 1
            return
        }

        if (currentEmployeeId) {
            await fetchQr(currentEmployeeId)
        }
    }, 1000)
}

function formatDate(dateValue) {
    if (!dateValue) return ''
    return new Date(dateValue).toLocaleString('vi-VN')
}

onMounted(async () => {
    if (authState.user?.role === 'Staff') {
        const identifier = (authState.user?.fullName || authState.user?.username || '').trim().toLowerCase()
        if (!identifier) return

        try {
            const res = await getAllEmployees()
            const employees = res.data || []
            const matched = employees.find(emp => 
                (emp.fullName || '').trim().toLowerCase() === identifier
            )
            
            if (matched) {
                employeeId.value = matched.employeeId
            } else {
                errorMessage.value = `Không tìm thấy hồ sơ nhân sự khớp với tài khoản (${authState.user?.fullName || authState.user?.username}). Vui lòng kiểm tra lại Danh sách Nhân viên.`
            }
        } catch (err) {
            console.error('Lỗi tự động lấy Employee ID:', err)
        }
    }
})

onBeforeUnmount(() => {
    stopAutoRefresh()
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
    font-size: 1.4rem;
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

.qr-layout {
    align-items: start;
}

.form-stack {
    display: grid;
    gap: 16px;
}

.form-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.field-label {
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 700;
}

.helper-list code,
.panel-copy code,
.empty-card code {
    padding: 2px 6px;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.06);
    font-family: 'JetBrains Mono', monospace;
}

.success-card {
    border-style: solid;
    border-color: rgba(20, 134, 109, 0.18);
    color: var(--accent-success);
}

.error-card {
    border-style: solid;
    border-color: rgba(195, 81, 70, 0.18);
    color: var(--accent-danger);
}

.qr-content {
    display: grid;
    gap: 18px;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.info-card {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 16px;
    border-radius: 18px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.72);
}

.info-card span,
.info-card small {
    color: var(--text-muted);
}

.info-card strong {
    color: var(--text-primary);
    font-family: var(--font-heading);
    font-size: 1rem;
    line-height: 1.25;
}

.countdown-card strong {
    font-size: 1.5rem;
}

.countdown-bar {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(24, 49, 77, 0.08);
    overflow: hidden;
}

.countdown-bar span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--accent-warning), var(--accent-primary));
}

.qr-box {
    display: flex;
    justify-content: center;
    padding: 18px;
    border-radius: 24px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(255, 255, 255, 0.94);
}

.qr-box img {
    width: min(100%, 320px);
    border-radius: 20px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: #fff;
    padding: 14px;
}

.payload-box {
    width: 100%;
    min-height: 110px;
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(24, 49, 77, 0.1);
    background: var(--bg-input);
    color: var(--text-primary);
    resize: vertical;
}

@media (max-width: 1180px) {
    .aside-metrics {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .info-grid {
        grid-template-columns: 1fr;
    }
}
</style>
