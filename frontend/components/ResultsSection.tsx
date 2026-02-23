'use client'

import { AnalysisResult } from '@/types'
import ResultsDisplay from './ResultsDisplay'

interface ResultsSectionProps {
  result: AnalysisResult | null
}

export default function ResultsSection({ result }: ResultsSectionProps) {
  if (!result) return null

  return (
    <section className="py-24 bg-slate-950 relative overflow-hidden">
      {/* Subtle background accent */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-600 rounded-full blur-3xl"></div>
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-8 shadow-glow-purple">
            <h2 className="font-display text-3xl font-bold text-slate-50 mb-6">
              Analysis Results
            </h2>
            <ResultsDisplay result={result} />
          </div>
        </div>
      </div>
    </section>
  )
}
