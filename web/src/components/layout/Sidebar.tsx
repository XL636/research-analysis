import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { BookOpen, LayoutDashboard, FileSearch, Library, Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const navItems = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/analyze', labelKey: 'nav.analyze', icon: FileSearch },
  { to: '/knowledge', labelKey: 'nav.knowledge', icon: Library },
]

export default function Sidebar() {
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
    <aside className="fixed top-0 left-0 h-screen w-64 bg-surface-sidebar flex flex-col">
      {/* App title */}
      <div className="flex items-center gap-3 px-6 py-6">
        <BookOpen className="h-7 w-7 text-primary-300" />
        <span className="text-lg font-heading font-bold text-white">
          {t('app.title')}
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 mt-2 space-y-1">
        {navItems.map(({ to, labelKey, icon: Icon }) => (
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
            {t(labelKey)}
          </NavLink>
        ))}
      </nav>

      {/* Language switcher + Version */}
      <div className="px-3 pb-4 space-y-2">
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
      </div>
    </aside>
  )
}
