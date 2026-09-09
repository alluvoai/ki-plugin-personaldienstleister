# alluvo-Anbindung (optional)

Gilt nur, wenn der alluvo-Assistent (MCP-Server) verbunden ist. Erkennung: Es gibt ein Tool
`manage-settings` oder `get-workflow-guidance`. In Claude Code sind MCP-Tools oft erst nach
einer Tool-Suche sichtbar; suche nach `manage-settings`, bevor du „nicht verbunden"
annimmst. Alle Aufrufe in Phase 0 sind lesend.

## Kontext lesen (Phase 0)

| Was | Aufruf | Verwendung |
|---|---|---|
| Anrede, Ton, Bio, Tabu-Wörter, Inklusivität | `manage-settings` mit `action: "get"`, `group: "brand_identity"` | `default_formality` (formal = Sie, informal = du), `default_tone`, `brand_bio` (Einstieg und „Über uns"), `terms_to_avoid`, `inclusivity_gender_neutral` und die weiteren Inklusivitäts-Flags, `personality` |
| Unternehmensname und Kontakt | `manage-settings` mit `action: "get"`, `group: "general"` | Absender, Ansprechpartner, Standard-Bewerbungsweg |
| Rollenkatalog | `search-model` mit `model_type: "0-100"` (StaffingRole), `q: "<Position>"` | Rollen als Optionen in Frage 1; `role_id` für die Anlage |
| Niederlassungen | `search-model` mit `model_type: "0-73"` (Branch) | Einsatzort-Optionen in Frage 2 |
| Personalbedarf des Kunden | `search-model` mit `model_type: "0-102"` (StaffingRequirement), `q: "<Kunde oder Rolle>"`, dann `get-model` | Position, Ort, Zeitraum, Anforderungen vorbelegen; Kundenname nur mit Erlaubnis in die Anzeige |
| Benefit-Katalog | `list-model-types` (ohne Parameter), in der Liste den Typ mit „Benefit" im Namen suchen, dann `search-model` mit diesem `model_type` | Benefits als Optionen in Frage 6, mit Gruppen (Sicherheit, Geld, Gesundheit, Freizeit); gibt es keinen solchen Typ, Frage 6 normal stellen |
| Stilreferenz | `search-model` mit `model_type: "0-80"` (Job), Filter `is_active: true`, `per_page: 3`, dann `get-model` auf eine Stelle | Ton und Struktur bestehender Anzeigen; nicht kopieren, nur angleichen |

Wenn ein Aufruf `MODULE_LOCKED` antwortet, sag es dem Nutzer in einem Satz und mach ohne
diese Quelle weiter.

## Stelle anlegen (Phase 4, Option 2)

Zwei Stufen, immer. Erst Vorschau, dann Bestätigung des Nutzers, dann Ausführung.

```
Tool: manage-model
action: "create"
model_type: "0-80"
data:
  title: "<Titel mit (m/w/d)>"
  description: "<Volltext als Markdown oder Absätze>"
  location: "<Stadt>"
  postal_code: "<PLZ>"
  employment_type: "<full_time | part_time | temporary | contractor | intern | other>"
  work_hours: "<z. B. 'Vollzeit 39 h, Schichtdienst'>"
  responsibilities: "<Aufgaben>"
  qualifications: "<Profil>"
  job_benefits: "<Wir bieten>"
  salary_min: <Zahl in EUR, z. B. 3400>
  salary_max: <Zahl in EUR>
  salary_currency: "EUR"
  salary_unit: "MONTH"
  role_id: <ID aus dem Rollenkatalog, optional>
  published_at: "<ISO 8601 mit Offset, z. B. 2026-10-01T09:00:00+02:00>"
  immediate_start: <true|false>
confirmed: false
```

Zeig die Vorschau, lass bestätigen, wiederhole mit `confirmed: true`. Das Ergebnis enthält
die `talent_hub_url`: nennen und anbieten, ein Hero-Foto zu ergänzen (Rezept über
`get-tool-guidance` mit `tool_names: ["manage-media"]`).

Gehaltsangaben immer in Euro, nie in Cent. `salary_unit` ist freier Text: `MONTH` für
Monatsgehalt, `HOUR` für Stundenlohn, `YEAR` für Jahresgehalt. `employment_type` ist ein
geschlossener Wert; bei Zweifel `get-model-schema` mit `model_type: "0-80"` und
`context: "form"` aufrufen.

Wenn der Nutzer die Stelle einer Kampagne zuordnen will: `search-model` mit `model_type:
"0-191"` (JobPostingCampaign) und die ID als `job_posting_campaign_id` mitgeben.

## Meta-Kampagne (Phase 4, Option 3, nur mit alluvo)

Für eine echte Kampagne statt nur Kurztexten: `get-workflow-guidance` mit
`workflow: "manage-meta-ads"` aufrufen und der Anleitung folgen. Die Talent-Hub-URL der
angelegten Stelle ist die Landingpage; die Meta-Kurztexte aus struktur.md sind die Creatives.
