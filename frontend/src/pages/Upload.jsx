import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, File, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../api'

export function Upload() {
    const [isDragging, setIsDragging] = useState(false)
    const [status, setStatus] = useState('idle') // idle, uploading, success, error
    const [errorMsg, setErrorMsg] = useState('')
    const fileInputRef = useRef(null)
    const navigate = useNavigate()

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        const files = e.dataTransfer.files
        if (files.length > 0) {
            handleUpload(files[0])
        }
    }

    const handleFileSelect = (e) => {
        if (e.target.files.length > 0) {
            handleUpload(e.target.files[0])
        }
    }

    const handleUpload = async (file) => {
        setStatus('uploading')
        setErrorMsg('')

        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await api.post('/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })

            setStatus('success')

            // Navigate to the auditor view after a short delay
            setTimeout(() => {
                navigate(`/bills/${response.data.id}`)
            }, 1500)

        } catch (err) {
            console.error(err)
            setStatus('error')
            setErrorMsg(err.response?.data?.detail || 'Failed to upload file. Please ensure the backend is running.')
        }
    }

    return (
        <div className="max-w-2xl mx-auto mt-20">
            <div className="text-center mb-10">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                    Upload Medical Bill
                </h2>
                <p className="text-zinc-400 mt-2">
                    Upload any document to start the auditing process.
                </p>
            </div>

            <motion.div
                layout
                className={`
          relative border-2 border-dashed rounded-3xl p-10 text-center transition-all duration-300
          ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-zinc-700 bg-surface/30'}
          ${status === 'error' ? 'border-danger/50' : ''}
          ${status === 'success' ? 'border-primary/50' : ''}
        `}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    onChange={handleFileSelect}
                />

                <AnimatePresence mode="wait">
                    {status === 'idle' && (
                        <motion.div
                            key="idle"
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="flex flex-col items-center gap-4"
                        >
                            <div className="w-20 h-20 rounded-full bg-zinc-800 flex items-center justify-center mb-2 shadow-inner">
                                <UploadCloud className="w-10 h-10 text-zinc-400" />
                            </div>
                            <div>
                                <p className="text-lg font-medium text-white">Drag & drop your file here</p>
                                <p className="text-sm text-zinc-500 mt-1">or click to browse</p>
                            </div>
                            <button
                                onClick={() => fileInputRef.current.click()}
                                className="mt-4 px-6 py-2 bg-zinc-100 text-zinc-900 rounded-full font-semibold hover:bg-white transition-colors"
                            >
                                Select File
                            </button>
                        </motion.div>
                    )}

                    {status === 'uploading' && (
                        <motion.div
                            key="uploading"
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="flex flex-col items-center gap-4 py-10"
                        >
                            <div className="relative">
                                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                                <Loader2 className="w-12 h-12 text-primary animate-spin relative z-10" />
                            </div>
                            <p className="text-lg font-medium animate-pulse">Uploading and Initializing OCR...</p>
                        </motion.div>
                    )}

                    {status === 'success' && (
                        <motion.div
                            key="success"
                            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                            className="flex flex-col items-center gap-4 py-8"
                        >
                            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center text-primary">
                                <CheckCircle className="w-10 h-10" />
                            </div>
                            <p className="text-xl font-bold text-white">Upload Complete!</p>
                            <p className="text-zinc-400">Redirecting to Auditor Workbench...</p>
                        </motion.div>
                    )}

                    {status === 'error' && (
                        <motion.div
                            key="error"
                            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                            className="flex flex-col items-center gap-4 py-8"
                        >
                            <div className="w-20 h-20 rounded-full bg-danger/20 flex items-center justify-center text-danger">
                                <AlertCircle className="w-10 h-10" />
                            </div>
                            <div>
                                <p className="text-xl font-bold text-danger">Upload Failed</p>
                                <p className="text-sm text-zinc-400 mt-2 max-w-sm mx-auto">{errorMsg}</p>
                            </div>
                            <button
                                onClick={() => setStatus('idle')}
                                className="mt-4 px-6 py-2 bg-zinc-800 rounded-full hover:bg-zinc-700 font-medium"
                            >
                                Try Again
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    )
}
