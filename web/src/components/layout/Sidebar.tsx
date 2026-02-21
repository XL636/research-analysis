import { NavLink } from 'react-router-dom'
import { BookOpen, LayoutDashboard, FileSearch, Library } from 'lucide-react'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'Analyze', icon: FileSearch },
  { to: '/knowledge', label: 'Knowledge Base', icon: Library },
]

export default function Sidebar() {
  return (
    <aside className="fixed top-0 left-0 h-screen w-64 bg-surface-sidebar flex flex-col">
      {/* App title */}
      <div className="flex items-center gap-3 px-6 py-6">
        <BookOpen className="h-7 w-7 text-primary-300" />
        <span className="text-lg font-heading font-bold text-white">
          Research Analysis
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 mt-2 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-white text-primary-900'
                  : 'text-primary-300 hover:bg-primary-900/50 hover:text-white'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Version */}
      <div className="px-6 py-4">
        <span className="text-xs text-primary-400">v0.2.0</span>
      </div>
    </aside>
  )
}
