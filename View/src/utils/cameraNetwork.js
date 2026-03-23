export const CAMERA_NETWORK_STORAGE_KEY = "vshield-camera-network-settings-v2"

export const DEFAULT_CAMERA_SETTINGS = [
  {
    id: 1,
    name: "CAM-01",
    label: "Cổng A - Trước",
    url: "",
    location: "Cổng A - Trước",
    online: false,
    enabled: false,
    recognitionType: "both",
    resolution: "1080p",
  },
  {
    id: 2,
    name: "CAM-02",
    label: "Cổng A - Sau",
    url: "",
    location: "Cổng A - Sau",
    online: false,
    enabled: false,
    recognitionType: "plate",
    resolution: "1080p",
  },
  {
    id: 3,
    name: "CAM-03",
    label: "Cổng B - Trước",
    url: "",
    location: "Cổng B - Trước",
    online: false,
    enabled: false,
    recognitionType: "face",
    resolution: "720p",
  },
  {
    id: 4,
    name: "CAM-04",
    label: "Cổng B - Sau",
    url: "",
    location: "Cổng B - Sau",
    online: false,
    enabled: false,
    recognitionType: "plate",
    resolution: "720p",
  },
]

export const createDefaultCameraSettings = () =>
  DEFAULT_CAMERA_SETTINGS.map((camera) => ({ ...camera }))

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

    const legacyParts = parseLegacyCameraName(
      savedCamera?.name,
      fallbackCamera.name,
      fallbackCamera.label
    )

    const normalizedUrl = savedCamera?.url?.trim() || ""

    return {
      ...fallbackCamera,
      ...(savedCamera || {}),
      id: fallbackCamera.id,
      name: savedCamera?.name?.trim()
        ? legacyParts.name
        : fallbackCamera.name,
      label: savedCamera?.label?.trim()
        ? savedCamera.label.trim()
        : legacyParts.label,
      url: normalizedUrl,
      location: savedCamera?.location?.trim() || fallbackCamera.location,
      online: Boolean(savedCamera?.online && normalizedUrl),
      enabled: Boolean(savedCamera?.enabled && normalizedUrl),
      recognitionType:
        savedCamera?.recognitionType || fallbackCamera.recognitionType,
      resolution: savedCamera?.resolution || fallbackCamera.resolution,
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
