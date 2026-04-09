import { requestLocalApi } from "./localApiClient"

export async function generateDynamicQr(employeeId) {
  const response = await requestLocalApi({
    method: "post",
    url: "/QR_Dong/generate",
    data: {
      employeeId: Number(employeeId),
    },
  })

  return response.data
}
