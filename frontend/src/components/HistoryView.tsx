import { useEffect, useState } from 'react'
import { listInvoices } from '../lib/api'
import type { InvoiceListItem } from '../types'

interface HistoryViewProps {
  refreshKey: number
}

export function HistoryView({ refreshKey }: HistoryViewProps) {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    listInvoices()
      .then(setInvoices)
      .catch(() => setError('No se pudo cargar el historial de facturas.'))
      .finally(() => setLoading(false))
  }, [refreshKey])

  if (loading) return <p className="text-sm text-slate-500">Cargando historial…</p>
  if (error) return <p className="text-sm text-red-400">{error}</p>
  if (invoices.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        Aún no se han procesado facturas. Ve a la pestaña "Extraer factura" para empezar.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead className="bg-slate-900 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <Th>Archivo</Th>
            <Th>Fecha emisión</Th>
            <Th>Valor total</Th>
            <Th>Moneda</Th>
            <Th>Proveedor</Th>
            <Th>N° Factura</Th>
            <Th>Procesado</Th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {invoices.map((invoice) => (
            <tr key={invoice.id} className="hover:bg-slate-900/50">
              <Td>{invoice.filename}</Td>
              <Td>
                {invoice.fecha_emision ?? '—'}
                {invoice.fecha_emision && !invoice.fecha_emision_valida && ' ⚠️'}
              </Td>
              <Td>{invoice.valor_total !== null ? invoice.valor_total.toLocaleString() : '—'}</Td>
              <Td>{invoice.moneda ?? '—'}</Td>
              <Td>{invoice.proveedor ?? '—'}</Td>
              <Td>{invoice.numero_factura ?? '—'}</Td>
              <Td>{new Date(invoice.created_at).toLocaleString()}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-medium">{children}</th>
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="whitespace-nowrap px-4 py-3 text-slate-300">{children}</td>
}
