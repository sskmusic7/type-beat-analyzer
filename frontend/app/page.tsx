'use client'

import { useState } from 'react'
import Hero from '@/components/Hero'
import TrendingSection from '@/components/TrendingSection'
import ResultsSection from '@/components/ResultsSection'
import MissionControl from '@/components/MissionControl'
import FingerprintTrainingDashboard from '@/components/FingerprintTrainingDashboard'
import { AnalysisResult, TrendingArtist as TrendingArtistType } from '@/types'

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [trendingArtists, setTrendingArtists] = useState<TrendingArtistType[]>([])
  const [loading, setLoading] = useState(false)
  const [showMissionControl, setShowMissionControl] = useState(true)
  const [showTrainingDashboard, setShowTrainingDashboard] = useState(true)

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result)
    // Scroll to results
    setTimeout(() => {
      const resultsSection = document.getElementById('results')
      resultsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Hero Section with Upload */}
      <Hero
        onAnalysisComplete={handleAnalysisComplete}
        loading={loading}
        setLoading={setLoading}
      />

      {/* Mission Control Dashboard */}
      <section id="mission-control" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="mb-4 flex justify-end gap-2">
          <button
            onClick={() => setShowTrainingDashboard(!showTrainingDashboard)}
            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-lg transition-colors"
          >
            {showTrainingDashboard ? 'Hide' : 'Show'} Training Dashboard
          </button>
          <button
            onClick={() => setShowMissionControl(!showMissionControl)}
            className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-lg transition-colors"
          >
            {showMissionControl ? 'Hide' : 'Show'} Mission Control
          </button>
        </div>
        {showTrainingDashboard && (
          <div className="mb-8">
            <FingerprintTrainingDashboard />
          </div>
        )}
        {showMissionControl && <MissionControl />}
      </section>

      {/* Results Section */}
      {analysisResult && (
        <div id="results">
          <ResultsSection result={analysisResult} />
        </div>
      )}

      {/* Trending Section */}
      <TrendingSection
        artists={trendingArtists}
        setArtists={setTrendingArtists}
      />
    </main>
  )
}
