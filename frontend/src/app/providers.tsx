"use client"

import React, { useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Toaster } from "react-hot-toast"
import { useAuth } from "@/hooks/useAuth"

function AuthHydration({ children }: { children: React.ReactNode }) {
  useAuth()
  return <>{children}</>
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 1000 * 30, // 30 seconds
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <AuthHydration>
        {children}
        <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
      </AuthHydration>
    </QueryClientProvider>
  )
}

