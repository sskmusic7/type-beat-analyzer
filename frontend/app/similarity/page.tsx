'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Dna, Loader2 } from 'lucide-react'
import { getApiBaseUrl } from '@/lib/api'
import { SimilarityMatrix } from '@/types/dna'

export default function SimilarityPage() {
  const [data, setData] = useState<SimilarityMatrix | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number } | null>(null)

  useEffect(() => {
    fetch(`${getApiBaseUrl()}/dna/similarity-matrix`)
      .then(r => r.json())
      .then(d => {
        setData(d)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Header */}
      <div className="border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/blend"
              className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Blend
            </Link>
            <div className="flex items-center gap-2">
              <Dna className="w-5 h-5 text-purple-400" />
              <h1 className="text-xl font-bold text-slate-50 font-display">
                Artist Similarity Matrix
              </h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-900/30 border border-red-500/50 rounded-lg">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {data && data.artists.length < 2 && (
          <div className="text-center py-20">
            <p className="text-slate-400">
              Need at least 2 artist DNA profiles to show similarity.
              Currently have {data.artists.length}.
            </p>
          </div>
        )}

        {data && data.artists.length >= 2 && (
          <div className="space-y-10">
            {/* Heatmap */}
            <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 overflow-x-auto">
              <h2 className="text-lg font-semibold text-slate-50 font-display mb-6">
                Cosine Similarity Heatmap
              </h2>
              <div className="inline-block">
                <table className="border-collapse">
                  <thead>
                    <tr>
                      <th className="w-28" />
                      {data.artists.map((artist, j) => (
                        <th
                          key={j}
                          className="text-xs text-slate-400 font-normal px-1 pb-2 w-14"
                          style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', height: '100px' }}
                        >
                          {artist}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.artists.map((artist, i) => (
                      <tr key={i}>
                        <td className="text-xs text-slate-300 pr-3 text-right whitespace-nowrap font-medium">
                          {artist}
                        </td>
                        {data.matrix[i].map((sim, j) => {
                          const isHovered =
                            hoveredCell?.row === i || hoveredCell?.col === j
                          const isSelf = i === j
                          return (
                            <td
                              key={j}
                              className={`w-14 h-10 text-center text-[10px] font-mono cursor-default transition-opacity ${
                                hoveredCell && !isHovered ? 'opacity-40' : ''
                              }`}
                              style={{
                                backgroundColor: isSelf
                                  ? 'transparent'
                                  : simColor(sim),
                                borderRadius: '2px',
                              }}
                              onMouseEnter={() => setHoveredCell({ row: i, col: j })}
                              onMouseLeave={() => setHoveredCell(null)}
                              title={`${artist} vs ${data.artists[j]}: ${Math.round(sim * 100)}%`}
                            >
                              {isSelf ? (
                                <span className="text-slate-600">-</span>
                              ) : (
                                <span className="text-slate-100 drop-shadow-sm">
                                  {Math.round(sim * 100)}
                                </span>
                              )}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {/* Legend */}
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
                  <span>Low</span>
                  <div className="flex h-3">
                    {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map(v => (
                      <div
                        key={v}
                        className="w-8 h-3"
                        style={{ backgroundColor: simColor(v) }}
                      />
                    ))}
                  </div>
                  <span>High</span>
                </div>
              </div>
            </div>

            {/* Top Pairs */}
            <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
              <h2 className="text-lg font-semibold text-slate-50 font-display mb-4">
                Most Similar Pairs
              </h2>
              <div className="space-y-2">
                {data.pairs.slice(0, 10).map((pair, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between px-4 py-3 bg-slate-800/40 rounded-lg border border-slate-700/30"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500 w-5">#{i + 1}</span>
                      <span className="text-slate-50 font-medium">{pair.artist_a}</span>
                      <span className="text-slate-500">&harr;</span>
                      <span className="text-slate-50 font-medium">{pair.artist_b}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-24 bg-slate-700/50 rounded-full h-2 overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${pair.similarity * 100}%`,
                            backgroundColor: simColor(pair.similarity),
                          }}
                        />
                      </div>
                      <span className="text-slate-200 font-mono text-sm w-12 text-right">
                        {Math.round(pair.similarity * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}

/** Map similarity [0,1] to a color from blue (low) → purple → hot pink (high) */
function simColor(sim: number): string {
  // Clamp
  const s = Math.max(0, Math.min(1, sim))
  if (s < 0.5) {
    // Blue → Purple
    const t = s / 0.5
    const r = Math.round(30 + t * 100)
    const g = Math.round(40 + t * 20)
    const b = Math.round(100 + t * 80)
    return `rgb(${r}, ${g}, ${b})`
  } else {
    // Purple → Hot pink
    const t = (s - 0.5) / 0.5
    const r = Math.round(130 + t * 125)
    const g = Math.round(60 - t * 30)
    const b = Math.round(180 - t * 40)
    return `rgb(${r}, ${g}, ${b})`
  }
}
