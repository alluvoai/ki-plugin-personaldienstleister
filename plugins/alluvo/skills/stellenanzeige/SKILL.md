---
name: stellenanzeige
description: Write a job posting (Stellenanzeige) for a staffing agency or any employer through a short guided interview — one question at a time, two or three headline variants to choose from, then the full text with an AGG, AÜG, pay-transparency and GDPR check before delivery. Works without an alluvo account; with the alluvo assistant connected it silently pulls the company's Anrede (du/Sie), tone, bio, benefits and roles, and can create the posting in alluvo and publish it on the Talent Hub. Use when the operator says "Stellenanzeige schreiben", "Stellenausschreibung erstellen", "Anzeige für eine Pflegefachkraft", "Jobanzeige texten", "Stellenanzeige überarbeiten", "Anzeige AGG-konform machen", "write a job posting", "draft a job ad", "create a job listing", "rewrite this job ad", or hands over a Personalbedarf, a role or an old ad to turn into a posting.
---

# Stellenanzeige — geführte Erstellung mit Compliance-Check

Du schreibst eine Stellenanzeige, die Bewerber:innen anspricht, rechtlich sauber ist und
in der Tonalität des Unternehmens klingt. Du arbeitest wie eine gute Texterin im Briefing:
erst verstehen, dann Varianten anbieten, dann ausformulieren, dann prüfen. Nichts geht
raus, was der Nutzer nicht freigegeben hat.

<HARD-GATE>
Schreibe den Volltext erst, wenn der Nutzer eine Headline-Variante gewählt hat. Liefere
nichts aus (Datei, alluvo, Kanalvarianten), bevor der Compliance-Check gelaufen ist und
der Nutzer die Auslieferungsform genannt oder gewählt hat.
</HARD-GATE>

## Wie du fragst

- **Eine Frage pro Nachricht.** Nie einen Fragenkatalog auf einmal.
- **Nutze das Frage-Tool der Umgebung**, wenn es eines gibt (in Claude Code
  `AskUserQuestion`): 2–4 konkrete Optionen, die erste ist deine Empfehlung mit
  „(empfohlen)". Der Nutzer kann immer frei antworten. Gibt es kein solches Tool, stelle
  dieselbe Frage als Text mit nummerierten Optionen.
- **Frag nichts, was du schon weißt.** Aus dem Auftrag, aus der Kontext-Sonde, aus
  früheren Antworten. Überspringe jede Frage, deren Antwort feststeht, und sag am Ende
  des Interviews in einem Satz, was du übernommen hast.
- **Antworte in der Sprache des Nutzers.** Die Anzeige selbst in der Sprache, die der
  Nutzer für die Anzeige will (Standard: Deutsch).

## Phase 0 — Kontext-Sonde (still, ohne Rückfrage)

Prüfe, ob der alluvo-Assistent verbunden ist: Existiert ein MCP-Tool `manage-settings`
oder `get-workflow-guidance`? Wenn ja, lies **lesend** die Dinge aus
[references/alluvo.md](references/alluvo.md), Abschnitt „Kontext lesen": Anrede
(du/Sie), Tonalität, Unternehmens-Bio, Tabu-Wörter, Inklusivitäts-Regeln, Benefits,
Rollenkatalog, und falls der Nutzer einen Personalbedarf, eine Rolle oder eine Firma
genannt hat, den passenden Datensatz. Veröffentlichte Stellen dienen als Stilreferenz.

Wenn alluvo nicht verbunden ist, ist das kein Fehler: Dieselben Punkte werden zu
Interviewfragen, aber nur die, die für diese Anzeige zählen.

Fasse in höchstens fünf Zeilen zusammen: „Was ich schon weiß" (Quelle nennen: Auftrag,
alluvo, Annahme). In dieser Phase schreibst du nichts und änderst nichts.

## Phase 1 — Interview

Arbeite den Fragenkatalog in [references/interview.md](references/interview.md) in der
angegebenen Reihenfolge ab, aber nur die Fragen, die noch offen sind. Regel: höchstens
sieben Fragen, in der Praxis meist drei bis fünf. Die Pflichtfragen, ohne die keine
Anzeige entsteht: Position und Level, Einsatzort, Einsatzform (Arbeitnehmerüberlassung
oder Direktvermittlung oder eigene Anstellung), Arbeitszeitmodell, Vergütung.

Wenn der Nutzer eine alte Anzeige oder einen Personalbedarf übergibt, extrahiere zuerst
alles daraus und frag nur die Lücken.

## Phase 2 — Varianten, dann Volltext

1. Biete **zwei bis drei Varianten** für Titel und Einstiegsabsatz an, die sich in der
   Haltung unterscheiden (z. B. sachlich-sicher, warm-teamorientiert, direkt-modern).
   Zeig sie nebeneinander, nenne deine Empfehlung und warum. Frag mit dem Frage-Tool,
   welche es sein soll.
2. Schreib den Volltext nach [references/struktur.md](references/struktur.md): Titel mit
   (m/w/d), Einstieg, Aufgaben, Profil, Wir bieten, Rahmen (Ort, Zeit, Vergütung,
   Einsatzform), Bewerbung und Kontakt. Nutze die Branchenvorlage, wenn eine passt.
3. Halte die Tonalität durch: Anrede konsequent (du **oder** Sie, nie gemischt),
   Tabu-Wörter weglassen, Inklusivitäts-Regeln einhalten, Floskeln streichen.
   Konkrete Zahlen schlagen Adjektive: „3.400–3.900 € brutto" statt „attraktive Vergütung".

## Phase 3 — Compliance-Check

Prüfe den Text gegen [references/compliance.md](references/compliance.md) und zeig das
Ergebnis als Tabelle: Prüfpunkt, Befund, Korrektur. Korrigiere jeden Befund im Text,
bevor du weitergehst. Nicht behebbare Punkte (z. B. fehlende Gehaltsangabe, weil der
Nutzer keine nennen will) benennst du als offenes Risiko mit einem Satz, warum es eines
ist. Du entscheidest nicht über das Risiko, der Nutzer tut es.

## Phase 4 — Auslieferung

**Wenn der Nutzer die Auslieferungsform schon genannt hat** (im Auftrag oder im
Interview), frag nicht nochmal, sondern liefere genau so.

**Sonst frag jetzt mit dem Frage-Tool**, Mehrfachauswahl erlaubt:

1. **Als Datei speichern** (empfohlen, wenn ein Dateisystem da ist): Markdown, Dateiname
   `stellenanzeige-<position>-<ort>.md`.
2. **In alluvo anlegen und im Talent Hub veröffentlichen**: nur anbieten, wenn alluvo
   verbunden ist. Rezept in [references/alluvo.md](references/alluvo.md), Abschnitt
   „Stelle anlegen": erst Vorschau mit `confirmed: false`, Nutzer bestätigt, dann
   `confirmed: true`. Danach die Talent-Hub-URL zeigen.
3. **Kanalvarianten erzeugen**: Indeed, Bundesagentur, Meta-Ads-Kurztexte, Social-Post,
   WhatsApp-Kurzfassung, Formate in [references/struktur.md](references/struktur.md).
   Für eine echte Meta-Kampagne, wenn alluvo verbunden ist: `get-workflow-guidance` mit
   `workflow: "manage-meta-ads"` aufrufen und dessen Anleitung folgen.
4. **Nur hier im Chat.**

Ohne Dateisystem und ohne alluvo bleiben 3 und 4.

Zum Schluss ein kurzer Abschlussblock: was geliefert wurde, wohin, welche offenen Risiken
aus Phase 3 bleiben, und ein Vorschlag für den nächsten Schritt (z. B. „Meta-Kampagne
dazu?", „Zweite Variante für Teilzeit?").

## Was du nicht tust

- Keine erfundenen Benefits, Gehälter, Tarife oder Standorte. Was du nicht weißt, fragst
  du oder lässt es weg.
- Keine Superlative ohne Beleg („marktführend", „Top-Arbeitgeber").
- Keine Anzeige ohne (m/w/d) oder gleichwertige Kennzeichnung, keine Altersangaben, keine
  Fotos-Anforderung, keine Muttersprache-Forderung (Sprachniveau ja).
- Keine Schreibzugriffe in alluvo ohne Vorschau und Bestätigung.
