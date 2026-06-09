#!/usr/bin/env python3
"""
fsrs.py - minimal FSRS-6 scheduler for the /learn skill.

Adapted from py-fsrs (MIT, github.com/open-spaced-repetition/py-fsrs).
Simplifications for this skill: reviews are session-grained (no sub-day
learning steps), no interval fuzzing (deterministic and inspectable),
stdlib only.

Grades (mapped from probe outcomes, see PROBE-PROTOCOL.md):
  1 = Again  (failed probe)
  2 = Hard   (passed below target level)
  3 = Good   (clean pass at target)
  4 = Easy   (exceeded target)

Usage:
  python3 fsrs.py new    --grade 3 [--date 2026-06-09]
  python3 fsrs.py review --stability 5.2 --difficulty 6.1 \
                         --last 2026-06-01 --grade 3 [--date 2026-06-09]
  python3 fsrs.py status --stability 5.2 --last 2026-06-01 [--date 2026-06-09]

All commands print JSON. The agent copies stability/difficulty/due into
the node's `fsrs:` line in LEDGER.md. Never compute these by hand.
"""

import argparse
import json
import math
import sys
from datetime import date, timedelta

# FSRS-6 default parameters (py-fsrs DEFAULT_PARAMETERS).
W = (
    0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001,
    1.8722, 0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014,
    1.8729, 0.5425, 0.0912, 0.0658, 0.1542,
)
DECAY = -W[20]
FACTOR = 0.9 ** (1 / DECAY) - 1
DESIRED_RETENTION = 0.9
MAX_INTERVAL = 365  # capability nodes shouldn't vanish for years
MIN_S, MIN_D, MAX_D = 0.001, 1.0, 10.0


def clamp_s(s):
    return max(s, MIN_S)


def clamp_d(d):
    return min(max(d, MIN_D), MAX_D)


def retrievability(stability, elapsed_days):
    """Predicted probability of recall after elapsed_days."""
    return (1 + FACTOR * max(0, elapsed_days) / stability) ** DECAY


def initial_stability(grade):
    return clamp_s(W[grade - 1])


def initial_difficulty(grade, clamp=True):
    d = W[4] - math.e ** (W[5] * (grade - 1)) + 1
    return clamp_d(d) if clamp else d


def next_difficulty(d, grade):
    delta = -(W[6] * (grade - 3))
    damped = d + (10.0 - d) * delta / 9.0  # linear damping
    mean_target = initial_difficulty(4, clamp=False)
    return clamp_d(W[7] * mean_target + (1 - W[7]) * damped)  # mean reversion


def short_term_stability(s, grade):
    """Same-day review (elapsed < 1 day)."""
    inc = (math.e ** (W[17] * (grade - 3 + W[18]))) * (s ** -W[19])
    if grade >= 3:
        inc = max(inc, 1.0)
    return clamp_s(s * inc)


def next_recall_stability(d, s, r, grade):
    hard_penalty = W[15] if grade == 2 else 1.0
    easy_bonus = W[16] if grade == 4 else 1.0
    return clamp_s(
        s * (1 + math.e ** W[8] * (11 - d) * s ** -W[9]
             * (math.e ** ((1 - r) * W[10]) - 1) * hard_penalty * easy_bonus)
    )


def next_forget_stability(d, s, r):
    long_term = (W[11] * d ** -W[12] * ((s + 1) ** W[13] - 1)
                 * math.e ** ((1 - r) * W[14]))
    short_term = s / math.e ** (W[17] * W[18])
    return clamp_s(min(long_term, short_term))


def interval_for(stability):
    days = (stability / FACTOR) * (DESIRED_RETENTION ** (1 / DECAY) - 1)
    return max(1, min(round(days), MAX_INTERVAL))


def parse_date(s):
    if s is None:
        return date.today()
    return date.fromisoformat(s)


def out(payload):
    print(json.dumps(payload, indent=2))


def cmd_new(args):
    today = parse_date(args.date)
    s = initial_stability(args.grade)
    d = initial_difficulty(args.grade)
    ivl = interval_for(s)
    out({
        "stability": round(s, 4),
        "difficulty": round(d, 4),
        "interval_days": ivl,
        "last": today.isoformat(),
        "due": (today + timedelta(days=ivl)).isoformat(),
        "ledger_line": f"fsrs: S={s:.2f} D={d:.2f} last={today.isoformat()} "
                       f"due={(today + timedelta(days=ivl)).isoformat()}",
    })


def cmd_review(args):
    today = parse_date(args.date)
    last = date.fromisoformat(args.last)
    elapsed = (today - last).days
    if elapsed < 0:
        sys.exit("error: review date is before last review date")

    s, d, g = args.stability, args.difficulty, args.grade
    r = retrievability(s, elapsed)

    if elapsed < 1:
        new_s = short_term_stability(s, g)
    elif g == 1:
        new_s = next_forget_stability(d, s, r)
    else:
        new_s = next_recall_stability(d, s, r, g)
    new_d = next_difficulty(d, g)

    ivl = interval_for(new_s)
    out({
        "retrievability_at_review": round(r, 4),
        "stability": round(new_s, 4),
        "difficulty": round(new_d, 4),
        "interval_days": ivl,
        "last": today.isoformat(),
        "due": (today + timedelta(days=ivl)).isoformat(),
        "ledger_line": f"fsrs: S={new_s:.2f} D={new_d:.2f} "
                       f"last={today.isoformat()} "
                       f"due={(today + timedelta(days=ivl)).isoformat()}",
    })


def cmd_status(args):
    today = parse_date(args.date)
    last = date.fromisoformat(args.last)
    elapsed = (today - last).days
    r = retrievability(args.stability, elapsed)
    ivl = interval_for(args.stability)
    due = last + timedelta(days=ivl)
    out({
        "elapsed_days": elapsed,
        "retrievability": round(r, 4),
        "due": due.isoformat(),
        "is_due": today >= due,
        "days_overdue": max(0, (today - due).days),
    })


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pn = sub.add_parser("new", help="first evidence event for a node")
    pn.add_argument("--grade", type=int, choices=[1, 2, 3, 4], required=True)
    pn.add_argument("--date")
    pn.set_defaults(fn=cmd_new)

    pr = sub.add_parser("review", help="subsequent evidence event")
    pr.add_argument("--stability", type=float, required=True)
    pr.add_argument("--difficulty", type=float, required=True)
    pr.add_argument("--last", required=True, help="last review date YYYY-MM-DD")
    pr.add_argument("--grade", type=int, choices=[1, 2, 3, 4], required=True)
    pr.add_argument("--date")
    pr.set_defaults(fn=cmd_review)

    ps = sub.add_parser("status", help="current retrievability / due state")
    ps.add_argument("--stability", type=float, required=True)
    ps.add_argument("--last", required=True)
    ps.add_argument("--date")
    ps.set_defaults(fn=cmd_status)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
