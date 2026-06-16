# utils/improvement_tracker.py
#
# Iterative Improvement Tracker
# ------------------------------
# This module takes the iteration_history list produced by the LangGraph
# pipeline and turns it into useful analysis objects for the Streamlit UI.
#
# It answers four questions the UI needs to display:
#   1. How did the total score change between every consecutive pair of iterations?
#   2. Which specific criteria improved, degraded, or stayed the same?
#   3. Which weaknesses from the initial evaluation were resolved by the final draft?
#   4. What is the headline "X → Y" summary a human would quote?
#
# Design note: all functions here are pure — they take lists/dicts and return
# new lists/dicts with no side effects.  This makes them trivial to unit test
# and means the Streamlit app can call them on cached state without re-running
# the LLM pipeline.
#
# Author: Krit Prakash (M.Tech Capstone — Vignan Institute)

from typing import List, Dict, Any


# ── Constants ─────────────────────────────────────────────────────────────────

CRITERIA          = ["innovation", "feasibility", "budget_clarity", "impact"]
CRITERIA_DISPLAY  = {
    "innovation":     "Innovation",
    "feasibility":    "Feasibility",
    "budget_clarity": "Budget Clarity",
    "impact":         "Impact",
}
MAX_CRITERION_SCORE = 25
MAX_TOTAL_SCORE     = 100


# ── Core delta computation ────────────────────────────────────────────────────

def compute_score_deltas(history: List[dict]) -> List[dict]:
    """
    Compute score changes between every consecutive pair of iterations.

    Each entry in the returned list represents the transition from
    iteration[i] to iteration[i+1] and contains:
      from_iteration:   0-based index of the earlier pass
      to_iteration:     0-based index of the later pass
      from_tag:         "initial" / "v2" / "v3"
      to_tag:           "initial" / "v2" / "v3"
      from_total:       total score before
      to_total:         total score after
      delta_total:      to_total - from_total (positive = improved)
      pct_change:       delta as percentage of max (100)
      criterion_deltas: per-criterion delta dicts (see below)

    Each criterion_deltas entry:
      criterion:  e.g. "innovation"
      label:      "Innovation"
      from_score: int
      to_score:   int
      delta:      int
      direction:  "improved" | "degraded" | "unchanged"

    Returns an empty list if history has fewer than 2 entries.
    """
    if len(history) < 2:
        return []

    deltas = []
    for i in range(len(history) - 1):
        a = history[i]
        b = history[i + 1]

        criterion_deltas = []
        for c in CRITERIA:
            from_sc = a.get("criterion_scores", {}).get(c, 0)
            to_sc   = b.get("criterion_scores", {}).get(c, 0)
            diff    = to_sc - from_sc
            direction = "improved" if diff > 0 else ("degraded" if diff < 0 else "unchanged")
            criterion_deltas.append({
                "criterion":  c,
                "label":      CRITERIA_DISPLAY[c],
                "from_score": from_sc,
                "to_score":   to_sc,
                "delta":      diff,
                "direction":  direction,
            })

        deltas.append({
            "from_iteration":   a.get("iteration", i),
            "to_iteration":     b.get("iteration", i + 1),
            "from_tag":         a.get("version_tag", f"v{i+1}"),
            "to_tag":           b.get("version_tag", f"v{i+2}"),
            "from_total":       a.get("total_score", 0),
            "to_total":         b.get("total_score", 0),
            "delta_total":      b.get("total_score", 0) - a.get("total_score", 0),
            "pct_change":       round(
                (b.get("total_score", 0) - a.get("total_score", 0)) / MAX_TOTAL_SCORE * 100, 1
            ),
            "criterion_deltas": criterion_deltas,
        })

    return deltas


def compute_overall_improvement(history: List[dict]) -> dict:
    """
    Compare the very first iteration to the very last — the headline number.

    Returns:
      initial_score:    total score at iteration 0
      final_score:      total score at the last iteration
      absolute_gain:    final - initial
      pct_gain:         gain as % of max (100)
      grade_initial:    A/B/C/D grade for initial score
      grade_final:      A/B/C/D grade for final score
      improved:         True if final > initial
      criterion_gains:  list of per-criterion gain dicts
      resolved_weaknesses: list of criteria whose weakness was addressed
      new_weaknesses:   list of criteria that became weak after refinement
      headline:         human-readable one-liner e.g.
                        "Initial Score: 58/100 → Improved Score: 79/100 (+21 pts)"
    """
    if not history:
        return _empty_improvement()

    first = history[0]
    last  = history[-1]

    initial = first.get("total_score", 0)
    final   = last.get("total_score", 0)
    gain    = final - initial

    # per-criterion gains
    criterion_gains = []
    for c in CRITERIA:
        fi = first.get("criterion_scores", {}).get(c, 0)
        fl = last.get("criterion_scores",  {}).get(c, 0)
        d  = fl - fi
        criterion_gains.append({
            "criterion":    c,
            "label":        CRITERIA_DISPLAY[c],
            "initial_score": fi,
            "final_score":   fl,
            "gain":          d,
            "direction":     "improved" if d > 0 else ("degraded" if d < 0 else "unchanged"),
        })

    # weakness resolution: was weak in first pass, not weak in last pass
    initial_weak = set(first.get("weaknesses", {}).keys())
    final_weak   = set(last.get("weaknesses",  {}).keys())
    resolved     = sorted(initial_weak - final_weak)
    new_weak     = sorted(final_weak   - initial_weak)

    sign = "+" if gain >= 0 else ""
    headline = (
        f"Initial Score: {initial}/100  →  "
        f"Improved Score: {final}/100  "
        f"({sign}{gain} pts)"
    )

    return {
        "initial_score":         initial,
        "final_score":           final,
        "absolute_gain":         gain,
        "pct_gain":              round(gain / MAX_TOTAL_SCORE * 100, 1),
        "grade_initial":         _grade(initial),
        "grade_final":           _grade(final),
        "improved":              final > initial,
        "criterion_gains":       criterion_gains,
        "resolved_weaknesses":   resolved,
        "new_weaknesses":        new_weak,
        "iterations_run":        len(history),
        "headline":              headline,
    }


# ── Per-criterion weakness resolution ────────────────────────────────────────

def build_weakness_resolution_table(history: List[dict]) -> List[dict]:
    """
    Build a table showing whether each criterion's weakness was resolved
    across all iterations.

    Returns a list of rows, one per criterion:
      criterion:      key string
      label:          display name
      initial_weak:   True if criterion was weak at iteration 0
      final_weak:     True if criterion is still weak at last iteration
      status:         "resolved" | "persists" | "new" | "always_ok"
      initial_weakness_text: text from first pass (empty if not weak then)
      final_weakness_text:   text from last pass  (empty if not weak now)
      score_journey:  list of per-iteration scores for this criterion
    """
    if not history:
        return []

    first = history[0]
    last  = history[-1]

    rows = []
    for c in CRITERIA:
        initial_weak = c in first.get("weaknesses", {})
        final_weak   = c in last.get("weaknesses",  {})

        if   initial_weak and not final_weak: status = "resolved"
        elif initial_weak and final_weak:     status = "persists"
        elif not initial_weak and final_weak: status = "new"
        else:                                 status = "always_ok"

        score_journey = [
            snap.get("criterion_scores", {}).get(c, 0)
            for snap in history
        ]

        rows.append({
            "criterion":             c,
            "label":                 CRITERIA_DISPLAY[c],
            "initial_weak":          initial_weak,
            "final_weak":            final_weak,
            "status":                status,
            "initial_weakness_text": first.get("weaknesses", {}).get(c, ""),
            "final_weakness_text":   last.get("weaknesses",  {}).get(c, ""),
            "score_journey":         score_journey,
        })

    return rows


# ── Formatted text report ─────────────────────────────────────────────────────

def format_improvement_report(history: List[dict]) -> str:
    """
    Produce a clean human-readable text report of the full iteration loop.
    Suitable for printing to the console, embedding in the .docx export,
    or displaying in the Streamlit UI's expander.

    Example output:

        ITERATIVE IMPROVEMENT REPORT
        ════════════════════════════════════════════════
        Iterations run: 3

        Initial Score: 58/100  →  Improved Score: 79/100  (+21 pts)
        Grade: C → B

        ────────────────────────────────────────────────
        Iteration 0 → 1  (initial → v2)
        ────────────────────────────────────────────────
        Total:          58 → 71  (+13 pts)
        Innovation:     14 → 18  (+4)  ↑ improved
        Feasibility:    16 → 19  (+3)  ↑ improved
        Budget Clarity: 12 → 17  (+5)  ↑ improved
        Impact:         16 → 17  (+1)  ↑ improved

        Iteration 1 → 2  (v2 → v3)
        ────────────────────────────────────────────────
        Total:          71 → 79  (+8 pts)
        ...

        Weakness Resolution Summary
        ────────────────────────────────────────────────
        ✓  Innovation      resolved (was: Novelty unclear)
        ✓  Budget Clarity  resolved (was: Cloud compute unjustified)
        ✗  Impact          persists (still: Scale unproven)
    """
    if len(history) < 1:
        return "No iterations to report."

    lines = []
    lines.append("ITERATIVE IMPROVEMENT REPORT")
    lines.append("═" * 52)
    lines.append(f"Iterations run: {len(history)}")
    lines.append("")

    overall = compute_overall_improvement(history)
    lines.append(overall["headline"])
    lines.append(
        f"Grade: {overall['grade_initial']}  →  {overall['grade_final']}"
    )
    lines.append("")

    # per-transition blocks
    deltas = compute_score_deltas(history)
    for d in deltas:
        lines.append("─" * 52)
        lines.append(
            f"Iteration {d['from_iteration']} → {d['to_iteration']}  "
            f"({d['from_tag']} → {d['to_tag']})"
        )
        lines.append("─" * 52)
        sign = "+" if d["delta_total"] >= 0 else ""
        lines.append(
            f"Total:           {d['from_total']:3d} → {d['to_total']:3d}  "
            f"({sign}{d['delta_total']} pts)"
        )
        for cd in d["criterion_deltas"]:
            sign_c  = "+" if cd["delta"] >= 0 else ""
            arrow   = "↑" if cd["direction"] == "improved" else (
                      "↓" if cd["direction"] == "degraded" else "→")
            lines.append(
                f"{cd['label']:15s}  {cd['from_score']:2d} → {cd['to_score']:2d}  "
                f"({sign_c}{cd['delta']})  {arrow} {cd['direction']}"
            )
        lines.append("")

    # weakness resolution table
    if len(history) >= 2:
        lines.append("─" * 52)
        lines.append("Weakness Resolution")
        lines.append("─" * 52)
        table = build_weakness_resolution_table(history)
        status_icons = {
            "resolved":  "✓",
            "persists":  "✗",
            "new":       "⚠",
            "always_ok": "✓",
        }
        for row in table:
            icon = status_icons[row["status"]]
            label = f"{row['label']:15s}"
            if row["status"] == "resolved":
                lines.append(
                    f"{icon}  {label}  resolved  "
                    f"(was: {_truncate(row['initial_weakness_text'], 50)})"
                )
            elif row["status"] == "persists":
                lines.append(
                    f"{icon}  {label}  still weak  "
                    f"(still: {_truncate(row['final_weakness_text'], 50)})"
                )
            elif row["status"] == "new":
                lines.append(
                    f"{icon}  {label}  NEW weakness  "
                    f"({_truncate(row['final_weakness_text'], 50)})"
                )
            else:
                lines.append(f"{icon}  {label}  consistently strong")

    lines.append("═" * 52)
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _grade(score: int) -> str:
    if score >= 90: return "A"
    if score >= 75: return "B"
    if score >= 60: return "C"
    return "D"

def _truncate(text: str, n: int) -> str:
    return text[:n] + "..." if len(text) > n else text

def _empty_improvement() -> dict:
    return {
        "initial_score": 0, "final_score": 0,
        "absolute_gain": 0, "pct_gain": 0.0,
        "grade_initial": "D", "grade_final": "D",
        "improved": False, "criterion_gains": [],
        "resolved_weaknesses": [], "new_weaknesses": [],
        "iterations_run": 0,
        "headline": "No iterations run yet.",
    }


# ── Mock history builder (for demo mode) ─────────────────────────────────────

def build_mock_history(final_score: int = 85, n_iters: int = 3) -> List[dict]:
    """
    Generate a realistic-looking iteration_history for demo mode.
    Scores start low and improve with each pass.  Weaknesses from
    early iterations get resolved in later ones.

    Args:
        final_score:  target total score for the last iteration
        n_iters:      number of iterations to simulate (2 or 3)

    Returns:
        List of IterationSnapshot dicts
    """
    # work backwards: distribute criterion scores so they sum to final_score
    # and show realistic improvement trajectory
    initial_offset = min(24, final_score // 3)  # start ~24 pts below final

    def make_snap(iter_idx, total, tag, weak_criteria):
        # distribute total across 4 criteria somewhat evenly
        base = total // 4
        remainder = total % 4
        scores = {}
        for i, c in enumerate(CRITERIA):
            sc = base + (1 if i < remainder else 0)
            # add small variation so not perfectly uniform
            sc = max(5, min(MAX_CRITERION_SCORE, sc + (1 if i % 2 == 0 else -1)))
        # normalise so they sum exactly to total
        raw = {c: base + (1 if i < remainder else 0) for i, c in enumerate(CRITERIA)}
        # add credible variation per criterion
        offsets = {"innovation": 0, "feasibility": 1, "budget_clarity": -1, "impact": 0}
        for c in CRITERIA:
            raw[c] = max(5, min(MAX_CRITERION_SCORE, raw[c] + offsets[c]))
        # fix sum
        diff = total - sum(raw.values())
        raw[CRITERIA[0]] = max(0, min(MAX_CRITERION_SCORE, raw[CRITERIA[0]] + diff))

        weaknesses = {}
        for c in weak_criteria:
            weaknesses[c] = {
                "innovation":     "Novelty of the proposed method is unclear compared to recent literature.",
                "feasibility":    "IRB approval timeline is not accounted for in the project schedule.",
                "budget_clarity": "Cloud compute estimate lacks a vendor quote or AWS calculator evidence.",
                "impact":         "International scalability is mentioned but not substantiated.",
            }.get(c, "Needs improvement.")

        return {
            "iteration":        iter_idx,
            "total_score":      total,
            "criterion_scores": raw,
            "weaknesses":       weaknesses,
            "proposal_title":   f"AI-Driven Research Proposal (Draft {iter_idx + 1})",
            "version_tag":      tag,
        }

    if n_iters == 2:
        initial_total = final_score - initial_offset
        return [
            make_snap(0, initial_total, "initial",
                      ["innovation", "budget_clarity"]),
            make_snap(1, final_score,   "v2", []),
        ]
    else:
        initial_total = final_score - initial_offset
        mid_total     = initial_total + (initial_offset * 2 // 3)
        return [
            make_snap(0, initial_total, "initial",
                      ["innovation", "feasibility", "budget_clarity"]),
            make_snap(1, mid_total,     "v2",
                      ["budget_clarity"]),
            make_snap(2, final_score,   "v3", []),
        ]
