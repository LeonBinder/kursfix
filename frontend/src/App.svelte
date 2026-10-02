<script>
  import { fade, fly } from 'svelte/transition'
  import { connected, engine, config, startEngine, stopEngine } from './lib/ws.js'
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
  const hasCourses = $derived($config.courses.some((c) => c.groups.length))

  const STEPS = [
    ['Kurse eintragen', 'Gruppennummern aus der linken LPIS-Spalte, erste Wahl zuerst.'],
    ['Start drücken', '15–25 Minuten vor der Öffnung — der WU-Login hält ca. 30 Minuten.'],
    ['Einloggen & Seiten öffnen', 'Im Browserfenster anmelden, jede Kursseite einmal öffnen. Den Rest macht kursfix.'],
  ]
</script>

<div class="flex min-h-screen flex-col">
  <!-- ======================= Kopfzeile ======================= -->
  <header class="sticky top-0 z-10 border-b border-zinc-200 bg-white/90 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/90">
    <div class="mx-auto flex h-14 max-w-6xl items-center gap-3 px-4 sm:px-6">
      <a href="/" class="flex items-center gap-2.5" aria-label="kursfix">
        <svg viewBox="0 0 32 32" class="h-7 w-7" aria-hidden="true">
          <rect width="32" height="32" rx="8" class="fill-zinc-950 dark:fill-white" />
          <circle cx="16" cy="16" r="8.5" fill="none" stroke-width="2.5"
                  class="stroke-white dark:stroke-zinc-950" />
          <circle cx="16" cy="16" r="3.5" class="fill-wu" />
        </svg>
        <span class="text-[17px] font-bold tracking-tight">kursfix</span>
        <span class="mt-0.5 hidden text-xs text-zinc-400 sm:inline">LPIS-Anmeldung auf die Sekunde</span>
      </a>

      <div class="ml-auto flex items-center gap-2">
        {#if clock.synced_at}
          <span transition:fade class="hidden items-center gap-1.5 rounded-full border border-zinc-200 px-3 py-1 font-mono text-[11px] tabular-nums text-zinc-600 md:flex dark:border-zinc-800 dark:text-zinc-300"
                title="Gemessener Uhr-Offset gegen LPIS ({clock.source})">
            <span class="h-1.5 w-1.5 rounded-full bg-wu"></span>
            {offsetMs >= 0 ? '+' : ''}{offsetMs} ms
            <span class="text-zinc-400">±{Math.round(clock.uncertainty * 1000)}</span>
            <span class="text-zinc-300 dark:text-zinc-600">·</span>
            {Math.round(clock.trip * 1000)} ms Latenz
          </span>
        {/if}
        <span class="flex items-center gap-1.5 text-[11px] font-medium {$connected ? 'text-zinc-400' : 'text-wu-red'}"
              title="Verbindung zum lokalen Backend">
          <span class="h-1.5 w-1.5 rounded-full {$connected ? 'bg-emerald-500' : 'animate-blink bg-wu-red'}"></span>
          {$connected ? 'lokal' : 'getrennt'}
        </span>
        <button onclick={toggleTheme} aria-label="Theme wechseln"
                class="grid h-8 w-8 place-items-center rounded-lg text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-white">
          {#if dark}
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
          {:else}
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>
          {/if}
        </button>
      </div>
    </div>
  </header>

  <main class="mx-auto w-full max-w-6xl flex-1 px-4 pt-6 pb-10 sm:px-6">
    <!-- ======================= Meldungen ======================= -->
    {#if $engine.logged_in === false}
      <div transition:fly={{ y: -8 }} role="alert"
           class="mb-6 flex items-center gap-3 rounded-xl border border-wu-red/30 bg-wu-red/5 px-4 py-3 text-sm font-medium text-wu-red">
        <span class="h-2 w-2 shrink-0 animate-blink rounded-full bg-wu-red"></span>
        LPIS hat dich ausgeloggt — im Bot-Browserfenster neu einloggen und die Kursseite wieder öffnen.
      </div>
    {/if}
    {#if error}
      <div transition:fly={{ y: -8 }} role="alert"
           class="mb-6 rounded-xl border border-wu-red/30 bg-wu-red/5 px-4 py-3 text-sm text-wu-red">
        {error}
      </div>
    {/if}

    <!-- ======================= Hero (nur im Leerlauf) ======================= -->
    {#if !$engine.running}
      <section transition:fade class="relative mb-10 overflow-hidden pt-6">
        <!-- dezentes Zielscheiben-Motiv rechts -->
        <svg viewBox="0 0 400 400" aria-hidden="true"
             class="pointer-events-none absolute -top-24 -right-16 hidden h-[420px] w-[420px] text-zinc-100 lg:block dark:text-zinc-900">
          <circle cx="200" cy="200" r="190" fill="none" stroke="currentColor" stroke-width="2" />
          <circle cx="200" cy="200" r="140" fill="none" stroke="currentColor" stroke-width="2" />
          <circle cx="200" cy="200" r="90" fill="none" stroke="currentColor" stroke-width="2" />
          <circle cx="200" cy="200" r="40" fill="none" stroke="currentColor" stroke-width="2" />
          <circle cx="200" cy="200" r="7" class="fill-wu/60" />
        </svg>
        <h1 class="relative max-w-xl text-4xl font-bold tracking-tight text-balance sm:text-5xl">
          Dein Wunschplatz,<br />
          <span class="text-wu">20&thinsp;ms</span> nach der Öffnung.
        </h1>
        <p class="mt-4 max-w-xl text-zinc-500 dark:text-zinc-400">
          kursfix gleicht deine Uhr mit dem WU-Zeitserver ab, hält die LPIS-Session frisch
          und klickt zur Öffnungssekunde den echten „anmelden“-Button deiner ersten freien
          Wunschgruppe. Lokal auf deinem Rechner, ohne gespeicherte Zugangsdaten.
        </p>
        <ol class="mt-8 grid gap-px overflow-hidden rounded-2xl border border-zinc-200 bg-zinc-200 sm:grid-cols-3 dark:border-zinc-800 dark:bg-zinc-800">
          {#each STEPS as [title, text], i}
            <li class="bg-white p-5 dark:bg-zinc-950">
              <span class="font-mono text-xs font-bold text-wu">0{i + 1}</span>
              <h3 class="mt-1 text-sm font-semibold">{title}</h3>
              <p class="mt-1 text-[13px] leading-relaxed text-zinc-500 dark:text-zinc-400">{text}</p>
            </li>
          {/each}
        </ol>
      </section>
    {/if}

    <!-- ======================= App-Bereich ======================= -->
    <div class="grid items-start gap-6 lg:grid-cols-[360px_1fr]">
      <aside class="flex flex-col gap-4 lg:sticky lg:top-20">
        <CourseEditor disabled={$engine.running} />

        <div class="flex gap-2">
          {#if $engine.running}
            <button onclick={() => run(stopEngine)} disabled={busy}
                    class="h-11 flex-1 rounded-xl bg-wu-red font-semibold text-white transition hover:bg-wu-red/90 active:scale-[0.99] disabled:opacity-50">
              Stop
            </button>
          {:else}
            <button onclick={() => run(() => startEngine(false))}
                    disabled={busy || !$connected || !hasCourses}
                    class="h-11 flex-1 rounded-xl bg-zinc-950 font-semibold text-white transition hover:bg-zinc-800 active:scale-[0.99] disabled:opacity-40 dark:bg-white dark:text-zinc-950 dark:hover:bg-zinc-200">
              Start
            </button>
            <button onclick={() => run(() => startEngine(true))}
                    disabled={busy || !$connected || !hasCourses}
                    title="Probe gegen einen lokalen Fake-LPIS — es geht nichts an die WU"
                    class="h-11 rounded-xl border border-zinc-300 px-4 font-medium text-zinc-700 transition hover:border-wu hover:text-wu active:scale-[0.99] disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-300 dark:hover:border-wu dark:hover:text-wu">
              Trockenlauf
            </button>
          {/if}
        </div>

        {#if $engine.running && $engine.dry_run}
          <p transition:fade class="flex items-center justify-center gap-2 text-xs font-medium text-wu">
            <span class="h-1.5 w-1.5 rounded-full bg-wu"></span>
            Trockenlauf — alles bleibt auf diesem Rechner.
          </p>
        {/if}
      </aside>

      <section class="flex min-w-0 flex-col gap-4">
        <Countdown />
        {#if $engine.courses.length}
          <div class="grid gap-4 xl:grid-cols-2">
            {#each $engine.courses as course (course.config.id)}
              <div transition:fly={{ y: 10 }}>
                <CourseCard {course} />
              </div>
            {/each}
          </div>
        {/if}
        <LogPanel />
      </section>
    </div>
  </main>

  <!-- ======================= Fußzeile ======================= -->
  <footer class="border-t border-zinc-200 py-5 dark:border-zinc-800">
    <p class="mx-auto max-w-6xl px-4 text-center text-xs text-zinc-400 sm:px-6">
      Inoffizielles Werkzeug, nicht von der WU Wien · läuft nur lokal · vorher WU-Regeln prüfen ·
      Nutzung auf eigenes Risiko ·
      <a href="https://github.com/LeonBinder/kursfix" class="underline-offset-2 transition hover:text-wu hover:underline">GitHub</a>
    </p>
  </footer>
</div>
