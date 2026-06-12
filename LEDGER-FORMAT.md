# LEDGER.md Format

`system/LEDGER.md` is the source of truth for what the learner can do, how confidently we know it, and what to teach next. It replaces both "learning records" and any invisible model of the learner. If it isn't in the ledger, the system doesn't know it.

## The learning root

Workspaces do not stand alone. The canonical layout is a **learning root**: one parent folder holding `registry.md`, the aggregate `map.html`, and one workspace subfolder per mission. Inside a workspace, the top level is the **learner's surface** — only files the learner uses — and `system/` is the agent's state: inspectable, never required reading.

```
learning/
  registry.md          list of workspaces (format below)
  map.html             aggregate map — `ledger_tools.py map --all`
  finance/
    MISSION.md, GLOSSARY.md, map.html, lessons/, reference/    ← the learner's
    system/                                                    ← the agent's
      LEDGER.md, NOTES.md, NEXT.md, RESOURCES.md, probes/
  rust-cli/
    …
```

`registry.md` format:

```md
# Learning Registry
protocol: 3

### finance
- path: finance
- cadence: daily · 30 min

### rust-cli
- cadence: 3x/week · 60 min
```

Each `###` header names a workspace. The name must be a lowercase slug (`a-z`, `0-9`, `-`, `_`) because it doubles as the prefix in cross-workspace prerequisites (`finance:N01`). Fields per workspace: `path` — folder relative to the root, defaults to the name; `cadence` — display only (the binding cadence lives in that workspace's `MISSION.md`). Cold start creates the root structure when it is missing ([SESSION-PROTOCOL.md](./SESSION-PROTOCOL.md)); the tools find the root by looking for `registry.md` in the workspace's parent folder, and each workspace's ledger at `<workspace>/system/LEDGER.md`. The registry carries the same protocol stamp as the ledgers and is rejected on the same terms.

## File header

The ledger begins with:

```md
# Capability Ledger
protocol: 3
```

The `protocol:` line ties the workspace to the ledger syntax version this skill expects. The linter warns when it is missing and **rejects any other version**: older ones have no migration path (v1–v2 predate the current layout — rebuild the workspace), and a newer number means the workspace was created by a newer skill, so update the skill rather than hand-editing the ledger.

## Capability levels

| Level | Name | Meaning | Minimum evidence |
|---|---|---|---|
| L0 | Introduced | Material was covered. Coverage is not learning. | none |
| L1 | Retrieved | Recalled the core idea from memory, ≥1 day after introduction | recall probe |
| L2 | Applied | Solved a practice-like task unaided (near transfer) | application probe, live |
| L3 | Transferred | Solved a novel-surface task unaided, ≥72h since last contact with the node | far-transfer probe |
| L4 | Generative | Taught it back surviving an adversarial follow-up, or combined ≥2 nodes (≥1 at L3) in one artifact | teach-back or combination artifact |

`level` is the highest level ever evidenced. Whether it is *currently trusted* is a separate question answered by FSRS (below).

## Node entry format

```md
### N07 · error-handling-with-result
- slice: S2 (parse one log line)
- prereqs: N03, N04
- level: L2 · achieved 2026-06-06
- fsrs: S=8.42 D=6.10 last=2026-06-06 due=2026-06-14
- flags: —
- evidence:
  - 2026-06-06 · L2 · probe 0007 (Good) — wrote the parser unaided; compiled first try
  - 2026-05-30 · L1 · recall in session (Good)
- reaches: 1 · (2026-05-30, asked for solution before attempting, lesson 0004)
```

Flags: `knowledge-only` (scope gate — node about a domain whose practice we don't coach), `prior-knowledge` (claimed already-known; level set only after a calibration probe, see PROBE-PROTOCOL.md), `mis-carve?` (repeated probe failures suggest the node is wrongly decomposed — review the cut before re-teaching).

### Cross-workspace prerequisites

A prerequisite may live in a sibling workspace: `prereqs: N03, finance:N01`. The prefix is the workspace's registry name; the linter resolves the reference by reading the sibling's ledger through `registry.md` and errors on an unknown workspace, a missing node, a malformed prefix, or a workspace that isn't under a learning root. This is how knowledge compounds across missions — a derivatives workspace leans on `finance:N01` instead of re-teaching double-entry.

The one-line evidence summary is **drafted by the learner**, edited by you.

## Scheduling (FSRS)

Each node carries `S` (stability), `D` (difficulty), `last` (last evidence date), `due`. All math via `scripts/fsrs.py`:

- First evidence event: `python3 scripts/fsrs.py new --grade G --date YYYY-MM-DD`
- Subsequent: `python3 scripts/fsrs.py review --stability S --difficulty D --last YYYY-MM-DD --grade G --date YYYY-MM-DD`
- Checking what's due / current retrievability: `python3 scripts/fsrs.py status --stability S --last YYYY-MM-DD`

Grades come from probe outcomes (mapping in [PROBE-PROTOCOL.md](./PROBE-PROTOCOL.md)). FSRS handles early, late, and same-day reviews natively — a successful re-probe after a long gap legitimately earns a long next interval. Trust it.

**A due node cannot satisfy a prerequisite — in any workspace.** It must be re-verified (re-probe at its achieved level) first. This is what makes decay bite without ever deleting history, and the rule crosses workspace boundaries: a due `finance:N01` blocks the derivatives node that depends on it.

## The frontier (what to teach next)

A node is **frontier-eligible** when: its level is L0 or L1, every prerequisite is ≥L2 and not due, and it is not flagged `knowledge-only`-blocked or void. Rank eligible nodes by mission-relevance; ties break toward the node unblocking the most descendants. The learner can always override — record the override.

## Decomposition rules

- **Project missions decompose by vertical slice, not by topic.** Slices (`S1 CLI echoes a file`, `S2 parse one log line`, …) each end in a working artifact; concept nodes attach to the slice that first needs them. Ownership gets taught when the borrow checker first complains — that is when it is learnable. A textbook-chapter map that delays the first working artifact past session 1 is mis-carved.
- Knowledge missions decompose by concept, but every node still names what the learner will be able to *do* (explain, predict, distinguish), not what will be "covered."
- The map is proposed by you and **approved by the learner** at cold start. It is revisable: repeated probe failures on one node trigger the `mis-carve?` check before any re-teaching.
- Keep it small. 8–15 nodes initially; grow as slices complete. A 60-node map at session 1 is a syllabus, not a frontier.

## Agency log

Bottom of the ledger:

```md
## Agency Log
- 2026-06-06 · N07 · attempted twice before asking — asked for review of approach (not a reach)
- 2026-05-30 · N04 · reach: asked for the solution before attempting (lesson 0004)
```

Definition of a reach-event and all framing rules: [AGENCY.md](./AGENCY.md). Per-node counts are mirrored in the node's `reaches` line.

## Machine checking

The formats above are machine-checked — keep the field syntax exactly as shown; the linter, the queue, and the map renderer all parse it.

- `python3 scripts/ledger_tools.py check` validates one workspace (ledger found at `system/LEDGER.md` by default; `--ledger` overrides): protocol version, node ids, prereq references (existence and cycles — cross-workspace references resolved through the registry, with the cycle check spanning sibling ledgers), level fields, fsrs lines, and dates. Run it at every session open and fix errors before anything else.
- `python3 scripts/ledger_tools.py today` walks the registry and emits the **unified due queue**: every due node across every registered workspace in one list, triaged by prerequisite-centrality (how many nodes anywhere depend on it) then days overdue. Mission-relevance is your overlay on that ordering.

## Map view

At session close, run `python3 scripts/ledger_tools.py map` to regenerate the workspace's `map.html` (written to the workspace root — the map belongs to the learner's surface, not `system/`) — a single self-contained HTML view of the ledger: slices as columns, nodes colored by state (unstarted / frontier / verified / due / knowledge-only), current retrievability per node, agency trend at the bottom — and `python3 scripts/ledger_tools.py map --all` to regenerate the aggregate map at the root: every workspace's slices, the unified due queue, and the combined agency trend. Same training-log tone as everything else. This is the learner's progress view; it is not optional.
