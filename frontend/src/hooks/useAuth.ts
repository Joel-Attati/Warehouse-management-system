"use client"

import { useEffect } from "react"
import { useAuthStore } from "@/stores/auth"

export function useAuth() {
  const { user, isLoading, fetchUser, logout } = useAuthStore()

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    logout,
  }
}

