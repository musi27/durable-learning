#!/usr/bin/env python3
"""
ledger_tools.py - integrity checks and map rendering for LEDGER.md.

Everything downstream (frontier, scheduling, prerequisites) trusts the
ledger, and a free-form markdown file maintained across many sessions
will drift. This tool makes drift visible.

Usage:
  python3 scripts/ledger_tools.py check [--ledger LEDGER.md]
  python3 scripts/ledger_tools.py map   [--ledger LEDGER.md] [--out map.html]

`check` exits non-zero on errors. Run it at every session open and fix
errors before doing anything else.
`map` writes a self-contained map.html: slices, node states, agency trend.
"""

import argparse
import html
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from fsrs import retrievability
except ImportError:
    retrievability = None

NODE_RE = re.compile(r"^###\s+(N\d+)\s*[·:\-]\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^-\s+(\w[\w-]*):\s*(.*)$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
FSRS_RE = re.compile(
    r"S=([\d.]+)\s+D=([\d.]+)\s+last=(\d{4}-\d{2}-\d{2})\s+due=(\d{4}-\d{2}-\d{2})"
)
LEVEL_RE = re.compile(r"L([0-4])")
EMPTY_VALUES = {"", "—", "-", "none", "n/a"}


def parse_ledger(path):
    """Return (nodes: dict, agency: list of (date_str, line), problems: list)."""
    nodes, agency, problems = {}, [], []
    current = None
    in_agency = False
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return nodes, agency, [("error", f"{path} not found")]

    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.startswith("## "):
            in_agency = "agency log" in line.lower()
            current = None
            continue
        m = NODE_RE.match(line)
        if m:
            nid, name = m.group(1), m.group(2)
            if nid in nodes:
                problems.append(("error", f"line {ln}: duplicate node id {nid}"))
            current = {"id": nid, "name": name, "line": ln, "fields": {},
                       "evidence_dates": []}
            nodes[nid] = current
            in_agency = False
            continue
        if in_agency:
            lm = re.match(r"^-\s+(\d{4}-\d{2}-\d{2})\s*[·:]\s*(.*)$", line)
            if lm:
                agency.append((lm.group(1), lm.group(2)))
            elif line.startswith("- ") and line.strip() != "-":
                problems.append(("warning",
                                 f"line {ln}: agency entry without parseable date"))
            continue
        if current is None:
            continue
        fm = FIELD_RE.match(line)
        if fm:
            current["fields"][fm.group(1).lower()] = fm.group(2).strip()
            continue
        em = re.match(r"^\s+-\s+(\d{4}-\d{2}-\d{2})", line)
        if em:
            current["evidence_dates"].append(em.group(1))
    return nodes, agency, problems


def node_level(node):
    m = LEVEL_RE.search(node["fields"].get("level", ""))
    return int(m.group(1)) if m else 0


def node_prereqs(node):
    raw = node["fields"].get("prereqs", "")
    if raw.lower() in EMPTY_VALUES:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def node_fsrs(node):
    m = FSRS_RE.search(node["fields"].get("fsrs", ""))
    if not m:
        return None
    return {"S": float(m.group(1)), "D": float(m.group(2)),
            "last": m.group(3), "due": m.group(4)}


def parse_iso(s):
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def detect_cycle(nodes):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in nodes}

    def visit(nid, path):
        color[nid] = GRAY
        for p in node_prereqs(nodes[nid]):
            if p not in nodes:
                continue
            if color[p] == GRAY:
                return path + [p]
            if color[p] == WHITE:
                found = visit(p, path + [p])
                if found:
                    return found
        color[nid] = BLACK
        return None

    for nid in nodes:
        if color[nid] == WHITE:
            cycle = visit(nid, [nid])
            if cycle:
                return cycle
    return None


def is_due(node, today):
    f = node_fsrs(node)
    if not f:
        return False
    d = parse_iso(f["due"])
    return d is not None and today >= d


def node_state(node, nodes, today):
    """unstarted | frontier | verified | due | knowledge-only"""
    if "knowledge-only" in node["fields"].get("flags", ""):
        return "knowledge-only"
    lvl = node_level(node)
    if lvl >= 1 and is_due(node, today):
        return "due"
    if lvl >= 2:
        return "verified"
    prereqs = node_prereqs(node)
    ready = all(
        p in nodes and node_level(nodes[p]) >= 2 and not is_due(nodes[p], today)
        for p in prereqs
    )
    if ready:
        return "frontier"
    return "verified" if lvl == 1 else "unstarted"


def cmd_check(args):
    today = date.today()
    nodes, agency, problems = parse_ledger(args.ledger)
    errors = [p for p in problems if p[0] == "error"]
    warnings = [p for p in problems if p[0] == "warning"]

    for nid, node in nodes.items():
        lvl = node_level(node)
        if "level" not in node["fields"]:
            warnings.append(("warning", f"{nid}: missing level field (treated as L0)"))
        f = node_fsrs(node)
        if lvl >= 1 and f is None:
            errors.append(("error",
                           f"{nid}: level L{lvl} but fsrs line missing or malformed "
                           f"(expected 'S=.. D=.. last=YYYY-MM-DD due=YYYY-MM-DD')"))
        if f:
            last, due = parse_iso(f["last"]), parse_iso(f["due"])
            if last is None or due is None:
                errors.append(("error", f"{nid}: unparseable fsrs date"))
            else:
                if due < last:
                    errors.append(("error", f"{nid}: due {due} before last {last}"))
                if last > today:
                    warnings.append(("warning", f"{nid}: last review {last} is in the future"))
        for p in node_prereqs(node):
            if p not in nodes:
                errors.append(("error", f"{nid}: prereq {p} does not exist"))
        for ed in node["evidence_dates"]:
            if parse_iso(ed) and parse_iso(ed) > today:
                warnings.append(("warning", f"{nid}: evidence dated in the future ({ed})"))

    cycle = detect_cycle(nodes)
    if cycle:
        errors.append(("error", "prerequisite cycle: " + " -> ".join(cycle)))

    due_nodes = [nid for nid, n in nodes.items()
                 if node_level(n) >= 1 and is_due(n, today)]

    print(f"ledger check: {len(nodes)} nodes, {len(agency)} agency entries")
    for _, msg in errors:
        print(f"  ERROR   {msg}")
    for _, msg in warnings:
        print(f"  warning {msg}")
    if due_nodes:
        print(f"  due for re-probe: {', '.join(sorted(due_nodes))}")
    if not errors and not warnings:
        print("  clean.")
    sys.exit(1 if errors else 0)


STATE_STYLE = {
    "verified": ("#2e7d32", "verified"),
    "due": ("#ef6c00", "due for re-probe"),
    "frontier": ("#1565c0", "frontier - ready to learn"),
    "unstarted": ("#9e9e9e", "not started"),
    "knowledge-only": ("#6a1b9a", "knowledge-only"),
}


def cmd_map(args):
    today = date.today()
    nodes, agency, problems = parse_ledger(args.ledger)
    if any(p[0] == "error" for p in problems):
        print("ledger has parse errors - run `check` first", file=sys.stderr)

    slices = {}
    for nid, node in nodes.items():
        s = node["fields"].get("slice", "").strip() or "(no slice)"
        slices.setdefault(s, []).append(nid)

    reaches = [a for a in agency if "reach" in a[1].lower()]
    recent = [a for a in reaches
              if parse_iso(a[0]) and (today - parse_iso(a[0])).days <= 14]
    prev = [a for a in reaches
            if parse_iso(a[0]) and 14 < (today - parse_iso(a[0])).days <= 28]

    cards = []
    for sname in sorted(slices):
        items = []
        for nid in sorted(slices[sname]):
            node = nodes[nid]
            state = node_state(node, nodes, today)
            color, label = STATE_STYLE[state]
            lvl = node_level(node)
            extra = ""
            f = node_fsrs(node)
            if f and retrievability and parse_iso(f["last"]):
                el = (today - parse_iso(f["last"])).days
                r = retrievability(f["S"], el)
                extra = f"<div class='meta'>R={r:.0%} · due {f['due']}</div>"
            items.append(
                f"<div class='node' style='border-left-color:{color}'>"
                f"<span class='lvl'>L{lvl}</span> "
                f"<strong>{html.escape(node['name'])}</strong>"
                f"<div class='meta'>{nid} · {label}</div>{extra}</div>"
            )
        cards.append(f"<div class='slice'><h2>{html.escape(sname)}</h2>"
                     + "".join(items) + "</div>")

    trend = (f"{len(recent)} reaches in the last 14 days "
             f"(vs {len(prev)} the 14 days before) · {len(reaches)} total")
    legend = " ".join(
        f"<span class='chip' style='background:{c}'>{l}</span>"
        for c, l in STATE_STYLE.values()
    )

    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Capability map</title><style>
body{{font-family:-apple-system,Segoe UI,sans-serif;margin:2rem;color:#212121;background:#fafafa}}
h1{{font-size:1.4rem}} h2{{font-size:1rem;margin:.2rem 0 .6rem}}
.slices{{display:flex;flex-wrap:wrap;gap:1rem;align-items:flex-start}}
.slice{{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:1rem;min-width:240px;flex:1}}
.node{{border-left:4px solid #ccc;padding:.4rem .6rem;margin:.4rem 0;background:#fcfcfc}}
.lvl{{font-size:.75rem;background:#eee;border-radius:4px;padding:0 .3rem}}
.meta{{font-size:.75rem;color:#757575}}
.chip{{color:#fff;font-size:.7rem;border-radius:4px;padding:.1rem .4rem}}
.agency{{margin-top:1.2rem;font-size:.85rem;color:#424242}}
</style></head><body>
<h1>Capability map · {today.isoformat()}</h1>
<div>{legend}</div>
<div class="slices">{''.join(cards)}</div>
<div class="agency"><strong>Agency log:</strong> {trend} - a training log, not a conscience.</div>
</body></html>"""

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"wrote {args.out} ({len(nodes)} nodes)")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="validate LEDGER.md integrity")
    pc.add_argument("--ledger", default="LEDGER.md")
    pc.set_defaults(fn=cmd_check)

    pm = sub.add_parser("map", help="render LEDGER.md to map.html")
    pm.add_argument("--ledger", default="LEDGER.md")
    pm.add_argument("--out", default="map.html")
    pm.set_defaults(fn=cmd_map)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
