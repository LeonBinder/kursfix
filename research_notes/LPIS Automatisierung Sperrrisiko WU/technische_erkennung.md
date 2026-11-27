# LPIS (WU Wien): Technisches Verhalten, Schutzmechanismen und Automatisierung – Stand November 2026

Methodik: reine Schreibtischrecherche. Gelesen wurde der Quellcode von 13 öffentlichen GitHub-Repositories (geklont am 27.11.2026, inkl. Commit-Historie und Issues) sowie öffentliche WU-Seiten. Es wurden keine Anfragen an lpis.wu.ac.at oder WU-Login-Systeme gesendet. GitLab wurde nicht durchsucht (siehe Gaps).

Kennzeichnung: **[belegt]** = steht so in einer Quelle (Code, README, Issue, WU-Seite). **[Schlussfolgerung]** = eigene Ableitung. Wichtig: "belegt" heißt "im Bot-Code/README so dokumentiert", nicht "am Live-System verifiziert". Bot-Code zeigt, was dessen Autor am LPIS-HTML beobachtet hat, zum jeweiligen Datum.

Untersuchte Repositories (Sterne / letzter Commit):

| Repo | Technik | Letzter Commit | Anmerkung |
|---|---|---|---|
| [discreteagent/wu-lpis-bot](https://github.com/discreteagent/wu-lpis-bot) | Python + Playwright (echtes Chrome, sichtbar) | 2026-09-28 (1 Commit, 0 Sterne) | aktuellster Bot, manueller Login |
| [blueqwertz/wu-lpis-api](https://github.com/blueqwertz/wu-lpis-api) | Python + mechanize/requests | 2026-11-16 (98 Commits) | aktiv gepflegter Fork von hofstaetter |
| [alexanderhofstaetter/wu-lpis-api](https://github.com/alexanderhofstaetter/wu-lpis-api) | Python 2 + mechanize | 2020-01-24 (23 Sterne, 7 Forks) | Ur-Projekt, Kern von "Flips" |
| [PreyMa/WU-LPIS-bot](https://github.com/PreyMa/WU-LPIS-bot) | Userscript (Tampermonkey) | 2023-09-23 (104 Commits) | |
| [nicospacez/lpisquickregistrationscript](https://github.com/nicospacez/lpisquickregistrationscript) | Userscript | 2018 (+2021 Lizenzhinweis) | Autor L. Burtscher, TISS-Skript-Port |
| [rafaelmohr/lpis-registration-script](https://github.com/rafaelmohr/lpis-registration-script) | Userscript | 2025-09-02 | |
| [nicospacez/WUstus](https://github.com/nicospacez/WUstus) | Chrome-Extension | 2025-01-26 | README-Badge "broken" |
| [MoritzRenkin/wu-lpis-automation](https://github.com/MoritzRenkin/wu-lpis-automation) | Python + Selenium, GUI | 2022-11-25 | "[DEPRECATED]" ohne Begründung |
| [schneiseb/LPIS-Bot](https://github.com/schneiseb/LPIS-Bot) | Node + Selenium | 2024-09-04 | |
| [Alexander070702/Wu-Lpis-Bot](https://github.com/Alexander070702/Wu-Lpis-Bot) | Python + Selenium | 2023-09-11 | |
| [TimWriter/lpis_registration_tool](https://github.com/TimWriter/lpis_registration_tool) | Userscript | 2022-10-18 | nur UI-Gerüst, keine Anmeldelogik |
| [alexanderhofstaetter/wu-js-lpis-api](https://github.com/alexanderhofstaetter/wu-js-lpis-api) | JS | 2019-01-24 | nicht im Detail gelesen |
| [semestria-at/semestria-lpis-bot](https://github.com/semestria-at/semestria-lpis-bot) | kommerzielle Desktop-App | 2026-10-15 | nur Marketing-README, kein Quellcode |

---

## 1. Wie implementieren öffentliche LPIS-Bots die Anmeldung (Reload vs. vorab geladenes Formular, Formularfelder, Begründung)?

### Takeaway
Praktisch alle öffentlichen Bots (2018–2026) laden die LV-Seite zum Öffnungszeitpunkt neu und klicken/senden dann das Formular der frisch geladenen Seite; als Grund nennt der Code durchgehend, dass der Anmelde-Button vor der Öffnung `disabled` ist – nicht, dass ein altes Token abgelehnt würde. Einzige Ausnahme sind zwei Selenium-Varianten, die das separate Formular "Nummerneingabe" vorab befüllen und zum Zeitpunkt ohne Reload absenden; ob das je erfolgreich war, ist nirgends dokumentiert.

### Cited Findings

**Seitenstruktur laut Bot-Code**
- [belegt] Die LV-Liste ist eine Tabelle `table.b3k-data`; je Zeile gibt es `td.action` mit einem `<form>` samt `input[type="submit"]`, einen Zeitstempel `td.action .timestamp span` im Format "ab dd.mm.yyyy hh:mm" / "bis ...", eine Statusbox `td.box` / `div.box.possible` und Kapazität `div[class*="capacity_entry"]` ("frei / gesamt"). — [hofstaetter WuLpisApiClass.py, Commit ae6cf74 (2020-01-24), Z. 176–202](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L176-L202)
- [belegt] Die Session steckt im URL-Pfad: nach dem Login wird auf `https://lpis.wu.ac.at/kdcs/bach-s##/#####/` weitergeleitet; alle weiteren relativen Links (`DLVO?ASPP=...;SPP=...;...`) hängen daran. — [hofstaetter, Z. 62–65](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L62-L65); 2026 bestätigt als `lpis.wu.ac.at/kdcs/<instance>/<session>/` in [blueqwertz ms_login.py, Commit 5b9a7c2 (2026-11-16)](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/ms_login.py#L4-L22)
- [belegt] Das Formular je LV hat einen `name` der Form `<PREFIX>_<interne ID>`; hofstaetter liest daraus `internal_id = form['name'].rsplit('_')[1]`. Formulare, deren Name mit `WLDEL` beginnt, überspringt blueqwertz (Warteliste-Austragen). — [hofstaetter Z. 188–190](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L188-L190); [blueqwertz WuLpisApiClass.py Z. 383–398](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L383-L398)
- [belegt] Neben "anmelden" gibt es einen eigenen Wartelisten-Button mit Wert "eintragen": WUstus sucht `'.action form input[value="anmelden"]:not([disabled])'` und danach `'.action form input[value="eintragen"]:not([disabled])'`. — [WUstus src/content.js, Commit 898699f (2025-01-26), Z. 332–368](https://github.com/nicospacez/WUstus/blob/898699fc1c6ff8089478501f5b9cdd674bfaaf72/src/content.js#L332-L368)
- [belegt] Nicht jede Zeile hat einen Submit-Button; PreyMa akzeptiert seit Commit f7d52ac (2022-09-01, "Allow links instead of submit buttons") auch `td.action a`. — [PreyMa wubot.js, Commit 475b31e, Z. 229–232](https://github.com/PreyMa/WU-LPIS-bot/blob/475b31efb5c0d6edc41d5111266333e4ff8abed7/wubot.js#L229-L232)

**Ablauf: Reload zum Öffnungszeitpunkt, dann Absenden der frischen Seite**
- [belegt] hofstaetter (2018–2020): wartet bis `Öffnungszeit − 1,0 s`, lädt dann die LV-Seite in einer Schleife ohne Pause neu, bis `div.box.possible` in der Zeile erscheint, und sendet anschließend das Formular aus genau dieser Antwort (`select_form(form1); submit()`). Log-Texte: `"registration is not (yet) possibe, waiting ..."`, `"reloading page and waiting for form to be submittable"`. — [Z. 247–281](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L247-L281)
- [belegt] blueqwertz (2024–2026): identische Logik, Vorlauf per `--offset` (Default 0,7 s) plus NTP-Korrektur; Kommentar `# Reload page until registration is possible`. — [Z. 355–400](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L355-L400)
- [belegt] nicospacez-Userscript (2018): `if ($(registrationButton).is(':disabled')) { //registration button is still disabled --> refresh page`; README: "If the registration button is still disabled at that point, the script performs refreshes of the page until the button gets activated or a configured maximum of refreshes is reached." — [Skript Z. 160–176](https://github.com/nicospacez/lpisquickregistrationscript/blob/b3bac721cdd286ad5002538a44a826a5f9382274/lpis_quick_registration_script.user.js#L160-L176); [README](https://github.com/nicospacez/lpisquickregistrationscript/blob/b3bac721cdd286ad5002538a44a826a5f9382274/README.md)
- [belegt] PreyMa (2022/23): Timer → `window.location.reload()`; nach dem Laden `if( !this.submitButton.disabled ) { ... this.submitButton.click(); }`, sonst erneuter Reload bis `maxRefreshTime` (Default 10 s); Reload wird 60 ms vor der Zeit abgeschickt (`latencyAdjustment= 60`). README: "the tabs will automatically reload the page repeatedly until it can click the `anmelden` button". — [wubot.js Z. 2196–2236, 1110–1111](https://github.com/PreyMa/WU-LPIS-bot/blob/475b31efb5c0d6edc41d5111266333e4ff8abed7/wubot.js#L2196-L2236)
- [belegt] MoritzRenkin (2022): `driver.refresh()` bis zu 10-mal im Abstand 0,1 s; Klick nur wenn `anmelden_button.get_attribute('disabled') != 'true'`, sonst Status "Registration is not yet allowed". — [bot.py Z. 205–240](https://github.com/MoritzRenkin/wu-lpis-automation/blob/b9a186aa9099199d218db1b75072f9b19b776558/bot.py#L205-L240); [config.ini](https://github.com/MoritzRenkin/wu-lpis-automation/blob/b9a186aa9099199d218db1b75072f9b19b776558/config.ini)
- [belegt] rafaelmohr (2025): `if (regButton.prop('disabled')) { self.log("Registration is not yet open, reloading..."); self.refreshPage(); }`; Selektor `td.action>form>input[type="submit"]`. — [Userscript Z. 136–150, 267](https://github.com/rafaelmohr/lpis-registration-script/blob/a2e1c1fde4bce8f1bfcd54a014d63c9820e72a72/LPIS%20Quick%20Registration%20Script-1.0.user.js)
- [belegt] WUstus v2 (2025): Reload zum Zeitpunkt, Klick auf ersten nicht-disabled "anmelden"-Button, sonst Reload, maximal 10 Versuche. — [content.js Z. 236–312](https://github.com/nicospacez/WUstus/blob/898699fc1c6ff8089478501f5b9cdd674bfaaf72/src/content.js#L236-L312)
- [belegt] discreteagent (Sept. 2026): `page.goto(url)` so getaktet, dass der Request ca. 20 ms nach Öffnung bei LPIS ankommt (`fire_time = opens_at - offset - trip/2 + unc + 0.02`), dann Klick auf den echten Button im DOM (`b.click()`), sofern `!b.disabled && !b.classList.contains('disabled')`. Bei noch gesperrter Seite Wiederholung alle 0,15 s in den ersten 2 s, danach 0,5 s, danach 2 s; Abbruch nach 30 s gesperrt bzw. 120 s gesamt; max. 3 Klickversuche je Gruppe. — [lpis_bot.py, Commit 28ff633 (2026-09-28), Z. 92–99, 227–229, 395–437](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L395-L437)
- [belegt] schneiseb (2023/24), Normalpfad: `driver.navigate().refresh()` 50 ms vor der vollen Stunde, dann Klick auf `//tr[contains(.,'${lvcode}')]//input[contains(@value,'anmelden')]`. — [BrowserConnect.js Z. 57–71](https://github.com/schneiseb/LPIS-Bot/blob/1d6864cc22b2a4c5340c01dadb2ff48112b5da5e/BrowserConnect.js#L57-L71)

**Ausnahme: vorab geladenes Formular "Nummerneingabe" ohne Reload**
- [belegt] schneiseb, SBWL-Pfad: klickt den Link "Nummerneingabe", trägt die LV-Nummer in `//form[contains(., 'LV-Nummer')]/input[2]` ein und klickt per `setTimeout` 50 ms vor dem Zeitpunkt den Button `'anmelden ...'` desselben, vorher geladenen Formulars – ohne Reload. — [BrowserConnect.js Z. 48–55](https://github.com/schneiseb/LPIS-Bot/blob/1d6864cc22b2a4c5340c01dadb2ff48112b5da5e/BrowserConnect.js#L48-L55)
- [belegt] MoritzRenkin hatte dieselbe Variante (Link `/html/body/a[7]`, LV-Nummer in `/html/body/form/input[2]`, `pause.until(submit_time)`, `submit_button.click()`), sie steht im aktuellen Stand aber auskommentiert in einem String-Block; der aktive Code nutzt Reload + Klick. — [bot.py Z. 242–252](https://github.com/MoritzRenkin/wu-lpis-automation/blob/b9a186aa9099199d218db1b75072f9b19b776558/bot.py#L242-L252)

**Formularfelder / Tokens**
- [belegt] Einzige Quelle, die versteckte Zufallsfelder nennt: discreteagent-README: "it clicks the real button inside the page ..., so LPIS receives exactly the form a mouse click sends, including the per-page random fields (`seed`, a randomly named hidden input) that break bots which build requests themselves." — [README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md)
- [belegt] Im Code desselben Repos kommt `seed` nicht vor (grep über alle 13 Repos: einziger Treffer ist diese README-Zeile); das Offline-Test-Fake-LPIS verwendet nur `<input type="hidden" name="lv" ...>`. — [tests/test_offline.py Z. 49](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/tests/test_offline.py#L49)
- [belegt] Dynamische Feldnamen sind unabhängig davon dokumentiert: (a) hofstaetter ermittelt die Namen der Login-Felder zur Laufzeit über `//input[@accesskey='u']/@name` bzw. `'p'` (2018); (b) Issue-Kommentar von Nutzer Ro43 (06.02.2024): "Der Name des Dropdownfeldes dürfte dynamisch vergeben werden. Jedes mal nach dem Einloggen steht was anderes bei name."; (c) blueqwertz greift deshalb per `form.controls[0].name` statt über den festen Namen `ASPP` zu. — [hofstaetter Z. 54–59](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L54-L59); [Issue #3](https://github.com/alexanderhofstaetter/wu-lpis-api/issues/3); [blueqwertz Z. 279–285](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L279-L285)
- [belegt] Kein Bot baut den Anmelde-POST selbst zusammen: Userscripts/Selenium/Playwright klicken den DOM-Button, mechanize sendet das geparste Formular inkl. aller Hidden-Felder. Ein Zeitstempel-Feld wird in keinem Repo erwähnt.

**Begründung für den Reload in den Quellen**
- [belegt] Genannte Gründe sind ausschließlich: Button noch `disabled` / Formular "not submittable" / Status noch nicht `box possible` (Zitate oben). Kein Kommentar, keine Commit-Message und kein Issue in den 13 Repos sagt, ein vor der Öffnung ausgegebenes Formular oder Token werde nach der Öffnung abgelehnt.

### Inferences
- [Schlussfolgerung] Der Reload ist in allen UI-Bots technisch zwingend, weil ein `disabled`-Submit-Button im Browser nicht klickbar ist; die Bots haben die Alternative (Button per JS aktivieren und altes Formular senden) schlicht nie probiert oder nie dokumentiert. Aus dem einheitlichen Reload-Muster folgt daher nicht, dass LPIS alte Formulare ablehnt.
- [Schlussfolgerung] Die `seed`-Angabe ist eine unbestätigte Einzelquelle (1 Commit, 0 Sterne, kein Code dazu), aber plausibel im Licht der unabhängig belegten dynamischen Feldnamen. Sie besagt nur "pro Seitenabruf zufällig", nicht "zeitlich validiert".
- [Schlussfolgerung] mechanize-Bots (hofstaetter/blueqwertz) funktionieren trotz Zufallsfeldern, weil sie das frisch geladene Formular vollständig übernehmen; "break bots which build requests themselves" betrifft nur hart kodierte POSTs.

### Gaps
- Kein Repo enthält einen HTML-Mitschnitt einer echten LPIS-Seite (discreteagent speichert `lpis_page_N.html` lokal, git-ignoriert). Die exakten Hidden-Felder des Anmeldeformulars sind daher öffentlich nicht einsehbar.
- Semestria (kommerziell) veröffentlicht keinen Code; Funktionsweise unbekannt.
- GitLab und GitHub-Code-Suche (erfordert Login) wurden nicht durchsucht; weitere, anders benannte Bots sind möglich.

---

## 2. Kann ein VOR der Öffnung geladenes Formular ZUR Öffnung ohne Reload erfolgreich abgesendet werden? Zeit-Validierung von Tokens?

### Takeaway
Öffentlich ist das weder belegt noch widerlegt. Belegt ist nur: die Seite enthält schon vor der Öffnung ein Formular mit deaktiviertem Button, und zwei Bots senden ein vorab geladenes "Nummerneingabe"-Formular zum Zeitpunkt ab – ohne jede Erfolgs- oder Fehlermeldung in den Quellen.

### Cited Findings
- [belegt] Vor der Öffnung existiert das Formular bereits, nur der Button ist deaktiviert: fünf unabhängige Bots (2018, 2022, 2022/23, 2025, 2025) prüfen `disabled` am Submit-Button innerhalb `td.action form` und laden sonst neu (Quellen in Abschnitt 1). hofstaetters `infos()` liest den Formularnamen für LVs, deren Zeitstempel noch "ab ..." lautet (Beispiel-JSON im README zeigt `internal_id` neben künftigem Anmeldebeginn). — [hofstaetter README](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/README.md); [Z. 188–196](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L188-L196)
- [belegt] discreteagent zeigt vor der Öffnung je Gruppe `button 'anmelden' locked, free 23, ab 28.09.2026 14:00` an, d. h. der Button samt Beschriftung ist im September 2026 vor der Öffnung im DOM vorhanden. — [README, Abschnitt Usage](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md)
- [belegt] Zwei Bots senden ein vorab geladenes Formular zum Zeitpunkt ohne Reload, aber über den separaten Weg "Nummerneingabe" (schneiseb SBWL-Pfad 2023/24; MoritzRenkin, auskommentiert). Quellen in Abschnitt 1. Erfolgsmeldungen, Issues oder Kommentare dazu gibt es nicht; schneiseb hat 0 Sterne und Commit-Messages wie "dew", "few".
- [belegt] MoritzRenkin hat die Nummerneingabe-Variante durch Reload + Klick ersetzt, ohne Begründung im Code oder in Commit-Messages. — [Commit-Historie](https://github.com/MoritzRenkin/wu-lpis-automation/commits/master)
- [belegt] Keine Quelle beschreibt eine Fehlermeldung wie "Formular abgelaufen" oder eine Token-Ablehnung nach Öffnung. Der einzige im Code behandelte Sitzungsfehler ist der Logout/Redirect auf `bach-id.` (discreteagent Z. 405–408).

### Inferences
- [Schlussfolgerung] Dass die Seite vor der Öffnung "gar kein Formular" enthält, ist durch den Code widerlegt, soweit es Zeilen mit Submit-Button betrifft; für Zeilen, die nur einen Link haben (PreyMa-Fallback `td.action a`), ist es offen.
- [Schlussfolgerung] Ob der Server ein vorab ausgegebenes Formular akzeptiert, hängt an drei unbekannten Punkten: (1) ob das Vor-Öffnungs-Formular dieselben Hidden-Felder trägt wie das Nach-Öffnungs-Formular, (2) ob `seed`/Zufallsfeld serverseitig an den Seitenabruf oder an eine Lebensdauer gebunden ist, (3) ob jeder weitere Seitenabruf in derselben Session (Keepalive-Reload, zweiter Tab) ältere Seeds entwertet. Zu keinem der drei Punkte gibt es eine öffentliche Quelle.
- [Schlussfolgerung] Die Nummerneingabe-Bots sind ein schwaches Indiz, dass zumindest dieses Formular nicht an die Öffnungszeit gebunden ist (es wird ja unabhängig von einer konkreten LV geladen); der Button "anmelden ..." mit Auslassungspunkten deutet auf einen Folgeschritt hin, sodass der eigentliche Anmelde-POST möglicherweise erst danach erfolgt. Beides ist Vermutung.
- [Schlussfolgerung] Der Zeitgewinn eines Verzichts auf den Reload wäre eine Server-Antwortzeit (ein GET der LV-Seite); laut rafaelmohr-README antwortet LPIS bei Andrang deutlich langsamer (Abschnitt 4), der Gewinn wäre also gerade bei begehrten LVs relevant – das Risiko ist ein verbrauchter Versuch mit unbekannter Serverreaktion.

### Gaps
- Die Kernfrage ist aus öffentlichen Quellen nicht beantwortbar. Sie ließe sich nur durch einen Test am Live-System klären, der hier ausdrücklich ausgeschlossen war.
- Unbekannt, ob LPIS serverseitig einen zu frühen POST mit einer Meldung quittiert, ignoriert oder protokolliert.

---

## 3. Hinweise auf Bot-Erkennung in LPIS oder im WU-SSO (CAPTCHA, Rate-Limit, IP-Sperre, UA-/Headless-Checks, Logging, Warteraum, Session-Limits)

### Takeaway
In keinem der 13 Repos (Code, READMEs, Issues, 2018–2026) findet sich ein Hinweis auf CAPTCHA, Rate-Limiting, IP-Sperren, Webdriver-Erkennung oder Sanktionen. Dokumentiert sind nur: seit 2026 verpflichtender Login über Keycloak → Microsoft Entra ID mit 2FA, kurze Sitzungsdauer (eine Quelle nennt 30 Minuten) und dynamisch vergebene Feldnamen.

### Cited Findings
- [belegt] Login-Umstellung: "LPIS hat seit 2026 kein eigenes Login-Formular mehr. Der Login läuft über Keycloak (`bach-id.wu.ac.at`) und von dort zwingend weiter über Microsoft Entra ID (`login.microsoftonline.com`) inklusive 2FA. Die Keycloak-Loginseite bietet ausschließlich den Identity Provider `wu-microsoft` an". Kette laut Code-Docstring: `lpis.wu.ac.at/lpis → short.wu.ac.at/wu-lpis → bach.wu.ac.at → lpis.wu.ac.at/lpispd → bach-id.wu.ac.at (Keycloak, realm "bach", client "bach-lpislg-prod") → login.microsoftonline.com → ... → lpis.wu.ac.at/kdcs/<instance>/<session>/`. — [blueqwertz README](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/README.md); [ms_login.py Z. 4–22](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/ms_login.py#L4-L22); eingeführt mit Commit 56b022c (2026-08-11) "feat: login via Microsoft SSO with 2FA and session storing"
- [belegt] 2FA ist an der WU für Studierende verpflichtend; ohne Einrichtung wird der Account deaktiviert. — [WU IT-Wiki 2FA](https://wiki.wu.ac.at/it/de/information-security/zwei-faktor-authentifizierung-2fa) (nur Suchmaschinen-Auszug gelesen)
- [belegt] Der SSO lässt sich weiterhin skripten: blueqwertz durchläuft die Kette mit `requests`, bestätigt 2FA per Authenticator-Push mit Number-Matching und speichert das persistente Microsoft-Cookie (`ESTSAUTHPERSISTENT`), sodass Folgeläufe "ohne Passwort- und ohne 2FA-Abfrage" durchlaufen. Ein CAPTCHA-Schritt kommt im 881-Zeilen-Login-Modul nicht vor. — [README, Abschnitt Session-Speicherung](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/README.md)
- [belegt] Session-Dauer: discreteagent-README: "WU's login asks for a fresh sign-in every 30 minutes" – deshalb Start 15–25 Minuten vor Öffnung und Keepalive-Reload alle 120 s (`KEEPALIVE_EVERY = 120`). rafaelmohr-README: "LPIS has a pretty short session time. Reload the course page a minute before registration starts". blueqwertz loggt sich 5 Minuten vor Öffnung neu ein, wenn die Öffnung mehr als 10 Minuten entfernt ist (Commit 7717854, 2024-09-23, "added login wait time"). — [discreteagent README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md); [rafaelmohr README](https://github.com/rafaelmohr/lpis-registration-script/blob/a2e1c1fde4bce8f1bfcd54a014d63c9820e72a72/README.md); [blueqwertz Z. 328–340](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L328-L340)
- [belegt] Logout-Erkennung: discreteagent wertet eine Seite ohne Tabelle mit `bach-id.` in der URL als "LPIS LOGGED YOU OUT". — [lpis_bot.py Z. 405–408](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L405-L408)
- [belegt] User-Agent: die mechanize-Bots setzen einen Chrome-User-Agent und `set_handle_robots(False)  # ignore robots`; eine Begründung (z. B. Blockade des Default-UA) steht nicht dabei. — [hofstaetter Z. 30–41](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L30-L41)
- [belegt] Headless/Webdriver: MoritzRenkin bietet einen Headless-Modus (Selenium); schneiseb und Alexander070702 nutzen unverändertes Selenium-Chrome. Keiner enthält Stealth-Maßnahmen oder erwähnt Erkennung. — [MoritzRenkin bot.py Z. 134–150](https://github.com/MoritzRenkin/wu-lpis-automation/blob/b9a186aa9099199d218db1b75072f9b19b776558/bot.py#L134-L150)
- [belegt] Anfragefrequenz, die Bots laut Code ohne dokumentierte Gegenreaktion fahren: hofstaetter/blueqwertz GET-Schleife ohne Pause ab ca. 0,7–1,0 s vor Öffnung; MoritzRenkin 10 Reloads à 0,1 s; discreteagent 0,15 s-Takt für 2 s; blueqwertz hat 2024–2026 den Vorlauf mehrfach justiert (0,5 → 1 → 0,9 → 0,83 → 0,80 → 0,7 s), nie wegen einer Sperre. — [blueqwertz Commits](https://github.com/blueqwertz/wu-lpis-api/commits/main)
- [belegt] discreteagent bezeichnet sich als "Gentle on LPIS: one session, one page load per attempt; quick retries (every 0.15 s) only during the first 2 seconds" und nutzt für die Zeitmessung 16 `HEAD /`-Requests an lpis.wu.ac.at plus SNTP an `timeserver.wu.ac.at`. — [README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md); [lpis_bot.py Z. 187–207](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L187-L207)
- [belegt] Warteraum: discreteagents `settle()` wartet bis 90 s, falls statt der Tabelle ein Text mit `warte|queue|wait` erscheint (Docstring: "if LPIS shows a busy/queue page instead, give it time to move on"). Ob eine solche Seite je beobachtet wurde, steht nicht im Repo. — [lpis_bot.py Z. 285–297](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L285-L297)
- [belegt] Haltung der WU (nur für den Einstieg in die Spezialisierung über myWU, nicht LPIS-spezifisch): "Wenn du eine WU-fremde Software verwendest, kann nicht garantiert werden, dass deine Anmeldung erfolgreich ist." Die Seite enthält keine Aussage zu Bots/Skripten oder Sanktionen. — [WU FAQ Einstieg in die Spezialisierung](https://www.wu.ac.at/studierende/mein-studium/bachelorguide/bachelorguide-fuer-deutschsprachige-programme/einstieg-in-die-spezialisierung/faqs)
- [belegt] Bot-Autoren weisen selbst auf Regelrisiko hin, ohne konkrete Fälle: discreteagent "Check WU's rules before using automated registration; you use it on your own account and at your own risk."; nicospacez ergänzte 2021 einen Haftungsausschluss (Commit b3bac72 "add legal notice"). — [discreteagent README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md)
- [belegt] Nebenbefund Datenabfluss an Dritte: blueqwertz sendet Logs samt Benutzername (Matrikel-Login), MAC-Adresse und Gerätename an eine Grafana-Loki-Instanz des Autors und das Anmeldeergebnis mit Benutzername an das öffentliche ntfy-Topic `lpis-bot`. — [logger.py](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/logger.py); [WuLpisApiClass.py Z. 428–433](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L428-L433)

### Inferences
- [Schlussfolgerung] Das Fehlen jeder CAPTCHA-/Sperr-Behandlung in acht Jahren Bot-Code, bei gleichzeitig aggressiven Reload-Schleifen, spricht dafür, dass LPIS bis Herbst 2026 keine für Bot-Autoren sichtbare technische Abwehr (CAPTCHA, harte Rate-Limits, Webdriver-Checks) im Anmeldepfad hatte. Es sagt nichts über serverseitiges Logging und nachträgliche Auswertung; dass jede Anfrage mit Session und Zeitstempel protokolliert werden kann, ist bei personalisierter Session im URL-Pfad naheliegend, aber unbelegt.
- [Schlussfolgerung] Die SSO-Umstellung 2026 wirkt faktisch als Automatisierungsbremse für Passwort-POST-Bots, ist nach Quellenlage aber eine allgemeine Sicherheitsmaßnahme (2FA-Pflicht), kein gezielter Anti-Bot-Schritt.
- [Schlussfolgerung] Die "30 Minuten" stammen aus einer einzelnen Bot-README; ob das ein Keycloak-/LPIS-Session-Limit, ein Idle-Timeout oder eine absolute Lebensdauer ist, bleibt offen. Der 120-s-Keepalive deutet darauf, dass der Autor ein Idle-Timeout zumindest nicht ausschließen wollte.
- [Schlussfolgerung] Die Queue-Erkennung bei discreteagent ist vorsorglicher Code, kein Beleg für einen Warteraum.

### Gaps
- Keine öffentliche WU-Aussage zu Erkennung, Protokollierung oder Sanktionierung automatisierter LPIS-Anmeldungen gefunden (Suche nach Benutzungsordnung/Sperre ergab nur Treffer zu Prüfungs-Erschleichung und anderen Unis). Das ist Thema der Nachbar-Recherche zu Regeln/Sperrrisiko.
- Der WU IT-ServiceGuide (PDF) war verschlüsselt und konnte nicht ausgelesen werden.
- Keine Reddit-/Forenberichte über gesperrte Bot-Nutzer gefunden; die Websuche lieferte generell keine Forentreffer zu LPIS.

---

## 4. Verhalten von LPIS unter Last zum Öffnungszeitpunkt

### Takeaway
Dokumentiert sind langsamere Antworten bei Andrang und Plätze, die binnen Sekunden weg sind; Fehlerseiten oder Ausfälle sind in den gefundenen Quellen nicht beschrieben. Bots kalkulieren Vorläufe von 60 ms bis 1 s ein und behandeln den Fall "frei angezeigt, trotzdem Warteliste".

### Cited Findings
- [belegt] "if a lot of students will try to register for this course lpis will respond much slower. So far we had good results with values between 500 and 1000 [ms]" (Reload-Vorlauf). — [rafaelmohr README (2025)](https://github.com/rafaelmohr/lpis-registration-script/blob/a2e1c1fde4bce8f1bfcd54a014d63c9820e72a72/README.md)
- [belegt] "Tested on the live LPIS during the WiSe 2026 registration (September 2026) ... Popular groups lost more than a third of their seats within two seconds of opening." Code-Kommentar: `NAV_TIMEOUT = 60_000 # ms; LPIS is slow at the opening second`. — [discreteagent README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md); [lpis_bot.py Z. 43](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L43)
- [belegt] Warteliste trotz angezeigter freier Plätze: discreteagent-Fehlertabelle: "`WAITING LIST` – The group filled a moment before the click"; der Bot erkennt das am Hinweistext (`.b3k_alert_content`) mit "warteliste|waiting list" nach dem Klick auf "anmelden". blueqwertz prüft nach dem Absenden eines Formulars, das bei `free1 > 0` gewählt wurde, ob der Alert "Warteliste" enthält, und versucht dann die Ausweich-LV. — [discreteagent Z. 440–450](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L440-L450); [blueqwertz Z. 402–427](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L402-L427)
- [belegt] Uhr-Synchronisation gilt als erfolgskritisch: `timeserver.wu.ac.at` wird von nicospacez (PowerShell-Skript 2018), hofstaetter (Kommentar), blueqwertz (NTP) und discreteagent (SNTP + HTTP-Date-Header von LPIS) genutzt; discreteagent: "A PC clock half a second off is common". Ein Studierendenbericht nennt "die Atomuhr und wenige Kursplätze" als Grund, warum Semesterplanung "fast unmöglich" sei. — [nicospacez time_sync](https://github.com/nicospacez/lpisquickregistrationscript/tree/b3bac721cdd286ad5002538a44a826a5f9382274/time_sync); [StudyCheck-Bericht](https://www.studycheck.de/studium/wirtschaftswissenschaft/wu-wien-27675/bericht-822563) (nur Suchauszug gelesen)
- [belegt] Typische Vorläufe: PreyMa 60 ms, nicospacez 300 ms, rafaelmohr 500–1000 ms, blueqwertz 0,7 s (mit Reload-Schleife), hofstaetter 1,0 s, discreteagent Ankunft +20 ms nach Öffnung. Quellen in Abschnitt 1.
- [belegt] LPIS liefert einen HTTP-`Date`-Header mit Sekundenauflösung, den discreteagent zur Eingrenzung der Serveruhr nutzt. — [lpis_bot.py Z. 187–207](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L187-L207)

### Inferences
- [Schlussfolgerung] Die Freischaltung erfolgt serverseitig zur vollen Minute der LPIS-Uhr; wer zu früh lädt, erhält die gesperrte Seite und verliert eine Antwortzeit. Deshalb fahren Bots entweder Schleifen mit Vorlauf (riskieren mehrere verlorene Roundtrips unter Last) oder zielen knapp hinter die Öffnung.
- [Schlussfolgerung] Zwischen Laden der Seite und Klick liegt ein Zeitfenster, in dem Plätze vergeben werden; die Platzanzeige der geladenen Seite ist zum Klickzeitpunkt bereits veraltet. Je langsamer LPIS antwortet, desto größer dieses Fenster – das ist der sachliche Grund, warum die Frage aus Abschnitt 2 relevant ist.

### Gaps
- Keine Messwerte zu Antwortzeiten, keine dokumentierten Fehlerseiten/HTTP-Statuscodes zur Öffnung gefunden.
- Keine offiziellen WU-Störungsmeldungen zu LPIS-Überlast gefunden.

---

## 5. Brüche nach LPIS-Änderungen laut Issues/Forks

### Takeaway
Zwei Änderungen sind belegt: dynamisch vergebene Formularfeldnamen (spätestens 2021 als Fehler sichtbar) und 2026 der Wegfall des LPIS-eigenen Login-Formulars zugunsten von Keycloak + Microsoft Entra ID mit 2FA. Die Tabellenstruktur der Anmeldeseite (`table.b3k-data`, `td.action form`, Button `disabled`) ist von 2018 bis 2026 laut Code stabil geblieben.

### Cited Findings
- [belegt] hofstaetter-Issue #4 (09.08.2021): "no control matching name 'ASPP'"; bestätigt 17.08.2022 und nachgefragt bis 25.02.2025 ("Gibts hierzu noch ein update?"). Ursache laut Ro43 (06.02.2024): Name des Dropdowns wird "dynamisch vergeben", "Jedes mal nach dem Einloggen steht was anderes". Der Autor am 06.08.2021 zur Aktualität: "schon länger nicht getestet". — [Issue #4](https://github.com/alexanderhofstaetter/wu-lpis-api/issues/4); [Issue #3](https://github.com/alexanderhofstaetter/wu-lpis-api/issues/3)
- [belegt] Login-Umstellung 2026: blueqwertz README/Commit 56b022c (11.08.2026); discreteagent README: "it works with WU's current single sign-on (bots that post your password to LPIS no longer do)". Nachfolge-Fixes bei blueqwertz: 63a5ab7 "Handle Microsoft login failures cleanly" (12.08.2026), fbd12e4 "fix: login error with some letters" (17.08.2026), d17f27b "Increase login timeout and retry attempts" (17.09.2026). — [blueqwertz Commits](https://github.com/blueqwertz/wu-lpis-api/commits/main); [discreteagent README](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/README.md)
- [belegt] Kleinere Anpassungen bei PreyMa im September 2022/2023: f7d52ac "Allow links instead of submit buttons", fbc1152 "LPIS provides all query params as a single string", 31b6f00 "Allow SPP query param to be at the end of the URL". — [PreyMa Commits](https://github.com/PreyMa/WU-LPIS-bot/commits/master)
- [belegt] blueqwertz 2501f13 (30.04.2024) "added last link rule" und späterer Selektor `title="Lehrveranstaltungsanmeldung"`: der Link zur LV-Anmeldung je Planpunkt musste anders ausgewählt werden. — [blueqwertz Z. 313](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L313)
- [belegt] blueqwertz PR #3 (16.11.2026): `timeserver.wu.ac.at` antwortet nicht immer per NTP ("UDP 123 blocked, off-campus network, server down"), daher Fallback auf andere Zeitserver. — [PR #3](https://github.com/blueqwertz/wu-lpis-api/pull/3)
- [belegt] WUstus trägt im README ein Badge "broken"; MoritzRenkin ist seit 25.11.2022 als "[DEPRECATED]" markiert; beides ohne Begründung. — [WUstus README](https://github.com/nicospacez/WUstus/blob/898699fc1c6ff8089478501f5b9cdd674bfaaf72/README.md); [MoritzRenkin Commit b9a186a](https://github.com/MoritzRenkin/wu-lpis-automation/commit/b9a186aa9099199d218db1b75072f9b19b776558)
- [belegt] Stabilität der Anmeldeseite: dieselben Selektoren (`table.b3k-data`, `td.action form input[type=submit]`, `.timestamp`, `.b3k_alert_content`) in hofstaetter (2018), PreyMa (2022), rafaelmohr (2025), blueqwertz (2026), discreteagent (2026). Quellen in Abschnitt 1.

### Inferences
- [Schlussfolgerung] Bots mit Login-Automatik über das alte Formular (hofstaetter, MoritzRenkin, schneiseb, Alexander070702: Selektoren `form 'login'` / `//*[@id='login']`) sind seit der Umstellung 2026 funktionslos, sofern blueqwertz' Beschreibung zutrifft. Userscripts, die erst nach manuellem Login auf der LV-Seite laufen, sind von der Login-Umstellung nicht betroffen.
- [Schlussfolgerung] Dynamische Feldnamen sind keine neue Maßnahme: die Login-Felder hatten schon 2018 zur Laufzeit ermittelte Namen. Sie erschweren hart kodierte Requests, nicht aber DOM-Klicks.
- [Schlussfolgerung] Seit der Umstellung bis November 2026 ist in den aktiven Repos (blueqwertz, discreteagent) keine weitere LPIS-seitige Änderung am Anmeldepfad dokumentiert.

### Gaps
- Kein offizielles WU-Dokument zum Datum/Anlass der LPIS-Login-Umstellung gefunden; die Jahreszahl 2026 stammt allein aus dem blueqwertz-README.
- Warum WUstus "broken" ist und MoritzRenkin eingestellt wurde, ist nicht dokumentiert.

---

## 6. Öffentliche Beschreibung der Vergaberegel durch die WU (First come first served, Wartelisten)

### Takeaway
Die WU nennt "First Come – First Served" als eines von mehreren Verfahren und sagt, dass ohne Präferenzen die Reihenfolge der Anmeldung zählt; eine technische Definition (Server-Eingangszeit) oder eine Wartelisten-Reihungsregel für LPIS wurde nicht gefunden. Das Wartelistenverhalten ist nur indirekt über Bot-Code belegt.

### Cited Findings
- [belegt] WU-FAQ zum Einstieg in die Spezialisierung: "Nur bei Spezialisierungen mit dem Verfahren 'First Come – First Served' ist eine schnelle Anmeldung erforderlich."; "Wenn du keine Präferenzen setzt, erfolgt die Reihung automatisch anhand der Reihenfolge deiner Anmeldung. Eine Zuteilung über MyMatch ist in jedem Fall möglich."; "ein Wartelisteneintrag zählt nicht" [als Anmeldung]; "Nach Ende der Anmeldefrist wird der Platz an die*den nächste*n Studierende*n weitergegeben."; "Melde dich ausschließlich über myWU an." — [WU FAQ](https://www.wu.ac.at/studierende/mein-studium/bachelorguide/bachelorguide-fuer-deutschsprachige-programme/einstieg-in-die-spezialisierung/faqs) (Zitate über ein Abruf-Tool extrahiert, nicht im Original gegengelesen)
- [belegt, nur Suchauszug] WU-Seite Master Economics: "LPIS registration for most courses opens once the official registration period starts. Places are allocated on a first-come-first-served basis." Die Seite lieferte beim direkten Abruf HTTP 404; das Zitat stammt aus dem Suchmaschinen-Snippet. — [WU Master Economics](https://www.wu.ac.at/en/students/my-program/masters-programs/masters-program-economics/structure-contents/areas-of-specialisation/information-preference-based-registration)
- [belegt] Wartelisten in LPIS laut Bot-Code: eigene Spalte/Tooltip "Anzahl Warteliste" bzw. nach Eintrag "aktuelle Wartelistenposition / Anzahl Wartelisteneinträge"; eigener Button "eintragen"; Formulare `WLDEL...` zum Austragen; README-Beispiel zeigt eine LV mit `"free": "0"`, `"waitlist": "16"`. — [blueqwertz Z. 413–417](https://github.com/blueqwertz/wu-lpis-api/blob/5b9a7c2440613907ab27c2102bd8587dcd171005/WuLpisApiClass.py#L413-L417); [WUstus content.js Z. 354–368](https://github.com/nicospacez/WUstus/blob/898699fc1c6ff8089478501f5b9cdd674bfaaf72/src/content.js#L354-L368); [hofstaetter README](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/README.md)
- [belegt] Automatische Wartelistenplatzierung beim Klick auf "anmelden", wenn die Gruppe inzwischen voll ist: discreteagent meldet "DONE - but LPIS put you on the WAITING LIST" und empfiehlt, von Hand in eine Gruppe mit freien Plätzen zu wechseln. — [lpis_bot.py Z. 440–447](https://github.com/discreteagent/wu-lpis-bot/blob/28ff633ba096c2a2f42351791914acc719449944/lpis_bot.py#L440-L447)
- [belegt] LPIS zeigt den eigenen Anmeldezeitpunkt minutengenau an (`registerd_at: "03.09.2018 15:00"` aus `td.box.active .timestamp span`). — [hofstaetter Z. 198–199 und README](https://github.com/alexanderhofstaetter/wu-lpis-api/blob/ae6cf7453be05c44540a1eb7c42f249fc8438ff9/WuLpisApiClass.py#L198-L199)
- [belegt] Wartelisten werden teils nachträglich aufgestockt, "oft je nach Studienfortschritt" (ÖH-WU-Dokument, nur Suchauszug). — [ÖH WU Download](https://oeh-wu.at/download/bbb47463-5a40-4b02-be37-f748a1e10950)

### Inferences
- [Schlussfolgerung] Bei FCFS-LVs entscheidet die Reihenfolge, in der die Anmelde-POSTs vom Server verarbeitet werden; das folgt aus "Reihenfolge deiner Anmeldung" plus dem beobachteten Verhalten (voll → Warteliste), ist aber von der WU nicht als "Server-Eingangszeit" formuliert.
- [Schlussfolgerung] Ein zu spät verarbeiteter Klick auf "anmelden" führt nicht zu einem Fehler, sondern zu einem Wartelistenplatz in der gewählten Gruppe; das kann schlechter sein als ein Fixplatz in einer Ausweichgruppe. Für Bot-Design ist das ein fachliches, kein Erkennungsrisiko.
- [Schlussfolgerung] Die WU-Aussage zu "WU-fremder Software" ist eine Gewährleistungs-, keine Verbotsformulierung, und steht im Kontext der myWU-Spezialisierungsanmeldung.

### Gaps
- Keine WU-Quelle zur Reihung auf LPIS-Wartelisten (Eintragszeit vs. Studienfortschritt) und zum automatischen Nachrücken gefunden.
- Die frühere LPIS-Infoseite `www.wu.ac.at/studierende/tools-services/lpis/` leitet inzwischen auf myWU (`bach.wu.ac.at/mywu/`) weiter; diese wurde wegen der Vorgabe "keine WU-Login-Systeme" nicht abgerufen. Eine öffentliche LPIS-Hilfe/FAQ konnte daher nicht ausgewertet werden.
- Die Master-Economics-Seite (FCFS-Zitat) war nicht direkt abrufbar (404); das Zitat ist nur über den Suchindex belegt.
