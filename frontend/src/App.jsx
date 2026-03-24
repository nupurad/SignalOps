import { useState, useEffect } from "react"
import axios from "axios"
import ServiceGroup from "./components/ServiceGroup.jsx"

export default function App() {
  const [services, setServices] = useState({})

  useEffect(() => {
    const fetchMonitors = () =>
      axios.get("/api/monitors").then((r) => {
        const grouped = r.data.reduce((acc, m) => {
          acc[m.service] = acc[m.service] || []
          acc[m.service].push(m)
          return acc
        }, {})
        setServices(grouped)
      })

    fetchMonitors()
    const id = setInterval(fetchMonitors, 30000)
    return () => clearInterval(id)
  }, [])

  return (
    <main>
      <h1>SignalOps</h1>
      {Object.entries(services).map(([name, monitors]) => (
        <ServiceGroup key={name} name={name} monitors={monitors} />
      ))}
    </main>
  )
}
