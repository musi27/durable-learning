# /durable-learning

**A tutor that measures what actually transferred to you — not what got produced.**

`/durable-learning` is an agent skill that turns any directory into a persistent, multi-session learning workspace. You tell it what you want to learn and why; it teaches you in tightly-scoped lessons, schedules reviews with a real memory model, and — the part no chatbot tutor does — honestly tracks whether the capability ended up in *you*.

Background & problem framing: [Durable learning with a model in the loop](https://musi.live/writing/durable-learning-with-a-model-in-the-loop)

## The problem it exists for

When a model sits in the learning loop, the oldest signal in education breaks: **output no longer proves understanding.** A learner can produce any answer by asking the model, move through material producing correct work, and never find out the capability didn't transfer. The bottleneck moves from *what the learner produces* to *what the learner can do without the model* — and almost nothing measures that.

Two things still determine lasting capability:

- **Compounding** — what you already know determines how fast the next thing sticks.
- **Agency** — the choice, at every gap, between reaching for the model and doing the work yourself. Capability is the residue of effort *you* did; whatever bypasses the effort bypasses the capability.

`/durable-learning` is built to grow both, and to measure both.

## How it's different

**A capability ledger, not a chat history.** Every skill you're building is a node with an evidence level: L1 *retrieved* → L2 *applied* → L3 *transferred* (solved a novel problem, unaided, days later) → L4 *generative* (taught it back and survived a hard follow-up). Levels are earned through probes, never through "we covered it." The ledger computes what you're ready to learn next.

**Teacher and Assessor are separate roles.** The Teacher explains, scaffolds, and adapts to you. The Assessor is a fresh-context grader that sees only your verbatim answer and the rubric — no rapport, no memory of how hard you tried. Teaching is soft; measurement is hard. A skipped probe records as *unknown*, never as a pass.

**Real spaced repetition.** Scheduling runs on [FSRS](https://github.com/open-spaced-repetition/free-spaced-repetition-scheduler) (ML-based spaced repetition algorithm), vendored as a small script. It handles real life: skip three weeks and nothing punishes you — a successful comeback review legitimately earns extra-long intervals. Reviews open every session, capped at 25% so they never swallow it.

**Agency telemetry.** The skill always answers when you ask — and logs when you reached for the answer before attempting. Fully visible, framed like an athlete's training log, never like a conscience. Over weeks you watch your independence compound next to your capability. We believe no other learning tool does this.

**Transfer probes the model can't fake.** Probes are generated fresh each time (same deep structure, novel surface), performed live. In agent-assisted domains like coding, only live in-session work counts as evidence — your repo is context, not proof, because the capability in it might be the model's. Each session opens with a *diff teach-back*: explain what you shipped this week; whatever you can't explain becomes the next lesson, free of shame and perfectly mission-relevant.

**Honest scope.** At setup, the skill classifies your topic on two axes: can evidence be *shown* (code runs, swatches photograph), and what does wrong assessment cost? If the wrong assessment can be costly (i.e. teaching physical exercises with no actual way of verifying your ability to perform them correctly), the skill will hand practice coaching to a human teacher and explain its rationale behind this decision. The explanation is the policy: friction without rationale is treated as a bug everywhere in the system ("legible pedagogy").

**The learner does the generative work.** You draft the glossary definitions and the one-line evidence summaries; the agent only edits. Compression is where learning happens — the system refuses to do it for you.

## What using it feels like

**First session.** A short interview — why do you want this, what does success look like — then a lesson within ten minutes. Project missions ship a working artifact on day one (a CLI that echoes a file), because the map is organized around vertical slices of *your* goal, not textbook chapters. You approve the capability map; it stays revisable.

**A typical session.** Five minutes of re-entry and free-recall review of whatever's due. Then one new capability: you attempt first, then get taught (with citations), then practice in a tight feedback loop. You write the takeaway line. The session closes with a contract for next time, including one midweek artifact assignment.

**Coming back after a gap.** It opens with your mission, not a wall of overdue counts. Decay is treated as physics the scheduler already priced in, the review triages to the few nodes everything else depends on, and it asks what caused the gap — then renegotiates the dose instead of re-prescribing it.

## What it deliberately won't do

Coach physical form or anything it can't observe where errors cost health or money. Count agent-assisted homework as evidence of your skill. Let a skipped probe pass silently. Lecture you about using AI — it logs, you decide. Compute scheduling "intuitively" — math goes through the script. Make you fight tooling: exercises check themselves inside the lesson page unless operating the tooling is the skill you're learning.

## Files

```
durable-learning/
  SKILL.md             entry point — philosophy, roles, workspace map
  SESSION-PROTOCOL.md  cold-start / standard / comeback session shapes
  LEDGER-FORMAT.md     capability nodes, levels, FSRS fields, frontier rule
  PROBE-PROTOCOL.md    Assessor mode — rubric, fresh-context grading, evidence rules
  AGENCY.md            attempt-first contract, reach-events, framing rules
  MISSION-FORMAT.md    mission template + the scope gate
  scripts/fsrs.py      vendored FSRS-6 scheduler (stdlib only)
```

Your learning workspace (created lazily, per topic): `MISSION.md`, `LEDGER.md`, `GLOSSARY.md`, `RESOURCES.md`, `NOTES.md`, `NEXT.md`, plus `lessons/`, `reference/`, and `probes/`. All plain files — inspectable, editable, yours to version-control.

## Install & run

Copy the `durable-learning/` directory into your agent's skills location (e.g. `~/.claude/skills/durable-learning`). Then, one folder per topic:

```bash
mkdir learn-rust && cd learn-rust
/durable-learning how to build a CLI in Rust
```

Come back to the same folder for every session. The workspace is the memory.

**Platform notes.** The core is portable: plain files plus Python stdlib. On platforms with scheduling (e.g. Cowork), the skill offers at setup to create a recurring nudge matching your cadence — a scheduled task that opens the workspace, reads what's due, and starts the session — and keeps it in sync when your cadence changes. On file-only platforms there is no nudge: a file can't notice you've been gone.

## Lineage

This is a learning skill built around transfer measurement and agency, with the purpose being to transfer the capability to the learner. Spaced repetition scheduling algorithm used is [FSRS / py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) (MIT). Pedagogy: retrieval practice & spacing (Roediger/Karpicke; Dunlosky et al. 2013), zone of proximal development (Vygotsky), productive failure (Kapur), autonomy-supportive rationale-giving (self-determination theory). 

Problem framing: [Durable learning with a model in the loop](https://musi.live/writing/durable-learning-with-a-model-in-the-loop).
