"use client"

import React, { useState } from "react"
import Image from "next/image"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Barcode,
  Camera,
  FolderPlus,
  Image as ImageIcon,
  Package,
  Plus,
  Search,
  Trash2,
} from "lucide-react"
import toast from "react-hot-toast"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { productsApi } from "@/lib/api"
import { useAuthStore } from "@/stores/auth"
import { Category, Product, ProductListItem } from "@/types"

export default function ProductsPage() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const canManage = user?.role === "admin" || user?.role === "manager"

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [categoryId, setCategoryId] = useState<number | undefined>()

  // Modals
  const [openCreateModal, setOpenCreateModal] = useState(false)
  const [openCategoryModal, setOpenCategoryModal] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [openDetailModal, setOpenDetailModal] = useState(false)

  // Product Form state
  const [sku, setSku] = useState("")
  const [name, setName] = useState("")
  const [prodCatId, setProdCatId] = useState<number | undefined>()
  const [unit, setUnit] = useState("pcs")
  const [barcode, setBarcode] = useState("")
  const [qrCode, setQrCode] = useState("")
  const [minStock, setMinStock] = useState(10)
  const [reorderLevel, setReorderLevel] = useState(25)
  const [hasExpiry, setHasExpiry] = useState(false)
  const [description, setDescription] = useState("")

  // Category form state
  const [catName, setCatName] = useState("")
  const [catDesc, setCatDesc] = useState("")

  // Queries
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: productsApi.listCategories,
  })

  const { data: productData, isLoading } = useQuery({
    queryKey: ["products", page, search, categoryId],
    queryFn: () =>
      productsApi.list({
        page,
        page_size: 15,
        search: search || undefined,
        category_id: categoryId,
      }),
  })

  // Mutations
  const createProductMutation = useMutation({
    mutationFn: productsApi.create,
    onSuccess: (newProd) => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      toast.success(`Product ${newProd.sku} created`)
      setOpenCreateModal(false)
      resetProductForm()
    },
  })

  const createCatMutation = useMutation({
    mutationFn: productsApi.createCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
      toast.success("Category created")
      setOpenCategoryModal(false)
      setCatName("")
      setCatDesc("")
    },
  })

  const uploadImageMutation = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) =>
      productsApi.uploadImage(id, file),
    onSuccess: (updatedProd) => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      setSelectedProduct(updatedProd)
      toast.success("Product image uploaded")
    },
  })

  const deleteImageMutation = useMutation({
    mutationFn: (id: number) => productsApi.deleteImage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["products"] })
      if (selectedProduct) {
        setSelectedProduct({ ...selectedProduct, image_path: null })
      }
      toast.success("Image removed")
    },
  })

  const resetProductForm = () => {
    setSku("")
    setName("")
    setProdCatId(undefined)
    setUnit("pcs")
    setBarcode("")
    setQrCode("")
    setMinStock(10)
    setReorderLevel(25)
    setHasExpiry(false)
    setDescription("")
  }

  const handleOpenDetail = async (prodId: number) => {
    try {
      const p = await productsApi.get(prodId)
      setSelectedProduct(p)
      setOpenDetailModal(true)
    } catch {
      toast.error("Failed to load product details")
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0] && selectedProduct) {
      uploadImageMutation.mutate({ id: selectedProduct.id, file: e.target.files[0] })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Product Registration</h1>
          <p className="text-sm text-slate-500">
            Manage SKU registration, barcode mapping, reorder thresholds, and images.
          </p>
        </div>
        {canManage && (
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOpenCategoryModal(true)}
            >
              <FolderPlus className="mr-2 h-4 w-4" />
              Categories
            </Button>
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => setOpenCreateModal(true)}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Product
            </Button>
          </div>
        )}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by SKU, product name, or barcode..."
              className="pl-9"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
            />
          </div>
          <div className="w-full sm:w-64">
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              value={categoryId || ""}
              onChange={(e) => {
                setCategoryId(e.target.value ? Number(e.target.value) : undefined)
                setPage(1)
              }}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingPage message="Loading products list..." />
          ) : !productData || productData.items.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <Package className="h-10 w-10 mx-auto text-slate-300 mb-2" />
              <p className="font-semibold text-slate-700">No products found</p>
              <p className="text-sm">Register your first item with SKU and barcode.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Image</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Product Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Barcode</TableHead>
                  <TableHead className="text-right">Total Stock</TableHead>
                  <TableHead className="text-right">Reorder</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {productData.items.map((prod: ProductListItem) => (
                  <TableRow key={prod.id}>
                    <TableCell>
                      {prod.image_path ? (
                        <div className="relative h-10 w-10 rounded-md overflow-hidden border bg-slate-100">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={`/uploads/${prod.image_path}`}
                            alt={prod.name}
                            className="h-full w-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="h-10 w-10 rounded-md bg-slate-100 border flex items-center justify-center text-slate-400">
                          <ImageIcon className="h-4 w-4" />
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs font-bold text-blue-700">
                      {prod.sku}
                    </TableCell>
                    <TableCell className="font-medium text-slate-900">{prod.name}</TableCell>
                    <TableCell className="text-slate-600 text-xs">
                      {prod.category_name || "Uncategorized"}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-slate-600">
                      {prod.barcode || "-"}
                    </TableCell>
                    <TableCell className="text-right font-bold text-slate-900">
                      {prod.total_stock} {prod.unit}
                    </TableCell>
                    <TableCell className="text-right text-xs text-slate-500">
                      {prod.reorder_level} {prod.unit}
                    </TableCell>
                    <TableCell>
                      <Badge variant={prod.status === "active" ? "success" : "secondary"}>
                        {prod.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs text-blue-600"
                        onClick={() => handleOpenDetail(prod.id)}
                      >
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {/* Pagination */}
          {productData && productData.total_pages > 1 && (
            <div className="p-4 border-t flex items-center justify-between text-sm text-slate-600">
              <div>
                Showing page {productData.page} of {productData.total_pages} ({productData.total} items)
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
                  disabled={page >= productData.total_pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal: Create Product */}
      <Dialog open={openCreateModal} onOpenChange={setOpenCreateModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Register New Product</DialogTitle>
            <DialogDescription>Add item to warehouse catalog with barcode tracking.</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-2">
            <div>
              <Label>SKU Code *</Label>
              <Input
                value={sku}
                onChange={(e) => setSku(e.target.value.toUpperCase())}
                placeholder="e.g. ELEC-001"
              />
            </div>
            <div>
              <Label>Product Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Wireless Barcode Scanner"
              />
            </div>
            <div>
              <Label>Category</Label>
              <select
                className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                value={prodCatId || ""}
                onChange={(e) => setProdCatId(e.target.value ? Number(e.target.value) : undefined)}
              >
                <option value="">Select category...</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Unit of Measure</Label>
              <Input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="pcs, kg, box" />
            </div>
            <div>
              <Label>Barcode (EAN-13, UPC, Code128)</Label>
              <Input
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                placeholder="Scan or type barcode"
              />
            </div>
            <div>
              <Label>QR Code identifier</Label>
              <Input value={qrCode} onChange={(e) => setQrCode(e.target.value)} placeholder="QR Code data" />
            </div>
            <div>
              <Label>Minimum Stock Threshold</Label>
              <Input
                type="number"
                value={minStock}
                onChange={(e) => setMinStock(Number(e.target.value))}
              />
            </div>
            <div>
              <Label>Reorder Level Alert Threshold</Label>
              <Input
                type="number"
                value={reorderLevel}
                onChange={(e) => setReorderLevel(Number(e.target.value))}
              />
            </div>
            <div className="col-span-2 flex items-center space-x-2 pt-1">
              <input
                type="checkbox"
                id="hasExpiry"
                checked={hasExpiry}
                onChange={(e) => setHasExpiry(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <Label htmlFor="hasExpiry">Track expiration dates for this product</Label>
            </div>
            <div className="col-span-2">
              <Label>Description / Specifications</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Product notes or handling requirements..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenCreateModal(false)}>
              Cancel
            </Button>
            <Button
              disabled={!sku || !name}
              onClick={() =>
                createProductMutation.mutate({
                  sku,
                  name,
                  category_id: prodCatId,
                  unit,
                  barcode: barcode || undefined,
                  qr_code: qrCode || undefined,
                  min_stock: minStock,
                  reorder_level: reorderLevel,
                  has_expiry: hasExpiry,
                  description,
                })
              }
            >
              Save Product
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Category Management */}
      <Dialog open={openCategoryModal} onOpenChange={setOpenCategoryModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Product Categories</DialogTitle>
            <DialogDescription>Group products into manageable operational categories.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2 border-b pb-4">
              <Label>New Category Name</Label>
              <div className="flex space-x-2">
                <Input
                  value={catName}
                  onChange={(e) => setCatName(e.target.value)}
                  placeholder="e.g. Raw Materials, Electronics"
                />
                <Button
                  disabled={!catName}
                  onClick={() => createCatMutation.mutate({ name: catName, description: catDesc })}
                >
                  Add
                </Button>
              </div>
            </div>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {categories.map((c) => (
                <div key={c.id} className="flex justify-between items-center text-sm p-2 rounded bg-slate-50">
                  <span className="font-medium text-slate-800">{c.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {c.product_count || 0} products
                  </Badge>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenCategoryModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Product Detail & Image Upload Drawer */}
      <Dialog open={openDetailModal} onOpenChange={setOpenDetailModal}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Product Information</DialogTitle>
            <DialogDescription>Detailed SKU record, barcode & image preview</DialogDescription>
          </DialogHeader>
          {selectedProduct && (
            <div className="space-y-6 py-2">
              <div className="flex items-start space-x-6">
                <div className="space-y-2">
                  <div className="h-32 w-32 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden relative">
                    {selectedProduct.image_path ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img
                        src={`/uploads/${selectedProduct.image_path}`}
                        alt={selectedProduct.name}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <ImageIcon className="h-10 w-10 text-slate-300" />
                    )}
                  </div>
                  {canManage && (
                    <div className="flex space-x-1">
                      <label className="cursor-pointer">
                        <Button size="sm" variant="outline" className="h-7 text-xs" asChild>
                          <span>
                            <Camera className="h-3 w-3 mr-1" />
                            Upload
                          </span>
                        </Button>
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="hidden"
                          onChange={handleFileChange}
                        />
                      </label>
                      {selectedProduct.image_path && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 text-xs text-red-600 hover:bg-red-50"
                          onClick={() => deleteImageMutation.mutate(selectedProduct.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex-1 space-y-2 text-sm">
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-semibold">SKU</span>
                    <p className="font-mono text-base font-bold text-blue-600">{selectedProduct.sku}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 uppercase font-semibold">Product Name</span>
                    <p className="font-semibold text-slate-900">{selectedProduct.name}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-2">
                    <div>
                      <span className="text-xs text-slate-400">Barcode</span>
                      <p className="font-mono text-xs">{selectedProduct.barcode || "None"}</p>
                    </div>
                    <div>
                      <span className="text-xs text-slate-400">Total Available</span>
                      <p className="font-bold text-emerald-600">
                        {selectedProduct.total_stock || 0} {selectedProduct.unit}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Barcode representation */}
              {selectedProduct.barcode && (
                <div className="border rounded-lg p-3 bg-slate-50 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Barcode className="h-6 w-6 text-slate-700" />
                    <span className="font-mono text-sm tracking-wider font-bold">
                      {selectedProduct.barcode}
                    </span>
                  </div>
                  <Badge variant="outline">Compatible with USB / Bluetooth Scanners</Badge>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenDetailModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

