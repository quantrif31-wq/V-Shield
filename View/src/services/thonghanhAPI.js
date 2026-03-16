import axios from "axios"

export function scanGate(){
    return axios.get("https://localhost:7107/api/Gate/scan")
}