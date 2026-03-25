'use client'

import { useState, useEffect } from 'react'
import { getApiBaseUrl } from '@/lib/api'
import { Loader2, Box } from 'lucide-react'
import dynamic from 'next/dynamic'

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

interface VisualizationPoint {
  id: number
  artist: string
  title: string
  x: number
  y: number
  z: number
}

interface VisualizationData {
  points: VisualizationPoint[]
  total: number
}

export default function Fingerprint3DVisualization() {
  const [data, setData] = useState<VisualizationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedArtist, setSelectedArtist] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const response = await fetch(`${getApiBaseUrl()}/api/fingerprint/visualization`)
        if (!response.ok) throw new Error('Failed to fetch visualization data')
        const visualizationData = await response.json()
        setData(visualizationData)
      } catch (err: any) {
        setError(err.message)
        console.error('Error fetching visualization:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 bg-slate-900/50 rounded-xl border border-slate-800/50">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <span className="ml-3 text-slate-400">Generating 3D visualization...</span>
      </div>
    )
  }

  if (error || !data || data.points.length === 0) {
    return (
      <div className="bg-slate-900/50 rounded-xl p-6 border border-slate-800/50 text-center">
        <Box className="w-12 h-12 mx-auto mb-4 text-slate-600" />
        <p className="text-slate-400">
          {error || 'No fingerprint data available for visualization'}
        </p>
      </div>
    )
  }

  // Group points by artist for coloring
  const artists = Array.from(new Set(data.points.map(p => p.artist)))
  const artistColors: Record<string, string> = {}
  const colors = [
    '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
    '#ec4899', '#6366f1', '#14b8a6', '#f97316', '#84cc16'
  ]
  artists.forEach((artist, idx) => {
    artistColors[artist] = colors[idx % colors.length]
  })

  // Prepare data for Plotly
  const traces = artists.map(artist => {
    const artistPoints = data.points.filter(p => p.artist === artist)
    const isSelected = selectedArtist === null || selectedArtist === artist
    
    return {
      x: artistPoints.map(p => p.x),
      y: artistPoints.map(p => p.y),
      z: artistPoints.map(p => p.z),
      mode: 'markers' as const,
      type: 'scatter3d' as const,
      name: artist,
      text: artistPoints.map(p => `${p.artist}<br>${p.title}`),
      hovertemplate: '<b>%{text}</b><extra></extra>',
      marker: {
        size: isSelected ? 8 : 4,
        color: artistColors[artist],
        opacity: isSelected ? 0.8 : 0.3,
        line: {
          color: 'rgba(0,0,0,0.1)',
          width: 1
        }
      }
    }
  })

  const layout = {
    title: {
      text: `3D Fingerprint Visualization (${data.total} fingerprints)`,
      font: { color: '#e2e8f0', size: 18 }
    },
    scene: {
      xaxis: { title: 'X', gridcolor: '#334155', backgroundcolor: '#0f172a' },
      yaxis: { title: 'Y', gridcolor: '#334155', backgroundcolor: '#0f172a' },
      zaxis: { title: 'Z', gridcolor: '#334155', backgroundcolor: '#0f172a' },
      bgcolor: '#0f172a',
      camera: {
        eye: { x: 1.5, y: 1.5, z: 1.5 }
      }
    },
    paper_bgcolor: '#1e293b',
    plot_bgcolor: '#0f172a',
    font: { color: '#cbd5e1' },
    margin: { l: 0, r: 0, t: 50, b: 0 },
    legend: {
      x: 1.05,
      y: 1,
      bgcolor: 'rgba(30, 41, 59, 0.8)',
      bordercolor: '#475569',
      borderwidth: 1
    }
  }

  const config = {
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    responsive: true
  }

  return (
    <div className="w-full bg-gradient-to-br from-slate-900/50 to-slate-950/50 rounded-xl p-6 border border-slate-800/50 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Box className="w-5 h-5 text-purple-400" />
            3D Fingerprint Visualization
          </h3>
          <p className="text-sm text-slate-400 mt-1">
            Interactive 3D scatter plot of all fingerprints, colored by artist
          </p>
        </div>
        <div className="text-sm text-slate-400">
          {data.total} fingerprints
        </div>
      </div>

      {/* Artist filter */}
      <div className="mb-4">
        <select
          value={selectedArtist || 'all'}
          onChange={(e) => setSelectedArtist(e.target.value === 'all' ? null : e.target.value)}
          className="px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Artists</option>
          {artists.map(artist => (
            <option key={artist} value={artist}>{artist}</option>
          ))}
        </select>
      </div>

      {/* 3D Plot */}
      <div className="bg-slate-900/30 rounded-lg p-4 border border-slate-700/50" style={{ height: '600px' }}>
        {typeof window !== 'undefined' && (
          <Plot
            data={traces}
            layout={layout as any}
            config={config as any}
            style={{ width: '100%', height: '100%' }}
          />
        )}
      </div>

      <div className="mt-4 text-xs text-slate-500">
        💡 Click and drag to rotate • Scroll to zoom • Click legend to toggle artists
      </div>
    </div>
  )
}
