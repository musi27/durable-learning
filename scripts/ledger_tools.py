#!/usr/bin/env python3
"""
ledger_tools.py - integrity checks, due queue, and map rendering for the
learning root.

Everything downstream (frontier, scheduling, prerequisites) trusts the
ledgers, and free-form markdown maintained across many sessions will
drift. This tool makes drift visible.

Canonical layout (protocol v3): a learning root containing registry.md
plus one workspace subfolder per mission. The workspace root is the
learner's surface (MISSION.md, GLOSSARY.md, map.html, lessons/,
reference/); the agent's state lives in system/ (LEDGER.md, NOTES.md,
NEXT.md, RESOURCES.md, probes/). Prerequisites may cross workspaces
("finance:N01"); they resolve through the registry. See LEDGER-FORMAT.md.

Usage:
  python3 scripts/ledger_tools.py check [--ledger system/LEDGER.md] [--root DIR]
  python3 scripts/ledger_tools.py today [--root DIR]
  python3 scripts/ledger_tools.py map   [--ledger system/LEDGER.md] [--out map.html]
  python3 scripts/ledger_tools.py map   --all [--root DIR] [--out map.html]

`check` exits non-zero on errors. Run it at every session open and fix
errors before doing anything else.
`today` walks the registry and emits one triaged due queue across all
registered workspaces.
`map` writes a self-contained map.html for one workspace; `map --all`
writes the aggregate map at the root.
All commands accept --date YYYY-MM-DD to override today (mainly for tests).
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

PROTOCOL_VERSION = 3

NODE_RE = re.compile(r"^###\s+(N\d+)\s*[·:\-]\s*(.+?)\s*$")
PROTOCOL_RE = re.compile(r"^protocol:\s*(\d+)\s*$")
FIELD_RE = re.compile(r"^-\s+(\w[\w-]*):\s*(.*)$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
FSRS_RE = re.compile(
    r"S=([\d.]+)\s+D=([\d.]+)\s+last=(\d{4}-\d{2}-\d{2})\s+due=(\d{4}-\d{2}-\d{2})"
)
LEVEL_RE = re.compile(r"L([0-4])")
EMPTY_VALUES = {"", "—", "-", "none", "n/a"}

WS_HEADER_RE = re.compile(r"^###\s+(\S+)\s*$")
WS_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
QUALIFIED_RE = re.compile(r"^([a-z0-9][a-z0-9_-]*):(N\d+)$")


def parse_ledger(path):
    """Return (nodes, agency, problems, protocol_version)."""
    nodes, agency, problems = {}, [], []
    protocol = None
    current = None
    in_agency = False
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (FileNotFoundError, OSError):
        return nodes, agency, [("error", f"{path} not found")], protocol

    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        pm = PROTOCOL_RE.match(line)
        if pm and protocol is None:
            protocol = int(pm.group(1))
            continue
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
    return nodes, agency, problems, protocol


def parse_registry(path):
    """Return (workspaces, problems, protocol). workspaces maps name ->
    {"name", "line", "fields"}, in registry order. The name doubles as the
    cross-workspace prereq prefix, so it must be a lowercase slug."""
    workspaces, problems = {}, []
    protocol = None
    current = None
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (FileNotFoundError, OSError):
        return {}, [("error", f"{path} not found")], None

    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        pm = PROTOCOL_RE.match(line)
        if pm and protocol is None:
            protocol = int(pm.group(1))
            continue
        m = WS_HEADER_RE.match(line)
        if m:
            name = m.group(1)
            if not WS_NAME_RE.match(name):
                problems.append(("error",
                                 f"registry line {ln}: workspace name '{name}' "
                                 "must be a lowercase slug (a-z, 0-9, -, _) — "
                                 "it is the cross-workspace prereq prefix"))
                current = None
                continue
            if name in workspaces:
                problems.append(("error",
                                 f"registry line {ln}: duplicate workspace '{name}'"))
            current = {"name": name, "line": ln, "fields": {}}
            workspaces[name] = current
            continue
        if current is None:
            continue
        fm = FIELD_RE.match(line)
        if fm:
            current["fields"][fm.group(1).lower()] = fm.group(2).strip()
    return workspaces, problems, protocol


def load_root(root):
    """Parse registry.md and every registered workspace's ledger.
    Returns (workspaces, problems): workspaces maps name ->
    {"name", "dir", "ledger", "fields", "nodes", "agency", "problems",
    "protocol"}, in registry order."""
    root = os.path.abspath(root)
    registry, problems, protocol = parse_registry(os.path.join(root, "registry.md"))
    if registry:
        if protocol is None:
            problems.append(("warning",
                             "registry.md has no 'protocol:' line — add "
                             f"'protocol: {PROTOCOL_VERSION}'"))
        elif protocol > PROTOCOL_VERSION:
            problems.append(("error",
                             f"registry protocol v{protocol} is newer than this "
                             f"skill supports (v{PROTOCOL_VERSION}) — update the "
                             "skill, don't edit the registry"))
        elif protocol < PROTOCOL_VERSION:
            problems.append(("error",
                             f"registry protocol v{protocol} is unsupported — v"
                             f"{PROTOCOL_VERSION} has no migration path; rebuild "
                             "the learning root (LEDGER-FORMAT.md)"))
    workspaces = {}
    for name, ws in registry.items():
        wdir = os.path.join(root, ws["fields"].get("path", name))
        ledger = os.path.join(wdir, "system", "LEDGER.md")
        nodes, agency, wproblems, wprotocol = parse_ledger(ledger)
        workspaces[name] = {"name": name, "dir": wdir, "ledger": ledger,
                            "fields": ws["fields"], "nodes": nodes,
                            "agency": agency, "problems": wproblems,
                            "protocol": wprotocol}
    return workspaces, problems


def workspace_dir(ledger_path):
    """The canonical layout is root/workspace/system/LEDGER.md, so the
    workspace is the ledger's grandparent directory."""
    return os.path.dirname(os.path.dirname(os.path.abspath(ledger_path)))


def find_root(ws_dir):
    """The root is the workspace's immediate parent — if it holds a
    registry.md. No walking further up: that would risk latching onto an
    unrelated registry."""
    parent = os.path.dirname(os.path.abspath(ws_dir))
    if os.path.isfile(os.path.join(parent, "registry.md")):
        return parent
    return None


def discover_root(arg_root):
    """Resolve the learning root for root-level commands: an explicit
    --root, else the cwd, else the cwd's parent (when run from inside a
    workspace). Returns None if no registry.md is found."""
    candidates = [arg_root] if arg_root else [os.getcwd(),
                                              os.path.dirname(os.getcwd())]
    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "registry.md")):
            return os.path.abspath(c)
    return None


def split_prereq(token):
    """'finance:N01' -> ('finance', 'N01'); 'N01' -> (None, 'N01').
    A token with a colon that doesn't parse comes back as (None, token)."""
    m = QUALIFIED_RE.match(token)
    if m:
        return m.group(1), m.group(2)
    return None, token


def make_resolver(local_nodes, workspaces=None):
    """Return fn(prereq_token) -> node dict or None, resolving bare ids
    locally and 'ws:Nxx' ids through the loaded root."""
    def resolve(token):
        ws, nid = split_prereq(token)
        if ws is None:
            return local_nodes.get(nid)
        if workspaces and ws in workspaces:
            return workspaces[ws]["nodes"].get(nid)
        return None
    return resolve


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


def arg_date(args):
    if getattr(args, "date", None):
        d = parse_iso(args.date)
        if d is None:
            sys.exit(f"error: bad --date {args.date!r} (want YYYY-MM-DD)")
        return d
    return date.today()


def detect_cycle(graph):
    """graph: key -> [prereq keys]. Returns a cycle path or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}

    def visit(k, path):
        color[k] = GRAY
        for p in graph.get(k, []):
            if p not in color:
                continue
            if color[p] == GRAY:
                return path + [p]
            if color[p] == WHITE:
                found = visit(p, path + [p])
                if found:
                    return found
        color[k] = BLACK
        return None

    for k in graph:
        if color[k] == WHITE:
            cycle = visit(k, [k])
            if cycle:
                return cycle
    return None


def local_graph(nodes):
    return {nid: [p for p in node_prereqs(n) if p in nodes]
            for nid, n in nodes.items()}


def global_graph(workspaces):
    """Prereq graph across the whole root, keyed 'ws:Nxx'. Bare prereq ids
    qualify to their own workspace; edges to missing nodes are dropped
    (their absence is reported separately by `check`)."""
    graph = {}
    for wname, ws in workspaces.items():
        for nid, node in ws["nodes"].items():
            edges = []
            for p in node_prereqs(node):
                pws, pid = split_prereq(p)
                edges.append(f"{pws or wname}:{pid}")
            graph[f"{wname}:{nid}"] = edges
    return {k: [e for e in edges if e in graph] for k, edges in graph.items()}


def dependent_counts(workspaces):
    """key -> number of nodes (anywhere in the root) that list it as a
    prereq. This is the prerequisite-centrality used for triage."""
    counts = {}
    for edges in global_graph(workspaces).values():
        for e in edges:
            counts[e] = counts.get(e, 0) + 1
    return counts


def is_due(node, today):
    f = node_fsrs(node)
    if not f:
        return False
    d = parse_iso(f["due"])
    return d is not None and today >= d


def node_state(node, resolve, today):
    """unstarted | frontier | verified | due | knowledge-only.
    A prereq satisfies only if it resolves, is >= L2, and is not due —
    the same rule whether it lives in this workspace or a sibling."""
    if "knowledge-only" in node["fields"].get("flags", ""):
        return "knowledge-only"
    lvl = node_level(node)
    if lvl >= 1 and is_due(node, today):
        return "due"
    if lvl >= 2:
        return "verified"
    ready = True
    for p in node_prereqs(node):
        pn = resolve(p)
        if pn is None or node_level(pn) < 2 or is_due(pn, today):
            ready = False
            break
    if ready:
        return "frontier"
    return "verified" if lvl == 1 else "unstarted"


def collect_due_queue(workspaces, today):
    """One triaged list across the root: every node at L1+ whose due date
    has arrived, ordered by prerequisite-centrality then days overdue.
    Mission-relevance is the agent's overlay on top of this ordering."""
    counts = dependent_counts(workspaces)
    entries = []
    for wname, ws in workspaces.items():
        for nid, node in ws["nodes"].items():
            if node_level(node) < 1 or not is_due(node, today):
                continue
            f = node_fsrs(node)
            r = None
            if retrievability and parse_iso(f["last"]):
                r = retrievability(f["S"], (today - parse_iso(f["last"])).days)
            key = f"{wname}:{nid}"
            entries.append({"key": key, "ws": wname, "id": nid,
                            "name": node["name"], "level": node_level(node),
                            "overdue": (today - parse_iso(f["due"])).days,
                            "r": r, "unblocks": counts.get(key, 0)})
    entries.sort(key=lambda e: (-e["unblocks"], -e["overdue"], e["key"]))
    return entries


def queue_line(e):
    overdue = "due today" if e["overdue"] == 0 else f"{e['overdue']}d overdue"
    r = f" · R={e['r']:.0%}" if e["r"] is not None else ""
    return (f"{e['key']} · {e['name']} · L{e['level']} · {overdue}{r}"
            f" · unblocks {e['unblocks']}")


def cmd_check(args):
    today = arg_date(args)
    ledger_path = os.path.abspath(args.ledger)
    nodes, agency, problems, protocol = parse_ledger(ledger_path)
    errors = [p for p in problems if p[0] == "error"]
    warnings = [p for p in problems if p[0] == "warning"]

    if protocol is None:
        warnings.append(("warning",
                         "no 'protocol:' line in header — add 'protocol: "
                         f"{PROTOCOL_VERSION}' (see LEDGER-FORMAT.md)"))
    elif protocol > PROTOCOL_VERSION:
        errors.append(("error",
                       f"ledger protocol v{protocol} is newer than this skill "
                       f"supports (v{PROTOCOL_VERSION}) — update the skill, "
                       "don't edit the ledger"))
    elif protocol < PROTOCOL_VERSION:
        errors.append(("error",
                       f"ledger protocol v{protocol} is unsupported — v"
                       f"{PROTOCOL_VERSION} has no migration path; rebuild "
                       "the workspace (LEDGER-FORMAT.md)"))

    ws_dir = workspace_dir(ledger_path)
    root = os.path.abspath(args.root) if args.root else find_root(ws_dir)
    workspaces, own_name = None, None
    if root:
        workspaces, reg_problems = load_root(root)
        for sev, msg in reg_problems:
            (errors if sev == "error" else warnings).append((sev, msg))
        for name, ws in workspaces.items():
            if os.path.realpath(ws["dir"]) == os.path.realpath(ws_dir):
                own_name = name
        if own_name is None:
            warnings.append(("warning",
                             "this workspace is not listed in "
                             f"{os.path.join(root, 'registry.md')} — "
                             "cross-workspace prereqs pointing here will "
                             "not resolve"))
        for name, ws in workspaces.items():
            if name == own_name:
                continue
            for sev, msg in ws["problems"]:
                if sev == "error":
                    warnings.append(("warning", f"sibling '{name}': {msg}"))

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
            pws, pid = split_prereq(p)
            if pws is None:
                if ":" in p:
                    errors.append(("error",
                                   f"{nid}: malformed prereq '{p}' — expected "
                                   "'Nxx' or 'workspace:Nxx' with a lowercase "
                                   "workspace slug"))
                elif pid not in nodes:
                    errors.append(("error", f"{nid}: prereq {p} does not exist"))
            elif workspaces is None:
                errors.append(("error",
                               f"{nid}: cross-workspace prereq '{p}' but no "
                               "registry.md in the parent directory — "
                               "workspaces live under a learning root "
                               "(LEDGER-FORMAT.md)"))
            elif pws not in workspaces:
                errors.append(("error",
                               f"{nid}: prereq '{p}' names workspace '{pws}' "
                               "which is not in registry.md"))
            elif pid not in workspaces[pws]["nodes"]:
                errors.append(("error",
                               f"{nid}: prereq '{p}' — node {pid} not found "
                               f"in workspace '{pws}'"))
        for ed in node["evidence_dates"]:
            if parse_iso(ed) and parse_iso(ed) > today:
                warnings.append(("warning", f"{nid}: evidence dated in the future ({ed})"))

    if workspaces and own_name:
        cycle = detect_cycle(global_graph(workspaces))
    else:
        cycle = detect_cycle(local_graph(nodes))
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


def cmd_today(args):
    today = arg_date(args)
    root = discover_root(args.root)
    if root is None:
        sys.exit("error: no registry.md found — pass --root or run from the "
                 "learning root (see LEDGER-FORMAT.md)")
    workspaces, problems = load_root(root)
    errors = [m for s, m in problems if s == "error"]
    for name, ws in workspaces.items():
        errors.extend(f"{name}: {m}" for s, m in ws["problems"] if s == "error")

    queue = collect_due_queue(workspaces, today)
    clear = [n for n, ws in workspaces.items()
             if not any(e["ws"] == n for e in queue)]

    print(f"unified due queue · {today.isoformat()} · "
          f"{len(queue)} due across {len(workspaces)} workspaces")
    if queue:
        print()
        for i, e in enumerate(queue, 1):
            print(f"  {i}. {queue_line(e)}")
        print()
        if clear:
            print(f"nothing due: {', '.join(clear)}")
        print("triage: take in order (prereq-centrality, then overdue), "
              "weigh mission-relevance; review cap stays 25% — fold the "
              "rest into teaching.")
    else:
        print("  nothing due today.")
    for msg in errors:
        print(f"  ERROR   {msg}")
    sys.exit(1 if errors else 0)


STATE_STYLE = {
    "verified": ("#2e7d32", "verified"),
    "due": ("#ef6c00", "due for re-probe"),
    "frontier": ("#1565c0", "frontier - ready to learn"),
    "unstarted": ("#9e9e9e", "not started"),
    "knowledge-only": ("#6a1b9a", "knowledge-only"),
}

MAP_CSS = """
body{font-family:-apple-system,Segoe UI,sans-serif;margin:2rem;color:#212121;background:#fafafa}
h1{font-size:1.4rem} h2{font-size:1.1rem;margin:1.4rem 0 .4rem}
h3{font-size:1rem;margin:.2rem 0 .6rem}
.slices{display:flex;flex-wrap:wrap;gap:1rem;align-items:flex-start}
.slice{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:1rem;min-width:240px;flex:1}
.node{border-left:4px solid #ccc;padding:.4rem .6rem;margin:.4rem 0;background:#fcfcfc}
.lvl{font-size:.75rem;background:#eee;border-radius:4px;padding:0 .3rem}
.meta{font-size:.75rem;color:#757575}
.chip{color:#fff;font-size:.7rem;border-radius:4px;padding:.1rem .4rem}
.agency{margin-top:1.2rem;font-size:.85rem;color:#424242}
.queue{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:.8rem 1rem;margin:.8rem 0;font-size:.9rem}
"""


def slices_html(nodes, resolve, today, heading_tag="h2"):
    slices = {}
    for nid, node in nodes.items():
        s = node["fields"].get("slice", "").strip() or "(no slice)"
        slices.setdefault(s, []).append(nid)

    cards = []
    for sname in sorted(slices):
        items = []
        for nid in sorted(slices[sname]):
            node = nodes[nid]
            state = node_state(node, resolve, today)
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
        cards.append(f"<div class='slice'><{heading_tag}>{html.escape(sname)}"
                     f"</{heading_tag}>" + "".join(items) + "</div>")
    return "<div class='slices'>" + "".join(cards) + "</div>"


def agency_trend(agency, today):
    reaches = [a for a in agency if "reach" in a[1].lower()]
    recent = [a for a in reaches
              if parse_iso(a[0]) and (today - parse_iso(a[0])).days <= 14]
    prev = [a for a in reaches
            if parse_iso(a[0]) and 14 < (today - parse_iso(a[0])).days <= 28]
    return (f"{len(recent)} reaches in the last 14 days "
            f"(vs {len(prev)} the 14 days before) · {len(reaches)} total")


def map_doc(title, today, body):
    legend = " ".join(
        f"<span class='chip' style='background:{c}'>{l}</span>"
        for c, l in STATE_STYLE.values()
    )
    return (f"<!DOCTYPE html><html><head><meta charset=\"utf-8\">\n"
            f"<title>{html.escape(title)}</title><style>{MAP_CSS}</style>"
            f"</head><body>\n<h1>{html.escape(title)} · {today.isoformat()}"
            f"</h1>\n<div>{legend}</div>\n{body}\n</body></html>")


def cmd_map(args):
    today = arg_date(args)
    if args.all:
        return map_all(args, today)

    nodes, agency, problems, _protocol = parse_ledger(args.ledger)
    if any(p[0] == "error" for p in problems):
        print("ledger has parse errors - run `check` first", file=sys.stderr)
    ws_dir = workspace_dir(args.ledger)
    root = find_root(ws_dir)
    workspaces = load_root(root)[0] if root else None
    resolve = make_resolver(nodes, workspaces)

    body = slices_html(nodes, resolve, today)
    body += (f"<div class='agency'><strong>Agency log:</strong> "
             f"{agency_trend(agency, today)} - a training log, not a "
             "conscience.</div>")
    # the map is the learner's surface: it lands in the workspace root,
    # not in system/
    out = args.out or os.path.join(ws_dir, "map.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(map_doc("Capability map", today, body))
    print(f"wrote {out} ({len(nodes)} nodes)")


def map_all(args, today):
    root = discover_root(args.root)
    if root is None:
        sys.exit("error: map --all needs a learning root — pass --root or "
                 "run from the root (see LEDGER-FORMAT.md)")
    workspaces, problems = load_root(root)
    for name, ws in workspaces.items():
        for sev, msg in ws["problems"]:
            if sev == "error":
                print(f"{name}: {msg} - run `check` first", file=sys.stderr)

    queue = collect_due_queue(workspaces, today)
    if queue:
        rows = "".join(f"<div>{html.escape(queue_line(e))}</div>" for e in queue)
        body = (f"<div class='queue'><strong>Due across all workspaces "
                f"({len(queue)}):</strong>{rows}</div>")
    else:
        body = "<div class='queue'>Nothing due today.</div>"

    agency_all, total_nodes = [], 0
    for name, ws in workspaces.items():
        resolve = make_resolver(ws["nodes"], workspaces)
        cadence = ws["fields"].get("cadence", "")
        sub = f" <span class='meta'>{html.escape(cadence)}</span>" if cadence else ""
        body += (f"<section><h2>{html.escape(name)}{sub}</h2>"
                 + slices_html(ws["nodes"], resolve, today, heading_tag="h3")
                 + "</section>")
        agency_all.extend(ws["agency"])
        total_nodes += len(ws["nodes"])

    body += (f"<div class='agency'><strong>Agency log (all workspaces):"
             f"</strong> {agency_trend(agency_all, today)} - a training log, "
             "not a conscience.</div>")
    out = args.out or os.path.join(root, "map.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(map_doc("Learning map", today, body))
    print(f"wrote {out} ({total_nodes} nodes across {len(workspaces)} workspaces)")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="validate a workspace's system/LEDGER.md")
    pc.add_argument("--ledger", default=os.path.join("system", "LEDGER.md"))
    pc.add_argument("--root", help="learning root (default: the workspace's parent)")
    pc.add_argument("--date", help="override today, YYYY-MM-DD")
    pc.set_defaults(fn=cmd_check)

    pt = sub.add_parser("today",
                        help="unified due queue across all registered workspaces")
    pt.add_argument("--root", help="learning root (default: auto-discover)")
    pt.add_argument("--date", help="override today, YYYY-MM-DD")
    pt.set_defaults(fn=cmd_today)

    pm = sub.add_parser("map", help="render map.html (one workspace, or --all)")
    pm.add_argument("--ledger", default=os.path.join("system", "LEDGER.md"))
    pm.add_argument("--all", action="store_true",
                    help="aggregate map across the learning root")
    pm.add_argument("--root", help="learning root for --all (default: auto-discover)")
    pm.add_argument("--out", default=None,
                    help="output path (default: <workspace>/map.html; "
                         "for --all, <root>/map.html)")
    pm.add_argument("--date", help="override today, YYYY-MM-DD")
    pm.set_defaults(fn=cmd_map)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
