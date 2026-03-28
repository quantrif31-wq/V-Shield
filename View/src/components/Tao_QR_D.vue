<template>
    <div class="page-container qr-page animate-in">


        <section class="qr-layout">
            <article class="ops-panel command-panel">
                <div class="panel-head">
                    <div>
                        <span class="panel-kicker">Điều phối phiên</span>
                        <h2 class="panel-title">{{ commandTitle }}</h2>
                        <p class="panel-copy">{{ commandCopy }}</p>
                    </div>

                    <span class="mode-pill" :class="isAdmin ? 'admin' : 'personal'">
                        {{ isAdmin ? 'Admin' : 'Cá nhân' }}
                    </span>
                </div>



                <div class="form-stack">
                    <label v-if="isAdmin" class="form-field">
                        <span class="field-label">Employee ID</span>
                        <div class="input-shell">
                            <input
                                v-model="employeeId"
                                type="number"
                                min="1"
                                class="filter-select qr-input"
                                placeholder="Nhập Employee ID cần cấp QR"
                                @keyup.enter="issueRealtime"
                            />
                            <small class="input-hint">
                                Backend sẽ tự tạo cấu hình QR động nếu nhân sự này chưa từng được phát mã trước đó.
                            </small>
                        </div>
                    </label>

                    <div v-else class="account-card">
                        <span class="metric-eyebrow">Chế độ cá nhân</span>
                        <strong>{{ heroEmployeeName }}</strong>
                        <p>
                            Trang này luôn phát QR cho nhân sự mang ID <b>{{ employeeId || '-----' }}</b>.
                            Chỉ cần giữ màn hình mở khi chuẩn bị quét tại cổng.
                        </p>
                    </div>

                    <div class="action-row">
                        <button class="btn btn-primary" :disabled="loading" @click="issueRealtime">
                            {{ primaryActionLabel }}
                        </button>

                        <button class="btn btn-secondary" :disabled="loading || !canToggleRealtime" @click="toggleRealtime">
                            {{ realtimeToggleLabel }}
                        </button>

                        <button class="btn btn-secondary subtle" :disabled="loading || !canRefreshManually" @click="refreshOnce">
                            Làm mới ngay
                        </button>
                    </div>
                </div>

                <div v-if="errorMessage || successMessage || copyMessage" class="feedback-stack" aria-live="polite">
                    <div v-if="errorMessage" class="feedback-card danger">{{ errorMessage }}</div>
                    <div v-if="successMessage" class="feedback-card success">{{ successMessage }}</div>
                    <div v-if="copyMessage" class="feedback-card info">{{ copyMessage }}</div>
                </div>


            </article>

            <div class="preview-stack">
                <article class="ops-panel live-panel">
                    <div class="panel-head">
                        <div>
                            <span class="panel-kicker">Sân khấu quét</span>
                            <h2 class="panel-title">QR đang phát tại chỗ</h2>
                            <p class="panel-copy">
                                Ưu tiên hiển thị lớn, rõ, và đọc nhanh. Mọi dữ liệu thời gian đều bám theo phản hồi mới nhất từ backend.
                            </p>
                        </div>

                        <span class="soft-chip" :class="readinessChipClass">{{ readinessLabel }}</span>
                    </div>

                    <div v-if="qrData" class="live-layout">
                        <div class="qr-stage">
                            <div class="stage-head">
                                <div>
                                    <span class="metric-eyebrow inverse">Mã hiện tại</span>
                                    <h3>{{ qrData.employeeName }}</h3>
                                </div>

                                <span class="stage-pill" :class="readinessChipClass">{{ readinessLabel }}</span>
                            </div>

                            <div class="qr-frame">
                                <div class="qr-frame-glow"></div>
                                <img v-if="qrImage" :src="qrImage" alt="Dynamic QR" />
                            </div>

                            <div class="stage-foot">
                                <div class="stage-stat">
                                    <span>Payload</span>
                                    <strong>{{ compactPayload }}</strong>
                                </div>

                                <button class="ghost-copy" :disabled="!canCopyPayload" @click="copyPayload">
                                    Sao chép payload
                                </button>
                            </div>
                        </div>

                        <div class="live-sidebar">
                            <div class="countdown-card" :class="countdownToneClass">
                                <span class="metric-eyebrow">Còn hiệu lực</span>
                                <strong>{{ remainingSeconds }}s</strong>
                                <p>{{ countdownMessage }}</p>

                                <div class="countdown-track">
                                    <span :style="{ width: `${countdownPercent}%` }"></span>
                                </div>
                            </div>

                            <div class="info-grid">
                                <div class="info-card">
                                    <span>Nhân sự</span>
                                    <strong>{{ qrData.employeeName }}</strong>
                                    <small>ID {{ qrData.employeeId }}</small>
                                </div>

                                <div class="info-card">
                                    <span>Chu kỳ</span>
                                    <strong>{{ qrData.timeStepSeconds }} giây</strong>
                                    <small>{{ isRealtimeActive ? 'Đang phát liên tục.' : 'Tạm dừng tự làm mới.' }}</small>
                                </div>

                                <div class="info-card">
                                    <span>Tạo lúc</span>
                                    <strong>{{ formatTimeOnly(qrData.generatedAtUtc) }}</strong>
                                    <small>{{ formatDate(qrData.generatedAtUtc) }}</small>
                                </div>

                                <div class="info-card">
                                    <span>Hết hạn lúc</span>
                                    <strong>{{ formatTimeOnly(qrData.expiresAtUtc) }}</strong>
                                    <small>{{ formatDate(qrData.expiresAtUtc) }}</small>
                                </div>
                            </div>

                            <div class="payload-card">
                                <div class="payload-head">
                                    <div>
                                        <span class="metric-eyebrow">QR payload</span>
                                        <p>Chuỗi gốc được dùng để render thành mã QR và phục vụ đối chiếu khi cần.</p>
                                    </div>

                                    <button class="ghost-copy secondary" :disabled="!canCopyPayload" @click="copyPayload">
                                        Copy
                                    </button>
                                </div>

                                <textarea rows="4" class="payload-box" readonly :value="qrData.qrPayload"></textarea>
                            </div>
                        </div>
                    </div>

                    <div v-else class="empty-shell">
                        <div class="empty-orb"></div>
                        <h3>Chưa có phiên QR nào đang phát</h3>
                        <p>
                            {{ isAdmin ? 'Nhập đúng Employee ID rồi phát realtime để cấp mã cho nhân sự tại cổng.' : 'Phiên sẽ tự khởi tạo ngay khi tài khoản có Employee ID hợp lệ và bạn phát mã lần đầu.' }}
                        </p>

                        <div class="empty-steps">
                            <span>1. Chọn nhân sự</span>
                            <span>2. Phát QR realtime</span>
                            <span>3. Xuất trình tại cổng</span>
                        </div>
                    </div>
                </article>


            </div>
        </section>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, watch } from 'vue'
import { ref } from 'vue'
import QRCode from 'qrcode'
import { generateDynamicQr } from '../services/dynamicQrApi'
import { authState } from '../stores/auth'

const DEFAULT_TIME_STEP_SECONDS = 30

const employeeId = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const copyMessage = ref('')
const qrData = ref(null)
const qrImage = ref('')
const remainingSeconds = ref(0)
const isRealtimeActive = ref(false)

const isAdmin = computed(() => authState.user?.role === 'Admin')
const accountEmployeeId = computed(() => authState.user?.employeeId?.toString() || '')
const userDisplayName = computed(() => authState.user?.fullName || authState.user?.username || 'Nhân sự')

let tickerTimeoutId = null
let copyTimeoutId = null
let currentEmployeeId = null
let refreshInFlight = false
let autoStartedForStaff = false

const activeTimeStep = computed(() => qrData.value?.timeStepSeconds || DEFAULT_TIME_STEP_SECONDS)

const pageTitle = computed(() => {
    return isAdmin.value ? 'Điều phối QR động theo từng nhân sự' : 'QR thông hành cá nhân'
})

const pageDescription = computed(() => {
    return isAdmin.value
        ? 'Phát đúng phiên QR realtime cho từng nhân sự, theo dõi thời gian sống của mã và giữ trạng thái luôn sẵn sàng cho camera tại cổng.'
        : 'Mã QR của bạn được làm mới theo chu kỳ ngắn. Chỉ cần giữ màn hình mở để hệ thống tự đồng bộ sang phiên kế tiếp đúng lúc.'
})

const modeLabel = computed(() => {
    return isAdmin.value ? 'Admin mode' : 'Self mode'
})

const commandTitle = computed(() => {
    return isAdmin.value ? 'Phát mã cho đúng nhân sự cần qua cổng' : 'Quản lý phiên QR của bạn'
})

const commandCopy = computed(() => {
    return isAdmin.value
        ? 'Nhập Employee ID rồi phát phiên mới. Frontend sẽ lấy payload hợp lệ từ backend và tự duy trì mã theo chu kỳ.'
        : 'Phiên QR bám theo tài khoản đăng nhập hiện tại. Bạn có thể phát lại, tạm dừng hoặc đồng bộ lại bất cứ lúc nào.'
})

const countdownPercent = computed(() => {
    if (!activeTimeStep.value) return 0
    return Math.max(0, Math.min(100, Math.round((remainingSeconds.value / activeTimeStep.value) * 100)))
})

const countdownToneClass = computed(() => {
    if (!qrData.value) return 'muted'
    if (remainingSeconds.value <= 0) return 'urgent'
    if (remainingSeconds.value <= 5) return 'urgent'
    if (remainingSeconds.value <= 10) return 'warning'
    return 'stable'
})

const qrStateLabel = computed(() => {
    if (loading.value) return 'Đang phát QR'
    if (errorMessage.value && !qrData.value) return 'Chưa đồng bộ được'
    if (!qrData.value) return 'Chưa có phiên'
    if (isRealtimeActive.value) return remainingSeconds.value <= 5 ? 'Sắp đổi mã' : 'Đang realtime'
    if (remainingSeconds.value > 0) return 'Đã tạm dừng'
    return 'Đã hết hạn'
})

const qrStateCopy = computed(() => {
    if (loading.value) return 'Frontend đang lấy payload mới từ backend.'
    if (errorMessage.value && !qrData.value) return 'Kiểm tra lại Employee ID hoặc kết nối API rồi phát lại.'
    if (!qrData.value) return 'Bấm phát QR để khởi tạo phiên đầu tiên.'
    if (isRealtimeActive.value && remainingSeconds.value <= 5) return 'Phiên mới sẽ được phát ngay khi bộ đếm kết thúc.'
    if (isRealtimeActive.value) return 'Mã hiện tại vẫn hợp lệ và sẽ tự đổi khi hết chu kỳ.'
    if (remainingSeconds.value > 0) return 'Realtime đang dừng, mã hiện tại sẽ chỉ sống tới khi bộ đếm về 0.'
    return 'Mã hiện tại đã hết hiệu lực. Hãy phát lại hoặc tiếp tục realtime.'
})

const heroEmployeeName = computed(() => {
    return qrData.value?.employeeName || userDisplayName.value
})

const heroEmployeeId = computed(() => {
    return qrData.value?.employeeId || employeeId.value || '-----'
})

const compactPayload = computed(() => {
    const payload = qrData.value?.qrPayload
    if (!payload) return 'Chưa có payload'
    return payload.length <= 28 ? payload : `${payload.slice(0, 28)}...`
})

const statusChipText = computed(() => {
    if (loading.value) return 'Đang đồng bộ'
    if (!qrData.value) return 'Chưa phát mã'
    if (isRealtimeActive.value) return 'Realtime đang chạy'
    if (remainingSeconds.value > 0) return 'Realtime tạm dừng'
    return 'Phiên đã hết hạn'
})

const statusChipClass = computed(() => {
    if (loading.value) return 'warn'
    if (!qrData.value) return 'warn'
    if (isRealtimeActive.value && remainingSeconds.value > 5) return 'success'
    if (remainingSeconds.value > 0) return 'warn'
    return 'danger'
})

const readinessLabel = computed(() => {
    if (!qrData.value) return 'Chưa sẵn sàng'
    if (remainingSeconds.value <= 0) return 'Mã đã hết hạn'
    if (remainingSeconds.value <= 5) return 'Sắp đổi mã'
    return 'Quét ngay'
})

const readinessChipClass = computed(() => {
    if (!qrData.value) return 'warn'
    if (remainingSeconds.value <= 5) return 'warn'
    return 'success'
})

const countdownMessage = computed(() => {
    if (!qrData.value) return 'Phát phiên mới để bắt đầu xuất trình tại cổng.'
    if (!isRealtimeActive.value && remainingSeconds.value > 0) return 'Realtime đang dừng, phiên này sẽ không tự được gia hạn thêm.'
    if (!isRealtimeActive.value) return 'Mã đã hết hiệu lực. Hãy tiếp tục realtime hoặc phát lại.'
    if (remainingSeconds.value <= 5) return 'Chuẩn bị đổi sang payload mới. Nên giữ nguyên màn hình cho camera đọc lại.'
    if (remainingSeconds.value <= 10) return 'Mã vẫn hợp lệ nhưng đã vào vùng sắp hết hạn.'
    return 'Mã đang hợp lệ và sẵn sàng cho thiết bị quét đọc.'
})

const backendSummary = computed(() => {
    if (!qrData.value) return `${activeTimeStep.value} giây / chu kỳ`
    return `EMP ${qrData.value.employeeId} · ${qrData.value.timeStepSeconds}s`
})

const backendCopy = computed(() => {
    if (!qrData.value) return 'Backend sẽ trả payload, thời điểm tạo và thời điểm hết hạn ngay khi phát phiên đầu tiên.'
    return 'Payload đang hiển thị được lấy trực tiếp từ API generate và render thành QR ở phía frontend.'
})

const primaryActionLabel = computed(() => {
    if (loading.value) return 'Đang phát phiên...'
    return qrData.value ? 'Phát lại QR realtime' : 'Phát QR realtime'
})

const realtimeToggleLabel = computed(() => {
    return isRealtimeActive.value ? 'Tạm dừng realtime' : 'Tiếp tục realtime'
})

const canToggleRealtime = computed(() => {
    return Boolean(qrData.value || normalizeEmployeeId(employeeId.value))
})

const canRefreshManually = computed(() => {
    return Boolean(normalizeEmployeeId(employeeId.value))
})

const canCopyPayload = computed(() => Boolean(qrData.value?.qrPayload))

watch(
    [isAdmin, accountEmployeeId],
    ([adminMode, accountId]) => {
        if (adminMode) return

        employeeId.value = accountId

        if (!accountId || autoStartedForStaff) return

        autoStartedForStaff = true
        void issueRealtime({ announce: false })
    },
    { immediate: true }
)

function clearMessages() {
    errorMessage.value = ''
    successMessage.value = ''
}

function clearCopyMessage() {
    if (copyTimeoutId) {
        clearTimeout(copyTimeoutId)
        copyTimeoutId = null
    }

    copyMessage.value = ''
}

function setCopyMessage(message) {
    clearCopyMessage()
    copyMessage.value = message

    copyTimeoutId = setTimeout(() => {
        copyMessage.value = ''
        copyTimeoutId = null
    }, 2400)
}

function clearTicker() {
    if (tickerTimeoutId) {
        clearTimeout(tickerTimeoutId)
        tickerTimeoutId = null
    }
}

function normalizeEmployeeId(value) {
    const parsed = Number(value)
    if (!Number.isFinite(parsed) || parsed <= 0) return null
    return Math.trunc(parsed)
}

function calculateRemainingSeconds(expiresAtUtc) {
    if (!expiresAtUtc) return 0

    const diffMs = new Date(expiresAtUtc).getTime() - Date.now()
    return Math.max(0, Math.ceil(diffMs / 1000))
}

async function renderQr(payload) {
    qrImage.value = await QRCode.toDataURL(payload, {
        width: 360,
        margin: 1,
        color: {
            dark: '#10283d',
            light: '#ffffff',
        },
    })
}

async function fetchQr(employeeIdValue, options = {}) {
    const { silent = false, preserveOnError = false, announce = true } = options

    if (!silent) {
        loading.value = true
        clearMessages()
    }

    try {
        const result = await generateDynamicQr(employeeIdValue)

        if (!result.success || !result.data?.qrPayload) {
            throw new Error(result.message || 'Tạo QR thất bại.')
        }

        qrData.value = result.data
        employeeId.value = String(result.data.employeeId)
        remainingSeconds.value = calculateRemainingSeconds(result.data.expiresAtUtc)
        await renderQr(result.data.qrPayload)

        if (!silent && announce) {
            successMessage.value = result.message || 'Tạo QR động thành công.'
        }

        errorMessage.value = ''
        return true
    } catch (error) {
        if (!preserveOnError) {
            qrData.value = null
            qrImage.value = ''
            remainingSeconds.value = 0
        } else if (qrData.value?.expiresAtUtc) {
            remainingSeconds.value = calculateRemainingSeconds(qrData.value.expiresAtUtc)
        }

        errorMessage.value = error?.response?.data?.message || error?.message || 'Không thể tạo QR động.'
        successMessage.value = ''
        return false
    } finally {
        if (!silent) {
            loading.value = false
        }
    }
}

async function runTicker() {
    clearTicker()

    if (qrData.value?.expiresAtUtc) {
        remainingSeconds.value = calculateRemainingSeconds(qrData.value.expiresAtUtc)
    } else {
        remainingSeconds.value = 0
    }

    if (isRealtimeActive.value && currentEmployeeId && remainingSeconds.value <= 0 && !refreshInFlight) {
        refreshInFlight = true
        const refreshed = await fetchQr(currentEmployeeId, {
            silent: true,
            preserveOnError: true,
            announce: false,
        })
        refreshInFlight = false

        if (!refreshed) {
            isRealtimeActive.value = false
        }
    }

    const shouldContinue = isRealtimeActive.value || remainingSeconds.value > 0
    if (shouldContinue) {
        tickerTimeoutId = setTimeout(() => {
            void runTicker()
        }, 1000)
    }
}

function startTicker() {
    void runTicker()
}

function ensureEmployeeId() {
    const normalized = normalizeEmployeeId(employeeId.value)

    if (normalized) return normalized

    errorMessage.value = isAdmin.value
        ? 'Vui lòng nhập Employee ID hợp lệ.'
        : 'Tài khoản của bạn chưa liên kết với nhân sự nào. Vui lòng liên hệ Admin.'
    successMessage.value = ''
    return null
}

async function issueRealtime(options = {}) {
    const { announce = true } = options

    clearCopyMessage()

    const normalized = ensureEmployeeId()
    if (!normalized) return

    currentEmployeeId = normalized
    const ok = await fetchQr(normalized, { announce })
    if (!ok) {
        isRealtimeActive.value = false
        clearTicker()
        return
    }

    isRealtimeActive.value = true
    if (announce) {
        successMessage.value = 'Đã phát QR realtime và bật tự làm mới theo chu kỳ.'
    }
    startTicker()
}

async function refreshOnce() {
    clearCopyMessage()

    const normalized = ensureEmployeeId()
    if (!normalized) return

    currentEmployeeId = normalized
    const keepRealtime = isRealtimeActive.value
    const ok = await fetchQr(normalized)

    if (!ok) {
        clearTicker()
        return
    }

    isRealtimeActive.value = keepRealtime
    successMessage.value = 'Đã đồng bộ lại QR hiện tại từ backend.'
    if (keepRealtime || remainingSeconds.value > 0) {
        startTicker()
    }
}

function pauseRealtime() {
    isRealtimeActive.value = false
    clearMessages()
    successMessage.value = 'Đã tạm dừng realtime. Mã hiện tại sẽ hết hạn theo bộ đếm đang hiển thị.'

    if (remainingSeconds.value > 0) {
        startTicker()
    } else {
        clearTicker()
    }
}

async function resumeRealtime() {
    clearCopyMessage()

    const normalized = ensureEmployeeId()
    if (!normalized) return

    currentEmployeeId = normalized

    const needsFreshQr =
        !qrData.value ||
        qrData.value.employeeId !== normalized ||
        calculateRemainingSeconds(qrData.value.expiresAtUtc) <= 0

    if (needsFreshQr) {
        const ok = await fetchQr(normalized)
        if (!ok) return
    }

    isRealtimeActive.value = true
    clearMessages()
    successMessage.value = 'Realtime đã được tiếp tục.'
    startTicker()
}

function toggleRealtime() {
    if (isRealtimeActive.value) {
        pauseRealtime()
        return
    }

    void resumeRealtime()
}

async function copyPayload() {
    if (!qrData.value?.qrPayload) return

    try {
        if (!navigator?.clipboard?.writeText) {
            throw new Error('Clipboard API not available')
        }

        await navigator.clipboard.writeText(qrData.value.qrPayload)
        setCopyMessage('Đã sao chép payload QR.')
    } catch {
        setCopyMessage('Không thể sao chép tự động. Vui lòng sao chép thủ công từ ô payload.')
    }
}

function formatDate(dateValue) {
    if (!dateValue) return '--'

    return new Date(dateValue).toLocaleString('vi-VN', {
        hour12: false,
    })
}

function formatTimeOnly(dateValue) {
    if (!dateValue) return '--:--:--'

    return new Date(dateValue).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    })
}

onBeforeUnmount(() => {
    clearTicker()
    clearCopyMessage()
})
</script>

<style scoped>
.qr-page {
    display: grid;
    gap: 24px;
}

.hero-shell {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.9fr);
    gap: 20px;
    padding: 24px;
    border-radius: 30px;
    border: 1px solid rgba(255, 255, 255, 0.72);
    background:
        radial-gradient(circle at top right, rgba(84, 196, 211, 0.16), transparent 28%),
        radial-gradient(circle at bottom left, rgba(216, 155, 55, 0.08), transparent 30%),
        rgba(255, 255, 255, 0.88);
    box-shadow: var(--shadow-sm);
    backdrop-filter: var(--glass-blur);
}

.hero-main,
.hero-side,
.command-panel,
.preview-stack,
.live-panel,
.support-panel,
.control-grid,
.form-stack,
.feedback-stack,
.live-sidebar {
    display: grid;
    gap: 16px;
}

.hero-title {
    max-width: 14ch;
    font-family: var(--font-heading);
    font-size: clamp(2rem, 3vw, 3.05rem);
    line-height: 0.98;
    letter-spacing: -0.04em;
    color: var(--text-primary);
}

.hero-copy {
    max-width: 58ch;
    color: var(--text-secondary);
    font-size: 1.03rem;
    line-height: 1.65;
}

.hero-tags,
.action-row,
.empty-steps {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.hero-metric,
.control-card,
.hint-card,
.info-card,
.payload-card,
.countdown-card,
.account-card,
.support-card {
    padding: 18px;
    border-radius: 22px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background: rgba(236, 244, 246, 0.64);
}

.hero-metric,
.control-card,
.info-card {
    display: grid;
    gap: 6px;
}

.hero-metric.primary,
.control-card.accent,
.support-card.accent {
    background:
        linear-gradient(135deg, rgba(15, 124, 130, 0.12), rgba(84, 196, 211, 0.08)),
        rgba(236, 244, 246, 0.72);
}

.hero-metric strong,
.control-card strong,
.countdown-card strong,
.info-card strong,
.account-card strong,
.support-card strong,
.stage-stat strong {
    color: var(--text-primary);
    font-family: var(--font-heading);
}

.hero-metric strong {
    font-size: 1.22rem;
}

.metric-eyebrow,
.input-hint,
.field-label,
.hero-metric small,
.control-card small,
.info-card small,
.support-card p,
.account-card p {
    color: var(--text-muted);
}

.metric-eyebrow {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.field-label {
    font-size: 0.92rem;
}

.input-hint,
.hero-metric small,
.control-card small,
.info-card small,
.support-card p,
.account-card p,
.panel-copy {
    font-size: 0.98rem;
    line-height: 1.6;
}

.soft-chip {
    font-size: 0.84rem;
}

.metric-eyebrow.inverse {
    color: rgba(239, 251, 252, 0.72);
}

.qr-layout {
    display: grid;
    grid-template-columns: minmax(340px, 420px) minmax(0, 1fr);
    gap: 24px;
    align-items: start;
}

.mode-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    padding: 0 14px;
    border-radius: 999px;
    font-size: 0.84rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.mode-pill.admin {
    background: rgba(15, 124, 130, 0.1);
    color: var(--accent-primary);
}

.mode-pill.personal {
    background: rgba(184, 111, 33, 0.1);
    color: var(--accent-warning);
}

.control-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.control-card strong {
    font-size: 1.38rem;
}

.form-field,
.input-shell,
.hint-card,
.account-card,
.payload-card,
.countdown-card,
.support-card {
    display: grid;
    gap: 10px;
}

.qr-input {
    min-height: 52px;
    font-size: 1rem;
}

.action-row .btn {
    flex: 1;
    min-width: 160px;
}

.action-row .btn.subtle {
    background: rgba(255, 255, 255, 0.9);
    border-color: rgba(24, 49, 77, 0.1);
    color: var(--text-primary);
    box-shadow: none;
}

.action-row .btn.subtle:hover:not(:disabled) {
    background: rgba(255, 255, 255, 1);
}

.feedback-card {
    padding: 14px 16px;
    border-radius: 16px;
    font-size: 0.9rem;
    font-weight: 600;
}

.feedback-card.success {
    border: 1px solid rgba(20, 134, 109, 0.18);
    background: rgba(20, 134, 109, 0.08);
    color: var(--accent-success);
}

.feedback-card.danger {
    border: 1px solid rgba(195, 81, 70, 0.18);
    background: rgba(195, 81, 70, 0.08);
    color: var(--accent-danger);
}

.feedback-card.info {
    border: 1px solid rgba(43, 109, 138, 0.18);
    background: rgba(43, 109, 138, 0.08);
    color: var(--accent-secondary);
}

.hint-list,
.support-list {
    margin: 0;
    padding-left: 18px;
    display: grid;
    gap: 8px;
    color: var(--text-secondary);
    font-size: 0.98rem;
    line-height: 1.65;
}

.live-layout {
    display: grid;
    grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
    gap: 20px;
    align-items: start;
}

.qr-stage {
    display: grid;
    gap: 18px;
    padding: 20px;
    border-radius: 28px;
    border: 1px solid rgba(24, 49, 77, 0.08);
    background:
        radial-gradient(circle at top right, rgba(84, 196, 211, 0.18), transparent 34%),
        linear-gradient(180deg, rgba(16, 32, 51, 0.98), rgba(24, 49, 77, 0.96));
    color: #eefbfc;
    box-shadow: var(--shadow-md);
}

.stage-head,
.stage-foot,
.payload-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.stage-head h3 {
    margin-top: 6px;
    font-family: var(--font-heading);
    font-size: 1.72rem;
    color: #ffffff;
}

.stage-pill,
.ghost-copy {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
}

.stage-pill {
    min-height: 34px;
    padding: 0 12px;
    background: rgba(255, 255, 255, 0.08);
    color: #eefbfc;
    font-size: 0.84rem;
    font-weight: 700;
}

.stage-pill.success {
    background: rgba(20, 134, 109, 0.18);
}

.stage-pill.warn {
    background: rgba(184, 111, 33, 0.18);
}

.qr-frame {
    position: relative;
    padding: 18px;
    border-radius: 28px;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02)),
        rgba(255, 255, 255, 0.02);
    overflow: hidden;
}

.qr-frame-glow {
    position: absolute;
    inset: 12px;
    border-radius: 24px;
    background: radial-gradient(circle at center, rgba(84, 196, 211, 0.32), transparent 60%);
    filter: blur(18px);
    opacity: 0.75;
}

.qr-frame img {
    position: relative;
    z-index: 1;
    display: block;
    width: min(100%, 320px);
    margin: 0 auto;
    padding: 16px;
    border-radius: 22px;
    border: 1px solid rgba(24, 49, 77, 0.12);
    background: #ffffff;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
}

.stage-stat {
    display: grid;
    gap: 4px;
}

.stage-stat span {
    color: rgba(239, 251, 252, 0.72);
    font-size: 0.9rem;
}

.stage-stat strong {
    color: #ffffff;
    font-size: 1.08rem;
}

.ghost-copy {
    min-height: 38px;
    padding: 0 14px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    background: rgba(255, 255, 255, 0.08);
    color: #eff7f8;
    font-size: 0.9rem;
    font-weight: 700;
    transition: transform var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast);
}

.ghost-copy:hover:not(:disabled) {
    transform: translateY(-1px);
    border-color: rgba(84, 196, 211, 0.34);
    background: rgba(84, 196, 211, 0.14);
}

.ghost-copy.secondary {
    border-color: rgba(24, 49, 77, 0.12);
    background: rgba(255, 255, 255, 0.82);
    color: var(--text-primary);
}

.ghost-copy.secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.96);
}

.ghost-copy:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

.countdown-card strong {
    font-size: clamp(2.1rem, 5vw, 3rem);
    line-height: 0.95;
}

.countdown-card p {
    color: var(--text-secondary);
    font-size: 1rem;
    line-height: 1.6;
}

.countdown-card.stable {
    background:
        linear-gradient(135deg, rgba(20, 134, 109, 0.1), rgba(84, 196, 211, 0.08)),
        rgba(236, 244, 246, 0.72);
}

.countdown-card.warning {
    background:
        linear-gradient(135deg, rgba(184, 111, 33, 0.12), rgba(216, 155, 55, 0.08)),
        rgba(236, 244, 246, 0.72);
}

.countdown-card.urgent {
    background:
        linear-gradient(135deg, rgba(195, 81, 70, 0.14), rgba(216, 155, 55, 0.08)),
        rgba(236, 244, 246, 0.72);
}

.countdown-card.muted {
    background: rgba(236, 244, 246, 0.72);
}

.countdown-track {
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: rgba(24, 49, 77, 0.08);
    overflow: hidden;
}

.countdown-track span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--accent-warning), var(--accent-primary));
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.info-card span {
    color: var(--text-muted);
    font-size: 0.9rem;
}

.info-card strong {
    font-size: 1.12rem;
    line-height: 1.3;
}

.payload-head p {
    margin-top: 4px;
    color: var(--text-secondary);
    font-size: 0.96rem;
    line-height: 1.6;
}

.payload-box {
    width: 100%;
    min-height: 126px;
    padding: 16px;
    border-radius: 18px;
    border: 1px solid rgba(24, 49, 77, 0.1);
    background: rgba(255, 255, 255, 0.82);
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    line-height: 1.55;
    resize: vertical;
}

.empty-shell {
    display: grid;
    place-items: center;
    gap: 14px;
    min-height: 520px;
    padding: 30px 24px;
    text-align: center;
    border-radius: 28px;
    border: 1px dashed rgba(24, 49, 77, 0.16);
    background:
        radial-gradient(circle at top, rgba(84, 196, 211, 0.12), transparent 32%),
        rgba(236, 244, 246, 0.4);
}

.empty-shell h3 {
    font-family: var(--font-heading);
    font-size: 1.45rem;
    color: var(--text-primary);
}

.empty-shell p {
    max-width: 48ch;
    color: var(--text-secondary);
}

.empty-orb {
    width: 96px;
    height: 96px;
    border-radius: 30px;
    background:
        radial-gradient(circle at 30% 30%, rgba(84, 196, 211, 0.8), rgba(43, 109, 138, 0.14)),
        rgba(255, 255, 255, 0.8);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.68),
        0 20px 40px rgba(43, 109, 138, 0.18);
}

.empty-steps span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 9px 14px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(24, 49, 77, 0.08);
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 700;
}

.support-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}

.support-card strong {
    font-size: 1.08rem;
}

@media (max-width: 1240px) {
    .hero-shell,
    .qr-layout,
    .live-layout {
        grid-template-columns: 1fr;
    }

    .hero-title {
        max-width: none;
    }
}

@media (max-width: 900px) {
    .control-grid,
    .support-grid,
    .info-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .hero-shell,
    .ops-panel,
    .qr-stage,
    .empty-shell {
        padding: 18px;
    }

    .action-row .btn {
        width: 100%;
    }

    .empty-shell {
        min-height: 420px;
    }
}
</style>
