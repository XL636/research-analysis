import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpenCheck, Upload, Trash2, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useDropzone } from 'react-dropzone'
import { useReaderDocuments, useUploadReaderDocument, useDeleteReaderDocument } from '../hooks/useReader'
import EmptyState from '../components/ui/EmptyState'

export default function ReaderListPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { data: documents, isLoading } = useReaderDocuments()
  const uploadDoc = useUploadReaderDocument()
  const deleteDoc = useDeleteReaderDocument()
  const [showUpload, setShowUpload] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      uploadDoc.mutate(acceptedFiles[0], {
        onSuccess: (doc) => {
          setShowUpload(false)
          navigate(`/reader/${doc.id}`)
        },
      })
    }
  }, [uploadDoc, navigate])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
    },
    maxFiles: 1,
  })

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    deleteDoc.mutate(id)
  }

  const fileTypeIcon = (type: string) => {
    const colors: Record<string, string> = {
      pdf: 'text-red-500',
      pptx: 'text-orange-500',
      docx: 'text-blue-500',
      md: 'text-gray-600',
      txt: 'text-gray-500',
    }
    return colors[type] || 'text-gray-400'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-heading font-bold text-primary-950">
          {t('reader.title')}
        </h1>
        <button
          onClick={() => setShowUpload(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
        >
          <Upload className="w-4 h-4" />
          {t('reader.upload')}
        </button>
      </div>

      {isLoading ? (
        <p className="text-gray-500">{t('common.loading')}</p>
      ) : !documents || documents.length === 0 ? (
        <EmptyState
          icon={BookOpenCheck}
          title={t('reader.emptyTitle')}
          description={t('reader.emptyDesc')}
          action={
            <button
              onClick={() => setShowUpload(true)}
              className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors duration-200"
            >
              {t('reader.upload')}
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              onClick={() => navigate(`/reader/${doc.id}`)}
              className="group bg-white rounded-xl border border-gray-200 p-5 cursor-pointer hover:shadow-md hover:border-primary-300 transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3 min-w-0">
                  <FileText className={`w-8 h-8 shrink-0 ${fileTypeIcon(doc.file_type)}`} />
                  <div className="min-w-0">
                    <h3 className="text-sm font-semibold text-primary-950 truncate">
                      {doc.title}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {doc.file_type.toUpperCase()} · {doc.total_pages} {t('reader.pages')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(e, doc.id)}
                  className="p-1.5 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all duration-200"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>
                  {t('reader.progress')}: {doc.current_page}/{doc.total_pages}
                </span>
                <span>{doc.updated_at}</span>
              </div>
              {/* Progress bar */}
              <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 rounded-full transition-all duration-300"
                  style={{ width: `${doc.total_pages > 0 ? (doc.current_page / doc.total_pages) * 100 : 0}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload dialog */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-heading font-semibold text-primary-950 mb-4">
              {t('reader.uploadTitle')}
            </h3>

            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-10 h-10 mx-auto text-gray-400 mb-3" />
              {isDragActive ? (
                <p className="text-primary-600 font-medium">{t('dropzone.dropHere')}</p>
              ) : (
                <>
                  <p className="text-gray-600 font-medium">{t('dropzone.dragOrClick')}</p>
                  <p className="text-sm text-gray-400 mt-1">{t('dropzone.supportedFormats')}</p>
                </>
              )}
            </div>

            {uploadDoc.isPending && (
              <div className="mt-4 text-center text-sm text-primary-600">
                {t('reader.uploading')}
              </div>
            )}

            <div className="flex justify-end mt-4">
              <button
                onClick={() => setShowUpload(false)}
                disabled={uploadDoc.isPending}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                {t('common.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
