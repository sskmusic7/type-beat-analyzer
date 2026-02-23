'use client'

import { TrendingUp } from 'lucide-react'
import TrendingArtists from './TrendingArtists'
import { TrendingArtist } from '@/types'

interface TrendingSectionProps {
  artists: TrendingArtist[]
  setArtists: (artists: TrendingArtist[]) => void
}

export default function TrendingSection({ artists, setArtists }: TrendingSectionProps) {
  return (
    <section className="py-24 bg-slate-900 relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-purple-500/20 to-transparent"></div>
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <TrendingUp className="w-6 h-6 text-cyan-400" />
            <span className="text-sm font-semibold text-cyan-400 uppercase tracking-wider">
              Trending Now
            </span>
          </div>
          <h2 className="font-display text-4xl font-bold text-slate-50 mb-4">
            Top Artists This Week
          </h2>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            See which artists are trending and get insights into the current music market
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          <TrendingArtists artists={artists} setArtists={setArtists} />
        </div>
      </div>
    </section>
  )
}
