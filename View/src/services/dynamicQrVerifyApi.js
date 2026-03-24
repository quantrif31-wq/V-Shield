import axios from "axios";

const api = axios.create({
  baseURL: "https://localhost:7107", // sửa lại đúng API của bạn
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export async function verifyDynamicQr(qrPayload, scannerDevice = "WEB_SCANNER") {
  const response = await api.post("/api/QR_Dong/verify", {
    qrPayload,
    scannerDevice,
  });
  return response.data;
}

export default api;