import { useState } from 'react'
import { ExtractView } from './components/ExtractView'
import { HistoryView } from './components/HistoryView'

type Tab = 'extract' | 'history'

function App() {
  const [tab, setTab] = useState<Tab>('extract')
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">🧾 Extractor de Facturas con LLM</h1>
        <p className="mt-1 text-sm text-slate-500">
          Backend FastAPI + PostgreSQL · Frontend React
        </p>
      </header>

      <nav className="mb-6 flex gap-2 border-b border-slate-800">
        <TabButton label="📤 Extraer factura" active={tab === 'extract'} onClick={() => setTab('extract')} />
        <TabButton label="🗂️ Historial" active={tab === 'history'} onClick={() => setTab('history')} />
      </nav>

      {tab === 'extract' ? (
        <ExtractView onExtracted={() => setRefreshKey((k) => k + 1)} />
      ) : (
        <HistoryView refreshKey={refreshKey} />
      )}
    </div>
  )
}

function TabButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`border-b-2 px-4 py-2 text-sm font-medium transition ${
        active
          ? 'border-indigo-500 text-indigo-400'
          : 'border-transparent text-slate-500 hover:text-slate-300'
      }`}
    >
      {label}
    </button>
  )
}

export default App
