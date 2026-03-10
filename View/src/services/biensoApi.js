import axios from "axios"

const API = axios.create({
  baseURL: "https://localhost:7107/api/BienSo",
  timeout: 5000
})

export async function getCameras(){

  const res = await API.get("/cameras")

  return res.data

}

export async function getPlate(ip){

  const res = await API.get("/plate",{
    params:{ ip }
  })

  return res.data

}