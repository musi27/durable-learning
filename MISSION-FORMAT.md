# MISSION.md Format

`MISSION.md` captures *why* the learner is here. Every decision — what to teach next, what homework to assign, which sources to trust — traces back to it. If the learner cannot articulate why, interview them before writing anything; a bad mission is worse than no mission.

## Template

```md
# Mission: {Topic}

## Why
{1–3 sentences. The concrete real-world outcome. "Ship a Rust CLI my team uses" beats "learn Rust."}

## Success looks like
- {Specific, observable capability}
- {…}

## Cadence
- Sessions: {e.g., Saturdays ~90 min}
- Midweek homework: {yes/no; dose — renegotiated after any dropout}

## Constraints
- {Time, budget, equipment, prior commitments}

## Strictness
- Complexity: {low | medium | high} — dials scaffolding, lesson size, review load.
  Assessment standards never dial. See PROBE-PROTOCOL.md.

## Scope gate (agent fills at cold start)
- Artifact-verifiable: {yes / partial / no} — {what artifacts exist}
- Harm-cost of wrong assessment: {low / high} — {notes}
- Mode: {full | knowledge-only for: …}
- Red-flag check: {none / e.g., "pain present → professional sign-off advised before practice"}

## Out of scope
- {Adjacent topics explicitly deferred — protects the frontier}
```

## Rules

- **One mission per workspace.** Two unrelated goals = two workspaces.
- **Concrete over abstract.** Push for the outcome behind "understand X."
- **Project missions decompose by vertical slice** (see LEDGER-FORMAT.md): first session ends with a working artifact, concepts attach to the slice that first needs them.
- **Revise on contact with reality.** Missions legitimately shift as capability grows. Confirm with the learner, update the file, note the shift in `NOTES.md`. Comeback sessions explicitly renegotiate cadence and homework dose.
- **Keep it under a screen.** A long mission is a plan, not a compass.

## The scope gate

Classify the topic on two axes before teaching anything:

**Axis 1 — artifact-verifiability.** Can the learner *show* rather than *tell*? Code runs; a crochet swatch photographs; a configured server responds; a composed paragraph is right there. Movement form, internal sensation, and live interpersonal performance cannot be shown to an agent.

**Axis 2 — harm-cost of wrong assessment.** When grading is wrong: frogged scarf, or herniated disc? Wasted weekend, or medical/financial/legal damage?

| | Low harm | High harm |
|---|---|---|
| **Verifiable** | Full mode | Full mode + explicit caution nodes |
| **Unverifiable** | Full, flagged: evidence limited to teach-back/knowledge proxies | **Knowledge-only mode** |

**Knowledge-only mode** (e.g., yoga, lifting form, anything pain/health-adjacent, high-stakes financial or legal *action*): teach the verifiable knowledge layer — terminology, theory, how to evaluate teachers/providers, what good instruction looks like — and never coach the practice itself. The ledger never contains a practice-capability node for that domain. The line does not creep: "just one alignment tip" is coaching.

**Never plainly refuse — always explain the delegation.** Template (adapt):

> "I'll teach you the knowledge layer of this — {vocabulary, theory, how to choose a good teacher} — but I won't coach your {form/practice}. Two reasons: I can't observe you, so any feedback I gave would be fake confidence; and in this domain fake confidence costs {injuries}, not {unraveled scarves}. A {teacher} who can watch you closes the feedback loop I can't. Here's what I *can* verify and teach…"

This is legible pedagogy applied to scope: the learner leaves knowing *why* the line sits where it does — which is itself a lesson about feedback loops.

**Red-flag check** for any health-adjacent topic: existing pain, injury, or medical conditions get a "see a professional first" note in the mission, stated once, kindly, without drama.
