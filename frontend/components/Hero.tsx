'use client'

import { useState } from 'react'
import { Upload, Music, TrendingUp, Sparkles, Dna } from 'lucide-react'
import Link from 'next/link'
import AudioUploader from './AudioUploader'
import { AnalysisResult } from '@/types'

interface HeroProps {
  onAnalysisComplete: (result: AnalysisResult) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export default function Hero({ onAnalysisComplete, loading, setLoading }: HeroProps) {
  return (
    <section className="relative pb-10 pt-20 md:pt-32 lg:h-[88vh] min-h-screen overflow-hidden">
      {/* Cohesive Gradient Background */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-navy-950 to-purple-950"></div>
        <div className="absolute inset-0 bg-gradient-to-tr from-purple-900/20 via-transparent to-cyan-900/20"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl"></div>
      </div>

      <div className="container h-full mx-auto px-4 relative z-10">
        <div className="grid h-full items-center gap-4 md:grid-cols-12">
          {/* Left Content */}
          <div className="col-span-12 md:col-span-6 flex h-full flex-col items-center justify-center py-10 md:items-start md:py-20 xl:col-span-5">
            <div className="mb-6 flex items-center gap-2 text-cyan-400">
              <Sparkles className="w-6 h-6 animate-pulse text-cyan-400" />
              <span className="text-sm font-semibold uppercase tracking-wider text-cyan-400">AI-Powered Analysis</span>
            </div>
            
            <h1 className="mb-6 text-center font-display text-5xl font-bold text-slate-50 md:text-left lg:text-6xl xl:text-7xl">
              Know Your Sound,
              <br />
              <span className="bg-gradient-to-r from-purple-400 via-purple-500 to-cyan-400 bg-clip-text text-transparent">
                Optimize for Market
              </span>
            </h1>
            
            <p className="mb-8 text-center text-lg text-slate-300 md:text-left max-w-lg">
              Shazam for type beats. Upload your beat and discover which artist's style it matches. 
              Get real-time trending intelligence to optimize your music production.
            </p>

            {/* Upload Section */}
            <div className="w-full max-w-lg mb-8">
              <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-glow-purple">
                <h2 className="text-xl font-semibold text-slate-50 mb-4 flex items-center gap-2">
                  <Upload className="w-5 h-5 text-purple-400" />
                  Upload Your Beat
                </h2>
                <AudioUploader
                  onAnalysisComplete={onAnalysisComplete}
                  loading={loading}
                  setLoading={setLoading}
                />
              </div>
            </div>

            {/* DNA Blend Link */}
            <Link
              href="/blend"
              className="mb-8 w-full max-w-lg flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-600/20 to-purple-600/20 hover:from-cyan-600/30 hover:to-purple-600/30 border border-cyan-500/30 hover:border-cyan-500/50 rounded-xl transition-all text-sm font-medium text-cyan-300"
            >
              <Dna className="w-4 h-4" />
              Try DNA Blend Analysis — find your sonic fingerprint
            </Link>

            {/* Stats */}
            <div className="flex gap-6 text-center md:text-left">
              <div>
                <div className="text-3xl font-bold text-slate-50">697</div>
                <div className="text-sm text-slate-400">Trained Fingerprints</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-50">74</div>
                <div className="text-sm text-slate-400">Artists</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-slate-50">65</div>
                <div className="text-sm text-slate-400">Fully Trained</div>
              </div>
            </div>
          </div>

          {/* Right Visual */}
          <div className="col-span-12 md:col-span-6 xl:col-span-7">
            <div className="relative text-center md:pl-8 md:text-right">
              {/* Animated Music Visualizer */}
              <div className="relative inline-block">
                <div className="absolute inset-0 bg-gradient-to-r from-purple-500/30 to-cyan-500/30 rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="relative bg-slate-900/60 backdrop-blur-xl rounded-3xl p-8 border border-slate-700/50 shadow-glow-lg">
                  <Music className="w-32 h-32 text-purple-400 mx-auto mb-4 animate-bounce" />
                  <div className="flex items-end justify-center gap-1 h-20">
                    {[1, 2, 3, 4, 5, 4, 3, 2].map((height, i) => (
                      <div
                        key={i}
                        className="w-2 bg-gradient-to-t from-purple-500 to-cyan-400 rounded-full animate-pulse"
                        style={{
                          height: `${height * 10}px`,
                          animationDelay: `${i * 0.1}s`,
                        }}
                      />
                    ))}
                  </div>
                  <p className="text-slate-300 mt-4 text-sm">Analyzing your beat...</p>
                </div>
              </div>

              {/* Floating Elements */}
              <div className="absolute top-0 right-0 animate-fly">
                <TrendingUp className="w-16 h-16 text-purple-400/30" />
              </div>
              <div className="absolute bottom-0 left-0 animate-fly" style={{ animationDelay: '2s' }}>
                <Sparkles className="w-12 h-12 text-cyan-400/30" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
