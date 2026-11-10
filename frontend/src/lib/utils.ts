import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString?: string | null): string {
  if (!dateString) return "-"
  try {
    const d = new Date(dateString)
    return d.toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return dateString
  }
}

export function formatShortDate(dateString?: string | null): string {
  if (!dateString) return "-"
  try {
    const d = new Date(dateString)
    return d.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
  } catch {
    return dateString
  }
}

