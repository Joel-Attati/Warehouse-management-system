"use client"

import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { ChevronDown, ChevronRight, FileCode, History, Search, ShieldCheck } from "lucide-react"

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
import { auditApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { AuditLog } from "@/types"

export default function AuditLogsPage() {
  const [page, setPage] = useState(1)
  const [searchUser, setSearchUser] = useState("")
  const [actionFilter, setActionFilter] = useState("")
  const [expandedRows, setExpandedRows] = useState<Record<number, boolean>>({})

  const { data: auditData, isLoading } = useQuery({
    queryKey: ["audit-logs", page, searchUser, actionFilter],
    queryFn: () =>
      auditApi.list({
        page,
        page_size: 25,
        username: searchUser || undefined,
        action: actionFilter || undefined,
      }),
  })

  const toggleExpand = (id: number) => {
    setExpandedRows((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System Audit Trail</h1>
          <p className="text-sm text-slate-500">
            Immutable append-only record of all security, inventory transactions, and administrative changes.
          </p>
        </div>
        <Badge variant="outline" className="flex items-center space-x-1.5 border-blue-300 bg-blue-50 text-blue-800">
          <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
          <span>Tamper-Resistant Journal</span>
        </Badge>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center gap-4">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Filter by username..."
              className="pl-9"
              value={searchUser}
              onChange={(e) => {
                setSearchUser(e.target.value)
                setPage(1)
              }}
            />
          </div>

          <div className="w-full sm:w-64">
            <select
              className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value)
                setPage(1)
              }}
            >
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="RECEIVE_STOCK">RECEIVE_STOCK</option>
              <option value="ISSUE_STOCK">ISSUE_STOCK</option>
              <option value="TRANSFER_STOCK">TRANSFER_STOCK</option>
              <option value="CREATE_PRODUCT">CREATE_PRODUCT</option>
              <option value="UPDATE_PRODUCT">UPDATE_PRODUCT</option>
              <option value="CREATE_USER">CREATE_USER</option>
              <option value="CREATE_WAREHOUSE">CREATE_WAREHOUSE</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Audit Log Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingPage message="Loading audit journal..." />
          ) : !auditData || auditData.items.length === 0 ? (
            <div className="p-12 text-center text-slate-500">
              <History className="h-10 w-10 mx-auto text-slate-300 mb-2" />
              <p className="font-semibold text-slate-700">No audit events recorded</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-8"></TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Entity</TableHead>
                    <TableHead>Entity ID</TableHead>
                    <TableHead>IP Address</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {auditData.items.map((log: AuditLog) => {
                    const isExpanded = !!expandedRows[log.id]
                    return (
                      <React.Fragment key={log.id}>
                        <TableRow
                          className="cursor-pointer hover:bg-slate-50"
                          onClick={() => toggleExpand(log.id)}
                        >
                          <TableCell className="p-2">
                            {log.detail ? (
                              isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-slate-400" />
                              ) : (
                                <ChevronRight className="h-4 w-4 text-slate-400" />
                              )
                            ) : null}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-500 whitespace-nowrap">
                            {formatDate(log.created_at)}
                          </TableCell>
                          <TableCell className="font-semibold text-slate-900">{log.username}</TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                log.action.includes("LOGIN")
                                  ? "default"
                                  : log.action.includes("RECEIVE")
                                  ? "success"
                                  : log.action.includes("ISSUE")
                                  ? "destructive"
                                  : "secondary"
                              }
                              className="text-[10px] font-mono"
                            >
                              {log.action}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-xs text-slate-600">{log.entity}</TableCell>
                          <TableCell className="font-mono text-xs text-slate-500">
                            {log.entity_id || "-"}
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-400">
                            {log.ip_address || "local"}
                          </TableCell>
                        </TableRow>
                        {isExpanded && log.detail && (
                          <TableRow className="bg-slate-50/70 border-b">
                            <TableCell colSpan={7} className="p-4">
                              <div className="rounded-md bg-slate-900 p-3 text-emerald-400 font-mono text-xs overflow-x-auto shadow-inner">
                                <pre>{JSON.stringify(log.detail, null, 2)}</pre>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </React.Fragment>
                    )
                  })}
                </TableBody>
              </Table>

              {auditData.total_pages > 1 && (
                <div className="p-4 border-t flex items-center justify-between text-sm text-slate-600">
                  <div>
                    Page {auditData.page} of {auditData.total_pages} ({auditData.total} events recorded)
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
                      disabled={page >= auditData.total_pages}
                      onClick={() => setPage((p) => p + 1)}
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
    </div>
  )
}

