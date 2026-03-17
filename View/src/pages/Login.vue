<template>
    <div class="login-page">
        <!-- Lochmara Animated Background Globs -->
        <div class="login-bg">
            <div class="bg-glow glow-1"></div>
            <div class="bg-glow glow-2"></div>
            <div class="bg-glow glow-3"></div>
            <div class="bg-grid"></div>
        </div>

        <div class="login-container animate-in">
            <!-- Brand Logo -->
            <div class="login-logo">
                <div class="logo-icon-lg">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" fill="currentColor" opacity="0.3" />
                        <path d="M12 8L8 10.5V15.5L12 18L16 15.5V10.5L12 8Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
                    </svg>
                </div>
                <h1 class="login-title">V-Shield</h1>
                <p class="login-subtitle">Hệ thống giám sát ra/vào thông minh</p>
            </div>

            <!-- Login Form -->
            <form class="login-form" @submit.prevent="handleLogin">
                <div class="form-group">
                    <label for="username">Tài khoản quản trị</label>
                    <div class="input-wrapper">
                        <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                        <input id="username" v-model="form.username" type="text" placeholder="Nhập tên đăng nhập" autocomplete="username" :disabled="loading" class="sleek-input" />
                    </div>
                </div>

                <div class="form-group">
                    <label for="password">Mật khẩu truy cập</label>
                    <div class="input-wrapper">
                        <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>
                        <input id="password" v-model="form.password" :type="showPassword ? 'text' : 'password'" placeholder="Nhập mật khẩu" autocomplete="current-password" :disabled="loading" class="sleek-input" />
                        <button type="button" class="toggle-password" @click="showPassword = !showPassword" tabindex="-1">
                            <svg v-if="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                <circle cx="12" cy="12" r="3" />
                            </svg>
                            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" />
                                <line x1="1" y1="1" x2="23" y2="23" />
                            </svg>
                        </button>
                    </div>
                </div>

                <!-- Error Notice -->
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
                    <span v-else>Đăng nhập an toàn</span>
                </button>
            </form>

            <div class="login-footer">
                <p>Môi trường được bảo vệ bởi <b>AI Pro Max 2.0</b></p>
                <p style="margin-top:2px;">© 2024 V-Shield Security Group</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
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
        error.value = 'Vui lòng điền đủ thông tin xác thực'
        return
    }

    loading.value = true
    try {
        await login(form.username, form.password)
        router.push('/')
    } catch (err) {
        if (err.response?.status === 401) {
            error.value = 'Hồ sơ xác thực không chính xác'
        } else if (err.code === 'ERR_NETWORK') {
            error.value = 'Lỗi kết nối tới Core Server. Vui lòng kiểm tra API.'
        } else {
            error.value = err.response?.data?.message || 'Có lỗi hệ thống phát sinh'
        }
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
/* Core Page Setup */
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: var(--bg-secondary); position: relative; overflow: hidden; font-family: 'Inter', sans-serif;}

/* Environment Background */
.login-bg { position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 0;}
.bg-glow { position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.4; animation: float 25s ease-in-out infinite; }
.glow-1 { width: 600px; height: 600px; background: var(--accent-primary); top: -150px; right: -150px; animation-delay: 0s; }
.glow-2 { width: 500px; height: 500px; background: var(--bg-primary); bottom: -100px; left: -100px; animation-delay: -5s; }
.glow-3 { width: 400px; height: 400px; background: var(--accent-secondary); top: 60%; left: 40%; transform: translate(-50%, -50%); opacity: 0.2; animation-delay: -10s; }
.bg-grid { position: absolute; inset: 0; background-image: linear-gradient(rgba(9, 31, 58, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(9, 31, 58, 0.05) 1px, transparent 1px); background-size: 32px 32px; opacity: 0.5; z-index: 1;}

@keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1); }
    25% { transform: translate(40px, -40px) scale(1.1); }
    50% { transform: translate(-30px, 30px) scale(0.95); }
    75% { transform: translate(20px, 20px) scale(1.05); }
}

/* Auth Card */
.login-container { width: 100%; max-width: 440px; padding: 48px 40px; background: var(--bg-card); backdrop-filter: blur(20px); border: 1px solid var(--border-color); border-radius: 20px; box-shadow: var(--shadow-lg); position: relative; z-index: 2; }

/* Branding */
.login-logo { text-align: center; margin-bottom: 40px; }
.logo-icon-lg { width: 64px; height: 64px; margin: 0 auto 20px; color: var(--accent-primary); filter: drop-shadow(0 0 15px rgba(78, 163, 255, 0.4));}
.logo-icon-lg svg { width: 100%; height: 100%; }
.login-title { font-size: 2.2rem; font-weight: 800; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 8px; letter-spacing: -0.5px;}
.login-subtitle { color: var(--text-secondary); font-size: 0.95rem; font-weight: 500;}

/* Input Area */
.login-form .form-group { margin-bottom: 24px; }
.login-form label { display: block; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;}

.input-wrapper { position: relative; display: flex; align-items: center; }
.input-icon { position: absolute; left: 16px; width: 20px; height: 20px; color: var(--text-muted); pointer-events: none; z-index: 1; transition: color 0.3s;}

.sleek-input { width: 100%; padding: 14px 44px 14px 48px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; color: var(--text-primary); font-size: 1rem; transition: all 0.3s; }
.sleek-input:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 4px rgba(78, 163, 255, 0.15); background: var(--bg-card);}
.sleek-input:focus ~ .input-icon, .input-wrapper:focus-within .input-icon { color: var(--accent-primary); }
.sleek-input::placeholder { color: var(--text-muted); }

.toggle-password { position: absolute; right: 14px; background: none; border: none; color: var(--text-muted); display: flex; align-items: center; justify-content: center; padding: 4px; transition: color 0.3s; cursor: pointer;}
.toggle-password:hover { color: var(--accent-primary); }
.toggle-password svg { width: 20px; height: 20px; }

/* Feedback */
.login-error { display: flex; align-items: center; gap: 10px; padding: 14px 16px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 12px; color: var(--accent-danger); font-size: 0.9rem; margin-bottom: 24px; font-weight: 500;}
.login-error svg { width: 20px; height: 20px; flex-shrink: 0; }
.slide-error-enter-active, .slide-error-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-error-enter-from, .slide-error-leave-to { opacity: 0; transform: translateY(-10px); }

/* Primary Action */
.btn-login { width: 100%; padding: 16px 24px; background: var(--accent-gradient); color: #fff; font-size: 1.05rem; font-weight: 600; border: none; border-radius: 12px; transition: all 0.3s; display: flex; align-items: center; justify-content: center; gap: 10px; box-shadow: 0 4px 15px rgba(78, 163, 255, 0.3); text-shadow: 0 1px 2px rgba(9, 31, 58, 0.2); cursor: pointer;}
.btn-login:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(78, 163, 255, 0.4); filter: brightness(1.05);}
.btn-login:disabled { opacity: 0.7; cursor: not-allowed; transform: none; box-shadow: none;}

.spinner { width: 22px; height: 22px; border: 3px solid rgba(255, 255, 255, 0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Footer */
.login-footer { text-align: center; margin-top: 36px; color: var(--text-muted); font-size: 0.8rem; line-height: 1.5;}
.login-footer b { color: var(--accent-primary); font-weight: 600;}

/* Mobile Optimization */
@media (max-width: 480px) {
    .login-container { margin: 16px; padding: 32px 24px; }
    .bg-grid { background-size: 20px 20px; }
}
</style>
