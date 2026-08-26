import axios from 'axios'
import type { InvoiceListItem, InvoiceResponse } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
})

export async function extractInvoice(file: File): Promise<InvoiceResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<InvoiceResponse>('/invoices/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function listInvoices(): Promise<InvoiceListItem[]> {
  const { data } = await api.get<InvoiceListItem[]>('/invoices')
  return data
}
