"use client"

import React, { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  ArrowDownLeft,
  ArrowLeftRight,
  ArrowUpRight,
  Barcode,
  History,
  QrCode,
  Search,
} from "lucide-react"
import toast from "react-hot-toast"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingPage } from "@/components/ui/loading"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { movementsApi, productsApi, warehousesApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { MovementResponse, Product } from "@/types"

export default function MovementsPage() {
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<"operations" | "history">("operations")
  const [operationType, setOperationType] = useState<"RECEIVE" | "ISSUE" | "TRANSFER">("RECEIVE")

  // Common Form States
  const [barcodeInput, setBarcodeInput] = useState("")
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [locationSearch, setLocationSearch] = useState("")
  const [locationId, setLocationId] = useState<number | undefined>()
  const [fromLocationId, setFromLocationId] = useState<number | undefined>()
  const [toLocationId, setToLocationId] = useState<number | undefined>()
  const [quantity, setQuantity] = useState<number>(1)
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")

  // Receive-specific
  const [batchNumber, setBatchNumber] = useState("")
  const [expiryDate, setExpiryDate] = useState("")

  // History Query State
  const [historyPage, setHistoryPage] = useState(1)
  const [historyType, setHistoryType] = useState<string>("")
  const [historySearch, setHistorySearch] = useState("")

  // Barcode Lookup Handler
  const handleBarcodeLookup = async (codeToLookup: string) => {
    if (!codeToLookup.trim()) return
    try {
      const p = await productsApi.lookupBarcode(codeToLookup.trim())
      setSelectedProduct(p)
      toast.success(`Scanned: ${p.sku} - ${p.name}`)
      setBarcodeInput("")
    } catch {
      // Try SKU lookup
      try {
        const p = await productsApi.lookupSku(codeToLookup.trim())
        setSelectedProduct(p)
        toast.success(`Identified SKU: ${p.sku} - ${p.name}`)
        setBarcodeInput("")
      } catch {
        toast.error(`No product matches code "${codeToLookup}"`)
      }
    }
  }

  // Location search query
  const { data: matchedLocations = [] } = useQuery({
    queryKey: ["search-locations", locationSearch],
    queryFn: () => (locationSearch.trim() ? warehousesApi.searchLocations(locationSearch.trim()) : Promise.resolve([])),
    enabled: locationSearch.trim().length > 0,
  })

  // Movements History Query
  const { data: movementHistory, isLoading: loadingHistory } = useQuery({
    queryKey: ["movements-history", historyPage, historyType, historySearch],
    queryFn: () =>
      movementsApi.list({
        page: historyPage,
        page_size: 20,
        movement_type: historyType || undefined,
        search: historySearch || undefined,
      }),
    enabled: activeTab === "history",
  })

  // Mutations
  const receiveMutation = useMutation({
    mutationFn: movementsApi.receive,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
      queryClient.invalidateQueries({ queryKey: ["inventory-stock"] })
      queryClient.invalidateQueries({ queryKey: ["products"] })
      toast.success("Stock received successfully")
      resetForm()
      setActiveTab("history")
    },
  })

  const issueMutation = useMutation({
    mutationFn: movementsApi.issue,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
      queryClient.invalidateQueries({ queryKey: ["inventory-stock"] })
      queryClient.invalidateQueries({ queryKey: ["products"] })
      toast.success("Stock issued successfully")
      resetForm()
      setActiveTab("history")
    },
  })

  const transferMutation = useMutation({
    mutationFn: movementsApi.transfer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
      queryClient.invalidateQueries({ queryKey: ["inventory-stock"] })
      toast.success("Stock transferred successfully")
      resetForm()
      setActiveTab("history")
    },
  })

  const resetForm = () => {
    setSelectedProduct(null)
    setBarcodeInput("")
    setLocationId(undefined)
    setFromLocationId(undefined)
    setToLocationId(undefined)
    setQuantity(1)
    setReference("")
    setNotes("")
    setBatchNumber("")
    setExpiryDate("")
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Inventory Movements</h1>
          <p className="text-sm text-slate-500">
            Execute receipts, issues, and transfers with barcode scanner support and atomic transactions.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-200/70 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab("operations")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1 transition-all ${
              activeTab === "operations"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <ArrowLeftRight className="h-3.5 w-3.5 mr-1" />
            New Operation
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1 transition-all ${
              activeTab === "history"
                ? "bg-white text-blue-700 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <History className="h-3.5 w-3.5 mr-1" />
            Movement History
          </button>
        </div>
      </div>

      {activeTab === "operations" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Scanner & Product Selector Panel */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle className="text-base flex items-center">
                <Barcode className="h-5 w-5 mr-2 text-blue-600" /> Scanner & Lookup
              </CardTitle>
              <CardDescription>
                Use USB/Bluetooth barcode scanner, tablet camera, or type SKU/barcode.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="scannerInput">Scan Barcode / QR / SKU</Label>
                <div className="flex space-x-2 mt-1">
                  <Input
                    id="scannerInput"
                    placeholder="Aim scanner and press trigger..."
                    value={barcodeInput}
                    onChange={(e) => setBarcodeInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault()
                        handleBarcodeLookup(barcodeInput)
                      }
                    }}
                    autoFocus
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => handleBarcodeLookup(barcodeInput)}
                  >
                    Find
                  </Button>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Scanner automatically sends Enter key after scan.
                </p>
              </div>

              {/* Selected Product Card */}
              {selectedProduct ? (
                <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-xs font-bold text-blue-700">
                        {selectedProduct.sku}
                      </span>
                      <h4 className="font-semibold text-slate-900 text-sm">{selectedProduct.name}</h4>
                    </div>
                    <Badge variant="outline">{selectedProduct.unit}</Badge>
                  </div>
                  <div className="text-xs text-slate-600 space-y-0.5">
                    <div>Barcode: {selectedProduct.barcode || "N/A"}</div>
                    <div>
                      Total On Hand:{" "}
                      <span className="font-bold text-slate-900">
                        {selectedProduct.total_stock || 0} {selectedProduct.unit}
                      </span>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="w-full text-xs text-slate-500 hover:text-slate-800"
                    onClick={() => setSelectedProduct(null)}
                  >
                    Clear selection
                  </Button>
                </div>
              ) : (
                <div className="p-6 rounded-xl border-2 border-dashed border-slate-200 text-center text-slate-400 text-xs">
                  Scan a barcode or enter SKU to link this movement.
                </div>
              )}
            </CardContent>
          </Card>

          {/* Operation Form Panel */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3 border-b">
              {/* Operation type selector */}
              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant={operationType === "RECEIVE" ? "default" : "outline"}
                  onClick={() => setOperationType("RECEIVE")}
                  className={operationType === "RECEIVE" ? "bg-blue-600" : ""}
                >
                  <ArrowDownLeft className="mr-1.5 h-4 w-4" /> Receive Inward
                </Button>
                <Button
                  size="sm"
                  variant={operationType === "ISSUE" ? "default" : "outline"}
                  onClick={() => setOperationType("ISSUE")}
                  className={operationType === "ISSUE" ? "bg-red-600 hover:bg-red-700" : ""}
                >
                  <ArrowUpRight className="mr-1.5 h-4 w-4" /> Issue Outward
                </Button>
                <Button
                  size="sm"
                  variant={operationType === "TRANSFER" ? "default" : "outline"}
                  onClick={() => setOperationType("TRANSFER")}
                  className={operationType === "TRANSFER" ? "bg-amber-600 hover:bg-amber-700" : ""}
                >
                  <ArrowLeftRight className="mr-1.5 h-4 w-4" /> Relocate / Transfer
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4 pt-4">
              {/* Location Selection */}
              {operationType === "RECEIVE" && (
                <div>
                  <Label>Destination Storage Location (Search by Code or Path) *</Label>
                  <Input
                    placeholder="Type to search e.g. BIN-01 or WH-MAIN..."
                    value={locationSearch}
                    onChange={(e) => setLocationSearch(e.target.value)}
                  />
                  {matchedLocations.length > 0 && (
                    <div className="mt-1 max-h-36 overflow-y-auto border rounded-md divide-y bg-white shadow-sm">
                      {matchedLocations.map((loc) => (
                        <div
                          key={loc.id}
                          onClick={() => {
                            setLocationId(loc.id)
                            setLocationSearch(loc.full_path)
                          }}
                          className={`p-2 text-xs cursor-pointer hover:bg-blue-50 ${
                            locationId === loc.id ? "bg-blue-100 font-bold text-blue-900" : "text-slate-700"
                          }`}
                        >
                          <span className="font-mono font-semibold">{loc.full_path}</span> - {loc.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {operationType === "ISSUE" && (
                <div>
                  <Label>Source Storage Location to Deduct From *</Label>
                  <Input
                    placeholder="Type to search e.g. BIN-01..."
                    value={locationSearch}
                    onChange={(e) => setLocationSearch(e.target.value)}
                  />
                  {matchedLocations.length > 0 && (
                    <div className="mt-1 max-h-36 overflow-y-auto border rounded-md divide-y bg-white shadow-sm">
                      {matchedLocations.map((loc) => (
                        <div
                          key={loc.id}
                          onClick={() => {
                            setLocationId(loc.id)
                            setLocationSearch(loc.full_path)
                          }}
                          className={`p-2 text-xs cursor-pointer hover:bg-blue-50 ${
                            locationId === loc.id ? "bg-blue-100 font-bold text-blue-900" : "text-slate-700"
                          }`}
                        >
                          <span className="font-mono font-semibold">{loc.full_path}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {operationType === "TRANSFER" && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Source Location (From)</Label>
                    <Input
                      placeholder="Source location code..."
                      onChange={(e) => {
                        warehousesApi.searchLocations(e.target.value).then((res) => {
                          if (res[0]) setFromLocationId(res[0].id)
                        })
                      }}
                    />
                  </div>
                  <div>
                    <Label>Destination Location (To)</Label>
                    <Input
                      placeholder="Destination location code..."
                      onChange={(e) => {
                        warehousesApi.searchLocations(e.target.value).then((res) => {
                          if (res[0]) setToLocationId(res[0].id)
                        })
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Quantity */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Quantity to Move *</Label>
                  <Input
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                  />
                </div>
                <div>
                  <Label>Reference Number (PO / DO / Transfer #)</Label>
                  <Input
                    placeholder="e.g. PO-2026-0042"
                    value={reference}
                    onChange={(e) => setReference(e.target.value)}
                  />
                </div>
              </div>

              {/* Batch & Expiry (Receive only) */}
              {operationType === "RECEIVE" && (
                <div className="grid grid-cols-2 gap-4 pt-1">
                  <div>
                    <Label>Batch / Lot Number (Optional)</Label>
                    <Input
                      placeholder="e.g. BATCH-2026-A"
                      value={batchNumber}
                      onChange={(e) => setBatchNumber(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Expiration Date (Optional)</Label>
                    <Input
                      type="date"
                      value={expiryDate}
                      onChange={(e) => setExpiryDate(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div>
                <Label>Notes / Reason</Label>
                <Input
                  placeholder="Additional transaction comments..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />
              </div>

              <div className="pt-2">
                <Button
                  className="w-full bg-blue-600 hover:bg-blue-700 h-10"
                  disabled={
                    !selectedProduct ||
                    quantity <= 0 ||
                    (operationType === "TRANSFER"
                      ? !fromLocationId || !toLocationId
                      : !locationId)
                  }
                  onClick={() => {
                    if (operationType === "RECEIVE") {
                      receiveMutation.mutate({
                        product_id: selectedProduct!.id,
                        location_id: locationId!,
                        quantity,
                        batch_number: batchNumber || undefined,
                        expiry_date: expiryDate || undefined,
                        reference_number: reference || undefined,
                        notes: notes || undefined,
                      })
                    } else if (operationType === "ISSUE") {
                      issueMutation.mutate({
                        product_id: selectedProduct!.id,
                        location_id: locationId!,
                        quantity,
                        reference_number: reference || undefined,
                        notes: notes || undefined,
                      })
                    } else if (operationType === "TRANSFER") {
                      transferMutation.mutate({
                        product_id: selectedProduct!.id,
                        from_location_id: fromLocationId!,
                        to_location_id: toLocationId!,
                        quantity,
                        reference_number: reference || undefined,
                        notes: notes || undefined,
                      })
                    }
                  }}
                >
                  Confirm & Post {operationType}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        /* Movement History Log */
        <Card>
          <CardHeader className="p-4 border-b flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search movements by SKU, product name, or reference..."
                className="pl-9"
                value={historySearch}
                onChange={(e) => {
                  setHistorySearch(e.target.value)
                  setHistoryPage(1)
                }}
              />
            </div>
            <div className="w-full sm:w-48">
              <select
                className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                value={historyType}
                onChange={(e) => {
                  setHistoryType(e.target.value)
                  setHistoryPage(1)
                }}
              >
                <option value="">All Movement Types</option>
                <option value="RECEIVE">RECEIVE</option>
                <option value="ISSUE">ISSUE</option>
                <option value="TRANSFER">TRANSFER</option>
              </select>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loadingHistory ? (
              <LoadingPage message="Loading movements log..." />
            ) : !movementHistory || movementHistory.items.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                <History className="h-10 w-10 mx-auto text-slate-300 mb-2" />
                <p className="font-semibold text-slate-700">No movement records found</p>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>SKU</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead>From Location</TableHead>
                      <TableHead>To Location</TableHead>
                      <TableHead className="text-right">Quantity</TableHead>
                      <TableHead>Reference</TableHead>
                      <TableHead>Performed By</TableHead>
                      <TableHead>Timestamp</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {movementHistory.items.map((m: MovementResponse) => (
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
                            className="text-[10px] uppercase font-bold"
                          >
                            {m.movement_type}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs font-bold text-blue-700">
                          {m.product_sku}
                        </TableCell>
                        <TableCell className="font-medium text-slate-900">{m.product_name}</TableCell>
                        <TableCell className="text-xs text-slate-500">{m.from_location_name || "-"}</TableCell>
                        <TableCell className="text-xs text-slate-500">{m.to_location_name || "-"}</TableCell>
                        <TableCell className="text-right font-mono font-bold">
                          {m.movement_type === "ISSUE" ? `-${m.quantity}` : `+${m.quantity}`}
                        </TableCell>
                        <TableCell className="text-xs text-slate-600 font-mono">
                          {m.reference_number || "-"}
                        </TableCell>
                        <TableCell className="text-xs text-slate-700">{m.performed_by_name}</TableCell>
                        <TableCell className="text-xs text-slate-400">{formatDate(m.created_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {movementHistory.total_pages > 1 && (
                  <div className="p-4 border-t flex items-center justify-between text-sm text-slate-600">
                    <div>
                      Page {movementHistory.page} of {movementHistory.total_pages} ({movementHistory.total} movements)
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={historyPage <= 1}
                        onClick={() => setHistoryPage((p) => Math.max(1, p - 1))}
                      >
                        Previous
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={historyPage >= movementHistory.total_pages}
                        onClick={() => setHistoryPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

