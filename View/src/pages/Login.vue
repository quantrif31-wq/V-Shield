<template>
    <div class="login-page">
        <div class="login-bg" aria-hidden="true">
            <div class="bg-orb orb-a"></div>
            <div class="bg-orb orb-b"></div>
            <div class="bg-orb orb-c"></div>
            <div class="bg-grid"></div>
        </div>

        <div class="login-shell animate-in">
            <section class="login-story">
                <span class="story-eyebrow">V-Shield Control Room</span>
                <h1>Kiểm soát ra vào với giao diện rõ ngữ cảnh, phản hồi nhanh và đủ tin cậy để vận hành mỗi ngày.</h1>
                <p class="story-copy">
                    Theo dõi nhân sự, phương tiện và camera trên cùng một mặt phẳng điều phối.
                    Mọi quyết định truy cập đều được gắn với dữ liệu nhận diện và lịch sử sự kiện rõ ràng.
                </p>

                <div class="story-metrics">
                    <article class="metric-card">
                        <strong>24/7</strong>
                        <span>Giám sát liên tục</span>
                    </article>
                    <article class="metric-card">
                        <strong>Face ID</strong>
                        <span>Nhận diện khuôn mặt</span>
                    </article>
                    <article class="metric-card">
                        <strong>ANPR</strong>
                        <span>Đối soát biển số</span>
                    </article>
                </div>

                <div class="story-panel">
                    <div class="panel-heading">
                        <span class="panel-chip">Live pipeline</span>
                        <span class="panel-status">
                            <span class="panel-dot"></span>
                            Ready
                        </span>
                    </div>

                    <div class="panel-steps">
                        <div class="panel-step">
                            <strong>01</strong>
                            <div>
                                <h3>Xác thực người vận hành</h3>
                                <p>Đảm bảo đúng vai trò truy cập trước khi vào trung tâm điều phối.</p>
                            </div>
                        </div>
                        <div class="panel-step">
                            <strong>02</strong>
                            <div>
                                <h3>Tổng hợp tín hiệu tại cổng</h3>
                                <p>Luồng nhân sự, phương tiện và camera được gom về một góc nhìn thống nhất.</p>
                            </div>
                        </div>
                        <div class="panel-step">
                            <strong>03</strong>
                            <div>
                                <h3>Ra quyết định nhanh</h3>
                                <p>Nhìn thấy trạng thái, nhật ký và cảnh báo ngay tại điểm cần can thiệp.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section class="login-card">
                <div class="brand-lockup">
                    <div class="brand-mark">
                        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
                            <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" fill="currentColor" opacity="0.24" />
                            <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round" />
                        </svg>
                    </div>
                    <div>
                        <span class="brand-kicker">Secure sign in</span>
                        <h2>Truy cập trung tâm điều phối</h2>
                    </div>
                </div>

                <form class="login-form" @submit.prevent="handleLogin">
                    <div class="form-group">
                        <label for="username">Tài khoản quản trị</label>
                        <div class="input-shell">
                            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                                <circle cx="12" cy="7" r="4" />
                            </svg>
                            <input
                                id="username"
                                v-model="form.username"
                                type="text"
                                placeholder="Nhập tên đăng nhập"
                                autocomplete="username"
                                :disabled="loading"
                            />
                        </div>
                    </div>

                    <div class="form-group">
                        <div class="label-row">
                            <label for="password">Mật khẩu truy cập</label>
                            <span class="field-hint">Bảo mật cấp vận hành</span>
                        </div>
                        <div class="input-shell">
                            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                <rect x="3" y="11" width="18" height="10" rx="2" />
                                <path d="M7 11V8a5 5 0 0110 0v3" />
                            </svg>
                            <input
                                id="password"
                                v-model="form.password"
                                :type="showPassword ? 'text' : 'password'"
                                placeholder="Nhập mật khẩu"
                                autocomplete="current-password"
                                :disabled="loading"
                            />
                            <button
                                type="button"
                                class="toggle-password"
                                :aria-label="showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
                                @click="showPassword = !showPassword"
                            >
                                <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                    <circle cx="12" cy="12" r="3" />
                                </svg>
                                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                    <path d="M17.94 17.94A10.94 10.94 0 0112 20c-7 0-11-8-11-8a21.76 21.76 0 015.17-5.94" />
                                    <path d="M9.88 9.88A3 3 0 0114.12 14.12" />
                                    <path d="M22.54 11.88A21.64 21.64 0 0017 6.12" />
                                    <line x1="1" y1="1" x2="23" y2="23" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <transition name="slide-error">
                        <div v-if="error" class="login-error">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M12 8v4" />
                                <path d="M12 16h.01" />
                            </svg>
                            <span>{{ error }}</span>
                        </div>
                    </transition>

                    <button type="submit" class="btn-login" :disabled="loading">
                        <span v-if="loading" class="spinner"></span>
                        <span v-else>Vào trung tâm điều phối</span>
                    </button>
                </form>

                <div class="login-footer">
                    <div class="footer-item">
                        <strong>Kênh truy cập</strong>
                        <span>Bảo vệ, vận hành, quản trị</span>
                    </div>
                    <div class="footer-item">
                        <strong>Phạm vi</strong>
                        <span>Nhân sự, camera, phương tiện, lịch sử</span>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../stores/auth'

const router = useRouter()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
    error.value = ''

    if (!form.username.trim() || !form.password.trim()) {
        error.value = 'Vui lòng điền đầy đủ thông tin xác thực.'
        return
    }

    loading.value = true
    try {
        await login(form.username, form.password)
        router.push('/')
    } catch (err) {
        if (err.response?.status === 401) {
            error.value = 'Thông tin đăng nhập chưa chính xác.'
        } else if (err.code === 'ERR_NETWORK') {
            error.value = 'Không thể kết nối tới Core Server. Vui lòng kiểm tra API.'
        } else {
            error.value = err.response?.data?.message || 'Đã xảy ra lỗi hệ thống khi xác thực.'
        }
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.login-page {
    min-height: 100vh;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 28px;
    overflow: hidden;
}

.login-bg {
    position: absolute;
    inset: 0;
    pointer-events: none;
}

.bg-orb {
    position: absolute;
    border-radius: 999px;
    filter: blur(90px);
    opacity: 0.35;
}

.orb-a {
    width: 440px;
    height: 440px;
    top: -120px;
    left: -120px;
    background: rgba(84, 196, 211, 0.34);
}

.orb-b {
    width: 380px;
    height: 380px;
    right: -60px;
    top: 18%;
    background: rgba(15, 124, 130, 0.22);
}

.orb-c {
    width: 320px;
    height: 320px;
    bottom: -80px;
    left: 38%;
    background: rgba(216, 155, 55, 0.16);
}

.bg-grid {
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(16, 32, 51, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(16, 32, 51, 0.04) 1px, transparent 1px);
    background-size: 44px 44px;
}

.login-shell {
    position: relative;
    z-index: 1;
    width: min(1200px, 100%);
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(360px, 420px);
    gap: 22px;
    align-items: stretch;
}

.login-story,
.login-card {
    border: 1px solid rgba(255, 255, 255, 0.66);
    background: rgba(255, 255, 255, 0.88);
    backdrop-filter: var(--glass-blur);
    box-shadow: var(--shadow-lg);
}

.login-story {
    padding: 34px;
    border-radius: 32px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 28px;
}

.story-eyebrow {
    display: inline-flex;
    align-items: center;
    align-self: flex-start;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(15, 124, 130, 0.08);
    color: var(--accent-primary);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.login-story h1 {
    font-family: var(--font-heading);
    font-size: clamp(2.2rem, 4vw, 3.4rem);
    font-weight: 700;
    line-height: 1.02;
    letter-spacing: -0.05em;
    color: var(--text-primary);
    max-width: 13ch;
}

.story-copy {
    max-width: 60ch;
    color: var(--text-secondary);
    font-size: 1rem;
}

.story-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
}

.metric-card {
    padding: 18px;
    border-radius: 22px;
    border: 1px solid var(--border-color);
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(236, 244, 246, 0.86));
}

.metric-card strong {
    display: block;
    font-family: var(--font-heading);
    font-size: 1.32rem;
    font-weight: 700;
    color: var(--text-primary);
}

.metric-card span {
    display: block;
    margin-top: 6px;
    color: var(--text-secondary);
    font-size: 0.84rem;
}

.story-panel {
    padding: 22px;
    border-radius: 28px;
    background: linear-gradient(135deg, rgba(16, 32, 51, 0.96), rgba(24, 49, 77, 0.92));
    color: var(--text-inverse);
    overflow: hidden;
    position: relative;
}

.story-panel::before {
    content: '';
    position: absolute;
    inset: auto -60px -60px auto;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(84, 196, 211, 0.24), transparent 70%);
}

.panel-heading {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 20px;
}

.panel-chip {
    display: inline-flex;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(84, 196, 211, 0.12);
    color: #b8f7ff;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.panel-status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #d7fbff;
    font-size: 0.8rem;
    font-weight: 700;
}

.panel-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #5de3c7;
    box-shadow: 0 0 0 5px rgba(93, 227, 199, 0.12);
}

.panel-steps {
    position: relative;
    z-index: 1;
    display: grid;
    gap: 14px;
}

.panel-step {
    display: grid;
    grid-template-columns: 44px minmax(0, 1fr);
    gap: 14px;
    padding: 14px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.panel-step:first-child {
    border-top: none;
    padding-top: 0;
}

.panel-step strong {
    width: 44px;
    height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 14px;
    background: rgba(84, 196, 211, 0.1);
    color: #c6fbff;
    font-family: var(--font-heading);
    font-weight: 700;
}

.panel-step h3 {
    font-size: 0.98rem;
    font-weight: 700;
    color: #f3fdff;
}

.panel-step p {
    margin-top: 6px;
    color: rgba(222, 241, 246, 0.78);
    font-size: 0.86rem;
}

.login-card {
    border-radius: 28px;
    padding: 28px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    gap: 24px;
}

.brand-lockup {
    display: flex;
    align-items: center;
    gap: 16px;
}

.brand-mark {
    width: 58px;
    height: 58px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(84, 196, 211, 0.18), rgba(43, 109, 138, 0.16));
    color: var(--accent-primary);
}

.brand-mark svg {
    width: 30px;
    height: 30px;
}

.brand-kicker {
    display: block;
    margin-bottom: 4px;
    color: var(--text-muted);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.brand-lockup h2 {
    font-family: var(--font-heading);
    font-size: 1.48rem;
    font-weight: 700;
    line-height: 1.08;
    color: var(--text-primary);
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: 18px;
    margin-top: 6px;
}

.label-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.field-hint {
    color: var(--text-muted);
    font-size: 0.75rem;
}

.input-shell {
    position: relative;
}

.input-shell input {
    width: 100%;
    min-height: 52px;
    padding: 0 48px 0 46px;
    border-radius: 16px;
    border: 1px solid rgba(24, 49, 77, 0.12);
    background: var(--bg-input);
    color: var(--text-primary);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast), background var(--transition-fast);
}

.input-shell input::placeholder {
    color: var(--text-muted);
}

.input-shell input:focus {
    border-color: rgba(15, 124, 130, 0.36);
    box-shadow: 0 0 0 4px rgba(84, 196, 211, 0.18);
    background: rgba(255, 255, 255, 0.98);
}

.input-icon {
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
    width: 18px;
    height: 18px;
    color: var(--text-muted);
}

.toggle-password {
    position: absolute;
    top: 50%;
    right: 10px;
    transform: translateY(-50%);
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    color: var(--text-muted);
}

.toggle-password:hover {
    color: var(--accent-primary);
    background: rgba(15, 124, 130, 0.08);
}

.toggle-password svg {
    width: 18px;
    height: 18px;
}

.login-error {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 14px 16px;
    border-radius: 16px;
    border: 1px solid rgba(195, 81, 70, 0.18);
    background: rgba(195, 81, 70, 0.08);
    color: var(--accent-danger);
    font-size: 0.88rem;
    line-height: 1.45;
}

.login-error svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    margin-top: 1px;
}

.slide-error-enter-active,
.slide-error-leave-active {
    transition: all 0.22s ease;
}

.slide-error-enter-from,
.slide-error-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

.btn-login {
    min-height: 54px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    border-radius: 18px;
    background: var(--accent-gradient);
    color: #fff;
    font-weight: 700;
    box-shadow: 0 18px 34px rgba(15, 124, 130, 0.22);
    transition: transform var(--transition-fast), box-shadow var(--transition-fast), filter var(--transition-fast);
}

.btn-login:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.03);
    box-shadow: 0 22px 42px rgba(15, 124, 130, 0.3);
}

.btn-login:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

.spinner {
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255, 255, 255, 0.24);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.login-footer {
    margin-top: auto;
    padding-top: 8px;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.footer-item {
    padding: 14px 16px;
    border-radius: 18px;
    background: rgba(236, 244, 246, 0.78);
    border: 1px solid rgba(24, 49, 77, 0.08);
}

.footer-item strong {
    display: block;
    color: var(--text-primary);
    font-size: 0.86rem;
    font-weight: 700;
}

.footer-item span {
    display: block;
    margin-top: 6px;
    color: var(--text-secondary);
    font-size: 0.8rem;
    line-height: 1.5;
}

@media (max-width: 1080px) {
    .login-shell {
        grid-template-columns: 1fr;
    }

    .login-story h1 {
        max-width: none;
    }
}

@media (max-width: 768px) {
    .login-page {
        padding: 16px;
    }

    .login-story,
    .login-card {
        padding: 22px;
        border-radius: 24px;
    }

    .story-metrics,
    .login-footer {
        grid-template-columns: 1fr;
    }

    .label-row {
        align-items: flex-start;
        flex-direction: column;
        gap: 4px;
    }
}
</style>
