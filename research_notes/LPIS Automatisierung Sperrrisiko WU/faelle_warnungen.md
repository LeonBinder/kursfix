# Dokumentierte Fälle, offizielle Warnungen und Community-Berichte zu LPIS-Bots an der WU Wien (Stand: 27.11.2026)

Hinweis zur Methode: Recherche per Websuche, direktem Abruf von Seiten und GitHub-REST-API (das `gh`-CLI war nicht installiert). Einstufung der Belege jeweils in Klammern: **[offiziell]**, **[Anbieterangabe]**, **[Entwicklerangabe]**, **[Erfahrungsbericht]**, **[Hörensagen]**, **[nur Such-Snippet, Seite nicht selbst gelesen]**. Alle GitHub-Zahlen (Sterne, Forks, Daten) wurden am 27.11.2026 abgerufen.

## 1. Gibt es eine offizielle Warnung von WU (Vizerektorat Lehre, Studienservices, IT-SERVICES) oder ÖH WU zu Bots/Skripten?

### Takeaway
Die einzige gefundene offizielle Aussage ist ein Hinweis auf der LPIS-Seite der WU: Anmeldung nur direkt über LPIS, bei "Nicht-WU-Software" keine Garantie, kein Support und keine Nachmeldung. Der Text nennt weder "Bot" noch "Skript" und droht keine Sperre, Abmeldung oder disziplinäre Folge an. Von der ÖH WU wurde gar nichts gefunden.

### Cited Findings
- **[offiziell]** WU, Seite "LPIS registration system" (englische Fassung, ohne Datum, Footer "© 2026"): "Please only register for courses and exams directly via LPIS." / "If you use non-WU software, we cannot guarantee that your registration will work." / "Neither support nor re- registrations are provided for problems caused using any other application than LPIS." — [WU: LPIS registration system](https://www.wu.ac.at/en/students/getting-organized/lpis-registration-system)
- **[offiziell]** Dieselbe Seite enthält laut Abruf keinerlei Erwähnung von Bots, Skripten, automatisierter Anmeldung oder Sanktionen; die genannte Folge ist ausschließlich der Wegfall von Garantie, Support und Nachmeldung. — [WU: LPIS registration system](https://www.wu.ac.at/en/students/getting-organized/lpis-registration-system)
- **[offiziell]** Zur Platzvergabe nennt dieselbe Seite für Wartelisten: "Places on the waiting list are assigned either on a first-come, first-served basis or based on the student's academic progress." — [WU: LPIS registration system](https://www.wu.ac.at/en/students/getting-organized/lpis-registration-system)
- **[Anbieterangabe]** Ein kommerzieller Bot-Anbieter verweist selbst darauf, dass die WU Regeln haben könne, ohne eine konkrete Regel zu zitieren: "Eigene Regeln für Hilfsprogramme legt die WU fest." sowie "Kein Angebot der WU und nicht mit ihr verbunden." — [lpisbot.app](https://www.lpisbot.app/)

### Inferences
- Die WU-Formulierung ist ein Haftungs- und Supportausschluss, kein ausdrückliches Verbot mit Sanktionsandrohung. Dass die WU überhaupt "non-WU software" adressiert, zeigt aber, dass ihr Fremdsoftware für die Anmeldung bekannt ist.
- Das praktisch relevante, offiziell benannte Risiko ist: Geht eine Anmeldung durch ein Fremdtool schief, gibt es keine Nachmeldung.
- Ob andere WU-Regelwerke (Satzung, IT-Benutzungsordnung) automatisierte Zugriffe erfassen, war nicht Teil dieser Recherche und wurde in keiner Fundstelle zitiert.

### Gaps
- Die deutsche Fassung der WU-LPIS-Seite konnte nicht abgerufen werden (zwei geratene URLs lieferten 404); der deutsche Originalwortlaut des Hinweises ist daher nicht belegt.
- Seit wann der Hinweis auf der WU-Seite steht, ist unbekannt (kein Seitendatum, keine Archivprüfung durchgeführt).
- ÖH WU: Suche nach Warnungen, FAQ oder Posts zu LPIS-Bots (inkl. forum.oeh-wu.at) ergab keinen Treffer. Die Seiten der ÖH WU und ihre Social-Media-Kanäle wurden nicht systematisch direkt durchsucht, nur über Websuche.
- Newsletter, Rundmails an Studierende und Social-Media-Posts der WU sind über Websuche nicht auffindbar; ihre Existenz kann weder bestätigt noch ausgeschlossen werden.

## 2. Gibt es Medienberichte über Anmeldebots an der WU oder anderen österreichischen Universitäten?

### Takeaway
Es wurde kein einziger Medienbericht (Standard, Presse, ORF, Kurier, Falter, futurezone, unimag) über LPIS-Bots oder eine Reaktion der WU darauf gefunden. Die Suchtreffer bestehen fast nur aus Anbieterseiten und GitHub-Projekten.

### Cited Findings
- **[Negativbefund]** Mehrere Suchanfragen mit Medien- und Schlagwortkombinationen ("Anmelde-Bot", "Bots", "Skript", WU, LPIS, Standard/Presse/ORF/Kurier/futurezone) lieferten keine Presseartikel, sondern Anbieterseiten wie [wubot.at](https://www.wubot.at/), [lpisbot.app](https://www.lpisbot.app/), [semestria.at](https://semestria.at/en), [lpisninja.at](https://lpisninja.at/) und GitHub-Repos.
- **[nur Such-Snippet]** Ein älterer Artikel der Wiener Zeitung beschreibt laut Suchergebnis ausgebuchte Kurse, Wartelisten und Serverausfälle bei der Anmeldung nach dem Prinzip "wer zuerst kommt"; Bots werden im Snippet nicht erwähnt, das Datum ist unklar. — [Wiener Zeitung: Wenn das Studium zur Farce wird](https://www.wienerzeitung.at/h/wenn-das-studium-zur-farce-wird)
- **[nur Such-Snippet, kein Bot-Bezug]** Der einzige Medien-Treffer zu "Sperren" an einer Wiener Uni betrifft Prüfungssperren der Uni Wien für unentschuldigtes Fernbleiben, nicht Bots. — [wien.ORF.at: Uni Wien verhängt Prüfungssperren](https://wien.orf.at/v2/news/stories/2733189/)

### Inferences
- Das Thema ist medial offenbar nicht aufgegriffen worden; ein öffentlich gewordener Sanktionsfall hätte mit einiger Wahrscheinlichkeit Spuren hinterlassen, das ist aber kein Beweis für das Fehlen von Fällen.

### Gaps
- Paywall-Archive (Presse, Falter, APA) wurden nicht durchsucht. Die Websuche war laut Tool-Hinweis US-basiert, was die Abdeckung österreichischer Medien einschränken kann.

## 3. Was sagen Foren und soziale Medien über Erwischtwerden, Sperren, Abmeldungen?

### Takeaway
Es wurde kein einziger Erfahrungsbericht aus erster Hand über eine Sperre, Abmeldung oder Disziplinarmaßnahme wegen eines LPIS-Bots gefunden. Gefunden wurden nur ein Erfahrungsbericht, der die Existenz von Bots beklagt, und ein vager Hörensagen-Hinweis aus einem TU-Forum von 2015.

### Cited Findings
- **[Erfahrungsbericht, WU-Studierender]** StudyCheck-Bericht zum WiSo-Bachelor der WU, geschrieben 15.01.2026, veröffentlicht 20.01.2026: "aber da auf Grund einiger kluger Köpfe mittlerweile sogar schon anmelde Bots im Umlauf sind" ... "hilft die Sekunde genaue Anmeldung auch oft nicht" ... "und es macht es beinahe unmöglich in der mindeststudienzeit abzuschließen." Keine Aussage zu Konsequenzen für Bot-Nutzer. — [StudyCheck, Bericht 773302](https://www.studycheck.de/studium/sozialwissenschaften/wu-wien-27675/bericht-773302)
- **[Hörensagen, nur Such-Snippet]** In einem Thread des Informatik-Forums der TU Wien (2015) zu TISS-Anmeldeskripten schreibt laut Suchzusammenfassung ein Poster, ein ähnliches Tool sei an WU und Uni Wien stark genutzt worden und es habe "Ärger" gegeben, ohne Details; Bots zur Vorteilsverschaffung seien eine nicht vorgesehene Nutzung; die TUNET-Benutzungsordnung verbiete Automatisierung nach Lesart des Posters nicht eindeutig. — [informatik-forum.at, Thread 110876](https://www.informatik-forum.at/forum/index.php?thread%2F110876-tiss-hacks-lva-anmeldung-automatisch-mit-script%2F=)
- **[Negativbefund]** Gezielte Suchen nach Reddit-Beiträgen (WU, LPIS, Bot, erwischt/gesperrt/abgemeldet/banned/caught) lieferten keinen Thread zu Konsequenzen; einziger Reddit-Treffer war laut Suchergebnis ein r/wien-Thread zur manuellen LPIS-Anmeldung ohne Bot-Bezug (URL wurde vom Suchtool nicht ausgegeben).

### Inferences
- Die öffentliche Beleglage zu Sanktionen ist leer: weder bestätigte noch glaubhaft geschilderte Einzelfälle. Das spricht für seltene oder nicht öffentlich gemachte Durchsetzung, belegt aber nicht, dass es keine gibt.
- Der StudyCheck-Bericht zeigt, dass Bots unter Studierenden als Fairnessproblem wahrgenommen werden; das erhöht die Wahrscheinlichkeit von Beschwerden an WU/ÖH.

### Gaps
- Der TU-Forenthread konnte nicht abgerufen werden (TLS-Zertifikatsfehler); der Wortlaut und was mit "Ärger" gemeint war, sind unverifiziert.
- Reddit wurde nur indirekt über Websuche abgefragt, nicht über die Reddit-Suche selbst. Jodel, Studo-Chats, WhatsApp-/Facebook-Gruppen und das ÖH-WU-Forum sind nicht öffentlich indexiert bzw. lieferten keine Treffer; dort können Berichte existieren.

## 4. Was sagen GitHub-Projekte (READMEs, Issues) über Erkennung, Sperren, Warnungen? Wie alt und verbreitet sind sie?

### Takeaway
Öffentliche LPIS-Bots gibt es mindestens seit 2018; alle sind winzig (maximal 23 Sterne, meist 0 bis 5). In keinem README und keinem Issue wird eine Sperre, Abmeldung, Verwarnung oder Erkennung durch die WU berichtet; Issues betreffen ausschließlich technische Defekte nach LPIS-Änderungen.

### Cited Findings
Repository-Metadaten (GitHub-API, 27.11.2026):

| Repo | Sterne / Forks | erstellt | letzter Push | Anmerkung |
|---|---|---|---|---|
| [alexanderhofstaetter/wu-lpis-api](https://github.com/alexanderhofstaetter/wu-lpis-api) | 23 / 7 | 2018-09-20 | 2020-01-24 | Python/mechanize, Kern der Web-Anwendung "Flips"; 5 offene Issues |
| [nicospacez/WUstus](https://github.com/nicospacez/WUstus) | 5 / 0 | 2018-08-21 | 2025-01-26 | Chrome-Extension; README trägt Badge "broken" |
| [MoritzRenkin/wu-lpis-automation](https://github.com/MoritzRenkin/wu-lpis-automation) | 5 / 0 | 2022-08-22 | 2022-11-25 | README-Titel "LPIS Skript [DEPRECATED]", ohne Begründung |
| [PreyMa/WU-LPIS-bot](https://github.com/PreyMa/WU-LPIS-bot) | 5 / 0 | 2022-08-26 | 2023-09-23 | Tampermonkey-Userscript |
| [TimWriter/lpis_registration_tool](https://github.com/TimWriter/lpis_registration_tool) | 0 / 0 | 2022-10-18 | 2022-10-18 | |
| [schneiseb/LPIS-Bot](https://github.com/schneiseb/LPIS-Bot) | 0 / 0 | 2023-08-20 | 2024-09-04 | |
| [Alexander070702/Wu-Lpis-Bot](https://github.com/Alexander070702/Wu-Lpis-Bot) | 0 / 0 | 2023-09-11 | 2023-09-11 | |
| [blueqwertz/wu-lpis-api](https://github.com/blueqwertz/wu-lpis-api) | 1 / 0 | 2024-04-17 | 2026-11-16 | aktiv gepflegte Variante der wu-lpis-api |
| [rafaelmohr/lpis-registration-script](https://github.com/rafaelmohr/lpis-registration-script) | 1 / 0 | 2025-09-02 | 2025-09-02 | Userscript, Fork des TISS Quick Registration Script |
| [discreteagent/wu-lpis-bot](https://github.com/discreteagent/wu-lpis-bot) | 0 / 0 | 2026-09-28 | 2026-09-28 | keine Issues |
| [semestria-at/semestria-lpis-bot](https://github.com/semestria-at/semestria-lpis-bot) | 1 / 0 | 2026-10-15 | 2026-10-15 | nur Produktinfos eines kommerziellen Anbieters, kein Quellcode |

- **[Entwicklerangabe]** discreteagent/wu-lpis-bot, Disclaimer im README: "Unofficial and not affiliated with WU Wien. Check WU's rules before using automated registration; you use it on your own account and at your own risk." Kein Hinweis auf bekannte Sanktionen. — [discreteagent/wu-lpis-bot](https://github.com/discreteagent/wu-lpis-bot)
- **[Entwicklerangabe]** Dasselbe README beschreibt bewusst schonendes Verhalten ("Gentle on LPIS: one session, one page load per attempt; quick retries (every 0.15 s) only during the first 2 seconds") und das Klicken des echten Buttons im Browser. — [discreteagent/wu-lpis-bot](https://github.com/discreteagent/wu-lpis-bot)
- **[Entwicklerangabe]** PreyMa/WU-LPIS-bot: "The whole system is intended to emulate a user with superhuman reflexes and mouse clicking speed, somewhat like a 'fancy' autoclicker." und der Bot nutze nicht "the LPIS API or any endpoints, it simply interacts with the user-interface like a regular user would." Die "Warning"-Box im README betrifft nur die Bedienung (Tab offen lassen), nicht Sanktionen. — [PreyMa/WU-LPIS-bot](https://github.com/PreyMa/WU-LPIS-bot)
- **[Entwicklerangabe]** alexanderhofstaetter/wu-lpis-api: Alle fünf Issues (2020 bis 2024) sind Funktionsfragen und Fehlermeldungen ("no control matching name 'ASPP'"); der Autor antwortete am 06.08.2021 auf die Frage, ob es noch funktioniere: "schon länger nicht getestet, aber da LPIS nicht lebt, sollte es schon funktionieren". Keine Erwähnung von Sperren oder WU-Kontakt. — [wu-lpis-api Issues](https://github.com/alexanderhofstaetter/wu-lpis-api/issues)
- **[Negativbefund]** Die Repos discreteagent, PreyMa, MoritzRenkin, WUstus und rafaelmohr haben keine Issues; blueqwertz hat nur ein technisches Issue und zwei technische PRs (2026). In den per Schlagwortsuche (Sperre, ban, detect, risk, Disclaimer, captcha usw.) geprüften READMEs findet sich außer dem oben zitierten Disclaimer nichts zu Erkennung oder Sanktionen. — [blueqwertz/wu-lpis-api](https://github.com/blueqwertz/wu-lpis-api)

Kommerzielle Anbieter (zur Einordnung der Verbreitung):
- **[Anbieterangabe]** LPIS Ninja wirbt mit "200+ Studierende vertrauen LPIS Ninja" und "98% Erfolgsquote bei 400+ Anmeldungen"; die FAQ-Überschrift "Ist das erlaubt?" ist vorhanden, die Antwort war beim Abruf nicht lesbar. — [lpisninja.at](https://lpisninja.at/)
- **[Anbieterangabe]** WuBot: "40+ Studenten lieben WuBot", "Zusätzlich ist WuBot nicht nachverfolgbar.", "Nicht verbunden mit der Wirtschaftsuniversität Wien."; keine Aussage zu Erlaubtheit oder Sperrrisiko. — [wubot.at](https://www.wubot.at/)
- **[Anbieterangabe]** LPIS Bot: "Höchstens etwa eine Anfrage pro Sekunde über eine einzige Verbindung", "keine Tricks an Sicherheitsabfragen vorbei", "Keine Garantie auf einen Fixplatz."; keine Angabe zu Sperren. — [lpisbot.app](https://www.lpisbot.app/)
- **[Anbieterangabe]** Semestria (Semestria e.U., Wien): Desktop-App, Login durch den Nutzer im App-Browser inklusive Microsoft; die FAQ enthält keine Aussage zu WU-Regeln, Sperrrisiko oder Erkennung. — [semestria.at FAQ](https://semestria.at/faq-en)

### Inferences
- Rund acht Jahre öffentliche Bot-Projekte plus mehrere zahlungspflichtige Dienste mit (selbst behaupteten) dutzenden bis hunderten Nutzern, ohne einen einzigen dokumentierten Sanktionsfall, deuten darauf hin, dass die WU bisher nicht sichtbar gegen einzelne Nutzer vorgeht. Die Anbieterzahlen sind unbelegt und werblich.
- Die Aussage "nicht nachverfolgbar" (WuBot) ist eine unbelegte Werbebehauptung; serverseitig sind Zeitpunkt und Muster von Requests grundsätzlich protokollierbar.
- Die geringe Sternezahl bedeutet nicht geringe Nutzung: Userscripts und EXE-Dateien werden typischerweise privat weitergegeben.

### Gaps
- Die Seiten zweier weiterer Anbieter (get-botz.com "WU Bot", learn-easy.at "WU LPIS Bot") tauchten in Suchergebnissen auf, waren aber nicht abrufbar (DNS-Fehler); Inhalte ungeprüft.
- [Alex8734/Lpis_Autopilot](https://github.com/Alex8734/Lpis_Autopilot) erschien in der Websuche, die API lieferte keine Metadaten (möglicherweise gelöscht oder privat).
- GitHub-Codesuche und Discussions wurden nicht durchsucht (API ohne Authentifizierung); Forks mit eigenen Hinweisen wurden nicht einzeln geprüft.

## 5. Hat die WU LPIS als Reaktion auf Bots verändert (Seed/Hidden-Felder, Queue, Zufallsvergabe, Warteraum)?

### Takeaway
Belegt sind technische Änderungen an LPIS, die Bots erschweren oder brechen (zufällige Formularfelder, dynamische Feldnamen, Umstellung auf Microsoft-Login mit 2FA). Eine offizielle Aussage der WU, dass diese Änderungen gegen Bots gerichtet sind, wurde nicht gefunden; ebenso kein Hinweis auf Warteraum, Queue oder Zufallsvergabe.

### Cited Findings
- **[Entwicklerangabe]** LPIS-Seiten enthalten pro Seitenaufruf zufällige Felder: "the per-page random fields (`seed`, a randomly named hidden input) that break bots which build requests themselves." — [discreteagent/wu-lpis-bot README](https://github.com/discreteagent/wu-lpis-bot)
- **[Nutzerbeobachtung in Issue, 06.02.2024]** "Der Name des Dropdownfeldes dürfte dynamisch vergeben werden. Jedes mal nach dem Einloggen steht was anderes bei name." Der zugehörige Fehler ("no control matching name 'ASPP'") ist seit 09.08.2021 gemeldet. — [wu-lpis-api Issue #3/#4](https://github.com/alexanderhofstaetter/wu-lpis-api/issues)
- **[Entwicklerangabe]** "LPIS hat seit 2026 kein eigenes Login-Formular mehr. Der Login läuft über Keycloak (`bach-id.wu.ac.at`) und von dort zwingend weiter über Microsoft Entra ID (`login.microsoftonline.com`) inklusive 2FA." — [blueqwertz/wu-lpis-api README](https://github.com/blueqwertz/wu-lpis-api)
- **[Anbieterangabe]** LPIS Ninja ist "Aktuell nicht verfügbar", weil LPIS auf "Login mit Microsoft" umgestellt hat; man arbeite an dem Problem. — [lpisninja.at](https://lpisninja.at/)
- **[Anbieterangabe]** Gleichzeitige Sitzungen beenden einander: "Öffnest du LPIS zusätzlich am Handy oder im Browser, fliegt der Bot raus." — [lpisbot.app](https://www.lpisbot.app/)
- **[offiziell]** Die WU-LPIS-Seite nennt für Wartelisten first-come-first-served oder Studienfortschritt; ein Warteraum oder eine Zufallsvergabe wird nicht beschrieben. — [WU: LPIS registration system](https://www.wu.ac.at/en/students/getting-organized/lpis-registration-system)
- **[Negativbefund]** Eine Suche nach einer WU- oder IT-SERVICES-Ankündigung zur Login-Umstellung von LPIS oder zu Bot-Schutzmaßnahmen ergab keinen Treffer; gefunden wurden nur allgemeine 2FA-Anleitungen, z. B. [WU-Wiki: Zwei-Faktor-Authentifizierung](https://wiki.wu.ac.at/it/de/information-security/zwei-faktor-authentifizierung-2fa).

### Inferences
- Die Zufallsfelder (seed, zufällig benannter Hidden-Input, dynamische Feldnamen) wirken wie ein gezielter Schutz gegen selbstgebaute HTTP-Requests; das ist plausibel, aber nicht offiziell bestätigt. Sie könnten ebenso CSRF-Schutz sein.
- Die Microsoft/2FA-Umstellung ist vermutlich eine allgemeine Sicherheitsmaßnahme (Single Sign-on), keine Anti-Bot-Maßnahme; als Nebeneffekt hat sie serverseitig arbeitende Bots mit hinterlegten Zugangsdaten gebrochen.
- Das Muster der WU-Reaktion scheint bislang technisch (Erschweren) statt disziplinär (Sanktionieren) zu sein. Das ist eine Schlussfolgerung aus dem Fehlen von Sanktionsbelegen.
- Browserbasierte Bots, die den echten Button klicken, sind von den Zufallsfeldern nicht betroffen; das erklärt, warum neuere Projekte fast durchweg diesen Ansatz wählen.

### Gaps
- Seit wann es die seed/Hidden-Felder gibt, ist unbelegt (frühester Hinweis auf dynamische Feldnamen: Issue von 2021/2024).
- Genaues Datum der Login-Umstellung 2026 und eine offizielle Mitteilung dazu wurden nicht gefunden.
- Ob LPIS Rate-Limiting, Logging-Auswertung oder automatische Sperren bei auffälligen Request-Mustern einsetzt, ist öffentlich nicht dokumentiert.

## 6. Vergleich: Umgang anderer Universitäten mit Anmeldebots (nur Einordnung)

### Takeaway
Auch für TU Wien (TISS) und Uni Wien (u:space) wurden öffentliche Bot-Projekte gefunden, aber keine dokumentierten Sanktionen. Dokumentierte ausdrückliche Verbote wurden nur für US-Universitäten als Such-Snippet gefunden, nicht verifiziert.

### Cited Findings
- **[Vergleich TU Wien, Entwicklerangabe]** Für TISS existieren mehrere öffentliche Bots, u. a. ein Projekt mit dem Hinweis "Use at own risk!" und eine Chrome-Extension "Anmeldung TU Wien" (laut Suchergebnis im September 2026 aktualisiert, "not affiliated with TU Wien"). — [lif22/tissbot](https://github.com/lif22/tissbot), [whynotzoidberg/TissRegistrationBot](https://github.com/whynotzoidberg/TissRegistrationBot), [Chrome Web Store: Anmeldung TU Wien](https://chromewebstore.google.com/detail/anmeldung-tu-wien/oifnnbkdfkdkegiogdmkefoficaichgg)
- **[Vergleich TU Wien]** Ein LPIS-Userscript ist ausdrücklich ein Fork des "TISS Quick Registration Script". — [rafaelmohr/lpis-registration-script](https://github.com/rafaelmohr/lpis-registration-script)
- **[Vergleich TU Wien, Hörensagen, nur Such-Snippet]** Forendiskussion von 2015 (siehe Abschnitt 3): Bots als nicht vorgesehene Nutzung, Benutzungsordnung nach Lesart eines Posters nicht eindeutig; keine berichtete Sanktion. — [informatik-forum.at, Thread 110876](https://www.informatik-forum.at/forum/index.php?thread%2F110876-tiss-hacks-lva-anmeldung-automatisch-mit-script%2F=)
- **[Vergleich Uni Wien, Negativbefund]** Suche nach Bots und Sperren bei u:space ergab nichts; die Uni Wien verteilt Plätze laut eigener Seite u. a. über Punkte- oder Präferenzsystem, was den Zeitvorteil eines Bots strukturell reduziert. — [Uni Wien: Empfohlener Studienpfad](https://studieren.univie.ac.at/anmeldung-zu-lehrveranstaltungenpruefungen/empfohlener-studienpfad/)
- **[Vergleich USA, nur Such-Snippet]** Laut Suchzusammenfassung verbieten Regelungen der University at Buffalo und der University of Washington Registrierungsskripte ausdrücklich; die UW-Seite (26.02.2019, "improper registration") war nur nach Login abrufbar. — [UW CSE Undergrad News](https://ugradnews.cs.washington.edu/2019/02/26/improper-registration), [University at Buffalo Registrar](https://www.buffalo.edu/registrar/instructions-for-using-HUB/register-for-classes.html)

### Inferences
- Im österreichischen Hochschulraum scheint die Bot-Nutzung bei First-come-first-served-Systemen (WU, TU) verbreitet und öffentlich geduldet oder zumindest nicht sichtbar sanktioniert zu sein.
- Universitäten mit Präferenz- oder Punktevergabe entziehen Bots den Nutzen; das ist die strukturelle Alternative zu Sanktionen.

### Gaps
- Für deutsche Universitäten wurde kein dokumentierter Sanktionsfall gefunden (eine Suche, nur allgemeine Anmeldeseiten als Treffer); die Abdeckung ist dünn.
- Die US-Regelungen wurden nicht im Wortlaut verifiziert und sind nur als Hinweis zu verwenden.
