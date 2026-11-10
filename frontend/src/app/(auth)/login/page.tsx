"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Lock, Server, Shield, User } from "lucide-react"
import toast from "react-hot-toast"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { authApi } from "@/lib/api"
import { useAuthStore } from "@/stores/auth"

export default function LoginPage() {
  const router = useRouter()
  const { fetchUser } = useAuthStore()

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      toast.error("Please enter both username and password")
      return
    }

    try {
      setLoading(true)
      await authApi.login(username.trim(), password)
      toast.success("Signed in successfully")
      await fetchUser()
      router.push("/dashboard")
    } catch (err: any) {
      const msg = err.response?.data?.detail
      if (msg) {
        const errorText = Array.isArray(msg)
          ? msg.map((m: any) => m.msg || JSON.stringify(m)).join(", ")
          : typeof msg === "string"
          ? msg
          : JSON.stringify(msg)
        toast.error(errorText)
      } else {
        toast.error("Unable to connect to server. Please check backend connection.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 shadow-lg text-white">
            <Server className="h-8 w-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Warehouse Management System
          </h1>
          <p className="text-sm text-slate-500">
            Local / On-Premises Infrastructure Deployment
          </p>
        </div>

        <Card className="border-slate-200 shadow-md">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">Sign in to your account</CardTitle>
            <CardDescription>
              Enter your credentials to access inventory and operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="e.g. admin or staff"
                    className="pl-9"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    autoFocus
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-9"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>

              <Button type="submit" className="w-full mt-2" disabled={loading}>
                {loading ? "Authenticating..." : "Sign in"}
              </Button>
            </form>

            <div className="mt-6 border-t pt-4">
              <div className="flex items-center justify-center space-x-1.5 text-xs text-slate-500">
                <Shield className="h-3.5 w-3.5 text-emerald-600" />
                <span>Isolated LAN Environment · Role-Based Security</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

