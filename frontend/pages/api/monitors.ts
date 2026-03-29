import type { NextApiRequest, NextApiResponse } from "next"

const API_BASE = process.env.API_BASE || "http://api:8000"

export default async function handler(_req: NextApiRequest, res: NextApiResponse) {
  try {
    const upstream = await fetch(`${API_BASE}/api/monitors`)
    const text = await upstream.text()
    res.status(upstream.status).send(text)
  } catch (err) {
    res.status(502).json({ error: "Upstream API unavailable" })
  }
}
