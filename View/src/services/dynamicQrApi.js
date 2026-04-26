import { requestLocalApi } from "./localApiClient"

const QR_GENERATE_TIMEOUT_MS = 12000

export async function generateDynamicQr(employeeId) {
  const response = await requestLocalApi({
    method: "post",
    url: "/QR_Dong/generate",
    timeout: QR_GENERATE_TIMEOUT_MS,
    data: {
      employeeId: Number(employeeId),
    },
  })

  return response.data
}
