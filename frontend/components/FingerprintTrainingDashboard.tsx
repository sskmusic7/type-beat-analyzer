'use client'

import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '@/lib/api'
import { 
  Database, 
  Music, 
  Users, 
  CheckCircle2, 
  Loader2, 
  TrendingUp,
  Search,
  Filter
} from 'lucide-react'

interface FingerprintStats {
  total_fingerprints: number
  artists: number
  artist_list: string[]
}

interface Fingerprint {
  id: number
  artist: string
  title: string
  audio_hash: string
  upload_date: string | null
  uploader_id: string | null
}

export default function FingerprintTrainingDashboard() {
  const [stats, setStats] = useState<FingerprintStats | null>(null)
  const [fingerprints, setFingerprints] = useState<Fingerprint[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterArtist, setFilterArtist] = useState<string>('all')
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchStats = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/stats`)
      if (!response.ok) throw new Error('Failed to fetch stats')
      const data = await response.json()
      setStats(data)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const fetchFingerprints = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/list`)
      if (!response.ok) throw new Error('Failed to fetch fingerprints')
      const data = await response.json()
      setFingerprints(data.fingerprints || [])
    } catch (error) {
      console.error('Error fetching fingerprints:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchFingerprints()
    // Auto-refresh every 5 seconds
    const interval = setInterval(() => {
      fetchStats()
      fetchFingerprints()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  // Filter fingerprints
  const filteredFingerprints = fingerprints.filter(fp => {
    const matchesSearch = 
      fp.artist.toLowerCase().includes(searchTerm.toLowerCase()) ||
      fp.title.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesArtist = filterArtist === 'all' || fp.artist === filterArtist
    return matchesSearch && matchesArtist
  })

  // Group by artist for stats
  const artistCounts = fingerprints.reduce((acc, fp) => {
    acc[fp.artist] = (acc[fp.artist] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const sortedArtists = Object.entries(artistCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 10) // Top 10 artists

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    )
  }

  return (
    <div className="w-full bg-gradient-to-br from-slate-900/50 to-slate-950/50 rounded-xl p-6 border border-slate-800/50 backdrop-blur-sm">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-1">
            Fingerprint Training Dashboard
          </h2>
          <p className="text-sm text-slate-400">
            Real-time tracking of trained fingerprints and artists
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-400">Last updated</div>
          <div className="text-sm text-cyan-400 font-mono">
            {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="flex items-center gap-3 mb-2">
            <Database className="w-5 h-5 text-purple-400" />
            <div className="text-sm text-slate-400">Total Fingerprints</div>
          </div>
          <div className="text-3xl font-bold text-white">
            {stats?.total_fingerprints || 0}
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <div className="text-sm text-slate-400">Unique Artists</div>
          </div>
          <div className="text-3xl font-bold text-white">
            {stats?.artists || 0}
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="flex items-center gap-3 mb-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div className="text-sm text-slate-400">Database Status</div>
          </div>
          <div className="text-lg font-semibold text-green-400">
            {stats && stats.total_fingerprints > 0 ? 'Active' : 'Empty'}
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search fingerprints by artist or title..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
          <select
            value={filterArtist}
            onChange={(e) => setFilterArtist(e.target.value)}
            className="pl-10 pr-8 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-purple-500 appearance-none"
          >
            <option value="all">All Artists</option>
            {stats?.artist_list.map(artist => (
              <option key={artist} value={artist}>{artist}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Top Artists */}
      {sortedArtists.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">Top Artists by Fingerprint Count</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {sortedArtists.map(([artist, count]) => (
              <div
                key={artist}
                className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50 hover:border-purple-500/50 transition-colors cursor-pointer"
                onClick={() => setFilterArtist(artist)}
              >
                <div className="text-sm text-slate-400 truncate mb-1">{artist}</div>
                <div className="text-xl font-bold text-white">{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fingerprints List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            All Trained Fingerprints ({filteredFingerprints.length})
          </h3>
          <div className="text-sm text-slate-400">
            Showing {filteredFingerprints.length} of {fingerprints.length}
          </div>
        </div>

        <div className="max-h-[500px] overflow-y-auto custom-scrollbar space-y-2">
          {filteredFingerprints.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              {fingerprints.length === 0 ? (
                <>
                  <Music className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                  <p>No fingerprints trained yet</p>
                  <p className="text-sm mt-2">Start training to see fingerprints here</p>
                </>
              ) : (
                <>
                  <Search className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                  <p>No fingerprints match your search</p>
                </>
              )}
            </div>
          ) : (
            filteredFingerprints.map((fp) => (
              <div
                key={fp.id}
                className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50 hover:border-purple-500/50 transition-all"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Music className="w-4 h-4 text-purple-400 flex-shrink-0" />
                      <span className="text-sm font-medium text-white truncate">
                        {fp.title}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 ml-6">
                      Artist: <span className="text-cyan-400">{fp.artist}</span>
                    </div>
                    {fp.upload_date && (
                      <div className="text-xs text-slate-500 ml-6 mt-1">
                        Trained: {new Date(fp.upload_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
