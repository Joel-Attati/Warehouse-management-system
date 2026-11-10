import React from "react"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("h-6 w-6 animate-spin text-blue-600", className)} />
}

export function LoadingPage({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] w-full space-y-3">
      <Spinner className="h-8 w-8" />
      <p className="text-sm text-slate-500 font-medium">{message}</p>
    </div>
  )
}

