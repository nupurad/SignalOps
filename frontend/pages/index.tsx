import { useEffect, useMemo, useState } from "react"

type Monitor = {
  id: number
  service: string
  endpoint: string
  url: string
  method: string
  interval: number
  status: "UP" | "DOWN" | null
  latency_ms: number | null
  checked_at: string | null
}

type Grouped = Record<string, Monitor[]>

function groupByService(items: Monitor[]): Grouped {
  return items.reduce((acc, m) => {
    acc[m.service] = acc[m.service] || []
    acc[m.service].push(m)
    return acc
  }, {} as Grouped)
}

export default function Home() {
  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [theme, setTheme] = useState<"dark" | "light">("dark")

  const grouped = useMemo(() => groupByService(monitors), [monitors])

  const fetchMonitors = async () => {
    try {
      const res = await fetch("/api/monitors")
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const data = (await res.json()) as Monitor[]
      setMonitors(data)
      setLastUpdated(new Date().toLocaleTimeString())
      setError(null)
    } catch (e) {
      setError("Unable to load monitors")
    }
  }

  useEffect(() => {
    fetchMonitors()
    const id = setInterval(fetchMonitors, 30000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const stored =
      typeof window !== "undefined" ? localStorage.getItem("signalops-theme") : null
    const prefersDark =
      typeof window !== "undefined" &&
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    const initial = (stored as "dark" | "light" | null) || (prefersDark ? "dark" : "light")
    setTheme(initial)
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", initial)
    }
  }, [])

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark"
    setTheme(next)
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", next)
    }
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("signalops-theme", next)
    }
  }

  return (
    <div className="page">
      <div className="sidebar-toggle">
        <button
          className="hamburger"
          aria-label="Open menu"
          onClick={(e) => {
            const el = document.getElementById("nav-drawer")
            if (el) el.classList.toggle("open")
          }}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      <aside id="nav-drawer" className="nav-drawer">
        <div className="nav-header">
          <span>Quick Links</span>
          <button
            className="nav-close"
            aria-label="Close menu"
            onClick={() => {
              const el = document.getElementById("nav-drawer")
              if (el) el.classList.remove("open")
            }}
          >
            ✕
          </button>
        </div>
        <nav className="nav-links">
          <a href="http://localhost:9090" target="_blank" rel="noreferrer">
            Prometheus
          </a>
          <a href="http://localhost:3001" target="_blank" rel="noreferrer">
            Grafana
          </a>
        </nav>
      </aside>

      <header className="header">
        <div>
          <h1>SignalOps</h1>
          <p className="subtitle">Microservice health overview</p>
        </div>
        <div className="meta">
          <span className="pill">Auto-refresh: 30s</span>
          <span className="pill">Last update: {lastUpdated || "--"}</span>
          <button className="toggle-switch" onClick={toggleTheme} aria-label="Toggle theme">
            <span className="toggle-track" aria-hidden="true">
              <span className="toggle-icon sun">
                <img
                  src="https://img.icons8.com/ios/50/sun--v1.png"
                  alt="Sun"
                />
              </span>
              <span className="toggle-icon moon">
                <img
                  src="https://img.icons8.com/ios/50/do-not-disturb-2.png"
                  alt="Moon"
                />
              </span>
              <span className={`toggle-thumb ${theme === "dark" ? "is-dark" : "is-light"}`} />
            </span>
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <div className="grid">
        {Object.entries(grouped).map(([service, items]) => (
          <section key={service} className="card">
            <div className="card-header">
              <h2>{service}</h2>
              <span className="count">{items.length} endpoints</span>
            </div>
            <div className="table">
              <div className="row head">
                <span>Endpoint</span>
                <span>Status</span>
                <span>Latency</span>
                <span>Interval</span>
              </div>
              {items.map((m) => (
                <div key={m.id} className="row">
                  <span className="endpoint">
                    <span className="method">{m.method}</span>
                    {m.endpoint}
                  </span>
                  <span className={`status ${m.status === "UP" ? "up" : "down"}`}>
                    {m.status || "UNKNOWN"}
                  </span>
                  <span className="latency">
                    {m.latency_ms != null ? `${m.latency_ms} ms` : "--"}
                  </span>
                  <span className="interval">{m.interval} min</span>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
