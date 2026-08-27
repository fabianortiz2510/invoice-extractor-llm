import { useState } from 'react'
import axios from 'axios'
import { extractInvoice } from '../lib/api'
import type { InvoiceResponse } from '../types'

const ACCEPTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf']

interface ExtractViewProps {
  onExtracted: () => void
}

export function ExtractView({ onExtracted }: ExtractViewProps) {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<InvoiceResponse | null>(null)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null
    setFile(selected)
    setResult(null)
    setError(null)
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null)
  }

  async function handleExtract() {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await extractInvoice(file)
      setResult(data)
      onExtracted()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(String(err.response.data.detail))
      } else {
        setError('Ocurrió un error inesperado al extraer la factura.')
      }
    } finally {
      setLoading(false)
    }
  }

  const isPdf = file?.type === 'application/pdf'

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div className="space-y-4">
        <label className="block text-sm font-medium text-slate-700">
          Carga una factura (PNG, JPG o PDF)
        </label>
        <input
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleFileChange}
          className="block w-full cursor-pointer rounded-lg border border-slate-300 bg-white p-2 text-sm text-slate-700 shadow-sm file:mr-4 file:rounded-md file:border-0 file:bg-teal-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-teal-500"
        />

        {previewUrl && (
          <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            {isPdf ? (
              <p className="text-sm text-slate-500">📄 Archivo PDF cargado. Se procesará la primera página.</p>
            ) : (
              <img src={previewUrl} alt="Vista previa de la factura" className="max-h-80 rounded-md" />
            )}
          </div>
        )}

        <button
          onClick={handleExtract}
          disabled={!file || loading}
          className="w-full rounded-lg bg-teal-600 px-4 py-2 font-medium text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Analizando factura con el LLM…' : 'Extraer datos'}
        </button>
      </div>

      <div className="space-y-4">
        <h2 className="text-sm font-medium text-slate-700">Resultado</h2>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
              Datos extraídos correctamente.
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Fecha de emisión" value={fieldOrFallback(result.fecha_emision, result.fecha_emision_valida)} />
              <Field
                label="Valor total"
                value={result.valor_total !== null ? `${result.valor_total.toLocaleString()} ${result.moneda ?? ''}`.trim() : 'No detectado'}
              />
              <Field label="Proveedor" value={result.proveedor ?? 'No detectado'} />
              <Field label="Número de factura" value={result.numero_factura ?? 'No detectado'} />
            </div>

            {result.fecha_emision && !result.fecha_emision_valida && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">
                La fecha extraída no pudo normalizarse a formato YYYY-MM-DD; se guardó tal como la
                devolvió el modelo.
              </div>
            )}

            <details className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
              <summary className="cursor-pointer text-sm text-slate-500">Ver respuesta cruda del LLM</summary>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600">
                {result.raw_llm_response}
              </pre>
            </details>
          </div>
        )}

        {!result && !error && (
          <p className="text-sm text-slate-500">
            Carga un archivo y presiona "Extraer datos" para ver los resultados aquí.
          </p>
        )}
      </div>
    </div>
  )
}

function fieldOrFallback(value: string | null, valid: boolean): string {
  if (!value) return 'No detectada'
  return valid ? value : `${value} ⚠️`
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-900">{value}</p>
    </div>
  )
}
