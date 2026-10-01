<script>
  import { engine } from '../lib/ws.js'

  let now = $state(Date.now() / 1000)
  $effect(() => {
    const timer = setInterval(() => { now = Date.now() / 1000 }, 100)
    return () => clearInterval(timer)
  })

  // Nächstes Ziel: der früheste bewaffnete Kurs
  const target = $derived(
    $engine.courses
      .filter((c) => c.opens_at && ['armed', 'firing'].includes(c.phase))
      .sort((a, b) => a.opens_at - b.opens_at)[0] ?? null
  )
  // Restzeit in LPIS-Zeit: die eigene Uhr um den gemessenen Offset korrigieren
  const remaining = $derived(target ? target.opens_at - (now + $engine.clock.offset) : null)

  function fmt(sec) {
    if (sec <= 0) return 'JETZT'
    const h = Math.floor(sec / 3600)
    const m = Math.floor((sec % 3600) / 60)
    const s = Math.floor(sec % 60)
    const t = Math.floor((sec % 1) * 10)
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${t}`
  }

  function lpisTime(ts) {
    return new Date(ts * 1000).toLocaleTimeString('de-AT')
  }
</script>

<div class="rounded-2xl bg-white p-5 text-center shadow-sm dark:bg-zinc-900">
  {#if target}
    <div class="font-mono text-6xl font-bold tabular-nums tracking-tight
                {remaining <= 10 ? 'text-orange-500' : ''}">
      {fmt(remaining)}
    </div>
    <div class="mt-1 text-sm text-zinc-500">
      bis zur Öffnung von <strong>{target.name || target.config.label || 'Kurs'}</strong>
      um {lpisTime(target.opens_at)} LPIS-Zeit
    </div>
  {:else if $engine.running}
    <div class="font-mono text-5xl font-bold text-zinc-300 dark:text-zinc-700">--:--:--</div>
    <div class="mt-1 text-sm text-zinc-500">Warte auf Kursseiten und Öffnungszeiten …</div>
  {:else}
    <div class="font-mono text-5xl font-bold text-zinc-300 dark:text-zinc-700">--:--:--</div>
    <div class="mt-1 text-sm text-zinc-500">Nicht gestartet</div>
  {/if}
</div>
