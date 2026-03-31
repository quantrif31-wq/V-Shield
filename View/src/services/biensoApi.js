import axios from "axios"
import { PLATE_API_BASE_URL } from "../config/api"

const DEFAULT_TIMEOUT_MS = 15000
const LOOPBACK_PROBE_TIMEOUT_MS = 1200
const PLATE_API_OVERRIDE_STORAGE_KEY = "vshield-plate-api-override"
const LOOPBACK_PLATE_API_BASE_URLS = [
  "http://127.0.0.1:5002/api",
  "http://localhost:5002/api"
]

let activePlateApiBaseUrl = ""

const trimTrailingSlash = (value = "") => String(value || "").replace(/\/+$/, "")

const isBrowser = () => typeof window !== "undefined"

const isLoopbackHostname = (hostname = "") => {
  const normalizedHostname = String(hostname || "").trim().toLowerCase()
  return (
    normalizedHostname === "localhost" ||
    normalizedHostname === "127.0.0.1" ||
    normalizedHostname === "::1" ||
    normalizedHostname === "[::1]"
  )
}

const isLoopbackBaseUrl = (value) => {
  try {
    const parsedUrl = new URL(value)
    return isLoopbackHostname(parsedUrl.hostname)
  } catch {
    return false
  }
}

const shouldPreferLocalLoopback = () => {
  if (!isBrowser()) return false
  return !isLoopbackHostname(window.location.hostname)
}

const readPlateApiOverride = () => {
  if (!isBrowser()) return ""
  return trimTrailingSlash(
    window.localStorage.getItem(PLATE_API_OVERRIDE_STORAGE_KEY) || ""
  )
}

const getCandidateBaseUrls = () => {
  const orderedBaseUrls = []
  const seenBaseUrls = new Set()

  const addBaseUrl = (value) => {
    const normalizedValue = trimTrailingSlash(value)
    if (!normalizedValue || seenBaseUrls.has(normalizedValue)) {
      return
    }

    seenBaseUrls.add(normalizedValue)
    orderedBaseUrls.push(normalizedValue)
  }

  addBaseUrl(activePlateApiBaseUrl)
  addBaseUrl(readPlateApiOverride())

  if (shouldPreferLocalLoopback()) {
    LOOPBACK_PLATE_API_BASE_URLS.forEach(addBaseUrl)
  }

  addBaseUrl(PLATE_API_BASE_URL)

  return orderedBaseUrls
}

const getTimeoutForBaseUrl = (baseUrl) => {
  const normalizedBaseUrl = trimTrailingSlash(baseUrl)
  const normalizedConfiguredBaseUrl = trimTrailingSlash(PLATE_API_BASE_URL)

  if (normalizedBaseUrl === normalizedConfiguredBaseUrl) {
    return DEFAULT_TIMEOUT_MS
  }

  return isLoopbackBaseUrl(normalizedBaseUrl)
    ? LOOPBACK_PROBE_TIMEOUT_MS
    : DEFAULT_TIMEOUT_MS
}

const normalizeError = (error, attemptedBaseUrls = []) => {
  if (error?.response?.data) {
    return error.response.data
  }

  const attemptedBaseUrlText = attemptedBaseUrls.filter(Boolean).join(" -> ")

  return {
    success: false,
    message:
      error?.message ||
      (attemptedBaseUrlText
        ? `Khong ket noi duoc bien so service (${attemptedBaseUrlText}).`
        : "Network error")
  }
}

async function request(config) {
  const candidateBaseUrls = getCandidateBaseUrls()
  const attemptedBaseUrls = []

  for (const baseURL of candidateBaseUrls) {
    attemptedBaseUrls.push(baseURL)

    try {
      const response = await axios({
        ...config,
        baseURL,
        timeout: getTimeoutForBaseUrl(baseURL)
      })

      activePlateApiBaseUrl = baseURL
      return response.data
    } catch (error) {
      if (error?.response) {
        activePlateApiBaseUrl = baseURL
        throw normalizeError(error, attemptedBaseUrls)
      }

      if (baseURL === candidateBaseUrls[candidateBaseUrls.length - 1]) {
        throw normalizeError(error, attemptedBaseUrls)
      }
    }
  }

  throw normalizeError(null, attemptedBaseUrls)
}

export async function turnOnCamera(ip) {
  return request({
    method: "post",
    url: "/camera/on",
    data: { ip }
  })
}

export async function turnOffCamera() {
  return request({
    method: "post",
    url: "/camera/off"
  })
}

export async function resetCameraState() {
  return request({
    method: "post",
    url: "/camera/reset"
  })
}

export async function getCameraStatus() {
  return request({
    method: "get",
    url: "/camera/status"
  })
}

export async function getCameraResult() {
  return request({
    method: "get",
    url: "/camera/result"
  })
}

export async function getLockedImages() {
  return request({
    method: "get",
    url: "/camera/locked-images"
  })
}

export function getResolvedPlateApiBaseUrl() {
  return activePlateApiBaseUrl || getCandidateBaseUrls()[0] || PLATE_API_BASE_URL
}
