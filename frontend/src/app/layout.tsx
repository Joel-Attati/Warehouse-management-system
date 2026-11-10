import type { Metadata } from "next"
import "./globals.css"
import { Providers } from "./providers"

export const metadata: Metadata = {
  title: "Warehouse Management System (WMS)",
  description: "On-premises local network Warehouse Management System",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full bg-slate-50">
      <body className="h-full antialiased text-slate-800 font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
