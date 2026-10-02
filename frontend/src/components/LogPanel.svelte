<script>
  import { slide } from 'svelte/transition'
  import { logs } from '../lib/ws.js'

  let open = $state(true)
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

<!-- Das Log als bewusst schwarzes Terminal-Element — auch im Light Mode -->
<div class="overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800">
  <button onclick={() => (open = !open)} aria-expanded={open}
          class="flex h-11 w-full items-center gap-2 px-4 text-left transition hover:bg-zinc-50 dark:hover:bg-zinc-900">
    <h2 class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Log</h2>
    {#if $logs.length}
      <span class="rounded-full bg-zinc-100 px-2 py-0.5 font-mono text-[10px] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
        {$logs.length}
      </span>
    {/if}
    <svg class="ml-auto h-3.5 w-3.5 text-zinc-400 transition-transform {open ? 'rotate-180' : ''}"
         viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg>
  </button>

  {#if open}
    <div transition:slide={{ duration: 150 }}>
      <div bind:this={box}
           class="{$logs.length ? 'h-52' : 'h-16'} overflow-y-auto bg-zinc-950 px-4 py-3 font-mono text-[11.5px] leading-[1.7] text-zinc-300 transition-all">
        {#if !$logs.length}
          <p class="text-zinc-600">Noch nichts passiert — nach dem Start erscheint hier jede Aktion.</p>
        {/if}
        {#each $logs as entry}
          <div class={entry.type === 'alarm' ? 'font-bold text-[#ff6b6b]' : ''}>
            <span class="text-zinc-600">{stamp(entry.ts)}</span>
            {#if entry.course}<span class="text-wu"> [{entry.course}]</span>{/if}
            <span class="ml-1">{entry.text}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
