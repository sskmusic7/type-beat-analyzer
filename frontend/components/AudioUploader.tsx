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
              ? 'border-primary-500 bg-primary-500/10'
              : 'border-gray-400 hover:border-primary-500 hover:bg-white/5'
          }
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        {loading ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
            <p className="text-white">Analyzing your beat...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <Upload className="w-12 h-12 text-gray-400" />
            <div>
              <p className="text-white text-lg font-medium">
                {isDragActive
                  ? 'Drop your beat here'
                  : 'Drag & drop your beat here'}
              </p>
              <p className="text-gray-400 text-sm mt-2">
                or click to browse (MP3, WAV, M4A, FLAC, OGG)
              </p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-500/20 border border-red-500 rounded-lg">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}
    </div>
  )
}
