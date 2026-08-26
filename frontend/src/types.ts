export interface InvoiceListItem {
  id: string
  filename: string
  fecha_emision: string | null
  fecha_emision_valida: boolean
  valor_total: number | null
  moneda: string | null
  proveedor: string | null
  numero_factura: string | null
  created_at: string
}

export interface InvoiceResponse extends InvoiceListItem {
  raw_llm_response: string | null
}
