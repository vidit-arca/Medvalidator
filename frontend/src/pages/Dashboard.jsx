import { motion } from 'framer-motion'
import { FileCheck, AlertCircle, DollarSign, Activity, FileText } from 'lucide-react'

const stats = [
    { label: 'Bills Processed today', value: '45', icon: FileText, color: 'from-blue-500 to-cyan-500' },
    { label: 'Valid Bills', value: '38', icon: FileCheck, color: 'from-primary to-emerald-400' },
    { label: 'Savings Detected', value: '₹12,450', icon: DollarSign, color: 'from-accent to-purple-400' },
    { label: 'Needs Review', value: '7', icon: AlertCircle, color: 'from-warning to-orange-400' },
]

const recentActivity = [
    { id: 1, file: 'INV-2024-001.pdf', status: 'VALID', time: '10 mins ago', amount: '₹450.00' },
    { id: 2, file: 'Medical_Rep_002.png', status: 'INVALID', time: '25 mins ago', amount: '₹1,200.00' },
    { id: 3, file: 'Scan_042.pdf', status: 'PROCESSING', time: 'Just now', amount: '-' },
]

export function Dashboard() {
    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold">Dashboard</h2>
                <p className="text-zinc-400">Overview of today's auditing performance</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, index) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="glass p-6 rounded-2xl relative overflow-hidden group"
                    >
                        <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-gradient-to-br ${stat.color} blur-2xl w-32 h-32 rounded-full`} />

                        <div className="flex items-start justify-between relative z-10">
                            <div>
                                <p className="text-sm text-zinc-400 font-medium">{stat.label}</p>
                                <h3 className="text-3xl font-bold mt-2">{stat.value}</h3>
                            </div>
                            <div className={`p-3 rounded-xl bg-gradient-to-br ${stat.color} shadow-lg shadow-black/20`}>
                                <stat.icon className="w-5 h-5 text-white" />
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            <div className="glass rounded-2xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                        <Activity className="w-5 h-5 text-accent" />
                        Recent Activity
                    </h3>
                    <button className="text-sm text-primary hover:text-primary/80 font-medium">View All</button>
                </div>

                <div className="space-y-4">
                    {recentActivity.map((item, i) => (
                        <motion.div
                            key={item.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.4 + (i * 0.1) }}
                            className="flex items-center justify-between p-4 rounded-xl bg-zinc-800/30 hover:bg-zinc-800/50 transition-colors border border-zinc-800"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-lg bg-zinc-700/50 flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-zinc-400" />
                                </div>
                                <div>
                                    <p className="font-medium">{item.file}</p>
                                    <p className="text-xs text-zinc-500">{item.time}</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-6">
                                <p className="font-mono text-zinc-300">{item.amount}</p>
                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${item.status === 'VALID' ? 'bg-primary/20 text-primary' :
                                    item.status === 'INVALID' ? 'bg-danger/20 text-danger' :
                                        'bg-warning/20 text-warning'
                                    }`}>
                                    {item.status}
                                </span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    )
}
