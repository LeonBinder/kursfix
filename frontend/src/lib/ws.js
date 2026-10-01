// WebSocket-Verbindung zum Backend plus die Svelte-Stores, die die UI speisen.
import { writable, get } from 'svelte/store'

export const connected = writable(false)
export const engine = writable({
  running: false, dry_run: false, logged_in: null,
  clock: { offset: 0, uncertainty: 0.5, trip: 0, source: 'none', synced_at: null },
  courses: [],
})
export const logs = writable([])
export const config = writable({ courses: [], save_snapshots: false })

const MAX_LOGS = 400
let socket = null

export function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${proto}://${location.host}/ws`)
  socket.onopen = () => connected.set(true)
  socket.onclose = () => {
    connected.set(false)
    setTimeout(connect, 1500)
  }
  socket.onmessage = (msg) => {
    const event = JSON.parse(msg.data)
    if (event.type === 'hello') {
      engine.set(event.state)
      logs.set(event.logs)
      config.set(event.config)
    } else if (event.type === 'state') {
      engine.set(event.state)
    } else if (event.type === 'log' || event.type === 'alarm') {
      logs.update((list) => [...list.slice(-MAX_LOGS + 1), event])
      if (event.type === 'alarm') beep()
    }
  }
}

// Drei kurze Pieptöne, wenn die Engine Alarm schlägt (z. B. Logout)
function beep() {
  try {
    const ctx = new AudioContext()
    for (let i = 0; i < 3; i++) {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain).connect(ctx.destination)
      osc.frequency.value = 880
      gain.gain.value = 0.15
      osc.start(ctx.currentTime + i * 0.25)
      osc.stop(ctx.currentTime + i * 0.25 + 0.15)
    }
  } catch { /* ohne Audio-Erlaubnis: still bleiben */ }
}

async function api(path, body) {
  const resp = await fetch(path, {
    method: body === undefined ? 'GET' : path.includes('config') ? 'PUT' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!resp.ok) {
    const detail = (await resp.json().catch(() => ({}))).detail
    throw new Error(detail || `${resp.status} ${resp.statusText}`)
  }
  return resp.json()
}

let saveTimer = null
export function saveConfigSoon() {
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => api('/api/config', get(config)).catch(console.error), 400)
}

export const startEngine = (dryRun) => api('/api/start', { dry_run: dryRun })
export const stopEngine = () => api('/api/stop', {})
