'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Dna, Users } from 'lucide-react'
import BeatBlendAnalyzer from '@/components/BeatBlendAnalyzer'
import { getApiBaseUrl } from '@/lib/api'
import { DNAArtist } from '@/types/dna'

export default function BlendPage() {
  const [artists, setArtists] = useState<DNAArtist[]>([])

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/dna/artists`)
      .then(r => r.json())
      .then(data => setArtists(data.artists || []))
      .catch(() => {})
  }, [])

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Link>
            <div className="flex items-center gap-2">
              <Dna className="w-5 h-5 text-cyan-400" />
              <h1 className="text-xl font-bold text-slate-50 font-display">
                Beat DNA Blend
              </h1>
            </div>
          </div>
          <Link
            href="/similarity"
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-300 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-lg transition-colors"
          >
            <Users className="w-4 h-4" />
            Similarity Matrix
          </Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Intro */}
        <div className="mb-8 text-center">
          <h2 className="text-3xl font-bold text-slate-50 font-display mb-3">
            What does your beat sound like?
          </h2>
          <p className="text-slate-400 max-w-lg mx-auto">
            Upload a beat and our Audio DNA engine will analyze its CLAP signature,
            tempo, key, and spectral features to find which artists it blends with.
          </p>
        </div>

        {/* Stats bar */}
        {artists.length > 0 && (
          <div className="mb-8 flex items-center justify-center gap-6 text-sm text-slate-400">
            <span>
              <span className="text-cyan-400 font-semibold">{artists.length}</span> artist profiles loaded
            </span>
            <span className="text-slate-700">|</span>
            <span>
              <span className="text-purple-400 font-semibold">
                {artists.reduce((sum, a) => sum + a.track_count, 0)}
              </span> total tracks analyzed
            </span>
          </div>
        )}

        {/* Main Analyzer */}
        <BeatBlendAnalyzer />
      </div>
    </main>
  )
}
