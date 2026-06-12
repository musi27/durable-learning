# Session Protocol

Every session is one of three shapes: **cold start** (first ever for this mission), **standard**, or **comeback** (gap ≥ 2× the agreed cadence). Detect which by reading the root `registry.md`, then the workspace's `MISSION.md`, `system/NEXT.md`, and the most recent dates in `system/LEDGER.md`. A mission new to an existing root is a cold start for that workspace only. Get today's date from the system (`date +%F`) — never guess it.

Throughout, the machinery is felt, not seen: detection, linting, scheduling, and bookkeeping happen without narration. The conversation is about the topic ([SKILL.md](./SKILL.md), legible pedagogy).

Time budgets below assume a 60-minute session; scale to the session length in `MISSION.md`.

**Short sessions (under ~20 min) don't shrink the lifecycle — they split it.** Running all four phases in 10 minutes turns the protocol into pure overhead. Instead, alternate session types across the week:

- **Review days** (5–10 min): re-entry in one line, then due re-probes only. No new material. This is most days for a 5-minute learner.
- **Teaching days** (the longest slots available): one micro-lesson (one capability, attempt-first, one practice rep) plus at most one due review folded in.
- Close shrinks to two lines: learner's one-line takeaway, agent updates `system/NEXT.md` with which type tomorrow is.

State the split in `system/NEXT.md` so you always know what kind of session the learner is walking into. FSRS doesn't care — short frequent retrieval is excellent scheduling; what must never be compressed is attempt-first and honest grading.

## Cold start (first session)

**Hard rule: the first lesson begins within ~10 minutes of session start.** Onboarding that eats the session kills the learner's reason for coming.

1. **Root structure.** If there is no `registry.md` here (or in the parent folder), this is a new learning root: create `registry.md` (format in [LEDGER-FORMAT.md](./LEDGER-FORMAT.md)) and a workspace subfolder named after the mission — a lowercase slug; it becomes the cross-workspace prereq prefix. Register the workspace (cadence gets filled in after the interview). Inside the workspace, the top level is the learner's surface (`MISSION.md`, `GLOSSARY.md`, `map.html`, `lessons/`, `reference/`) and `system/` holds your state (`LEDGER.md`, `NOTES.md`, `NEXT.md`, `RESOURCES.md`, `probes/`); the root holds only the registry and the aggregate map. If a root already exists, just add the new workspace folder and its registry entry. This is one minute of file setup, not part of the onboarding conversation — do it silently.
2. **Mission interview** (≤10 min). Why this topic, what does success look like, cadence **and session length** (5 minutes a day and 30 minutes a day are different protocols — ask, don't assume), constraints. Push concrete over abstract. **Confirm the artifact medium — never infer it.** "You're technical" does not mean they want to learn through code; a domain mission (finance, music theory) is not a coding mission unless the learner says so. Run the scope gate ([MISSION-FORMAT.md](./MISSION-FORMAT.md)) — including the red-flag check for any pain/health/high-stakes adjacency. Write `MISSION.md`.
3. **First lesson immediately.** For project missions, ship the thinnest vertical slice that produces a working artifact today ("CLI that echoes a file"). Tangible win first; theory attaches later. Alongside it, drop `lessons/0000-how-this-works.html` into the workspace: a one-page, learner-facing explainer of the system — levels L1–L4 and how probes earn them, why sessions open with review, what decay means, what the agency log is and isn't, and a short **"which files are yours"** section: yours are `lessons/`, `reference/`, `map.html`, `MISSION.md`, `GLOSSARY.md`; `system/` is the tutor's filing cabinet — inspectable, safe to ignore. Training-log tone, one screen, no homework attached, never quizzed on. **This page is the only home for system explanation**: point the learner at it once, here, and never re-narrate the machinery in sessions. The first real lesson is numbered `0001`.
4. **After the lesson**, draft the capability map (see decomposition rules in [LEDGER-FORMAT.md](./LEDGER-FORMAT.md)) and walk the learner through it for approval. The map is a proposal, not a verdict. Where a sibling workspace already holds a capability this mission needs, reference it (`finance:N01`) instead of re-mapping it — that is the point of the shared root.
5. **Schedule the nudge.** If the platform has scheduling tools (e.g. Cowork scheduled tasks), offer to create a recurring task matching the cadence in `MISSION.md` — prompt along the lines of: "Open the {learning root} folder, read registry.md, run `ledger_tools.py today`, and start today's session — lead with what's due." **One nudge per root, not per workspace** — the unified queue is what makes one daily session serve every mission; update the existing nudge rather than adding a second. Keep it in sync: update or remove the task whenever cadence is renegotiated. On file-only platforms, say so once: the workspace can't notice the learner has been gone.
6. **Close** as in the standard session below. Resource search can continue between sessions; note gaps in `system/RESOURCES.md`.

## Standard session

### 1. Re-entry (≤5 min)

Read [AGENT-BRIEF.md](./AGENT-BRIEF.md), then the root `registry.md`, then the active workspace's `system/NEXT.md` and `system/LEDGER.md`. Run `python3 scripts/ledger_tools.py check` — fix any errors before proceeding (the ledger is load-bearing; a corrupted fsrs line or dangling prereq silently breaks the frontier) — then `python3 scripts/ledger_tools.py today` for the unified due queue across all registered workspaces. All of that is silent prep, not conversation. Open with the mission, then where they stand in topic terms: what's solid, what's slipping, what's next. Ask about the homework/assignment from `system/NEXT.md`.

**Diff teach-back** (project missions): if the project changed since last session, have the learner walk you through the diff — "explain anything you shipped." Code or work they explain well is free generative evidence (record it). Anything they *can't* explain is not shame — it is a **frontier signal**: maximally mission-relevant teaching material, because they already shipped it. Rationale line: "you shipped it; let's make sure you own it."

### 2. Review block (≤25% of session — hard cap)

The queue is `python3 scripts/ledger_tools.py today`: every due node across every registered workspace, already ordered by prerequisite-centrality then days overdue. Due nodes from sibling workspaces belong in this block too — one session serves the whole root; that consolidation is the adherence lever. If more is due than fits the cap, **triage**: take the queue in order, weighing mission-relevance on top of the computed ordering. Fold the remainder into the teaching block where today's material naturally exercises them; otherwise they stay due. Never let review consume the session.

Reviews are retrieval-first: free recall before recognition ("explain X from memory" before any multiple choice). Grade and update FSRS state per [PROBE-PROTOCOL.md](./PROBE-PROTOCOL.md).

### 3. Teaching block (bulk of session)

Pick the frontier node ([LEDGER-FORMAT.md](./LEDGER-FORMAT.md)) unless the learner names a target. One capability per lesson. Structure:

1. **Attempt first** — pose the problem before the instruction. Productive failure is the point; 2–5 minutes of struggle, then teach.
2. **Teach** — knowledge from `system/RESOURCES.md`, cited. Produce/update the lesson HTML.
3. **Practice** — tight feedback loop, ideally automatic. **Practice medium rule: put the friction in the capability, not the tooling.** Choose the lowest-extraneous-load medium that still exercises the target node — the default is interactive, self-checking elements *inside* the lesson HTML (one click to open, instant red/green feedback). External tooling (scripts, terminals, editors) is justified only when operating that tooling *is* the capability being trained — and even then, the learner writes the code attempt-first; never hand them agent-written scaffolds with holes to fill (all the syntax tax, none of the design learning).
4. **The learner does the generative work**: they draft the glossary entry and the one-line ledger evidence summary. You edit.

Same-session assessment caps at L2 (see [PROBE-PROTOCOL.md](./PROBE-PROTOCOL.md)). Schedule the L3 probe ≥72h out via `system/NEXT.md`.

### 4. Close (5–10 min)

Spoken, in topic terms — two beats, no protocol narration:

1. Ask the learner for a one-line takeaway, in their words.
2. State what's next: next session's focus and type, the **one midweek artifact assignment** tied to the mission (code to write, swatch to crochet, paragraph to compose — something inspectable), plus a one-sentence progress note with the agency trend, training-log tone (see [AGENCY.md](./AGENCY.md)).

Silently, around those beats: update `system/LEDGER.md` (evidence events, FSRS fields via script, agency log); write `system/NEXT.md` (planned frontier node, due re-probes, the assignment, optionally a 5-minute self-quiz of 3–5 free-recall prompts); run `python3 scripts/ledger_tools.py map` and `map --all` to regenerate both maps; append the **protocol self-audit** line to `system/NOTES.md`: "Protocol self-audit: steps skipped or bent today — {none | list}." Honest drift is recoverable; silent drift is not — the audit is for the file, never for the conversation.

### Encore (more today)

"Can we do more today?" is always yes — never block an eager learner; enthusiasm is the scarcest resource in the system. An encore is a normal teaching block on the next frontier node, nothing special. Assessment caps do not move: material introduced today still caps at L2 today, and L3 still needs its 72 hours — an encore changes what got taught, never what got verified. At most one line on the trade-off, once per workspace, *ever*: something like "happy to keep going — just know the long-term gains come from the spacing, so tomorrow's ten minutes will beat tonight's extra hour." Said the first time only, never as a refusal. Rewrite `system/NEXT.md` after each encore so the plan reflects where today actually ended.

## Comeback session (gap ≥ 2× cadence)

The avalanche is emotional before it is computational. Order matters:

1. **Mission first, never metrics.** Open with the mission ("how's the back-stiffness been?" / "did the team use the CLI?") — not with the due-count.
2. **Frame decay as physics, not failure.** One line: "Memory decays on a curve; the scheduler already priced this in — a successful review now actually buys unusually long intervals." (True under FSRS: low retrievability → bigger stability gain.)
3. **Triage hard.** Review cap stays at 25%. Pick 2–3 due nodes from the top of the unified `today` queue (it already ranks by prerequisite-centrality, across all workspaces). Everything else folds into future lessons or waits. Say so explicitly: "the rest re-verify as they come up — nothing is lost."
4. **First action = easiest win.** Open with the re-probe most likely to succeed. Momentum before rigor.
5. **Collect the dropout data.** Ask what happened, without judgment. Was the homework dose too big? Cadence unrealistic? Record the cause in `system/NOTES.md`; renegotiate cadence/dose in `MISSION.md`. Re-prescribing the dose that caused the dropout is a protocol failure. If a scheduled nudge exists, update it to the new cadence.
6. Proceed as a standard session with whatever time remains.

## What this protocol never does

- Lets review swallow the session (cap is hard).
- Probes today's material above L2 today.
- Computes dates or intervals by hand instead of `scripts/fsrs.py`.
- Opens a comeback with a wall of overdue items.
- Narrates its own machinery — protocol talk belongs in `lessons/0000-how-this-works.html`; rationales are answers to pushback, not announcements.
- Turns down a learner who asks for more today (see Encore).
- Sends the learner to external tooling when an in-lesson exercise would exercise the same node.
