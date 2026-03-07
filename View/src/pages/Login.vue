<template>
    <div class="login-page">
        <div class="login-bg">
            <div class="bg-glow glow-1"></div>
            <div class="bg-glow glow-2"></div>
            <div class="bg-glow glow-3"></div>
        </div>

        <div class="login-container animate-in">
            <!-- Logo -->
            <div class="login-logo">
                <div class="logo-icon-lg">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" stroke-width="2"
                            stroke-linejoin="round" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" fill="currentColor" opacity="0.3" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" stroke="currentColor" stroke-width="1.5"
                            stroke-linejoin="round" />
                    </svg>
                </div>
                <h1 class="login-title">V-Shield</h1>
                <p class="login-subtitle">Hệ thống quản lý ra/vào thông minh</p>
            </div>

            <!-- Form -->
            <form class="login-form" @submit.prevent="handleLogin">
                <div class="form-group">
                    <label for="username">Tên đăng nhập</label>
                    <div class="input-wrapper">
                        <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                        </svg>
                        <input id="username" v-model="form.username" type="text" placeholder="Nhập tên đăng nhập"
                            autocomplete="username" :disabled="loading" />
                    </div>
                </div>

                <div class="form-group">
                    <label for="password">Mật khẩu</label>
                    <div class="input-wrapper">
                        <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                            <path d="M7 11V7a5 5 0 0110 0v4" />
                        </svg>
                        <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'"
                            placeholder="Nhập mật khẩu" autocomplete="current-password" :disabled="loading" />
                        <button type="button" class="toggle-password" @click="showPassword = !showPassword"
                            tabindex="-1">
                            <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                <circle cx="12" cy="12" r="3" />
                            </svg>
                            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path
                                    d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                                <line x1="1" y1="1" x2="23" y2="23" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Error message -->
                <transition name="slide-error">
                    <div v-if="error" class="login-error">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="15" y1="9" x2="9" y2="15" />
                            <line x1="9" y1="9" x2="15" y2="15" />
                        </svg>
                        <span>{{ error }}</span>
                    </div>
                </transition>

                <button type="submit" class="btn-login" :disabled="loading">
                    <span v-if="loading" class="spinner"></span>
                    <span v-else>Đăng nhập</span>
                </button>
            </form>

            <p class="login-footer">© 2024 V-Shield Security System</p>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../stores/auth'

const router = useRouter()

const form = reactive({
    username: '',
    password: '',
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
    error.value = ''

    if (!form.username.trim() || !form.password.trim()) {
        error.value = 'Vui lòng nhập đầy đủ thông tin'
        return
    }

    loading.value = true
    try {
        await login(form.username, form.password)
        router.push('/')
    } catch (err) {
        if (err.response?.status === 401) {
            error.value = 'Tên đăng nhập hoặc mật khẩu không đúng'
        } else if (err.code === 'ERR_NETWORK') {
            error.value = 'Không thể kết nối đến server. Vui lòng kiểm tra API.'
        } else {
            error.value = err.response?.data?.message || 'Đã xảy ra lỗi, vui lòng thử lại'
        }
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    position: relative;
    overflow: hidden;
}

/* Animated background glows */
.login-bg {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
}

.bg-glow {
    position: absolute;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.15;
    animation: float 20s ease-in-out infinite;
}

.glow-1 {
    width: 500px;
    height: 500px;
    background: var(--accent-primary);
    top: -100px;
    right: -100px;
    animation-delay: 0s;
}

.glow-2 {
    width: 400px;
    height: 400px;
    background: var(--accent-secondary);
    bottom: -50px;
    left: -50px;
    animation-delay: -7s;
}

.glow-3 {
    width: 300px;
    height: 300px;
    background: var(--accent-info);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation-delay: -14s;
}

@keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1); }
    25% { transform: translate(30px, -30px) scale(1.1); }
    50% { transform: translate(-20px, 20px) scale(0.95); }
    75% { transform: translate(20px, 10px) scale(1.05); }
}

/* Container */
.login-container {
    width: 100%;
    max-width: 420px;
    padding: 40px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-lg);
    box-shadow: var(--shadow-lg), 0 0 60px rgba(59, 130, 246, 0.05);
    position: relative;
    z-index: 1;
}

/* Logo */
.login-logo {
    text-align: center;
    margin-bottom: 36px;
}

.logo-icon-lg {
    width: 56px;
    height: 56px;
    margin: 0 auto 16px;
    color: var(--accent-primary);
}

.logo-icon-lg svg {
    width: 100%;
    height: 100%;
}

.login-title {
    font-size: 2rem;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 6px;
}

.login-subtitle {
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Form */
.login-form .form-group {
    margin-bottom: 20px;
}

.login-form label {
    display: block;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
}

.input-icon {
    position: absolute;
    left: 14px;
    width: 18px;
    height: 18px;
    color: var(--text-muted);
    pointer-events: none;
    z-index: 1;
}

.input-wrapper input {
    width: 100%;
    padding: 12px 44px 12px 44px;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    color: var(--text-primary);
    font-size: 0.95rem;
    transition: all var(--transition-normal);
}

.input-wrapper input:focus {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.input-wrapper input::placeholder {
    color: var(--text-muted);
}

.toggle-password {
    position: absolute;
    right: 12px;
    background: none;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    transition: color var(--transition-fast);
}

.toggle-password:hover {
    color: var(--text-primary);
}

.toggle-password svg {
    width: 18px;
    height: 18px;
}

/* Error */
.login-error {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--border-radius-sm);
    color: var(--accent-danger);
    font-size: 0.85rem;
    margin-bottom: 20px;
}

.login-error svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
}

.slide-error-enter-active,
.slide-error-leave-active {
    transition: all 0.3s ease;
}

.slide-error-enter-from,
.slide-error-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

/* Login Button */
.btn-login {
    width: 100%;
    padding: 13px 24px;
    background: var(--accent-gradient);
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    border-radius: var(--border-radius-sm);
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.btn-login:hover:not(:disabled) {
    background: var(--accent-gradient-hover);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    transform: translateY(-2px);
}

.btn-login:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

/* Spinner */
.spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Footer */
.login-footer {
    text-align: center;
    margin-top: 28px;
    color: var(--text-muted);
    font-size: 0.75rem;
}

/* Responsive */
@media (max-width: 480px) {
    .login-container {
        margin: 16px;
        padding: 28px 24px;
    }
}
</style>
