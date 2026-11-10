"use client"

import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { AlertCircle, Boxes, CheckCircle2, Filter, Layers, Search } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { inventoryApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { InventoryStock, StockSummary } from "@/types"

export default function InventoryPage() {
  const [viewMode, setViewMode] = useState<"detailed" | "summary">("detailed")
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [lowStockOnly, setLowStockOnly] = useState(false)

  // Detailed stock query
  const { data: stockData, isLoading: loadingDetailed } = useQuery({
    queryKey: ["inventory-stock", page, search, lowStockOnly],
    queryFn: () =>
      inventoryApi.listStock({
        page,
        page_size: 20,
        search: search || undefined,
        low_stock_only: lowStockOnly,
      }),
    enabled: viewMode === "detailed",
  })

  // Summary stock query
  const { data: summaryData = [], isLoading: loadingSummary } = useQuery({
    queryKey: ["inventory-summary", search],
    queryFn: () => inventoryApi.stockSummary({ search: search || undefined }),
    enabled: viewMode === "summary",
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inventory Stock</h1>
          <p className="text-sm text-slate-500">
            Real-time physical inventory balances tracked across products, storage locations, and batches.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex bg-slate-200/70 p-1 rounded-lg">
          <button
            onClick={() => setViewMode("detailed")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              viewMode === "detailed"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Location Balances
          </button>
          <button
            onClick={() => setViewMode("summary")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
              viewMode === "summary"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Product Summary
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by SKU, product name, or location..."
              className="pl-9"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
            />
          </div>

          {viewMode === "detailed" && (
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="lowStockToggle"
                checked={lowStockOnly}
                onChange={(e) => {
                  setLowStockOnly(e.target.checked)
                  setPage(1)
                }}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="lowStockToggle" className="text-sm font-medium text-slate-700">
                Low stock only
              </label>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content */}
      <Card>
        <CardContent className="p-0">
          {viewMode === "detailed" ? (
            loadingDetailed ? (
              <LoadingPage message="Loading storage location balances..." />
            ) : !stockData || stockData.items.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <Boxes className="h-10 w-10 mx-auto text-slate-300 mb-2" />
                <p className="font-semibold text-slate-700">No stock records found</p>
                <p className="text-sm">Receive items into warehouse locations to see quantities here.</p>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>SKU</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>Location Path</TableHead>
                      <TableHead>Batch</TableHead>
                      <TableHead className="text-right">Quantity</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Last Updated</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stockData.items.map((stock: InventoryStock) => (
                      <TableRow key={stock.id}>
                        <TableCell className="font-mono text-xs font-bold text-blue-700">
                          {stock.product_sku}
                        </TableCell>
                        <TableCell className="font-medium text-slate-900">
                          {stock.product_name}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-slate-700">
                          <span className="bg-slate-100 px-2 py-1 rounded">
                            {stock.location_path || stock.location_code}
                          </span>
                        </TableCell>
                        <TableCell className="text-xs text-slate-600">
                          {stock.batch_number ? (
                            <span>
                              {stock.batch_number}
                              {stock.expiry_date && (
                                <span className="block text-[10px] text-slate-400">
                                  Exp: {stock.expiry_date}
                                </span>
                              )}
                            </span>
                          ) : (
                            "-"
                          )}
                        </TableCell>
                        <TableCell className="text-right font-mono font-bold text-base">
                          <span
                            className={
                              stock.stock_status === "critical"
                                ? "text-red-600 font-extrabold"
                                : stock.stock_status === "low"
                                ? "text-amber-600 font-bold"
                                : "text-emerald-700"
                            }
                          >
                            {stock.quantity}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              stock.stock_status === "critical"
                                ? "destructive"
                                : stock.stock_status === "low"
                                ? "warning"
                                : "success"
                            }
                          >
                            {stock.stock_status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-slate-400">
                          {formatDate(stock.last_updated)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {stockData.total_pages > 1 && (
                  <div className="p-4 border-t flex items-center justify-between text-sm text-slate-600">
                    <div>
                      Page {stockData.page} of {stockData.total_pages} ({stockData.total} items)
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        Previous
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page >= stockData.total_pages}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )
          ) : (
            /* Summary View */
            loadingSummary ? (
              <LoadingPage message="Aggregating product balances..." />
            ) : summaryData.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <Boxes className="h-10 w-10 mx-auto text-slate-300 mb-2" />
                <p className="font-semibold text-slate-700">No inventory balances</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Product</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Total Quantity</TableHead>
                    <TableHead className="text-right">Locations</TableHead>
                    <TableHead className="text-right">Reorder Level</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summaryData.map((s: StockSummary) => (
                    <TableRow key={s.product_id}>
                      <TableCell className="font-mono text-xs font-bold text-blue-700">{s.sku}</TableCell>
                      <TableCell className="font-medium text-slate-900">{s.name}</TableCell>
                      <TableCell className="text-xs text-slate-600">{s.category_name || "Uncategorized"}</TableCell>
                      <TableCell className="text-right font-bold text-base">
                        <span
                          className={
                            s.stock_status === "critical"
                              ? "text-red-600"
                              : s.stock_status === "low"
                              ? "text-amber-600"
                              : "text-emerald-700"
                          }
                        >
                          {s.total_quantity} {s.unit}
                        </span>
                      </TableCell>
                      <TableCell className="text-right text-xs text-slate-600">
                        {s.location_count} bin(s)
                      </TableCell>
                      <TableCell className="text-right text-xs text-slate-500">
                        {s.reorder_level} {s.unit}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            s.stock_status === "critical"
                              ? "destructive"
                              : s.stock_status === "low"
                              ? "warning"
                              : "success"
                          }
                        >
                          {s.stock_status}
                        </Badge>
                      </TableCell>
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

