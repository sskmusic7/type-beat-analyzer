'use client'

import { useState } from 'react'
import { Upload, TrendingUp, Music } from 'lucide-react'
import AudioUploader from '@/components/AudioUploader'
import ResultsDisplay from '@/components/ResultsDisplay'
import TrendingArtists from '@/components/TrendingArtists'
import { AnalysisResult, TrendingArtist as TrendingArtistType } from '@/types'

export default function Home() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [trendingArtists, setTrendingArtists] = useState<TrendingArtistType[]>([])
  const [loading, setLoading] = useState(false)

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4 flex items-center justify-center gap-3">
            <Music className="w-12 h-12" />
            Type Beat Analyzer
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            Shazam for type beats - Know your sound, optimize for the market
          </p>
          <p className="text-sm text-gray-400">
            Upload your beat • Get artist matches • See who's trending
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Upload & Results Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload Section */}
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                <Upload className="w-6 h-6" />
                Upload Your Beat
              </h2>
              <AudioUploader
                onAnalysisComplete={handleAnalysisComplete}
                loading={loading}
                setLoading={setLoading}
              />
            </div>

            {/* Results Section */}
            {analysisResult && (
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
                <ResultsDisplay result={analysisResult} />
              </div>
            )}
          </div>

          {/* Trending Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 sticky top-4">
              <h2 className="text-2xl font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="w-6 h-6" />
                Trending Now
              </h2>
              <TrendingArtists
                artists={trendingArtists}
                setArtists={setTrendingArtists}
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
