<template>
    <div class="page-container animate-in">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h1 class="page-title">Giám sát Camera</h1>
                <p class="page-subtitle">Theo dõi camera trực tiếp và nhận dạng tự động</p>
            </div>
            <div class="header-actions">
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    LIVE
                </div>
                <select v-model="layoutMode" class="filter-select" style="min-width: 140px;">
                    <option value="2x2">2 × 2</option>
                    <option value="3x2">3 × 2</option>
                    <option value="1x1">Toàn màn hình</option>
                </select>
            </div>
        </div>

        <!-- Camera Grid -->
        <div class="camera-grid" :class="layoutMode">
            <div v-for="cam in cameras" :key="cam.id" class="camera-card" :class="{ offline: !cam.online }">
                <div class="camera-feed">
                    <div v-if="cam.online" class="camera-placeholder">
                        <div class="camera-animation">
                            <div class="scan-line"></div>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
                                class="camera-watermark">
                                <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                                <circle cx="12" cy="13" r="4" />
                            </svg>
                        </div>
                    </div>
                    <div v-else class="camera-offline">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                            style="width: 40px; height: 40px; opacity: 0.3;">
                            <path
                                d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <p>Mất kết nối</p>
                    </div>

                    <!-- Overlay Info -->
                    <div class="camera-overlay">
                        <div class="camera-top-bar">
                            <span class="camera-name">{{ cam.name }}</span>
                            <span class="camera-status" :class="{ online: cam.online }">
                                <span class="status-dot"></span>
                                {{ cam.online ? 'Online' : 'Offline' }}
                            </span>
                        </div>
                        <div class="camera-bottom-bar">
                            <span class="camera-location">{{ cam.location }}</span>
                            <span class="camera-time">{{ cam.online ? currentTime : '—' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Recognitions -->
        <div class="recognitions-section">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Nhận dạng gần đây</h3>
                    <span class="badge info">{{ recognitions.length }} kết quả</span>
                </div>
                <div class="recognition-grid">
                    <div v-for="rec in recognitions" :key="rec.id" class="recognition-card">
                        <div class="rec-avatar" :class="rec.type">
                            {{ rec.initials }}
                        </div>
                        <div class="rec-info">
                            <span class="rec-name">{{ rec.name }}</span>
                            <span class="rec-detail">{{ rec.detail }}</span>
                        </div>
                        <div class="rec-meta">
                            <span class="badge" :class="rec.action">
                                <span class="badge-dot"></span>
                                {{ rec.action === 'check-in' ? 'Vào' : 'Ra' }}
                            </span>
                            <span class="rec-time">{{ rec.time }}</span>
                            <span class="rec-confidence" :class="getConfidenceClass(rec.confidence)">
                                {{ rec.confidence }}%
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const layoutMode = ref('2x2')
const currentTime = ref('')

let timer = null

const updateTime = () => {
    currentTime.value = new Date().toLocaleTimeString('vi-VN')
}

onMounted(() => {
    updateTime()
    timer = setInterval(updateTime, 1000)
})

onUnmounted(() => clearInterval(timer))

const cameras = ref([
    { id: 1, name: 'CAM-01', location: 'Cổng A - Trước', online: true },
    { id: 2, name: 'CAM-02', location: 'Cổng A - Sau', online: true },
    { id: 3, name: 'CAM-03', location: 'Cổng B - Trước', online: true },
    { id: 4, name: 'CAM-04', location: 'Cổng B - Sau', online: false },
    { id: 5, name: 'CAM-05', location: 'Bãi xe A', online: true },
    { id: 6, name: 'CAM-06', location: 'Bãi xe B', online: true },
])

const recognitions = ref([
    { id: 1, name: 'Nguyễn Văn An', initials: 'NA', detail: 'CAM-01 · Biển số 51A-123.45', type: 'face', action: 'check-in', time: '08:05', confidence: 98 },
    { id: 2, name: 'Xe 30H-567.89', initials: '30H', detail: 'CAM-02 · LPR Detection', type: 'plate', action: 'check-out', time: '08:20', confidence: 95 },
    { id: 3, name: 'Trần Thị Bình', initials: 'TB', detail: 'CAM-03 · Face Recognition', type: 'face', action: 'check-in', time: '08:12', confidence: 99 },
    { id: 4, name: 'Xe 51B-234.56', initials: '51B', detail: 'CAM-01 · LPR Detection', type: 'plate', action: 'check-in', time: '08:25', confidence: 92 },
    { id: 5, name: 'Phạm Minh Đức', initials: 'PD', detail: 'CAM-01 · Face Recognition', type: 'face', action: 'check-in', time: '08:25', confidence: 97 },
    { id: 6, name: 'Unknown Person', initials: '??', detail: 'CAM-03 · Face not recognized', type: 'unknown', action: 'check-in', time: '08:40', confidence: 45 },
])

const getConfidenceClass = (c) => {
    if (c >= 90) return 'high'
    if (c >= 70) return 'medium'
    return 'low'
}
</script>

<style scoped>
.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.live-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: var(--border-radius-sm);
    color: var(--accent-danger);
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.1em;
}

.live-dot {
    width: 8px;
    height: 8px;
    background: var(--accent-danger);
    border-radius: 50%;
    animation: pulse 1.5s infinite;
}

/* Camera Grid */
.camera-grid {
    display: grid;
    gap: 16px;
    margin-bottom: 24px;
}

.camera-grid.\32x2 {
    grid-template-columns: 1fr 1fr;
}

.camera-grid.\33x2 {
    grid-template-columns: 1fr 1fr 1fr;
}

.camera-grid.\31x1 {
    grid-template-columns: 1fr;
}

.camera-card {
    border-radius: var(--border-radius);
    overflow: hidden;
    border: 1px solid var(--border-color);
    transition: all var(--transition-normal);
}

.camera-card:hover {
    border-color: var(--accent-primary);
    box-shadow: var(--shadow-glow);
}

.camera-card.offline {
    opacity: 0.6;
}

.camera-feed {
    position: relative;
    aspect-ratio: 16/9;
    background: #0a0f1e;
    overflow: hidden;
}

.camera-placeholder {
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #0a0f1e 0%, #111d35 50%, #0a0f1e 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.camera-animation {
    width: 100%;
    height: 100%;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

.scan-line {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
    opacity: 0.4;
    animation: scan 3s ease-in-out infinite;
}

@keyframes scan {

    0%,
    100% {
        top: 10%;
    }

    50% {
        top: 90%;
    }
}

.camera-watermark {
    width: 48px;
    height: 48px;
    color: var(--text-muted);
    opacity: 0.2;
}

.camera-offline {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    background: var(--bg-secondary);
}

.camera-offline p {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.camera-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 12px;
    background: linear-gradient(to bottom, rgba(0, 0, 0, 0.5) 0%, transparent 30%, transparent 70%, rgba(0, 0, 0, 0.5) 100%);
}

.camera-top-bar,
.camera-bottom-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.camera-name {
    font-weight: 700;
    font-size: 0.85rem;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.camera-status {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(239, 68, 68, 0.2);
    color: var(--accent-danger);
}

.camera-status.online {
    background: rgba(16, 185, 129, 0.2);
    color: var(--accent-success);
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
}

.camera-location,
.camera-time {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.camera-time {
    font-family: monospace;
    font-weight: 600;
}

/* Recognitions */
.recognitions-section {
    margin-top: 4px;
}

.recognition-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.recognition-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 0;
    border-bottom: 1px solid var(--border-color);
}

.recognition-card:last-child {
    border-bottom: none;
}

.rec-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.75rem;
    flex-shrink: 0;
}

.rec-avatar.face {
    background: rgba(59, 130, 246, 0.15);
    color: var(--accent-primary);
}

.rec-avatar.plate {
    background: rgba(139, 92, 246, 0.15);
    color: var(--accent-secondary);
}

.rec-avatar.unknown {
    background: rgba(239, 68, 68, 0.15);
    color: var(--accent-danger);
}

.rec-info {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.rec-name {
    font-weight: 600;
    font-size: 0.9rem;
}

.rec-detail {
    font-size: 0.78rem;
    color: var(--text-muted);
}

.rec-meta {
    display: flex;
    align-items: center;
    gap: 10px;
}

.rec-time {
    font-size: 0.8rem;
    color: var(--text-secondary);
    font-family: monospace;
}

.rec-confidence {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 10px;
}

.rec-confidence.high {
    background: rgba(16, 185, 129, 0.12);
    color: var(--accent-success);
}

.rec-confidence.medium {
    background: rgba(245, 158, 11, 0.12);
    color: var(--accent-warning);
}

.rec-confidence.low {
    background: rgba(239, 68, 68, 0.12);
    color: var(--accent-danger);
}

@media (max-width: 768px) {

    .camera-grid.\32x2,
    .camera-grid.\33x2 {
        grid-template-columns: 1fr;
    }
}
</style>
