import { getResolvedLocalApiBaseUrl, requestLocalApi } from "./localApiClient"

const SECURITY_AI_STATUS_TIMEOUT_MS = 12000
const SECURITY_AI_START_TIMEOUT_MS = 120000
const SECURITY_AI_STOP_TIMEOUT_MS = 12000
const SECURITY_AI_ALERTS_TIMEOUT_MS = 12000
const SECURITY_AI_RESULT_TIMEOUT_MS = 12000
const SECURITY_AI_RESET_TIMEOUT_MS = 12000
const SECURITY_AI_SEEK_TIMEOUT_MS = 12000

export async function getSecurityAiStatus() {
    const res = await requestLocalApi({
        method: "get",
        url: "/SecurityAi/status",
        timeout: SECURITY_AI_STATUS_TIMEOUT_MS,
    })
    return res.data
}

export async function startSecurityAi(data) {
    const res = await requestLocalApi({
        method: "post",
        url: "/SecurityAi/start",
        data,
        timeout: SECURITY_AI_START_TIMEOUT_MS,
    })
    return res.data
}

export async function stopSecurityAi() {
    const res = await requestLocalApi({
        method: "post",
        url: "/SecurityAi/stop",
        timeout: SECURITY_AI_STOP_TIMEOUT_MS,
    })
    return res.data
}

export async function resetSecurityAi() {
    const res = await requestLocalApi({
        method: "post",
        url: "/SecurityAi/reset",
        timeout: SECURITY_AI_RESET_TIMEOUT_MS,
    })
    return res.data
}

export async function seekSecurityAi(frameIndex) {
    const res = await requestLocalApi({
        method: "post",
        url: "/SecurityAi/seek",
        data: { frameIndex },
        timeout: SECURITY_AI_SEEK_TIMEOUT_MS,
    })
    return res.data
}

export async function getSecurityAiResult() {
    const res = await requestLocalApi({
        method: "get",
        url: "/SecurityAi/result",
        timeout: SECURITY_AI_RESULT_TIMEOUT_MS,
    })
    return res.data
}

export async function getSecurityAiCameraStatus() {
    const res = await requestLocalApi({
        method: "get",
        url: "/SecurityAi/camera/status",
        timeout: SECURITY_AI_STATUS_TIMEOUT_MS,
    })
    return res.data
}

export async function getSecurityAiAlerts(params = {}) {
    const res = await requestLocalApi({
        method: "get",
        url: "/SecurityAi/alerts",
        params,
        timeout: SECURITY_AI_ALERTS_TIMEOUT_MS,
    })
    return res.data
}

export function getSecurityAiFrameUrl(cacheBuster = Date.now()) {
    const base = getResolvedLocalApiBaseUrl()
    return `${base}/SecurityAi/camera/frame?ts=${cacheBuster}`
}
