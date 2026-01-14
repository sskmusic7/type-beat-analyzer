'use client'

import { AnalysisResult } from '@/types'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface ResultsDisplayProps {
  result: AnalysisResult
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
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

  return (
    <div>
      <h2 className="text-2xl font-semibold text-white mb-6">Analysis Results</h2>

      <div className="space-y-4">
        {result.matches.map((match, index) => (
          <div
            key={index}
            className="bg-white/5 rounded-lg p-6 border border-white/10 hover:border-primary-500/50 transition-all"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white mb-1">
                  {match.artist}
                </h3>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <span>
                    {Math.round(match.confidence * 100)}% match
                  </span>
                  {match.trending && (
                    <>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        {getTrendIcon(match.trending.trend_direction)}
                        {match.trending.trend_direction === 'up' && 'Trending'}
                        {match.trending.trend_direction === 'down' && 'Cooling'}
                        {match.trending.trend_direction === 'stable' && 'Stable'}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Confidence Bar */}
            <div className="mb-4">
              <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500"
                  style={{ width: `${match.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Trending Data */}
            {match.trending && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                {match.trending.rank && (
                  <div>
                    <span className="text-gray-400">Rank:</span>
                    <span className="text-white ml-2 font-medium">
                      #{match.trending.rank}
                    </span>
                  </div>
                )}
                <div>
                  <span className="text-gray-400">Velocity:</span>
                  <span className="text-white ml-2 font-medium">
                    {Math.round(match.trending.velocity)} views/day
                  </span>
                </div>
                {match.trending.total_views > 0 && (
                  <div className="col-span-2">
                    <span className="text-gray-400">Total Views:</span>
                    <span className="text-white ml-2 font-medium">
                      {match.trending.total_views.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {result.processing_time_ms > 0 && (
        <p className="text-xs text-gray-500 mt-4 text-right">
          Processed in {result.processing_time_ms.toFixed(0)}ms
        </p>
      )}
    </div>
  )
}
