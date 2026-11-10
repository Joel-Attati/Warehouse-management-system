"use client"

import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Download, FileSpreadsheet, Filter, RefreshCw } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { LoadingPage } from "@/components/ui/loading"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { productsApi, reportsApi, warehousesApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { InventoryStock, MovementResponse } from "@/types"

export default function ReportsPage() {
  const [reportType, setReportType] = useState<"inventory" | "movements">("inventory")

  // Inventory Report Filters
  const [selectedWhId, setSelectedWhId] = useState<number | undefined>()
  const [selectedCatId, setSelectedCatId] = useState<number | undefined>()

  // Movements Report Filters
  const [movType, setMovType] = useState<string>("")
  const [dateFrom, setDateFrom] = useState<string>("")
  const [dateTo, setDateTo] = useState<string>("")

  // Meta queries
  const { data: warehouses = [] } = useQuery({
    queryKey: ["warehouses"],
    queryFn: warehousesApi.list,
  })

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.listCategories,
  })

  // Report Queries
  const { data: inventoryData = [], isLoading: loadingInventory, refetch: refetchInv } = useQuery({
    queryKey: ["report-inventory", selectedWhId, selectedCatId],
    queryFn: () =>
      reportsApi.inventory({
        warehouse_id: selectedWhId,
        category_id: selectedCatId,
      }),
    enabled: reportType === "inventory",
  })

  const { data: movementsData = [], isLoading: loadingMovements, refetch: refetchMov } = useQuery({
    queryKey: ["report-movements", movType, dateFrom, dateTo],
    queryFn: () =>
      reportsApi.movements({
        movement_type: movType || undefined,
        date_from: dateFrom ? `${dateFrom}T00:00:00Z` : undefined,
        date_to: dateTo ? `${dateTo}T23:59:59Z` : undefined,
      }),
    enabled: reportType === "movements",
  })

  const handleExportCsv = () => {
    if (reportType === "inventory") {
      const url = reportsApi.exportInventoryCsvUrl(selectedWhId, selectedCatId)
      window.open(url, "_blank")
    } else {
      const df = dateFrom ? `${dateFrom}T00:00:00Z` : undefined
      const dt = dateTo ? `${dateTo}T23:59:59Z` : undefined
      const url = reportsApi.exportMovementsCsvUrl(movType || undefined, df, dt)
      window.open(url, "_blank")
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reports & Data Export</h1>
          <p className="text-sm text-slate-500">
            Generate operational audit reports and export tabular datasets to CSV for spreadsheets and ERP integration.
          </p>
        </div>

        {/* Export Action */}
        <Button onClick={handleExportCsv} className="bg-emerald-600 hover:bg-emerald-700 text-white">
          <Download className="mr-2 h-4 w-4" />
          Export to CSV
        </Button>
      </div>

      {/* Report Switcher & Filter Bar */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="flex bg-slate-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setReportType("inventory")}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                reportType === "inventory"
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
              <span>Full Inventory Report</span>
            </button>
            <button
              onClick={() => setReportType("movements")}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                reportType === "movements"
                  ? "bg-white text-blue-700 shadow-sm"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
              <span>Movements Audit Report</span>
            </button>
          </div>

          {/* Conditional Filters */}
          {reportType === "inventory" ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Filter Warehouse:</span>
                <select
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none"
                  value={selectedWhId || ""}
                  onChange={(e) => setSelectedWhId(e.target.value ? Number(e.target.value) : undefined)}
                >
                  <option value="">All Warehouses</option>
                  {warehouses.map((wh) => (
                    <option key={wh.id} value={wh.id}>
                      {wh.code} - {wh.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <span className="text-xs text-slate-500 block mb-1">Filter Category:</span>
                <select
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none"
                  value={selectedCatId || ""}
                  onChange={(e) => setSelectedCatId(e.target.value ? Number(e.target.value) : undefined)}
                >
                  <option value="">All Categories</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-end">
                <Button variant="outline" size="sm" onClick={() => refetchInv()} className="h-9">
                  <RefreshCw className="h-4 w-4 mr-1.5" /> Refresh Preview
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 pt-2 border-t">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Movement Type:</span>
                <select
                  className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none"
                  value={movType}
                  onChange={(e) => setMovType(e.target.value)}
                >
                  <option value="">All Types</option>
                  <option value="RECEIVE">RECEIVE</option>
                  <option value="ISSUE">ISSUE</option>
                  <option value="TRANSFER">TRANSFER</option>
                </select>
              </div>

              <div>
                <span className="text-xs text-slate-500 block mb-1">Date From:</span>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="h-9"
                />
              </div>

              <div>
                <span className="text-xs text-slate-500 block mb-1">Date To:</span>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="h-9"
                />
              </div>

              <div className="flex items-end">
                <Button variant="outline" size="sm" onClick={() => refetchMov()} className="h-9">
                  <RefreshCw className="h-4 w-4 mr-1.5" /> Refresh Preview
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Table Preview */}
      <Card>
        <CardHeader className="py-3 px-4 border-b">
          <CardTitle className="text-sm font-semibold text-slate-700">
            {reportType === "inventory" ? "Inventory Balance Records" : "Transaction Log Records"}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {reportType === "inventory" ? (
            loadingInventory ? (
              <LoadingPage message="Generating report preview..." />
            ) : inventoryData.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">No matching inventory records.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Location Path</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Product Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Batch</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {inventoryData.slice(0, 50).map((row: InventoryStock) => (
                    <TableRow key={row.id}>
                      <TableCell className="font-mono text-xs font-semibold text-slate-700">
                        {row.location_path || row.location_code}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-blue-700">
                        {row.product_sku}
                      </TableCell>
                      <TableCell className="font-medium text-slate-900">{row.product_name}</TableCell>
                      <TableCell className="text-xs text-slate-500">{row.category_name || "-"}</TableCell>
                      <TableCell className="text-xs font-mono">{row.batch_number || "-"}</TableCell>
                      <TableCell className="text-right font-bold text-slate-900">{row.quantity}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            row.stock_status === "critical"
                              ? "destructive"
                              : row.stock_status === "low"
                              ? "warning"
                              : "success"
                          }
                        >
                          {row.stock_status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-slate-400">{formatDate(row.last_updated)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )
          ) : (
            loadingMovements ? (
              <LoadingPage message="Generating movement report..." />
            ) : movementsData.length === 0 ? (
              <div className="p-8 text-center text-sm text-slate-500">No movement records match filters.</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>From</TableHead>
                    <TableHead>To</TableHead>
                    <TableHead className="text-right">Qty</TableHead>
                    <TableHead>Ref</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {movementsData.slice(0, 50).map((row: MovementResponse) => (
                    <TableRow key={row.id}>
                      <TableCell>
                        <Badge
                          variant={
                            row.movement_type === "RECEIVE"
                              ? "default"
                              : row.movement_type === "ISSUE"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-[10px]"
                        >
                          {row.movement_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold text-blue-700">{row.product_sku}</TableCell>
                      <TableCell className="font-medium text-slate-900">{row.product_name}</TableCell>
                      <TableCell className="text-xs text-slate-500">{row.from_location_name || "-"}</TableCell>
                      <TableCell className="text-xs text-slate-500">{row.to_location_name || "-"}</TableCell>
                      <TableCell className="text-right font-mono font-bold">{row.quantity}</TableCell>
                      <TableCell className="text-xs text-slate-600 font-mono">{row.reference_number || "-"}</TableCell>
                      <TableCell className="text-xs text-slate-700">{row.performed_by_name}</TableCell>
                      <TableCell className="text-xs text-slate-400">{formatDate(row.created_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )
          )}
        </CardContent>
      </Card>
    </div>
  )
}

