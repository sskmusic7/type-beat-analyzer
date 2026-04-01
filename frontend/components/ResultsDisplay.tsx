'use client'

import { AnalysisResult } from '@/types'
import { BlendResult } from '@/types/dna'
import { TrendingUp, TrendingDown, Minus, Zap, Key, Tag } from 'lucide-react'

interface ResultsDisplayProps {
  result: AnalysisResult
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
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

  // Handle empty results
  if (result.matches.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-800/50 mb-4">
          <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-slate-50 mb-2">No Matches Found</h3>
        <p className="text-slate-400 max-w-md mx-auto">
          This beat doesn't match any artists in our database yet. The track was analyzed successfully, but no similar styles were found.
        </p>
        {result.processing_time_ms > 0 && (
          <p className="text-xs text-slate-500 mt-4">
            Processed in {result.processing_time_ms.toFixed(0)}ms
          </p>
        )}
      </div>
    )
  }

  return (
    <div>
      <div className="space-y-4">
        {result.matches.map((match, index) => (
          <div
            key={index}
            className="bg-slate-800/50 rounded-lg p-6 border border-slate-700/50 hover:border-purple-500/50 transition-all backdrop-blur-sm"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-slate-50 mb-1">
                  {match.artist}
                </h3>
                <div className="flex items-center gap-2 text-sm text-slate-400">
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
              <div className="w-full bg-slate-700/50 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-purple-500 to-cyan-400 transition-all duration-500"
                  style={{ width: `${match.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Trending Data */}
            {match.trending && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                {match.trending.rank && (
                  <div>
                    <span className="text-slate-400">Rank:</span>
                    <span className="text-slate-50 ml-2 font-medium">
                      #{match.trending.rank}
                    </span>
                  </div>
                )}
                <div>
                  <span className="text-slate-400">Velocity:</span>
                  <span className="text-slate-50 ml-2 font-medium">
                    {Math.round(match.trending.velocity)} views/day
                  </span>
                </div>
                {match.trending.total_views > 0 && (
                  <div className="col-span-2">
                    <span className="text-slate-400">Total Views:</span>
                    <span className="text-slate-50 ml-2 font-medium">
                      {match.trending.total_views.toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* DNA Blend Section */}
      {result.dnaBlend && <DnaBlendSection blend={result.dnaBlend} />}

      {result.processing_time_ms > 0 && (
        <p className="text-xs text-slate-500 mt-4 text-right">
          Processed in {result.processing_time_ms.toFixed(0)}ms
        </p>
      )}
    </div>
  )
}

function DnaBlendSection({ blend }: { blend: BlendResult }) {
  const bp = blend.beat_profile
  const maxSim = blend.artists.length > 0
    ? Math.max(...blend.artists.map(a => a.similarity))
    : 1

  return (
    <div className="mt-8 space-y-6">
      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
        <span className="text-xs font-semibold text-cyan-400 tracking-widest uppercase">DNA Blend</span>
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
      </div>

      {/* Beat Profile */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Zap className="w-3.5 h-3.5" /> BPM
          </div>
          <p className="text-2xl font-bold text-slate-50">
            {bp.bpm ? Math.round(bp.bpm) : '--'}
          </p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Key className="w-3.5 h-3.5" /> Key
          </div>
          <p className="text-2xl font-bold text-slate-50">
            {bp.key || '--'}
          </p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Tag className="w-3.5 h-3.5" /> Vibe
          </div>
          <p className="text-sm font-medium text-slate-50 leading-tight">
            {bp.top_tags.length > 0 ? bp.top_tags.slice(0, 3).join(', ') : '--'}
          </p>
        </div>
      </div>

      {/* CLAP Tags */}
      {bp.top_tags.length > 3 && (
        <div className="flex flex-wrap gap-2">
          {bp.top_tags.slice(3).map(tag => (
            <span
              key={tag}
              className="px-2.5 py-1 text-xs rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/25"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Artist DNA Blend Bars */}
      {blend.artists.length > 0 ? (
        <div className="space-y-3">
          {blend.artists.map((artist, i) => {
            const pct = Math.round(artist.similarity * 100)
            const barWidth = (artist.similarity / maxSim) * 100
            return (
              <div key={artist.artist}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 w-5">#{i + 1}</span>
                    <span className="text-slate-50 font-medium text-sm">{artist.artist}</span>
                    {artist.key_match && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        Key Match
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    {artist.bpm_diff !== undefined && (
                      <span className="text-slate-400 text-xs">
                        {artist.bpm_diff > 0 ? '+' : ''}{Math.round(artist.bpm_diff)} BPM
                      </span>
                    )}
                    <span className="text-slate-50 font-semibold tabular-nums w-12 text-right">
                      {pct}%
                    </span>
                  </div>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                      width: `${barWidth}%`,
                      background: i === 0
                        ? 'linear-gradient(to right, #06b6d4, #a855f7)'
                        : i === 1
                        ? 'linear-gradient(to right, #6366f1, #8b5cf6)'
                        : 'linear-gradient(to right, #475569, #64748b)',
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-slate-400 text-sm text-center py-4">
          No artist DNA profiles available for comparison yet.
        </p>
      )}
    </div>
  )
}
