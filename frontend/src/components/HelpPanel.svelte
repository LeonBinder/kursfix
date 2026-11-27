<script>
  import { slide } from 'svelte/transition'

  let open = $state(false)

  const TOPICS = [
    {
      q: 'Gruppen & Priorität — wen klickt kursfix?',
      a: `Pro Kurs trägst du die 4-stelligen Gruppennummern aus der linken LPIS-Spalte ein,
          erste Wahl zuerst. Zur Öffnung lädt kursfix die Seite neu und klickt die erste
          Gruppe deiner Liste, die offen ist und freie Plätze zeigt. Schlägt ein Klick fehl,
          wird neu geladen und erneut geprüft — maximal 3 Versuche pro Gruppe, schnelle
          Wiederholungen nur in den ersten 2 Sekunden. Wichtig: Alle Gruppen EINES Kurses
          gehören in EINEN Eintrag, nicht auf mehrere verteilt.`,
    },
    {
      q: 'Warteliste an/aus — was heißt das genau?',
      a: `Die Warteliste greift nur, wenn ALLE deine Gruppen 0 freie Plätze zeigen.
          An (Standard): kursfix trägt dich dann in die Warteliste deiner ERSTEN Wahl ein
          und zeigt dir danach die freien Plätze der anderen Gruppen, falls du lieber von
          Hand wechselst. Aus: kursfix klickt keine volle Gruppe an, sondern beobachtet
          weiter — wird in den ersten 2 Minuten ein Platz frei (jemand meldet sich ab),
          schlägt es zu. Danach gibt es auf. Warteliste aus ist sinnvoll, wenn dir ein
          Wartelistenplatz nichts bringt oder er einen besseren Platz blockieren würde.`,
    },
    {
      q: 'Startzeit — wann muss ich sie setzen?',
      a: `Normalerweise nie: kursfix liest den Öffnungszeitpunkt („ab 28.09. 14:00“) direkt
          von der Kursseite. Nur wenn dort keiner steht, trägst du ihn manuell ein —
          als 14:00, 14:00:00 oder 28.09.2026 14:00 (Wiener Zeit). Eine gesetzte Startzeit
          hat immer Vorrang vor der Seite. Im Trockenlauf wird sie ignoriert.`,
    },
    {
      q: 'Der Ablauf — was passiert nach „Start“?',
      a: `1. Ein echtes Browserfenster öffnet sich mit der LPIS-Loginseite: dort loggst du
          dich selbst ein (WU-SSO) — kursfix sieht deine Zugangsdaten nie. 2. Du öffnest
          jede Kursseite (die mit den „anmelden“-Buttons) einmal; kursfix erkennt sie an
          den Gruppennummern und übernimmt sie in eigene Tabs. 3. Sobald ein Kurs ARMED
          meldet: Fenster in Ruhe lassen. kursfix hält die Session mit Reloads alle
          2 Minuten frisch, gleicht die Uhr mit timeserver.wu.ac.at ab und synchronisiert
          45 Sekunden vor der Öffnung noch einmal. 4. Nach dem Schuss steht das Ergebnis
          auf der Kurskarte — zur Sicherheit in der LPIS-Anmeldeliste gegenprüfen.`,
    },
    {
      q: 'Ausgeloggt? Das 30-Minuten-Problem',
      a: `Die WU verlangt nach ca. 30 Minuten einen frischen Login — deshalb erst
          15–25 Minuten vor der Öffnung starten. Fliegst du trotzdem raus, warnt kursfix
          mit Banner und Ton: einfach im Bot-Fenster neu einloggen und die betroffene
          Kursseite wieder öffnen. kursfix macht automatisch weiter, alle Einstellungen
          bleiben scharf.`,
    },
    {
      q: 'Erfolg, Warteliste oder Fehler — woran erkenne ich es?',
      a: `Angemeldet: Der Button der Gruppe wechselt zu „abmelden“, die Karte wird grün.
          Warteliste: LPIS meldet es im Klick-Ergebnis, die Karte zeigt WARTELISTE in Gold.
          „Kein Button gefunden“: LPIS hat sein Seitenlayout geändert — dann nicht auf
          kursfix verlassen und von Hand anmelden. „Aufgegeben“: 2 Minuten nach Öffnung
          ohne Erfolg; Nummern und Uhrzeit prüfen.`,
    },
    {
      q: 'Prüflauf — liest kursfix die echte Seite richtig?',
      a: `Der Prüflauf geht gegen das echte LPIS, klickt aber garantiert nichts: Du loggst
          dich ein und öffnest die Kursseiten wie beim Start; kursfix liest Gruppen, freie
          Plätze, Buttons und Öffnungszeit, gleicht die Uhr ab und meldet pro Kurs
          „geprüft“ oder das Problem. Ideal ein paar Stunden vor der Öffnung. Achtung:
          Ist eine Anmeldung schon offen, sagt dir der Prüflauf das — „Start“ würde dann
          sofort anmelden.`,
    },
    {
      q: 'Echt oder Fake — wogegen läuft es gerade?',
      a: `Unter den Buttons steht während jedes Laufs der Modus: ECHTES LPIS (rot, es wird
          wirklich angemeldet), PRÜFLAUF (gold, echtes LPIS, nur lesen) oder TROCKENLAUF
          (lokaler Fake). Zusätzlich: Die Adresszeile im Bot-Fenster zeigt lpis.wu.ac.at
          bzw. 127.0.0.1, die erste Logzeile nennt das Ziel, und nur das echte LPIS
          verlangt deinen WU-Login.`,
    },
    {
      q: 'Trockenlauf — gefahrlos üben',
      a: `Der Trockenlauf baut einen Fake-LPIS mit genau deinen Kursen auf diesem Rechner
          (Öffnung nach 60 Sekunden) und spielt alles durch: Login-Klick, Kursseiten
          öffnen, Countdown, Anmeldung. Es verlässt kein einziger Request deinen Rechner —
          ideal, um den Ablauf einmal gesehen zu haben, bevor es zählt.`,
    },
  ]
</script>

<div class="overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800">
  <button onclick={() => (open = !open)} aria-expanded={open}
          class="flex h-11 w-full items-center gap-2 px-4 text-left transition hover:bg-zinc-50 dark:hover:bg-zinc-900">
    <h2 class="text-[11px] font-semibold tracking-[0.2em] text-zinc-400 uppercase">Hilfe</h2>
    <span class="text-[11px] text-zinc-400">Warteliste, Priorität, Ablauf</span>
    <svg class="ml-auto h-3.5 w-3.5 text-zinc-400 transition-transform {open ? 'rotate-180' : ''}"
         viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg>
  </button>

  {#if open}
    <div transition:slide={{ duration: 150 }} class="border-t border-zinc-200 dark:border-zinc-800">
      {#each TOPICS as topic, i}
        <details class="group border-zinc-200 dark:border-zinc-800 {i > 0 ? 'border-t' : ''}">
          <summary class="flex cursor-pointer items-center gap-2 px-4 py-2.5 text-[13px] font-medium transition select-none hover:text-wu [&::-webkit-details-marker]:hidden">
            <span class="text-wu transition-transform group-open:rotate-90">›</span>
            {topic.q}
          </summary>
          <p class="px-4 pb-3 pl-7 text-[13px] leading-relaxed text-zinc-500 dark:text-zinc-400">
            {topic.a}
          </p>
        </details>
      {/each}
    </div>
  {/if}
</div>
