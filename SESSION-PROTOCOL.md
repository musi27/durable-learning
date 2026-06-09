# Session Protocol

Every session is one of three shapes: **cold start** (first ever), **standard**, or **comeback** (gap ≥ 2× the agreed cadence). Detect which by reading `MISSION.md`, `NEXT.md`, and the most recent dates in `LEDGER.md`. Get today's date from the system (`date +%F`) — never guess it.

Time budgets below assume a 60-minute session; scale to the session length in `MISSION.md`.

**Short sessions (under ~20 min) don't shrink the lifecycle — they split it.** Running all four phases in 10 minutes turns the protocol into pure overhead. Instead, alternate session types across the week:

- **Review days** (5–10 min): re-entry in one line, then due re-probes only. No new material. This is most days for a 5-minute learner.
- **Teaching days** (the longest slots available): one micro-lesson (one capability, attempt-first, one practice rep) plus at most one due review folded in.
- Close shrinks to two lines: learner's one-line takeaway, agent updates `NEXT.md` with which type tomorrow is.

State the split in `NEXT.md` so the learner always knows what kind of session they're walking into. FSRS doesn't care — short frequent retrieval is excellent scheduling; what must never be compressed is attempt-first and honest grading.

## Cold start (first session)

**Hard rule: the first lesson begins within ~10 minutes of session start.** Onboarding that eats the session kills the learner's reason for coming.

1. **Mission interview** (≤10 min). Why this topic, what does success look like, cadence **and session length** (5 minutes a day and 30 minutes a day are different protocols — ask, don't assume), constraints. Push concrete over abstract. **Confirm the artifact medium — never infer it.** "You're technical" does not mean they want to learn through code; a domain mission (finance, music theory) is not a coding mission unless the learner says so. Run the scope gate ([MISSION-FORMAT.md](./MISSION-FORMAT.md)) — including the red-flag check for any pain/health/high-stakes adjacency. Write `MISSION.md`.
2. **First lesson immediately.** For project missions, ship the thinnest vertical slice that produces a working artifact today ("CLI that echoes a file"). Tangible win first; theory attaches later.
3. **After the lesson**, draft the capability map (see decomposition rules in [LEDGER-FORMAT.md](./LEDGER-FORMAT.md)) and walk the learner through it for approval. The map is a proposal, not a verdict.
4. **Schedule the nudge.** If the platform has scheduling tools (e.g. Cowork scheduled tasks), offer to create a recurring task matching the cadence in `MISSION.md` — prompt along the lines of: "Open the {workspace} folder, read NEXT.md and LEDGER.md, and start today's session — lead with what's due." Keep it in sync: update or remove the task whenever cadence is renegotiated. On file-only platforms, say so once: the workspace can't notice the learner has been gone.
5. **Close** as in the standard session below. Resource search can continue between sessions; note gaps in `RESOURCES.md`.

## Standard session

### 1. Re-entry (≤5 min)

Read [AGENT-BRIEF.md](./AGENT-BRIEF.md), then `NEXT.md` and `LEDGER.md`. Run `python3 scripts/ledger_tools.py check` — fix any errors before proceeding (the ledger is load-bearing; a corrupted fsrs line or dangling prereq silently breaks the frontier). It also lists what's due. Open with the mission, then the map state: what's verified, what's due, what's next. Ask about the homework/assignment from `NEXT.md`.

**Diff teach-back** (project missions): if the project changed since last session, have the learner walk you through the diff — "explain anything you shipped." Code or work they explain well is free generative evidence (record it). Anything they *can't* explain is not shame — it is a **frontier signal**: maximally mission-relevant teaching material, because they already shipped it. Rationale line: "you shipped it; let's make sure you own it."

### 2. Review block (≤25% of session — hard cap)

Run `scripts/fsrs.py status` over ledger nodes to find what's due. If more nodes are due than fit the cap, **triage**: order by mission-relevance × prerequisite-centrality (how many other nodes depend on it). Fold the remainder into the teaching block where today's material naturally exercises them; otherwise they stay due. Never let review consume the session.

Reviews are retrieval-first: free recall before recognition ("explain X from memory" before any multiple choice). Grade and update FSRS state per [PROBE-PROTOCOL.md](./PROBE-PROTOCOL.md).

### 3. Teaching block (bulk of session)

Pick the frontier node ([LEDGER-FORMAT.md](./LEDGER-FORMAT.md)) unless the learner names a target. One capability per lesson. Structure:

1. **Attempt first** — pose the problem before the instruction. Productive failure is the point; 2–5 minutes of struggle, then teach.
2. **Teach** — knowledge from `RESOURCES.md`, cited. Produce/update the lesson HTML.
3. **Practice** — tight feedback loop, ideally automatic. **Practice medium rule: put the friction in the capability, not the tooling.** Choose the lowest-extraneous-load medium that still exercises the target node — the default is interactive, self-checking elements *inside* the lesson HTML (one click to open, instant red/green feedback). External tooling (scripts, terminals, editors) is justified only when operating that tooling *is* the capability being trained — and even then, the learner writes the code attempt-first; never hand them agent-written scaffolds with holes to fill (all the syntax tax, none of the design learning).
4. **The learner does the generative work**: they draft the glossary entry and the one-line ledger evidence summary. You edit.

Same-session assessment caps at L2 (see [PROBE-PROTOCOL.md](./PROBE-PROTOCOL.md)). Schedule the L3 probe ≥72h out via `NEXT.md`.

### 4. Close (5–10 min)

1. Learner writes a one-line takeaway (in their words — this is retrieval, not ceremony).
2. Update `LEDGER.md`: evidence events, FSRS fields (via script), agency log.
3. Write `NEXT.md`: planned frontier node, due re-probes, **one midweek artifact assignment** tied to the mission (code to write, swatch to crochet, paragraph to compose — something inspectable), and optionally a 5-minute self-quiz (3–5 free-recall prompts).
4. Run `python3 scripts/ledger_tools.py map` to regenerate `map.html`, then give a one-sentence map summary: progress + agency trend, training-log tone (see [AGENCY.md](./AGENCY.md)).
5. **Protocol self-audit** — append one line to `NOTES.md`: "Protocol self-audit: steps skipped or bent today — {none | list}." Honest drift is recoverable; silent drift is not.

## Comeback session (gap ≥ 2× cadence)

The avalanche is emotional before it is computational. Order matters:

1. **Mission first, never metrics.** Open with the mission ("how's the back-stiffness been?" / "did the team use the CLI?") — not with the due-count.
2. **Frame decay as physics, not failure.** One line: "Memory decays on a curve; the scheduler already priced this in — a successful review now actually buys unusually long intervals." (True under FSRS: low retrievability → bigger stability gain.)
3. **Triage hard.** Review cap stays at 25%. Pick 2–3 due nodes by prerequisite-centrality. Everything else folds into future lessons or waits. Say so explicitly: "the rest re-verify as they come up — nothing is lost."
4. **First action = easiest win.** Open with the re-probe most likely to succeed. Momentum before rigor.
5. **Collect the dropout data.** Ask what happened, without judgment. Was the homework dose too big? Cadence unrealistic? Record the cause in `NOTES.md`; renegotiate cadence/dose in `MISSION.md`. Re-prescribing the dose that caused the dropout is a protocol failure. If a scheduled nudge exists, update it to the new cadence.
6. Proceed as a standard session with whatever time remains.

## What this protocol never does

- Lets review swallow the session (cap is hard).
- Probes today's material above L2 today.
- Computes dates or intervals by hand instead of `scripts/fsrs.py`.
- Opens a comeback with a wall of overdue items.
- Imposes friction without its one-line rationale.
- Sends the learner to external tooling when an in-lesson exercise would exercise the same node.
