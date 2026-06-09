# Probe Protocol (Assessor Mode)

Probes are how capability levels are earned. Everything else in the system adapts to the learner; this file does not. **Soft teaching, hard measurement.**

## Ground rules

1. **Assessor mode is declared.** Announce the switch: "Assessor mode — I won't help until we're done; I'll record your answer as given." Exit is also declared.
2. **Probes are generated fresh every time.** Same deep structure, novel surface features. Nothing to leak, nothing to memorize. Old probe transcripts are study material, not future probes.
3. **No help during a probe.** Clarifying the *task statement* is allowed; hints are not. If the learner asks for help mid-probe, the probe ends as a skip.
4. **A skipped probe records as unknown** — node goes/stays due. Never silently passed, never punished beyond honesty. Rationale (said once): "the map only works if it's honest — it decides what you never get taught."
5. **Timing caps:** material introduced today caps at L2 today. L3 requires ≥72h since the node was last touched (taught, reviewed, or used) — time-based, not session-based. Back-to-back weekend sessions do not unlock L3.

## Probe types

- **Recall** — free recall first ("explain X from memory"), recognition only as a fallback. Evidence ceiling: L1.
- **Application** — a task resembling the practice context, performed live, unaided. Ceiling: L2.
- **Far transfer** — novel surface, same deep structure ("you've error-chained file I/O; now do env-var config parsing"). Ceiling: L3.
- **Artifact** — the learner makes a thing and shows it (photo of the swatch, running code, composed paragraph). Far-transfer artifacts ("a stitch pattern you haven't used, photographed") are the strongest probes available — for hands-domains the model cannot do them for the learner.
- **Teach-back** — learner teaches the concept; must survive one adversarial follow-up question. Ceiling: L4.

### Evidence rules by domain

- **Agent-assisted domains (code, writing, anything the model itself is good at): only live, in-session production counts as ledger evidence.** Repo artifacts and homework are *context and frontier signal* (see diff teach-back in SESSION-PROTOCOL.md), never level evidence — the capability in them may be the model's. Where possible, grade mechanically: compile it, run it, `cargo test` it.
- **Hands domains (crochet, cooking, hardware):** photo/video/working-object artifacts are first-class evidence.
- **Self-report is never level evidence.** It feeds pacing and the practice log only.
- **Prior-knowledge claims** ("I already know X"): respond with a 2-question calibration probe before setting any level. Record claimed depth vs. demonstrated depth.

## Pre-flight check (before posing any probe)

Every probe declares, in the transcript file *before* it is posed:

```md
- target: N07 @ L3
- requires: N03 (≥L2, not due) ✓, N04 (≥L2, not due) ✓
- must-not-require: anything outside ledger; specifically checked: no serde, no lifetimes
- solution sketch: <2-3 lines — what a passing answer contains>
- pass criteria: <observable, gradeable>
```

Validate `requires` against the ledger. **A probe that turns out to need an untaught or due node is VOID, not a fail** — annotate, regenerate.

## Grading: fresh-context subagent

The grader must not be the teacher. Spawn a fresh-context subagent (Task tool, no conversation history) with exactly: the probe text, the pass criteria and solution sketch, the rubric row for the target level, relevant `GLOSSARY.md` excerpts, and the learner's **verbatim** response. Not the teaching history, not the rapport.

Grader instructions (include verbatim in the subagent prompt):

> Grade strictly against the criteria. Your rationale must quote specific evidence from the response. Fluency is not understanding; a confident wrong answer is wrong. When in doubt, grade down — a false positive corrupts the learner's map and harms them. Return: grade (Again/Hard/Good/Easy), rationale with quotes, one observed gap if any.

**Fallback when subagents are unavailable** (platform has no Task/spawn tool): grade in-conversation, but declared and constrained — state "no fresh-context grader available on this platform, so validity is degraded"; write the pre-flight pass criteria *before* seeing the response; grade strictly against them using the same instructions above, quoting evidence; and mark the evidence entry `graded: in-context` in the ledger so a future fresh-context re-probe knows to confirm it. Never silently substitute self-grading for the subagent.

## Grade mapping

| Outcome | Grade | FSRS | Ledger effect |
|---|---|---|---|
| Failed / major gaps | Again (1) | forget curve | level unchanged; node due; 2nd consecutive fail at an achieved level → flag `mis-carve?` |
| Passed below target level | Hard (2) | small gain | evidence recorded at the level actually demonstrated |
| Clean pass at target | Good (3) | normal gain | level = target |
| Exceeded target | Easy (4) | bonus gain | level = target; consider scheduling next-level probe |

Run `scripts/fsrs.py` immediately and update the node's `fsrs:` line.

## Transcript file

Every probe (including voids and skips) is saved to `probes/NNNN-<node>.md`: pre-flight block, probe as posed, learner response verbatim, grade + rationale (quoted evidence), FSRS update applied. The learner can read everything — transparency is a feature; fresh generation is what protects validity.

## The other-tab problem

During a probe, nothing technically stops the learner consulting another model. Do not police; do not moralize. State the deal once per workspace (and only once): probes measure *for the learner* — a faked level corrupts their own map, and the map decides what they never get taught. After that, trust them like an athlete with their own training log.
