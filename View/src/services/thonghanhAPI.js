import axios from "axios"

const api = axios.create({
  baseURL: "https://localhost:7107/api",
  headers: {
    "Content-Type": "application/json"
  }
})

export function scanGate(payload) {
  return api.post("/Gate/scan", payload)
}