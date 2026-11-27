<script>
  import { engine, skew } from '../lib/ws.js'

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
  // Restzeit in LPIS-Zeit: Browser-Uhr -> Engine-Uhr (skew) -> LPIS-Uhr (offset)
  const remaining = $derived(target ? target.opens_at - (now + $skew + $engine.clock.offset) : null)
  const critical = $derived(remaining !== null && remaining <= 10)

  function fmt(sec) {
    if (sec <= 0) return 'JETZT'
    const h = Math.floor(sec / 3600)
    const m = Math.floor((sec % 3600) / 60)
    const s = Math.floor(sec % 60)
    const t = Math.floor((sec % 1) * 10)
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${t}`
  }

  const lpisTime = (ts) => new Date(ts * 1000).toLocaleTimeString('de-AT')

  // Countdown auch im Tab-Titel, falls das Fenster im Hintergrund liegt
  $effect(() => {
    document.title = target && remaining > 0
      ? `${fmt(remaining).slice(0, -2)} · kursfix`
      : 'kursfix — LPIS-Anmeldung auf die Sekunde'
  })
</script>

<div class="relative overflow-hidden rounded-2xl border border-zinc-200 px-6 py-7 text-center dark:border-zinc-800">
  <!-- feine WU-Akzentlinie oben -->
  <span class="absolute inset-x-0 top-0 h-px {target ? 'bg-wu' : 'bg-zinc-200 dark:bg-zinc-800'}"></span>

  {#if target}
    <p class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Nächste Öffnung</p>
    <div class="mt-2 font-sans text-6xl font-black tracking-tighter tabular-nums sm:text-7xl
                {critical ? 'text-wu-red' : ''}">
      {fmt(remaining)}
    </div>
    <p class="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
      <strong class="font-semibold text-zinc-900 dark:text-zinc-100">
        {target.name || target.config.label || 'Kurs'}</strong>
      öffnet um {lpisTime(target.opens_at)} LPIS-Zeit
      {#if target.fire_at}
        <span class="text-zinc-400">· Schuss um {lpisTime(target.fire_at + $engine.clock.offset)} LPIS-Zeit</span>
      {/if}
    </p>
  {:else if $engine.running}
    <p class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Vorbereitung</p>
    <div class="mt-2 font-sans text-6xl font-black tracking-tighter text-zinc-200 tabular-nums sm:text-7xl dark:text-zinc-800">
      00:00:00<span class="text-4xl sm:text-5xl">.0</span>
    </div>
    <p class="mt-2 flex items-center justify-center gap-2 text-sm text-zinc-500 dark:text-zinc-400">
      <span class="h-1.5 w-1.5 animate-blink rounded-full bg-wu"></span>
      Warte auf Login und Kursseiten im Browserfenster …
    </p>
  {:else}
    <p class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Bereit</p>
    <div class="mt-2 font-sans text-6xl font-black tracking-tighter text-zinc-200 tabular-nums sm:text-7xl dark:text-zinc-800">
      00:00:00<span class="text-4xl sm:text-5xl">.0</span>
    </div>
    <p class="mt-2 text-sm text-zinc-400">
      Noch nicht gestartet — nach dem Start erscheinen hier Countdown und Live-Karten deiner Kurse.
    </p>
  {/if}
</div>
