"use client"

import React, { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { KeyRound, Plus, Shield, UserCheck, UserPlus, UserX } from "lucide-react"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { usersApi } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { useAuthStore } from "@/stores/auth"
import { User, UserRole } from "@/types"

export default function UsersPage() {
  const queryClient = useQueryClient()
  const { user: currentUser } = useAuthStore()

  const [page, setPage] = useState(1)

  // Dialog states
  const [openCreateModal, setOpenCreateModal] = useState(false)
  const [openResetModal, setOpenResetModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)

  // Form states
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [fullName, setFullName] = useState("")
  const [password, setPassword] = useState("")
  const [role, setRole] = useState<UserRole>("staff")
  const [newPassword, setNewPassword] = useState("")

  const { data: userData, isLoading } = useQuery({
    queryKey: ["users", page],
    queryFn: () => usersApi.list({ page, page_size: 20 }),
  })

  const createUserMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: (u) => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success(`User ${u.username} created`)
      setOpenCreateModal(false)
      resetForm()
    },
  })

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, pass }: { id: number; pass: string }) =>
      usersApi.resetPassword(id, pass),
    onSuccess: () => {
      toast.success("User password has been reset")
      setOpenResetModal(false)
      setNewPassword("")
    },
  })

  const toggleUserActiveMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      usersApi.update(id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      toast.success("User status updated")
    },
  })

  const resetForm = () => {
    setUsername("")
    setEmail("")
    setFullName("")
    setPassword("")
    setRole("staff")
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">User & Access Management</h1>
          <p className="text-sm text-slate-500">
            Control local account provisioning, administrative privileges, and role permissions.
          </p>
        </div>

        <Button
          onClick={() => setOpenCreateModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white"
        >
          <UserPlus className="mr-2 h-4 w-4" />
          Create New User
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingPage message="Loading system users..." />
          ) : !userData || userData.items.length === 0 ? (
            <div className="p-12 text-center text-slate-500">No users found.</div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Full Name</TableHead>
                    <TableHead>Email Address</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {userData.items.map((u: User) => (
                    <TableRow key={u.id}>
                      <TableCell className="font-mono text-xs font-bold text-slate-900">
                        {u.username}
                      </TableCell>
                      <TableCell className="font-medium text-slate-800">
                        {u.full_name || "-"}
                      </TableCell>
                      <TableCell className="text-xs text-slate-500">{u.email}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            u.role === "admin"
                              ? "destructive"
                              : u.role === "manager"
                              ? "default"
                              : u.role === "staff"
                              ? "success"
                              : "secondary"
                          }
                          className="uppercase text-[10px]"
                        >
                          {u.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={u.is_active ? "success" : "secondary"}>
                          {u.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-slate-400">{formatDate(u.created_at)}</TableCell>
                      <TableCell className="text-right space-x-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 text-xs text-slate-600"
                          onClick={() => {
                            setSelectedUser(u)
                            setOpenResetModal(true)
                          }}
                        >
                          <KeyRound className="h-3.5 w-3.5 mr-1" /> Reset Pass
                        </Button>
                        {u.id !== currentUser?.id && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className={`h-8 text-xs ${u.is_active ? "text-red-600 hover:bg-red-50" : "text-emerald-600 hover:bg-emerald-50"}`}
                            onClick={() =>
                              toggleUserActiveMutation.mutate({ id: u.id, is_active: !u.is_active })
                            }
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {userData.total_pages > 1 && (
                <div className="p-4 border-t flex items-center justify-between text-sm text-slate-600">
                  <div>
                    Page {userData.page} of {userData.total_pages}
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
                      disabled={page >= userData.total_pages}
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

      {/* Modal: Create User */}
      <Dialog open={openCreateModal} onOpenChange={setOpenCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Provision New User</DialogTitle>
            <DialogDescription>
              Create an on-premises authenticated account and assign access role.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>Username *</Label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                placeholder="e.g. jsmith"
              />
            </div>
            <div>
              <Label>Email Address *</Label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jsmith@warehouse.local"
              />
            </div>
            <div>
              <Label>Full Name</Label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Smith"
              />
            </div>
            <div>
              <Label>Initial Password *</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <div>
              <Label>System Role *</Label>
              <select
                className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus:outline-none"
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
              >
                <option value="staff">Staff (Receive, Issue, Transfer, View)</option>
                <option value="manager">Manager (Warehouse Setup, Reports, Alerts)</option>
                <option value="admin">Administrator (Full Control & User Management)</option>
                <option value="viewer">Viewer (Read-Only)</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenCreateModal(false)}>
              Cancel
            </Button>
            <Button
              disabled={!username || !email || !password}
              onClick={() =>
                createUserMutation.mutate({
                  username,
                  email,
                  full_name: fullName || undefined,
                  password,
                  role,
                })
              }
            >
              Create Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal: Reset Password */}
      <Dialog open={openResetModal} onOpenChange={setOpenResetModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password for {selectedUser?.username}</DialogTitle>
            <DialogDescription>Assign a new password to this account.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <Label>New Password</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenResetModal(false)}>
              Cancel
            </Button>
            <Button
              disabled={newPassword.length < 6}
              onClick={() => {
                if (selectedUser) {
                  resetPasswordMutation.mutate({ id: selectedUser.id, pass: newPassword })
                }
              }}
            >
              Update Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

