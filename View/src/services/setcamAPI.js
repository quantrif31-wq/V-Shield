import { requestLocalApi } from "./localApiClient"

// ================= CAMERA =================

// lấy danh sách
export async function getCameras() {
    const res = await requestLocalApi({
        method: "get",
        url: "/SetCam",
    })
    return res.data
}

// lấy theo id
export async function getCameraById(id) {
    const res = await requestLocalApi({
        method: "get",
        url: `/SetCam/${id}`,
    })
    return res.data
}

// thêm
export async function createCamera(data) {
    const res = await requestLocalApi({
        method: "post",
        url: "/SetCam",
        data,
    })
    return res.data
}

// cập nhật
export async function updateCamera(id, data) {
    const res = await requestLocalApi({
        method: "put",
        url: `/SetCam/${id}`,
        data,
    })
    return res.data
}

// xóa
export async function deleteCamera(id) {
    const res = await requestLocalApi({
        method: "delete",
        url: `/SetCam/${id}`,
    })
    return res.data
}

// ================= 🔥 GO2RTC =================

// reload + tự update UrlView
export async function reloadGo2rtc() {
    const res = await requestLocalApi({
        method: "post",
        url: "/SetCam/reload-go2rtc",
    })
    return res.data
}

// stop
export async function stopGo2rtc() {
    const res = await requestLocalApi({
        method: "post",
        url: "/SetCam/stop-go2rtc",
    })
    return res.data
}
