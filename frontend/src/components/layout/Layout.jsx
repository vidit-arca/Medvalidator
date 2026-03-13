import { Sidebar } from './Sidebar'

export function Layout({ children }) {
    return (
        <div className="min-h-screen bg-background text-zinc-100 font-sans">
            <div className="fixed inset-0 z-0 opacity-20 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-primary/20 blur-[150px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent/20 blur-[150px]" />
            </div>

            <Sidebar />

            <main className="pl-64 min-h-screen relative z-10">
                <div className="p-8 max-w-7xl mx-auto">
                    {children}
                </div>
            </main>
        </div>
    )
}
