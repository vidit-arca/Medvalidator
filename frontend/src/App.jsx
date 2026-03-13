import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { Dashboard } from './pages/Dashboard'
import { Upload } from './pages/Upload'
import { AuditorList } from './pages/AuditorList'
import { AuditorDetail } from './pages/AuditorDetail'
import { MasterPrices } from './pages/MasterPrices'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/bills" element={<AuditorList />} />
        <Route path="/bills/:id" element={<AuditorDetail />} />
        <Route path="/master-prices" element={<MasterPrices />} />
      </Routes>
    </Layout>
  )
}

export default App
