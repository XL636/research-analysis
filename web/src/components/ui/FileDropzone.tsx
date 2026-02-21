import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileText } from 'lucide-react'

interface FileDropzoneProps {
  onFilesSelected: (files: File[]) => void
  accept?: Record<string, string[]>
}

export default function FileDropzone({
  onFilesSelected,
  accept = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
  },
}: FileDropzoneProps) {
  const [files, setFiles] = useState<File[]>([])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const updated = [...files, ...acceptedFiles]
      setFiles(updated)
      onFilesSelected(updated)
    },
    [files, onFilesSelected],
  )

  const removeFile = useCallback(
    (index: number) => {
      const updated = files.filter((_, i) => i !== index)
      setFiles(updated)
      onFilesSelected(updated)
    },
    [files, onFilesSelected],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
  })

  return (
    <div>
      <div
        {...getRootProps()}
        className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-all duration-200 cursor-pointer ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 bg-white hover:border-primary-400 hover:bg-primary-50/50'
        }`}
      >
        <input {...getInputProps()} />
        <Upload
          className={`h-10 w-10 mb-3 transition-colors duration-200 ${
            isDragActive ? 'text-primary-500' : 'text-gray-400'
          }`}
        />
        {isDragActive ? (
          <p className="text-sm font-medium text-primary-600">
            Drop files here...
          </p>
        ) : (
          <>
            <p className="text-sm font-medium text-gray-600">
              Drag & drop files here, or click to browse
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Supports PDF, PPTX, TXT, MD
            </p>
          </>
        )}
      </div>

      {/* Selected files list */}
      {files.length > 0 && (
        <ul className="mt-4 space-y-2">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center justify-between rounded-lg bg-white border border-gray-200 px-4 py-2.5"
            >
              <div className="flex items-center gap-3 min-w-0">
                <FileText className="h-4 w-4 flex-shrink-0 text-primary-500" />
                <span className="text-sm text-primary-950 truncate">
                  {file.name}
                </span>
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="ml-2 rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-red-500 transition-all duration-200"
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
