'use client'

import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '@/lib/api'
import { Dna, Users, Music, ChevronDown, ChevronUp, Search } from 'lucide-react'

interface ArtistProfile {
  artist: string
  track_count: number
  bpm_mean: number
  top_key: string
  signature_tags: string[]
  has_stems: boolean
}

interface SimilarPair {
  artist_a: string
  artist_b: string
  similarity: number
}

export default function ArtistDNAPanel() {
  const [artists, setArtists] = useState<ArtistProfile[]>([])
  const [topPairs, setTopPairs] = useState<SimilarPair[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch(`${getApiBaseUrl()}/dna/artists`).then(r => r.json()),
      fetch(`${getApiBaseUrl()}/dna/similarity-matrix`).then(r => r.json()),
    ])
      .then(([artistData, simData]) => {
        setArtists(artistData.artists || [])
        setTopPairs(simData.top_pairs || [])
      })
      .catch(err => setError('Failed to load DNA data'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = artists.filter(a =>
    a.artist.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const stemCount = artists.filter(a => a.has_stems).length
  const totalTracks = artists.reduce((sum, a) => sum + a.track_count, 0)

  if (loading) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full mx-auto mb-3" />
        <p className="text-slate-400">Loading DNA profiles...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-xl p-6 text-red-300">
        {error}
      </div>
    )
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      {/* Stats Header */}
      <div className="p-6 border-b border-slate-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-cyan-400">{artists.length}</p>
            <p className="text-xs text-slate-400 mt-1">Artist Profiles</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-purple-400">{totalTracks}</p>
            <p className="text-xs text-slate-400 mt-1">Tracks Analyzed</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{stemCount}</p>
            <p className="text-xs text-slate-400 mt-1">With Stems</p>
          </div>
          <div className="bg-slate-800/50 rounded-lg p-4 text-center">
            <p className="text-2xl font-bold text-amber-400">{topPairs.length}</p>
            <p className="text-xs text-slate-400 mt-1">Similar Pairs</p>
          </div>
        </div>
      </div>

      {/* Top Similar Pairs */}
      {topPairs.length > 0 && (
        <div className="p-6 border-b border-slate-800">
          <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Users className="w-4 h-4 text-purple-400" />
            Most Similar Artists
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {topPairs.slice(0, 6).map((pair, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-800/30 rounded-lg px-3 py-2">
                <span className="text-sm text-slate-300">
                  {pair.artist_a} <span className="text-slate-500">&</span> {pair.artist_b}
                </span>
                <span className="text-xs font-mono text-cyan-400">
                  {(pair.similarity * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Artist List */}
      <div className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search artists..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 px-3 py-2 text-sm text-slate-400 hover:text-slate-200 bg-slate-800 border border-slate-700 rounded-lg"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {expanded ? 'Collapse' : 'Show All'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {(expanded ? filtered : filtered.slice(0, 12)).map(artist => (
            <div
              key={artist.artist}
              className="flex items-center gap-3 bg-slate-800/30 hover:bg-slate-800/50 rounded-lg px-3 py-2 transition-colors"
            >
              <Music className="w-4 h-4 text-slate-500 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-200 truncate">{artist.artist}</p>
                <p className="text-xs text-slate-500">
                  {artist.track_count} tracks &middot; {artist.bpm_mean?.toFixed(0) || '?'} BPM &middot; {artist.top_key || '?'}
                  {artist.has_stems && ' \u00b7 stems'}
                </p>
              </div>
              <div className="flex flex-wrap gap-1">
                {(artist.signature_tags || []).slice(0, 2).map(tag => (
                  <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-cyan-900/30 text-cyan-400 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {!expanded && filtered.length > 12 && (
          <p className="text-center text-xs text-slate-500 mt-3">
            Showing 12 of {filtered.length} &middot; click "Show All" to see more
          </p>
        )}
      </div>
    </div>
  )
}
