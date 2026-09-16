---
name: write-job-posting
description: Write or revise a job posting through a short guided interview, offer headline choices, and check the result for AGG, AÜG, pay-transparency, and GDPR requirements. Use for "Stellenanzeige schreiben", "Stellenausschreibung erstellen", "Jobanzeige texten", "Stellenanzeige überarbeiten" or "Anzeige AGG-konform machen". It works without an alluvo account and can use connected alluvo company settings and publishing tools when available.
summary: Write or revise a compliant job posting through a guided interview.
triggers: Stellenanzeige schreiben, Stellenausschreibung erstellen, Jobanzeige texten, Stellenanzeige überarbeiten, Anzeige AGG-konform machen
aliases: stellenanzeige
---

# Job posting — guided creation with compliance check

Write a job posting that appeals to applicants, is legally sound, and matches the company's
voice. Work like a good copywriter in a briefing: understand first, offer variants, draft,
then check. Nothing goes out without the user's approval.

<HARD-GATE>
Write the full text only after the user has chosen a headline variant. Do not deliver
anything (file, alluvo, channel variants) until the compliance check has run and the user
has named or chosen the delivery format.
</HARD-GATE>

## How to ask

- **One question per message.** Never send a questionnaire all at once.
- **Use the environment's question tool** when one exists (in Claude Code,
  `AskUserQuestion`): give 2–4 concrete options, with your recommendation first and
  „(empfohlen)". The user can always answer freely. If no such tool exists, ask the same
  question as text with numbered options.
- **Do not ask what you already know.** Use the request, the context probe, and earlier
  answers. Skip every question whose answer is established, and say in one sentence at
  the end of the interview what you carried over.
- **Answer in the user's language.** Write the posting in the language the user requests
  (default: German).

## Phase 0 — Context probe (silent, no follow-up)

Check whether the alluvo assistant is connected: does an MCP tool `manage-settings` or
`get-workflow-guidance` exist? If so, read the items in [references/alluvo.md](references/alluvo.md),
section “Context reading”, **read-only**: formality (du/Sie), tone, company bio, taboo words,
inclusivity rules, benefits, role catalogue, and, if the user named a staffing requirement,
role, or company, the matching record. Published jobs are style references.

If alluvo is not connected, that is not an error: turn the same points into interview
questions, asking only those relevant to this posting.

Summarize in no more than five lines: „Was ich schon weiß" (name the source: request,
alluvo, assumption). Write and change nothing in this phase.

## Phase 1 — Interview

Follow the questionnaire in [references/interview.md](references/interview.md) in its stated
order, but ask only questions that remain open. Ask at most seven questions, usually three
to five. Required questions without which no posting can be created: position and level,
work location, placement form (Arbeitnehmerüberlassung, Direktvermittlung, or own employment),
working-time model, and compensation.

If the user supplies an old posting or staffing requirement, extract everything from it
first and ask only about gaps.

## Phase 2 — Variants, then full text

1. Offer **two to three variants** for the title and opening paragraph that differ in
   attitude (for example factual-confident, warm-team-oriented, direct-modern). Show them
   side by side, state your recommendation and why, then use the question tool to ask which
   one to use.
2. Write the full text using [references/structure.md](references/structure.md): title with
   (m/w/d), opening, responsibilities, profile, benefits, framework (place, time,
   compensation, placement form), application, and contact. Use an industry template when
   one fits.
3. Keep the voice consistent: use one form of address (du **or** Sie, never mixed), omit
   taboo words, follow inclusivity rules, and remove filler. Concrete numbers beat
   adjectives: „3.400–3.900 € brutto" rather than „attraktive Vergütung".

## Phase 3 — Compliance check

Check the text against [references/compliance.md](references/compliance.md) and show the
result as a table: check, finding, correction. Correct every finding in the text before
continuing. Name anything that cannot be fixed (for example a missing salary because the
user does not want to provide one) as an open risk, with one sentence explaining why it is
a risk. Do not decide on the risk; the user does.

## Phase 4 — Delivery

**If the user has already named the delivery format** (in the request or interview), do not
ask again; deliver exactly that way.

**Otherwise ask now with the question tool**, allowing multiple selections:

1. **Als Datei speichern** (empfohlen, wenn ein Dateisystem da ist): Markdown, Dateiname
   `stellenanzeige-<position>-<ort>.md`.
2. **In alluvo anlegen und im Talent Hub veröffentlichen**: offer only when alluvo is
   connected. Follow [references/alluvo.md](references/alluvo.md), section “Create the job”:
   first preview with `confirmed: false`, get the user's confirmation, then use
   `confirmed: true`. Show the Talent Hub URL afterwards.
3. **Kanalvarianten erzeugen**: Indeed, Bundesagentur, Meta-Ads short copy, social post,
   WhatsApp short version, using the formats in [references/structure.md](references/structure.md).
   For a real Meta campaign, when alluvo is connected, call `get-workflow-guidance` with
   `workflow: "manage-meta-ads"` and follow its guidance.
4. **Nur hier im Chat.**

Without a filesystem and without alluvo, only options 3 and 4 remain.

End with a short closing block: what was delivered, where it was delivered, which open risks
from Phase 3 remain, and a suggested next step (for example „Meta-Kampagne dazu?", „Zweite
Variante für Teilzeit?").

## What you do not do

- No invented benefits, salaries, tariffs, or locations. Ask about anything unknown or
  leave it out.
- No unsupported superlatives („marktführend", „Top-Arbeitgeber").
- No posting without (m/w/d) or equivalent wording, no age requirements, no photo request,
  and no native-language requirement (a language level is fine).
- No writes in alluvo without a preview and confirmation.
