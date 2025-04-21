"use client"

import Link from "next/link"
import { ModeToggle } from "./mode-toggle"

export function Navbar() {
  return (
    <nav className="border-b">
      <div className="container flex h-16 items-center px-4">
        <Link href="/" className="font-bold">
          ParseAI
        </Link>
        <div className="ml-auto flex items-center space-x-4">
          <ModeToggle />
        </div>
      </div>
    </nav>
  )
} 