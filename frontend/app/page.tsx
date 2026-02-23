'use client'

import { useState } from 'react'
import Hero from '@/components/Hero'
import TrendingSection from '@/components/TrendingSection'
import ResultsSection from '@/components/ResultsSection'
import { AnalysisResult, TrendingArtist as TrendingArtistType } from '@/types'

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [trendingArtists, setTrendingArtists] = useState<TrendingArtistType[]>([])
  const [loading, setLoading] = useState(false)

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result)
    // Scroll to results
    setTimeout(() => {
      const resultsSection = document.getElementById('results')
      resultsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 100)
  }

  return (
    <main className="min-h-screen">
      {/* Hero Section with Upload */}
      <Hero
        onAnalysisComplete={handleAnalysisComplete}
        loading={loading}
        setLoading={setLoading}
      />

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
