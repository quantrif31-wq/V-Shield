import { requestLocalApi } from "./localApiClient"

export async function verifyDynamicQr(qrPayload, scannerDevice = 'WEB_SCANNER') {
    const response = await requestLocalApi({
        method: "post",
        url: "/QR_Dong/verify",
        data: {
            qrPayload,
            scannerDevice,
        },
    })
    return response.data
}
