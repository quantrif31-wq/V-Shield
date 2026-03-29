export const CAMERA_NETWORK_STORAGE_KEY = "vshield-camera-network-settings-v2"

const HTTP_CAMERA_PROTOCOL_REGEX = /^https?:\/\//i
const RTSP_CAMERA_PROTOCOL_REGEX = /^rtsp:\/\//i
const HLS_CAMERA_PATH_REGEX = /\.m3u8($|[?#])/i
const BROWSER_VIDEO_PATH_REGEX = /\.(mp4|webm|ogg)($|[?#])/i
const STREAM_PREVIEW_PATHS = new Set(["/video", "/videofeed"])

export const DEFAULT_CAMERA_SETTINGS = [
  {
    id: 1,
    name: "CAM-01",
    label: "Cổng A - Trước",
    url: "",
    previewUrl: "",
    location: "Cổng A - Trước",
    online: false,
    enabled: false,
  },
  {
    id: 2,
    name: "CAM-02",
    label: "Cổng A - Sau",
    url: "",
    previewUrl: "",
    location: "Cổng A - Sau",
    online: false,
    enabled: false,
  },
  {
    id: 3,
    name: "CAM-03",
    label: "Cổng B - Trước",
    url: "",
    previewUrl: "",
    location: "Cổng B - Trước",
    online: false,
    enabled: false,
  },
  {
    id: 4,
    name: "CAM-04",
    label: "Cổng B - Sau",
    url: "",
    previewUrl: "",
    location: "Cổng B - Sau",
    online: false,
    enabled: false,
  },
]

export const createDefaultCameraSettings = () =>
  DEFAULT_CAMERA_SETTINGS.map((camera) => ({ ...camera }))

export const isHttpCameraUrl = (url) => HTTP_CAMERA_PROTOCOL_REGEX.test(url || "")

export const isRtspCameraUrl = (url) => RTSP_CAMERA_PROTOCOL_REGEX.test(url || "")

export const isHlsCameraUrl = (url) => {
  const value = (url || "").trim()
  return isHttpCameraUrl(value) && HLS_CAMERA_PATH_REGEX.test(value)
}

export const isBrowserVideoCameraUrl = (url) => {
  const value = (url || "").trim()
  return isHttpCameraUrl(value) && BROWSER_VIDEO_PATH_REGEX.test(value)
}

export const looksLikeHostInput = (value) =>
  /^[\w.-]+(?::\d+)?(?:\/.*)?$/i.test((value || "").trim())

export const normalizeCameraUrl = (rawValue) => {
  let value = (rawValue || "").trim()
  if (!value) return ""

  value = value.replace(/^\/+/, "")
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(value) && looksLikeHostInput(value)) {
    value = `http://${value}`
  }

  try {
    const parsedUrl = new URL(value)
    if (
      (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") &&
      (!parsedUrl.pathname || parsedUrl.pathname === "/")
    ) {
      if (parsedUrl.port === "8081") {
        parsedUrl.pathname = "/video"
      } else if (parsedUrl.port === "8080") {
        parsedUrl.pathname = "/videofeed"
      }
    }

    return parsedUrl.toString()
  } catch {
    return (rawValue || "").trim()
  }
}

export const isKnownStreamPreviewUrl = (url) => {
  if (!isHttpCameraUrl(url)) return false

  try {
    const parsedUrl = new URL(normalizeCameraUrl(url))
    return STREAM_PREVIEW_PATHS.has(parsedUrl.pathname.toLowerCase())
  } catch {
    return false
  }
}

export const buildCameraHealthProbeUrl = (url) => {
  if (!isHttpCameraUrl(url)) return ""

  try {
    const parsedUrl = new URL(normalizeCameraUrl(url))
    if (!STREAM_PREVIEW_PATHS.has(parsedUrl.pathname.toLowerCase())) {
      return parsedUrl.toString()
    }

    parsedUrl.pathname = "/"
    parsedUrl.search = ""
    parsedUrl.hash = ""
    return parsedUrl.toString()
  } catch {
    return (url || "").trim()
  }
}

export const shouldAppendPreviewCacheBust = (url) =>
  isHttpCameraUrl(url) && !isKnownStreamPreviewUrl(url)

export const resolveCameraPreviewUrl = (camera) =>
  camera?.previewUrl?.trim() || camera?.url?.trim() || ""

export const resolveCameraSourceUrl = (camera) =>
  camera?.url?.trim() || camera?.previewUrl?.trim() || ""

const parseLegacyCameraName = (value, fallbackName, fallbackLabel) => {
  const name = (value || "").trim()
  if (!name) {
    return { name: fallbackName, label: fallbackLabel }
  }

  const match = name.match(/^([^()]+?)\s*\(([^)]+)\)$/)
  if (match) {
    return {
      name: match[1].trim() || fallbackName,
      label: match[2].trim() || fallbackLabel,
    }
  }

  return {
    name,
    label: fallbackLabel,
  }
}

export const normalizeCameraSettings = (settings) =>
  createDefaultCameraSettings().map((fallbackCamera) => {
    const savedCamera = Array.isArray(settings)
      ? settings.find((item) => Number(item?.id) === fallbackCamera.id)
      : null
    const savedCameraData =
      savedCamera && typeof savedCamera === "object" ? { ...savedCamera } : {}
    delete savedCameraData.recognitionType
    delete savedCameraData.resolution

    const legacyParts = parseLegacyCameraName(
      savedCameraData.name,
      fallbackCamera.name,
      fallbackCamera.label
    )

    const normalizedUrl = savedCameraData.url?.trim() || ""
    const normalizedPreviewUrl = savedCameraData.previewUrl?.trim() || ""
    const hasAnyUrl = Boolean(normalizedUrl || normalizedPreviewUrl)

    return {
      ...fallbackCamera,
      ...savedCameraData,
      id: fallbackCamera.id,
      name: savedCameraData.name?.trim()
        ? legacyParts.name
        : fallbackCamera.name,
      label: savedCameraData.label?.trim()
        ? savedCameraData.label.trim()
        : legacyParts.label,
      url: normalizedUrl,
      previewUrl: normalizedPreviewUrl,
      location: savedCameraData.location?.trim() || fallbackCamera.location,
      online: Boolean(savedCameraData.online && hasAnyUrl),
      enabled: Boolean(savedCameraData.enabled && hasAnyUrl),
    }
  })

export const loadCameraNetworkSettings = () => {
  const rawValue = localStorage.getItem(CAMERA_NETWORK_STORAGE_KEY)
  if (!rawValue) {
    return createDefaultCameraSettings()
  }

  try {
    return normalizeCameraSettings(JSON.parse(rawValue))
  } catch {
    return createDefaultCameraSettings()
  }
}

export const saveCameraNetworkSettings = (settings) => {
  const normalizedSettings = normalizeCameraSettings(settings)
  localStorage.setItem(
    CAMERA_NETWORK_STORAGE_KEY,
    JSON.stringify(normalizedSettings)
  )
  return normalizedSettings
}

export const getConfiguredCameraSettings = (
  settings = loadCameraNetworkSettings()
) =>
  normalizeCameraSettings(settings).filter((camera) => {
    const sourceUrl = resolveCameraSourceUrl(camera)
    const previewUrl = resolveCameraPreviewUrl(camera)
    return Boolean(camera?.enabled && (sourceUrl || previewUrl))
  })

export const extractCameraDisplayParts = (cameraLike, fallbackIndex = 1) => {
  const fallbackSlotName = `CAM-${String(fallbackIndex).padStart(2, "0")}`

  if (cameraLike && typeof cameraLike === "object") {
    return {
      slotName: cameraLike.name?.trim() || fallbackSlotName,
      sourceName: cameraLike.label?.trim() || "",
    }
  }

  const legacyParts = parseLegacyCameraName(
    cameraLike,
    fallbackSlotName,
    ""
  )

  return {
    slotName: legacyParts.name,
    sourceName: legacyParts.label,
  }
}
