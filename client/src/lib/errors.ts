import { isAxiosError } from 'axios'

/** Prefer FastAPI `detail` string when present; fall back to Error.message. */
export function getApiErrorMessage(error: unknown, fallback = 'Request failed') {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === 'object' && item && 'msg' in item
            ? String(item.msg)
            : String(item),
        )
        .join('; ')
    }
    if (error.message) return error.message
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}
