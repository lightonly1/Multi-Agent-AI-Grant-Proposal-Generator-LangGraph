#!/usr/bin/env python3
# run_graph.py
#
# CLI Runner — FREE MODE (No OpenAI Required)

import argparse
import json
import os
import sys

from dotenv import load_dotenv

# load .env (optional, not required now)
load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Grant Proposal Generator — CLI Runner (FREE MODE)"
    )
    parser.add_argument("--topic", required=True, help="Research topic")
    parser.add_argument("--pdf", required=True, help="Path to PDF")
    parser.add_argument("--max-iter", type=int, default=3)
    parser.add_argument("--threshold", type=int, default=75)
    parser.add_argument("--output-json", action="store_true")
    return parser.parse_args()


def run_pipeline(topic, pdf_path, max_iterations, score_threshold):
    from graph.build_graph import build_proposal_graph
    from graph.state import ProposalState

    graph = build_proposal_graph()

    initial_state: ProposalState = {
        "topic": topic,
        "pdf_path": pdf_path,
        "max_iterations": max_iterations,
        "score_threshold": score_threshold,
        "guidelines_summary": None,
        "faiss_index_path": None,
        "proposal_draft": None,
        "budget_timeline": None,
        "eval_scores": None,
        "iteration": 0,
        "refinement_brief": None,
        "run_id": None
    }

    print("\n============================================================")
    print("  AI Grant Proposal Generator — FREE MODE")
    print("============================================================")
    print(f"  Topic: {topic}")
    print(f"  PDF:   {pdf_path}")
    print(f"  Max Iterations: {max_iterations}")
    print(f"  Score Target:   {score_threshold}/100")
    print("============================================================\n")

    final_state = graph.invoke(initial_state)
    return final_state


def print_results(final_state):
    proposal = final_state.get("proposal_draft", {})
    scores = final_state.get("eval_scores", {})
    budget = final_state.get("budget_timeline", {})
    iteration = final_state.get("iteration", 0)

    print("\n================ FINAL OUTPUT ================\n")

    print("TOPIC:\n", final_state.get("topic"))

    print("\nPROPOSAL:\n", proposal)

    print("\nBUDGET:\n", budget)

    print("\nEVALUATION:\n", scores)

    print(f"\nFINAL SCORE: {scores.get('total_score', 0)}/100")
    print(f"ITERATIONS USED: {iteration}")

    print("\n=============================================\n")

    # Optional: export docx
    try:
        from utils.exporters import export_proposal_docx

        path = export_proposal_docx(
            proposal_draft=proposal,
            budget_timeline=budget,
            eval_scores=scores,
            topic=final_state.get("topic", "proposal"),
            iteration=iteration
        )
        print(f"Document exported to: {path}")
    except Exception as e:
        print(f"Export failed: {e}")


def main():
    args = parse_args()

    if not os.path.exists(args.pdf):
        print(f"ERROR: PDF not found at '{args.pdf}'")
        sys.exit(1)

    print("Running in FREE MODE (No OpenAI required)\n")

    final_state = run_pipeline(
        topic=args.topic,
        pdf_path=args.pdf,
        max_iterations=args.max_iter,
        score_threshold=args.threshold
    )

    if args.output_json:
        safe_state = {
            k: v for k, v in final_state.items()
            if isinstance(v, (str, int, float, bool, dict, list, type(None)))
        }
        print(json.dumps(safe_state, indent=2))
    else:
        print_results(final_state)


if __name__ == "__main__":
    main()