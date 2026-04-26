import axios from "axios"
import { API_BASE_URL } from "../config/api"

const DEFAULT_TIMEOUT_MS = 15000
const LOOPBACK_PROBE_TIMEOUT_MS = 1200
const trimTrailingSlash = (value = "") => String(value || "").replace(/\/+$/, "")
const isBrowser = () => typeof window !== "undefined"

const LOCAL_API_OVERRIDE_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_LOCAL_API_BASE_URL || ""
)
const LOOPBACK_LOCAL_API_BASE_URLS = [
  "http://127.0.0.1:5107/api",
  "http://localhost:5107/api",
]

let activeLocalApiBaseUrl = ""

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

const buildCandidateBaseUrls = () => {
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

  addBaseUrl(activeLocalApiBaseUrl)
  addBaseUrl(LOCAL_API_OVERRIDE_BASE_URL)

  // Prefer configured API first when it points outside loopback (typically VPS),
  // or when frontend itself is not running on loopback.
  const hasNonLoopbackConfiguredApi = !isLoopbackBaseUrl(API_BASE_URL)
  const preferConfiguredApiFirst =
    hasNonLoopbackConfiguredApi ||
    (isBrowser() ? !isLoopbackHostname(window.location.hostname) : true)

  if (preferConfiguredApiFirst) {
    addBaseUrl(API_BASE_URL)
    LOOPBACK_LOCAL_API_BASE_URLS.forEach(addBaseUrl)
  } else {
    LOOPBACK_LOCAL_API_BASE_URLS.forEach(addBaseUrl)
    addBaseUrl(API_BASE_URL)
  }

  return orderedBaseUrls
}

const getTimeoutForBaseUrl = (baseUrl, explicitTimeout) => {
  if (Number(explicitTimeout) > 0) {
    return Number(explicitTimeout)
  }

  return isLoopbackBaseUrl(baseUrl) ? LOOPBACK_PROBE_TIMEOUT_MS : DEFAULT_TIMEOUT_MS
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
        ? `Khong ket noi duoc local API (${attemptedBaseUrlText}).`
        : "Khong ket noi duoc local API."),
  }
}

export async function requestLocalApi(config) {
  const candidateBaseUrls = buildCandidateBaseUrls()
  const attemptedBaseUrls = []

  for (const baseURL of candidateBaseUrls) {
    attemptedBaseUrls.push(baseURL)

    try {
      const response = await axios({
        ...config,
        baseURL,
        timeout: getTimeoutForBaseUrl(baseURL, config?.timeout),
      })

      activeLocalApiBaseUrl = baseURL
      return response
    } catch (error) {
      if (error?.response) {
        activeLocalApiBaseUrl = baseURL
        throw normalizeError(error, attemptedBaseUrls)
      }

      if (baseURL === candidateBaseUrls[candidateBaseUrls.length - 1]) {
        throw normalizeError(error, attemptedBaseUrls)
      }
    }
  }

  throw normalizeError(null, attemptedBaseUrls)
}

export function getResolvedLocalApiBaseUrl() {
  return (
    activeLocalApiBaseUrl ||
    buildCandidateBaseUrls()[0] ||
    LOOPBACK_LOCAL_API_BASE_URLS[0]
  )
}
