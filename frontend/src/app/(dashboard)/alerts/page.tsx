"use client"

import React, { useState } from "react"
import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { AlertCircle, AlertTriangle, ArrowRight, Clock } from "lucide-react"

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
import { alertsApi } from "@/lib/api"
import { formatShortDate } from "@/lib/utils"
import { ExpiryAlert, LowStockAlert } from "@/types"

export default function AlertsPage() {
  const [expiryDays, setExpiryDays] = useState(30)

  const { data: lowStockAlerts = [], isLoading: loadingLowStock } = useQuery({
    queryKey: ["alerts-low-stock"],
    queryFn: alertsApi.lowStock,
    refetchInterval: 30000,
  })

  const { data: expiryAlerts = [], isLoading: loadingExpiry } = useQuery({
    queryKey: ["alerts-expiring", expiryDays],
    queryFn: () => alertsApi.expiring(expiryDays),
    refetchInterval: 30000,
  })

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inventory Alerts</h1>
        <p className="text-sm text-slate-500">
          Proactive monitoring for replenishment triggers and product lot expirations.
        </p>
      </div>

      {/* Low Stock Alerts Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center space-x-2 text-slate-900">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              <span>Low Stock & Reorder Thresholds</span>
            </CardTitle>
            <CardDescription>
              Products whose on-hand balance is at or below defined minimum or reorder points.
            </CardDescription>
          </div>
          <Badge variant={lowStockAlerts.length > 0 ? "warning" : "success"} className="text-xs">
            {lowStockAlerts.length} item(s) flagged
          </Badge>
        </CardHeader>
        <CardContent className="p-0">
          {loadingLowStock ? (
            <LoadingPage message="Checking inventory levels..." />
          ) : lowStockAlerts.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              All registered inventory items satisfy minimum safe stock requirements.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Current Stock</TableHead>
                  <TableHead className="text-right">Min Stock</TableHead>
                  <TableHead className="text-right">Reorder Level</TableHead>
                  <TableHead>Urgency</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lowStockAlerts.map((item: LowStockAlert) => (
                  <TableRow key={item.product_id}>
                    <TableCell className="font-mono text-xs font-bold text-blue-700">
                      {item.sku}
                    </TableCell>
                    <TableCell className="font-semibold text-slate-900">{item.name}</TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {item.category_name || "Uncategorized"}
                    </TableCell>
                    <TableCell className="text-right font-bold text-red-600">
                      {item.current_stock} {item.unit}
                    </TableCell>
                    <TableCell className="text-right text-xs text-slate-500">
                      {item.min_stock} {item.unit}
                    </TableCell>
                    <TableCell className="text-right text-xs text-slate-500">
                      {item.reorder_level} {item.unit}
                    </TableCell>
                    <TableCell>
                      <Badge variant={item.status === "critical" ? "destructive" : "warning"}>
                        {item.status === "critical" ? "Critical Minimum" : "Below Reorder"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href="/movements">
                        <Button size="sm" variant="outline" className="h-7 text-xs">
                          Receive Stock <ArrowRight className="h-3 w-3 ml-1" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Expiry Tracking Section */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-lg flex items-center space-x-2 text-slate-900">
              <Clock className="h-5 w-5 text-rose-500" />
              <span>Lot & Batch Expiry Tracking</span>
            </CardTitle>
            <CardDescription>
              Batches nearing expiration to enforce FIFO/FEFO picking and minimize wastage.
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-500 font-medium">Window:</span>
            <select
              className="h-8 rounded-md border border-input bg-transparent px-2 text-xs focus:outline-none"
              value={expiryDays}
              onChange={(e) => setExpiryDays(Number(e.target.value))}
            >
              <option value="15">Within 15 days</option>
              <option value="30">Within 30 days</option>
              <option value="60">Within 60 days</option>
              <option value="90">Within 90 days</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loadingExpiry ? (
            <LoadingPage message="Evaluating batch expiration dates..." />
          ) : expiryAlerts.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No batches expiring within the next {expiryDays} days.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch / Lot #</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Expiry Date</TableHead>
                  <TableHead>Days Remaining</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead>Location</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {expiryAlerts.map((b: ExpiryAlert) => (
                  <TableRow key={b.batch_id}>
                    <TableCell className="font-mono text-xs font-bold text-slate-800">
                      {b.batch_number}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-blue-700">{b.sku}</TableCell>
                    <TableCell className="font-medium text-slate-900">{b.name}</TableCell>
                    <TableCell className="font-mono text-xs text-rose-600 font-semibold">
                      {formatShortDate(b.expiry_date)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={b.days_until_expiry <= 7 ? "destructive" : "warning"}
                        className="text-xs"
                      >
                        {b.days_until_expiry < 0
                          ? `Expired (${Math.abs(b.days_until_expiry)}d ago)`
                          : `${b.days_until_expiry} days left`}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-bold text-slate-900">
                      {b.quantity}
                    </TableCell>
                    <TableCell className="text-xs text-slate-600 font-mono">
                      {b.location_name}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

