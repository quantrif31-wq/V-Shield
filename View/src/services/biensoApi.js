import axios from "axios"

const API = axios.create({
  baseURL: "http://127.0.0.1:5002/api",
  timeout: 15000
})

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.data) {
      return Promise.reject(error.response.data)
    }

    return Promise.reject({
      success: false,
      message: error?.message || "Network error"
    })
  }
)

export async function turnOnCamera(ip) {
  const res = await API.post("/camera/on", { ip })
  return res.data
}

export async function turnOffCamera() {
  const res = await API.post("/camera/off")
  return res.data
}

export async function resetCameraState() {
  const res = await API.post("/camera/reset")
  return res.data
}

export async function getCameraStatus() {
  const res = await API.get("/camera/status")
  return res.data
}

export async function getCameraResult() {
  const res = await API.get("/camera/result")
  return res.data
}

export async function getLockedImages() {
  const res = await API.get("/camera/locked-images")
  return res.data
}