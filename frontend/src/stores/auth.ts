import { create } from "zustand"
import { authApi } from "@/lib/api"
import { User } from "@/types"

interface AuthState {
  user: User | null
  isLoading: boolean
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  fetchUser: () => Promise<User | null>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user }),
  setLoading: (isLoading) => set({ isLoading }),
  fetchUser: async () => {
    try {
      set({ isLoading: true })
      const user = await authApi.me()
      set({ user, isLoading: false })
      return user
    } catch {
      set({ user: null, isLoading: false })
      return null
    }
  },
  logout: async () => {
    try {
      await authApi.logout()
    } finally {
      set({ user: null })
      if (typeof window !== "undefined") {
        window.location.href = "/login"
      }
    }
  },
}))

