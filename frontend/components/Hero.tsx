'use client'

import { useState } from 'react'
import { Upload, Music, TrendingUp, Sparkles } from 'lucide-react'
import AudioUploader from './AudioUploader'
import { AnalysisResult } from '@/types'

interface HeroProps {
  onAnalysisComplete: (result: AnalysisResult) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export default function Hero({ onAnalysisComplete, loading, setLoading }: HeroProps) {
  return (
    <section className="relative pb-10 pt-20 md:pt-32 lg:h-[88vh] min-h-screen">
      {/* Gradient Background */}
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10">
        <div className="h-full w-full bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900"></div>
      </div>
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 hidden dark:block">
        <div className="h-full w-full bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900"></div>
      </div>

      <div className="container h-full mx-auto px-4">
        <div className="grid h-full items-center gap-4 md:grid-cols-12">
          {/* Left Content */}
          <div className="col-span-12 md:col-span-6 flex h-full flex-col items-center justify-center py-10 md:items-start md:py-20 xl:col-span-5">
            <div className="mb-6 flex items-center gap-2 text-accent">
              <Sparkles className="w-6 h-6 animate-pulse" />
              <span className="text-sm font-semibold uppercase tracking-wider">AI-Powered Analysis</span>
            </div>
            
            <h1 className="mb-6 text-center font-display text-5xl font-bold text-white md:text-left lg:text-6xl xl:text-7xl">
              Know Your Sound,
              <br />
              <span className="bg-gradient-to-r from-accent to-accent-light bg-clip-text text-transparent">
                Optimize for Market
              </span>
            </h1>
            
            <p className="mb-8 text-center text-lg text-gray-300 md:text-left max-w-lg">
              Shazam for type beats. Upload your beat and discover which artist's style it matches. 
              Get real-time trending intelligence to optimize your music production.
            </p>

            {/* Upload Section */}
            <div className="w-full max-w-lg mb-8">
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
                <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload Your Beat
                </h2>
                <AudioUploader
                  onAnalysisComplete={onAnalysisComplete}
                  loading={loading}
                  setLoading={setLoading}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="flex gap-6 text-center md:text-left">
              <div>
                <div className="text-3xl font-bold text-white">697</div>
                <div className="text-sm text-gray-400">Trained Fingerprints</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-white">74</div>
                <div className="text-sm text-gray-400">Artists</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-white">65</div>
                <div className="text-sm text-gray-400">Fully Trained</div>
              </div>
            </div>
          </div>

          {/* Right Visual */}
          <div className="col-span-12 md:col-span-6 xl:col-span-7">
            <div className="relative text-center md:pl-8 md:text-right">
              {/* Animated Music Visualizer */}
              <div className="relative inline-block">
                <div className="absolute inset-0 bg-gradient-to-r from-accent/20 to-accent-light/20 rounded-full blur-3xl animate-pulse"></div>
                <div className="relative bg-white/5 backdrop-blur-lg rounded-3xl p-8 border border-white/20">
                  <Music className="w-32 h-32 text-accent mx-auto mb-4 animate-bounce" />
                  <div className="flex items-end justify-center gap-1 h-20">
                    {[1, 2, 3, 4, 5, 4, 3, 2].map((height, i) => (
                      <div
                        key={i}
                        className="w-2 bg-gradient-to-t from-accent to-accent-light rounded-full animate-pulse"
                        style={{
                          height: `${height * 10}px`,
                          animationDelay: `${i * 0.1}s`,
                        }}
                      />
                    ))}
                  </div>
                  <p className="text-white mt-4 text-sm">Analyzing your beat...</p>
                </div>
              </div>

              {/* Floating Elements */}
              <div className="absolute top-0 right-0 animate-fly">
                <TrendingUp className="w-16 h-16 text-accent/30" />
              </div>
              <div className="absolute bottom-0 left-0 animate-fly" style={{ animationDelay: '2s' }}>
                <Sparkles className="w-12 h-12 text-accent-light/30" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
