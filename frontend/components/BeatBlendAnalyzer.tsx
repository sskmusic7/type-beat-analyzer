'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Loader2, Music, Zap, Key, Tag, ChevronDown } from 'lucide-react'
import axios from 'axios'
import { getApiBaseUrl } from '@/lib/api'
import { BlendResult, DNAArtist } from '@/types/dna'

export default function BeatBlendAnalyzer() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BlendResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setError(null)
    setLoading(true)
    setFileName(file.name)
    setResult(null)

    try {
      // First, upload the file to a temp location via the analyze endpoint
      // The blend endpoint needs a file path, so we use a two-step process:
      // 1. Upload file to server temp dir
      // 2. Call blend with the temp path
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post<BlendResult>(
        `${getApiBaseUrl()}/dna/blend-upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 120000, // DNA analysis can take a while
        }
      )

      setResult(response.data)
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Blend analysis failed. Make sure artist profiles are trained.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg'] },
    maxFiles: 1,
    disabled: loading,
  })

  return (
    <div className="space-y-8">
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragActive
            ? 'border-cyan-500 bg-cyan-500/10 shadow-glow-cyan'
            : 'border-slate-600 hover:border-cyan-500/50 hover:bg-slate-800/50'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        {loading ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
            <div>
              <p className="text-slate-200">Analyzing DNA blend...</p>
              <p className="text-slate-400 text-sm mt-1">
                Running CLAP scoring + feature extraction on {fileName}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <Music className={`w-12 h-12 ${isDragActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              <Zap className="w-5 h-5 text-purple-400 absolute -top-1 -right-1" />
            </div>
            <div>
              <p className="text-slate-50 text-lg font-medium">
                {isDragActive ? 'Drop your beat here' : 'Drop a beat to analyze its DNA'}
              </p>
              <p className="text-slate-400 text-sm mt-2">
                Find out which artists your production sounds like
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-900/30 border border-red-500/50 rounded-lg backdrop-blur-sm">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Results */}
      {result && <BlendResults result={result} fileName={fileName} />}
    </div>
  )
}

function BlendResults({ result, fileName }: { result: BlendResult; fileName: string | null }) {
  const [expanded, setExpanded] = useState(false)
  const bp = result.beat_profile

  // Calculate max similarity for scale
  const maxSim = result.artists.length > 0
    ? Math.max(...result.artists.map(a => a.similarity))
    : 1

  return (
    <div className="space-y-6">
      {/* Beat Profile Card */}
      <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-slate-50 mb-4 font-display">
          Beat Profile
          {fileName && (
            <span className="text-sm font-normal text-slate-400 ml-2">
              {fileName}
            </span>
          )}
        </h3>
        <div className="grid grid-cols-3 gap-4">
          {/* BPM */}
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Zap className="w-3.5 h-3.5" />
              BPM
            </div>
            <p className="text-2xl font-bold text-slate-50">
              {bp.bpm ? Math.round(bp.bpm) : '--'}
            </p>
          </div>
          {/* Key */}
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Key className="w-3.5 h-3.5" />
              Key
            </div>
            <p className="text-2xl font-bold text-slate-50">
              {bp.key || '--'}
            </p>
          </div>
          {/* Tags */}
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/30">
            <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
              <Tag className="w-3.5 h-3.5" />
              Vibe
            </div>
            <p className="text-sm font-medium text-slate-50 leading-tight">
              {bp.top_tags.length > 0 ? bp.top_tags.slice(0, 2).join(', ') : '--'}
            </p>
          </div>
        </div>
        {bp.top_tags.length > 2 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {bp.top_tags.slice(2).map((tag) => (
              <span
                key={tag}
                className="px-2.5 py-1 text-xs rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Artist Blend Breakdown */}
      <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
        <h3 className="text-lg font-semibold text-slate-50 mb-4 font-display">
          Artist DNA Blend
        </h3>
        {result.artists.length === 0 ? (
          <p className="text-slate-400 text-sm">
            No artist profiles available for comparison. Train artist DNA profiles first.
          </p>
        ) : (
          <div className="space-y-3">
            {result.artists.map((artist, i) => {
              const pct = Math.round(artist.similarity * 100)
              const barWidth = (artist.similarity / maxSim) * 100
              return (
                <div key={artist.artist} className="group">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500 w-5">#{i + 1}</span>
                      <span className="text-slate-50 font-medium">{artist.artist}</span>
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
                  <div className="w-full bg-slate-700/50 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700 ease-out"
                      style={{
                        width: `${barWidth}%`,
                        background: i === 0
                          ? 'linear-gradient(to right, #a855f7, #06b6d4)'
                          : i === 1
                          ? 'linear-gradient(to right, #8b5cf6, #6366f1)'
                          : 'linear-gradient(to right, #64748b, #475569)',
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Pie-style visual */}
      {result.artists.length > 0 && (
        <div className="bg-slate-900/60 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center justify-between w-full text-left"
          >
            <h3 className="text-lg font-semibold text-slate-50 font-display">
              Blend Visualization
            </h3>
            <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </button>
          {expanded && (
            <div className="mt-4">
              <BlendPieChart artists={result.artists} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function BlendPieChart({ artists }: { artists: BlendResult['artists'] }) {
  // Simple CSS-based pie chart using conic-gradient
  const colors = ['#a855f7', '#06b6d4', '#8b5cf6', '#f59e0b', '#10b981']
  const total = artists.reduce((sum, a) => sum + a.similarity, 0)

  let cumulative = 0
  const segments = artists.map((artist, i) => {
    const start = cumulative
    const pct = (artist.similarity / total) * 100
    cumulative += pct
    return { artist: artist.artist, pct, start, end: cumulative, color: colors[i % colors.length] }
  })

  const gradient = segments
    .map(s => `${s.color} ${s.start}% ${s.end}%`)
    .join(', ')

  return (
    <div className="flex items-center gap-8 justify-center">
      <div
        className="w-40 h-40 rounded-full border-2 border-slate-700/50"
        style={{
          background: `conic-gradient(${gradient})`,
        }}
      />
      <div className="space-y-2">
        {segments.map((s) => (
          <div key={s.artist} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: s.color }} />
            <span className="text-slate-300 text-sm">
              {s.artist} — {Math.round(s.pct)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
