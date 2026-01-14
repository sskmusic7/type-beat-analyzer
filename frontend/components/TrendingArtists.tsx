'use client'

import { useEffect, useState } from 'react'
import { TrendingArtist } from '@/types'
import axios from 'axios'
import { TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react'

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
          'http://localhost:8000/api/trending?limit=10'
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
        return <TrendingUp className="w-4 h-4 text-green-400" />
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-400" />
      default:
        return <Minus className="w-4 h-4 text-gray-400" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (artists.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-4">
        No trending data available
      </p>
    )
  }

  return (
    <div className="space-y-3">
      {artists.map((artist, index) => (
        <div
          key={index}
          className="bg-white/5 rounded-lg p-4 border border-white/10 hover:border-primary-500/50 transition-all"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-primary-500 font-bold text-lg">
                #{artist.rank}
              </span>
              <span className="text-white font-medium">{artist.artist}</span>
            </div>
            {getTrendIcon(artist.trend_direction)}
          </div>
          <div className="text-xs text-gray-400 space-y-1">
            <div>
              <span>Velocity: </span>
              <span className="text-white">
                {Math.round(artist.velocity)} views/day
              </span>
            </div>
            <div>
              <span>Total: </span>
              <span className="text-white">
                {artist.total_views.toLocaleString()} views
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
