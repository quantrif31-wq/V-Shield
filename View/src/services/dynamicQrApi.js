import axios from "axios";

const api = axios.create({
  baseURL: "https://localhost:7107", // sửa lại đúng API của bạn
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
});

export async function generateDynamicQr(employeeId) {
  const response = await api.post("/api/QR_Dong/generate", {
    employeeId: Number(employeeId),
  });
  return response.data;
}

export default api;