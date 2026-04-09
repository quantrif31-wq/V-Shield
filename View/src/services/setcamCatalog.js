import { getCameras } from "./setcamAPI"

const normalizeText = (...parts) =>
  parts
    .map((part) => String(part || "").trim().toLowerCase())
    .filter(Boolean)
    .join(" ")

const CAMERA_ROLE_PATTERNS = {
  qr: [" qr", "qr ", "qr_", "qr-", "qrcode", "dynamic", "dong", "scan qr"],
  plate: ["plate", "lpr", "license", "bien", "bienso", "number"],
}

const hasRolePattern = (searchText, role) =>
  CAMERA_ROLE_PATTERNS[role]?.some((pattern) => searchText.includes(pattern)) || false

export function normalizeSetCamCamera(camera) {
  const normalizedCamera = {
    ...camera,
    id: Number(camera?.cameraId || 0),
    name: String(camera?.cameraName || "").trim(),
    gateId: camera?.gateId ?? null,
    gateName: String(camera?.gateName || "").trim(),
    cameraType: String(camera?.cameraType || "").trim(),
    sourceUrl: String(camera?.streamUrl || "").trim(),
    browserPreviewUrl: String(camera?.urlView || "").trim(),
  }

  const labelParts = [normalizedCamera.gateName, normalizedCamera.cameraType].filter(Boolean)
  const searchText = normalizeText(
    normalizedCamera.name,
    normalizedCamera.gateName,
    normalizedCamera.cameraType,
    normalizedCamera.sourceUrl
  )

  return {
    ...normalizedCamera,
    label: labelParts.join(" | ") || "Chua gan gate",
    searchText,
  }
}

export async function fetchSetCamCatalog() {
  const response = await getCameras()
  const cameras = Array.isArray(response) ? response : []

  return cameras
    .map(normalizeSetCamCamera)
    .filter((camera) => camera.sourceUrl || camera.browserPreviewUrl)
}

const scoreCameraForRole = (camera, role) => {
  if (!camera) return Number.NEGATIVE_INFINITY

  let score = 0
  if (camera.browserPreviewUrl) score += 4
  if (camera.sourceUrl) score += 3

  if (role === "any") {
    return score
  }

  if (hasRolePattern(camera.searchText, role)) {
    score += 100
  }

  if (role === "qr" && hasRolePattern(camera.searchText, "plate")) {
    score -= 40
  }

  if (role === "plate" && hasRolePattern(camera.searchText, "qr")) {
    score -= 40
  }

  return score
}

export function pickDefaultSetCamCamera(
  cameras,
  { role = "any", preferredId = "", excludedIds = [] } = {}
) {
  const list = Array.isArray(cameras) ? cameras : []
  const excludedIdSet = new Set(excludedIds.map((value) => String(value)))

  if (preferredId) {
    const preferredCamera = list.find(
      (camera) =>
        !excludedIdSet.has(String(camera.id)) &&
        String(camera.id) === String(preferredId)
    )

    if (preferredCamera) {
      return preferredCamera
    }
  }

  const candidates = list
    .filter((camera) => !excludedIdSet.has(String(camera.id)))
    .map((camera, index) => ({
      camera,
      index,
      score: scoreCameraForRole(camera, role),
    }))
    .sort((left, right) => right.score - left.score || left.index - right.index)

  return candidates[0]?.camera || null
}
