<script>
  import { fade, slide } from 'svelte/transition'
  import { config, saveConfigSoon, saveState } from '../lib/ws.js'

  let { disabled = false } = $props()
  // Rohtext der Gruppen-Eingabe pro Kurs, damit Tippen nicht normalisiert wird
  let drafts = $state({})

  const TIME_RE = /^(\d{1,2}\.\d{1,2}\.\d{4}\s+)?\d{1,2}:\d{2}(:\d{2})?$/

  function update(id, field, value) {
    config.update((c) => {
      const course = c.courses.find((x) => x.id === id)
      if (course) course[field] = value
      return { ...c }
    })
    saveConfigSoon()
  }

  function setGroups(id, text) {
    drafts[id] = text
    update(id, 'groups', text.split(',').map((g) => g.trim()).filter(Boolean))
  }

  function addCourse() {
    config.update((c) => ({
      ...c,
      courses: [...c.courses, {
        id: crypto.randomUUID(), label: '', groups: [], start_at: null, waitlist: true,
      }],
    }))
    saveConfigSoon()
  }

  function removeCourse(id) {
    delete drafts[id]
    config.update((c) => ({ ...c, courses: c.courses.filter((x) => x.id !== id) }))
    saveConfigSoon()
  }

  const inputClass = 'w-full rounded-lg border border-zinc-200 bg-transparent px-2.5 py-1.5 text-sm ' +
    'placeholder:text-zinc-400 transition focus:border-wu dark:border-zinc-700 dark:placeholder:text-zinc-600'
</script>

<div class="rounded-2xl border border-zinc-200 dark:border-zinc-800">
  <div class="flex h-11 items-center gap-2 border-b border-zinc-200 px-4 dark:border-zinc-800">
    <h2 class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Kurse</h2>
    {#if $saveState !== 'idle'}
      <span transition:fade={{ duration: 150 }} class="text-[11px] text-zinc-400">
        {$saveState === 'saving' ? 'speichert …' : '✓ gespeichert'}
      </span>
    {/if}
    <button onclick={addCourse} {disabled}
            class="ml-auto rounded-lg px-2 py-1 text-sm font-semibold text-wu transition hover:bg-wu/10 disabled:opacity-40">
      + Kurs
    </button>
  </div>

  <div class="flex flex-col gap-3 p-4">
    {#if !$config.courses.length}
      <p class="py-2 text-[13px] leading-relaxed text-zinc-400">
        Noch keine Kurse. Mit <span class="font-semibold text-wu">+ Kurs</span> anfangen und die
        4-stelligen Gruppennummern aus der linken LPIS-Spalte eintragen — erste Wahl zuerst.
      </p>
    {/if}

    {#each $config.courses as course, i (course.id)}
      <fieldset transition:slide={{ duration: 150 }} {disabled}
                class="group rounded-xl border border-zinc-200 p-3 transition-colors focus-within:border-wu/50 disabled:opacity-60 dark:border-zinc-800">
        <div class="flex items-center gap-2">
          <input value={course.label} placeholder="Kurs {i + 1} — Name (optional)"
                 oninput={(e) => update(course.id, 'label', e.target.value)}
                 class="{inputClass} font-medium" />
          <button onclick={() => removeCourse(course.id)} aria-label="Kurs entfernen"
                  class="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-zinc-300 transition hover:bg-wu-red/10 hover:text-wu-red disabled:pointer-events-none dark:text-zinc-600">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <input value={drafts[course.id] ?? course.groups.join(', ')}
               placeholder="Gruppen: 1111, 1112, 1113"
               title="Die 4-stelligen Nummern aus der linken LPIS-Spalte, erste Wahl zuerst. Alle Gruppen EINES Kurses in EIN Feld."
               oninput={(e) => setGroups(course.id, e.target.value)}
               class="{inputClass} mt-2 font-mono" />
        {#if course.groups.length}
          <div class="mt-2 flex flex-wrap items-center gap-1" aria-label="Prioritätsreihenfolge">
            {#each course.groups as g, rank}
              {#if rank > 0}<span class="text-[10px] text-zinc-300 dark:text-zinc-600">→</span>{/if}
              <span class="rounded-md px-1.5 py-0.5 font-mono text-[11px] font-medium
                           {rank === 0 ? 'bg-wu/10 text-wu' : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400'}">
                {g}
              </span>
            {/each}
          </div>
        {/if}

        <div class="mt-2 flex items-center gap-3">
          <input value={course.start_at ?? ''}
                 placeholder="Startzeit 14:00 (leer = LPIS)"
                 title="Nur nötig, wenn LPIS keine Öffnungszeit anzeigt. Hat sonst Vorrang vor der Seite. Formate: 14:00, 14:00:00, 28.09.2026 14:00 (Wiener Zeit)."
                 oninput={(e) => update(course.id, 'start_at', e.target.value.trim() || null)}
                 class="{inputClass} {course.start_at && !TIME_RE.test(course.start_at) ? 'border-wu-red focus:border-wu-red' : ''}" />
          <label class="flex shrink-0 cursor-pointer items-center gap-1.5 text-[13px] text-zinc-500 dark:text-zinc-400"
                 title="Wenn ALLE Gruppen voll sind: an = Warteliste der ersten Wahl nehmen; aus = weiter auf frei werdende Plätze lauern (2 Minuten), dann aufgeben.">
            <input type="checkbox" checked={course.waitlist}
                   onchange={(e) => update(course.id, 'waitlist', e.target.checked)}
                   class="accent-[#0b80a7]" />
            Warteliste
          </label>
        </div>
        {#if course.start_at && !TIME_RE.test(course.start_at)}
          <p transition:slide={{ duration: 100 }} class="mt-1.5 text-[11px] text-wu-red">
            Format: 14:00, 14:00:00 oder 28.09.2026 14:00
          </p>
        {/if}
      </fieldset>
    {/each}

    {#if $config.courses.length}
      <label class="flex cursor-pointer items-center gap-1.5 text-[11px] text-zinc-400">
        <input type="checkbox" checked={$config.save_snapshots} {disabled}
               onchange={(e) => { config.update((c) => ({ ...c, save_snapshots: e.target.checked })); saveConfigSoon() }}
               class="accent-[#0b80a7]" />
        HTML-Snapshots speichern (enthalten Name + Matrikelnr., bleiben lokal in data/)
      </label>
    {/if}
  </div>
</div>
