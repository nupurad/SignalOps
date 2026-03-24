import { useState } from "react"
import axios from "axios"
import { LineChart, Line, XAxis, Tooltip } from "recharts"

export default function EndpointCard({ monitor }) {
  const [history, setHistory] = useState(null)

  const handleClick = () =>
    axios
      .get(`/api/monitors/${monitor.id}/results`)
      .then((r) => setHistory(r.data.reverse()))

  const status = monitor.status || "UNKNOWN"

  return (
    <div onClick={handleClick} className="card">
      <span className={`badge ${status === "UP" ? "green" : "red"}`}>
        {status}
      </span>
      <span className="endpoint">{monitor.endpoint}</span>
      <span className="latency">{monitor.latency_ms ?? "-"}ms</span>
      {history && (
        <LineChart width={300} height={80} data={history}>
          <Line dataKey="latency_ms" dot={false} />
          <XAxis dataKey="checked_at" hide />
          <Tooltip />
        </LineChart>
      )}
    </div>
  )
}
