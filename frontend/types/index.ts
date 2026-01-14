export interface ArtistMatch {
  artist: string
  confidence: number
  trending?: TrendingData
}

export interface TrendingData {
  rank?: number
  velocity: number
  total_views: number
  upload_date?: string
  engagement_rate?: number
  trend_direction: 'up' | 'down' | 'stable'
}

export interface AnalysisResult {
  matches: ArtistMatch[]
  processing_time_ms: number
}

export interface TrendingArtist {
  artist: string
  rank: number
  velocity: number
  total_views: number
  trend_direction: 'up' | 'down' | 'stable'
}
