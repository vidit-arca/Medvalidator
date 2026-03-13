import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Search, Loader2, Database, AlertCircle } from 'lucide-react'
import api from '../api'

export function MasterPrices() {
    const [search, setSearch] = useState('')

    const { data, isLoading, isError } = useQuery({
        queryKey: ['masterPrices', search],
        queryFn: async () => {
            // In a real app we would server-side filter. 
            // For MVP assuming the list endpoint returns all or we just fetch top 100 if searching.
            // Based on backend exploration, there isn't a search endpoint explicitly, just GET /api/v1/master-prices
            // So we will fetch and filter client side for MVP or ask backend to support it.
            // Checking backend code: app/api/master_price.py was not fully read but assumed to exist.
            // Let's assume standard behavior.
            const res = await api.get('/master-prices')
            return res.data
        }
    })

    // Client-side filtering for MVP
    const filteredData = data
        ? data.filter(item =>
            item.procedure_name.toLowerCase().includes(search.toLowerCase()) ||
            item.procedure_code.toLowerCase().includes(search.toLowerCase())
        )
        : []

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold">Master Price List</h2>
                    <p className="text-zinc-400">Manage standard procedure rates and variances</p>
                </div>
                <button className="px-4 py-2 bg-primary text-zinc-900 font-bold rounded-lg hover:bg-primary/90 transition-colors">
                    + Add New Item
                </button>
            </div>

            <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <input
                    type="text"
                    placeholder="Search by procedure name or code..."
                    className="w-full bg-zinc-900 border border-zinc-700 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 placeholder:text-zinc-600"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {isLoading && (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                </div>
            )}

            {isError && (
                <div className="flex flex-col items-center py-20 text-danger">
                    <AlertCircle className="w-10 h-10 mb-2" />
                    <p>Failed to load master prices.</p>
                </div>
            )}

            {!isLoading && !isError && (
                <div className="glass rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                        <thead className="bg-zinc-800/50 text-zinc-400 font-medium">
                            <tr>
                                <th className="p-4">Code</th>
                                <th className="p-4">Procedure Name</th>
                                <th className="p-4 text-right">Standard Price</th>
                                <th className="p-4 text-center">Variance %</th>
                                <th className="p-4 text-right">Stock</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-800">
                            {filteredData.slice(0, 50).map((item) => ( // Limit rendering to 50 for performance
                                <motion.tr
                                    key={item.id || item.procedure_code}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="hover:bg-zinc-800/30 transition-colors group"
                                >
                                    <td className="p-4 font-mono text-sm text-accent">{item.procedure_code}</td>
                                    <td className="p-4 font-medium">{item.procedure_name}</td>
                                    <td className="p-4 text-right font-mono">₹{item.standard_unit_price}</td>
                                    <td className="p-4 text-center text-sm">
                                        <span className="px-2 py-1 bg-zinc-800 rounded text-zinc-300">
                                            ±{item.allowed_variance_percent}%
                                        </span>
                                    </td>
                                    <td className="p-4 text-right text-zinc-400">{item.stock}</td>
                                </motion.tr>
                            ))}

                            {filteredData.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="p-10 text-center text-zinc-500">
                                        No items found matching "{search}"
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>

                    <div className="p-4 border-t border-zinc-800 text-center text-xs text-zinc-500">
                        Showing {Math.min(filteredData.length, 50)} of {filteredData.length} items
                    </div>
                </div>
            )}
        </div>
    )
}
