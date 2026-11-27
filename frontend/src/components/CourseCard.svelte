<script>
  let { course } = $props()

  // Phasen in der WU-Palette: Petrol = scharf, Gold = feuert, Grün = fertig, Rot = Fehler
  const PHASES = {
    idle: ['wartet', 'text-zinc-500 border-zinc-300 dark:border-zinc-600', 'bg-zinc-400'],
    waiting: ['Kursseite öffnen', 'text-wu-gold border-wu-gold/40', 'animate-blink bg-wu-gold'],
    preparing: ['liest Gruppen', 'text-wu border-wu/40', 'animate-blink bg-wu'],
    armed: ['ARMED', 'text-wu border-wu/40', 'bg-wu'],
    firing: ['FEUERT', 'text-wu-gold border-wu-gold/40', 'animate-blink bg-wu-gold'],
    done: ['fertig', 'text-wu-green border-wu-green/40 dark:text-emerald-400', 'bg-wu-green dark:bg-emerald-400'],
    error: ['Fehler', 'text-wu-red border-wu-red/40', 'bg-wu-red'],
  }
  const phase = $derived(PHASES[course.phase] ?? PHASES.idle)
  const resultTone = $derived(
    /^(angemeldet|bereits|geprüft)/.test(course.result)
      ? 'text-wu-green dark:text-emerald-400'
      : course.result.includes('WARTELISTE')
        ? 'text-wu-gold'
        : 'text-wu-red'
  )
</script>

<div class="flex h-full flex-col rounded-2xl border border-zinc-200 p-4 transition-colors dark:border-zinc-800
            {['armed', 'firing'].includes(course.phase) ? 'border-wu/40 dark:border-wu/40' : ''}">
  <div class="mb-3 flex items-center gap-2">
    <h3 class="truncate font-semibold tracking-tight">
      {course.name || course.config.label || course.config.groups.join(', ')}
    </h3>
    <span class="ml-auto flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-bold tracking-wide {phase[1]}">
      <span class="h-1.5 w-1.5 rounded-full {phase[2]}"></span>
      {phase[0]}
    </span>
  </div>

  {#if course.groups.length}
    <ul class="divide-y divide-zinc-100 text-sm dark:divide-zinc-800/80">
      {#each course.groups as g (g.rank)}
        <li class="flex items-center gap-2.5 py-1.5">
          <span class="grid h-5 w-5 shrink-0 place-items-center rounded-md text-[11px] font-bold
                       {g.rank === 1 ? 'bg-wu/10 text-wu' : 'bg-zinc-100 text-zinc-400 dark:bg-zinc-800'}">
            {g.rank}
          </span>
          <span class="font-mono font-medium tabular-nums">{g.id}</span>
          {#if g.on_page}
            <span class="min-w-0 flex-1 truncate text-[13px] text-zinc-400">{g.who}</span>
            <span class="font-mono text-[13px] tabular-nums {g.free === 0 ? 'text-wu-red' : 'text-zinc-500 dark:text-zinc-400'}">
              {g.free === null ? '' : `${g.free} frei`}
            </span>
            {#if /abmelden|deregist/i.test(g.button)}
              <!-- Button zeigt „abmelden“ = hier bist du angemeldet -->
              <span class="shrink-0 rounded-md bg-wu-green/10 px-1.5 py-0.5 text-[11px] font-bold text-wu-green dark:bg-emerald-400/10 dark:text-emerald-400">
                ✓ angemeldet
              </span>
            {:else if g.button}
              <span class="shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-medium
                           {g.enabled
                             ? 'bg-wu-green/10 text-wu-green dark:bg-emerald-400/10 dark:text-emerald-400'
                             : 'bg-zinc-100 text-zinc-400 dark:bg-zinc-800 dark:text-zinc-500'}">
                {g.enabled ? g.button : `${g.button} · gesperrt`}
              </span>
            {:else}
              <span class="shrink-0 text-[11px] font-semibold text-wu-red">kein Button!</span>
            {/if}
          {:else}
            <span class="flex-1 text-right text-[12px] text-wu-red">nicht auf der Seite — Nummer prüfen</span>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}

  {#if course.result}
    <p class="mt-auto pt-3 text-sm font-semibold {resultTone}">{course.result}</p>
  {:else if course.message}
    <p class="mt-auto pt-3 text-xs text-zinc-400">{course.message}</p>
  {/if}
</div>
