import React from 'react'
import { Toaster } from 'react-hot-toast'
import { ExternalDevelopmentControlCenter } from './pages/ExternalDevelopmentControlCenter'
import './index.css'

const CockpitApp: React.FC = () => (
  <div className="min-h-screen bg-slate-950 text-slate-100">
    <ExternalDevelopmentControlCenter />
    <Toaster position="top-right" />
  </div>
)

export default CockpitApp
