"use client"

import React, { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ChevronRight, FolderPlus, Layers, MapPin, Plus, Warehouse as WhIcon } from "lucide-react"
import toast from "react-hot-toast"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingPage } from "@/components/ui/loading"
import { warehousesApi } from "@/lib/api"
import { useAuthStore } from "@/stores/auth"
import { StorageLocation, Warehouse } from "@/types"

export default function WarehousesPage() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canManage = user?.role === "admin" || user?.role === "manager"

  const [selectedWh, setSelectedWh] = useState<Warehouse | null>(null)
  const [selectedAisle, setSelectedAisle] = useState<any | null>(null)
  const [selectedRack, setSelectedRack] = useState<any | null>(null)
  const [selectedShelf, setSelectedShelf] = useState<any | null>(null)

  // Dialog states
  const [openWhModal, setOpenWhModal] = useState(false)
  const [openAisleModal, setOpenAisleModal] = useState(false)
  const [openRackModal, setOpenRackModal] = useState(false)
  const [openShelfModal, setOpenShelfModal] = useState(false)
  const [openLocationModal, setOpenLocationModal] = useState(false)

  // Form states
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [address, setAddress] = useState("")

  // Fetch Warehouses
  const { data: warehouses = [], isLoading: loadingWh } = useQuery({
    queryKey: ["warehouses"],
    queryFn: warehousesApi.list,
  })

  // Fetch Aisles
  const { data: aisles = [], isLoading: loadingAisles } = useQuery({
    queryKey: ["aisles", selectedWh?.id],
    queryFn: () => (selectedWh ? warehousesApi.getAisles(selectedWh.id) : Promise.resolve([])),
    enabled: !!selectedWh,
  })

  // Fetch Racks
  const { data: racks = [], isLoading: loadingRacks } = useQuery({
    queryKey: ["racks", selectedAisle?.id],
    queryFn: () => (selectedAisle ? warehousesApi.getRacks(selectedAisle.id) : Promise.resolve([])),
    enabled: !!selectedAisle,
  })

  // Fetch Shelves
  const { data: shelves = [], isLoading: loadingShelves } = useQuery({
    queryKey: ["shelves", selectedRack?.id],
    queryFn: () => (selectedRack ? warehousesApi.getShelves(selectedRack.id) : Promise.resolve([])),
    enabled: !!selectedRack,
  })

  // Fetch Locations
  const { data: locations = [], isLoading: loadingLocations } = useQuery({
    queryKey: ["locations", selectedShelf?.id],
    queryFn: () => (selectedShelf ? warehousesApi.getLocations(selectedShelf.id) : Promise.resolve([])),
    enabled: !!selectedShelf,
  })

  // Create Warehouse Mutation
  const createWhMutation = useMutation({
    mutationFn: warehousesApi.create,
    onSuccess: (newWh) => {
      queryClient.invalidateQueries({ queryKey: ["warehouses"] })
      toast.success(`Warehouse ${newWh.code} created`)
      setOpenWhModal(false)
      resetForm()
    },
  })

  // Create Aisle Mutation
  const createAisleMutation = useMutation({
    mutationFn: (data: any) => warehousesApi.createAisle(selectedWh!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["aisles", selectedWh?.id] })
      queryClient.invalidateQueries({ queryKey: ["warehouses"] })
      toast.success("Aisle created")
      setOpenAisleModal(false)
      resetForm()
    },
  })

  // Create Rack Mutation
  const createRackMutation = useMutation({
    mutationFn: (data: any) => warehousesApi.createRack(selectedAisle!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["racks", selectedAisle?.id] })
      toast.success("Rack created")
      setOpenRackModal(false)
      resetForm()
    },
  })

  // Create Shelf Mutation
  const createShelfMutation = useMutation({
    mutationFn: (data: any) => warehousesApi.createShelf(selectedRack!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shelves", selectedRack?.id] })
      toast.success("Shelf created")
      setOpenShelfModal(false)
      resetForm()
    },
  })

  // Create Location Mutation
  const createLocationMutation = useMutation({
    mutationFn: (data: any) => warehousesApi.createLocation(selectedShelf!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["locations", selectedShelf?.id] })
      toast.success("Storage location created")
      setOpenLocationModal(false)
      resetForm()
    },
  })

  const resetForm = () => {
    setCode("")
    setName("")
    setDescription("")
    setAddress("")
  }

  if (loadingWh) return <LoadingPage message="Loading warehouse hierarchy..." />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Warehouse Hierarchy</h1>
          <p className="text-sm text-slate-500">
            Organize storage locations by Warehouse → Aisle → Rack → Shelf → Storage Location.
          </p>
        </div>
        {canManage && (
          <Button onClick={() => setOpenWhModal(true)} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="mr-2 h-4 w-4" />
            Add Warehouse
          </Button>
        )}
      </div>

      {/* Breadcrumb Trail */}
      <div className="flex items-center space-x-2 text-sm text-slate-600 bg-white p-3 rounded-lg border shadow-sm">
        <span className="font-semibold text-slate-800">Hierarchy:</span>
        <span
          className={`cursor-pointer hover:underline ${selectedWh ? "text-blue-600" : "font-bold text-slate-900"}`}
          onClick={() => {
            setSelectedAisle(null)
            setSelectedRack(null)
            setSelectedShelf(null)
          }}
        >
          {selectedWh ? selectedWh.name : "All Warehouses"}
        </span>

        {selectedWh && (
          <>
            <ChevronRight className="h-4 w-4 text-slate-400" />
            <span
              className={`cursor-pointer hover:underline ${selectedAisle ? "text-blue-600" : "font-bold text-slate-900"}`}
              onClick={() => {
                setSelectedRack(null)
                setSelectedShelf(null)
              }}
            >
              {selectedAisle ? `Aisle ${selectedAisle.code}` : "Select Aisle"}
            </span>
          </>
        )}

        {selectedAisle && (
          <>
            <ChevronRight className="h-4 w-4 text-slate-400" />
            <span
              className={`cursor-pointer hover:underline ${selectedRack ? "text-blue-600" : "font-bold text-slate-900"}`}
              onClick={() => setSelectedShelf(null)}
            >
              {selectedRack ? `Rack ${selectedRack.code}` : "Select Rack"}
            </span>
          </>
        )}

        {selectedRack && (
          <>
            <ChevronRight className="h-4 w-4 text-slate-400" />
            <span className="font-bold text-slate-900">
              {selectedShelf ? `Shelf ${selectedShelf.code}` : "Select Shelf"}
            </span>
          </>
        )}
      </div>

      {/* Main Hierarchy Drill-down */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Step 1: Warehouses */}
        <Card className="col-span-1">
          <CardHeader className="p-4 pb-2 border-b flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center">
              <WhIcon className="mr-2 h-4 w-4 text-blue-600" /> Warehouses
            </CardTitle>
          </CardHeader>
          <CardContent className="p-2 space-y-1">
            {warehouses.length === 0 ? (
              <p className="text-xs text-slate-500 p-3">No warehouses registered yet.</p>
            ) : (
              warehouses.map((wh) => (
                <div
                  key={wh.id}
                  onClick={() => {
                    setSelectedWh(wh)
                    setSelectedAisle(null)
                    setSelectedRack(null)
                    setSelectedShelf(null)
                  }}
                  className={`p-2.5 rounded-lg text-sm cursor-pointer transition-all flex items-center justify-between ${
                    selectedWh?.id === wh.id
                      ? "bg-blue-50 border border-blue-200 text-blue-900 font-semibold"
                      : "hover:bg-slate-50 text-slate-700"
                  }`}
                >
                  <div>
                    <div className="font-mono text-xs text-blue-600">{wh.code}</div>
                    <div>{wh.name}</div>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">
                    {wh.aisle_count || 0} aisles
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Step 2: Aisles */}
        <Card className="col-span-1">
          <CardHeader className="p-4 pb-2 border-b flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center">
              <Layers className="mr-2 h-4 w-4 text-indigo-600" /> Aisles
            </CardTitle>
            {selectedWh && canManage && (
              <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => setOpenAisleModal(true)}>
                <Plus className="h-3 w-3 mr-1" /> Add
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-2 space-y-1">
            {!selectedWh ? (
              <p className="text-xs text-slate-400 p-3">Select a warehouse first</p>
            ) : aisles.length === 0 ? (
              <p className="text-xs text-slate-500 p-3">No aisles in this warehouse.</p>
            ) : (
              aisles.map((a: any) => (
                <div
                  key={a.id}
                  onClick={() => {
                    setSelectedAisle(a)
                    setSelectedRack(null)
                    setSelectedShelf(null)
                  }}
                  className={`p-2.5 rounded-lg text-sm cursor-pointer transition-all flex items-center justify-between ${
                    selectedAisle?.id === a.id
                      ? "bg-indigo-50 border border-indigo-200 text-indigo-900 font-semibold"
                      : "hover:bg-slate-50 text-slate-700"
                  }`}
                >
                  <div>
                    <div className="font-mono text-xs text-indigo-600">{a.code}</div>
                    <div>{a.name}</div>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">
                    {a.rack_count || 0} racks
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Step 3: Racks & Shelves */}
        <Card className="col-span-1">
          <CardHeader className="p-4 pb-2 border-b flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center">
              <FolderPlus className="mr-2 h-4 w-4 text-amber-600" /> Racks & Shelves
            </CardTitle>
            {selectedAisle && canManage && (
              <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => setOpenRackModal(true)}>
                <Plus className="h-3 w-3 mr-1" /> Rack
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-2 space-y-2">
            {!selectedAisle ? (
              <p className="text-xs text-slate-400 p-3">Select an aisle first</p>
            ) : racks.length === 0 ? (
              <p className="text-xs text-slate-500 p-3">No racks in this aisle.</p>
            ) : (
              racks.map((r: any) => (
                <div key={r.id} className="border rounded-lg p-2 bg-slate-50/50">
                  <div
                    onClick={() => {
                      setSelectedRack(r)
                      setSelectedShelf(null)
                    }}
                    className={`font-semibold text-sm cursor-pointer flex justify-between items-center ${
                      selectedRack?.id === r.id ? "text-amber-700" : "text-slate-800"
                    }`}
                  >
                    <span>Rack {r.code} - {r.name}</span>
                    {selectedRack?.id === r.id && canManage && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-6 px-1.5 text-[10px]"
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenShelfModal(true)
                        }}
                      >
                        + Shelf
                      </Button>
                    )}
                  </div>

                  {selectedRack?.id === r.id && (
                    <div className="mt-2 pl-2 space-y-1 border-l-2 border-amber-300">
                      {shelves.length === 0 ? (
                        <p className="text-[11px] text-slate-400">No shelves yet.</p>
                      ) : (
                        shelves.map((s: any) => (
                          <div
                            key={s.id}
                            onClick={() => setSelectedShelf(s)}
                            className={`text-xs p-1.5 rounded cursor-pointer flex justify-between ${
                              selectedShelf?.id === s.id
                                ? "bg-amber-100 text-amber-900 font-bold"
                                : "hover:bg-slate-100 text-slate-600"
                            }`}
                          >
                            <span>Shelf {s.code}</span>
                            <span className="text-[10px] text-slate-400">
                              {s.location_count || 0} locs
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Step 4: Storage Locations */}
        <Card className="col-span-1">
          <CardHeader className="p-4 pb-2 border-b flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold flex items-center">
              <MapPin className="mr-2 h-4 w-4 text-emerald-600" /> Storage Locations
            </CardTitle>
            {selectedShelf && canManage && (
              <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => setOpenLocationModal(true)}>
                <Plus className="h-3 w-3 mr-1" /> Add
              </Button>
            )}
          </CardHeader>
          <CardContent className="p-2 space-y-1">
            {!selectedShelf ? (
              <p className="text-xs text-slate-400 p-3">Select a shelf first</p>
            ) : locations.length === 0 ? (
              <p className="text-xs text-slate-500 p-3">No locations registered on this shelf.</p>
            ) : (
              locations.map((loc: StorageLocation) => (
                <div
                  key={loc.id}
                  className="p-2 rounded border bg-emerald-50/40 text-emerald-950 flex items-center justify-between"
                >
                  <div>
                    <div className="font-mono font-bold text-xs text-emerald-700">{loc.code}</div>
                    <div className="text-xs">{loc.name}</div>
                  </div>
                  <Badge variant="success" className="text-[9px]">
                    Active
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Modal: Add Warehouse */}
      <Dialog open={openWhModal} onOpenChange={setOpenWhModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Register New Warehouse</DialogTitle>
            <DialogDescription>Define a top-level warehouse facility.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Warehouse Code (e.g. WH-MAIN)</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="WH-MAIN" />
            </div>
            <div>
              <Label>Warehouse Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Main Distribution Hub" />
            </div>
            <div>
              <Label>Physical Address</Label>
              <Input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="123 Industrial Park Way" />
            </div>
            <div>
              <Label>Description</Label>
              <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Notes..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenWhModal(false)}>Cancel</Button>
            <Button
              disabled={!code || !name}
              onClick={() => createWhMutation.mutate({ code, name, address, description })}
            >
              Create Warehouse
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Add Aisle */}
      <Dialog open={openAisleModal} onOpenChange={setOpenAisleModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Aisle to {selectedWh?.code}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Aisle Code (e.g. A01)</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="A01" />
            </div>
            <div>
              <Label>Aisle Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="East Bay Aisle 1" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenAisleModal(false)}>Cancel</Button>
            <Button
              disabled={!code || !name}
              onClick={() => createAisleMutation.mutate({ code, name, description })}
            >
              Add Aisle
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Add Rack */}
      <Dialog open={openRackModal} onOpenChange={setOpenRackModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Rack to Aisle {selectedAisle?.code}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Rack Code (e.g. R01)</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="R01" />
            </div>
            <div>
              <Label>Rack Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Heavy Duty Rack 1" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenRackModal(false)}>Cancel</Button>
            <Button disabled={!code || !name} onClick={() => createRackMutation.mutate({ code, name, description })}>
              Add Rack
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Add Shelf */}
      <Dialog open={openShelfModal} onOpenChange={setOpenShelfModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Shelf to Rack {selectedRack?.code}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Shelf Code (e.g. S01, S02)</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="S01" />
            </div>
            <div>
              <Label>Shelf Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Tier 1 Bottom Shelf" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenShelfModal(false)}>Cancel</Button>
            <Button disabled={!code || !name} onClick={() => createShelfMutation.mutate({ code, name, description })}>
              Add Shelf
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Add Location */}
      <Dialog open={openLocationModal} onOpenChange={setOpenLocationModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Storage Location</DialogTitle>
            <DialogDescription>Define exact bin/location in Shelf {selectedShelf?.code}.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Location / Bin Code (e.g. BIN-01)</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="BIN-01" />
            </div>
            <div>
              <Label>Location Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Left Section Bin 1" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenLocationModal(false)}>Cancel</Button>
            <Button disabled={!code || !name} onClick={() => createLocationMutation.mutate({ code, name, description })}>
              Register Location
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

