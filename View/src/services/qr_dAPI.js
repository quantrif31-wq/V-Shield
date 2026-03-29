export async function startQr(rtsp) {
  return fetch("http://127.0.0.1:8001/qr/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rtsp })
  }).then(r => r.json())
}

export async function scanQr() {
  return fetch("http://127.0.0.1:8001/qr/scan", {
    method: "POST"
  }).then(r => r.json())
}

export async function resetQr() {
  return fetch("http://127.0.0.1:8001/qr/reset", {
    method: "POST"
  }).then(r => r.json())
}

export async function stopQr() {
  return fetch("http://127.0.0.1:8001/qr/stop", {
    method: "POST"
  }).then(r => r.json())
}

export async function getQrResult() {
  return fetch("http://127.0.0.1:8001/qr/result")
    .then(r => r.json())
}