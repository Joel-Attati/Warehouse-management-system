import axios from "axios"
import toast from "react-hot-toast"
import {
  AuditLog,
  Batch,
  Category,
  DashboardStats,
  ExpiryAlert,
  InventoryStock,
  IssueRequest,
  LocationFullPath,
  LowStockAlert,
  MovementResponse,
  PaginatedResponse,
  Product,
  ProductListItem,
  ReceiveRequest,
  StockSummary,
  StorageLocation,
  TransferRequest,
  User,
  UserCreate,
  UserUpdate,
  Warehouse,
} from "@/types"

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
})

// Global response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const url = error.config?.url || ""
    const message = error.response?.data?.detail || "An unexpected error occurred"

    if (status === 401) {
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/login"
      }
    } else if (status >= 400 && status < 500) {
      // Don't show toast for silent session check on /auth/me
      if (!url.includes("/auth/me")) {
        const errorText = Array.isArray(message)
          ? message.map((m: any) => m.msg || JSON.stringify(m)).join(", ")
          : typeof message === "string"
          ? message
          : JSON.stringify(message)
        toast.error(errorText)
      }
    } else if (status >= 500) {
      toast.error("Internal server error. Please try again later.")
    }
    return Promise.reject(error)
  }
)

// ── Auth API ──
export const authApi = {
  login: async (username: string, password: string) => {
    const res = await apiClient.post<{ access_token: string; role: string; username: string }>(
      "/auth/login",
      { username, password }
    )
    return res.data
  },
  logout: async () => {
    const res = await apiClient.post("/auth/logout")
    return res.data
  },
  me: async () => {
    const res = await apiClient.get<User>("/auth/me")
    return res.data
  },
  changePassword: async (old_password: string, new_password: string) => {
    const res = await apiClient.post("/auth/me/change-password", { old_password, new_password })
    return res.data
  },
}

// ── Users API (Admin) ──
export const usersApi = {
  list: async (params?: { page?: number; page_size?: number; role?: string; search?: string }) => {
    const res = await apiClient.get<PaginatedResponse<User>>("/users", { params })
    return res.data
  },
  create: async (data: UserCreate) => {
    const res = await apiClient.post<User>("/users", data)
    return res.data
  },
  get: async (id: number) => {
    const res = await apiClient.get<User>(`/users/${id}`)
    return res.data
  },
  update: async (id: number, data: UserUpdate) => {
    const res = await apiClient.put<User>(`/users/${id}`, data)
    return res.data
  },
  delete: async (id: number) => {
    const res = await apiClient.delete(`/users/${id}`)
    return res.data
  },
  resetPassword: async (id: number, new_password: string) => {
    const res = await apiClient.post(`/users/${id}/reset-password`, { new_password })
    return res.data
  },
}

// ── Warehouses API ──
export const warehousesApi = {
  list: async () => {
    const res = await apiClient.get<Warehouse[]>("/warehouses")
    return res.data
  },
  create: async (data: { code: string; name: string; address?: string; description?: string }) => {
    const res = await apiClient.post<Warehouse>("/warehouses", data)
    return res.data
  },
  getAisles: async (warehouseId: number) => {
    const res = await apiClient.get<any[]>(`/warehouses/${warehouseId}/aisles`)
    return res.data
  },
  createAisle: async (warehouseId: number, data: { code: string; name: string; description?: string }) => {
    const res = await apiClient.post(`/warehouses/${warehouseId}/aisles`, data)
    return res.data
  },
  getRacks: async (aisleId: number) => {
    const res = await apiClient.get<any[]>(`/warehouses/aisles/${aisleId}/racks`)
    return res.data
  },
  createRack: async (aisleId: number, data: { code: string; name: string; description?: string }) => {
    const res = await apiClient.post(`/warehouses/aisles/${aisleId}/racks`, data)
    return res.data
  },
  getShelves: async (rackId: number) => {
    const res = await apiClient.get<any[]>(`/warehouses/racks/${rackId}/shelves`)
    return res.data
  },
  createShelf: async (rackId: number, data: { code: string; name: string; description?: string }) => {
    const res = await apiClient.post(`/warehouses/racks/${rackId}/shelves`, data)
    return res.data
  },
  getLocations: async (shelfId: number) => {
    const res = await apiClient.get<StorageLocation[]>(`/warehouses/shelves/${shelfId}/locations`)
    return res.data
  },
  createLocation: async (shelfId: number, data: { code: string; name: string; description?: string }) => {
    const res = await apiClient.post<StorageLocation>(`/warehouses/shelves/${shelfId}/locations`, data)
    return res.data
  },
  searchLocations: async (query: string) => {
    const res = await apiClient.get<LocationFullPath[]>("/warehouses/locations/search", { params: { query } })
    return res.data
  },
  getLocation: async (id: number) => {
    const res = await apiClient.get<LocationFullPath>(`/warehouses/locations/${id}`)
    return res.data
  },
}

// ── Products API ──
export const productsApi = {
  listCategories: async () => {
    const res = await apiClient.get<Category[]>("/products/categories")
    return res.data
  },
  createCategory: async (data: { name: string; description?: string }) => {
    const res = await apiClient.post<Category>("/products/categories", data)
    return res.data
  },
  list: async (params?: {
    page?: number
    page_size?: number
    search?: string
    category_id?: number
    status?: string
    low_stock_only?: boolean
  }) => {
    const res = await apiClient.get<PaginatedResponse<ProductListItem>>("/products", { params })
    return res.data
  },
  create: async (data: any) => {
    const res = await apiClient.post<Product>("/products", data)
    return res.data
  },
  get: async (id: number) => {
    const res = await apiClient.get<Product>(`/products/${id}`)
    return res.data
  },
  update: async (id: number, data: any) => {
    const res = await apiClient.put<Product>(`/products/${id}`, data)
    return res.data
  },
  delete: async (id: number) => {
    const res = await apiClient.delete(`/products/${id}`)
    return res.data
  },
  uploadImage: async (id: number, file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    const res = await apiClient.post<Product>(`/products/${id}/image`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    return res.data
  },
  deleteImage: async (id: number) => {
    const res = await apiClient.delete(`/products/${id}/image`)
    return res.data
  },
  lookupBarcode: async (barcode: string) => {
    const res = await apiClient.get<Product>(`/products/barcode/${encodeURIComponent(barcode)}`)
    return res.data
  },
  lookupSku: async (sku: string) => {
    const res = await apiClient.get<Product>(`/products/sku/${encodeURIComponent(sku)}`)
    return res.data
  },
}

// ── Inventory API ──
export const inventoryApi = {
  listStock: async (params?: {
    page?: number
    page_size?: number
    product_id?: number
    location_id?: number
    warehouse_id?: number
    search?: string
    low_stock_only?: boolean
  }) => {
    const res = await apiClient.get<PaginatedResponse<InventoryStock>>("/inventory/stock", { params })
    return res.data
  },
  stockSummary: async (params?: { category_id?: number; search?: string }) => {
    const res = await apiClient.get<StockSummary[]>("/inventory/stock/summary", { params })
    return res.data
  },
  listBatches: async (params?: { product_id?: number }) => {
    const res = await apiClient.get<Batch[]>("/inventory/batches", { params })
    return res.data
  },
  createBatch: async (data: any) => {
    const res = await apiClient.post<Batch>("/inventory/batches", data)
    return res.data
  },
}

// ── Movements API ──
export const movementsApi = {
  receive: async (data: ReceiveRequest) => {
    const res = await apiClient.post<MovementResponse>("/movements/receive", data)
    return res.data
  },
  issue: async (data: IssueRequest) => {
    const res = await apiClient.post<MovementResponse>("/movements/issue", data)
    return res.data
  },
  transfer: async (data: TransferRequest) => {
    const res = await apiClient.post<MovementResponse>("/movements/transfer", data)
    return res.data
  },
  list: async (params?: {
    page?: number
    page_size?: number
    product_id?: number
    movement_type?: string
    performed_by?: number
    date_from?: string
    date_to?: string
    search?: string
  }) => {
    const res = await apiClient.get<PaginatedResponse<MovementResponse>>("/movements", { params })
    return res.data
  },
}

// ── Alerts API ──
export const alertsApi = {
  lowStock: async () => {
    const res = await apiClient.get<LowStockAlert[]>("/alerts/low-stock")
    return res.data
  },
  expiring: async (days: number = 30) => {
    const res = await apiClient.get<ExpiryAlert[]>("/alerts/expiring", { params: { days } })
    return res.data
  },
}

// ── Dashboard API ──
export const dashboardApi = {
  getStats: async () => {
    const res = await apiClient.get<DashboardStats>("/dashboard")
    return res.data
  },
}

// ── Reports API ──
export const reportsApi = {
  inventory: async (params?: { warehouse_id?: number; category_id?: number }) => {
    const res = await apiClient.get<InventoryStock[]>("/reports/inventory", { params })
    return res.data
  },
  exportInventoryCsvUrl: (warehouse_id?: number, category_id?: number) => {
    const base = process.env.NEXT_PUBLIC_API_URL || "/api"
    const q = new URLSearchParams({ format: "csv" })
    if (warehouse_id) q.append("warehouse_id", warehouse_id.toString())
    if (category_id) q.append("category_id", category_id.toString())
    return `${base}/reports/inventory?${q.toString()}`
  },
  movements: async (params?: { movement_type?: string; date_from?: string; date_to?: string }) => {
    const res = await apiClient.get<MovementResponse[]>("/reports/movements", { params })
    return res.data
  },
  exportMovementsCsvUrl: (movement_type?: string, date_from?: string, date_to?: string) => {
    const base = process.env.NEXT_PUBLIC_API_URL || "/api"
    const q = new URLSearchParams({ format: "csv" })
    if (movement_type) q.append("movement_type", movement_type)
    if (date_from) q.append("date_from", date_from)
    if (date_to) q.append("date_to", date_to)
    return `${base}/reports/movements?${q.toString()}`
  },
}

// ── Audit API ──
export const auditApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    username?: string
    action?: string
    entity?: string
    date_from?: string
    date_to?: string
  }) => {
    const res = await apiClient.get<PaginatedResponse<AuditLog>>("/audit", { params })
    return res.data
  },
}

