import { LayoutDashboard, UploadCloud, FileText, Settings, Database } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import { motion } from 'framer-motion'

const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: UploadCloud, label: 'Upload Bill', path: '/upload' },
    { icon: FileText, label: 'Auditor', path: '/bills' }, // Placeholder path for list
    { icon: Database, label: 'Master Prices', path: '/master-prices' },
    { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar() {
    const location = useLocation()

    return (
        <aside className="w-64 h-screen border-r border-zinc-800 bg-surface/50 backdrop-blur flex flex-col fixed left-0 top-0 z-50">
            <div className="p-6">
                <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                    MedValidator
                </h1>
                <p className="text-xs text-zinc-500 mt-1">Auditor Workbench v1.0</p>
            </div>

            <nav className="flex-1 px-4 space-y-2">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path))

                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={clsx(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative",
                                isActive ? "text-white" : "text-zinc-400 hover:text-white hover:bg-zinc-800/50"
                            )}
                        >
                            {isActive && (
                                <motion.div
                                    layoutId="activeNav"
                                    className="absolute inset-0 bg-zinc-800 border border-zinc-700/50 rounded-xl"
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                />
                            )}

                            <item.icon className={clsx("w-5 h-5 relative z-10", isActive ? "text-primary" : "group-hover:text-primary/80")} />
                            <span className="font-medium relative z-10">{item.label}</span>
                        </Link>
                    )
                })}
            </nav>

            <div className="p-4 border-t border-zinc-800">
                <div className="flex items-center gap-3 px-4 py-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-xs shadow-lg shadow-primary/20">
                        VK
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">Vidit Khairkar</p>
                        <p className="text-xs text-zinc-500">Senior Auditor</p>
                    </div>
                </div>
            </div>
        </aside>
    )
}
