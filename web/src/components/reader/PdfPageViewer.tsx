import { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

interface PdfPageViewerProps {
  fileUrl: string
  pageNumber: number
  onLoadSuccess?: (numPages: number) => void
}

export default function PdfPageViewer({ fileUrl, pageNumber, onLoadSuccess }: PdfPageViewerProps) {
  const [containerWidth, setContainerWidth] = useState(0)
  const [numPages, setNumPages] = useState(0)

  useEffect(() => {
    const updateWidth = () => {
      const container = document.getElementById('pdf-container')
      if (container) {
        setContainerWidth(container.clientWidth - 32) // padding
      }
    }
    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  const handleDocLoadSuccess = ({ numPages: n }: { numPages: number }) => {
    setNumPages(n)
    onLoadSuccess?.(n)
  }

  return (
    <div id="pdf-container" className="flex justify-center w-full">
      <Document
        file={fileUrl}
        onLoadSuccess={handleDocLoadSuccess}
        loading={
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
          </div>
        }
        error={
          <div className="text-center py-20 text-red-500">
            PDF failed to load
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
