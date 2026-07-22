import { useSyncExternalStore } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export interface ToastItem {
  id: string
  message: string
  tone: ToastTone
}

type Listener = () => void

let toasts: ToastItem[] = []
const listeners = new Set<Listener>()
let counter = 0

function emit() {
  for (const listener of listeners) {
    listener()
  }
}

function push(message: string, tone: ToastTone) {
  const id = `toast-${++counter}`
  toasts = [...toasts, { id, message, tone }]
  emit()
  window.setTimeout(() => dismiss(id), 4200)
  return id
}

function dismiss(id: string) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

export const toast = {
  success: (message: string) => push(message, 'success'),
  error: (message: string) => push(message, 'error'),
  info: (message: string) => push(message, 'info'),
  dismiss,
}

function subscribe(listener: Listener) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

function getSnapshot() {
  return toasts
}

export function useToasts() {
  return useSyncExternalStore(subscribe, getSnapshot, () => [])
}
