import axios from "axios";

const API = axios.create({
  baseURL: "https://localhost:5107/api/BienSo",
  timeout: 5000
});

// ========================
// STATUS
// ========================
export async function getStatus() {
  const res = await API.get("/status");
  return res.data;
}

// ========================
// START CAMERA
// ========================
export async function startCamera(ip) {

  const res = await API.post(
    `/start?ip=${encodeURIComponent(ip)}`
  );

  return res.data;
}

// ========================
// STOP CAMERA
// ========================
export async function stopCamera() {

  const res = await API.post("/stop");

  return res.data;
}

// ========================
// GET PLATE RESULT
// ========================
export async function getPlate() {

  const res = await API.get("/plate");

  return res.data;
}

// ========================
// PYTHON STREAM URL
// ========================
const PYTHON_API = "http://127.0.0.1:8001";

export function getStreamUrl() {

  // cache bust để tránh browser cache
  return `${PYTHON_API}/stream?t=${Date.now()}`;

}