import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 overflow-y-auto bg-surface p-8 min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}
