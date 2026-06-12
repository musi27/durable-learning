"""Tests for ledger_tools.py v2 — learning root, cross-workspace prereqs,
unified due queue, aggregate map.

Fixture: a two-workspace learning root (finance, rust-cli) where rust-cli
declares a cross-workspace prereq on finance:N01. All date-sensitive
commands take --date so the fixture is deterministic.

Run: python3 -m unittest discover -s tests
"""

import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts" / "ledger_tools.py"
sys.path.insert(0, str(REPO / "scripts"))
import ledger_tools as lt  # noqa: E402

TODAY = "2026-06-12"

REGISTRY = """\
# Learning Registry
protocol: 2

### finance
- path: finance
- cadence: daily · 30 min

### rust-cli
- cadence: 3x/week · 60 min
"""

FINANCE_LEDGER = """\
# Capability Ledger
protocol: 2

## Nodes

### N01 · double-entry
- slice: S1 (read a balance sheet)
- prereqs: —
- level: L3 · achieved 2026-06-01
- fsrs: S=2.00 D=5.00 last=2026-06-01 due=2026-06-08
- flags: —
- evidence:
  - 2026-06-01 · L3 · probe 0003 (Good)

### N02 · accrual-vs-cash
- slice: S1 (read a balance sheet)
- prereqs: N01
- level: L2 · achieved 2026-06-02
- fsrs: S=20.00 D=5.00 last=2026-06-02 due=2026-06-30
- flags: —
- evidence:
  - 2026-06-02 · L2 · probe 0004 (Good)

## Agency Log
- 2026-06-01 · N01 · reach: asked for the solution before attempting (lesson 0002)
"""

RUST_LEDGER = """\
# Capability Ledger
protocol: 2

## Nodes

### N01 · ownership-basics
- slice: S1 (CLI echoes a file)
- prereqs: —
- level: L2 · achieved 2026-05-30
- fsrs: S=1.50 D=6.00 last=2026-06-05 due=2026-06-12
- flags: —
- evidence:
  - 2026-06-05 · L2 · probe 0002 (Good)

### N02 · double-entry-for-budgets
- slice: S2 (budget tracker)
- prereqs: N01, finance:N01
- level: L0
- flags: —

## Agency Log
"""


def run_tool(*argv, cwd=None):
    return subprocess.run([sys.executable, str(TOOL), *argv],
                          capture_output=True, text=True, cwd=cwd)


class RootFixture(unittest.TestCase):
    """Builds the two-workspace root in a temp dir before each test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.write("registry.md", REGISTRY)
        self.write("finance/LEDGER.md", FINANCE_LEDGER)
        self.write("rust-cli/LEDGER.md", RUST_LEDGER)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def check(self, workspace, **kw):
        return run_tool("check", "--ledger",
                        str(self.root / workspace / "LEDGER.md"),
                        "--date", TODAY, **kw)


class TestCheck(RootFixture):
    def test_clean_two_workspace_root(self):
        for ws in ("finance", "rust-cli"):
            r = self.check(ws)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # due detection is date-deterministic: finance N01 is 4d overdue
        self.assertIn("N01", self.check("finance").stdout)

    def test_rejects_protocol_v1(self):
        self.write("finance/LEDGER.md",
                   FINANCE_LEDGER.replace("protocol: 2", "protocol: 1"))
        r = self.check("finance")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unsupported", r.stdout.lower())

    def test_rejects_newer_protocol(self):
        self.write("finance/LEDGER.md",
                   FINANCE_LEDGER.replace("protocol: 2", "protocol: 3"))
        r = self.check("finance")
        self.assertEqual(r.returncode, 1)
        self.assertIn("newer", r.stdout.lower())

    def test_missing_protocol_warns(self):
        self.write("finance/LEDGER.md",
                   FINANCE_LEDGER.replace("protocol: 2\n", ""))
        r = self.check("finance")
        self.assertEqual(r.returncode, 0)
        self.assertIn("protocol", r.stdout.lower())
        self.assertIn("warning", r.stdout.lower())

    def test_unknown_workspace_prefix_is_error(self):
        self.write("rust-cli/LEDGER.md",
                   RUST_LEDGER.replace("finance:N01", "nope:N01"))
        r = self.check("rust-cli")
        self.assertEqual(r.returncode, 1)
        self.assertIn("nope", r.stdout)

    def test_missing_node_in_sibling_is_error(self):
        self.write("rust-cli/LEDGER.md",
                   RUST_LEDGER.replace("finance:N01", "finance:N99"))
        r = self.check("rust-cli")
        self.assertEqual(r.returncode, 1)
        self.assertIn("N99", r.stdout)

    def test_malformed_qualified_prereq_is_error(self):
        self.write("rust-cli/LEDGER.md",
                   RUST_LEDGER.replace("finance:N01", "Finance:N01"))
        r = self.check("rust-cli")
        self.assertEqual(r.returncode, 1)
        self.assertIn("malformed", r.stdout.lower())

    def test_cross_prereq_without_registry_is_error(self):
        # standalone workspace: no registry.md in the parent directory
        with tempfile.TemporaryDirectory() as solo:
            ledger = Path(solo) / "rust-cli" / "LEDGER.md"
            ledger.parent.mkdir()
            ledger.write_text(RUST_LEDGER, encoding="utf-8")
            r = run_tool("check", "--ledger", str(ledger), "--date", TODAY)
            self.assertEqual(r.returncode, 1)
            self.assertIn("registry", r.stdout.lower())

    def test_cross_workspace_cycle_detected(self):
        self.write("finance/LEDGER.md",
                   FINANCE_LEDGER.replace("- prereqs: —\n",
                                          "- prereqs: rust-cli:N02\n", 1))
        r = self.check("finance")
        self.assertEqual(r.returncode, 1)
        self.assertIn("cycle", r.stdout.lower())

    def test_unregistered_workspace_warns(self):
        self.write("orphan/LEDGER.md",
                   "# Capability Ledger\nprotocol: 2\n\n"
                   "### N01 · something\n- level: L0\n")
        r = self.check("orphan")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("not listed", r.stdout)


class TestToday(RootFixture):
    def test_unified_queue_triaged(self):
        r = run_tool("today", "--root", str(self.root), "--date", TODAY)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        # both workspaces' due nodes appear, finance:N01 first
        # (unblocks 2 — finance:N02 and rust-cli:N02 — vs 1 for rust-cli:N01)
        self.assertIn("finance:N01", out)
        self.assertIn("rust-cli:N01", out)
        self.assertLess(out.index("finance:N01"), out.index("rust-cli:N01"))
        self.assertIn("unblocks 2", out)
        self.assertIn("4d overdue", out)
        self.assertIn("due today", out)
        self.assertIn("triage", out.lower())

    def test_discovers_root_from_workspace_dir(self):
        r = run_tool("today", "--date", TODAY, cwd=str(self.root / "finance"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("finance:N01", r.stdout)

    def test_nothing_due(self):
        r = run_tool("today", "--root", str(self.root), "--date", "2026-06-09")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nothing due", r.stdout.lower())

    def test_requires_registry(self):
        with tempfile.TemporaryDirectory() as solo:
            r = run_tool("today", "--date", TODAY, cwd=solo)
            self.assertEqual(r.returncode, 1)

    def test_broken_sibling_ledger_is_error(self):
        (self.root / "rust-cli" / "LEDGER.md").unlink()
        r = run_tool("today", "--root", str(self.root), "--date", TODAY)
        self.assertEqual(r.returncode, 1)
        self.assertIn("rust-cli", r.stdout + r.stderr)


class TestMap(RootFixture):
    def test_map_all_aggregates_at_root(self):
        r = run_tool("map", "--all", "--root", str(self.root), "--date", TODAY)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = self.root / "map.html"
        self.assertTrue(out.exists())
        html = out.read_text(encoding="utf-8")
        for needle in ("finance", "rust-cli", "double-entry",
                       "ownership-basics", "double-entry-for-budgets"):
            self.assertIn(needle, html)

    def test_map_all_discovers_root_from_cwd(self):
        r = run_tool("map", "--all", "--date", TODAY, cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.root / "map.html").exists())

    def test_single_workspace_map_still_works(self):
        out = self.root / "finance" / "map.html"
        r = run_tool("map", "--ledger", str(self.root / "finance/LEDGER.md"),
                     "--out", str(out), "--date", TODAY)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("double-entry", out.read_text(encoding="utf-8"))


class TestCrossWorkspaceState(RootFixture):
    """A due node cannot satisfy a prerequisite — across workspaces too."""

    def load(self):
        workspaces, problems = lt.load_root(str(self.root))
        self.assertFalse([p for p in problems if p[0] == "error"], problems)
        return workspaces

    def test_due_cross_prereq_blocks_frontier(self):
        ws = self.load()
        rust = ws["rust-cli"]
        resolve = lt.make_resolver(rust["nodes"], ws)
        # on 2026-06-12 finance:N01 is due -> rust N02 is not frontier
        state = lt.node_state(rust["nodes"]["N02"], resolve, date(2026, 6, 12))
        self.assertEqual(state, "unstarted")
        # on 2026-06-07 nothing is due -> rust N02 is frontier
        state = lt.node_state(rust["nodes"]["N02"], resolve, date(2026, 6, 7))
        self.assertEqual(state, "frontier")

    def test_unresolvable_cross_prereq_blocks_frontier(self):
        ws = self.load()
        rust = ws["rust-cli"]
        resolve = lt.make_resolver(rust["nodes"], None)  # no root context
        state = lt.node_state(rust["nodes"]["N02"], resolve, date(2026, 6, 7))
        self.assertEqual(state, "unstarted")


class TestRegistryParsing(RootFixture):
    def test_paths_default_to_workspace_name(self):
        ws, problems = lt.load_root(str(self.root))
        self.assertEqual(list(ws), ["finance", "rust-cli"])
        # finance declares path explicitly; rust-cli falls back to its name
        self.assertEqual(Path(ws["finance"]["dir"]), self.root / "finance")
        self.assertEqual(Path(ws["rust-cli"]["dir"]), self.root / "rust-cli")
        self.assertEqual(ws["finance"]["fields"]["cadence"], "daily · 30 min")

    def test_duplicate_workspace_is_error(self):
        self.write("registry.md", REGISTRY + "\n### finance\n- path: finance\n")
        _, problems, _ = lt.parse_registry(str(self.root / "registry.md"))
        self.assertTrue(any("duplicate" in m for _, m in problems))

    def test_bad_workspace_name_is_error(self):
        self.write("registry.md", REGISTRY.replace("### finance", "### Finance"))
        _, problems, _ = lt.parse_registry(str(self.root / "registry.md"))
        self.assertTrue(any("lowercase" in m for _, m in problems))


if __name__ == "__main__":
    unittest.main()
