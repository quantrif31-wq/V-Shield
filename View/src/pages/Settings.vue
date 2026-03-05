<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Cài đặt Hệ thống</h1>
                <p class="page-subtitle">Cấu hình hệ thống V-Shield</p>
            </div>
        </div>

        <div class="settings-layout">
            <!-- Sidebar -->
            <div class="settings-nav">
                <button v-for="tab in tabs" :key="tab.id" class="settings-tab" :class="{ active: activeTab === tab.id }"
                    @click="activeTab = tab.id">
                    <span class="tab-icon" v-html="tab.icon"></span>
                    <span>{{ tab.label }}</span>
                </button>
            </div>

            <!-- Content -->
            <div class="settings-content">
                <!-- General Settings -->
                <div v-if="activeTab === 'general'" class="settings-section">
                    <h2 class="section-heading">Cài đặt chung</h2>
                    <p class="section-desc">Cấu hình thông tin cơ bản của hệ thống</p>

                    <div class="settings-card">
                        <div class="form-group">
                            <label>Tên công ty</label>
                            <input v-model="settings.companyName" type="text" />
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Giờ mở cổng</label>
                                <input v-model="settings.openTime" type="time" />
                            </div>
                            <div class="form-group">
                                <label>Giờ đóng cổng</label>
                                <input v-model="settings.closeTime" type="time" />
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Ngôn ngữ</label>
                            <select v-model="settings.language">
                                <option value="vi">Tiếng Việt</option>
                                <option value="en">English</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Múi giờ</label>
                            <select v-model="settings.timezone">
                                <option value="UTC+7">UTC+7 (Việt Nam)</option>
                                <option value="UTC+8">UTC+8 (Singapore)</option>
                                <option value="UTC+9">UTC+9 (Japan)</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Camera Settings -->
                <div v-if="activeTab === 'camera'" class="settings-section">
                    <h2 class="section-heading">Cài đặt Camera</h2>
                    <p class="section-desc">Quản lý kết nối và cấu hình camera</p>

                    <div v-for="cam in cameraSettings" :key="cam.id" class="settings-card camera-setting-card">
                        <div class="cam-header">
                            <div class="cam-info">
                                <h4>{{ cam.name }}</h4>
                                <span class="badge" :class="cam.online ? 'active' : 'inactive'">
                                    <span class="badge-dot"></span>
                                    {{ cam.online ? 'Online' : 'Offline' }}
                                </span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="cam.enabled" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>URL Stream</label>
                                <input v-model="cam.url" type="text" />
                            </div>
                            <div class="form-group">
                                <label>Vị trí</label>
                                <input v-model="cam.location" type="text" />
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Loại nhận dạng</label>
                                <select v-model="cam.recognitionType">
                                    <option value="face">Khuôn mặt</option>
                                    <option value="plate">Biển số xe</option>
                                    <option value="both">Cả hai</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Độ phân giải</label>
                                <select v-model="cam.resolution">
                                    <option value="1080p">1080p</option>
                                    <option value="720p">720p</option>
                                    <option value="480p">480p</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recognition Settings -->
                <div v-if="activeTab === 'recognition'" class="settings-section">
                    <h2 class="section-heading">Nhận dạng AI</h2>
                    <p class="section-desc">Cấu hình nhận dạng khuôn mặt và biển số xe</p>

                    <div class="settings-card">
                        <h4 style="margin-bottom: 16px; font-size: 1rem;">Nhận dạng khuôn mặt</h4>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Bật nhận dạng khuôn mặt</span>
                                <span class="setting-desc">Tự động nhận dạng nhân viên qua camera</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="recognitionSettings.faceEnabled" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Ngưỡng tin cậy (%)</label>
                            <input v-model.number="recognitionSettings.faceThreshold" type="range" min="50" max="100"
                                class="range-input" />
                            <span class="range-value">{{ recognitionSettings.faceThreshold }}%</span>
                        </div>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Anti-spoofing</span>
                                <span class="setting-desc">Phát hiện ảnh giả mạo</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="recognitionSettings.antiSpoofing" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>

                    <div class="settings-card" style="margin-top: 16px;">
                        <h4 style="margin-bottom: 16px; font-size: 1rem;">Nhận dạng biển số xe (LPR)</h4>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Bật nhận dạng biển số</span>
                                <span class="setting-desc">Tự động đọc biển số xe qua camera</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="recognitionSettings.plateEnabled" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="form-group">
                            <label>Ngưỡng tin cậy (%)</label>
                            <input v-model.number="recognitionSettings.plateThreshold" type="range" min="50" max="100"
                                class="range-input" />
                            <span class="range-value">{{ recognitionSettings.plateThreshold }}%</span>
                        </div>
                    </div>
                </div>

                <!-- Notification Settings -->
                <div v-if="activeTab === 'notifications'" class="settings-section">
                    <h2 class="section-heading">Thông báo</h2>
                    <p class="section-desc">Cấu hình cảnh báo và thông báo</p>

                    <div class="settings-card">
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Người lạ được phát hiện</span>
                                <span class="setting-desc">Thông báo khi phát hiện người không đăng ký</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="notifSettings.strangerAlert" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Xe không đăng ký</span>
                                <span class="setting-desc">Cảnh báo phương tiện chưa đăng ký</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="notifSettings.unregisteredVehicle" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Camera mất kết nối</span>
                                <span class="setting-desc">Thông báo khi camera offline</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="notifSettings.cameraOffline" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="setting-toggle-item">
                            <div>
                                <span class="setting-label">Check-in ngoài giờ</span>
                                <span class="setting-desc">Phát hiện ra/vào ngoài giờ làm việc</span>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" v-model="notifSettings.afterHours" />
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Save Button -->
                <div class="settings-footer">
                    <button class="btn btn-secondary">Hủy bỏ</button>
                    <button class="btn btn-primary" @click="saveSettings">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width: 16px; height: 16px;">
                            <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
                            <polyline points="17 21 17 13 7 13 7 21" />
                            <polyline points="7 3 7 8 15 8" />
                        </svg>
                        Lưu cài đặt
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('general')

const tabs = [
    { id: 'general', label: 'Cài đặt chung', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' },
    { id: 'camera', label: 'Camera', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>' },
    { id: 'recognition', label: 'Nhận dạng AI', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
    { id: 'notifications', label: 'Thông báo', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>' },
]

const settings = ref({
    companyName: 'V-Shield Corp.',
    openTime: '06:00',
    closeTime: '22:00',
    language: 'vi',
    timezone: 'UTC+7',
})

const cameraSettings = ref([
    { id: 1, name: 'CAM-01', url: 'rtsp://192.168.1.101:554/stream', location: 'Cổng A - Trước', online: true, enabled: true, recognitionType: 'both', resolution: '1080p' },
    { id: 2, name: 'CAM-02', url: 'rtsp://192.168.1.102:554/stream', location: 'Cổng A - Sau', online: true, enabled: true, recognitionType: 'plate', resolution: '1080p' },
    { id: 3, name: 'CAM-03', url: 'rtsp://192.168.1.103:554/stream', location: 'Cổng B - Trước', online: true, enabled: true, recognitionType: 'face', resolution: '720p' },
    { id: 4, name: 'CAM-04', url: 'rtsp://192.168.1.104:554/stream', location: 'Cổng B - Sau', online: false, enabled: false, recognitionType: 'plate', resolution: '720p' },
])

const recognitionSettings = ref({
    faceEnabled: true,
    faceThreshold: 85,
    antiSpoofing: true,
    plateEnabled: true,
    plateThreshold: 80,
})

const notifSettings = ref({
    strangerAlert: true,
    unregisteredVehicle: true,
    cameraOffline: true,
    afterHours: false,
})

const saveSettings = () => {
    alert('Cài đặt đã được lưu thành công!')
}
</script>

<style scoped>
.settings-layout {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 24px;
    align-items: start;
}

.settings-nav {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 8px;
    position: sticky;
    top: calc(var(--header-height) + 24px);
}

.settings-tab {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 12px 16px;
    background: transparent;
    color: var(--text-secondary);
    border-radius: var(--border-radius-sm);
    font-size: 0.9rem;
    font-weight: 500;
    transition: all var(--transition-fast);
    text-align: left;
}

.settings-tab:hover {
    background: rgba(59, 130, 246, 0.06);
    color: var(--text-primary);
}

.settings-tab.active {
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent-primary);
}

.tab-icon {
    display: flex;
    align-items: center;
    width: 20px;
    height: 20px;
}

.section-heading {
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 4px;
}

.section-desc {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 20px;
}

.settings-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 24px;
}

.camera-setting-card {
    margin-bottom: 16px;
}

.cam-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.cam-info {
    display: flex;
    align-items: center;
    gap: 10px;
}

.cam-info h4 {
    font-size: 1rem;
    font-weight: 600;
}

/* Toggle Switch */
.toggle-switch {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
}

.toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.toggle-slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background: var(--bg-input);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    transition: all var(--transition-normal);
}

.toggle-slider::before {
    content: '';
    position: absolute;
    height: 18px;
    width: 18px;
    left: 2px;
    bottom: 2px;
    background: var(--text-secondary);
    border-radius: 50%;
    transition: all var(--transition-normal);
}

.toggle-switch input:checked+.toggle-slider {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
}

.toggle-switch input:checked+.toggle-slider::before {
    transform: translateX(20px);
    background: #fff;
}

/* Setting Toggle Item */
.setting-toggle-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid var(--border-color);
}

.setting-toggle-item:last-child {
    border-bottom: none;
}

.setting-label {
    font-weight: 600;
    font-size: 0.9rem;
    display: block;
}

.setting-desc {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 2px;
    display: block;
}

/* Range Input */
.range-input {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 6px;
    background: var(--bg-input);
    border-radius: 3px;
    outline: none;
    margin-top: 8px;
}

.range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    background: var(--accent-primary);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
}

.range-value {
    display: inline-block;
    margin-top: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--accent-primary);
}

/* Footer */
.settings-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
    .settings-layout {
        grid-template-columns: 1fr;
    }

    .settings-nav {
        position: static;
        display: flex;
        overflow-x: auto;
        gap: 4px;
    }

    .settings-tab {
        white-space: nowrap;
    }
}
</style>
