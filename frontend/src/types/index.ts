export type UserRole = "admin" | "manager" | "staff" | "viewer"

export interface User {
  id: number
  username: string
  email: string
  full_name?: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string
  role: UserRole
  is_active?: boolean
}

export interface UserUpdate {
  email?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

export interface Warehouse {
  id: number
  code: string
  name: string
  address?: string | null
  description?: string | null
  is_active: boolean
  created_at: string
  aisle_count?: number
}

export interface Aisle {
  id: number
  warehouse_id: number
  code: string
  name: string
  description?: string | null
  is_active: boolean
  rack_count?: number
}

export interface Rack {
  id: number
  aisle_id: number
  code: string
  name: string
  description?: string | null
  is_active: boolean
  shelf_count?: number
}

export interface Shelf {
  id: number
  rack_id: number
  code: string
  name: string
  description?: string | null
  is_active: boolean
  location_count?: number
}

export interface StorageLocation {
  id: number
  shelf_id: number
  code: string
  name: string
  description?: string | null
  is_active: boolean
  created_at: string
  full_path?: string
}

export interface LocationFullPath {
  id: number
  code: string
  name: string
  full_path: string
  warehouse_name: string
  aisle_name: string
  rack_name: string
  shelf_name: string
}

export interface Category {
  id: number
  name: string
  description?: string | null
  created_at: string
  product_count?: number
}

export type ProductStatus = "active" | "inactive"

export interface Product {
  id: number
  sku: string
  name: string
  category_id?: number | null
  category_name?: string | null
  unit: string
  barcode?: string | null
  qr_code?: string | null
  min_stock: number
  reorder_level: number
  has_expiry: boolean
  image_path?: string | null
  status: ProductStatus
  description?: string | null
  created_at: string
  updated_at: string
  total_stock?: number
}

export interface ProductListItem {
  id: number
  sku: string
  name: string
  category_id?: number | null
  category_name?: string | null
  unit: string
  barcode?: string | null
  min_stock: number
  reorder_level: number
  has_expiry: boolean
  status: ProductStatus
  image_path?: string | null
  total_stock: number
}

export interface Batch {
  id: number
  product_id: number
  product_sku?: string
  product_name?: string
  batch_number: string
  expiry_date?: string | null
  manufacture_date?: string | null
  notes?: string | null
  created_at: string
}

export interface InventoryStock {
  id: number
  product_id: number
  product_sku: string
  product_name: string
  category_name?: string | null
  location_id: number
  location_code: string
  location_path?: string | null
  batch_id?: number | null
  batch_number?: string | null
  expiry_date?: string | null
  quantity: number
  min_stock: number
  reorder_level: number
  stock_status: "ok" | "low" | "critical"
  last_updated: string
}

export interface StockSummary {
  product_id: number
  sku: string
  name: string
  category_name?: string | null
  unit: string
  total_quantity: number
  min_stock: number
  reorder_level: number
  stock_status: "ok" | "low" | "critical"
  location_count: number
}

export type MovementType = "RECEIVE" | "ISSUE" | "TRANSFER" | "ADJUSTMENT"

export interface MovementResponse {
  id: number
  movement_type: MovementType
  product_id: number
  product_sku: string
  product_name: string
  batch_id?: number | null
  batch_number?: string | null
  from_location_id?: number | null
  from_location_name?: string | null
  to_location_id?: number | null
  to_location_name?: string | null
  quantity: number
  reference_number?: string | null
  notes?: string | null
  performed_by: number
  performed_by_name: string
  created_at: string
}

export interface ReceiveRequest {
  product_id: number
  location_id: number
  quantity: number
  batch_number?: string
  expiry_date?: string
  manufacture_date?: string
  reference_number?: string
  notes?: string
}

export interface IssueRequest {
  product_id: number
  location_id: number
  quantity: number
  batch_id?: number
  reference_number?: string
  notes?: string
}

export interface TransferRequest {
  product_id: number
  from_location_id: number
  to_location_id: number
  quantity: number
  batch_id?: number
  reference_number?: string
  notes?: string
}

export interface LowStockAlert {
  product_id: number
  sku: string
  name: string
  category_name?: string | null
  unit: string
  current_stock: number
  min_stock: number
  reorder_level: number
  status: "low" | "critical"
}

export interface ExpiryAlert {
  batch_id: number
  product_id: number
  sku: string
  name: string
  batch_number: string
  expiry_date: string
  days_until_expiry: number
  quantity: number
  location_name?: string
}

export interface MovementChartPoint {
  date: string
  receives: number
  issues: number
  transfers: number
}

export interface DashboardStats {
  total_products: number
  total_locations: number
  total_movements_today: number
  low_stock_count: number
  expiring_soon_count: number
  recent_movements: MovementResponse[]
  top_low_stock: LowStockAlert[]
  movement_trends: MovementChartPoint[]
}

export interface AuditLog {
  id: number
  user_id?: number | null
  username: string
  action: string
  entity: string
  entity_id?: string | null
  detail?: any
  ip_address?: string | null
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
