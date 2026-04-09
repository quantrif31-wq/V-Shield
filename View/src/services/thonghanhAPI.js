import { requestLocalApi } from "./localApiClient"

export function scanGate(payload) {
  return requestLocalApi({
    method: "post",
    url: "/Gate/scan",
    data: payload,
  })
}

export function confirmGateLocally(payload) {
  return requestLocalApi({
    method: "post",
    url: "/Gate/local-confirm",
    data: payload,
  })
}
