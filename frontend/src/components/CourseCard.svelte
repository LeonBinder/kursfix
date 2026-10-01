<script>
  let { course } = $props()

  const PHASES = {
    idle: ['wartet', 'bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300'],
    waiting: ['Kursseite öffnen!', 'bg-amber-200 text-amber-900 dark:bg-amber-900 dark:text-amber-100'],
    preparing: ['liest Gruppen', 'bg-sky-200 text-sky-900 dark:bg-sky-900 dark:text-sky-100'],
    armed: ['ARMED', 'bg-violet-200 text-violet-900 dark:bg-violet-900 dark:text-violet-100'],
    firing: ['FEUERT', 'bg-orange-200 text-orange-900 dark:bg-orange-900 dark:text-orange-100'],
    done: ['fertig', 'bg-emerald-200 text-emerald-900 dark:bg-emerald-900 dark:text-emerald-100'],
    error: ['Fehler', 'bg-red-200 text-red-900 dark:bg-red-900 dark:text-red-100'],
  }
  const phase = $derived(PHASES[course.phase] ?? PHASES.idle)
  const resultTone = $derived(
    course.result.startsWith('angemeldet') || course.result.startsWith('bereits')
      ? 'text-emerald-600 dark:text-emerald-400'
      : course.result.includes('WARTELISTE')
        ? 'text-amber-600 dark:text-amber-400'
        : 'text-red-600 dark:text-red-400'
  )
</script>

<div class="rounded-2xl bg-white p-4 shadow-sm dark:bg-zinc-900">
  <div class="mb-2 flex items-center gap-2">
    <h3 class="truncate font-semibold">
      {course.name || course.config.label || course.config.groups.join(', ')}
    </h3>
    <span class="ml-auto shrink-0 rounded-full px-2 py-0.5 text-xs font-bold {phase[1]}">
      {phase[0]}
    </span>
  </div>

  {#if course.groups.length}
    <table class="w-full text-sm">
      <tbody>
        {#each course.groups as g (g.rank)}
          <tr class="border-t border-zinc-100 dark:border-zinc-800">
            <td class="py-1 pr-2 text-zinc-400">{g.rank}.</td>
            <td class="py-1 pr-2 font-mono">{g.id}</td>
            {#if g.on_page}
              <td class="max-w-28 truncate py-1 pr-2 text-zinc-500">{g.who}</td>
              <td class="py-1 pr-2 text-right font-mono tabular-nums">
                {g.free === null ? '–' : `${g.free} frei`}
              </td>
              <td class="py-1 text-right">
                {#if g.button}
                  <span class="rounded px-1.5 py-0.5 text-xs font-medium
                               {g.enabled ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200'
                                          : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400'}">
                    {g.button}{g.enabled ? '' : ' 🔒'}
                  </span>
                {:else}
                  <span class="text-xs font-semibold text-red-500">kein Button!</span>
                {/if}
              </td>
            {:else}
              <td colspan="3" class="py-1 text-xs text-red-500">
                nicht auf der Seite — Nummer prüfen
              </td>
            {/if}
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}

  {#if course.result}
    <p class="mt-2 text-sm font-semibold {resultTone}">{course.result}</p>
  {:else if course.message}
    <p class="mt-2 text-xs text-zinc-500">{course.message}</p>
  {/if}
</div>
