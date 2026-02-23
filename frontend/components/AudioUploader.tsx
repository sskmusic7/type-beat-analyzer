'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Loader2 } from 'lucide-react'
import axios from 'axios'
import { AnalysisResult } from '@/types'
import { getApiBaseUrl } from '@/lib/api'

interface AudioUploaderProps {
  onAnalysisComplete: (result: AnalysisResult) => void
  loading: boolean
  setLoading: (loading: boolean) => void
}

export default function AudioUploader({
  onAnalysisComplete,
  loading,
  setLoading,
}: AudioUploaderProps) {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      setError(null)
      setLoading(true)

      try {
        const formData = new FormData()
        formData.append('file', file)

        const response = await axios.post<AnalysisResult>(
          `${getApiBaseUrl()}/api/analyze`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        )

        onAnalysisComplete(response.data)
      } catch (err: any) {
        setError(
          err.response?.data?.detail || 'Failed to analyze audio. Please try again.'
        )
      } finally {
        setLoading(false)
      }
    },
    [onAnalysisComplete, setLoading]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.ogg'],
    },
    maxFiles: 1,
    disabled: loading,
  })

  return (
    <div>
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${
            isDragActive
              ? 'border-purple-500 bg-purple-500/20 shadow-glow-purple'
              : 'border-slate-600 hover:border-purple-500/50 hover:bg-slate-800/50'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        {loading ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
            <p className="text-slate-200">Analyzing your beat...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <Upload className={`w-12 h-12 ${isDragActive ? 'text-purple-400' : 'text-slate-400'}`} />
            <div>
              <p className="text-slate-50 text-lg font-medium">
                {isDragActive
                  ? 'Drop your beat here'
                  : 'Drag & drop your beat here'}
              </p>
              <p className="text-slate-400 text-sm mt-2">
                or click to browse (MP3, WAV, M4A, FLAC, OGG)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-900/30 border border-red-500/50 rounded-lg backdrop-blur-sm">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}
    </div>
  )
}
