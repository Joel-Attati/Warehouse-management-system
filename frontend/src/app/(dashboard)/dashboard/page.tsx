"use client"

import React from "react"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowLeftRight,
  ArrowUpRight,
  Boxes,
  Clock,
  Package,
  Warehouse,
} from "lucide-react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingPage } from "@/components/ui/loading"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { dashboardApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.getStats,
    refetchInterval: 15000, // auto-refresh every 15s
  })

  if (isLoading) {
    return <LoadingPage message="Loading operational dashboard..." />
  }

  if (error || !stats) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center text-red-800">
        <p className="font-semibold">Unable to load dashboard data</p>
        <p className="text-sm">Please ensure the backend API and database are running.</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Operational Overview</h1>
          <p className="text-sm text-slate-500">
            Real-time warehouse metrics, stock levels, and daily movement activity.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link href="/movements">
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
              <ArrowLeftRight className="mr-2 h-4 w-4" />
              New Movement
            </Button>
          </Link>
          <Link href="/products">
            <Button size="sm" variant="outline">
              <Package className="mr-2 h-4 w-4" />
              Manage Products
            </Button>
          </Link>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Products */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Products</CardTitle>
            <div className="h-9 w-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
              <Package className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">{stats.total_products}</div>
            <p className="text-xs text-slate-500 mt-1">Active registered catalog items</p>
          </CardContent>
        </Card>

        {/* Total Locations */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Storage Locations</CardTitle>
            <div className="h-9 w-9 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
              <Warehouse className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">{stats.total_locations}</div>
            <p className="text-xs text-slate-500 mt-1">Configured rack / shelf locations</p>
          </CardContent>
        </Card>

        {/* Movements Today */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Movements Today</CardTitle>
            <div className="h-9 w-9 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <ArrowLeftRight className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">{stats.total_movements_today}</div>
            <p className="text-xs text-slate-500 mt-1">Receipts, issues, & transfers today</p>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <Card className={stats.low_stock_count > 0 ? "border-amber-300 bg-amber-50/30" : ""}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Low Stock Alerts</CardTitle>
            <div className="h-9 w-9 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
              <AlertTriangle className="h-5 w-5" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-700">{stats.low_stock_count}</div>
            <p className="text-xs text-amber-800/80 mt-1">Items at or below reorder level</p>
          </CardContent>
        </Card>
      </div>

      {/* Notification Banner for Expiring Batches */}
      {stats.expiring_soon_count > 0 && (
        <div className="flex items-center justify-between rounded-xl border border-rose-200 bg-rose-50 px-5 py-3.5 text-rose-900">
          <div className="flex items-center space-x-3">
            <Clock className="h-5 w-5 text-rose-600" />
            <div>
              <span className="font-semibold">{stats.expiring_soon_count} batch(es)</span> expiring within the next 30 days!
            </div>
          </div>
          <Link href="/alerts">
            <Button size="sm" variant="outline" className="border-rose-300 text-rose-700 hover:bg-rose-100">
              View Expiring Batches
            </Button>
          </Link>
        </div>
      )}

      {/* Chart: Movement Trends (7 Days) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">Inventory Movement Trends (Last 7 Days)</CardTitle>
          <CardDescription>Daily volume breakdown across receipts, issues, and transfers</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.movement_trends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="date" stroke="#64748B" fontSize={12} />
                <YAxis allowDecimals={false} stroke="#64748B" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#FFFFFF",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    border: "1px solid #E2E8F0",
                  }}
                />
                <Legend />
                <Bar dataKey="receives" name="Received" fill="#2563EB" radius={[4, 4, 0, 0]} />
                <Bar dataKey="issues" name="Issued" fill="#DC2626" radius={[4, 4, 0, 0]} />
                <Bar dataKey="transfers" name="Transferred" fill="#F59E0B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Two Columns: Critical Stock & Recent Movements */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Critical Low Stock */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold">Critical Stock Items</CardTitle>
              <CardDescription>Top priority items requiring reordering</CardDescription>
            </div>
            <Link href="/alerts">
              <Button variant="ghost" size="sm" className="text-xs">
                View all alerts
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {stats.top_low_stock.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-500">
                All inventory items are currently at healthy stock levels.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead className="text-right">Current</TableHead>
                    <TableHead className="text-right">Reorder</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.top_low_stock.map((item) => (
                    <TableRow key={item.product_id}>
                      <TableCell className="font-mono text-xs font-semibold">{item.sku}</TableCell>
                      <TableCell className="font-medium text-slate-900 truncate max-w-[140px]">
                        {item.name}
                      </TableCell>
                      <TableCell className="text-right font-bold text-red-600">
                        {item.current_stock} {item.unit}
                      </TableCell>
                      <TableCell className="text-right text-slate-500 text-xs">
                        {item.reorder_level} {item.unit}
                      </TableCell>
                      <TableCell>
                        <Badge variant={item.status === "critical" ? "destructive" : "warning"}>
                          {item.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Recent Movements */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base font-semibold">Recent Movements</CardTitle>
              <CardDescription>Latest inventory transactions performed</CardDescription>
            </div>
            <Link href="/movements">
              <Button variant="ghost" size="sm" className="text-xs">
                Full log
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {stats.recent_movements.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-500">
                No inventory movements recorded yet.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead className="text-right">Qty</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.recent_movements.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell>
                        <Badge
                          variant={
                            m.movement_type === "RECEIVE"
                              ? "default"
                              : m.movement_type === "ISSUE"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-[10px] uppercase font-semibold"
                        >
                          {m.movement_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">{m.product_sku}</TableCell>
                      <TableCell className="text-right font-semibold">
                        {m.movement_type === "ISSUE" ? `-${m.quantity}` : `+${m.quantity}`}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600">{m.performed_by_name}</TableCell>
                      <TableCell className="text-xs text-slate-400">{formatDate(m.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

