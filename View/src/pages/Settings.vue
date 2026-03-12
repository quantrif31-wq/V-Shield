<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Cài đặt Hệ thống</h1>
                <p class="page-subtitle">Tùy chỉnh nền tảng & quản lý thông báo AI</p>
            </div>
            <div class="header-actions">
               <button class="btn btn-primary action-btn" @click="saveSettings">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 16px; height: 16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
                        <polyline stroke-linecap="round" stroke-linejoin="round" points="17 21 17 13 7 13 7 21" />
                        <polyline stroke-linecap="round" stroke-linejoin="round" points="7 3 7 8 15 8" />
                    </svg>
                    Lưu cài đặt
                </button>
            </div>
        </header>

        <div class="settings-layout">
            <!-- Sidebar Navigation -->
            <div class="settings-nav bento-card">
                <button v-for="tab in tabs" :key="tab.id" class="settings-tab" :class="{ active: activeTab === tab.id }" @click="activeTab = tab.id">
                    <span class="tab-icon" v-html="tab.icon"></span>
                    <span class="tab-label">{{ tab.label }}</span>
                </button>
            </div>

            <!-- Main Content Area -->
            <div class="settings-content">
                <!-- General Settings -->
                <transition name="fade-up" mode="out-in">
                    <div v-if="activeTab === 'general'" key="general" class="settings-section">
                        <div class="bento-card">
                            <h2 class="bento-title mb-1">Cài đặt chung</h2>
                            <p class="text-secondary text-sm mb-4">Quản lý và thiết lập thông tin cơ sở kinh doanh</p>

                            <div class="form-grid">
                                <div class="input-pane full-width">
                                    <label>Tên cơ sở / Công ty</label>
                                    <input v-model="settings.companyName" type="text" class="sleek-input" />
                                </div>
                                <div class="form-row grid-2">
                                    <div class="input-pane">
                                        <label>Giờ mở cổng</label>
                                        <input v-model="settings.openTime" type="time" class="sleek-input" />
                                    </div>
                                    <div class="input-pane">
                                        <label>Giờ đóng cổng</label>
                                        <input v-model="settings.closeTime" type="time" class="sleek-input" />
                                    </div>
                                </div>
                                <div class="form-row grid-2">
                                    <div class="input-pane">
                                        <label>Ngôn ngữ</label>
                                        <select v-model="settings.language" class="sleek-select">
                                            <option value="vi">Tiếng Việt</option>
                                            <option value="en">English (US)</option>
                                        </select>
                                    </div>
                                    <div class="input-pane">
                                        <label>Múi giờ</label>
                                        <select v-model="settings.timezone" class="sleek-select">
                                            <option value="UTC+7">UTC+7 (Hanoi, Bangkok)</option>
                                            <option value="UTC+8">UTC+8 (Singapore)</option>
                                            <option value="UTC+9">UTC+9 (Tokyo)</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Camera Settings -->
                    <div v-else-if="activeTab === 'camera'" key="camera" class="settings-section">
                        <div class="bento-card bg-transparent border-0 p-0" style="background:transparent; border:none; padding:0; box-shadow:none;">
                            <h2 class="bento-title mb-1 px-1">Danh sách Camera</h2>
                            <p class="text-secondary text-sm mb-4 px-1">Cấu hình luồng kỹ thuật số và điểm lắp đặt</p>
                            
                            <div class="camera-grid">
                                <div v-for="cam in cameraSettings" :key="cam.id" class="bento-card cam-card">
                                    <div class="cam-header">
                                        <div class="cam-info">
                                            <h4>{{ cam.name }}</h4>
                                            <span class="status-pill minimal" :class="cam.online ? 'active' : 'inactive'">
                                                <span class="pill-dot"></span>
                                                {{ cam.online ? 'Trực tuyến' : 'Ngoại tuyến' }}
                                            </span>
                                        </div>
                                        <label class="modern-toggle">
                                            <input type="checkbox" v-model="cam.enabled" />
                                            <span class="toggle-track"></span>
                                        </label>
                                    </div>
                                    <div class="cam-form">
                                        <div class="input-pane">
                                            <label>RTSP Stream URL</label>
                                            <input v-model="cam.url" type="text" class="sleek-input text-mono text-sm" />
                                        </div>
                                        <div class="input-pane">
                                            <label>Vị trí lắp đặt</label>
                                            <input v-model="cam.location" type="text" class="sleek-input" />
                                        </div>
                                        <div class="grid-2">
                                            <div class="input-pane">
                                                <label>Loại giám sát gốc</label>
                                                <select v-model="cam.recognitionType" class="sleek-select text-sm">
                                                    <option value="face">Khuôn mặt (Face)</option>
                                                    <option value="plate">Biển số (LPR)</option>
                                                    <option value="both">Hỗn hợp (Face + LPR)</option>
                                                </select>
                                            </div>
                                            <div class="input-pane">
                                                <label>Phân giải AI</label>
                                                <select v-model="cam.resolution" class="sleek-select text-sm">
                                                    <option value="1080p">FHD 1080p</option>
                                                    <option value="720p">HD 720p</option>
                                                    <option value="480p">SD 480p</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recognition Settings -->
                    <div v-else-if="activeTab === 'recognition'" key="recognition" class="settings-section">
                        <div class="bento-card mb-4">
                            <h2 class="bento-title mb-4 flex-center gap-2">
                                <span class="icon-box blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 0-10 10c0 5.52 4.48 10 10 10s10-4.48 10-10A10 10 0 0 0 12 2z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg></span>
                                Nhận diện Khuôn mặt (Face ID)
                            </h2>
                            
                            <div class="toggle-list">
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Kích hoạt Face ID Engine</span>
                                        <span class="t-desc">Phân tích luồng video và đối chiếu CSDL trong thời gian thực</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="recognitionSettings.faceEnabled" />
                                        <span class="toggle-track"></span>
                                    </label>
                                </div>
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Công nghệ liveness (Anti-spoofing)</span>
                                        <span class="t-desc">Chống giả mạo qua hình ảnh tĩnh, video phát lại qua điện thoại</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="recognitionSettings.antiSpoofing" />
                                        <span class="toggle-track"></span>
                                    </label>
                                </div>
                                <div class="slider-item mt-2">
                                    <div class="slider-header flex-between mb-2">
                                        <label class="t-label font-medium mb-0">Ngưỡng tin cậy (Confidence Threshold)</label>
                                        <span class="slider-val text-primary font-bold">{{ recognitionSettings.faceThreshold }}%</span>
                                    </div>
                                    <input v-model.number="recognitionSettings.faceThreshold" type="range" min="50" max="100" class="modern-range" />
                                    <div class="flex-between text-xs text-muted mt-1"><span>Linh hoạt (50%)</span><span>Nghiêm ngặt (100%)</span></div>
                                </div>
                            </div>
                        </div>

                        <div class="bento-card">
                            <h2 class="bento-title mb-4 flex-center gap-2">
                                <span class="icon-box purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="8" width="18" height="8" rx="2" ry="2"/><line x1="7" y1="12" x2="7.01" y2="12"/><path d="M12 12h4"/></svg></span>
                                Nhận diện Biển số (LPR)
                            </h2>
                            
                            <div class="toggle-list">
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Kích hoạt LPR Engine</span>
                                        <span class="t-desc">Hỗ trợ nhận diện tự động ô tô/xe máy với biển số Việt Nam</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="recognitionSettings.plateEnabled" />
                                        <span class="toggle-track"></span>
                                    </label>
                                </div>
                                <div class="slider-item mt-2">
                                    <div class="slider-header flex-between mb-2">
                                        <label class="t-label font-medium mb-0">Ngưỡng tin cậy LPR</label>
                                        <span class="slider-val text-purple font-bold">{{ recognitionSettings.plateThreshold }}%</span>
                                    </div>
                                    <input v-model.number="recognitionSettings.plateThreshold" type="range" min="50" max="100" class="modern-range purple-range" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Notification Settings -->
                    <div v-else-if="activeTab === 'notifications'" key="notifications" class="settings-section">
                        <div class="bento-card">
                            <h2 class="bento-title mb-1">Cảnh báo & Giao tiếp</h2>
                            <p class="text-secondary text-sm mb-4">Thiết lập các Rule cảnh báo hành vi ngoại lệ</p>

                            <div class="toggle-list">
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Khuôn mặt người lạ (Stranger Alert)</span>
                                        <span class="t-desc">Gửi cảnh báo nếu có đối tượng lảng vảng khuôn viên không có trong DB</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="notifSettings.strangerAlert" />
                                        <span class="toggle-track warning"></span>
                                    </label>
                                </div>
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Phương tiện không đăng ký</span>
                                        <span class="t-desc">Cảnh báo khi cổng vào mở cho một xe chui lọt lưới trái phép</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="notifSettings.unregisteredVehicle" />
                                        <span class="toggle-track danger"></span>
                                    </label>
                                </div>
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Mất dòng Video (Camera Offline)</span>
                                        <span class="t-desc">Kích hoạt lỗi Critical ngay khi RTSP drop hoặc camera đóng điện</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="notifSettings.cameraOffline" />
                                        <span class="toggle-track danger"></span>
                                    </label>
                                </div>
                                <div class="toggle-item">
                                    <div class="toggle-text">
                                        <span class="t-label">Xâm nhập ngoài giờ (After-hours)</span>
                                        <span class="t-desc">Cảnh báo bất kỳ check-in/out nào ngoài cung giờ mở cửa thiết lập ở tab Chung</span>
                                    </div>
                                    <label class="modern-toggle lg">
                                        <input type="checkbox" v-model="notifSettings.afterHours" />
                                        <span class="toggle-track warning"></span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </transition>
            </div>
        </div>
        
        <!-- Toast UI -->
        <transition name="toast-slide">
            <div v-if="toast" class="modern-toast success">
                <div class="toast-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <span>{{ toast.message }}</span>
            </div>
        </transition>

    </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('general')

const tabs = [
    { id: 'general', label: 'Cài đặt chung', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' },
    { id: 'camera', label: 'Mạng lưới Camera', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>' },
    { id: 'recognition', label: 'Hệ thống AI', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
    { id: 'notifications', label: 'Cảnh báo tự động', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>' },
]

const settings = ref({
    companyName: 'V-Shield Security Group',
    openTime: '06:00',
    closeTime: '22:00',
    language: 'vi',
    timezone: 'UTC+7',
})

const cameraSettings = ref([
    { id: 1, name: 'CAM-01 (Gate Alpha)', url: 'rtsp://10.0.1.11:554/cam/realmonitor', location: 'Cổng chính - Luồng vào', online: true, enabled: true, recognitionType: 'both', resolution: '1080p' },
    { id: 2, name: 'CAM-02 (Gate Beta)', url: 'rtsp://10.0.1.12:554/cam/realmonitor', location: 'Cổng phụ - Luồng ra', online: true, enabled: true, recognitionType: 'plate', resolution: '1080p' },
    { id: 3, name: 'CAM-03 (Lobby Front)', url: 'rtsp://10.0.1.13:554/cam/realmonitor', location: 'Cửa xoay sảnh chính', online: true, enabled: true, recognitionType: 'face', resolution: '720p' },
    { id: 4, name: 'CAM-04 (Basement B1)', url: 'rtsp://10.0.1.14:554/cam/realmonitor', location: 'Hầm gửi xe B1', online: false, enabled: false, recognitionType: 'plate', resolution: '720p' },
])

const recognitionSettings = ref({
    faceEnabled: true,
    faceThreshold: 88,
    antiSpoofing: true,
    plateEnabled: true,
    plateThreshold: 85,
})

const notifSettings = ref({
    strangerAlert: true,
    unregisteredVehicle: true,
    cameraOffline: true,
    afterHours: false,
})

const toast = ref(null)
let toastTimer = null

const saveSettings = () => {
    if(toastTimer) clearTimeout(toastTimer)
    toast.value = { message: 'Đã lưu cấu hình hệ thống thành công!' }
    toastTimer = setTimeout(() => { toast.value = null }, 3500)
}
</script>

<style scoped>
/* Layout */
.bento-header { margin-bottom: 24px; padding: 0 4px; display: flex; justify-content: space-between; align-items: center; }
.bento-header .greeting h1 { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
.bento-header .greeting p { color: var(--text-secondary); font-size: 0.95rem; }

.settings-layout { display: grid; grid-template-columns: 260px 1fr; gap: 24px; align-items: start; }

/* Navigation Sidebar */
.settings-nav { padding: 12px; position: sticky; top: calc(var(--header-height) + 24px); display: flex; flex-direction: column; gap: 4px;}
.settings-tab { display: flex; align-items: center; gap: 14px; width: 100%; padding: 14px 16px; background: transparent; border: none; color: var(--text-secondary); border-radius: 12px; font-size: 0.95rem; font-weight: 600; transition: all 0.2s; text-align: left; cursor: pointer; }
.settings-tab:hover { background: var(--bg-card-hover); color: var(--text-primary); }
.settings-tab.active { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); box-shadow: inset 4px 0 0 var(--accent-primary);}
.tab-icon { width: 22px; height: 22px; flex-shrink: 0;}
.tab-icon :deep(svg) { width: 100%; height: 100%; }

/* Card Components */
.bento-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--border-radius-lg); padding: 24px; }
.bento-title { font-size: 1.15rem; font-weight: 700; color: var(--text-primary); margin: 0; }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.text-sm { font-size: 0.85rem; }
.text-xs { font-size: 0.75rem; }
.mb-1 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 24px; }
.mb-2 { margin-bottom: 12px; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 16px; }

/* Forms */
.form-grid { display: flex; flex-direction: column; gap: 20px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.input-pane { display: flex; flex-direction: column; gap: 8px; }
.input-pane label { font-size: 0.9rem; font-weight: 500; color: var(--text-secondary); }

.sleek-input, .sleek-select { width: 100%; padding: 12px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); outline: none; transition: border 0.2s; font-size: 0.95rem; }
.sleek-input:focus, .sleek-select:focus { border-color: var(--accent-primary); box-shadow: 0 0 0 3px rgba(16, 121, 196, 0.15); }
.text-mono { font-family: 'JetBrains Mono', monospace; }

/* Camera Grid */
.camera-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.cam-card { padding: 20px; transition: transform 0.2s, box-shadow 0.2s; }
.cam-card:hover { border-color: rgba(16, 121, 196,0.3); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.cam-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed var(--border-color); }
.cam-info h4 { font-size: 1.05rem; font-weight: 600; margin: 0 0 6px 0; color: var(--text-primary);}
.cam-form { display: flex; flex-direction: column; gap: 16px; }

/* Status Badges */
.status-pill.minimal { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid transparent; letter-spacing: 0.5px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600;}
.status-pill.active { background: rgba(16, 185, 129, 0.05); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }
.status-pill.inactive { background: rgba(239, 68, 68, 0.05); color: var(--accent-danger); border-color: rgba(239, 68, 68, 0.2); }
.pill-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* Icon Boxes */
.flex-center { display: flex; align-items: center; }
.gap-2 { gap: 12px; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.icon-box { width: 32px; height: 32px; border-radius: 8px; display: flex; justify-content: center; align-items: center; }
.icon-box.blue { background: rgba(16, 121, 196, 0.1); color: var(--accent-primary); }
.icon-box.purple { background: rgba(168, 85, 247, 0.1); color: #a855f7; }
.icon-box svg { width: 18px; height: 18px; }
.text-purple { color: #a855f7; }
.font-medium { font-weight: 500; }
.font-bold { font-weight: 700; }

/* Toggle List */
.toggle-list { display: flex; flex-direction: column; gap: 16px; }
.toggle-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: var(--bg-input); border-radius: 12px; border: 1px solid var(--border-color); transition: background 0.2s; }
.toggle-item:hover { background: var(--bg-card-hover); }
.toggle-text { display: flex; flex-direction: column; gap: 4px; padding-right: 20px;}
.t-label { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); }
.t-desc { font-size: 0.8rem; color: var(--text-secondary); }

/* Modern Modern Toggle Switch */
.modern-toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.modern-toggle.lg { width: 50px; height: 28px; }
.modern-toggle input { opacity: 0; width: 0; height: 0; }
.toggle-track { position: absolute; cursor: pointer; inset: 0; background: rgba(255,255,255,0.1); border-radius: 34px; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); border: 1px solid var(--border-color); }
.toggle-track::before { content: ''; position: absolute; height: 18px; width: 18px; left: 2px; bottom: 2px; background: #94a3b8; border-radius: 50%; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.modern-toggle.lg .toggle-track::before { height: 20px; width: 20px; left: 3px; bottom: 3px;}

.modern-toggle input:checked + .toggle-track { background: var(--accent-primary); border-color: var(--accent-primary); }
.modern-toggle input:checked + .toggle-track.warning { background: var(--accent-warning); border-color: var(--accent-warning); }
.modern-toggle input:checked + .toggle-track.danger { background: var(--accent-danger); border-color: var(--accent-danger); }
.modern-toggle input:checked + .toggle-track::before { transform: translateX(20px); background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.2);}
.modern-toggle.lg input:checked + .toggle-track::before { transform: translateX(22px); }

/* Modern Ranges */
.slider-item { padding: 0 4px; }
.modern-range { -webkit-appearance: none; appearance: none; width: 100%; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; outline: none; transition: 0.2s; border: 1px solid rgba(255,255,255,0.05);}
.modern-range::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 20px; height: 20px; background: var(--accent-primary); border-radius: 50%; cursor: pointer; box-shadow: 0 0 10px rgba(16, 121, 196,0.6); border: 2px solid #fff; transition: transform 0.1s;}
.modern-range::-webkit-slider-thumb:hover { transform: scale(1.1); }
.purple-range::-webkit-slider-thumb { background: #a855f7; box-shadow: 0 0 10px rgba(168,85,247,0.6); }

/* Fade Transtions */
.fade-up-enter-active, .fade-up-leave-active { transition: all 0.3s ease; }
.fade-up-enter-from { opacity: 0; transform: translateY(10px); }
.fade-up-leave-to { opacity: 0; transform: translateY(-10px); }

/* Toast */
.modern-toast { position: fixed; bottom: 32px; right: 32px; padding: 14px 20px; border-radius: 12px; font-size: 0.95rem; font-weight: 500; z-index: 9999; box-shadow: var(--shadow-xl); display: flex; align-items: center; gap: 12px; border: 1px solid rgba(255,255,255,0.1); background: var(--bg-card); color: var(--text-primary); }
.toast-icon svg { width: 22px; height: 22px; }
.modern-toast.success .toast-icon { color: var(--accent-success); }
.toast-slide-enter-active, .toast-slide-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.toast-slide-enter-from, .toast-slide-leave-to { opacity: 0; transform: translateY(30px) scale(0.9); }

@media (max-width: 1024px) {
    .settings-layout { grid-template-columns: 220px 1fr; }
    .camera-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
    .settings-layout { grid-template-columns: 1fr; }
    .settings-nav { position: static; flex-direction: row; overflow-x: auto; padding: 8px; border-radius: 8px; gap: 8px;}
    .settings-tab { white-space: nowrap; padding: 10px 14px;}
    .grid-2 { grid-template-columns: 1fr; }
    .bento-header { flex-direction: column; align-items: flex-start; gap: 16px; }
    .header-actions { width: 100%; display: flex; justify-content: flex-end;}
}
</style>
