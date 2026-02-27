import { useState, useEffect, useRef, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Use Vite ?url import for reliable worker path resolution
import pdfjsWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorkerUrl

interface PdfPageViewerProps {
  fileUrl: string
  pageNumber: number
  onLoadSuccess?: (numPages: number) => void
}

export default function PdfPageViewer({ fileUrl, pageNumber, onLoadSuccess }: PdfPageViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)
  const [numPages, setNumPages] = useState(0)
  const [error, setError] = useState<string>('')

  const updateWidth = useCallback(() => {
    if (containerRef.current) {
      setContainerWidth(containerRef.current.clientWidth - 32)
    }
  }, [])

  useEffect(() => {
    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [updateWidth])

  const handleDocLoadSuccess = ({ numPages: n }: { numPages: number }) => {
    setNumPages(n)
    setError('')
    onLoadSuccess?.(n)
  }

  const [fileStatus, setFileStatus] = useState<'checking' | 'ok' | 'not_found' | 'error'>('checking')

  // Pre-check if the file is accessible before handing to react-pdf
  useEffect(() => {
    setFileStatus('checking')
    fetch(fileUrl, { method: 'HEAD' })
      .then(resp => {
        if (resp.ok) {
          setFileStatus('ok')
        } else if (resp.status === 404) {
          setFileStatus('not_found')
        } else {
          setFileStatus('error')
          setError(`HTTP ${resp.status}`)
        }
      })
      .catch(() => {
        setFileStatus('error')
        setError('Network error')
      })
  }, [fileUrl])

  const handleDocLoadError = (err: Error) => {
    console.error('PDF load error:', err)
    setError(err.message || 'Unknown error')
  }

  if (fileStatus === 'checking') {
    return (
      <div ref={containerRef} className="flex items-center justify-center py-20 w-full">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    )
  }

  if (fileStatus === 'not_found') {
    return (
      <div ref={containerRef} className="flex flex-col items-center w-full">
        <div className="text-center py-20">
          <p className="text-red-500 font-medium mb-2">PDF 原始文件不存在</p>
          <p className="text-xs text-gray-400 mb-3">文件可能在服务器重启后丢失，请重新上传文档</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="flex flex-col items-center w-full">
      <Document
        file={fileUrl}
        onLoadSuccess={handleDocLoadSuccess}
        onLoadError={handleDocLoadError}
        loading={
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
          </div>
        }
        error={
          <div className="text-center py-20">
            <p className="text-red-500 font-medium mb-2">PDF failed to load</p>
            {error && <p className="text-xs text-gray-400">{error}</p>}
            <a
              href={fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-3 text-sm text-primary-600 underline hover:text-primary-800"
            >
              Download PDF
            </a>
          </div>
        }
      >
        {numPages > 0 && pageNumber >= 1 && pageNumber <= numPages && (
          <Page
            pageNumber={pageNumber}
            width={containerWidth > 0 ? containerWidth : undefined}
            renderTextLayer={true}
            renderAnnotationLayer={true}
          />
        )}
      </Document>
    </div>
  )
}
