import axios from "axios"
import { API_BASE_URL } from "../config/api"

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
})

export function scanGate(payload) {
  return api.post("/Gate/scan", payload)
}
