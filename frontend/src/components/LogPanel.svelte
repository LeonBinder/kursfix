<script>
  import { logs } from '../lib/ws.js'

  let box = $state(null)
  $effect(() => {
    $logs
    if (box) box.scrollTop = box.scrollHeight
  })

  function stamp(ts) {
    const d = new Date(ts * 1000)
    return d.toLocaleTimeString('de-AT') + '.' + String(d.getMilliseconds()).padStart(3, '0')
  }
</script>

<div class="rounded-2xl bg-white p-4 shadow-sm dark:bg-zinc-900">
  <h2 class="mb-2 font-semibold">Log</h2>
  <div bind:this={box} class="h-48 overflow-y-auto rounded-lg bg-zinc-50 p-2 font-mono text-xs leading-5 dark:bg-zinc-950">
    {#if !$logs.length}
      <p class="text-zinc-400">Noch nichts passiert.</p>
    {/if}
    {#each $logs as entry}
      <div class={entry.type === 'alarm' ? 'font-bold text-red-600 dark:text-red-400' : ''}>
        <span class="text-zinc-400">{stamp(entry.ts)}</span>
        {#if entry.course}<span class="text-sky-600 dark:text-sky-400"> [{entry.course}]</span>{/if}
        {entry.text}
      </div>
    {/each}
  </div>
</div>
