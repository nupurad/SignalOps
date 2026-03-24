import EndpointCard from "./EndpointCard.jsx"

export default function ServiceGroup({ name, monitors }) {
  return (
    <section>
      <h2>{name}</h2>
      <div>
        {monitors.map((m) => (
          <EndpointCard key={m.id} monitor={m} />
        ))}
      </div>
    </section>
  )
}
