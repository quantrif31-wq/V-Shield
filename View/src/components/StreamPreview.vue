<template>
    <div class="stream-preview" :class="[`mode-${playerMode}`, { loading: isLoading }]">
        <img
            v-if="playerMode === 'image'"
            :src="resolvedUrl"
            :alt="label"
            class="stream-media"
            @load="handleReady"
            @error="handleError('Khong tai duoc anh preview tu camera.')"
        />

        <video
            v-else-if="playerMode === 'video' || playerMode === 'hls'"
            ref="videoRef"
            class="stream-media"
            controls
            autoplay
            muted
            playsinline
            @loadeddata="handleReady"
            @error="handleError('Khong tai duoc luong video tren trinh duyet.')"
        ></video>

        <div v-else-if="playerMode === 'rtsp'" class="preview-message">
            <strong>RTSP da san sang cho AI</strong>
            <p>Trinh duyet khong phat truc tiep RTSP. Hay them Preview URL dang HLS/WebRTC/MJPEG de xem tren web.</p>
        </div>

        <div v-else-if="playerMode === 'empty'" class="preview-message">
            <strong>Chua co preview</strong>
            <p>Hay nhap URL xem tren web trong phan quan ly camera de hien thi tai day.</p>
        </div>

        <div v-else class="preview-message">
            <strong>Khong ho tro xem truc tiep</strong>
            <p>{{ errorMessage || 'URL nay can mot bridge de chuyen sang dinh dang trinh duyet phat duoc.' }}</p>
        </div>

        <div v-if="isLoading" class="preview-overlay">Dang tai stream...</div>
        <div v-else-if="errorMessage && playerMode !== 'unsupported'" class="preview-overlay error">{{ errorMessage }}</div>
    </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { isBrowserVideoCameraUrl, isHlsCameraUrl, isHttpCameraUrl, isRtspCameraUrl } from '../utils/cameraNetwork'

const props = defineProps({
    url: {
        type: String,
        default: '',
    },
    label: {
        type: String,
        default: 'Camera preview',
    },
})

const HLS_SCRIPT_SRC = 'https://cdn.jsdelivr.net/npm/hls.js@1/dist/hls.min.js'

let hlsScriptPromise

const videoRef = ref(null)
const errorMessage = ref('')
const isLoading = ref(false)
let hlsInstance = null

const resolvedUrl = computed(() => String(props.url || '').trim())

const playerMode = computed(() => {
    const url = resolvedUrl.value
    if (!url) return 'empty'
    if (isHlsCameraUrl(url)) return 'hls'
    if (isBrowserVideoCameraUrl(url)) return 'video'
    if (isRtspCameraUrl(url)) return 'rtsp'
    if (isHttpCameraUrl(url)) return 'image'
    return 'unsupported'
})

const resetVideoElement = () => {
    const element = videoRef.value
    if (!element) return
    element.pause()
    element.removeAttribute('src')
    element.load()
}

const destroyHls = () => {
    if (hlsInstance) {
        hlsInstance.destroy()
        hlsInstance = null
    }
}

const resetState = () => {
    destroyHls()
    resetVideoElement()
    errorMessage.value = ''
    isLoading.value = false
}

const handleReady = () => {
    errorMessage.value = ''
    isLoading.value = false
}

const handleError = (message) => {
    errorMessage.value = message
    isLoading.value = false
}

const ensureHlsLibrary = async () => {
    if (window.Hls) return window.Hls

    if (!hlsScriptPromise) {
        hlsScriptPromise = new Promise((resolve, reject) => {
            const existing = document.querySelector(`script[src="${HLS_SCRIPT_SRC}"]`)
            if (existing) {
                existing.addEventListener('load', () => resolve(window.Hls), { once: true })
                existing.addEventListener('error', () => reject(new Error('Khong tai duoc HLS player.')), { once: true })
                return
            }

            const script = document.createElement('script')
            script.src = HLS_SCRIPT_SRC
            script.async = true
            script.onload = () => resolve(window.Hls)
            script.onerror = () => reject(new Error('Khong tai duoc HLS player.'))
            document.head.appendChild(script)
        })
    }

    return hlsScriptPromise
}

const attachVideoPreview = async () => {
    await nextTick()
    const element = videoRef.value
    if (!element) return

    resetVideoElement()
    errorMessage.value = ''
    isLoading.value = true
    element.src = resolvedUrl.value
    try {
        await element.play()
    } catch {
        // Browser autoplay can fail silently; controls remain available.
    }
}

const attachHlsPreview = async () => {
    await nextTick()
    const element = videoRef.value
    if (!element) return

    resetVideoElement()
    errorMessage.value = ''
    isLoading.value = true

    if (element.canPlayType('application/vnd.apple.mpegurl')) {
        element.src = resolvedUrl.value
        try {
            await element.play()
        } catch {
            // Browser autoplay can fail silently; controls remain available.
        }
        return
    }

    try {
        const Hls = await ensureHlsLibrary()
        if (!Hls?.isSupported?.()) {
            handleError('Trinh duyet nay khong ho tro HLS player.')
            return
        }

        hlsInstance = new Hls({
            enableWorker: true,
            lowLatencyMode: true,
        })

        hlsInstance.on(Hls.Events.ERROR, (_, data) => {
            if (data?.fatal) {
                handleError('Khong mo duoc luong HLS tu camera.')
            }
        })

        hlsInstance.loadSource(resolvedUrl.value)
        hlsInstance.attachMedia(element)
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, async () => {
            try {
                await element.play()
            } catch {
                // Browser autoplay can fail silently; controls remain available.
            }
        })
    } catch (error) {
        handleError(error instanceof Error ? error.message : 'Khong tai duoc HLS player.')
    }
}

const attachPreview = async () => {
    resetState()

    if (playerMode.value === 'video') {
        await attachVideoPreview()
        return
    }

    if (playerMode.value === 'hls') {
        await attachHlsPreview()
    }
}

watch(
    () => resolvedUrl.value,
    async () => {
        await attachPreview()
    },
    { immediate: true }
)

onBeforeUnmount(() => {
    resetState()
})
</script>

<style scoped>
.stream-preview {
    position: relative;
    min-height: 220px;
    border-radius: 18px;
    overflow: hidden;
    background:
        radial-gradient(circle at top left, rgba(31, 94, 143, 0.22), transparent 48%),
        linear-gradient(140deg, #0f172a, #12263f 60%, #17324d);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stream-media {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    background: rgba(15, 23, 42, 0.92);
}

.preview-message {
    display: grid;
    gap: 10px;
    min-height: 220px;
    align-content: center;
    padding: 22px;
    color: rgba(226, 232, 240, 0.94);
}

.preview-message strong {
    font-size: 1rem;
}

.preview-message p {
    color: rgba(191, 209, 229, 0.88);
    line-height: 1.5;
}

.preview-overlay {
    position: absolute;
    right: 12px;
    bottom: 12px;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.7);
    color: #e2e8f0;
    font-size: 0.78rem;
    font-weight: 700;
    backdrop-filter: blur(8px);
}

.preview-overlay.error {
    left: 12px;
    right: 12px;
    border-radius: 14px;
    background: rgba(127, 29, 29, 0.88);
    color: #fee2e2;
}
</style>
