<script>
  import { config, saveConfigSoon } from '../lib/ws.js'

  let { disabled = false } = $props()
  // Rohtext der Gruppen-Eingabe pro Kurs, damit Tippen nicht normalisiert wird
  let drafts = $state({})

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
</script>

<div class="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-sm dark:bg-zinc-900">
  <div class="flex items-center justify-between">
    <h2 class="font-semibold">Kurse</h2>
    <button onclick={addCourse} {disabled}
            class="rounded-lg bg-zinc-100 px-2.5 py-1 text-sm font-medium hover:bg-zinc-200 disabled:opacity-40 dark:bg-zinc-800 dark:hover:bg-zinc-700">
      + Kurs
    </button>
  </div>

  {#if !$config.courses.length}
    <p class="text-sm text-zinc-500">
      Noch keine Kurse. „+ Kurs“ drücken und die 4-stelligen Gruppennummern aus der
      linken LPIS-Spalte eintragen — erste Wahl zuerst.
    </p>
  {/if}

  {#each $config.courses as course (course.id)}
    <div class="flex flex-col gap-2 rounded-xl border border-zinc-200 p-3 dark:border-zinc-700">
      <div class="flex items-center gap-2">
        <input value={course.label} {disabled} placeholder="Name (optional)"
               oninput={(e) => update(course.id, 'label', e.target.value)}
               class="w-full rounded-lg border border-zinc-300 bg-transparent px-2 py-1 text-sm dark:border-zinc-600" />
        <button onclick={() => removeCourse(course.id)} {disabled} aria-label="Kurs entfernen"
                class="shrink-0 rounded-lg px-2 py-1 text-sm text-zinc-400 hover:bg-red-50 hover:text-red-600 disabled:opacity-40 dark:hover:bg-red-950">
          ✕
        </button>
      </div>
      <input value={drafts[course.id] ?? course.groups.join(', ')} {disabled}
             placeholder="Gruppen, z. B. 1111, 1112, 1113"
             oninput={(e) => setGroups(course.id, e.target.value)}
             class="rounded-lg border border-zinc-300 bg-transparent px-2 py-1 font-mono text-sm dark:border-zinc-600" />
      <div class="flex items-center gap-3">
        <input value={course.start_at ?? ''} {disabled}
               placeholder="Startzeit, z. B. 14:00 (leer = von LPIS lesen)"
               oninput={(e) => update(course.id, 'start_at', e.target.value.trim() || null)}
               class="w-full rounded-lg border border-zinc-300 bg-transparent px-2 py-1 text-sm dark:border-zinc-600" />
        <label class="flex shrink-0 items-center gap-1.5 text-sm text-zinc-600 dark:text-zinc-300">
          <input type="checkbox" checked={course.waitlist} {disabled}
                 onchange={(e) => update(course.id, 'waitlist', e.target.checked)}
                 class="accent-emerald-600" />
          Warteliste
        </label>
      </div>
    </div>
  {/each}

  <label class="flex items-center gap-1.5 text-xs text-zinc-500">
    <input type="checkbox" checked={$config.save_snapshots} {disabled}
           onchange={(e) => { config.update((c) => ({ ...c, save_snapshots: e.target.checked })); saveConfigSoon() }}
           class="accent-emerald-600" />
    HTML-Snapshots speichern (enthalten Name + Matrikelnr., bleiben lokal in data/)
  </label>
</div>
