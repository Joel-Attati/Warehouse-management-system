"use client"

import React from "react"
import { ShieldCheck, Wifi } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface TopbarProps {
  title?: string
  subtitle?: string
}

export function Topbar({ title, subtitle }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b bg-white/95 px-8 backdrop-blur shadow-sm">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">{title || "Warehouse Management"}</h2>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-3">
        <Badge variant="outline" className="flex items-center space-x-1.5 border-emerald-300 bg-emerald-50 text-emerald-800">
          <Wifi className="h-3 w-3 text-emerald-600" />
          <span className="text-xs font-medium">Local Network Online</span>
        </Badge>
        <Badge variant="secondary" className="flex items-center space-x-1">
          <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
          <span className="text-xs">Role Enforcement Active</span>
        </Badge>
      </div>
    </header>
  )
}

