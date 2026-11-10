"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  AlertTriangle,
  ArrowLeftRight,
  Boxes,
  FileSpreadsheet,
  History,
  LayoutDashboard,
  LogOut,
  Package,
  ShieldCheck,
  Users,
  Warehouse,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/stores/auth"

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  adminOnly?: boolean
}

const navigation: NavItem[] = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Warehouses", href: "/warehouses", icon: Warehouse },
  { name: "Products", href: "/products", icon: Package },
  { name: "Inventory", href: "/inventory", icon: Boxes },
  { name: "Movements", href: "/movements", icon: ArrowLeftRight },
  { name: "Alerts", href: "/alerts", icon: AlertTriangle },
  { name: "Reports", href: "/reports", icon: FileSpreadsheet },
  { name: "Users", href: "/users", icon: Users, adminOnly: true },
  { name: "Audit Logs", href: "/audit", icon: History, adminOnly: true },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  const isAdmin = user?.role === "admin"

  return (
    <aside className="fixed left-0 top-0 bottom-0 z-40 flex w-64 flex-col border-r bg-white shadow-sm">
      {/* Brand Header */}
      <div className="flex h-16 items-center px-6 border-b">
        <Link href="/dashboard" className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white font-bold shadow-md">
            WMS
          </div>
          <div>
            <h1 className="font-bold text-slate-900 leading-tight">Warehouse MS</h1>
            <p className="text-[11px] text-slate-500 font-medium">On-Premises Local</p>
          </div>
        </Link>
      </div>

      {/* Navigation links */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto">
        {navigation.map((item) => {
          if (item.adminOnly && !isAdmin) return null
          const isActive = pathname.startsWith(item.href)
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                isActive
                  ? "bg-blue-50 text-blue-700 shadow-sm font-semibold"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              )}
            >
              <Icon
                className={cn(
                  "mr-3 h-5 w-5 shrink-0 transition-colors",
                  isActive ? "text-blue-600" : "text-slate-400 group-hover:text-slate-600"
                )}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* User profile & Logout */}
      <div className="border-t p-4 bg-slate-50/70">
        <div className="flex items-center justify-between mb-3">
          <div className="truncate">
            <p className="text-sm font-semibold text-slate-900 truncate">
              {user?.full_name || user?.username || "Authenticated"}
            </p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
          <Badge
            variant={
              user?.role === "admin"
                ? "destructive"
                : user?.role === "manager"
                ? "default"
                : user?.role === "staff"
                ? "success"
                : "secondary"
            }
            className="uppercase text-[10px] tracking-wider font-semibold"
          >
            {user?.role || "viewer"}
          </Badge>
        </div>

        <Button
          variant="outline"
          size="sm"
          className="w-full text-slate-700 border-slate-300 hover:bg-red-50 hover:text-red-600 hover:border-red-200"
          onClick={() => logout()}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </Button>
      </div>
    </aside>
  )
}

