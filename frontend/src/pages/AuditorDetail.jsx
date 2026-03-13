import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Loader2, Check, X, AlertTriangle, ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '../api'

export function AuditorDetail() {
    const { id } = useParams()

    const { data: bill, isLoading } = useQuery({
        queryKey: ['bill', id],
        queryFn: async () => {
            const res = await api.get(`/bills/${id}`)
            return res.data
        },
        refetchInterval: (query) => {
            const status = query.state.data?.status
            return status === 'PROCESSING' || status === 'PENDING' ? 1000 : false
        }
    })

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh]">
                <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                <p className="text-zinc-400">Loading Bill Data...</p>
            </div>
        )
    }

    if (!bill) {
        return <div>Bill not found</div>
    }

    // Placeholder for line items if not yet populated or backend format differs
    const lineItems = bill.line_items || []

    return (
        <div className="h-[calc(100vh-6rem)] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                    <Link to="/bills" className="p-2 hover:bg-zinc-800 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h2 className="text-xl font-bold">{bill.filename}</h2>
                        <p className="text-xs text-zinc-500 font-mono">ID: {id}</p>
                    </div>
                </div>

                <div className="flex gap-3">
                    <div className={`px-6 py-2 rounded-xl font-bold flex items-center gap-3 border shadow-lg ${bill.final_decision === 'VALID' ? 'bg-primary/20 text-primary border-primary/30' :
                        bill.final_decision === 'INVALID' ? 'bg-danger/20 text-danger border-danger/30' :
                            'bg-zinc-800 text-zinc-400 border-zinc-700'
                        }`}>
                        {bill.final_decision === 'VALID' && <Check className="w-6 h-6" />}
                        {bill.final_decision === 'INVALID' && <X className="w-6 h-6" />}
                        {bill.final_decision === 'REVIEW' && <AlertTriangle className="w-6 h-6" />}
                        <span className="text-lg uppercase tracking-wider">{bill.final_decision || bill.status}</span>
                    </div>
                </div>
            </div>

            {/* Split View */}
            <div className="flex-1 grid grid-cols-2 gap-6 min-h-0">
                {/* Left: Document Viewer */}
                <div className="glass rounded-2xl overflow-hidden bg-black/50 relative flex flex-col">
                    <div className="p-3 bg-zinc-900/80 border-b border-zinc-800 flex justify-between items-center backdrop-blur">
                        <span className="text-sm font-medium text-zinc-400">Original Document</span>
                        <button className="text-xs bg-zinc-800 px-2 py-1 rounded">Open Original</button>
                    </div>
                    <div className="flex-1 relative flex items-center justify-center bg-zinc-950">
                        {bill.filename.toLowerCase().endsWith('.pdf') ? (
                            <iframe
                                src={`http://localhost:8000/raw_storage/${bill.id}_${bill.filename}`}
                                className="w-full h-full border-0"
                                title="Original Document"
                            />
                        ) : (
                            <img
                                src={`http://localhost:8000/raw_storage/${bill.id}_${bill.filename}`}
                                alt="Original Bill"
                                className="max-w-full max-h-full object-contain"
                            />
                        )}
                    </div>
                </div>

                {/* Right: Validation & Line Items */}
                <div className="flex flex-col gap-4 overflow-hidden">
                    <div className="glass rounded-2xl flex-1 flex flex-col overflow-hidden">
                        <div className="p-4 border-b border-zinc-800 bg-zinc-900/50">
                            <h3 className="font-bold">Extracted Line Items</h3>
                        </div>

                        <div className="overflow-y-auto p-4 space-y-3 flex-1">
                            {lineItems.length === 0 && (
                                <div className="text-center py-10 text-zinc-500">
                                    {bill.status === 'PROCESSING' || bill.status === 'PENDING' ? (
                                        <div className="flex flex-col items-center gap-2">
                                            <Loader2 className="w-6 h-6 animate-spin" />
                                            <p className="animate-pulse">
                                                {bill.audit_logs && bill.audit_logs.length > 0
                                                    ? `Step: ${bill.audit_logs[bill.audit_logs.length - 1].component}...`
                                                    : 'Initializing Pipeline...'
                                                }
                                            </p>
                                        </div>
                                    ) : (
                                        'No items extracted found.'
                                    )}
                                </div>
                            )}

                            {lineItems.map((item, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.05 }}
                                    className={`p-4 rounded-xl border ${item.line_decision === 'VALID' ? 'bg-primary/5 border-primary/20' :
                                        item.line_decision === 'INVALID' ? 'bg-danger/5 border-danger/20' :
                                            'bg-zinc-800/40 border-zinc-700'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <h4 className="font-medium text-lg">{item.item_name || item.raw_ocr_text}</h4>
                                        <span className="font-mono font-bold">₹{item.extracted_price}</span>
                                    </div>

                                    <div className="space-y-2 text-sm">
                                        <div className="flex items-center justify-between text-zinc-400">
                                            <span>Mapped Code:</span>
                                            <div className="flex items-center gap-2">
                                                {item.is_payable === false && (
                                                    <span className="text-xs bg-red-500/20 text-red-500 border border-red-500/30 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                                                        Non-Payable
                                                    </span>
                                                )}
                                                <span className="text-accent font-mono bg-accent/10 px-1 rounded">
                                                    {item.mapped_procedure_code || 'Unmapped'}
                                                </span>
                                            </div>
                                        </div>

                                        {item.price_difference !== undefined && item.price_difference !== null && (
                                            <div className="flex flex-col gap-1 items-end">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-zinc-500 text-xs">Diff:</span>
                                                    <span className={`text-xs font-mono font-medium ${item.price_difference > 0 ? 'text-danger' : 'text-primary'}`}>
                                                        {item.price_difference > 0 ? '+' : ''}{item.price_difference}
                                                    </span>
                                                </div>
                                            </div>
                                        )}

                                        {item.mapping_reason && (
                                            <div className="text-xs text-zinc-500 bg-black/20 p-2 rounded mt-2">
                                                AI Reason: {item.mapping_reason}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
