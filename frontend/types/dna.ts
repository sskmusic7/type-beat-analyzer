export interface BlendArtist {
  artist: string
  similarity: number
  bpm_diff: number
  key_match: boolean
}

export interface BlendResult {
  success: boolean
  artists: BlendArtist[]
  beat_profile: {
    bpm: number | null
    key: string | null
    top_tags: string[]
  }
}

export interface DNAArtist {
  artist: string
  track_count: number
  bpm_mean: number | null
  top_key: string | null
}

export interface SimilarityEntry {
  artist_a: string
  artist_b: string
  similarity: number
}

export interface SimilarityMatrix {
  artists: string[]
  matrix: number[][]
  pairs: SimilarityEntry[]
}
