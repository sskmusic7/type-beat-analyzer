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
    <section className="py-24 bg-jacarta-50 dark:bg-jacarta-900">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <TrendingUp className="w-6 h-6 text-accent" />
            <span className="text-sm font-semibold text-accent uppercase tracking-wider">
              Trending Now
            </span>
          </div>
          <h2 className="font-display text-4xl font-bold text-jacarta-700 dark:text-white mb-4">
            Top Artists This Week
          </h2>
          <p className="text-lg text-jacarta-500 dark:text-jacarta-300 max-w-2xl mx-auto">
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
