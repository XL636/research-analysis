import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { BookOpen, BookOpenCheck, LayoutDashboard, FileSearch, Library, PenLine, Globe, Settings, ChevronsLeft, ChevronsRight, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const STORAGE_KEY = 'sidebar-collapsed'

const navItems = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/analyze', labelKey: 'nav.analyze', icon: FileSearch },
  { to: '/knowledge', labelKey: 'nav.knowledge', icon: Library },
  { to: '/templates', labelKey: 'nav.templates', icon: FileText },
  { to: '/paper', labelKey: 'nav.paper', icon: PenLine },
  { to: '/reader', labelKey: 'nav.reader', icon: BookOpenCheck },
  { to: '/settings', labelKey: 'nav.settings', icon: Settings },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { t, i18n } = useTranslation()

  useEffect(() => {
    document.documentElement.lang = i18n.language
  }, [i18n.language])

  const toggleLanguage = () => {
    const next = i18n.language === 'zh-CN' ? 'en' : 'zh-CN'
    i18n.changeLanguage(next)
  }

  const targetLang = i18n.language === 'zh-CN' ? t('lang.en') : t('lang.zhCN')

  return (
    <aside
      className={`fixed top-0 left-0 h-screen bg-surface-sidebar flex flex-col transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* App title */}
      <div className={`flex items-center py-6 ${collapsed ? 'justify-center px-2' : 'gap-3 px-6'}`}>
        <BookOpen className="h-7 w-7 text-primary-300 shrink-0" />
        {!collapsed && (
          <span className="text-lg font-heading font-bold text-white whitespace-nowrap overflow-hidden">
            {t('app.title')}
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className={`flex-1 mt-2 space-y-1 ${collapsed ? 'px-1.5' : 'px-3'}`}>
        {navItems.map(({ to, labelKey, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            title={collapsed ? t(labelKey) : undefined}
            className={({ isActive }) =>
              `group relative flex items-center rounded-lg text-sm font-medium transition-all duration-200 ${
                collapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-4 py-2.5'
              } ${
                isActive
                  ? 'bg-white text-primary-900'
                  : 'text-primary-300 hover:bg-primary-900/50 hover:text-white'
              }`
            }
          >
            <Icon className="h-5 w-5 shrink-0" />
            {!collapsed && t(labelKey)}
            {/* Tooltip on hover when collapsed */}
            {collapsed && (
              <span className="absolute left-full ml-2 px-2 py-1 rounded bg-gray-900 text-white text-xs whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
                {t(labelKey)}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Language switcher + Version + Collapse toggle */}
      <div className={`pb-4 space-y-2 ${collapsed ? 'px-1.5' : 'px-3'}`}>
        {!collapsed ? (
          <>
            <button
              type="button"
              onClick={toggleLanguage}
              className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-primary-300 hover:bg-primary-900/50 hover:text-white transition-all duration-200"
            >
              <Globe className="h-4 w-4" />
              {targetLang}
            </button>
            <div className="px-3">
              <span className="text-xs text-primary-400">v0.2.0</span>
            </div>
          </>
        ) : (
          <button
            type="button"
            onClick={toggleLanguage}
            title={targetLang}
            className="group relative flex items-center justify-center w-full py-2 rounded-lg text-primary-300 hover:bg-primary-900/50 hover:text-white transition-all duration-200"
          >
            <Globe className="h-4 w-4" />
            <span className="absolute left-full ml-2 px-2 py-1 rounded bg-gray-900 text-white text-xs whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50">
              {targetLang}
            </span>
          </button>
        )}

        {/* Collapse / Expand toggle */}
        <button
          type="button"
          onClick={onToggle}
          className={`flex items-center w-full py-2 rounded-lg text-sm text-primary-300 hover:bg-primary-900/50 hover:text-white transition-all duration-200 ${
            collapsed ? 'justify-center' : 'gap-2 px-3'
          }`}
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!collapsed && <span className="text-xs">{t('nav.collapse', '收起')}</span>}
        </button>
      </div>
    </aside>
  )
}

export { STORAGE_KEY }
