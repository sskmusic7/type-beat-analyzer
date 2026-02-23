'use client'

import { useEffect, useState } from 'react'
import { TrendingArtist } from '@/types'
import axios from 'axios'
import { TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react'
import { getApiBaseUrl } from '@/lib/api'

interface TrendingArtistsProps {
  artists: TrendingArtist[]
  setArtists: (artists: TrendingArtist[]) => void
}

export default function TrendingArtists({ artists, setArtists }: TrendingArtistsProps) {
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const response = await axios.get<TrendingArtist[]>(
          `${getApiBaseUrl()}/api/trending?limit=10`
        )
        setArtists(response.data)
      } catch (error) {
        console.error('Failed to fetch trending artists:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTrending()
    // Refresh every 5 minutes
    const interval = setInterval(fetchTrending, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [setArtists])

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-cyan-400" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-400" />
      default:
        return <Minus className="w-4 h-4 text-slate-400" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
      </div>
    )
  }

  if (artists.length === 0) {
    return (
      <p className="text-slate-400 text-sm text-center py-4">
        No trending data available
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {artists.map((artist, index) => (
        <div
          key={index}
          className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50 hover:border-purple-500/50 transition-all backdrop-blur-sm"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-purple-400 font-bold text-lg">
                #{artist.rank}
              </span>
              <span className="text-slate-50 font-medium">{artist.artist}</span>
            </div>
            {getTrendIcon(artist.trend_direction)}
          </div>
          <div className="text-xs text-slate-400 space-y-1">
            <div>
              <span>Velocity: </span>
              <span className="text-slate-200">
                {Math.round(artist.velocity)} views/day
              </span>
            </div>
            <div>
              <span>Total: </span>
              <span className="text-slate-200">
                {artist.total_views.toLocaleString()} views
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
