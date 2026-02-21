import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  FileText,
  Lightbulb,
  FlaskConical,
  Award,
  AlertTriangle,
  ArrowRight,
  BarChart3,
} from 'lucide-react'
import { useDocument } from '../hooks/useDocuments'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import type { AnalysisResult } from '../types'

function ScoreIndicator({ score }: { score: number }) {
  const percentage = (score / 10) * 100
  const circumference = 2 * Math.PI * 54
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative h-36 w-36">
        <svg className="h-36 w-36 -rotate-90" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="#E5E7EB"
            strokeWidth="8"
          />
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="url(#scoreGradient)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-500"
          />
          <defs>
            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366F1" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-3xl font-heading font-bold text-primary-950">
            {score.toFixed(1)}
          </span>
        </div>
      </div>
      <p className="mt-2 text-sm text-gray-500">out of 10</p>
    </div>
  )
}

function AnalysisCards({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-surface-card rounded-xl shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="h-5 w-5 text-primary-600" />
          <h2 className="font-heading text-lg font-semibold text-primary-950">
            Summary
          </h2>
        </div>
        <p className="text-primary-950 leading-relaxed">{analysis.summary}</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Key Findings */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Key Findings
            </h2>
          </div>
          <ol className="space-y-4">
            {analysis.key_findings.map((kf, idx) => (
              <li key={idx} className="space-y-1">
                <p className="font-bold text-primary-950">
                  {idx + 1}. {kf.finding}
                </p>
                <p className="text-sm italic text-gray-600">{kf.evidence}</p>
                <p className="text-sm text-primary-950">{kf.significance}</p>
              </li>
            ))}
          </ol>
        </div>

        {/* Methodology */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <FlaskConical className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Methodology
            </h2>
          </div>
          <p className="text-primary-950 mb-4">{analysis.methodology.approach}</p>
          <div className="space-y-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Strengths
              </h3>
              <ul className="space-y-1.5">
                {analysis.methodology.strengths.map((s, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                    <span className="mt-0.5 text-emerald-500 shrink-0">&#10003;</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Limitations
              </h3>
              <ul className="space-y-1.5">
                {analysis.methodology.limitations.map((l, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                    <span className="mt-0.5 text-red-500 shrink-0">&#10007;</span>
                    {l}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Contributions */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <Award className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Contributions
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.contributions.map((c, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary-500 shrink-0" />
                {c}
              </li>
            ))}
          </ul>
        </div>

        {/* Limitations */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Limitations
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.limitations.map((l, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-500 shrink-0" />
                {l}
              </li>
            ))}
          </ul>
        </div>

        {/* Future Work */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <ArrowRight className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Future Work
            </h2>
          </div>
          <ul className="space-y-2">
            {analysis.future_work.map((fw, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-primary-950">
                <ArrowRight className="mt-0.5 h-4 w-4 text-primary-500 shrink-0" />
                {fw}
              </li>
            ))}
          </ul>
        </div>

        {/* Relevance Score */}
        <div className="bg-surface-card rounded-xl shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-primary-600" />
            <h2 className="font-heading text-lg font-semibold text-primary-950">
              Relevance Score
            </h2>
          </div>
          <ScoreIndicator score={analysis.relevance_score} />
        </div>
      </div>
    </div>
  )
}

export default function DocumentDetailPage() {
  const { id } = useParams()
  const { data: doc, isLoading } = useDocument(Number(id))

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-6">
          Document Detail
        </h1>
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  if (!doc) {
    return (
      <div>
        <Link
          to="/knowledge"
          className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-800 transition-colors duration-200 mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Knowledge Base
        </Link>
        <EmptyState
          icon={FileText}
          title="Document not found"
          description="The document you are looking for does not exist or has been removed."
        />
      </div>
    )
  }

  return (
    <div>
      {/* Back button */}
      <Link
        to="/knowledge"
        className="inline-flex items-center gap-1.5 text-sm text-primary-600 hover:text-primary-800 transition-colors duration-200 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Knowledge Base
      </Link>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-heading font-bold text-primary-950 mb-3">
          {doc.title}
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="primary">{doc.file_type}</Badge>
          {doc.tags
            .split(', ')
            .filter(Boolean)
            .map((tag) => (
              <Badge key={tag} variant="accent">
                {tag}
              </Badge>
            ))}
          <span className="text-sm text-gray-500">{doc.date}</span>
        </div>
      </div>

      {/* Analysis content or empty state */}
      {doc.analysis ? (
        <AnalysisCards analysis={doc.analysis} />
      ) : (
        <EmptyState
          icon={FileText}
          title="No analysis available"
          description="This document has not been analyzed yet. Run the analysis pipeline to generate insights."
        />
      )}
    </div>
  )
}
