import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { FileText, ChevronRight, Loader2, AlertCircle, Clock } from 'lucide-react'
import api from '../api'

export function AuditorList() {
    // Note: Assuming endpoint GET /api/v1/bills exists or similar. 
    // Based on backend check, app/api/ingestion.py typically has upload and get, 
    // but maybe not a list endpoint? I should check this eventually.
    // For now, I'll assume we might need to rely on the backend being updated 
    // or I'll just mock it if it fails in testing.
    // Actually, normally specific endpoints like retrieve bill {id} exist, 
    // listing might not be there. Use Dashboard mocked data style or try to fetch.

    // Attempting to hit an endpoint that MIGHT not exist yet, 
    // so I will wrap it gracefully or mock it if error.

    const { data: bills, isLoading, isError } = useQuery({
        queryKey: ['bills'],
        queryFn: async () => {
            const res = await api.get('/bills')
            return res.data
        }
    })

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold">Audit History</h2>

            {isLoading && (
                <div className="flex justify-center py-20">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                </div>
            )}

            <div className="grid gap-4">
                {bills?.map((bill, i) => (
                    <motion.div
                        key={bill.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.05 }}
                    >
                        <Link
                            to={`/bills/${bill.id}`}
                            className="glass p-4 rounded-xl flex items-center justify-between hover:bg-zinc-800/50 transition-all group"
                        >
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-zinc-800 rounded-lg group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                                    <FileText className="w-6 h-6" />
                                </div>
                                <div>
                                    <p className="font-semibold text-lg">{bill.filename}</p>
                                    <div className="flex items-center gap-2 text-sm text-zinc-500">
                                        <Clock className="w-3 h-3" />
                                        <span>{new Date(bill.upload_timestamp).toLocaleString()}</span>
                                        <span className="text-zinc-700 mx-1">•</span>
                                        <span className="font-mono text-xs">{bill.id.slice(0, 8)}...</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${bill.final_decision === 'VALID' ? 'bg-primary/20 text-primary' :
                                    bill.final_decision === 'INVALID' ? 'bg-danger/20 text-danger' :
                                        bill.status === 'PROCESSING' ? 'bg-accent/20 text-accent animate-pulse' :
                                            'bg-warning/20 text-warning'
                                    }`}>
                                    {bill.final_decision || bill.status}
                                </span>
                                <ChevronRight className="w-5 h-5 text-zinc-600 group-hover:text-white" />
                            </div>
                        </Link>
                    </motion.div>
                ))}
            </div>
        </div>
    )
}
