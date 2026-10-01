<script>
  import { connected, engine, startEngine, stopEngine } from './lib/ws.js'
  import CourseEditor from './components/CourseEditor.svelte'
  import CourseCard from './components/CourseCard.svelte'
  import Countdown from './components/Countdown.svelte'
  import LogPanel from './components/LogPanel.svelte'

  let dark = $state(document.documentElement.classList.contains('dark'))
  let error = $state('')
  let busy = $state(false)

  function toggleTheme() {
    dark = !dark
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  async function run(fn) {
    error = ''
    busy = true
    try { await fn() } catch (e) { error = e.message } finally { busy = false }
  }

  const clock = $derived($engine.clock)
  const offsetMs = $derived(Math.round(clock.offset * 1000))
</script>

<div class="mx-auto flex min-h-screen max-w-6xl flex-col gap-4 p-4">
  <header class="flex flex-wrap items-center gap-3">
    <h1 class="text-2xl font-bold tracking-tight">
      kursfix
      <span class="ml-1 text-sm font-normal text-zinc-500">LPIS-Anmeldung, auf die Sekunde</span>
    </h1>
    <span class="ml-auto flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs text-zinc-600 shadow-sm dark:bg-zinc-900 dark:text-zinc-300">
      {#if clock.synced_at}
        Uhr {offsetMs >= 0 ? '+' : ''}{offsetMs} ms
        <span class="text-zinc-400">±{Math.round(clock.uncertainty * 1000)} ms</span>
        · Latenz {Math.round(clock.trip * 1000)} ms
        <span class="text-zinc-400">({clock.source})</span>
      {:else}
        Uhr: noch nicht synchronisiert
      {/if}
    </span>
    <span class="flex items-center gap-1.5 text-xs text-zinc-500" title="Verbindung zum Backend">
      <span class="h-2 w-2 rounded-full {$connected ? 'bg-emerald-500' : 'bg-red-500'}"></span>
      {$connected ? 'verbunden' : 'getrennt'}
    </span>
    <button onclick={toggleTheme} aria-label="Theme wechseln"
            class="rounded-lg bg-white px-2.5 py-1 text-sm shadow-sm hover:bg-zinc-50 dark:bg-zinc-900 dark:hover:bg-zinc-800">
      {dark ? '☀️' : '🌙'}
    </button>
  </header>

  {#if $engine.logged_in === false}
    <div class="animate-pulse rounded-xl border border-red-300 bg-red-50 px-4 py-3 font-medium text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
      ⚠ LPIS hat dich ausgeloggt — im Bot-Browserfenster neu einloggen und die Kursseite wieder öffnen!
    </div>
  {:else if !$engine.running}
    <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
      <strong>Tipp:</strong> 15–25 Minuten vor der Öffnung starten — die WU verlangt nach ca. 30 Minuten
      einen frischen Login. Nach dem Start im Browserfenster einloggen und jede Kursseite
      (mit den „anmelden“-Buttons) einmal öffnen.
    </div>
  {/if}

  {#if error}
    <div class="rounded-xl border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
      {error}
    </div>
  {/if}

  <div class="grid gap-4 lg:grid-cols-[minmax(320px,1fr)_2fr]">
    <section class="flex flex-col gap-3">
      <CourseEditor disabled={$engine.running} />
      <div class="flex gap-2">
        {#if $engine.running}
          <button onclick={() => run(stopEngine)} disabled={busy}
                  class="flex-1 rounded-xl bg-red-600 px-4 py-2.5 font-semibold text-white shadow hover:bg-red-500 disabled:opacity-50">
            Stop
          </button>
        {:else}
          <button onclick={() => run(() => startEngine(false))} disabled={busy || !$connected}
                  class="flex-1 rounded-xl bg-emerald-600 px-4 py-2.5 font-semibold text-white shadow hover:bg-emerald-500 disabled:opacity-50">
            Start
          </button>
          <button onclick={() => run(() => startEngine(true))} disabled={busy || !$connected}
                  title="Probe gegen einen lokalen Fake-LPIS — es geht nichts an die WU"
                  class="rounded-xl bg-zinc-200 px-4 py-2.5 font-medium text-zinc-700 shadow hover:bg-zinc-300 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700">
            Trockenlauf
          </button>
        {/if}
      </div>
      {#if $engine.running && $engine.dry_run}
        <p class="text-center text-xs font-medium text-sky-600 dark:text-sky-400">
          Trockenlauf — alles läuft gegen den lokalen Fake-LPIS.
        </p>
      {/if}
    </section>

    <section class="flex flex-col gap-4">
      <Countdown />
      {#if $engine.courses.length}
        <div class="grid gap-3 xl:grid-cols-2">
          {#each $engine.courses as course (course.config.id)}
            <CourseCard {course} />
          {/each}
        </div>
      {/if}
    </section>
  </div>

  <LogPanel />

  <footer class="pb-2 text-center text-xs text-zinc-400">
    Inoffizielles Werkzeug, nicht von der WU — Nutzung auf eigenes Risiko. Läuft nur lokal.
  </footer>
</div>
