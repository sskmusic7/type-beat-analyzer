'use client'

import FingerprintTrainingDashboard from '@/components/FingerprintTrainingDashboard'
import Fingerprint3DVisualization from '@/components/Fingerprint3DVisualization'
import MissionControl from '@/components/MissionControl'
import ArtistDNAPanel from '@/components/ArtistDNAPanel'
import { Shield, Database, Activity, Box, Dna } from 'lucide-react'

export default function AdminDashboard() {
  return (
    <main className="min-h-screen bg-slate-950">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-950 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3 mb-2">
            <Shield className="w-6 h-6 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
          </div>
          <p className="text-slate-400">
            Manage fingerprints, monitor training, and track system activity
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Fingerprint Training Dashboard */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-cyan-400" />
            <h2 className="text-xl font-semibold text-white">Fingerprint Training</h2>
          </div>
          <FingerprintTrainingDashboard />
        </section>

        {/* Artist DNA Profiles */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Dna className="w-5 h-5 text-green-400" />
            <h2 className="text-xl font-semibold text-white">Artist DNA Profiles</h2>
          </div>
          <ArtistDNAPanel />
        </section>

        {/* 3D Visualization */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Box className="w-5 h-5 text-cyan-400" />
            <h2 className="text-xl font-semibold text-white">3D Fingerprint Visualization</h2>
          </div>
          <Fingerprint3DVisualization />
        </section>

        {/* Mission Control */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-purple-400" />
            <h2 className="text-xl font-semibold text-white">Task Monitoring</h2>
          </div>
          <MissionControl />
        </section>
      </div>
    </main>
  )
}
