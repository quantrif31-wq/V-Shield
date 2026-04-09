const trimTrailingSlash = (value = "") => String(value || "").replace(/\/+$/, "")

const QR_API_BASE_URL = trimTrailingSlash(
  import.meta.env.VITE_QR_API_BASE_URL || "http://localhost:8001"
)

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${QR_API_BASE_URL}${path}`, options)
  } catch (error) {
    throw new Error(
      `Khong ket noi duoc QR service tai ${QR_API_BASE_URL}. Hay kiem tra QR_Dong.py dang chay o dung cong.`
    )
  }

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const message =
      data?.message ||
      data?.detail ||
      `QR service loi ${response.status}`

    throw new Error(message)
  }

  return data
}

export async function startQr(rtsp) {
  return request("/qr/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rtsp }),
  })
}

export async function scanQr() {
  return request("/qr/scan", {
    method: "POST",
  })
}

export async function resetQr() {
  return request("/qr/reset", {
    method: "POST",
  })
}

export async function stopQr() {
  return request("/qr/stop", {
    method: "POST",
  })
}

export async function getQrResult() {
  return request("/qr/result")
}

export async function getQrLockedImage() {
  return request("/qr/locked-image")
}

export { QR_API_BASE_URL }
