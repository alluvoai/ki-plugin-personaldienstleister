---
name: write-job-posting
description: Write or revise a job posting through a short guided interview, offer headline choices, and check the result for AGG, AÜG, pay-transparency, and GDPR requirements. Use for "Stellenanzeige schreiben", "Stellenausschreibung erstellen", "Jobanzeige texten", "Stellenanzeige überarbeiten", "Anzeige AGG-konform machen", "Stellenanzeige veröffentlichen" or "im Talent Hub ausschreiben"; an already finished text skips the interview and goes straight to the check and publishing. It works without an alluvo account and can use connected alluvo company settings and publishing tools when available.
summary: Write or revise a compliant job posting through a guided interview.
triggers: Stellenanzeige schreiben, Stellenausschreibung erstellen, Stellenanzeige veröffentlichen, im Talent Hub ausschreiben, Stellenanzeige überarbeiten, Anzeige AGG-konform machen
aliases: stellenanzeige
---

# Job posting — guided creation with compliance check

Write a job posting that appeals to applicants, is legally sound, and matches the company's
voice. Work like a good copywriter in a briefing: understand first, offer variants, draft,
then check. Nothing goes out without the user's approval.

<HARD-GATE>
Write the full text only after the user has chosen a headline variant. (A finished text the user supplies has no headline step; see “Shortcut” below.) Do not deliver
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

## Shortcut — the text already exists

If the user supplies a finished posting (pasted text, file, or an existing job they want
published) and asks to publish it („Stellenanzeige veröffentlichen", „im Talent Hub
ausschreiben"), do not rewrite it. Run Phase 0, then ask only for the fields the alluvo job
still needs and the text does not state (usually location, placement type, contract type and
working time, salary). Split the text into a short intro and the three lists (tasks, profile,
benefits), as the `publish-job-posting` workflow describes. Skip Phase 1 and Phase 2, run Phase 3 on the given text and propose corrections
as a diff the user approves, then go straight to Phase 4 option 2 with a preview
(`confirmed: false`) before publishing. The HARD-GATE's headline-variant step does not apply
here; the compliance check and the preview do.

If the user only says „lass uns eine Stellenanzeige im Talent Hub veröffentlichen" without a
text, run the normal flow and treat delivery option 2 as already chosen.

## Phase 0 — Context probe (silent, no follow-up)

Check whether the alluvo assistant is connected: does an MCP tool `get-workflow-guidance` or
`manage-settings` exist? If so, follow [references/alluvo.md](references/alluvo.md): load the
`publish-job-posting` workflow and run its context step **read-only**: formality (du/Sie), tone,
company bio, taboo words, inclusivity rules, benefits, role catalogue, and, if the user named a
staffing requirement, role, or company, the matching record. Published jobs are style references.

If alluvo is not connected, that is not an error: turn the same points into interview
questions, asking only those relevant to this posting.

Summarize in no more than five lines: „Was ich schon weiß" (name the source: request,
alluvo, assumption). Write and change nothing in this phase.

## Phase 1 — Interview

Follow the questionnaire in [references/interview.md](references/interview.md) in its stated
order, but ask only questions that remain open. Ask at most seven questions, usually three
to five. Required questions without which no posting can be created: position and level,
work location, placement type (Arbeitnehmerüberlassung, Direktvermittlung, eigene Stelle, or
Freelance; skip when obvious from the request or the hub default), working-time model, and
compensation. When alluvo is connected, the `publish-job-posting` workflow maps the answers to
the job's contract fields.

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
   connected. Load `get-workflow-guidance(workflow: "publish-job-posting")` and follow it with
   the approved text: it checks that the Talent Hub is enabled, creates the job with preview and
   confirmation, runs the Google-for-Jobs check and only then shows the Talent Hub URL.
3. **In alluvo anlegen und bei der Bundesagentur für Arbeit veröffentlichen**: offer only when
   alluvo is connected **and** the Bundesagentur integration is set up. It needs the job from
   option 2; the same `publish-job-posting` workflow carries the readiness checklist and the
   publishing steps.
4. **Kanalvarianten erzeugen**: Indeed, Bundesagentur (copy for manual entry, only when the
   channel above is not available), Meta-Ads short copy, social post, WhatsApp short version,
   using the formats in [references/structure.md](references/structure.md).
   For a real Meta campaign, when alluvo is connected, call `get-workflow-guidance` with
   `workflow: "manage-meta-ads"` and follow its guidance.
5. **Nur hier im Chat.**

Without a filesystem and without alluvo, only options 4 and 5 remain.

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
