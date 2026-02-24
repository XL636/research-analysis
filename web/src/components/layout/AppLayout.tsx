import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar, { STORAGE_KEY } from './Sidebar'

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  })

  const handleToggle = () => {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem(STORAGE_KEY, String(next))
      return next
    })
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar collapsed={collapsed} onToggle={handleToggle} />
      <main
        className={`flex-1 overflow-y-auto bg-surface p-8 min-h-screen transition-all duration-300 ${
          collapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        <Outlet />
      </main>
    </div>
  )
}
