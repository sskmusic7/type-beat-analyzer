'use client'

import { AnalysisResult } from '@/types'
import ResultsDisplay from './ResultsDisplay'

interface ResultsSectionProps {
  result: AnalysisResult | null
}

export default function ResultsSection({ result }: ResultsSectionProps) {
  if (!result) return null

  return (
    <section className="py-24 bg-white dark:bg-jacarta-800">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white dark:bg-jacarta-700 rounded-2.5xl border border-jacarta-100 dark:border-jacarta-700 p-8 shadow-lg">
            <h2 className="font-display text-3xl font-bold text-jacarta-700 dark:text-white mb-6">
              Analysis Results
            </h2>
            <ResultsDisplay result={result} />
          </div>
        </div>
      </div>
    </section>
  )
}
