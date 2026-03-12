<template>
    <div class="page-container animate-in">
        <!-- Minimalist Header -->
        <header class="page-header bento-header">
            <div class="greeting">
                <h1 class="page-title">Giám sát Camera</h1>
                <p class="page-subtitle">Theo dõi luồng video trực tiếp & nhận diện tự động</p>
            </div>
            <div class="header-actions">
                <div class="live-indicator">
                    <span class="live-dot"></span>
                    <span class="live-txt">LIVE</span>
                </div>
                <select v-model="layoutMode" class="minimal-select layout-select">
                    <option value="2x2">Hiển thị: 2 × 2</option>
                    <option value="3x2">Hiển thị: 3 × 2</option>
                    <option value="1x1">Toàn màn hình</option>
                </select>
            </div>
        </header>

        <!-- Camera Grid -->
        <div class="camera-grid" :class="layoutMode">
            <div v-for="cam in cameras" :key="cam.id" class="bento-card camera-card" :class="{ offline: !cam.online }">
                <div class="camera-feed">
                    <div v-if="cam.online" class="camera-placeholder">
                        <div class="camera-animation">
                            <div class="scan-line"></div>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="camera-watermark">
                                <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                                <circle cx="12" cy="13" r="4" />
                            </svg>
                        </div>
                    </div>
                    <div v-else class="camera-offline">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M16.5 9.4l-9-5.19M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                        <p>Mất kết nối tín hiệu</p>
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
                            <span class="camera-location flex-center gap-1">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px; height:12px"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                                {{ cam.location }}
                            </span>
                            <span class="camera-time">{{ cam.online ? currentTime : '—' }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Recognitions in Bento Card -->
        <div class="bento-card recognitions-section mt-4">
            <div class="bento-header-mini">
                <h3 class="bento-title">Nhận dạng AI gần đây</h3>
                <span class="badge minimal">{{ recognitions.length }} kết quả</span>
            </div>
            
            <div class="recognition-list">
                <div v-for="rec in recognitions" :key="rec.id" class="recognition-row">
                    <!-- Icon / Avatar -->
                    <div class="rec-avatar" :class="rec.type">
                        {{ rec.initials }}
                    </div>
                    
                    <!-- Main Info -->
                    <div class="rec-core">
                        <span class="rec-name">{{ rec.name }}</span>
                        <span class="rec-detail">{{ rec.detail }}</span>
                    </div>
                    
                    <!-- Action Badge -->
                    <div class="rec-action">
                        <span class="status-pill minimal" :class="rec.action === 'check-in' ? 'check-in' : 'check-out'">
                            <span class="pill-dot"></span>
                            {{ rec.action === 'check-in' ? 'VÀO' : 'RA' }}
                        </span>
                    </div>
                    
                    <!-- Confidence -->
                    <div class="rec-conf">
                        <span class="tl-chip" :class="getConfidenceClass(rec.confidence)">
                            Độ xác tín: {{ rec.confidence }}%
                        </span>
                    </div>

                    <!-- Time -->
                    <div class="rec-time">{{ rec.time }}</div>
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
    { id: 6, name: 'Unknown Person', initials: '??', detail: 'CAM-03 · Không nhận dạng được khuôn mặt', type: 'unknown', action: 'check-in', time: '08:40', confidence: 45 },
])

const getConfidenceClass = (c) => {
    if (c >= 90) return 'high'
    if (c >= 70) return 'medium'
    return 'low'
}
</script>

<style scoped>
/* Page Layout */
.bento-header { margin-bottom: 24px; padding: 0 4px; display: flex; justify-content: space-between; align-items: center; }
.bento-header .greeting h1 { font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
.bento-header .greeting p { color: var(--text-secondary); font-size: 0.95rem; }

.header-actions { display: flex; align-items: center; gap: 16px; }

/* Dashboard Cards */
.bento-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--border-radius-lg); padding: 24px; }
.bento-header-mini { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 16px; margin-bottom: 16px; }
.bento-title { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); margin: 0; }
.badge.minimal { background: var(--bg-input); border: 1px solid var(--border-color); color: var(--text-secondary); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 500;}

/* Live Indicator */
.live-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; color: var(--accent-danger); box-shadow: 0 0 10px rgba(239, 68, 68, 0.15); }
.live-txt { font-weight: 700; font-size: 0.85rem; letter-spacing: 0.5px; }
.live-dot { width: 8px; height: 8px; background: var(--accent-danger); border-radius: 50%; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.7); } 70% { box-shadow: 0 0 0 6px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }

.minimal-select { padding: 8px 14px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); cursor: pointer; outline: none; font-size: 0.9rem;}
.layout-select { min-width: 150px; }

/* Camera Grid System */
.camera-grid { display: grid; gap: 16px; margin-bottom: 24px; transition: all 0.3s; }
.camera-grid.\32x2 { grid-template-columns: repeat(2, 1fr); }
.camera-grid.\33x2 { grid-template-columns: repeat(3, 1fr); }
.camera-grid.\31x1 { grid-template-columns: 1fr; }

.camera-card { padding: 0; overflow: hidden; position: relative; border-radius: 16px; background: var(--bg-card); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(255,255,255,0.05); }
.camera-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); border-color: rgba(16, 121, 196,0.3); }
.camera-card.offline { opacity: 0.7; filter: grayscale(0.5); }

.camera-feed { position: relative; aspect-ratio: 16/9; background: #030712; overflow: hidden; }

/* Camera Graphics */
.camera-placeholder { width: 100%; height: 100%; background: radial-gradient(circle at center, #0f172a 0%, #030712 100%); display: flex; justify-content: center; align-items: center; }
.camera-animation { width: 100%; height: 100%; position: relative; display: flex; align-items: center; justify-content: center; }
.scan-line { position: absolute; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, transparent, rgba(14, 165, 233, 0.5), transparent); animation: scan 3s cubic-bezier(0.4, 0, 0.2, 1) infinite; box-shadow: 0 0 10px rgba(14, 165, 233, 0.5); }
@keyframes scan { 0%, 100% { top: 5%; opacity: 0; } 10% { opacity: 1; } 50% { top: 95%; } 90% { opacity: 1; } }
.camera-watermark { width: 56px; height: 56px; color: var(--accent-primary); opacity: 0.15; filter: drop-shadow(0 0 8px rgba(16, 121, 196,0.5)); }

.camera-offline { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; background: repeating-linear-gradient(45deg, #0f172a, #0f172a 10px, #030712 10px, #030712 20px); }
.camera-offline svg { width: 48px; height: 48px; color: var(--text-muted); opacity: 0.4; }
.camera-offline p { color: var(--text-secondary); font-size: 0.9rem; font-weight: 500; font-style: italic; background: rgba(0,0,0,0.5); padding: 4px 12px; border-radius: 4px;}

/* Overlays */
.camera-overlay { position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: space-between; padding: 14px; background: linear-gradient(to bottom, rgba(0, 0, 0, 0.7) 0%, transparent 20%, transparent 80%, rgba(0, 0, 0, 0.8) 100%); pointer-events: none; }
.camera-top-bar, .camera-bottom-bar { display: flex; justify-content: space-between; align-items: center; }

.camera-name { font-weight: 700; font-size: 0.9rem; color: #fff; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8); letter-spacing: 0.5px;}

.camera-status { display: flex; align-items: center; gap: 6px; font-size: 0.7rem; font-weight: 700; padding: 4px 8px; border-radius: 6px; background: rgba(220, 38, 38, 0.5); color: #fca5a5; backdrop-filter: blur(4px); text-transform: uppercase;}
.camera-status.online { background: rgba(5, 150, 105, 0.5); color: #6ee7b7; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.camera-location { font-size: 0.8rem; color: #e2e8f0; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8); font-weight: 500;}
.camera-time { font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.85rem; color: #fff; text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8); }

/* Recognition List Row Design */
.recognition-list { display: flex; flex-direction: column; gap: 8px; }
.recognition-row { display: flex; align-items: center; gap: 16px; padding: 14px 16px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 12px; transition: background 0.2s; }
.recognition-row:hover { background: var(--bg-card-hover); }

.rec-avatar { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.05);}
.rec-avatar.face { background: linear-gradient(135deg, rgba(16, 121, 196,0.2), rgba(37,99,235,0.2)); color: var(--accent-primary); border-color: rgba(16, 121, 196,0.3); }
.rec-avatar.plate { background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(147,51,234,0.2)); color: #a855f7; border-color: rgba(168,85,247,0.3);}
.rec-avatar.unknown { background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.2)); color: var(--accent-danger); border-color: rgba(239,68,68,0.3);}

.rec-core { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.rec-name { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); }
.rec-detail { font-size: 0.8rem; color: var(--text-secondary); }

.status-pill.minimal { padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid transparent; letter-spacing: 0.5px; display: inline-flex; align-items: center; gap: 6px; font-weight: 600;}
.status-pill.check-in { background: rgba(16, 185, 129, 0.05); color: var(--accent-success); border-color: rgba(16, 185, 129, 0.2); }
.status-pill.check-out { background: rgba(16, 121, 196, 0.05); color: var(--accent-primary); border-color: rgba(16, 121, 196, 0.2); }

.tl-chip { font-size: 0.75rem; font-weight: 600; padding: 4px 10px; border-radius: 6px; letter-spacing: 0.3px; }
.tl-chip.high { background: rgba(16, 185, 129, 0.1); color: var(--accent-success); }
.tl-chip.medium { background: rgba(245, 158, 11, 0.1); color: var(--accent-warning); }
.tl-chip.low { background: rgba(239, 68, 68, 0.1); color: var(--accent-danger); }

.rec-time { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: var(--text-muted); font-weight: 500; min-width: 60px; text-align: right; }

.flex-center { display: flex; align-items: center; }
.gap-1 { gap: 4px; }
.mt-4 { margin-top: 24px; }

@media (max-width: 1024px) {
    .camera-grid.\33x2 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
    .camera-grid.\32x2, .camera-grid.\33x2 { grid-template-columns: 1fr; }
    .recognition-row { flex-wrap: wrap; }
    .rec-time { width: 100%; text-align: left; padding-left: 60px; margin-top: -10px;}
}
</style>
