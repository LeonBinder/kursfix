// WebSocket-Verbindung zum Backend plus die Svelte-Stores, die die UI speisen.
import { writable, get } from 'svelte/store'

export const connected = writable(false)
export const engine = writable({
  running: false, dry_run: false, mode: 'live', target: '', logged_in: null,
  clock: { offset: 0, uncertainty: 0.5, trip: 0, source: 'none', synced_at: null },
  courses: [],
})
// Abstand Engine-Uhr minus Browser-Uhr (s). Die Engine rechnet auf einer eigenen,
// gleichmäßig laufenden Uhr; der Countdown muss dieselbe benutzen.
export const skew = writable(0)
const noteServerTime = (state) => {
  if (state && state.now) skew.set(state.now - Date.now() / 1000)
}
export const logs = writable([])
export const config = writable({ courses: [], save_snapshots: false, direct_shot: false })

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
      noteServerTime(event.state)
      engine.set(event.state)
      logs.set(event.logs)
      config.set(event.config)
    } else if (event.type === 'state') {
      noteServerTime(event.state)
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

// 'idle' | 'saving' | 'saved' — speist die dezente Speicher-Anzeige im Editor
export const saveState = writable('idle')
let saveTimer = null
let savedTimer = null
export function saveConfigSoon() {
  clearTimeout(saveTimer)
  saveState.set('saving')
  saveTimer = setTimeout(async () => {
    try {
      await api('/api/config', get(config))
      saveState.set('saved')
      clearTimeout(savedTimer)
      savedTimer = setTimeout(() => saveState.set('idle'), 1500)
    } catch (e) {
      console.error(e)
      saveState.set('idle')
    }
  }, 400)
}

// mode: 'live' (echte Anmeldung) | 'dry' (Fake-LPIS) | 'check' (echtes LPIS, nur lesen)
export const startEngine = (mode = 'live') =>
  api('/api/start', { dry_run: mode === 'dry', check: mode === 'check' })
export const stopEngine = () => api('/api/stop', {})
