import axios from "axios"
import { API_BASE_URL } from "../config/api"

const API = `${API_BASE_URL}/Video`

export const uploadFaceVideo = async (file, employeeId, onProgress)=>{

    const formData = new FormData()

    formData.append("file", file)

    if(employeeId)
        formData.append("employeeId", employeeId)

    return axios.post(
        API + "/upload",
        formData,
        {
            headers:{
                Authorization:`Bearer ${localStorage.getItem("v_shield_token")}`,
                "Content-Type":"multipart/form-data"
            },

            onUploadProgress:(e)=>{
                if(onProgress){
                    const percent = Math.round((e.loaded*100)/e.total)
                    onProgress(percent)
                }
            }
        }
    )
}


export const getEmployeeVideos = (employeeId)=>{
    return axios.get(
        `${API}/employee/${employeeId}`,
        {
            headers:{
                Authorization:`Bearer ${localStorage.getItem("v_shield_token")}`
            }
        }
    )
}


export const deleteVideo = (id)=>{
    return axios.delete(
        `${API}/${id}`,
        {
            headers:{
                Authorization:`Bearer ${localStorage.getItem("v_shield_token")}`
            }
        }
    )
}
