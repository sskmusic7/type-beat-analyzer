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
  Filter,
  Play,
  Square,
  AlertCircle
} from 'lucide-react'
import type { TrendingArtist } from '@/types'

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

interface TrainingStatus {
  status: 'idle' | 'running' | 'completed' | 'failed' | 'stopping'
  progress: number
  current_artist: string | null
  artists_processed: number
  total_artists: number
  fingerprints_generated: number
  started_at: string | null
  completed_at: string | null
  error: string | null
  logs: string[]
}

export default function FingerprintTrainingDashboard() {
  const [stats, setStats] = useState<FingerprintStats | null>(null)
  const [fingerprints, setFingerprints] = useState<Fingerprint[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterArtist, setFilterArtist] = useState<string>('all')
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null)
  const [isStartingTraining, setIsStartingTraining] = useState(false)
  const [showTrainingPanel, setShowTrainingPanel] = useState(false)
  const [artistBatchInput, setArtistBatchInput] = useState('')
  const [trendingArtists, setTrendingArtists] = useState<TrendingArtist[]>([])
  const [trendingLoading, setTrendingLoading] = useState(false)

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
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', errorText)
        throw new Error(`Failed to fetch fingerprints: ${response.status}`)
      }
      const data = await response.json()
      console.log('Fetched fingerprints:', data) // Debug log
      setFingerprints(data.fingerprints || [])
    } catch (error) {
      console.error('Error fetching fingerprints:', error)
      // Set empty array on error so UI shows "no fingerprints" instead of loading forever
      setFingerprints([])
    } finally {
      setLoading(false)
    }
  }

  const fetchTrainingStatus = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/train/status`)
      if (!response.ok) throw new Error('Failed to fetch training status')
      const data = await response.json()
      setTrainingStatus(data)
      
      // Auto-show panel if training is running
      if (data.status === 'running' || data.status === 'stopping') {
        setShowTrainingPanel(true)
      }
    } catch (error) {
      console.error('Error fetching training status:', error)
    }
  }

  const fetchTrendingArtists = async () => {
    setTrendingLoading(true)
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/trending?limit=10`)
      if (!response.ok) throw new Error('Failed to fetch trending artists')
      const data = await response.json()
      setTrendingArtists(data || [])
    } catch (error) {
      console.error('Error fetching trending artists:', error)
      setTrendingArtists([])
    } finally {
      setTrendingLoading(false)
    }
  }

  const startTraining = async (
    clearExisting: boolean = true,
    maxPerArtist: number = 5,
    artistText?: string
  ) => {
    setIsStartingTraining(true)
    try {
      const formData = new FormData()
      formData.append('clear_existing', clearExisting.toString())
      formData.append('max_per_artist', maxPerArtist.toString())

      const text = (artistText ?? artistBatchInput).trim()
      if (text.length > 0) {
        // Backend will split on commas/newlines
        formData.append('artists', text)
      }
      
      const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/train/start`, {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to start training')
      }
      
      const data = await response.json()
      setTrainingStatus(data.status)
      setShowTrainingPanel(true)
      
      // Refresh stats immediately
      await fetchStats()
      await fetchTrainingStatus()
    } catch (error: any) {
      alert(`Error starting training: ${error.message}`)
      console.error('Error starting training:', error)
    } finally {
      setIsStartingTraining(false)
    }
  }

  const stopTraining = async () => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/train/stop`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to stop training')
      }
      
      await fetchTrainingStatus()
    } catch (error: any) {
      alert(`Error stopping training: ${error.message}`)
      console.error('Error stopping training:', error)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchFingerprints()
    fetchTrainingStatus()
    fetchTrendingArtists()
    
    // Auto-refresh every 2 seconds for real-time progress
    const interval = setInterval(() => {
      fetchStats()
      fetchFingerprints()
      fetchTrainingStatus()
    }, 2000)
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
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowTrainingPanel(!showTrainingPanel)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              showTrainingPanel || trainingStatus?.status === 'running'
                ? 'bg-purple-600 text-white hover:bg-purple-700'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
            }`}
          >
            {showTrainingPanel ? 'Hide' : 'Show'} Training Controls
          </button>
          <div className="text-right">
            <div className="text-sm text-slate-400">Last updated</div>
            <div className="text-sm text-cyan-400 font-mono">
              {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* Training Control Panel */}
      {(showTrainingPanel || trainingStatus?.status === 'running') && (
        <div className="mb-6 bg-gradient-to-br from-purple-900/20 to-cyan-900/20 rounded-xl p-6 border border-purple-500/30">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Music className="w-5 h-5 text-purple-400" />
              Training Control
            </h3>
            {trainingStatus?.status === 'running' && (
              <div className="flex items-center gap-2 text-cyan-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm font-medium">Training in progress...</span>
              </div>
            )}
          </div>

          {/* Training Status */}
          {trainingStatus && trainingStatus.status !== 'idle' && (
            <div className="mb-4 space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">Status:</span>
                <span className={`font-semibold ${
                  trainingStatus.status === 'running' ? 'text-cyan-400' :
                  trainingStatus.status === 'completed' ? 'text-green-400' :
                  trainingStatus.status === 'failed' ? 'text-red-400' :
                  'text-yellow-400'
                }`}>
                  {trainingStatus.status.toUpperCase()}
                </span>
              </div>

              {trainingStatus.status === 'running' && (
                <>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Progress:</span>
                      <span className="text-white font-medium">
                        {trainingStatus.artists_processed} / {trainingStatus.total_artists} artists
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2.5">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-cyan-500 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${trainingStatus.progress}%` }}
                      />
                    </div>
                  </div>

                  {trainingStatus.current_artist && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Current Artist:</span>
                      <span className="text-cyan-400 font-medium">{trainingStatus.current_artist}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">Fingerprints Generated:</span>
                    <span className="text-green-400 font-medium">
                      {trainingStatus.fingerprints_generated}
                    </span>
                  </div>
                </>
              )}

              {trainingStatus.status === 'completed' && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">Training completed successfully!</span>
                  </div>
                  <div className="text-sm text-slate-400 mt-2">
                    Generated {trainingStatus.fingerprints_generated} fingerprints from {trainingStatus.artists_processed} artists
                  </div>
                </div>
              )}

              {trainingStatus.status === 'failed' && trainingStatus.error && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-red-400">
                    <AlertCircle className="w-5 h-5" />
                    <span className="font-medium">Training failed</span>
                  </div>
                  <div className="text-sm text-slate-400 mt-2">{trainingStatus.error}</div>
                </div>
              )}

              {/* Training Logs */}
              {trainingStatus.logs && trainingStatus.logs.length > 0 && (
                <div className="mt-4">
                  <div className="text-sm text-slate-400 mb-2">Recent Logs:</div>
                  <div className="bg-slate-900/50 rounded-lg p-3 max-h-32 overflow-y-auto custom-scrollbar">
                    <div className="space-y-1 text-xs font-mono text-slate-300">
                      {trainingStatus.logs.slice(-10).map((log, idx) => (
                        <div key={idx}>{log}</div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Artist Batch Input */}
          <div className="mb-4 grid grid-cols-1 lg:grid-cols-[2fr,3fr] gap-4">
            {/* Left: Artist batch input */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Artist batch (one per line or comma-separated)
              </label>
              <textarea
                value={artistBatchInput}
                onChange={(e) => setArtistBatchInput(e.target.value)}
                rows={4}
                placeholder="e.g.\nTaylor Swift\nBurna Boy\nRAYE\nMahalia\nAriana Grande"
                className="w-full px-3 py-2 bg-slate-900/60 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
              />
              <p className="mt-2 text-xs text-slate-400">
                This will <span className="text-green-400 font-semibold">add fingerprints</span> for these artists on top of your existing database.
                It does <span className="text-red-400 font-semibold">not delete</span> existing fingerprints.
              </p>
            </div>
            {/* Right: Trending type-beat artists with quick-add */}
            <div className="text-xs text-slate-400 space-y-2">
              <div className="flex items-center justify-between">
                <p className="font-semibold text-slate-200 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-cyan-400" />
                  YouTube “type beat” trending artists
                </p>
                <button
                  onClick={fetchTrendingArtists}
                  className="px-2 py-1 text-[11px] border border-slate-600 rounded-md text-slate-300 hover:bg-slate-800"
                >
                  Refresh
                </button>
              </div>
              <p>
                This panel looks at YouTube for queries like
                <span className="text-slate-200 font-mono"> “artist name type beat” </span>
                and ranks artists by type‑beat velocity (views / day).
                Click an artist to add them to the training batch.
              </p>

              <div className="mt-2 max-h-40 overflow-y-auto custom-scrollbar space-y-1">
                {trendingLoading ? (
                  <div className="flex items-center gap-2 text-slate-400">
                    <Loader2 className="w-3 h-3 animate-spin text-cyan-400" />
                    <span>Loading trending artists…</span>
                  </div>
                ) : trendingArtists.length === 0 ? (
                  <div className="text-slate-500">
                    No trending type-beat data available right now.
                  </div>
                ) : (
                  trendingArtists.map((artist) => (
                    <button
                      key={artist.artist}
                      type="button"
                      onClick={() => {
                        const current = artistBatchInput.split(/[\n,]/).map(a => a.trim()).filter(Boolean)
                        if (!current.includes(artist.artist)) {
                          setArtistBatchInput(
                            (current.concat(artist.artist)).join('\n')
                          )
                        }
                      }}
                      className="w-full flex items-center justify-between px-2 py-1 rounded-md hover:bg-slate-900 text-left"
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-purple-400 font-semibold text-[11px]">
                          #{artist.rank}
                        </span>
                        <span className="text-slate-100 text-xs">
                          {artist.artist}
                        </span>
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {Math.round(artist.velocity).toLocaleString()} views/day
                      </span>
                    </button>
                  ))
                )}
              </div>

              <p className="pt-1">
                Leave the box empty to use the legacy full‑dataset training list
                (only recommended with the full regenerate option below).
              </p>
            </div>
          </div>

          {/* Training Controls */}
          <div className="flex flex-col md:flex-row items-start md:items-center gap-3 md:gap-4">
            {trainingStatus?.status === 'running' || trainingStatus?.status === 'stopping' ? (
              <button
                onClick={stopTraining}
                disabled={trainingStatus.status === 'stopping'}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Square className="w-4 h-4" />
                Stop Training
              </button>
            ) : (
              <>
                <button
                  onClick={() => startTraining(false, 5)}
                  disabled={isStartingTraining}
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-700 hover:to-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isStartingTraining ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Start Training (Add Artists Only)
                    </>
                  )}
                </button>

                <button
                  onClick={() => {
                    const confirmed = window.confirm(
                      'This will CLEAR all existing fingerprints and fully regenerate the database using the main training list. Are you sure?'
                    )
                    if (confirmed) {
                      startTraining(true, 5, '')
                    }
                  }}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-900 border border-red-500/60 text-red-300 rounded-lg text-xs md:text-sm hover:bg-red-950/40 transition-colors"
                >
                  <AlertCircle className="w-4 h-4" />
                  Full Regenerate (Danger)
                </button>
              </>
            )}

            <div className="text-xs text-slate-400 md:ml-auto">
              Downloads from YouTube, generates comprehensive fingerprints, deletes audio immediately
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700/50">
          <div className="flex items-center gap-3 mb-2">
            <Database className="w-5 h-5 text-purple-400" />
            <div className="text-sm text-slate-400">Total Fingerprints</div>
            {loading && <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />}
          </div>
          <div className="text-3xl font-bold text-white">
            {stats?.total_fingerprints || 0}
          </div>
          {stats && stats.total_fingerprints > 0 && (
            <div className="text-xs text-slate-500 mt-1">
              Target: ~370 (74 artists × 5 tracks)
            </div>
          )}
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
