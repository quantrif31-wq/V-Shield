import { requestLocalApi } from "./localApiClient"

const QR_VERIFY_TIMEOUT_MS = 12000
const QR_VERIFY_RETRY_TIMEOUT_MS = 16000

const isTimeoutLikeError = (error) =>
  /timeout/i.test(String(error?.message || ""))

export async function verifyDynamicQr(qrPayload, scannerDevice = 'WEB_SCANNER') {
    const payload = {
        method: "post",
        url: "/QR_Dong/verify",
        data: {
            qrPayload,
            scannerDevice,
        },
    }

    try {
        const response = await requestLocalApi({
            ...payload,
            timeout: QR_VERIFY_TIMEOUT_MS,
        })
        return response.data
    } catch (error) {
        if (!isTimeoutLikeError(error)) {
            throw error
        }

        // Retry once with a longer timeout for high-latency VPS hops.
        const retryResponse = await requestLocalApi({
            ...payload,
            timeout: QR_VERIFY_RETRY_TIMEOUT_MS,
        })
        return retryResponse.data
    }
}
