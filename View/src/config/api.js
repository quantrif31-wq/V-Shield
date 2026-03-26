const trimTrailingSlash = (value = "") => value.replace(/\/+$/, "");

const ensureApiBaseUrl = (value, fallbackPort) => {
  const normalizedValue = trimTrailingSlash(value || "");
  if (normalizedValue) {
    return normalizedValue.endsWith("/api") ? normalizedValue : `${normalizedValue}/api`;
  }

  if (typeof window === "undefined") {
    return `http://localhost:${fallbackPort}/api`;
  }

  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:${fallbackPort}/api`;
};

const ensureServiceBaseUrl = (value, fallbackPort) => {
  const normalizedValue = trimTrailingSlash(value || "");
  if (normalizedValue) {
    return normalizedValue;
  }

  return ensureApiBaseUrl("", fallbackPort);
};

const stripApiSuffix = (value) => value.replace(/\/api$/, "");

export const API_BASE_URL = ensureApiBaseUrl(import.meta.env.VITE_API_BASE_URL, 5107);
export const API_ORIGIN = stripApiSuffix(API_BASE_URL);

export const FACE_API_BASE_URL = ensureServiceBaseUrl(import.meta.env.VITE_FACE_API_BASE_URL, 5001);
export const FACE_API_ORIGIN = stripApiSuffix(FACE_API_BASE_URL);

export const PLATE_API_BASE_URL = ensureServiceBaseUrl(import.meta.env.VITE_PLATE_API_BASE_URL, 5002);
export const PLATE_API_ORIGIN = stripApiSuffix(PLATE_API_BASE_URL);
