import { useState } from 'react'
import {
  Search,
  Loader,
  Wrench,
  Clock,
  Star,
  DollarSign,
  Calendar,
  Zap,
  AlertTriangle,
  CheckCircle
} from 'lucide-react'

// ─── InfoCard ────────────────────────────────────────────────────────────────
function InfoCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue:   ['border-blue-200','bg-blue-50','text-blue-600'],
    green:  ['border-green-200','bg-green-50','text-green-600'],
    yellow: ['border-yellow-200','bg-yellow-50','text-yellow-600'],
    purple: ['border-purple-200','bg-purple-50','text-purple-600']
  }[color] || ['border-gray-200','bg-gray-50','text-gray-600']

  return (
    <div className={`rounded-lg p-4 border ${colors[0]} ${colors[1]}`}>
      <div className="flex items-center space-x-2 mb-1">
        <Icon className={`w-5 h-5 ${colors[2]}`} />
        <span className={`font-medium ${colors[2]}`}>{label}</span>
      </div>
      <p className={`text-lg font-semibold ${colors[2]}`}>{value}</p>
    </div>
  )
}

// ─── ListSection ────────────────────────────────────────────────────────────
function ListSection({ icon: Icon, title, items = [] }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="flex items-center font-medium text-gray-800 mb-2 space-x-2">
        <Icon className="w-5 h-5 text-gray-600" />
        <span>{title}</span>
      </h3>
      <ul className="list-disc list-inside space-y-1 text-gray-700">
        {items.map((it,i) => <li key={i}>{it}</li>)}
      </ul>
    </div>
  )
}

// ─── StepsList ───────────────────────────────────────────────────────────────
function StepsList({ steps = [] }) {
  return (
    <div className="space-y-4">
      {steps.map((s,i) => (
        <div
          key={i}
          className="bg-white p-5 rounded-lg shadow hover:shadow-lg transition-shadow"
        >
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 bg-red-600 text-white w-7 h-7 flex items-center justify-center rounded-full font-bold">
              {s.step_number}
            </div>
            <div className="flex-1">
              <p className="mb-3 text-gray-700">{s.description}</p>
              {s.tools_needed?.length > 0 && (
                <p className="text-sm"><strong>Tools:</strong> {s.tools_needed.join(', ')}</p>
              )}
              {s.materials_needed?.length > 0 && (
                <p className="text-sm"><strong>Materials:</strong> {s.materials_needed.join(', ')}</p>
              )}
              {s.safety_tips?.length > 0 && (
                <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="flex items-center font-semibold text-yellow-800 mb-1">
                    <AlertTriangle className="w-4 h-4 mr-2"/> Safety Tips
                  </p>
                  <ul className="list-disc list-inside text-yellow-700">
                    {s.safety_tips.map((t,j) => <li key={j}>{t}</li>)}
                  </ul>
                </div>
              )}
              {s.troubleshooting_notes?.length > 0 && (
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="flex items-center font-semibold text-red-800 mb-1">
                    <AlertTriangle className="w-4 h-4 mr-2"/> Troubleshooting
                  </p>
                  <ul className="list-disc list-inside text-red-700">
                    {s.troubleshooting_notes.map((n,j) => <li key={j}>{n}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── LinksCard ───────────────────────────────────────────────────────────────
function LinksCard({ title, data = {} }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="font-medium text-gray-800 mb-3">{title}</h3>
      {Object.entries(data).map(([name, links], idx) => (
        <div key={idx} className="mb-4 last:mb-0">
          <p className="font-semibold text-gray-700 mb-1">{name}</p>
          <ul className="list-none pl-0 space-y-1">
            {Array.isArray(links)
              ? links.map((u,i) => {
                  const [href, tag] = u.split(' - ')
                  return (
                    <li key={i}>
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {tag ?? href}
                      </a>
                    </li>
                  )
                })
              : (
                <li>
                  <a
                    href={links}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {links}
                  </a>
                </li>
              )
            }
          </ul>
        </div>
      ))}
    </div>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [query, setQuery]     = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)

  async function handleSearch() {
    if (!query.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      if (!res.ok) {
        console.error(res.statusText)
        return
      }
      const data = await res.json()
      setResult({
        ...data,
        Tools:      Array.isArray(data.Tools)       ? data.Tools       : [],
        materials: Array.isArray(data.materials)   ? data.materials   : [],
        steps:     Array.isArray(data.steps)       ? data.steps       : [],
        shopping:  data['Looking for tools and materials?']?.[0] ?? {},
        resources: data['Additional resources']?.[0] ?? {}
      })
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const diffColor = (r) => {
    const n = parseInt(r,10) || 0
    return n <= 3 ? 'green' : n <= 6 ? 'yellow' : 'purple'
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* ─── HEADER ───────────────────────────────────── */}
      <header className="bg-red-700 text-white py-6 shadow">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-center items-center space-x-2">
            {/* enlarged, perfectly centered logo */}
            <img
              src="/toyota-logo.png"
              alt="Toyota Logo"
              className="h-16 w-auto"
            />
            <h1 className="text-2xl font-bold">Toyota Expert Mechanic</h1>
            <Wrench className="w-6 h-6"/>
          </div>
          <p className="text-red-200 text-center mt-1">
            Professional repair guidance powered by AI
          </p>
        </div>
      </header>

      {/* ─── SEARCH BAR ───────────────────────────────── */}
      <div className="flex-grow flex items-center justify-center">
        <div className="max-w-6xl w-full px-4">
          <div className="flex overflow-hidden rounded-lg shadow bg-white">
            <div className="px-3 flex items-center text-gray-500">
              <Search className="w-5 h-5" />
            </div>
            <input
              className="flex-1 px-3 py-2 focus:outline-none"
              placeholder="Ask about any Toyota maintenance or repair…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key==='Enter' && handleSearch()}
              disabled={loading}
            />
            <button
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              className="bg-red-600 hover:bg-red-800 disabled:opacity-50 px-5 flex items-center justify-center text-white"
            >
              {loading
                ? <Loader className="w-6 h-6 animate-spin" />
                : 'Get Help'
              }
            </button>
          </div>
        </div>
      </div>

      {/* ─── RESULTS / TWO‑COLUMN LAYOUT ─────────────── */}
      {result && (
        <div className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-6 lg:col-span-2">
            {/* InfoCards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <InfoCard
                icon={Clock}
                label="Time"
                value={result.Estimated_Time}
                color="blue"
              />
              <InfoCard
                icon={Star}
                label="Difficulty"
                value={result['Difficulty rating']}
                color={diffColor(result['Difficulty rating'])}
              />
              <InfoCard
                icon={DollarSign}
                label="Tools Cost"
                value={result['Estimated_Cost for tools/materials']}
                color="green"
              />
              <InfoCard
                icon={Calendar}
                label="Replace"
                value={result['Needs to be replaced/changed in']}
                color="purple"
              />
            </div>

            {/* Tools & Materials */}
            <div className="grid lg:grid-cols-2 gap-4">
              <ListSection icon={Wrench} title="Required Tools" items={result.Tools} />
              <ListSection icon={Zap} title="Materials Needed" items={result.materials} />
            </div>

            {/* Parts Cost */}
            <div className="bg-white p-4 rounded-lg shadow text-center">
              <p className="font-medium text-orange-700">Estimated Parts Cost</p>
              <p className="mt-2 text-2xl font-semibold text-orange-600">
                {result['Estimated_Cost for Part(s)']}
              </p>
            </div>

            {/* Steps */}
            <StepsList steps={result.steps} />
          </div>

          {/* Sticky sidebar */}
          <aside className="space-y-6 lg:sticky lg:top-24">
            <LinksCard title="🔗 Shopping Links" data={result.shopping} />
            <LinksCard title="📚 Additional Resources" data={result.resources} />
          </aside>
        </div>
      )}
    </div>
  )
}
