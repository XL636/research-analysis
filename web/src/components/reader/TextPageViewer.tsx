import MarkdownRenderer from '../ui/MarkdownRenderer'

interface TextPageViewerProps {
  content: string
  isLoading?: boolean
}

export default function TextPageViewer({ content, isLoading }: TextPageViewerProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  if (!content.trim()) {
    return (
      <div className="text-center py-20 text-gray-400">
        (empty page)
      </div>
    )
  }

  return (
    <div className="px-2 py-4">
      <MarkdownRenderer content={content} />
    </div>
  )
}
